# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import random
from copy import deepcopy
from mimetypes import guess_extension
from os import path
from tempfile import NamedTemporaryFile

from flask import session, request, g
from sqlalchemy.orm import load_only, noload

from indico.core.config import Config
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import send_email, make_email
from indico.modules.api import settings as api_settings
from indico.modules.auth.util import url_for_register
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.models.report_links import ReportLink
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.web.forms.colors import get_colors
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for


def preload_events(ids, lightweight=True):
    """Preload events so they are in SA's identity cache

    This is useful for legacy pages where we have to show large
    numbers of events without being able to query them from the
    db cleanly.

    :param ids: An iterable of IDs or Conference objects
    :param lightweight: Only load dates and title
    """
    cache = g.setdefault('_event_cache', {})
    ids = {int(getattr(id_, 'id', id_)) for id_ in ids} - cache.viewkeys()
    query = Event.find(Event.id.in_(ids))
    if lightweight:
        query = query.options(load_only('id', 'title', 'start_dt', 'end_dt', 'timezone'))
    cache.update((e.id, e) for e in query)


def get_object_from_args(args=None):
    """Retrieves an event object from request arguments.

    This utility is meant to be used in cases where the same controller
    can deal with objects attached to various parts of an event which
    use different URLs to indicate which object to use.

    :param args: The request arguments. If unspecified,
                 ``request.view_args`` is used.
    :return: An ``(object_type, event, object)`` tuple.  The event is
             always the :class:`Event` associated with the object.
             The object may be an `Event`, `Session`, `Contribution`
             or `SubContribution`.  If the object does not exist,
             ``(object_type, None, None)`` is returned.
    """
    if args is None:
        args = request.view_args
    object_type = args['object_type']
    event = Event.find_first(id=args['confId'], is_deleted=False)
    if event is None:
        obj = None
    elif object_type == 'event':
        obj = event
    elif object_type == 'session':
        obj = Session.query.with_parent(event).filter_by(id=args['session_id']).first()
    elif object_type == 'contribution':
        obj = Contribution.query.with_parent(event).filter_by(id=args['contrib_id']).first()
    elif object_type == 'subcontribution':
        obj = SubContribution.find(SubContribution.id == args['subcontrib_id'], ~SubContribution.is_deleted,
                                   SubContribution.contribution.has(event_new=event, id=args['contrib_id'],
                                                                    is_deleted=False)).first()
    else:
        raise ValueError('Unexpected object type: {}'.format(object_type))
    if obj is not None:
        return object_type, event, obj
    else:
        return object_type, None, None


def get_events_managed_by(user, from_dt=None, to_dt=None):
    """Gets the IDs of events where the user has management privs.

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    :return: A set of event ids
    """
    query = (user.in_event_acls
             .join(Event)
             .options(noload('user'), noload('local_group'), load_only('event_id'))
             .filter(~Event.is_deleted, Event.starts_between(from_dt, to_dt))
             .filter(EventPrincipal.has_management_role('ANY')))
    return {principal.event_id for principal in query}


def get_events_created_by(user, from_dt=None, to_dt=None):
    """Gets the IDs of events created by the user

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    :return: A set of event ids
    """
    query = user.created_events.filter(~Event.is_deleted, Event.starts_between(from_dt, to_dt))
    return {event.id for event in query}


def get_events_with_linked_event_persons(user, from_dt=None, to_dt=None):
    """Returns a list of all events for which the user is an EventPerson

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    """
    query = (user.event_persons
             .options(load_only('event_id'))
             .options(noload('*'))
             .join(Event, Event.id == EventPerson.event_id)
             .filter(EventPerson.event_links.any())
             .filter(~Event.is_deleted, Event.starts_between(from_dt, to_dt)))
    return {ep.event_id for ep in query}


