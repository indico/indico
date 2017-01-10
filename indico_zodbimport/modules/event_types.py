# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals, division

from operator import itemgetter

from indico.core.db import db
from indico.modules.events.models.events import Event, EventType
from indico.util.console import verbose_iterator

from indico_zodbimport import Importer


class EventTypeImporter(Importer):
    def has_data(self):
        return Event.query.filter(Event.type_ != EventType.meeting).has_rows()

    def migrate(self):
        self.migrate_event_types()

    def migrate_event_types(self):
        self.print_step("Migrating event types")
        all_event_ids = {x for x, in db.session.query(Event.id)}
        wf_event_ids = {int(x) for x in self.zodb_root['webfactoryregistry'].iterkeys() if x.isdigit()}
        # since most events are meetings all events are meetings by default when the column is created
        # conferences don't have a WF or a None WF
        conference_ids = all_event_ids - wf_event_ids
        lecture_ids = set()
        meeting_count = 0
        for event_id, wf in self._iter_wfs():
            if event_id not in all_event_ids:
                continue
            if wf is None:
                conference_ids.add(event_id)
            elif wf.id == 'simple_event':
                lecture_ids.add(event_id)
            elif wf.id == 'meeting':
                meeting_count += 1
            else:
                self.print_error('Unexpected WF ID: {}'.format(wf.id), event_id=event_id)
        self.print_success('{} lectures'.format(len(lecture_ids)))
        self.print_success('{} meetings'.format(meeting_count))
        self.print_success('{} conferences'.format(len(conference_ids)))
        Event.query.filter(Event.id.in_(lecture_ids)).update({Event.type_: EventType.lecture},
                                                             synchronize_session=False)
        Event.query.filter(Event.id.in_(conference_ids)).update({Event.type_: EventType.conference},
                                                                synchronize_session=False)
        assert Event.query.filter_by(type_=EventType.lecture).count() == len(lecture_ids)
        assert Event.query.filter_by(type_=EventType.meeting).count() == meeting_count
        assert Event.query.filter_by(type_=EventType.conference).count() == len(conference_ids)
        db.session.commit()

    def _iter_wfs(self):
        it = self.zodb_root['webfactoryregistry'].iteritems()
        total = len(self.zodb_root['webfactoryregistry'])
        it = verbose_iterator(it, total, itemgetter(0), lambda x: '')
        for conf_id, wf in it:
            if conf_id.isdigit():
                yield int(conf_id), wf
