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

from operator import attrgetter

import transaction

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.util.console import verbose_iterator, cformat
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer


class EventCategoriesImporter(Importer):
    def has_data(self):
        return Event.query.filter(Event.category_id.isnot(None)).has_rows()

    def migrate(self):
        self._load_data()
        self.migrate_event_categories()

    def _load_data(self):
        self.category_mapping = {}
        for category in self.zodb_root['categories'].itervalues():
            self.category_mapping[int(category.id)] = map(int, category.getCategoryPath())

    def migrate_event_categories(self):
        self.print_step("Migrating event categories")
        delete_events = set()
        for conf in committing_iterator(self._iter_events()):
            try:
                category_chain = self.category_mapping[int(conf._Conference__owners[0].id)]
            except (IndexError, KeyError):
                self.print_error(cformat('%{red!}Event has no category!'), event_id=conf.id)
                delete_events.add(int(conf.id))
                continue
            Event.query.filter_by(id=int(conf.id)).update({Event.category_id: category_chain[-1]},
                                                          synchronize_session=False)
            if not self.quiet:
                self.print_success(repr(category_chain), event_id=conf.id)
        for event_id in delete_events:
            self.print_warning(cformat('%{yellow!}Deleting broken event {}').format(event_id))
            Event.query.filter_by(id=event_id).update({Event.is_deleted: True}, synchronize_session=False)
            if self.zodb_root['conferences'].has_key(str(event_id)):
                del self.zodb_root['conferences'][str(event_id)]
        db.session.commit()
        transaction.commit()

    def _iter_events(self):
        it = self.zodb_root['conferences'].itervalues()
        total = len(self.zodb_root['conferences'])
        if self.quiet:
            it = verbose_iterator(it, total, attrgetter('id'), lambda x: x.__dict__.get('title', ''))
        for conf in self.flushing_iterator(it):
            yield conf