def get_random_color(event):
    breaks = Break.query.filter(Break.timetable_entry.has(event_new=event))
    used_colors = {s.colors for s in event.sessions} | {b.colors for b in breaks}
    unused_colors = set(get_colors()) - used_colors
    return random.choice(tuple(unused_colors) or get_colors())


def notify_pending(acl_entry):
    """Sends a notification to a user with an email-based ACL entry

    :param acl_entry: An email-based EventPrincipal
    """
    assert acl_entry.type == PrincipalType.email
    if acl_entry.full_access:
        template_name = 'events/emails/pending_manager.txt'
        endpoint = 'event_mgmt.conferenceModification-managementAccess'
    elif acl_entry.has_management_role('submit', explicit=True):
        template_name = 'events/emails/pending_submitter.txt'
        endpoint = 'event.conferenceDisplay'
    else:
        return
    event = acl_entry.event_new
    email = acl_entry.principal.email
    template = get_template_module(template_name, event=event, email=email,
                                   url=url_for_register(url_for(endpoint, event), email=email))
    send_email(make_email(to_list={email}, template=template), event.as_legacy, module='Protection')


def serialize_event_person(person):
    """Serialize EventPerson to JSON-like object"""
    return {'_type': 'EventPerson',
            'id': person.id,
            'email': person.email,
            'name': person.full_name,
            'firstName': person.first_name,
            'familyName': person.last_name,
            'title': person.title,
            'affiliation': person.affiliation,
            'phone': person.phone,
            'address': person.address}


def serialize_person_link(person_link):
    """Serialize PersonLink to JSON-like object"""
    return {'_type': 'PersonLink',
            'id': person_link.person.id,
            'personId': person_link.person.id,
            'email': person_link.person.email,
            'name': person_link.full_name,
            'firstName': person_link.first_name,
            'familyName': person_link.last_name,
            'title': person_link.title,
            'affiliation': person_link.affiliation,
            'phone': person_link.phone,
            'address': person_link.address}


def update_object_principals(obj, new_principals, read_access=False, full_access=False, role=None):
    """Updates an object's ACL with a new list of principals

    Exactly one argument out of `read_access`, `full_access` and `role` must be specified.

    :param obj: The object to update. Must have ``acl_entries``
    :param new_principals: The set containing the new principals
    :param read_access: Whether the read access ACL should be updated
    :param full_access: Whether the full access ACL should be updated
    :param role: The role ACL that should be updated
    """
    if read_access + full_access + bool(role) != 1:
        raise ValueError('Only one ACL property can be specified')
    if full_access:
        existing = {acl.principal for acl in obj.acl_entries if acl.full_access}
        grant = {'full_access': True}
        revoke = {'full_access': False}
    elif read_access:
        existing = {acl.principal for acl in obj.acl_entries if acl.read_access}
        grant = {'read_access': True}
        revoke = {'read_access': False}
    elif role:
        existing = {acl.principal for acl in obj.acl_entries if acl.has_management_role(role, explicit=True)}
        grant = {'add_roles': {role}}
        revoke = {'del_roles': {role}}

    new_principals = set(new_principals)
    for principal in new_principals - existing:
        obj.update_principal(principal, **grant)
    for principal in existing - new_principals:
        obj.update_principal(principal, **revoke)


