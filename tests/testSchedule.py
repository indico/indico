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

"""Contains tests regarding some scenarios related to schedule management.
"""
import unittest
import os, pdb


from datetime import datetime,timedelta
from pytz import timezone

from MaKaC.errors import MaKaCError
from MaKaC.conference import Conference, Session, SessionSlot, Contribution
from MaKaC.user import Avatar

from MaKaC.schedule import IndTimeSchEntry
from MaKaC.common.contextManager import ContextManager

class ConferenceFacade(Conference):
    def notifyModification(self):
        pass

    def unindexConf(self):
        pass

    def indexConf(self):
        pass

class ContributionFacade(Contribution):
    def notifyModification(self):
        pass

    def unindexConf(self):
        pass

    def indexConf(self):
        pass

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


class TestTimeSchedule(unittest.TestCase):
    """Tests the basic schedule management functions
    """

    def setUp( self ):

        a = Avatar()
        a.setId("creator")
        self._conf = ConferenceFacade( a )
        self._conf.setId('a')
        self._conf.setTimezone('UTC')

        self._conf.setDates(datetime(2009, 9, 21, 16, 0 ,0, tzinfo=timezone("UTC")), datetime(2009, 9, 21, 19, 0 ,0, tzinfo=timezone("UTC")))

    def testBasicAddAndRemove( self ):
        from MaKaC.schedule import TimeSchedule
        sDateSch,eDateSch=datetime(2004,1,1,10,0, tzinfo=timezone('UTC')),datetime(2004,1,1,12,0, tzinfo=timezone('UTC'))
        schOwner=_ScheduleOwnerWrapper(sDateSch,eDateSch)
        sch=TimeSchedule(schOwner)
        entry1=IndTimeSchEntry()
        entry1.setDuration(0,25)
        entry2=IndTimeSchEntry()
        entry2.setDuration(0,30)
        entry3=IndTimeSchEntry()
        self.assert_(not entry1.isScheduled())
        self.assert_(not entry2.isScheduled())
        self.assert_(not entry3.isScheduled())
        sch.addEntry(entry1)
        sch.addEntry(entry2)
        sch.addEntry(entry3)
        self.assert_(entry1.isScheduled())
        self.assert_(entry2.isScheduled())
        self.assert_(entry3.isScheduled())
        self.assert_(entry1==sch.getEntries()[0])
        self.assert_(entry2==sch.getEntries()[1])
        self.assert_(entry3==sch.getEntries()[2])
        self.assert_(entry1.getStartDate()==datetime(2004,1,1,10,0, tzinfo=timezone('UTC')))
        self.assert_(entry1.getDuration()==timedelta(minutes=25))
        self.assert_(entry2.getStartDate()==datetime(2004,1,1,10,25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getDuration()==timedelta(minutes=30))
        self.assert_(entry3.getStartDate()==datetime(2004,1,1,10,55, tzinfo=timezone('UTC')))
        self.assert_(entry3.getDuration()==timedelta(minutes=5))
        sch.removeEntry(entry1)
        self.assert_(not entry1.isScheduled())
        self.assert_(entry2.isScheduled())
        self.assert_(entry3.isScheduled())
        self.assert_(entry1 not in sch.getEntries())
        self.assert_(entry2==sch.getEntries()[0])
        self.assert_(entry3==sch.getEntries()[1])
        self.assert_(entry1.getDuration()==timedelta(minutes=25))
        self.assert_(entry2.getStartDate()==datetime(2004,1,1,10,25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getDuration()==timedelta(minutes=30))
        self.assert_(entry3.getStartDate()==datetime(2004,1,1,10,55, tzinfo=timezone('UTC')))
        self.assert_(entry3.getDuration()==timedelta(minutes=5))

    def testCompact(self):
        from MaKaC.schedule import TimeSchedule
        sDateSch=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        eDateSch=datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC'))
        schOwner=_ScheduleOwnerWrapper(sDateSch,eDateSch)
        sch=TimeSchedule(schOwner)
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
        entry1.setStartDate(datetime(2004, 01, 01, 11, 00, tzinfo=timezone('UTC')))
        entry2.setStartDate(datetime(2004, 01, 01, 11, 15, tzinfo=timezone('UTC')))
        entry3.setStartDate(datetime(2004, 01, 01, 11, 25, tzinfo=timezone('UTC')))
        self.assert_(entry1.getStartDate()==datetime(2004, 01, 01, 11, 00, tzinfo=timezone('UTC')))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 11, 15, tzinfo=timezone('UTC')))
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 11, 25, tzinfo=timezone('UTC')))
        sch.compact()
        self.assert_(entry1.getStartDate()==datetime(2004 ,01, 01, 10, 00, tzinfo=timezone('UTC')))
        self.assert_(entry1.getDuration()==timedelta(minutes=25))
        self.assert_(entry2.getStartDate()==datetime(2004, 01, 01, 10, 25, tzinfo=timezone('UTC')))
        self.assert_(entry2.getDuration()==timedelta(minutes=25))
        self.assert_(entry3.getStartDate()==datetime(2004, 01, 01, 10, 50, tzinfo=timezone('UTC')))
        self.assert_(entry3.getDuration()==timedelta(minutes=30))

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


