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

from flask import request
from sqlalchemy.orm import load_only, noload

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import send_email, make_email
from indico.modules.auth.util import url_for_register
from indico.modules.events import Event
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.fulltextindexes.models.events import IndexedEvent
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
    obj = None
    if event is None:
        obj = None
    elif object_type == 'event':
        obj = event
    elif object_type == 'session':
        obj = event.sessions.filter_by(id=args['session_id'], is_deleted=False).first()
    elif object_type == 'contribution':
        obj = event.contributions.filter_by(id=args['contrib_id'], is_deleted=False).first()
    elif object_type == 'subcontribution':
        obj = SubContribution.find(SubContribution.contribution.has(event_new=event, id=args['contrib_id'],
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
    event_date_filter = None
    if from_dt and to_dt:
        event_date_filter = IndexedEvent.start_date.between(from_dt, to_dt)
    elif from_dt:
        event_date_filter = IndexedEvent.start_date >= from_dt
    elif to_dt:
        event_date_filter = IndexedEvent.start_date <= to_dt
    query = (user.in_event_acls
             .join(Event)
             .options(noload('user'), noload('local_group'), load_only('event_id'))
             .filter(~Event.is_deleted)
             .filter(EventPrincipal.has_management_role('ANY')))
    if event_date_filter is not None:
        query = query.join(IndexedEvent, IndexedEvent.id == EventPrincipal.event_id)
        query = query.filter(event_date_filter)
    return {principal.event_id for principal in query}


def get_events_created_by(user, from_dt=None, to_dt=None):
    """Gets the IDs of events created by the user

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    :return: A set of event ids
    """
    event_date_filter = None
    if from_dt and to_dt:
        event_date_filter = IndexedEvent.start_date.between(from_dt, to_dt)
    elif from_dt:
        event_date_filter = IndexedEvent.start_date >= from_dt
    elif to_dt:
        event_date_filter = IndexedEvent.start_date <= to_dt
    query = (user.created_events.filter(~Event.is_deleted))
    if event_date_filter is not None:
        query = query.join(IndexedEvent, IndexedEvent.id == Event.id)
        query = query.filter(event_date_filter)
    return {event.id for event in query}


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
