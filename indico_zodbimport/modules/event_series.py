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

import re
import urlparse
from collections import defaultdict
from itertools import chain

from sqlalchemy.orm import joinedload, load_only

from indico.core.db import db
from indico.modules.attachments import AttachmentFolder
from indico.modules.attachments.models.legacy_mapping import LegacyAttachmentFolderMapping
from indico.modules.events import LegacyEventMapping
from indico.modules.events.models.events import Event
from indico.modules.events.models.series import EventSeries
from indico.util.console import verbose_iterator
from indico.util.string import is_legacy_id
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer


class EventSeriesImporter(Importer):
    def has_data(self):
        return EventSeries.query.has_rows()

    def migrate(self):
        self.migrate_event_series()

    def migrate_event_series(self):
        self.print_step("Migrating event series")
        all_series = self.get_event_series()
        all_series_ids = set(chain.from_iterable(all_series))
        events = {e.id: e for e in Event.find(Event.id.in_(all_series_ids)).options(load_only('id', 'series_id'))}
        for series in committing_iterator(verbose_iterator(all_series, len(all_series), lambda x: 0, lambda x: '')):
            series &= events.viewkeys()
            if len(series) < 2:
                self.print_warning('Skipping single-event series: {}'.format(sorted(series)))
                continue
            es = EventSeries(show_sequence_in_title=False)
            for id_ in series:
                events[id_].series = es
            if not self.quiet:
                self.print_success(repr(series))
        AttachmentFolder.find(AttachmentFolder.title.op('~')('^part\d+$')).update({AttachmentFolder.is_deleted: True},
                                                                                  synchronize_session=False)
        db.session.commit()

    def _extract_event_id(self, link_url):
        parsed_url = urlparse.urlparse(link_url)
        path = parsed_url.path
        query = parsed_url.query
        if query:
            parsed_qs = urlparse.parse_qs(query)
            if not parsed_qs:
                event_id = query
            else:
                event_id = parsed_qs['confId'][0]
            if is_legacy_id(event_id):
                try:
                    event_id = self.legacy_event_mapping[event_id]
                except KeyError:
                    return None
        else:
            match = re.match(r'/(?:event|e)/(?P<event_id>\d+)/material/(?P<material_id>\d+)/?', path)
            if match is not None:
                folder = LegacyAttachmentFolderMapping.find(event_id=match.group('event_id'), contribution_id=None,
                                                            session_id=None, subcontribution_id=None,
                                                            material_id=match.group('material_id')).one().folder
                return self._extract_event_id(folder.attachments[0].link_url)
            match = re.match(r'/(?:event|e)/(?P<event_id>\d+)/?', path)
            if match is None:
                print path
            event_id = match.group('event_id')
        return int(event_id)

    def _extract_event_ids(self, event):
        for folder in self.attachment_folders[event.id]:
            id_ = self._extract_event_id(folder.attachments[0].link_url)
            if id_ is None:
                self.print_warning('Invalid event link: {}'.format(folder.attachments[0].link_url), event_id=event.id)
                continue
            yield id_

    def get_event_series(self):
        self.legacy_event_mapping = {x.legacy_event_id: x.event_id for x in LegacyEventMapping.query}
        self.attachment_folders = defaultdict(set)
        folder_query = (AttachmentFolder.find(AttachmentFolder.linked_event_id.in_({e.id for e in self._events_query}))
                        .filter(AttachmentFolder.title.op('~')('^part\d+$'))
                        .options(joinedload('attachments')))
        for af in folder_query:
            self.attachment_folders[af.linked_event_id].add(af)

        series_list = []
        series_map = {}
        for event in self._events_query:
            series_ids = {event.id} | set(self._extract_event_ids(event))
            series = filter(None, (series_map.get(id_) for id_ in series_ids))
            if not series:
                series_list.append(series_ids)
                for id_ in series_ids:
                    series_map[id_] = series_ids
            else:
                assert len(set(map(frozenset, series))) == 1
                if series[0] != series_ids:
                    self.print_warning('Inconsistent series found; merging them', event_id=event.id)
                    self.print_warning('Series IDs:    {}'.format(sorted(series[0])), event_id=event.id)
                    self.print_warning('Reachable IDs: {}'.format(sorted(series_ids)), event_id=event.id)
                    series[0] |= series_ids
                    for id_ in series_ids:
                        series_map[id_] = series_ids
        return series_list

    @property
    def _events_query(self):
        return Event.find(Event.attachment_folders.any(AttachmentFolder.title.op('~')('^part\d+$')))
