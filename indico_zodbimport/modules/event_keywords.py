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

from operator import attrgetter

from indico.modules.events.models.events import Event
from indico.util.console import verbose_iterator
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


class EventKeywordsImporter(Importer):
    def migrate(self):
        self.migrate_event_keywords()

    def migrate_event_keywords(self):
        self.print_step("Migrating event keywords")
        for old_event in committing_iterator(self._iter_events()):
            old_keywords = old_event._keywords
            keywords = filter(None, map(unicode.strip, map(convert_to_unicode, old_keywords.splitlines())))
            if not keywords:
                continue
            Event.query.filter_by(id=int(old_event.id)).update({Event.keywords: keywords}, synchronize_session=False)
            if not self.quiet:
                self.print_success(repr(keywords), event_id=old_event.id)

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        total = len(self.zodb_root['conferences'])
        if self.quiet:
            it = verbose_iterator(it, total, attrgetter('id'), lambda x: '')
        for old_event in self.flushing_iterator(it):
            yield old_event
