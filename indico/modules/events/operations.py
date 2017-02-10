# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from operator import attrgetter

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events import Event, EventLogKind, EventLogRealm, logger
from indico.modules.events.features import features_event_settings
from indico.modules.events.layout import layout_settings
from indico.modules.events.logs.util import make_diff_log
from indico.modules.events.models.events import EventType
from indico.modules.events.models.references import ReferenceType


def create_reference_type(data):
    reference_type = ReferenceType()
    reference_type.populate_from_dict(data)
    db.session.add(reference_type)
    db.session.flush()
    logger.info('Reference type "%s" created by %s', reference_type, session.user)
    return reference_type


def update_reference_type(reference_type, data):
    reference_type.populate_from_dict(data)
    db.session.flush()
    logger.info('Reference type "%s" updated by %s', reference_type, session.user)


def delete_reference_type(reference_type):
    db.session.delete(reference_type)
    db.session.flush()
    logger.info('Reference type "%s" deleted by %s', reference_type, session.user)


def create_event_references(event, data):
    event.references = data['references']
    db.session.flush()
    for reference in event.references:
        logger.info('Reference "%s" created by %s', reference, session.user)


@no_autoflush
def create_event(category, event_type, data, add_creator_as_manager=True, features=None):
    """Create a new event.

    :param category: The category in which to create the event
    :param event_type: An `EventType` value
    :param data: A dict containing data used to populate the event
    :param add_creator_as_manager: Whether the creator (current user)
                                   should be added as a manager
    :param features: A list of features that will be enabled for the
                     event. If set, only those features will be used
                     and the default feature set for the event type
                     will be ignored.
    """
    from MaKaC.conference import Conference, ConferenceHolder
    conf = Conference()
    event = Event(category=category, type_=event_type)
    ConferenceHolder().add(conf, event)
    data.setdefault('creator', session.user)
    theme = data.pop('theme', None)
    person_link_data = data.pop('person_link_data', {})
    event.populate_from_dict(data)
    db.session.flush()
    event.person_link_data = person_link_data
    if theme is not None:
        layout_settings.set(event, 'timetable_theme', theme)
    if add_creator_as_manager:
        with event.logging_disabled:
            event.update_principal(event.creator, full_access=True)
    if features is not None:
        features_event_settings.set(event, 'enabled', features)
    db.session.flush()
    signals.event.created.send(event)
    logger.info('Event %r created in %r by %r ', event, category, session.user)
    event.log(EventLogRealm.event, EventLogKind.positive, 'Event', 'Event created', session.user)
    db.session.flush()
    return event


def _get_venue_room_name(data):
    venue_name = data['venue'].name if data.get('venue') else data.get('venue_name')
    room_name = data['room'].full_name if data.get('room') else data.get('room_name')
    return venue_name, room_name


def _format_location(data):
    venue_name = data[0]
    room_name = data[1]
    if venue_name and room_name:
        return '{}: {}'.format(venue_name, room_name)
    elif venue_name or room_name:
        return venue_name or room_name
    else:
        return None


def _split_location_changes(changes):
    location_changes = changes.pop('location_data', None)
    if location_changes is None:
        return
    if location_changes[0]['address'] != location_changes[1]['address']:
        changes['address'] = (location_changes[0]['address'], location_changes[1]['address'])
    venue_room_changes = (_get_venue_room_name(location_changes[0]), _get_venue_room_name(location_changes[1]))
    if venue_room_changes[0] != venue_room_changes[1]:
        changes['venue_room'] = map(_format_location, venue_room_changes)


def _format_person(data):
    return '{} <{}>'.format(data.full_name, data.email) if data.email else data.full_name


def update_event(event, update_timetable=False, **data):
    # TODO: Move this legacy stuff to proper places and then handle it together with the other new data
    _unset = object()
    displayed_start_dt = data.pop('displayed_start_dt', _unset)
    displayed_end_dt = data.pop('displayed_end_dt', _unset)
    if displayed_start_dt is not _unset:
        event.as_legacy.setScreenStartDate(displayed_start_dt)
    if displayed_end_dt is not _unset:
        event.as_legacy.setScreenEndDate(displayed_end_dt)

    assert data.viewkeys() <= {'title', 'description', 'url_shortcut', 'location_data', 'keywords', 'person_link_data',
                               'start_dt', 'end_dt', 'timezone'}
    old_person_links = event.person_links[:]
    if (update_timetable or event.type == EventType.lecture) and 'start_dt' in data:
        # Lectures have no exposed timetable so if we have any timetable entries
        # (e.g. because the event had a different type before) we always update them
        # silently.
        event.move_start_dt(data.pop('start_dt'))
    changes = event.populate_from_dict(data)
    if event.person_links != old_person_links:
        changes['person_links'] = (old_person_links, event.person_links)
    db.session.flush()
    signals.event.updated.send(event)
    # Now log everything nicely...
    logger.info('Event %r updated with %r by %r', event, data, session.user)
    log_fields = {
        'title': {'title': 'Title', 'type': 'string'},
        'description': 'Description',
        'url_shortcut': {'title': 'URL Shortcut', 'type': 'string'},
        'address': 'Address',
        'venue_room': {'title': 'Location', 'type': 'string'},
        'keywords': 'Keywords',
        'person_links': {
            'title': 'Speakers' if event.type_ == EventType.lecture else 'Chairpersons',
            'convert': lambda changes: [map(_format_person, persons) for persons in changes]
        },
        'start_dt': 'Start date',
        'end_dt': 'End date',
        'timezone': {'title': 'Timezone', 'type': 'string'}
    }
    _split_location_changes(changes)
    changes.pop('person_link_data', None)
    if changes:
        # XXX: we don't end up logging reordering of person links - there is no way to keep the old
        # order in here as it is updated on the objects already in the DB by the wtforms field
        if changes.viewkeys() <= {'timezone', 'start_dt', 'end_dt'}:
            what = 'Dates'
        elif len(changes) == 1:
            what = log_fields[changes.keys()[0]]
            if isinstance(what, dict):
                what = what['title']
        else:
            what = 'Data'
        event.log(EventLogRealm.management, EventLogKind.change, 'Event', '{} updated'.format(what), session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})


def update_event_protection(event, data):
    assert data.viewkeys() <= {'protection_mode', 'own_no_access_contact', 'access_key'}
    changes = event.populate_from_dict(data)
    db.session.flush()
    signals.event.updated.send(event)
    # Log everything...
    logger.info('Protection of event %r updated with %r by %r', event, data, session.user)
    if changes:
        log_fields = {'protection_mode': 'Protection mode',
                      'own_no_access_contact': 'No access contact',
                      'access_key': {'title': 'Access key', 'type': 'string'}}
        event.log(EventLogRealm.management, EventLogKind.change, 'Event', 'Protection updated', session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})


def delete_event(event):
    event.as_legacy.delete(session.user)
    db.session.flush()
    logger.info('Event %r deleted by %r', event, session.user)
    event.log(EventLogRealm.event, EventLogKind.negative, 'Event', 'Event deleted', session.user)
