# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import attrgetter

from flask import g, session

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.categories.models.event_move_request import EventMoveRequest
from indico.modules.categories.util import format_visibility
from indico.modules.events import Event, EventLogRealm, logger
from indico.modules.events.cloning import EventCloner, get_event_cloners
from indico.modules.events.features import features_event_settings
from indico.modules.events.layout import layout_settings
from indico.modules.events.management.settings import privacy_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.util import format_log_person, format_log_ref, split_log_location_changes
from indico.modules.logs.models.entries import CategoryLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import orig_string
from indico.util.signals import make_interceptable


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
    if category is None:
        # don't allow setting a protection mode on unlisted events; we
        # keep the inheriting default
        data.pop('protection_mode', None)
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
    sep = ' \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK} '
    event.log(EventLogRealm.event, LogKind.positive, 'Event', 'Event created', session.user,
              data={'Category': sep.join(category.chain_titles) if category else None})
    if category:
        category.log(CategoryLogRealm.events, LogKind.positive, 'Content', f'Event created: "{event.title}"',
                     session.user, data={'ID': event.id, 'Type': orig_string(event.type_.title)})
    db.session.flush()
    if create_booking:
        room_id = data['location_data'].pop('room_id', None)
        if room_id:
            booking = create_booking_for_event(room_id, event)
            if booking:
                logger.info('Booking %r created for event %r', booking, event)
                log_data = {'Room': booking.room.full_name,
                            'Date': booking.start_dt.strftime('%d/%m/%Y'),
                            'Times': '{} - {}'.format(booking.start_dt.strftime('%H:%M'),
                                                      booking.end_dt.strftime('%H:%M'))}
                event.log(EventLogRealm.event, LogKind.positive, 'Event', 'Room booked for the event',
                          session.user, data=log_data)
                db.session.flush()
    return event


@make_interceptable
@no_autoflush
def update_event(event, *, update_timetable=False, _extra_log_fields=None, **data):
    old_person_links = event.sorted_person_links[:]
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
    # we don't have proper change tracking there in some cases
    changes.pop('person_link_data', None)
    visible_person_link_changes = event.sorted_person_links != old_person_links
    if visible_person_link_changes or 'person_link_data' in data:
        changes['person_links'] = (old_person_links, event.sorted_person_links)
    db.session.flush()
    signals.event.updated.send(event, changes=changes)
    logger.info('Event %r updated with %r by %r', event, data, session.user)
    _log_event_update(event, changes, _extra_log_fields, visible_person_link_changes=visible_person_link_changes)


