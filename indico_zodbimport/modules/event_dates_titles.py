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
        return (Event.query
                .filter(Event.title.isnot(None) | Event.description.isnot(None) | Event.start_dt.isnot(None) |
                        Event.end_dt.isnot(None) | Event.timezone.isnot(None))
                .has_rows())

    def migrate(self):
        self.migrate_event_dates_titles()

    def migrate_event_dates_titles(self):
        self.print_step("Migrating event dates and titles")
        for old_event in committing_iterator(self._iter_events()):
            if 'title' not in old_event.__dict__:
                self.print_error('Event has no title in ZODB', old_event.id)
                continue
            tz = old_event.__dict__.get('timezone', 'UTC')
            updates = {
                Event.title: convert_to_unicode(old_event.__dict__['title']) or '(no title)',
                Event.description: convert_to_unicode(old_event.__dict__['description']) or '',
                Event.timezone: tz,
                Event.start_dt: self._fix_naive(old_event, old_event.__dict__['startDate'], tz),
                Event.end_dt: self._fix_naive(old_event, old_event.__dict__['endDate'], tz)
            }
            Event.query.filter_by(id=int(old_event.id)).update(updates, synchronize_session=False)
            if not self.quiet:
                self.print_success('', event_id=old_event.id)

        # deleted events are not in zodb but also need data
        updates = {Event.title: '***deleted***',
                   Event.description: '',
                   Event.timezone: 'UTC',
                   Event.start_dt: datetime(1970, 1, 1, tzinfo=pytz.utc),
                   Event.end_dt: datetime(1970, 1, 1, tzinfo=pytz.utc)}
        Event.query.filter_by(is_deleted=True).update(updates, synchronize_session=False)
        db.session.commit()

    def _iter_events(self):
        def _it():
            for conf in self.zodb_root['conferences'].itervalues():
                dir(conf)  # make zodb load attrs
                yield conf
        it = _it()
        total = len(self.zodb_root['conferences'])
        if self.quiet:
            it = verbose_iterator(it, total, attrgetter('id'), lambda x: x.__dict__.get('title', ''))
        for old_event in self.flushing_iterator(it):
            yield old_event

    def _fix_naive(self, old_event, dt, tz):
        if dt.tzinfo is None:
            self.print_warning('Naive datetime converted ({})'.format(dt), old_event.id)
            return pytz.timezone(tz).localize(dt)
        else:
            return dt
