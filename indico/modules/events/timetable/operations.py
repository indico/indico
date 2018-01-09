# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from indico.core.errors import UserValueError
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.sessions.operations import update_session_block
from indico.modules.events.timetable import logger
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.timetable.util import find_latest_entry_end_dt
from indico.util.date_time import format_datetime
from indico.util.i18n import _


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
    return create_timetable_entry(event, entry_data, parent=parent, extend_parent=True)


def update_break_entry(break_, data):
    start_dt = data.pop('start_dt', None)
    if start_dt is not None:
        update_timetable_entry(break_.timetable_entry, {'start_dt': start_dt})
    break_.populate_from_dict(data)


def create_session_block_entry(session_, data):
    from indico.modules.events.sessions.operations import create_session_block

    start_dt = data.pop('start_dt')
    block = create_session_block(session_=session_, data=data)
    entry_data = {'object': block, 'start_dt': start_dt}
    return create_timetable_entry(session_.event, entry_data, extend_parent=True)


def create_timetable_entry(event, data, parent=None, extend_parent=False):
    entry = TimetableEntry(event=event, parent=parent)
    entry.populate_from_dict(data)
    object_type, object_title = _get_object_info(entry)
    db.session.flush()
    signals.event.timetable_entry_created.send(entry)
    logger.info('Timetable entry %s created by %s', entry, session.user)
    entry.event.log(EventLogRealm.management, EventLogKind.positive, 'Timetable',
                    "Entry for {} '{}' created".format(object_type, object_title), session.user,
                    data={'Time': format_datetime(entry.start_dt)})
    if extend_parent:
        entry.extend_parent()
    return entry


def schedule_contribution(contribution, start_dt, session_block=None, extend_parent=False):
    data = {'object': contribution, 'start_dt': start_dt}
    parent = None
    if session_block:
        contribution.session = session_block.session
        contribution.session_block = session_block
        parent = session_block.timetable_entry
    entry = create_timetable_entry(contribution.event, data, parent=parent, extend_parent=extend_parent)
    return entry


def update_timetable_entry(entry, data):
    changes = entry.populate_from_dict(data)
    object_type, object_title = _get_object_info(entry)
    db.session.flush()
    if changes:
        signals.event.timetable_entry_updated.send(entry, changes=changes)
        logger.info('Timetable entry %s updated by %s', entry, session.user)
        entry.event.log(EventLogRealm.management, EventLogKind.change, 'Timetable',
                        "Entry for {} '{}' modified".format(object_type, object_title), session.user,
                        data={'Time': format_datetime(entry.start_dt)})


def delete_timetable_entry(entry, log=True):
    object_type, object_title = _get_object_info(entry)
    signals.event.timetable_entry_deleted.send(entry)
    entry.object = None
    db.session.flush()
    if log:
        logger.info('Timetable entry %s deleted by %s', entry, session.user)
        entry.event.log(EventLogRealm.management, EventLogKind.negative, 'Timetable',
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
        entry.event.log(EventLogRealm.management, EventLogKind.change, 'Timetable',
                        "Session block fitted to contents", session.user,
                        data={'Session block': entry.session_block.full_title})


def move_timetable_entry(entry, parent=None, day=None):
    """Move the `entry` to another session or top-level timetable

    :param entry: `TimetableEntry` to be moved
    :param parent: If specified then the entry will be set as a child
                         of parent
    :param day: If specified then the entry will be moved to the
                        top-level timetable on this day
    """
    if bool(parent) + bool(day) != 1:
        raise TypeError("Wrong number of arguments")

    from indico.modules.events.contributions.operations import update_contribution

    updates = {}
    contrib_update_data = {}
    if day:
        new_start_dt = entry.start_dt.replace(day=day.day, month=day.month)
        updates['start_dt'] = new_start_dt
        updates['parent'] = None
        contrib_update_data = {'session_id': None, 'session_block_id': None}
    elif parent:
        new_start_dt = find_latest_entry_end_dt(parent.object) or parent.start_dt
        tz = entry.event.tzinfo
        if (new_start_dt + entry.duration).astimezone(tz).date() != parent.start_dt.astimezone(tz).date():
            raise UserValueError(_('Session block cannot span more than one day'))
        updates['parent'] = parent
        updates['start_dt'] = new_start_dt
        contrib_update_data = {'session': parent.session_block.session, 'session_block': parent.session_block}

    update_timetable_entry(entry, updates)
    if entry.type == TimetableEntryType.CONTRIBUTION:
        update_contribution(entry.object, contrib_update_data)
    if parent and entry.end_dt > parent.end_dt:
        duration = parent.object.duration + (entry.end_dt - parent.end_dt)
        update_session_block(parent.object, {'duration': duration})


def update_timetable_entry_object(entry, data):
    """Update the `object` of a timetable entry according to its type"""
    from indico.modules.events.contributions.operations import update_contribution
    obj = entry.object
    if entry.type == TimetableEntryType.CONTRIBUTION:
        update_contribution(obj, data)
    elif entry.type == TimetableEntryType.SESSION_BLOCK:
        update_session_block(obj, data)
    elif entry.type == TimetableEntryType.BREAK:
        obj.populate_from_dict(data)
    db.session.flush()


def swap_timetable_entry(entry, direction, session_=None):
    """Swap entry with closest gap or non-parallel sibling"""
    in_session = session_ is not None
    sibling = get_sibling_entry(entry, direction=direction, in_session=in_session)
    if not sibling:
        return
    if direction == 'down':
        if entry.end_dt != sibling.start_dt:
            entry.move_next_to(sibling, position='before')
        elif not sibling.is_parallel(in_session=in_session):
            sibling.move(entry.start_dt)
            entry.move(sibling.end_dt)
    elif direction == 'up':
        if entry.start_dt != sibling.end_dt:
            entry.move_next_to(sibling, position='after')
        elif not sibling.is_parallel(in_session=in_session):
            entry.move(sibling.start_dt)
            sibling.move(entry.end_dt)


def can_swap_entry(entry, direction, in_session=False):
    sibling = get_sibling_entry(entry, direction=direction, in_session=in_session)
    if not sibling:
        return False
    if direction == 'down':
        return entry.end_dt != sibling.start_dt or not sibling.is_parallel(in_session=in_session)
    elif direction == 'up':
        return entry.start_dt != sibling.end_dt or not sibling.is_parallel(in_session=in_session)


def get_sibling_entry(entry, direction, in_session=False):
    siblings = entry.siblings if not in_session else entry.session_siblings
    if direction == 'down':
        siblings = [x for x in siblings if x.start_dt >= entry.end_dt]
        return min(siblings, key=attrgetter('start_dt')) if siblings else None
    elif direction == 'up':
        siblings = [x for x in siblings if x.end_dt <= entry.start_dt]
        return max(siblings, key=attrgetter('end_dt')) if siblings else None