def clone_event(event, n_occurrence, start_dt, cloners, category=None, refresh_users=False):
    """Clone an event on a given date/time.

    Runs all required cloners.

    :param n_occurrence: The 1-indexed number of the occurrence, if this is a "recurring" clone, otherwise `0`
    :param start_dt: The start datetime of the new event;
    :param cloners: A set containing the names of all enabled cloners;
    :param category: The `Category` the new event will be created in.
    :aparam refresh_users: Whether `EventPerson` data should be updated from
                           their linked `User` object
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
    if refresh_users:
        new_event.refresh_event_persons(notify=False)
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
    g.importing_event = True
    used_cloners = EventCloner.run_cloners(source_event, target_event, cloners, event_exists=True)
    del g.importing_event
    signals.event.imported.send(target_event, source_event=source_event)
    cloner_classes = {c.name: c for c in get_event_cloners().values()}
    target_event.log(EventLogRealm.event, LogKind.change, 'Event', 'Data imported', session.user,
                     data={'Modules': ', '.join(orig_string(used_cloners[c].friendly_name)
                                                for c in cloners if not cloner_classes[c].is_internal)})

    return target_event


def _log_event_update(event, changes, extra_log_fields, visible_person_link_changes=False):
    log_fields = {
        'title': {'title': 'Title', 'type': 'string'},
        'description': 'Description',
        'url_shortcut': {'title': 'URL Shortcut', 'type': 'string'},
        'address': 'Address',
        'venue_room': {'title': 'Location', 'type': 'string'},
        'keywords': 'Keywords',
        'references': {
            'title': 'External IDs',
            'convert': lambda changes: [list(map(format_log_ref, refs)) for refs in changes]
        },
        'person_links': {
            'title': 'Speakers' if event.type_ == EventType.lecture else 'Chairpersons',
            'convert': lambda changes: [list(map(format_log_person, persons)) for persons in changes]
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
        'own_map_url': {'title': 'Map URL', 'type': 'string'},
        'supported_locales': 'Supported languages',
        'default_locale': 'Default language',
        'enforce_locale': 'Enforce language',
        **(extra_log_fields or {})
    }
    split_log_location_changes(changes)
    if not visible_person_link_changes:
        # Don't log a person link change with no visible changes (changes
        # on an existing link or reordering). It would look quite weird in
        # the event log.
        # TODO: maybe use a separate signal for such changes to log them
        # anyway and allow other code to act on them?
        changes.pop('person_links', None)
    if changes:
        if set(changes.keys()) <= {'timezone', 'start_dt', 'end_dt', 'start_dt_override', 'end_dt_override'}:
            what = 'Dates'
        elif len(changes) == 1:
            what = log_fields[list(changes.keys())[0]]
            if isinstance(what, dict):
                what = what['title']
        else:
            what = 'Data'
        event.log(EventLogRealm.management, LogKind.change, 'Event', f'{what} updated', session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})


@make_interceptable
def update_event_protection(event, data, *, _extra_log_fields=None):
    changes = event.populate_from_dict(data)
    db.session.flush()
    signals.event.updated.send(event, changes=changes)
    logger.info('Protection of event %r updated with %r by %r', event, data, session.user)
    if changes:
        log_fields = {'protection_mode': 'Protection mode',
                      'own_no_access_contact': 'No access contact',
                      'access_key': {'title': 'Access key', 'type': 'string'},
                      'visibility': {'title': 'Visibility', 'type': 'string',
                                     'convert': lambda changes: [format_visibility(event, x) for x in changes]},
                      'public_regform_access': 'Public registration form access',
                      'subcontrib_speakers_can_submit': 'Subcontribution speakers submission privileges',
                      **(_extra_log_fields or {})}
        event.log(EventLogRealm.management, LogKind.change, 'Event', 'Protection updated', session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})


def update_event_type(event, type_):
    if event.type_ == type_:
        return
    event.type_ = type_
    logger.info('Event %r type changed to %s by %r', event, type_.name, session.user)
    event.log(EventLogRealm.event, LogKind.change, 'Event', f'Type changed to {type_.title}', session.user)


def lock_event(event):
    event.is_locked = True
    db.session.flush()
    logger.info('Event %r locked by %r', event, session.user)
    event.log(EventLogRealm.event, LogKind.change, 'Event', 'Event locked', session.user)


def unlock_event(event):
    event.is_locked = False
    db.session.flush()
    logger.info('Event %r unlocked by %r', event, session.user)
    event.log(EventLogRealm.event, LogKind.change, 'Event', 'Event unlocked', session.user)


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
    logger.info('Reviewing question %r updated by %r', question, session.user)


def delete_reviewing_question(question):
    question.is_deleted = True
    db.session.flush()
    logger.info('Reviewing question %r deleted by %r', question, session.user)


def sort_reviewing_questions(questions, new_positions):
    questions_by_id = {q.id: q for q in questions}
    for index, new_position in enumerate(new_positions, 0):
        questions_by_id[new_position].position = index
        del questions_by_id[new_position]
    for index, field in enumerate(sorted(questions_by_id.values(), key=attrgetter('position')), len(new_positions)):
        field.position = index
    db.session.flush()
    logger.info('Reviewing questions of %r reordered by %r', questions[0].event, session.user)


def create_event_request(event, category, comment=''):
    assert event.category != category
    if event.pending_move_request:
        event.pending_move_request.withdraw()
    req = EventMoveRequest(event=event, category=category, requestor=session.user, requestor_comment=comment)
    db.session.flush()
    logger.info('Category move request %r to %r created by %r', req, category, session.user)
    sep = ' \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK} '
    verb = 'move' if event.category else 'publish'
    event.log(EventLogRealm.event, LogKind.change, 'Category', f'{verb.capitalize()} to "{category.title}" requested',
              user=session.user, data={'Category ID': category.id, 'Category': sep.join(category.chain_titles),
                                       'Comment': comment},
              meta={'event_move_request_id': req.id})
    category_log_data = {'Event ID': event.id}
    if event.category:
        category_log_data['From'] = sep.join(event.category.chain_titles)
    category.log(CategoryLogRealm.events, LogKind.positive, 'Moderation', f'Event {verb} requested: "{event.title}"',
                 session.user, data=category_log_data, meta={'event_move_request_id': req.id})
    return req


def update_event_privacy(event, data):
    log_fields = {
        'data_controller_name': {'title': 'Data controller name', 'type': 'string'},
        'data_controller_email': {'title': 'Data controller e-mail', 'type': 'string'},
        'privacy_policy_urls': {
            'title': 'Privacy policy URLs',
            'type': 'struct_list',
            'convert': lambda changes: [[dict(sorted(rec.items())) for rec in chg] for chg in changes]
        },
        'privacy_policy': {'title': 'Privacy policy', 'type': 'text'}
    }
    assert set(data.keys()) <= log_fields.keys()
    changes = {}
    for key, value in data.items():
        old_value = privacy_settings.get(event, key)
        if old_value != value:
            changes[key] = (old_value, value)
    privacy_settings.set_multi(event, data)
    logger.info('Privacy settings of event %r updated with %r by %r', event, data, session.user)
    if changes:
        event.log(EventLogRealm.management, LogKind.change, 'Event', 'Privacy settings updated', session.user,
                  data={'Changes': make_diff_log(changes, log_fields)})
