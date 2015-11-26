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

from operator import attrgetter

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.models.events import Event
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.console import cformat, verbose_iterator
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


class TimetableMigration(object):
    def __init__(self, importer, old_event, event):
        self.importer = importer
        self.old_event = old_event
        self.event = event
        self.legacy_session_map = {}
        self.legacy_contribution_map = {}

    def __repr__(self):
        return '<TimetableMigration({})>'.format(self.event)

    def run(self):
        self.importer.print_success('Importing {}'.format(self.old_event), event_id=self.event.id)
        self._migrate_sessions()
        self._migrate_contributions()
        self._migrate_timetable()

    def _migrate_sessions(self):
        for old_session in self.old_event.sessions.itervalues():
            session = Session(event_new=self.event, title=convert_to_unicode(old_session.title),
                              colors=ColorTuple(old_session._textColor, old_session._color),
                              default_contribution_duration=old_session._contributionDuration)
            if not self.importer.quiet:
                self.importer.print_info(cformat('%{blue!}Session%{reset} {}').format(session.title))
            self.legacy_session_map[old_session] = session

    def _migrate_contributions(self):
        for old_contrib in self.old_event.contributions.itervalues():
            contrib = Contribution(event_new=self.event, title=convert_to_unicode(old_contrib.title),
                                   description=convert_to_unicode(old_contrib.description),
                                   duration=old_contrib.duration)
            if not self.importer.quiet:
                self.importer.print_info(cformat('%{cyan}Contribution%{reset} {}').format(contrib.title))
            self.legacy_contribution_map[old_contrib] = contrib
            contrib.subcontributions = [self._migrate_subcontribution(old_subcontrib, pos)
                                        for pos, old_subcontrib in enumerate(old_contrib._subConts, 1)]

    def _migrate_subcontribution(self, old_subcontrib, position):
        subcontrib = SubContribution(position=position, friendly_id=position, duration=old_subcontrib.duration,
                                     title=convert_to_unicode(old_subcontrib.title),
                                     description=convert_to_unicode(old_subcontrib.description))
        if not self.importer.quiet:
            self.importer.print_info(cformat('  %{cyan!}SubContribution%{reset} {}').format(subcontrib.title))
        return subcontrib

    def _migrate_timetable(self):
        self._migrate_timetable_entries(self.old_event._Conference__schedule._entries)

    def _migrate_timetable_entries(self, old_entries, session_block=None):
        for old_entry in old_entries:
            item_type = old_entry.__class__.__name__
            if item_type == 'ContribSchEntry':
                self._migrate_contribution_timetable_entry(old_entry, session_block)
            elif item_type == 'BreakTimeSchEntry':
                self._migrate_break_timetable_entry(old_entry, session_block)
            elif item_type == 'LinkedTimeSchEntry':
                parent = old_entry._LinkedTimeSchEntry__owner
                parent_type = parent.__class__.__name__
                if parent_type == 'Contribution':
                    self.importer.print_warning(cformat('%{yellow!}Found LinkedTimeSchEntry for contribution'),
                                                event_id=self.event.id)
                    self._migrate_contribution_timetable_entry(old_entry, session_block)
                    continue
                elif parent_type != 'SessionSlot':
                    self.importer.print_error(cformat('%{red!}Found LinkedTimeSchEntry for {}').format(parent_type),
                                              event_id=self.event.id)
                    continue
                assert session_block is None
                self._migrate_block_timetable_entry(old_entry)
            else:
                raise ValueError('Unexpected item type: ' + item_type)

    def _migrate_contribution_timetable_entry(self, old_entry, session_block=None):
        old_contrib = old_entry._LinkedTimeSchEntry__owner
        contrib = self.legacy_contribution_map[old_contrib]
        contrib.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_contrib.startDate)
        if session_block:
            contrib.session = session_block.session
            contrib.session_block = session_block
            contrib.timetable_entry.parent = session_block.timetable_entry

    def _migrate_break_timetable_entry(self, old_entry, session_block=None):
        break_ = Break(title=convert_to_unicode(old_entry.title), description=convert_to_unicode(old_entry.description),
                       duration=old_entry.duration)
        break_.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_entry.startDate)
        if session_block:
            break_.timetable_entry.parent = session_block.timetable_entry

    def _migrate_block_timetable_entry(self, old_entry):
        old_block = old_entry._LinkedTimeSchEntry__owner
        session = self.legacy_session_map[old_block.session]
        session_block = SessionBlock(session=session, title=convert_to_unicode(old_block.title),
                                     duration=old_block.duration)
        session_block.timetable_entry = TimetableEntry(event_new=self.event, start_dt=old_block.startDate)
        self._migrate_timetable_entries(old_block._schedule._entries, session_block)


class EventTimetableImporter(Importer):
    def has_data(self):
        models = (TimetableEntry, Break, Session, SessionBlock, Contribution)
        return any(x.has_rows() for x in models)

    def migrate(self):
        self.migrate_events()

    def migrate_events(self):
        for old_event, event in committing_iterator(self._iter_events()):
            mig = TimetableMigration(self, old_event, event)
            with db.session.no_autoflush:
                mig.run()
            db.session.flush()

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        all_events = {e.id: e for e in Event.find_all(is_deleted=False)}
        for old_event in self.flushing_iterator(it):
            event = all_events.get(int(old_event.id))
            if event is None:
                self.print_error(cformat('%{red!}Event is only in ZODB but not in SQL'), event_id=old_event.id)
                continue
            yield old_event, event
