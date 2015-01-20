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

# For now, disable Pylint
# pylint: disable-all


"""
Contains tests regarding some scenarios related to schedule management.
"""
import unittest
from indico.tests.env import *

import os
from datetime import datetime,timedelta
from pytz import timezone

from MaKaC.schedule import IndTimeSchEntry
from MaKaC.errors import MaKaCError
from MaKaC.conference import Conference, Category
from MaKaC.user import Avatar
import MaKaC.common.indexes as indexes


class _ScheduleOwnerWrapper:

    def __init__(self,sDate,eDate):
        self._sDate,self._eDate=sDate,eDate

    def getStartDate(self):
        return self._sDate

    def getEndDate(self):
        return self._eDate

    def getAdjustedStartDate( self, tz=None ):
        if not tz:
            tz = self.getTimezone()
        return self.getStartDate().astimezone(timezone(tz))

    def getAdjustedEndDate( self, tz=None ):
        if not tz:
            tz = self.getTimezone()
        return self.getEndDate().astimezone(timezone(tz))

    def setStartDate(self, sd):
        self._sDate=sd

    def setEndDate(self, ed):
        self._eDate=ed

    def setDates(self, sd, ed):
        self._sDate=sd
        self._eDate=ed


class _Needs_Rewriting_TestTimeSchedule(unittest.TestCase):
    """Tests the basic schedule management functions
    """

    def setUp( self ):
        a = Avatar()
        a.setId("creator")
        self._conf = Conference( a )
        self._conf.setId('a')
        category=Category()
        category.setId('1')
        self._conf.addOwner(category)
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateIdx.indexConf(self._conf)
        self._conf.setTimezone('UTC')

#TODO We need somehow to link schOwner with self._conf (Same thing for the following test
#    def testBasicAddAndRemove( self ):
#        from MaKaC.schedule import TimeSchedule
#        sDateSch,eDateSch=datetime(2004,1,1,10,0, tzinfo=timezone('UTC')),datetime(2004,1,1,12,0, tzinfo=timezone('UTC'))
#        schOwner=_ScheduleOwnerWrapper(sDateSch,eDateSch)
#        sch=TimeSchedule(schOwner)
#        self._conf.addOwner(sch)
#        entry1=IndTimeSchEntry()
#        entry1.setDuration(0,25)
#        entry2=IndTimeSchEntry()
#        entry2.setDuration(0,30)
#        entry3=IndTimeSchEntry()
#        self.assert_(not entry1.isScheduled())
#        self.assert_(not entry2.isScheduled())
#        self.assert_(not entry3.isScheduled())
#        sch.addEntry(entry1)
#        sch.addEntry(entry2)
#        sch.addEntry(entry3)
#        self.assert_(entry1.isScheduled())
#        self.assert_(entry2.isScheduled())
#        self.assert_(entry3.isScheduled())
#        self.assert_(entry1==sch.getEntries()[0])
#        self.assert_(entry2==sch.getEntries()[1])
#        self.assert_(entry3==sch.getEntries()[2])
#        self.assert_(entry1.getStartDate()==datetime(2004,1,1,10,0, tzinfo=timezone('UTC')))
#        self.assert_(entry1.getDuration()==timedelta(minutes=25))
#        self.assert_(entry2.getStartDate()==datetime(2004,1,1,10,25, tzinfo=timezone('UTC')))
#        self.assert_(entry2.getDuration()==timedelta(minutes=30))
#        self.assert_(entry3.getStartDate()==datetime(2004,1,1,10,55, tzinfo=timezone('UTC')))
#        self.assert_(entry3.getDuration()==timedelta(minutes=5))
#        sch.removeEntry(entry1)
#        self.assert_(not entry1.isScheduled())
#        self.assert_(entry2.isScheduled())
#        self.assert_(entry3.isScheduled())
#        self.assert_(entry1 not in sch.getEntries())
#        self.assert_(entry2==sch.getEntries()[0])
#        self.assert_(entry3==sch.getEntries()[1])
#        self.assert_(entry1.getDuration()==timedelta(minutes=25))
#        self.assert_(entry2.getStartDate()==datetime(2004,1,1,10,25, tzinfo=timezone('UTC')))
#        self.assert_(entry2.getDuration()==timedelta(minutes=30))
#        self.assert_(entry3.getStartDate()==datetime(2004,1,1,10,55, tzinfo=timezone('UTC')))
#        self.assert_(entry3.getDuration()==timedelta(minutes=5))

