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
from indico.modules.events import Event
from indico.util.console import verbose_iterator
from indico.util.struct.iterables import committing_iterator
from indico_zodbimport import Importer


class EventStubImporter(Importer):
    def has_data(self):
        return Event.query.has_rows()

    def migrate(self):
        self.migrate_event_stubs()
        self.fix_sequences('events', {'events'})

    def migrate_event_stubs(self):
        self.print_step('migrating event stubs')
        for event_id in committing_iterator(self._iter_event_ids(), 5000):
            db.session.add(Event(id=int(event_id)))

    def _iter_event_ids(self):
        it = iter(self.zodb_root['conferences'])
        return verbose_iterator(it, len(self.zodb_root['conferences']), lambda x: x, lambda x: 'n/a', 1000)