class TestConferenceSchedule(unittest.TestCase):
    """Tests the basic schedule management functions
    """

    def setUp( self ):

        # create a context, for storing autoOps
        ContextManager.create()
        ContextManager.set('autoOps', [])

        a = Avatar()
        a.setId("creator")
        self._conf = ConferenceFacade( a )
        self._conf.setId('a')
        self._conf.setTimezone('UTC')

        self._conf.setDates(datetime(2009, 9, 21, 16, 0 ,0, tzinfo=timezone("UTC")),
                            datetime(2009, 9, 21, 19, 0 ,0, tzinfo=timezone("UTC")))

        self._slot1_sDate = datetime(2009, 9, 21, 17, 0, 0, tzinfo=timezone("UTC"))
        self._slot1_eDate = datetime(2009, 9, 21, 18, 0, 0, tzinfo=timezone("UTC"))
        self._slot2_sDate = datetime(2009, 9, 21, 18, 0, 0, tzinfo=timezone("UTC"))
        self._slot2_eDate = datetime(2009, 9, 21, 19, 0, 0, tzinfo=timezone("UTC"))

        self._slot2_laterDate = datetime(2009, 9, 21, 20, 0, 0, tzinfo=timezone("UTC"))

        self._session1 = Session()
        self._session1.setValues({
            'sDate': self._slot1_sDate,
            'eDate': self._slot1_eDate
            })

        self._conf.addSession(self._session1)

        self._slot1 = self._session1.getSlotById(0)
        self._slot2 = SessionSlot(self._session1)

        self._slot2.setValues({
            'sDate': self._slot2_sDate,
            'eDate': self._slot2_eDate
            });

        self._session1.addSlot(self._slot2)

    def tearDown(self):
        ContextManager.destroy()

    def _addContribToSession(self, session, sDate, duration):
        contrib = ContributionFacade()

        contrib.setParent(self._conf)

        session.addContribution(contrib)

        contrib.setDuration(duration,0)
        contrib.setStartDate(sDate)

        return contrib

    def _expandNewTest(self, sDate, duration, expSDate, expEDate):
        from MaKaC.schedule import ConferenceSchedule

        schedule = ConferenceSchedule(self._conf)

        contrib = self._addContribToSession(self._session1, sDate, duration)

        # scheduling
        self._slot2.getSchedule().addEntry(contrib.getSchEntry())

        self.assert_(self._slot2.getAdjustedStartDate() == expSDate)
        self.assert_(self._slot2.getAdjustedEndDate() == expEDate)


    def _expandResizeTest(self, sDate, sDuration, newDate, newDuration, expSDate, expEDate):
        from MaKaC.schedule import ConferenceSchedule

        schedule = ConferenceSchedule(self._conf)

        contrib = self._addContribToSession(self._session1, sDate, sDuration)

        # scheduling
        self._slot2.getSchedule().addEntry(contrib.getSchEntry())

        # changing time
        contrib.setStartDate(newDate)
        contrib.setDuration(dur=timedelta(hours=newDuration))

        self.assert_(self._slot2.getAdjustedStartDate() == expSDate)
        self.assert_(self._slot2.getAdjustedEndDate() == expEDate)

    def testNewContentExpandsSlotDown(self):
        """ A slot grows down due to new overflowing content """
        return self._expandNewTest(self._slot2_sDate,
                                   2,
                                   self._slot2_sDate,
                                   self._slot2_laterDate)

    def testNotifyNewContentExpandsSlotDown(self):
        """ When a slot grows down (new content), proper notification is triggered  """

        self.testNewContentExpandsSlotDown()

        ops = ContextManager.get('autoOps')

        self.assert_(len(ops) == 4)

        op1 = ops[0]
        op2 = ops[1]
        op3 = ops[0]
        op4 = ops[1]

##         self.assert_(type(op1[0]) == SessionSlot)
##         self.assert_(op1[1] == 'OWNER_END_DATE_EXTENDED')
##         self.assert_(type(op1[2]) == Session)
##         self.assert_(op1[3] == self._slot2_laterDate)

##         self.assert_(type(op2[0]) == SessionSlot)
##         self.assert_(op2[1] == 'OWNER_START_DATE_EXTENDED')
##         self.assert_(type(op2[2]) == SessionSlot)
##         self.assert_(op2[3] == self._slot1_sDate)

##         self.assert_(type(op3[0]) == SessionSlot)
##         self.assert_(op3[1] == 'OWNER_END_DATE_EXTENDED')
##         self.assert_(type(op3[2]) == Session)
##         self.assert_(op3[3] == self._slot2_laterDate)

