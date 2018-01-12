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

from sqlalchemy.orm import defaultload, joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.i18n import _


class TimetableCloner(EventCloner):
    name = 'timetable'
    friendly_name = _('Timetable')
    requires = {'sessions', 'contributions'}

    @property
    def is_available(self):
        return bool(self.old_event.timetable_entries.count())

    @property
    def is_default(self):
        return self.old_event.type_ == EventType.meeting

    @property
    def is_visible(self):
        return self.old_event.type_ in {EventType.meeting, EventType.conference}

    def run(self, new_event, cloners, shared_data):
        self._session_block_map = shared_data['sessions']['session_block_map']
        self._contrib_map = shared_data['contributions']['contrib_map']
        with db.session.no_autoflush:
            self._clone_timetable(new_event)
        db.session.flush()

    def _clone_timetable(self, new_event):
        offset = new_event.start_dt - self.old_event.start_dt
        # no need to copy the type; it's set automatically based on the object
        attrs = get_simple_column_attrs(TimetableEntry) - {'type', 'start_dt'}
        break_strategy = defaultload('break_')
        break_strategy.joinedload('own_venue')
        break_strategy.joinedload('own_room').lazyload('*')
        query = (self.old_event.timetable_entries
                 .options(joinedload('parent').lazyload('*'),
                          break_strategy)
                 .order_by(TimetableEntry.parent_id.is_(None).desc()))
        # iterate over all timetable entries; start with top-level
        # ones so we can build a mapping that can be used once we
        # reach nested entries
        entry_map = {}
        for old_entry in query:
            entry = TimetableEntry()
            entry.start_dt = old_entry.start_dt + offset
            entry.populate_from_attrs(old_entry, attrs)
            if old_entry.parent is not None:
                entry.parent = entry_map[old_entry.parent]
            if old_entry.session_block is not None:
                entry.session_block = self._session_block_map[old_entry.session_block]
            if old_entry.contribution is not None:
                entry.contribution = self._contrib_map[old_entry.contribution]
            if old_entry.break_ is not None:
                entry.break_ = self._clone_break(old_entry.break_)
            new_event.timetable_entries.append(entry)
            entry_map[old_entry] = entry

    def _clone_break(self, old_break):
        attrs = get_simple_column_attrs(Break) | {'own_room', 'own_venue'}
        break_ = Break()
        break_.populate_from_attrs(old_break, attrs)
        return break_
