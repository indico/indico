# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from BTrees.OOBTree import OOBTree

from indico.core.index.event import CategoryEventStartDateIndex

from MaKaC.common import DBMgr
from MaKaC.plugins.base import extension_point


# TODO: decorator for annoying 'db parameter'

class Catalog(OOBTree):
    _indexMap = {
        'categ_conf_sd': CategoryEventStartDateIndex
        }

    @classmethod
    def initialize(cls, db=None):
        if not db:
            db = DBMgr.getInstance().getDBConnection()

        catalog = cls()

        for indexName, clazz in cls._iterIndexes():
            newIdx = clazz()
            catalog[indexName] = newIdx

        db.root()['catalog'] = catalog

    @classmethod
    def _iterIndexes(cls):
        for t in cls._indexMap.iteritems():
            yield t

        # ask plugins for their indexes
        for lcomp in extension_point('catalogIndexProvider'):
            for t in lcomp:
                yield t

    @classmethod
    def getIdx(cls, indexName, db=None):
        if not db:
            db = DBMgr.getInstance().getDBConnection()

        if 'catalog' not in db.root():
            cls.initialize(db=db)

        return db.root()['catalog'].get(indexName)

    @classmethod
    def updateDB(cls, dbi=None):
        if not dbi:
            dbi = DBMgr.getInstance()
        db = dbi.getDBConnection()

        root = db.root()

        if not 'catalog' in root:
            cls.initialize(db=db)

        for indexName, clazz in cls._iterIndexes():
            if indexName not in root['catalog']:
                newIdx = clazz()
                root['catalog'][indexName] = newIdx
                newIdx.initialize(dbi=dbi)
