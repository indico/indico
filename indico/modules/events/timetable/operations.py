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
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.sessions.operations import create_session_block
from indico.modules.events.timetable import logger
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.date_time import format_datetime


def _get_object_info(entry):
    if entry.type == TimetableEntryType.CONTRIBUTION:
        object_type = 'contribution'
        object_title = entry.contribution.title
    elif entry.type == TimetableEntryType.SESSION_BLOCK:
        object_type = 'session block'
        object_title = entry.session_block.title or entry.session_block.session.title
    elif entry.type == TimetableEntryType.BREAK:
        object_type = 'break'
        object_title = entry.break_.title
    else:
        raise ValueError('No object associated with timetable entry')
    return object_type, object_title


def create_break_entry(event, data, session_block=None):
    break_ = Break()
    entry_data = {'object': break_,
                  'start_dt': data.pop('start_dt')}
    break_.populate_from_dict(data)
    parent = session_block.timetable_entry if session_block else None
    return create_timetable_entry(event, entry_data, parent=parent)


def create_session_block_entry(session_, data):
    start_dt = data.pop('start_dt')
    block = create_session_block(session_=session_, data=data)
    entry_data = {'object': block, 'start_dt': start_dt}
    return create_timetable_entry(session_.event_new, entry_data)


def create_timetable_entry(event, data, parent=None):
    entry = TimetableEntry(event_new=event, parent=parent)
    entry.populate_from_dict(data)
    object_type, object_title = _get_object_info(entry)
    db.session.flush()
    signals.event.timetable_entry_created.send(entry)
    logger.info('Timetable entry %s created by %s', entry, session.user)
    entry.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Timetable',
                        "Entry for {} '{}' created".format(object_type, object_title), session.user,
                        data={'Time': format_datetime(entry.start_dt)})
    return entry


def schedule_contribution(contribution, start_dt, session_block=None):
    data = {'object': contribution, 'start_dt': start_dt}
    parent = None
    if session_block:
        contribution.session = session_block.session
        contribution.session_block = session_block
        parent = session_block.timetable_entry
    return create_timetable_entry(contribution.event_new, data, parent=parent)


def update_timetable_entry(entry, data):
    entry.populate_from_dict(data)
    object_type, object_title = _get_object_info(entry)
    db.session.flush()
    signals.event.timetable_entry_updated.send(entry)
    logger.info('Timetable entry %s updated by %s', entry, session.user)
    entry.event_new.log(EventLogRealm.management, EventLogKind.change, 'Timetable',
                        "Entry for {} '{}' modified".format(object_type, object_title), session.user,
                        data={'Time': format_datetime(entry.start_dt)})


def delete_timetable_entry(entry, log=True):
    object_type, object_title = _get_object_info(entry)
    signals.event.timetable_entry_deleted.send(entry)
    entry.object = None
    db.session.flush()
    if log:
        logger.info('Timetable entry %s deleted by %s', entry, session.user)
        entry.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Timetable',
                            "Entry for {} '{}' deleted".format(object_type, object_title), session.user,
                            data={'Time': format_datetime(entry.start_dt)})


def fit_session_block_entry(entry, log=True):
    assert entry.type == TimetableEntryType.SESSION_BLOCK
    children = entry.children
    if not children:
        return
    entry.start_dt = min(x.start_dt for x in children)
    end_dt = max(x.end_dt for x in children)
    entry.session_block.duration = end_dt - entry.start_dt
    db.session.flush()
    if log:
        entry.event_new.log(EventLogRealm.management, EventLogKind.change, 'Timetable',
                            "Session block fitted to contents", session.user,
                            data={'Session block': entry.session_block.full_title})
