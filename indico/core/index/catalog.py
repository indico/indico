# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from indico.core.db import DBMgr
from MaKaC.plugins.base import extension_point
from indico.modules.oauth.components import UserOAuthRequestTokenIndex, UserOAuthAccessTokenIndex


# TODO: decorator for annoying 'db parameter'

class Catalog(OOBTree):
    _indexMap = {
        'categ_conf_sd': CategoryEventStartDateIndex,
        'user_oauth_access_token': UserOAuthAccessTokenIndex,
        'user_oauth_request_token': UserOAuthRequestTokenIndex
        }

    @classmethod
    def initialize(cls, db=None, init_indexes=False):
        if not db:
            db = DBMgr.getInstance().getDBConnection()

        catalog = cls()

        for indexName, clazz in cls._iterIndexes():
            newIdx = clazz()
            if init_indexes:
                newIdx.initialize()
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
    def _get_idx_class(cls, index_name):
        if index_name in cls._indexMap:
            return cls._indexMap[index_name]
        else:
            # ask plugins for their indexes
            for lcomp in extension_point('catalogIndexProvider'):
                for t in lcomp:
                    if index_name in t:
                        return t[1]
        return None

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
            cls.initialize(db=db, init_indexes=True)
        else:
            for indexName, clazz in cls._iterIndexes():
                if indexName not in root['catalog']:
                    cls.create_idx(indexName, dbi, clazz)

    @classmethod
    def create_idx(cls, index_name, dbi=None, clazz=None):
        if not dbi:
            dbi = DBMgr.getInstance()
        db = dbi.getDBConnection()

        root = db.root()

        if not clazz:
            clazz = cls._get_idx_class(index_name)

        new_idx = clazz()
        root['catalog'][index_name] = new_idx
        new_idx.initialize(dbi=dbi)