class ReporterBase(object):
    """Base class for classes performing actions on reports.

    :param event: The associated `Event`
    :param entry_parent: The parent of the entries of the report. If it's None,
                         the parent is assumed to be the event itself.
    """

    #: The endpoint of the report management page
    endpoint = None
    #: Unique report identifier
    report_link_type = None
    #: The default report configuration dictionary
    default_report_config = None

    def __init__(self, event, entry_parent=None):
        self.report_event = event
        self.entry_parent = entry_parent or event
        self.filterable_items = None
        self.static_link_used = 'config' in request.args

    def _get_config_session_key(self):
        """Compose the unique configuration ID.

        This ID will be used as a key to set the report's configuration to the
        session.
        """
        return '{}_config_{}'.format(self.report_link_type, self.entry_parent.id)

    def _get_config(self):
        """Load the report's configuration from the DB and return it."""
        session_key = self._get_config_session_key()
        if self.static_link_used:
            uuid = request.args['config']
            configuration = ReportLink.load(self.report_event, self.report_link_type, uuid)
            if configuration and configuration['entry_parent_id'] == self.entry_parent.id:
                session[session_key] = configuration['data']
        return session.get(session_key, self.default_report_config)

    def build_query(self):
        """Return the query of the report's entries.

        The query should not take into account the user's filtering
        configuration, for example::

            return Contribution.query.with_parent(self.report_event)
        """
        raise NotImplementedError

    def filter_report_entries(self):
        """Apply user's filters to query and return it."""
        raise NotImplementedError

    def get_filters_from_request(self):
        """Get the new filters after the filter form is submitted."""
        filters = deepcopy(self.default_report_config['filters'])
        for item_id, item in self.filterable_items.iteritems():
            if item.get('filter_choices'):
                options = [x if x != 'None' else None for x in request.form.getlist('field_{}'.format(item_id))]
                if options:
                    filters['items'][item_id] = options
        return filters

    def get_report_url(self, uuid=None, external=False):
        """Return the URL of the report management page."""
        return url_for(self.endpoint, self.entry_parent, config=uuid, _external=external)

    def generate_static_url(self):
        """Return a URL with a uuid referring to the report's configuration."""
        session_key = self._get_config_session_key()
        configuration = {
            'entry_parent_id': self.entry_parent.id,
            'data': session.get(session_key)
        }
        if configuration['data']:
            link = ReportLink.create(self.report_event, self.report_link_type, configuration)
            return self.get_report_url(uuid=link.uuid, external=True)
        else:
            return self.get_report_url(external=True)

    def store_filters(self):
        """Load the filters from the request and store them in the session."""
        filters = self.get_filters_from_request()
        session_key = self._get_config_session_key()
        self.report_config = session.setdefault(session_key, {})
        self.report_config['filters'] = filters
        session.modified = True


def get_base_ical_parameters(user, event, detail):
    """Returns a dict of all parameters expected by iCal template"""

    from indico.web.http_api.util import generate_public_auth_request

    api_mode = api_settings.get('security_mode')
    persistent_allowed = api_settings.get('allow_persistent')
    api_key = user.api_key if user else None
    persistent_user_enabled = api_key.is_persistent_allowed if api_key else None
    tpl = get_template_module('api/_messages.html')
    persistent_agreement = tpl.get_ical_persistent_msg()
    top_urls = generate_public_auth_request(api_key, '/export/event/{0}.ics'.format(event.id))
    urls = generate_public_auth_request(api_key, '/export/event/{0}.ics'.format(event.id), {'detail': detail})
    request_urls = {
        'publicRequestURL': top_urls['publicRequestURL'],
        'authRequestURL': top_urls['authRequestURL'],
        'publicRequestDetailedURL': urls['publicRequestURL'],
        'authRequestDetailedURL': urls['authRequestURL']
    }

    return {'api_mode': api_mode, 'api_key': api_key, 'persistent_allowed': persistent_allowed,
            'persistent_user_enabled': persistent_user_enabled, 'api_active': api_key is not None,
            'api_key_user_agreement': tpl.get_ical_api_key_msg(), 'api_persistent_user_agreement': persistent_agreement,
            'user_logged': user is not None, 'request_urls': request_urls}


def create_event_logo_tmp_file(event):
    """Creates a temporary file with the event's logo"""
    logo_meta = event.logo_metadata
    logo_extension = guess_extension(logo_meta['content_type']) or path.splitext(logo_meta['filename'])[1]
    temp_file = NamedTemporaryFile(delete=False, dir=Config.getInstance().getTempDir(), suffix=logo_extension)
    temp_file.write(event.logo)
    temp_file.flush()
    return temp_file
