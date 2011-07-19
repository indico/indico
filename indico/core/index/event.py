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

from indico.core.index.base import IOIndex, Index
from indico.core.index.adapter import IIndexableByStartDateTime
from indico.util.date_time import utc_timestamp
from BTrees.OOBTree import OOSet, OOBTree


class CategoryEventStartDateIndex(Index):

    def __init__(self):
        self._container = OOBTree()

    def __getitem__(self, key):
        return self.getCategory[key]

    def __setitem__(self, key, value):
        self._container[key] = value

    def getCategory(self, categId):
        if categId not in self._container:
            self._container[categId] =  IOIndex(IIndexableByStartDateTime)
        return self._container[categId]

    def index_obj(self, obj):
        self.getCategory(obj.getOwner().getId()).index_obj(obj)

    def unindex_obj(self, obj):
        self.getCategory(obj.getOwner().getId()).unindex_obj(obj)

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
