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

from indico.core.db import db
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.timetable import logger
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


def create_timetable_entry(event, data):
    entry = TimetableEntry(event_new=event)
    entry.populate_from_dict(data)
    object_type, object_title = _get_object_info(entry)
    db.session.flush()
    logger.info('Timetable entry %s created by %s', entry, session.user)
    entry.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Timetable',
                        "Entry for {} '{}' created".format(object_type, object_title), session.user,
                        data={'Time': format_datetime(entry.start_dt)})
    return entry


def update_timetable_entry(entry, data):
    entry.populate_from_dict(data)
    object_type, object_title = _get_object_info(entry)
    db.session.flush()
    logger.info('Timetable entry %s updated by %s', entry, session.user)
    entry.event_new.log(EventLogRealm.management, EventLogKind.change, 'Timetable',
                        "Entry for {} '{}' modified".format(object_type, object_title), session.user,
                        data={'Time': format_datetime(entry.start_dt)})
