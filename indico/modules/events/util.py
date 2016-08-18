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

import json
import random
import warnings
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from mimetypes import guess_extension
from os import path
from tempfile import NamedTemporaryFile

from flask import session, request, g, current_app
from sqlalchemy import inspect
from sqlalchemy.orm import load_only, noload

from indico.core import signals
from indico.core.config import Config
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.errors import UserValueError
from indico.core.notifications import send_email, make_email
from indico.modules.api import settings as api_settings
from indico.modules.auth.util import url_for_register
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.models.static_list_links import StaticListLink
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.i18n import _
from indico.web.forms.colors import get_colors
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for


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
    query = user.created_events.filter(~Event.is_deleted, Event.starts_between(from_dt, to_dt)).options(load_only('id'))
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
            'address': person.address,
            'user_id': person.user_id}


def serialize_person_link(person_link):
    """Serialize PersonLink to JSON-like object"""
    return {'_type': 'PersonLink',
            'id': person_link.person.id,
            'personId': person_link.person.id,
            'email': person_link.person.email,
            'name': person_link.full_name,
            'fullName': person_link.full_name,
            'firstName': person_link.first_name,
            'familyName': person_link.last_name,
            'title': person_link.title,
            'affiliation': person_link.affiliation,
            'phone': person_link.phone,
            'address': person_link.address,
            'displayOrder': person_link.display_order}


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


class ListGeneratorBase(object):
    """Base class for classes performing actions on Indico object lists.

    :param event: The associated `Event`
    :param entry_parent: The parent of the entries of the list. If it's None,
                         the parent is assumed to be the event itself.
    """

    #: The endpoint of the list management page
    endpoint = None
    #: Unique list identifier
    list_link_type = None
    #: The default list configuration dictionary
    default_list_config = None

    def __init__(self, event, entry_parent=None):
        #: The event the list is associated with
        self.list_event = event
        #: The parent object of the list items
        self.entry_parent = entry_parent or event
        #: Columns that originate from the list item's properties,
        #: relationships etc, but not from user defined fields (e.g.
        #: registration/contribution fields)
        self.static_items = None
        self.static_link_used = 'config' in request.args

    def _get_config_session_key(self):
        """Compose the unique configuration ID.

        This ID will be used as a key to set the list's configuration to the
        session.
        """
        return '{}_config_{}'.format(self.list_link_type, self.entry_parent.id)

    def _get_config(self):
        """Load the list's configuration from the DB and return it."""
        session_key = self._get_config_session_key()
        if self.static_link_used:
            uuid = request.args['config']
            configuration = StaticListLink.load(self.list_event, self.list_link_type, uuid)
            if configuration and configuration['entry_parent_id'] == self.entry_parent.id:
                session[session_key] = configuration['data']
        return session.get(session_key, self.default_list_config)

    def _split_item_ids(self, item_ids, separator_type=None):
        """Separate the dynamic item ids from the static

        :param item_ids: The list of ids to be splitted.
        :param separator_type: The type of the item to base the partitioning on.
                               If the value is 'dynamic', the function will
                               return a tuple where the first element is a list
                               of the dynamic item IDs and the second element a
                               list of the rest item IDs. If the value is
                               'static', the first element of the returned
                               tuple will be a list of the static item IDs.
        :return: A tuple of 2 lists as a result of the item_ids list
                 partitioning.
        """
        if separator_type == 'dynamic':
            dynamic_item_ids = [item_id for item_id in item_ids if not isinstance(item_id, basestring)]
            return dynamic_item_ids, [item_id for item_id in item_ids if item_id not in dynamic_item_ids]
        elif separator_type == 'static':
            static_item_ids = [item_id for item_id in item_ids if item_id in self.static_items]
            return static_item_ids, [item_id for item_id in item_ids if item_id not in static_item_ids]
        return item_ids,

    def _build_query(self):
        """Return the query of the list's entries.

        The query should not take into account the user's filtering
        configuration, for example::

            return Contribution.query.with_parent(self.list_event)
        """
        raise NotImplementedError

    def _filter_list_entries(self):
        """Apply user's filters to query and return it."""
        raise NotImplementedError

    def _get_filters_from_request(self):
        """Get the new filters after the filter form is submitted."""
        filters = deepcopy(self.default_list_config['filters'])
        for item_id, item in self.static_items.iteritems():
            if item.get('filter_choices'):
                options = [x if x != 'None' else None for x in request.form.getlist('field_{}'.format(item_id))]
                if options:
                    filters['items'][item_id] = options
        return filters

    def get_list_url(self, uuid=None, external=False):
        """Return the URL of the list management page."""
        return url_for(self.endpoint, self.entry_parent, config=uuid, _external=external)

    def generate_static_url(self):
        """Return a URL with a uuid referring to the list's configuration."""
        session_key = self._get_config_session_key()
        configuration = {
            'entry_parent_id': self.entry_parent.id,
            'data': session.get(session_key)
        }
        if configuration['data']:
            link = StaticListLink.create(self.list_event, self.list_link_type, configuration)
            return self.get_list_url(uuid=link.uuid, external=True)
        else:
            return self.get_list_url(external=True)

    def store_configuration(self):
        """Load the filters from the request and store them in the session."""
        filters = self._get_filters_from_request()
        session_key = self._get_config_session_key()
        self.list_config = session.setdefault(session_key, {})
        self.list_config['filters'] = filters
        if request.values.get('visible_items'):
            visible_items = json.loads(request.values['visible_items'])
            self.list_config['items'] = sorted(visible_items)
        session.modified = True


