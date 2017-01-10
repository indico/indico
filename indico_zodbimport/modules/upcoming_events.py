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

from __future__ import unicode_literals

from indico.core.db import db
from indico.modules.categories import upcoming_events_settings

from indico_zodbimport import Importer


class UpcomingEventsImporter(Importer):
    def migrate(self):
        self.migrate_settings()

    def migrate_settings(self):
        self.print_step('migrating upcoming events settings')
        mod = self.zodb_root['modules']['upcoming_events']
        upcoming_events_settings.set('max_entries', int(mod._maxEvents))
        entries = [{'weight': float(entry.weight),
                    'days': entry.advertisingDelta.days,
                    'type': 'category' if type(entry.obj).__name__ == 'Category' else 'event',
                    'id': int(entry.obj.id)}
                   for entry in mod._objects]
        upcoming_events_settings.set('entries', entries)
        db.session.commit()
