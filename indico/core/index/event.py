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

from indico.core.index.base import IOIndex, Index, ElementNotFoundException
from indico.core.index.adapter import IIndexableByStartDateTime
from indico.util.date_time import utc_timestamp
from BTrees.OOBTree import OOSet, OOBTree


class CategoryEventStartDateIndex(Index):

    def __init__(self):
        self._container = OOBTree()
        # add home category by default
        self.add_category('0')

    def __getitem__(self, key):
        return self._container[key]

    def __setitem__(self, key, value):
        self._container[key] = value

    def getCategory(self, categId, create=False):
        if categId not in self._container:
            if create:
                self.add_category(categId)
            else:
                raise KeyError(categId)
        return self._container[categId]

    def add_category(self, categId):
        self._container[categId] =  IOIndex(IIndexableByStartDateTime)

    def index_obj(self, obj):
        try:
            category = self.getCategory(obj.getOwner().getId())
        except KeyError:
            # some legacy events are in categories that don't exist anymore...
            return
        category.index_obj(obj)

    def unindex_obj(self, obj):
        try:
            category = self.getCategory(obj.getOwner().getId())
        except KeyError:
            # some legacy events are in categories that don't exist anymore...
            return
        try:
            category.unindex_obj(obj)
        except ElementNotFoundException:
            # some legacy events are not in this index...
            pass

    def remove_category(self, categId):
        del self._container[categId]

    def _initializeSubIndex(self, cset):
        tsIndex = IOIndex(IIndexableByStartDateTime)
        for conf in cset:
            tsIndex.index_obj(conf)
        return tsIndex

    def initialize(self, dbi=None):
        from MaKaC.conference import CategoryManager

        for cid, categ in CategoryManager()._getIdx().iteritems():
            self[cid] = self._initializeSubIndex(categ.conferences)
            if dbi:
                dbi.commit()

    def _check(self, dbi=None):
        from MaKaC.conference import CategoryManager, ConferenceHolder
        confIdx = ConferenceHolder()._getIdx()
        categIdx = CategoryManager()._getIdx()

        i = 0

        for cid, index in self._container.iteritems():
            # simple data structure check
            for problem in index._check():
                yield problem

            # consistency with CategoryManager
            if cid not in categIdx:
                yield "Category '%s' not in CategoryManager" % cid

            # consistency with ConferenceHolder
            for ts, conf in index.iteritems():
                if conf.getId() not in confIdx:
                    yield "[%s] Conference '%s'(%s) not in ConferenceHolder" \
                          % (cid, conf.getId(), ts)

                if dbi and i % 100 == 99:
                    dbi.abort()

                i += 1
