# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.models.events import EventType
from indico.modules.events.sessions import COORDINATOR_PRIV_SETTINGS, COORDINATOR_PRIV_TITLES, logger, session_settings
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.logs.models.entries import EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import orig_string


def create_session(event, data):
    """Create a new session with the information passed in the `data` argument."""
    event_session = Session(event=event)
    event_session.populate_from_dict(data)
    db.session.flush()
    event.log(EventLogRealm.management, LogKind.positive, 'Sessions',
              f'Session "{event_session.title}" has been created', session.user,
              meta={'session_id': event_session.id})
    logger.info('Session %s created by %s', event_session, session.user)
    return event_session


def create_session_block(session_, data):
    block = SessionBlock(session=session_)
    block.populate_from_dict(data)
    db.session.flush()
    session_.event.log(EventLogRealm.management, LogKind.positive, 'Sessions',
                       f'Session block "{block.title}" for session "{session_.title}" has been created', session.user,
                       meta={'session_block_id': block.id})
    logger.info('Session block %s created by %s', block, session.user)
    return block


def update_session(event_session, data):
    """Update a session based on the information in the `data`."""
    event_session.populate_from_dict(data)
    db.session.flush()
    signals.event.session_updated.send(event_session)
    event_session.event.log(EventLogRealm.management, LogKind.change, 'Sessions',
                            f'Session "{event_session.title}" has been updated', session.user,
                            meta={'session_id': event_session.id})
    logger.info('Session %s modified by %s', event_session, session.user)


def delete_session(event_session):
    """Delete session from the event."""
    event_session.is_deleted = True
    for contribution in event_session.contributions[:]:
        contribution.session = None
    for block in list(event_session.blocks):
        delete_session_block(block, delete_empty_session=False, log=False)
    signals.event.session_deleted.send(event_session)
    event_session.event.log(EventLogRealm.management, LogKind.negative, 'Sessions',
                            f'Session "{event_session.title}" has been deleted', session.user,
                            meta={'session_id': event_session.id})
    logger.info('Session %s deleted by %s', event_session, session.user)


def update_session_block(session_block, data):
    """Update a session block with data passed in the `data` argument."""
    from indico.modules.events.timetable.operations import update_timetable_entry

    start_dt = data.pop('start_dt', None)
    if start_dt is not None:
        session_block.timetable_entry.move(start_dt)
        update_timetable_entry(session_block.timetable_entry, {'start_dt': start_dt})
    session_block.populate_from_dict(data)
    db.session.flush()
    signals.event.session_block_updated.send(session_block)
    session_block.event.log(EventLogRealm.management, LogKind.change, 'Sessions',
                            f'Session block "{session_block.title}" has been updated', session.user,
                            meta={'session_block_id': session_block.id})
    logger.info('Session block %s modified by %s', session_block, session.user)


def delete_session_block(session_block, *, delete_empty_session=True, log=True):
    from indico.modules.events.contributions.operations import delete_contribution
    from indico.modules.events.timetable.operations import delete_timetable_entry
    session_ = session_block.session
    unschedule_contribs = session_.event.type_ == EventType.conference
    for contribution in session_block.contributions[:]:
        contribution.session_block = None
        if unschedule_contribs:
            delete_timetable_entry(contribution.timetable_entry, log=False)
        else:
            delete_contribution(contribution)
    for entry in session_block.timetable_entry.children[:]:
        delete_timetable_entry(entry, log=False)
    delete_timetable_entry(session_block.timetable_entry, log=False)
    signals.event.session_block_deleted.send(session_block)
    if session_block in session_.blocks:
        session_.blocks.remove(session_block)
    if delete_empty_session and not session_.blocks and session_.event.type_ != EventType.conference:
        delete_session(session_)
    db.session.flush()
    if log:
        session_.event.log(EventLogRealm.management, LogKind.negative, 'Sessions',
                           f'Session block "{session_block.title}" has been deleted', session.user,
                           meta={'session_block_id': session_block.id})
        logger.info('Session block %s deleted by %s', session_block, session.user)


def update_session_coordinator_privs(event, data):
    changes = {}
    for priv, enabled in data.items():
        setting = COORDINATOR_PRIV_SETTINGS[priv]
        if session_settings.get(event, setting) == enabled:
            continue
        session_settings.set(event, setting, enabled)
        changes[priv] = (not enabled, enabled)
    db.session.flush()
    logger.info('Session coordinator privs of event %r updated with %r by %r', event, data, session.user)
    if changes:
        log_fields = {priv: orig_string(title) for priv, title in COORDINATOR_PRIV_TITLES.items()}
        event.log(EventLogRealm.management, LogKind.change, 'Sessions', 'Coordinator privileges updated',
                  session.user, data={'Changes': make_diff_log(changes, log_fields)})
