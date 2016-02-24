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


from __future__ import unicode_literals, division

from datetime import datetime
from operator import attrgetter

import pytz

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.util.console import verbose_iterator
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


class EventDatesTitlesImporter(Importer):
    def has_data(self):
        return bool(Event.query
                    .filter(Event.title.isnot(None) | Event.description.isnot(None) | Event.start_dt.isnot(None) |
                            Event.end_dt.isnot(None) | Event.timezone.isnot(None))
                    .count())

    def migrate(self):
        self.migrate_event_dates_titles()

    def migrate_event_dates_titles(self):
        self.print_step("Migrating event dates and titles")
        for old_event in committing_iterator(self._iter_events()):
            updates = {
                Event.title: convert_to_unicode(old_event.title) or '(no title)',
                Event.description: convert_to_unicode(old_event.description) or '',
                Event.timezone: getattr(old_event, 'timezone', 'UTC'),
                Event.start_dt: old_event.startDate,
                Event.end_dt: old_event.endDate
            }
            Event.query.filter_by(id=int(old_event.id)).update(updates, synchronize_session=False)
            if not self.quiet:
                self.print_success('', event_id=old_event.id)
        updates = {Event.title: '***deleted***',
                   Event.description: '',
                   Event.timezone: 'UTC',
                   Event.start_dt: datetime(1970, 1, 1, tzinfo=pytz.utc),
                   Event.end_dt: datetime(1970, 1, 1, tzinfo=pytz.utc)}
        Event.query.filter_by(is_deleted=True).update(updates, synchronize_session=False)
        db.session.commit()

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        total = len(self.zodb_root['conferences'])
        if self.quiet:
            it = verbose_iterator(it, total, attrgetter('id'), attrgetter('title'))
        for old_event in self.flushing_iterator(it):
            yield old_event
