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


import unittest
from indico.core.db import DBMgr
from MaKaC.common.indexes import IndexesHolder, CategoryDateIndexLtd
from BTrees.OOBTree import OOBTree
from datetime import datetime
from pytz import timezone
from MaKaC.conference import ConferenceHolder


def buildCategoryDateIndexLtd():
    """ Builds limited version of CategoryDateIndex.
        Can take a long time
    """
    DBMgr.getInstance().startRequest()
    idx = CategoryDateIndexLtd()
    idx.buildIndex()
    IndexesHolder()._getIdx()["categoryDateLtd"] = idx
    DBMgr.getInstance().endRequest()


def removeCategoryDateIndexLtd():
    """ Removes CategoryDateIndexLtd from index holder """

    DBMgr.getInstance().startRequest()
    del IndexesHolder()._getIdx()["categoryDateLtd"]
    DBMgr.getInstance().endRequest()


class TestCategoryDayIndex(unittest.TestCase):

    def setUp(self):
        DBMgr.getInstance().startRequest()
        self.oldIndex = IndexesHolder()._getIdx()["categoryDateLtd"]
        self.newIndex = IndexesHolder()._getIdx()["categoryDate"]
        self.startDate = datetime(2010,5,13, 10, 0, 0, tzinfo=timezone('UTC'))
        self.endDate = datetime(2010,5,14, 14, 0, 0, tzinfo=timezone('UTC'))
        self.ch = ConferenceHolder()
        self.categId = '0'

    def tearDownModule(self):
        DBMgr.getInstance().abort()
        DBMgr.getInstance().endRequest()

    def testGetObjectsStartingInDay(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsStartingInDay(self.startDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsStartingInDay(self.startDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))

        assert(oldRes == newRes)

    def testGetObjectsStartingIn(self):
        newRes = self.newIndex.getObjectsStartingIn(self.categId, self.startDate, self.endDate)
        oldTmp = self.oldIndex.getObjectsStartingIn(self.categId, self.startDate, self.endDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)

    def testGetObjectsStartingAfterTest(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsStartingAfter(self.startDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsStartingAfter(self.startDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)

    def testGetObjectsEndingAfterTest(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsEndingAfter(self.startDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsEndingAfter(self.startDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)

    def testGetObjectsEndingInDay(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsEndingInDay(self.startDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsEndingInDay(self.startDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)

    def testGetObjectsEndingIn(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsEndingIn(self.startDate,self.endDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsEndingIn(self.startDate,self.endDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)

    def testGetObjectsInDay(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsInDay(self.startDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsInDay(self.startDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)

    def testGetObjectsIn(self):
        newRes = self.newIndex._idxCategItem[self.categId].getObjectsIn(self.startDate,self.endDate)
        oldTmp = self.oldIndex._idxCategItem[self.categId].getObjectsIn(self.startDate,self.endDate)
        oldRes = set()
        for res in oldTmp:
            oldRes.add(self.ch.getById(res))
        assert(oldRes == newRes)
