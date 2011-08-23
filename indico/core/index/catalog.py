# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from BTrees.OOBTree import OOBTree

from indico.core.index.event import CategoryEventStartDateIndex

from MaKaC.common import DBMgr


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

        for indexName, clazz in cls._indexMap.iteritems():
            newIdx = clazz()
            catalog[indexName] = newIdx

        db.root()['catalog'] = catalog

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

        for indexName, clazz in cls._indexMap.iteritems():
            newIdx = clazz()
            root['catalog'][indexName] = newIdx
            newIdx.initialize(dbi=dbi)
