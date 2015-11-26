# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db
from indico.util.console import cformat
from indico.modules.events.models.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry

from indico_zodbimport import Importer


class EventTimetableImporter(Importer):
    def has_data(self):
        pass

    def migrate(self):
        self.migrate_timetable()

    def migrate_timetable(self):
        print cformat('%{white!}migrating timetable')

        event = self.zodb_root['conferences']['304944']
        event_new = Event.get(event.id)
        legacy_session_mapping = {}

        # Import sessions
        for legacy_session in event.sessions.itervalues():
            session = Session(event_new=event_new, title=legacy_session.title,
                              colors=(legacy_session._textColor, legacy_session._color),
                              default_contribution_duration=legacy_session._contributionDuration)
            event_new.sessions.append(session)
            legacy_session_mapping[legacy_session] = session
            self.print_success(cformat('- %{cyan}[Session] {}').format(session.title), event_id=event.id)

        # Import session blocks and breaks
        self._process_entries(event._Conference__schedule._entries, event_new, legacy_session_mapping)

        db.session.flush()
        db.session.commit()

    def _process_entries(self, entries, event_new, legacy_session_mapping, session_block=None):
        for entry in entries:
            item_type = getattr(entry, 'ITEM_TYPE', None)
            if item_type and item_type == 'contribution':
                # Contribution
                legacy_contrib = entry._LinkedTimeSchEntry__owner
                contribution = Contribution(title=legacy_contrib.title, description=legacy_contrib.description,
                                            duration=legacy_contrib.duration, event_new=event_new)
                tt_entry = TimetableEntry(event_new=event_new, start_dt=legacy_contrib.startDate,
                                          contribution=contribution)
                if session_block:
                    contribution.session = session_block.session
                    contribution.session_block = session_block
                    tt_entry.parent = session_block.timetable_entry

                event_new.timetable_entries.append(tt_entry)
                self.print_success(cformat('- %{yellow}[Contribution] {}').format(contribution.title),
                                   event_id=event_new.id)
            elif item_type and item_type == 'break':
                # Break
                break_ = Break(title=entry.title, description=entry.description, duration=entry.duration)
                tt_entry = TimetableEntry(event_new=event_new, break_=break_, start_dt=entry.startDate)
                if session_block:
                    tt_entry.parent = session_block.timetable_entry
                self.print_success(cformat('- %{white}[Break] {}').format(break_.title), event_id=event_new.id)
            else:
                # Session block
                legacy_block = entry._LinkedTimeSchEntry__owner
                parent_session = legacy_session_mapping[legacy_block.session]
                block = SessionBlock(session=parent_session, title=legacy_block.title, duration=legacy_block.duration)
                tt_entry = TimetableEntry(event_new=event_new, session_block=block, start_dt=legacy_block.startDate)
                parent_session.blocks.append(block)
                self.print_success(cformat('- %{red}[Session block] {}').format(block.title), event_id=event_new.id)

                # Import session block timetable entries
                self._process_entries(legacy_block._schedule._entries, event_new, legacy_session_mapping,
                                      session_block=block)