#    def testCompact(self):
#        from MaKaC.schedule import TimeSchedule
#        sDateSch=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
#        eDateSch=datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC'))
#        schOwner=_ScheduleOwnerWrapper(sDateSch,eDateSch)
#        sch=TimeSchedule(schOwner)
#        from MaKaC.schedule import TimeSchEntry
#        entry1,entry2=IndTimeSchEntry(),IndTimeSchEntry()
#        entry3=IndTimeSchEntry()
#        entry1.setDuration(0,25)
#        entry2.setDuration(0,25)
#        entry3.setDuration(0,30)
#        sch.addEntry(entry1)
#        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
#        sch.addEntry(entry2)
#        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
#        sch.addEntry(entry3)
#        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 50, tzinfo=timezone('UTC')))
#        entry1.setStartDate(datetime(2004, 01, 01, 11, 00, tzinfo=timezone('UTC')))
#        entry2.setStartDate(datetime(2004, 01, 01, 11, 15, tzinfo=timezone('UTC')))
#        entry3.setStartDate(datetime(2004, 01, 01, 11, 25, tzinfo=timezone('UTC')))
#        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 11, 00, tzinfo=timezone('UTC')))
#        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 11, 15, tzinfo=timezone('UTC')))
#        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 11, 25, tzinfo=timezone('UTC')))
#        sch.compact()
#        self.assert_(entry1.getStartDate()==datetime(2004 ,01, 01, 10, 00, tzinfo=timezone('UTC')))
#        self.assert_(entry1.getDuration()==timedelta(minutes=25))
#        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
#        self.assert_(entry2.getDuration()==timedelta(minutes=25))
#        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 50, tzinfo=timezone('UTC')))
#        self.assert_(entry3.getDuration()==timedelta(minutes=30))

    def testStartEndDates(self):
        from MaKaC.schedule import TimeSchedule
        sDateSch,eDateSch=datetime(2004,1,1,10,0, tzinfo=timezone('UTC')),datetime(2004,1,1,12,0, tzinfo=timezone('UTC'))
        schOwner=_ScheduleOwnerWrapper(sDateSch,eDateSch)
        sch=TimeSchedule(schOwner)
        self.assert_(sch.getStartDate()==schOwner.getStartDate())
        self.assert_(sch.getEndDate()==schOwner.getEndDate())
        schOwner.setStartDate(datetime(2004, 01, 02, 10, 00, tzinfo=timezone('UTC')))
        schOwner.setEndDate(datetime(2004, 01, 02, 12, 00, tzinfo=timezone('UTC')))
        self.assert_(sch.getStartDate()==datetime(2004, 01, 02, 10, 00, tzinfo=timezone('UTC')))
        self.assert_(sch.getEndDate()==datetime(2004, 01, 02, 12, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,schOwner.setDates,
        #                   datetime(2004, 01, 02, 10, 00, tzinfo=timezone('UTC')),
        #                   datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,schOwner.setDates,
        #                   datetime(2004, 01, 02, 10, 00, tzinfo=timezone('UTC')),
        #                   None)
        #schOwner.setDates(None,None)
        #self.assert_(sch.getStartDate()==schOwner.getStartDate())
        #self.assert_(sch.getEndDate()==schOwner.getEndDate())
        #entry1=IndTimeSchEntry()
        #entry1.setDuration(0,25)
        #entry2=IndTimeSchEntry()
        #entry2.setDuration(0,30)
        #sch.addEntry(entry1)
        #sch.addEntry(entry2)
        #schOwner.setDates(datetime(2004, 01, 01, 9, 00, tzinfo=timezone('UTC')))
        #schOwner.setDates(eDate=datetime(2004, 01, 01, 17, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,schOwner.setDates,
        #                   **{"sDate":datetime(2004, 01, 01, 10, 01, tzinfo=timezone('UTC'))})
        #self.assertRaises(MaKaCError,schOwner.setDates,
        #                   **{"sDate":datetime(2004, 01, 01, 11, 15, tzinfo=timezone('UTC'))})
        #self.assertRaises(MaKaCError,schOwner.setDates,
        #                   **{"eDate":datetime(2004, 01, 01, 10, 15, tzinfo=timezone('UTC'))})
        #schOwner.setDates(eDate=datetime(2004, 01, 01, 10, 55, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,schOwner.setDates,
        #                   **{"eDate":datetime(2004, 01, 01, 10, 54, tzinfo=timezone('UTC'))})

    def testMoveUp(self):
        from MaKaC.schedule import ConferenceSchedule
        sDateSch=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        eDateSch=datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC'))
        self._conf.setStartDate(sDateSch)
        self._conf.setEndDate(eDateSch)
        sch=ConferenceSchedule(self._conf)
        from MaKaC.schedule import TimeSchEntry
        entry1,entry2=IndTimeSchEntry(),IndTimeSchEntry()
        entry3=IndTimeSchEntry()
        entry1.setDuration(0,25)
        entry2.setDuration(0,25)
        entry3.setDuration(0,30)
        sch.addEntry(entry1)
        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        sch.addEntry(entry2)
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        sch.addEntry(entry3)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 50, tzinfo=timezone('UTC')))
        sch.moveUpEntry(entry3)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10 ,55, tzinfo=timezone('UTC')))
        sch.moveUpEntry(entry1)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 30, tzinfo=timezone('UTC')))
        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 10, 55, tzinfo=timezone('UTC')))
        entry2.setStartDate(datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        entry3.setStartDate(datetime(2004, 01, 01, 10, 35, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 35, tzinfo=timezone('UTC')))
        sch.moveUpEntry(entry3)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 55, tzinfo=timezone('UTC')))

    def testMoveDown(self):
        from MaKaC.schedule import ConferenceSchedule
        sDateSch=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        eDateSch=datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC'))
        self._conf.setStartDate(sDateSch)
        self._conf.setEndDate(eDateSch)
        sch=ConferenceSchedule(self._conf)
        from MaKaC.schedule import TimeSchEntry
        entry1,entry2=IndTimeSchEntry(),IndTimeSchEntry()
        entry3=IndTimeSchEntry()
        entry1.setDuration(0,25)
        entry2.setDuration(0,25)
        entry3.setDuration(0,30)
        sch.addEntry(entry1)
        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        sch.addEntry(entry2)
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        sch.addEntry(entry3)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 50, tzinfo=timezone('UTC')))
        sch.moveDownEntry(entry2)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 55, tzinfo=timezone('UTC')))
        sch.moveDownEntry(entry2)
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 50, tzinfo=timezone('UTC')))
        entry1.setStartDate(datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        entry2.setStartDate(datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        entry3.setStartDate(datetime(2004, 01, 01, 10, 35, tzinfo=timezone('UTC')))
        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 35, tzinfo=timezone('UTC')))
        sch.moveDownEntry(entry2)
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 55, tzinfo=timezone('UTC')))
