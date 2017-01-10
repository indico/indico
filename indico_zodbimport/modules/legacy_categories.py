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

from operator import attrgetter

import transaction

from indico.core.db import db
from indico.modules.categories.models.legacy_mapping import LegacyCategoryMapping
from indico.util.console import cformat, verbose_iterator
from indico.util.string import is_legacy_id
from indico_zodbimport import Importer


class LegacyCategoryImporter(Importer):
    def has_data(self):
        return LegacyCategoryMapping.query.has_rows()

    def migrate(self):
        self.migrate_legacy_categories()

    def migrate_legacy_categories(self):
        print cformat('%{white!}migrating legacy categories')

        indexes = [self.zodb_root['categories'], self.zodb_root['catalog']['categ_conf_sd']._container]
        indexes += [self.zodb_root['indexes'][x]._idxCategItem for x in ('category', 'categoryDate', 'categoryDateAll')]
        mapping = {}

        for categ in self._committing_iterator(self._get_categories()):
            if not hasattr(categ, '_old_id'):
                new_id = self.gen_categ_id()
                index_data = [idx.pop(categ.id, None) for idx in indexes]
                categ._old_id = categ.id
                categ.id = new_id
                for idx, data in zip(indexes, index_data):
                    assert categ.id not in idx
                    if data is not None:
                        idx[categ.id] = data
                self.zodb_root['categories'][categ.id] = categ
                FavoriteCategory.find(target_id=categ._old_id).update({FavoriteCategory.target_id: categ.id})
                db.session.add(LegacyCategoryMapping(legacy_category_id=categ._old_id, category_id=int(categ.id)))
                print cformat('%{green}+++%{reset} '
                              '%{white!}{:6s}%{reset} %{cyan}{}').format(categ._old_id, int(categ.id))
            else:
                # happens if this importer was executed before but you want to add the mapping to your DB again
                db.session.add(LegacyCategoryMapping(legacy_category_id=categ._old_id, category_id=int(categ.id)))
                msg = cformat('%{green}+++%{reset} '
                              '%{white!}{:6s}%{reset} %{cyan}{}%{reset} %{yellow}(already updated in zodb)')
                print msg.format(categ._old_id, int(categ.id))
            mapping[categ._old_id] = categ.id

        print cformat('%{white!}fixing subcategory lists')
        for categ in self._committing_iterator(self.flushing_iterator(self.zodb_root['categories'].itervalues())):
            for subcateg_id in categ.subcategories.keys():
                new_id = mapping.get(subcateg_id)
                if new_id is not None:
                    categ.subcategories[new_id] = categ.subcategories.pop(subcateg_id)
                    categ._p_changed = True

    def gen_categ_id(self):
        counter = self.zodb_root['counters']['CATEGORY']
        rv = str(counter._Counter__count)
        counter._Counter__count += 1
        return rv

    def _get_categories(self):
        # we modify the categories dict so we can't iterate over it while doing so
        cats = self.flushing_iterator(self.zodb_root['categories'].itervalues())
        cats = verbose_iterator(cats, len(self.zodb_root['categories']), attrgetter('id'), attrgetter('name'))
        return [cat for cat in cats if is_legacy_id(cat.id) or hasattr(cat, '_old_id')]

    def _committing_iterator(self, iterable):
        for i, data in enumerate(iterable, 1):
            yield data
            if i % 500 == 0:
                db.session.commit()
                transaction.commit()
        db.session.commit()
        transaction.commit()
