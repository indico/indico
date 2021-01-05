# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.orm import defaultload, joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.i18n import _


class TimetableCloner(EventCloner):
    name = 'timetable'
    friendly_name = _('Timetable')
    requires = {'sessions', 'contributions'}

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    @property
    def is_default(self):
        return self.old_event.type_ == EventType.meeting

    @property
    def is_visible(self):
        return self.old_event.type_ in {EventType.meeting, EventType.conference}

    def has_conflicts(self, target_event):
        return self._has_content(target_event) or self.old_event.duration > target_event.duration

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._session_block_map = shared_data['sessions']['session_block_map']
        self._contrib_map = shared_data['contributions']['contrib_map']
        with db.session.no_autoflush:
            self._clone_timetable(new_event)
        db.session.flush()

    def _has_content(self, event):
        return event.timetable_entries.has_rows()

    def _clone_timetable(self, new_event):
        offset = new_event.start_dt - self.old_event.start_dt
        # no need to copy the type; it's set automatically based on the object
        attrs = get_simple_column_attrs(TimetableEntry) - {'type', 'start_dt'}
        break_strategy = defaultload('break_')
        break_strategy.joinedload('own_venue')
        break_strategy.joinedload('own_room').lazyload('*')
        entry_key_order = db.case({
            TimetableEntryType.SESSION_BLOCK: db.func.concat('s', TimetableEntry.id),
            TimetableEntryType.CONTRIBUTION: db.func.concat('c', TimetableEntry.id),
            TimetableEntryType.BREAK: db.func.concat('b', TimetableEntry.id),
        }, value=TimetableEntry.type)
        query = (self.old_event.timetable_entries
                 .options(joinedload('parent').lazyload('*'),
                          break_strategy)
                 .order_by(TimetableEntry.parent_id.is_(None).desc(), entry_key_order))
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