def get_base_ical_parameters(user, object, detail, path):
    """Returns a dict of all parameters expected by iCal template"""

    from indico.web.http_api.util import generate_public_auth_request

    api_mode = api_settings.get('security_mode')
    persistent_allowed = api_settings.get('allow_persistent')
    api_key = user.api_key if user else None
    persistent_user_enabled = api_key.is_persistent_allowed if api_key else None
    tpl = get_template_module('api/_messages.html')
    persistent_agreement = tpl.get_ical_persistent_msg()
    top_urls = generate_public_auth_request(api_key, path)
    urls = generate_public_auth_request(api_key, path, {'detail': detail})
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


@contextmanager
def track_time_changes(auto_extend=False, user=None):
    """Track time changes of event objects.

    This provides a list of changes while the context manager was
    active and also triggers `times_changed` signals.

    If the code running inside the ``with`` block of this context
    manager raises an exception, no signals will be triggered.

    :param auto_extend: Whether entry parents will get their boundaries
                        automatically extended or not. Passing ``'start'`` will
                        extend only start datetime, ``'end'`` to extend only
                        end datetime.
    :param user: The `User` that will trigger time changes.
    """
    if auto_extend:
        assert user is not None
    if 'old_times' in g:
        raise RuntimeError('time change tracking may not be nested')
    g.old_times = defaultdict(dict)
    changes = defaultdict(dict)
    try:
        yield changes
    except:
        del g.old_times
        raise
    else:
        if auto_extend:
            by_start = auto_extend in (True, 'start')
            by_end = auto_extend in (True, 'end')
            initial_changes = set(g.old_times)
            # g.old_times changes during iteration
            for obj in list(g.old_times):
                if not isinstance(obj, Event):
                    obj.extend_parent(by_start=by_start, by_end=by_end)
            cascade_changes = set(g.old_times) - initial_changes
            for obj in cascade_changes:
                if isinstance(obj, Event):
                    if not obj.can_manage(user):
                        # TODO: raise Forbidden exceptions after adding protection check in the UI
                        raise UserValueError(_("Your action requires modification of event boundaries, but you are "
                                               "not authorized to manage the event."))
                elif not obj.object.can_manage(user):
                    # TODO: raise Forbidden exceptions after adding protection check in the UI
                    raise UserValueError(_("Your action requires modification of session block boundaries, but you are "
                                           "not authorized to manage the session block."))
        old_times = g.pop('old_times')
        for obj, info in old_times.iteritems():
            if isinstance(obj, TimetableEntry):
                obj = obj.object
            if obj.start_dt != info['start_dt']:
                changes[obj]['start_dt'] = (info['start_dt'], obj.start_dt)
            if obj.duration != info['duration']:
                changes[obj]['duration'] = (info['duration'], obj.duration)
            if obj.end_dt != info['end_dt']:
                changes[obj]['end_dt'] = (info['end_dt'], obj.end_dt)
        for obj, obj_changes in changes.iteritems():
            entry = None if isinstance(obj, Event) else obj.timetable_entry
            signals.event.times_changed.send(type(obj), entry=entry, obj=obj, changes=obj_changes)


def register_time_change(entry):
    """Register a time-related change for a timetable entry

    This is an internal helper function used in the models to record
    changes of the start time or duration.  The changes are exposed
    through the `track_time_changes` contextmanager function.
    """
    # if it's a new object it's not a change so we just ignore it
    if not inspect(entry).persistent:
        return
    try:
        old_times = g.old_times
    except AttributeError:
        msg = 'Time change of {} was not tracked'.format(entry)
        if current_app.config.get('REPL'):
            warnings.warn(msg + ' (exception converted to a warning since you are using the REPL)', stacklevel=2)
            return
        elif current_app.config['TESTING']:
            warnings.warn(msg + ' (exception converted to a warning during tests)', stacklevel=2)
            return
        else:
            raise RuntimeError(msg)
    for field in ('start_dt', 'duration', 'end_dt'):
        if old_times[entry].get(field) is None:
            old_times[entry][field] = getattr(entry, field)


def register_event_time_change(event):
    """Register a time-related change for an event

    This is an internal helper function used in the model to record
    changes of the start time or end time.  The changes are exposed
    through the `track_time_changes` contextmanager function.
    """
    # if it's a new object it's not a change so we just ignore it
    if not inspect(event).persistent:
        return
    try:
        old_times = g.old_times
    except AttributeError:
        msg = 'Time change of {} was not tracked'.format(event)
        if current_app.config.get('REPL'):
            warnings.warn(msg + ' (exception converted to a warning since you are using the REPL)', stacklevel=2)
            return
        elif current_app.config['TESTING']:
            warnings.warn(msg + ' (exception converted to a warning during tests)', stacklevel=2)
            return
        else:
            raise RuntimeError(msg)
    for field in ('start_dt', 'duration', 'end_dt'):
        if old_times[event].get(field) is None:
            old_times[event][field] = getattr(event, field)


def serialize_event_for_ical(event, detail_level):
    from indico.modules.events.contributions.util import serialize_contribution_for_ical
    fossil = 'conferenceMetadataWithContribs' if detail_level == 'contributions' else 'conferenceMetadata'
    data = {'id': event.id, 'title': event.title, 'description': event.description, 'startDate': event.start_dt,
            'endDate': event.end_dt, 'url': url_for('event.conferenceDisplay', event, _external=True),
            'location': event.venue_name, 'roomFullname': event.room_name, 'speakers': [], '_fossil': fossil,
            'contributions': []}
    if detail_level == 'contributions':
        data['contributions'] = [serialize_contribution_for_ical(c) for c in event.contributions]
    return data