##         self.assert_(type(op4[0]) == SessionSlot)
##         self.assert_(op4[1] == 'OWNER_END_DATE_EXTENDED')
##         self.assert_(type(op4[2]) == SessionSlot)
##         self.assert_(op4[3] == self._slot2_laterDate)

    def testNewContentExpandsSlotUp(self):
        """ A slot grows up due to new "underflowing" content """
        return self._expandNewTest(self._slot1_sDate,
                                   2,
                                   self._slot1_sDate,
                                   self._slot2_eDate)

    def testNotifyNewContentExpandsSlotUp(self):
        """ When a slot grows up (new content), proper notification is triggered  """

#        import rpdb2; rpdb2.start_embedded_debugger_interactive_password()

        self.testNewContentExpandsSlotUp()

        ops = ContextManager.get('autoOps')

        self.assert_(len(ops) == 3)

        op1 = ops[0]
        op2 = ops[1]

##         self.assert_(type(op1[0]) == SessionSlot)
##         self.assert_(op1[1] == 'OWNER_START_DATE_EXTENDED')
##         self.assert_(type(op1[2]) == SessionSlot)
##         self.assert_(op1[3] == self._slot1_sDate)
##         self.assert_(op1[4] == self._slot2_sDate)

##         # in an ideal world, this one should not be shown
##         self.assert_(type(op2[0]) == SessionSlot)
##         self.assert_(op2[1] == 'OWNER_END_DATE_EXTENDED')
##         self.assert_(type(op2[2]) == SessionSlot)
##         self.assert_(op2[3] == self._slot2_eDate)
##         self.assert_(op2[4] == self._slot2_sDate)

    def testNewContentExpandsSlotBoth(self):
        """ A slot grows up due to new content that both "underflows" and overflows """
        self._expandNewTest(datetime(2009, 9, 21, 17, 0, 0, tzinfo=timezone("UTC")),
                            3,
                            self._slot1_sDate,
                            self._slot2_laterDate)

    def testNewCrossingDoesNotCorruptSessionTime(self):
        """ Session start/end time does not get messed up by new overflowing content """
        from MaKaC.schedule import ConferenceSchedule

        schedule = ConferenceSchedule(self._conf)

        earlyDate = datetime(2009, 9, 21, 16, 0, 0, tzinfo=timezone("UTC"))

        contrib = self._addContribToSession(self._session1, earlyDate, 1)

        # scheduling
        self._slot2.getSchedule().addEntry(contrib.getSchEntry())

        self.assert_(self._session1.getAdjustedStartDate() == earlyDate)
        self.assert_(self._session1.getAdjustedEndDate() == self._slot2_eDate)

    def testResizeContentExpandsSlotDown(self):
        """ A slot grows down by resizing content to overflow"""
        self._expandResizeTest(self._slot2_sDate,
                         1,
                         datetime(2009, 9, 21, 18, 0, 0, tzinfo=timezone("UTC")),
                         2,
                         self._slot2_sDate,
                         datetime(2009, 9, 21, 20, 0, 0, tzinfo=timezone("UTC")))

    def testResizeContentExpandsSlotUp(self):
        """ A slot grows down by resizing content to "underflow" """
        self._expandNewTest(datetime(2009, 9, 21, 17, 0, 0, tzinfo=timezone("UTC")),
                         2,
                         datetime(2009, 9, 21, 17, 0, 0, tzinfo=timezone("UTC")),
                         self._slot2_eDate)

    def testResizeContentExpandsSlotBoth(self):
        """ A slot grows down by resizing content to bot "underflow" and overflow"""
        self._expandNewTest(datetime(2009, 9, 21, 17, 0, 0, tzinfo=timezone("UTC")),
                         3,
                         datetime(2009, 9, 21, 17, 0, 0, tzinfo=timezone("UTC")),
                         datetime(2009, 9, 21, 20, 0, 0, tzinfo=timezone("UTC")))

    def testResizeCrossingDoesNotCorruptSessionTime(self):
        """ Session start/end time does not get messed up by resizing content to overflow """
        from MaKaC.schedule import ConferenceSchedule

        schedule = ConferenceSchedule(self._conf)
        contrib = self._addContribToSession(self._session1, self._slot2_sDate, 1)

        # scheduling
        self._slot2.getSchedule().addEntry(contrib.getSchEntry())

        # changing time
        earlyDate = datetime(2009, 9, 21, 16, 0, 0, tzinfo=timezone("UTC"))
        contrib.setStartDate(earlyDate)

        self.assert_(self._session1.getAdjustedStartDate() == earlyDate)
        self.assert_(self._session1.getAdjustedEndDate() == self._slot2_eDate)


def testsuite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestTimeSchedule) )
    suite.addTest( unittest.makeSuite(TestConferenceSchedule) )
    return suite

if __name__ == '__main__':
    unittest.main()
