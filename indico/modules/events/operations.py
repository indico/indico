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

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events import Event, EventLogKind, EventLogRealm, logger
from indico.modules.events.features import features_event_settings
from indico.modules.events.layout import layout_settings
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


def update_event(event, data):
    event.populate_from_dict(data)
    db.session.flush()
    signals.event.updated.send(event)
    logger.info('Event %r updated with %r', event, data)


def delete_event(event):
    event.as_legacy.delete(session.user)
    db.session.flush()
    logger.info('Event %r deleted by %r', event, session.user)
