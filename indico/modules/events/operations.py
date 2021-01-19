# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from operator import attrgetter

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.categories.util import get_visibility_options
from indico.modules.events import Event, EventLogKind, EventLogRealm, logger
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features import features_event_settings
from indico.modules.events.layout import layout_settings
from indico.modules.events.logs.util import make_diff_log
from indico.modules.events.models.events import EventType
from indico.modules.events.models.labels import EventLabel
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


def create_event_label(data):
    event_label = EventLabel()
    event_label.populate_from_dict(data)
    db.session.add(event_label)
    db.session.flush()
    logger.info('Event label "%s" created by %s', event_label, session.user)
    return event_label


def update_event_label(event_label, data):
    event_label.populate_from_dict(data)
    db.session.flush()
    logger.info('Event label "%s" updated by %s', event_label, session.user)


def delete_event_label(event_label):
    db.session.delete(event_label)
    db.session.flush()
    logger.info('Event label "%s" deleted by %s', event_label, session.user)


@no_autoflush
def create_event(category, event_type, data, add_creator_as_manager=True, features=None, cloning=False):
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
    :param cloning: Whether the event is created via cloning or not
    """
    from indico.modules.rb.operations.bookings import create_booking_for_event
    event = Event(category=category, type_=event_type)
    data.setdefault('creator', session.user)
    theme = data.pop('theme', None)
    create_booking = data.pop('create_booking', False)
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
    signals.event.created.send(event, cloning=cloning)
    logger.info('Event %r created in %r by %r ', event, category, session.user)
    event.log(EventLogRealm.event, EventLogKind.positive, 'Event', 'Event created', session.user)
    db.session.flush()
    if create_booking:
        room_id = data['location_data'].pop('room_id', None)
        if room_id:
            booking = create_booking_for_event(room_id, event)
            if booking:
                logger.info('Booking %r created for event %r', booking, event)
                log_data = {'Room': booking.room.full_name,
                            'Date': booking.start_dt.strftime('%d/%m/%Y'),
                            'Times': '%s - %s' % (booking.start_dt.strftime('%H:%M'), booking.end_dt.strftime('%H:%M'))}
                event.log(EventLogRealm.event, EventLogKind.positive, 'Event', 'Room booked for the event',
                          session.user, data=log_data)
                db.session.flush()
    return event


def update_event(event, update_timetable=False, **data):
    assert set(data.viewkeys()) <= {'title', 'description', 'url_shortcut', 'location_data', 'keywords',
                                    'person_link_data', 'start_dt', 'end_dt', 'timezone', 'keywords', 'references',
                                    'organizer_info', 'additional_info', 'contact_title', 'contact_emails',
                                    'contact_phones', 'start_dt_override', 'end_dt_override', 'label', 'label_message',
                                    'own_map_url'}
    old_person_links = event.person_links[:]
    changes = {}
    if (update_timetable or event.type == EventType.lecture) and 'start_dt' in data:
        # Lectures have no exposed timetable so if we have any timetable entries
        # (e.g. because the event had a different type before) we always update them
        # silently.
        start_dt = data.pop('start_dt')
        changes['start_dt'] = (event.start_dt, start_dt)
        event.move_start_dt(start_dt)
    changes.update(event.populate_from_dict(data))
    # Person links are partially updated when the WTForms field is processed,
    # we we don't have proper change tracking there in some cases
    changes.pop('person_link_data', None)
    visible_person_link_changes = event.person_links != old_person_links
    if visible_person_link_changes or 'person_link_data' in data:
        changes['person_links'] = (old_person_links, event.person_links)
    db.session.flush()
    signals.event.updated.send(event, changes=changes)
    logger.info('Event %r updated with %r by %r', event, data, session.user)
    _log_event_update(event, changes, visible_person_link_changes=visible_person_link_changes)


def clone_event(event, n_occurrence, start_dt, cloners, category=None):
    """Clone an event on a given date/time.

    Runs all required cloners.

    :param n_occurrence: The 1-indexed number of the occurrence, if this is a "recurring" clone, otherwise `0`
    :param start_dt: The start datetime of the new event;
    :param cloners: A set containing the names of all enabled cloners;
    :param category: The `Category` the new event will be created in.
    """
    end_dt = start_dt + event.duration
    data = {
        'start_dt': start_dt,
        'end_dt': end_dt,
        'timezone': event.timezone,
        'title': event.title,
        'description': event.description,
        'own_map_url': event.own_map_url
    }
    new_event = create_event(category or event.category, event.type_, data,
                             features=features_event_settings.get(event, 'enabled'),
                             add_creator_as_manager=False, cloning=True)

    # Run the modular cloning system
    EventCloner.run_cloners(event, new_event, cloners, n_occurrence)
    signals.event.cloned.send(event, new_event=new_event)

    # Grant access to the event creator -- must be done after modular cloners
    # since cloning the event ACL would result in a duplicate entry
    with new_event.logging_disabled:
        new_event.update_principal(session.user, full_access=True)

    return new_event


def clone_into_event(source_event, target_event, cloners):
    """Clone data into an existing event.

    Runs all required cloners.

    :param source_event: The `Event` to clone data from;
    :param target_event: The `Event` to clone data into;
    :param cloners: A set containing the names of all enabled cloners.
    """

    # Run the modular cloning system
    EventCloner.run_cloners(source_event, target_event, cloners, event_exists=True)
    signals.event.imported.send(target_event, source_event=source_event)

    return target_event


def _log_event_update(event, changes, visible_person_link_changes=False):
    log_fields = {
        'title': {'title': 'Title', 'type': 'string'},
        'description': 'Description',
        'url_shortcut': {'title': 'URL Shortcut', 'type': 'string'},
        'address': 'Address',
        'venue_room': {'title': 'Location', 'type': 'string'},
        'keywords': 'Keywords',
        'references': {
            'title': 'External IDs',
            'convert': lambda changes: [map(_format_ref, refs) for refs in changes]
        },
        'person_links': {
            'title': 'Speakers' if event.type_ == EventType.lecture else 'Chairpersons',
            'convert': lambda changes: [map(_format_person, persons) for persons in changes]
        },
        'start_dt': 'Start date',
        'end_dt': 'End date',
        'start_dt_override': 'Displayed start date',
        'end_dt_override': 'Displayed end date',
        'timezone': {'title': 'Timezone', 'type': 'string'},
        'organizer_info': 'Organizers',
        'additional_info': 'Additional Info',
        'contact_title': {'title': 'Contact/Support title', 'type': 'string'},
        'contact_emails': 'Contact emails',
        'contact_phones': 'Contact phone numbers',
        'label': {'title': 'Label', 'type': 'string', 'attr': 'title'},
        'label_message': 'Label message',
        'own_map_url': {'title': 'Map URL', 'type': 'string'}
    }
    _split_location_changes(changes)
    if not visible_person_link_changes:
        # Don't log a person link change with no visible changes (changes
        # on an existing link or reordering). It would look quite weird in
        # the event log.
        # TODO: maybe use a separate signal for such changes to log them
        # anyway and allow other code to act on them?
        changes.pop('person_links', None)
    if changes:
        if set(changes.viewkeys()) <= {'timezone', 'start_dt', 'end_dt', 'start_dt_override', 'end_dt_override'}:
            what = 'Dates'
        elif len(changes) == 1:
            what = log_fields[changes.keys()[0]]
            if isinstance(what, dict):
                what = what['title']
        else:
            what = 'Data'
        event.log(EventLogRealm.management, EventLogKind.change, 'Event', '{} updated'.format(what), session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})


def _format_ref(ref):
    return '{}:{}'.format(ref.reference_type.name, ref.value)


def _get_venue_room_name(data):
    venue_name = data['venue'].name if data.get('venue') else data.get('venue_name', '')
    room_name = data['room'].full_name if data.get('room') else data.get('room_name', '')
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


def update_event_protection(event, data):
    assert set(data.viewkeys()) <= {'protection_mode', 'own_no_access_contact', 'access_key',
                                    'visibility', 'public_regform_access'}
    changes = event.populate_from_dict(data)
    db.session.flush()
    signals.event.updated.send(event, changes=changes)
    logger.info('Protection of event %r updated with %r by %r', event, data, session.user)
    if changes:
        log_fields = {'protection_mode': 'Protection mode',
                      'own_no_access_contact': 'No access contact',
                      'access_key': {'title': 'Access key', 'type': 'string'},
                      'visibility': {'title': 'Visibility', 'type': 'string',
                                     'convert': lambda changes: [_format_visibility(event, x) for x in changes]},
                      'public_regform_access': 'Public registration form access'}
        event.log(EventLogRealm.management, EventLogKind.change, 'Event', 'Protection updated', session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})


def _format_visibility(event, visibility):
    options = dict(get_visibility_options(event, allow_invisible=True))
    return options[visibility if visibility is not None else '']


def update_event_type(event, type_):
    if event.type_ == type_:
        return
    event.type_ = type_
    logger.info('Event %r type changed to %s by %r', event, type_.name, session.user)
    event.log(EventLogRealm.event, EventLogKind.change, 'Event', 'Type changed to {}'.format(type_.title), session.user)


def lock_event(event):
    event.is_locked = True
    db.session.flush()
    logger.info('Event %r locked by %r', event, session.user)
    event.log(EventLogRealm.event, EventLogKind.change, 'Event', 'Event locked', session.user)


def unlock_event(event):
    event.is_locked = False
    db.session.flush()
    logger.info('Event %r unlocked by %r', event, session.user)
    event.log(EventLogRealm.event, EventLogKind.change, 'Event', 'Event unlocked', session.user)


def create_reviewing_question(event, question_model, wtf_field_cls, form, data=None):
    new_question = question_model()
    new_question.no_score = True
    if 'no_score' in form:
        new_question.no_score = form.no_score.data

    field = wtf_field_cls(new_question)
    field.update_object(form.data)
    form.populate_obj(new_question)
    if data is not None:
        new_question.populate_from_dict(data)
    return new_question


def update_reviewing_question(question, form):
    question.field.update_object(form.data)
    form.populate_obj(question)
    db.session.flush()
    logger.info("Reviewing question %r updated by %r", question, session.user)


def delete_reviewing_question(question):
    question.is_deleted = True
    db.session.flush()
    logger.info("Reviewing question %r deleted by %r", question, session.user)


def sort_reviewing_questions(questions, new_positions):
    questions_by_id = {q.id: q for q in questions}
    for index, new_position in enumerate(new_positions, 0):
        questions_by_id[new_position].position = index
        del questions_by_id[new_position]
    for index, field in enumerate(sorted(questions_by_id.values(), key=attrgetter('position')), len(new_positions)):
        field.position = index
    db.session.flush()
    logger.info("Reviewing questions of %r reordered by %r", questions[0].event, session.user)
