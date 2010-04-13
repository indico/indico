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

"""Contains tests regarding some scenarios related to session management.
"""
import unittest
import os

from datetime import datetime,timedelta
from pytz import timezone

from MaKaC.user import Avatar
from MaKaC.conference import SCIndex,Session,Conference,Contribution,SessionSlot
from MaKaC.errors import MaKaCError

import MaKaC.conference as conference


class TestBasicManagement(unittest.TestCase):
    """Tests the basic contribution management functions
    """

    def setUp( self ):
        a = Avatar()
        a.setId("creator")
        self._conf = Conference( a )
        self._conf.setDates(datetime(2000,1,1,tzinfo=timezone('UTC')),datetime(2020,1,1,tzinfo=timezone('UTC')))

    def testDates(self):
        session1=Session()
        #self._conf.setStartDate(datetime(2004,1,1,8,0,tzinfo=timezone('UTC')))
        #self._conf.setEndDate(datetime(2005,1,1,8,0,tzinfo=timezone('UTC')))
        session1.setStartDate(datetime(2004,2,15,tzinfo=timezone('UTC')))
        self.assertRaises(MaKaCError,session1.setEndDate,datetime(2004,2,14,tzinfo=timezone('UTC')))
        session1.setEndDate(datetime(2004,2,16,tzinfo=timezone('UTC')))
        self.assert_(session1.getStartDate()==datetime(2004,2,15,tzinfo=timezone('UTC')))
        self.assert_(session1.getEndDate()==datetime(2004,2,16,tzinfo=timezone('UTC')))
        session1.setDates(datetime(2004,2,10,tzinfo=timezone('UTC')),datetime(2004,2,11,tzinfo=timezone('UTC')))
        self.assert_(session1.getStartDate()==datetime(2004,2,10,tzinfo=timezone('UTC')))
        self.assert_(session1.getEndDate()==datetime(2004,2,11,tzinfo=timezone('UTC')))
        session1.setDates(datetime(2004,2,15,tzinfo=timezone('UTC')),datetime(2004,2,16,tzinfo=timezone('UTC')))
        self.assert_(session1.getStartDate()==datetime(2004,2,15,tzinfo=timezone('UTC')))
        self.assert_(session1.getEndDate()==datetime(2004,2,16,tzinfo=timezone('UTC')))
        session1.setDates(datetime(2004,2,14,tzinfo=timezone('UTC')),datetime(2004,2,17,tzinfo=timezone('UTC')))
        self.assert_(session1.getStartDate()==datetime(2004,2,14,tzinfo=timezone('UTC')))
        self.assert_(session1.getEndDate()==datetime(2004,2,17,tzinfo=timezone('UTC')))

    def testBasicAddAndRemove( self ):
        session1,session2=Session(),Session()
        self._conf.addSession(session1)
        self.assert_(self._conf.getSessionById(session1.getId())==session1)
        self.assert_(session1 in self._conf.getSessionList())
        session1.delete()
        self.assert_(session1 not in self._conf.getSessionList())
        self.assert_(self._conf.getSessionById(session1.getId())==None)

    def testDateModification(self):
        self._conf.setDates(datetime(2004,1,1,tzinfo=timezone('UTC')),datetime(2004,1,5,tzinfo=timezone('UTC')))
        ##checks that a session cannot be added if its dates are outside the 
        ##   schedule boundaries
        #s1=Session()
        #s1.setDates(datetime(2003,12,31,tzinfo=timezone('UTC')),datetime(2004,1,31,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #s1.setDates(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')),datetime(2004,1,31,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #s1.setDates(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')),datetime(2004,1,4,tzinfo=timezone('UTC')))
        #self._conf.addSession(s1)
        #self._conf.removeSession(s1)
        #self._conf.getSchedule().setDates(datetime(2004,1,2,tzinfo=timezone('UTC')),datetime(2004,1,7,tzinfo=timezone('UTC')))
        #s1=Session()
        #s1.setDates(datetime(2003,12,31,tzinfo=timezone('UTC')),datetime(2004,1,31,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #s1.setDates(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')),datetime(2004,1,31,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #s1.setDates(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')),datetime(2004,1,4,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #s1.setDates(datetime(2004,1,2,11,0,tzinfo=timezone('UTC')),datetime(2004,1,6,tzinfo=timezone('UTC')))
        #self._conf.addSession(s1)
        ##checks that when modifying the session dates to ones which are outside
        ##   the conference schedule scope is not allowed
        #s1.setDates(datetime(2004,1,3,tzinfo=timezone('UTC')),datetime(2004,1,5,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,s1.setDates,datetime(2004,1,3,tzinfo=timezone('UTC')),datetime(2004,1,8,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,s1.setDates,datetime(2005,1,1,11,0,tzinfo=timezone('UTC')),datetime(2004,1,6,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,s1.setDates,datetime(2005,1,1,11,0,tzinfo=timezone('UTC')),datetime(2004,1,8,tzinfo=timezone('UTC')))

    def testContributionInclusion(self):
        session1,session2=Session(),Session()
        self._conf.addSession(session1)
        self._conf.addSession(session2)
        contrib1=Contribution()
        session1.addContribution(contrib1)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(session1.hasContribution(contrib1))
        self.assert_(not session2.hasContribution(contrib1))
        session1.removeContribution(contrib1)
        session2.addContribution(contrib1)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(not session1.hasContribution(contrib1))
        self.assert_(session2.hasContribution(contrib1))
        session2.removeContribution(contrib1)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(not session1.hasContribution(contrib1))
        self.assert_(not session2.hasContribution(contrib1))

    def testCoordination(self):
        session1,session2,session3=Session(),Session(),Session()
        self._conf.addSession(session1)
        self._conf.addSession(session2)
        c1,c2=Avatar(),Avatar()
        c1.setId("1")
        c2.setId("2")
        session1.addCoordinator(c1)
        self.assert_(c1 in session1.getCoordinatorList())
        self.assert_(len(session1.getCoordinatorList())==1)
        self.assert_(session1.isCoordinator(c1))
        self.assert_(not session1.isCoordinator(c2))
        self.assert_(not session1.isCoordinator(None))
        self.assert_(session1 in self._conf.getCoordinatedSessions(c1))
        self.assert_(len(self._conf.getCoordinatedSessions(c1))==1)
        self.assert_(len(self._conf.getCoordinatedSessions(c2))==0)
        self._conf.addSessionCoordinator(session1,c1)
        self.assert_(c1 in session1.getCoordinatorList())
        self.assert_(len(session1.getCoordinatorList())==1)
        self.assert_(session1.isCoordinator(c1))
        self.assert_(not session1.isCoordinator(c2))
        self.assert_(not session1.isCoordinator(None))
        self.assert_(session1 in self._conf.getCoordinatedSessions(c1))
        self.assert_(len(self._conf.getCoordinatedSessions(c1))==1)
        self.assert_(len(self._conf.getCoordinatedSessions(c2))==0)
        self._conf.addSessionCoordinator(session2,c2)
        self.assert_(c2 in session2.getCoordinatorList())
        self.assert_(not session1.isCoordinator(c2))
        self.assert_(session2 in self._conf.getCoordinatedSessions(c2))
        self.assert_(len(self._conf.getCoordinatedSessions(c1))==1)
        self.assert_(len(self._conf.getCoordinatedSessions(c2))==1)
        self._conf.addSession(session3)
        session3.addCoordinator(c2)
        self.assert_(c2 in session3.getCoordinatorList())
        self.assert_(not session1.isCoordinator(c2))
        self.assert_(session3 in self._conf.getCoordinatedSessions(c2))
        self.assert_(session2 in self._conf.getCoordinatedSessions(c2))
        self.assert_(len(self._conf.getCoordinatedSessions(c1))==1)
        self.assert_(len(self._conf.getCoordinatedSessions(c2))==2)
        self._conf.removeSession(session1)
        self.assert_(session1 not in self._conf.getCoordinatedSessions(c1))
        self.assert_(len(self._conf.getCoordinatedSessions(c1))==0)
        self.assert_(len(self._conf.getCoordinatedSessions(c2))==2)
        session2.removeCoordinator(c2)
        self.assert_(c2 not in session2.getCoordinatorList())
        self.assert_(c2 in session3.getCoordinatorList())
        self.assert_(session3 in self._conf.getCoordinatedSessions(c2))
        self.assert_(session2 not in self._conf.getCoordinatedSessions(c2))
        self.assert_(len(self._conf.getCoordinatedSessions(c1))==0)
        self.assert_(len(self._conf.getCoordinatedSessions(c2))==1)


class TestSchedule(unittest.TestCase):
    """Tests the schedule management functions
    """

    def setUp( self ):
        from MaKaC.user import Avatar
        a = Avatar()
        a.setId("creator")
        from MaKaC.conference import Conference
        self._conf = Conference( a )
        self._conf.setTimezone('UTC')

    def testTypeSetUp(self):
        #test setting up the schedule type of a session works correctly
        self._conf.setDates(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')),datetime(2004,1,5,10,0,tzinfo=timezone('UTC')))
        session=Session()
        session.setStartDate(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        session.setDuration(hours=10,minutes=0)
        self._conf.addSession(session)
        slot1=SessionSlot(session)
        session.addSlot(slot1)
        c1,c2,c3=Contribution(),Contribution(),Contribution()
        session.addContribution(c1)
        session.addContribution(c2)
        session.addContribution(c3)
        slot1.getSchedule().addEntry(c1.getSchEntry())
        slot1.getSchedule().addEntry(c2.getSchEntry())
        slot1.getSchedule().addEntry(c3.getSchEntry())
        self.assert_(c1.getSchEntry()==slot1.getSchedule().getEntries()[0])
        self.assert_(c2.getSchEntry()==slot1.getSchedule().getEntries()[1])
        self.assert_(c3.getSchEntry()==slot1.getSchedule().getEntries()[2])
        self.assert_(session.getScheduleType()=="standard")
        self.assert_(slot1.getSchedule().__class__==conference.SlotSchedule)
        session.setScheduleType("poster")
        self.assert_(session.getScheduleType()=="poster")
        self.assert_(slot1.getSchedule().__class__==conference.PosterSlotSchedule)
        self.assert_(len(slot1.getSchedule().getEntries())==0)

    def testSessionDates(self):
        from MaKaC.conference import Session,SessionSlot, Conference
        self._conf.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2004,1,1,15,0,tzinfo=timezone('UTC')))
        session1=Session()
        session1.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        session1.setEndDate(datetime(2004,1,1,15,0,tzinfo=timezone('UTC')))
        self._conf.addSession(session1)
        slot1=SessionSlot(session1)
        slot1.setDuration(hours=2,minutes=0)
        slot1.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        session1.addSlot(slot1)
        # ------- SESSIONS -------
        # Session start date can not be bigger than the first slot start date
        self.assertRaises(MaKaCError, session1.setStartDate, datetime(2004,1,1,12,0,tzinfo=timezone('UTC')))
        # Session end date can not be prior than the last slot end date
        self.assertRaises(MaKaCError, session1.setEndDate, datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        # Session duration must be bigger than zero.
        self.assertRaises(MaKaCError, session1.setDuration, 0,0)
        # Session start date can not be prior than the conference end date
        #self.assertRaises(MaKaCError, session1.setStartDate, datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        # Session end date can not be bigger than the conference end date
        #self.assertRaises(MaKaCError, session1.setEndDate, datetime(2004,1,1,15,1,tzinfo=timezone('UTC')))
        # Session end date can not be bigger than the conference end date
        #self.assertRaises(MaKaCError, session1.setDuration, 6,1)

        # ------- SESSION SLOTS -------
        self._conf.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2004,1,1,15,0,tzinfo=timezone('UTC')))
        session1.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        session1.setEndDate(datetime(2004,1,1,15,0,tzinfo=timezone('UTC')))
        # Session slot duration must be bigger than zero.
        self.assertRaises(MaKaCError, slot1.setDuration, 0,0,0)
        # Forbid to create a slot alogn several days
        self._conf.setEndDate(datetime(2005,1,1,15,0,tzinfo=timezone('UTC')))
        self.assertRaises(MaKaCError, slot1.setDuration, 1,0,1)
        # Slot start date has to be between the session ones
        #self.assertRaises(MaKaCError, slot1.setStartDate, datetime(2004,1,1,9,59,tzinfo=timezone('UTC')))
        # Slot end date has to be between the session ones
        #self.assertRaises(MaKaCError, slot1.setDuration, 0,5,1)
        # If the duration is modified and any of the slot entries is affected then an excetpion is raised
        c1,c2,c3=Contribution(),Contribution(),Contribution()
        session1.addContribution(c1)
        session1.addContribution(c2)
        session1.addContribution(c3)
        c1.setDuration(0,30)
        c2.setDuration(0,30)
        c3.setDuration(0,30)
        from MaKaC.schedule import BreakTimeSchEntry
        b1=BreakTimeSchEntry()
        slot1.getSchedule().addEntry(c1.getSchEntry())
        slot1.getSchedule().addEntry(c2.getSchEntry())
        slot1.getSchedule().addEntry(c3.getSchEntry())
        self.assertRaises(MaKaCError, slot1.setDuration, 0,1,29)
        # Check that the duration of the entries do not overpass the slot duration
        slot1.setDuration(hours=1,minutes=30)
        #self.assertRaises(MaKaCError,c3.setDuration,0,31)
        c3.setDuration(0,30)
        slot1.setDuration(hours=2,minutes=0)
        slot1.getSchedule().addEntry(b1)
        #self.assertRaises(MaKaCError,b1.setDuration,0,31)
        #Check that entries start date is not less than owner start date
        #self.assertRaises(MaKaCError,c1.setStartDate,datetime(2004,1,1,9,59,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,b1.setStartDate,datetime(2004,1,1,9,59,tzinfo=timezone('UTC')))
        #Move all the entries
        slot3=SessionSlot(session1)
        slot3.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        slot3.setDuration(hours=3,minutes=0)        
        session1.addSlot(slot3)
        c4,c5=Contribution(),Contribution()
        session1.addContribution(c4)
        session1.addContribution(c5)
        c4.setTitle("campeon")
        c5.setTitle("campeonisimo")
        c4.setStartDate(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        c4.setDuration(0,30)
        c5.setDuration(0,30)        
        b2=BreakTimeSchEntry()
        b2.setDuration(0,30)
        b2.setTitle("breaaaaaaak")
        slot3.getSchedule().addEntry(c4.getSchEntry())
        slot3.getSchedule().addEntry(c5.getSchEntry())
        slot3.getSchedule().addEntry(b2)
        self.assert_(c4.getStartDate() == datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        slot3.setStartDate(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        #self.assert_(c4.getStartDate() == datetime(2004,1,1,12,0,tzinfo=timezone('UTC')))
        

        # ------- CONFERENCE -------
        # Conference should not start after a entry
        #self.assertRaises(MaKaCError,self._conf.setStartDate,datetime(2004,1,1,10,1,tzinfo=timezone('UTC')))
        # Conference should not finish before a entry
        #self.assertRaises(MaKaCError,self._conf.setEndDate,datetime(2004,1,1,14,59,tzinfo=timezone('UTC')))
        # Conference should not start after a entry (TIME)
        #self.assertRaises(MaKaCError,self._conf.setStartTime,10,1)
        # Conference should not finish before a entry (TIME)
        self._conf.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2005,1,1,18,0,tzinfo=timezone('UTC')))
        session2=Session()
        self._conf.addSession(session2)
        session2.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        session2.setEndDate(datetime(2005,1,1,18,0,tzinfo=timezone('UTC')))
        slot2=SessionSlot(session2)
        slot2.setDuration(hours=2,minutes=0)
        slot2.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        session2.addSlot(slot2)
        #self.assertRaises(MaKaCError,self._conf.setEndTime,17,59)
        

    def testSlots(self):
        self._conf.setDates(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')),datetime(2004,1,5,10,0,tzinfo=timezone('UTC')))
        session1=Session()
        session1.setStartDate(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        session1.setDuration(hours=10,minutes=0)
        self._conf.addSession(session1)
        slot1=SessionSlot(session1)
        slot1.setDuration(hours=2,minutes=0)
        session1.addSlot(slot1)
        self.assert_(slot1.getSessionSchEntry() in session1.getSchedule().getEntries())
        self.assert_(slot1.getStartDate()==session1.getStartDate())
        self.assert_(slot1.getDuration().seconds==7200)
        slot2=SessionSlot(session1)
        slot2.setDuration(hours=2,minutes=0)
        session1.addSlot(slot2)
        self.assert_(slot1.getSessionSchEntry()==session1.getSchedule().getEntries()[0])
        self.assert_(slot1.getStartDate()==session1.getStartDate())
        self.assert_(slot1.getDuration().seconds==7200)
        self.assert_(slot2.getSessionSchEntry()==session1.getSchedule().getEntries()[1])
        self.assert_(slot2.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        self.assert_(slot2.getDuration().seconds==7200)
        slot2.setStartDate(datetime(2004,1,1,15,0,tzinfo=timezone('UTC')))
        self.assert_(slot1.getSessionSchEntry()==session1.getSchedule().getEntries()[0])
        self.assert_(slot1.getStartDate()==session1.getStartDate())
        self.assert_(slot1.getDuration().seconds==7200)
        self.assert_(slot2.getSessionSchEntry()==session1.getSchedule().getEntries()[1])
        self.assert_(slot2.getStartDate()==datetime(2004,1,1,15,0,tzinfo=timezone('UTC')))
        self.assert_(slot2.getDuration().seconds==7200)
        slot1.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        slot2.setStartDate(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        self.assert_(slot2.getStartDate()==datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        #slot1.setStartDate(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        #slot2.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self.assert_(slot1.getSessionSchEntry()==session1.getSchedule().getEntries()[1])
        self.assert_(slot1.getDuration().seconds==7200)
        self.assert_(slot2.getSessionSchEntry()==session1.getSchedule().getEntries()[0])
        self.assert_(slot2.getStartDate()==datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        self.assert_(slot2.getDuration().seconds==7200)

    def testContributions(self):
        self._conf.setDates(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')),datetime(2004,1,5,10,0,tzinfo=timezone('UTC')))
        from MaKaC.conference import Session,Contribution,SessionSlot
        self._conf.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2005,1,1,10,0,tzinfo=timezone('UTC')))
        session1=Session()
        self._conf.addSession(session1)
        session1.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        session1.setDuration(hours=5,minutes=0)
        slot1=SessionSlot(session1)
        slot1.setDuration(hours=2,minutes=0)
        session1.addSlot(slot1)
        slot2=SessionSlot(session1)
        slot2.setDuration(hours=2,minutes=0)
        session1.addSlot(slot2)
        self.assert_(slot2.getStartDate()==datetime(2004,1,1,12,0,tzinfo=timezone('UTC')))
        c1,c2,c3=Contribution(),Contribution(),Contribution()
        session1.addContribution(c1)
        session1.addContribution(c2)
        session1.addContribution(c3)
        c1.setDuration(0,30)
        c2.setDuration(0,30)
        c3.setDuration(0,30)
        from MaKaC.errors import MaKaCError
        #self.assertRaises(MaKaCError,slot1.getSchedule().addEntry,c1.getSchEntry())
        slot1.getSchedule().addEntry(c1.getSchEntry())
        slot1.getSchedule().addEntry(c2.getSchEntry())
        slot1.getSchedule().addEntry(c3.getSchEntry())
        self.assert_(c1.getStartDate()==datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self.assert_(c2.getStartDate()==datetime(2004,1,1,10,30,tzinfo=timezone('UTC')))
        self.assert_(c3.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        #slot2.getSchedule().addEntry(c1.getSchEntry())
        #self.assert_(c1.getStartDate()==datetime(2004,1,1,12,0,tzinfo=timezone('UTC')))
        #self.assert_(c2.getStartDate()==datetime(2004,1,1,10,30,tzinfo=timezone('UTC')))
        #self.assert_(c3.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        from MaKaC.schedule import BreakTimeSchEntry
        b1=BreakTimeSchEntry()
        slot1.getSchedule().addEntry(b1)
        self.assert_(b1 in slot1.getSchedule().getEntries())
        #self.assert_(b1.getStartDate()==datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))

    def testMoveScheduledContribToSession(self):
        #tests that moving scheduled contributions at conference level into a 
        #   session works correctly: removes them from the conference schedule
        #   and includes them into the selected session
        self._conf.setDates(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')),datetime(2004,1,5,10,0,tzinfo=timezone('UTC')))
        session1=Session()
        session1.setStartDate(datetime(2004,1,1,9,0,tzinfo=timezone('UTC')))
        session1.setDuration(hours=1,minutes=0)
        self._conf.addSession(session1)
        c1,c2=Contribution(),Contribution()
        self._conf.addContribution(c1)
        self._conf.addContribution(c2)
        self._conf.getSchedule().addEntry(c1.getSchEntry())
        self._conf.getSchedule().addEntry(c2.getSchEntry())
        self.assert_(c1.isScheduled())
        self.assert_(c2.isScheduled())
        session1.addContribution(c1)
        self.assert_(not c1.isScheduled())
        self.assert_(c2.isScheduled())


class TestPosterSchedule(unittest.TestCase):
    """Tests the schedule for posters like schedules management functions
    """

    def setUp( self ):
        a=Avatar()
        a.setId("creator")
        self._conf=Conference(a)
        self._conf.setTimezone('UTC')
        self._conf.setStartDate(datetime(2004,1,1,10,0,tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2004,1,1,13,0,tzinfo=timezone('UTC')))
        self._session=Session()
        self._session.setStartDate(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        self._session.setEndDate(datetime(2004,1,1,13,0,tzinfo=timezone('UTC')))
        self._conf.addSession(self._session)
        self._slot1=SessionSlot(self._session)
        self._slot1.setStartDate(datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        self._slot1.setDuration(hours=1)
        self._session.addSlot(self._slot1)
        self._session.setScheduleType("poster")
        self._session.setContribDuration(1,0)

    def testBasic(self):
        #tests the basic adding of entries to a poster like timetable
        p1,p2,p3=Contribution(),Contribution(),Contribution()
        self._session.addContribution(p1)
        self._session.addContribution(p2)
        self._session.addContribution(p3)
        self._slot1.getSchedule().addEntry(p1.getSchEntry())
        self._slot1.getSchedule().addEntry(p2.getSchEntry())
        self._slot1.getSchedule().addEntry(p3.getSchEntry())
        self.assert_(p1.getDuration()==self._session.getContribDuration())
        self.assert_(p2.getDuration()==self._session.getContribDuration())
        self.assert_(p3.getDuration()==self._session.getContribDuration())
        self.assert_(p1.getStartDate()==self._slot1.getStartDate())
        self.assert_(p2.getStartDate()==self._slot1.getStartDate())
        self.assert_(p3.getStartDate()==self._slot1.getStartDate())
        self.assert_(p1.getSchEntry()==self._slot1.getSchedule().getEntries()[0])
        self.assert_(p2.getSchEntry()==self._slot1.getSchedule().getEntries()[1])
        self.assert_(p3.getSchEntry()==self._slot1.getSchedule().getEntries()[2])
        self._session.removeContribution(p2)
        self.assert_(p1.getDuration()==self._session.getContribDuration())
        self.assert_(p3.getDuration()==self._session.getContribDuration())
        self.assert_(p1.getStartDate()==self._slot1.getStartDate())
        self.assert_(p3.getStartDate()==self._slot1.getStartDate())
        self.assert_(p1.getSchEntry()==self._slot1.getSchedule().getEntries()[0])
        self.assert_(p3.getSchEntry()==self._slot1.getSchedule().getEntries()[1])

    def testStartDateNotChanging(self):
        #tests that changing the start date of an entry scheduled within a
        #   poster schedule has no effect
        p1=Contribution()
        self._session.addContribution(p1)
        self._slot1.getSchedule().addEntry(p1.getSchEntry())
        self.assert_(p1.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        p1.setStartDate(datetime(2004,1,1,11,25,tzinfo=timezone('UTC')))
        self.assert_(p1.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))

    def testChangeSlotStartDate(self):
        #checks that changing the start date of a slot changes all the entries'
        p1,p2=Contribution(),Contribution()
        self._session.addContribution(p1)
        self._session.addContribution(p2)
        self._slot1.getSchedule().addEntry(p1.getSchEntry())
        self._slot1.getSchedule().addEntry(p2.getSchEntry())
        self.assert_(p1.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        self.assert_(p2.getStartDate()==datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
        self._slot1.setStartDate(datetime(2004,1,1,11,25,tzinfo=timezone('UTC')))
        #self.assert_(p1.getStartDate()==datetime(2004,1,1,11,25,tzinfo=timezone('UTC')))
        #self.assert_(p2.getStartDate()==datetime(2004,1,1,11,25,tzinfo=timezone('UTC')))


class TestCoordinatorsIndexComponent(unittest.TestCase):
    """
    """

    def setUp( self ):
        pass

    def test(self):
        idx=SCIndex()
        c1=Avatar()
        c1.setId("1")
        s1=Session()
        idx.index(c1,s1)
        self.assert_(s1 in idx.getSessions(c1))
        self.assert_(len(idx.getSessions(c1))==1)
        c2=Avatar()
        c2.setId("2")
        idx.index(c2,s1)
        self.assert_(s1 in idx.getSessions(c1))
        self.assert_(len(idx.getSessions(c1))==1)
        self.assert_(s1 in idx.getSessions(c2))
        self.assert_(len(idx.getSessions(c2))==1)
        s2=Session()
        idx.index(c2,s2)
        self.assert_(s1 in idx.getSessions(c1))
        self.assert_(len(idx.getSessions(c1))==1)
        self.assert_(s1 in idx.getSessions(c2))
        self.assert_(s2 in idx.getSessions(c2))
        self.assert_(len(idx.getSessions(c2))==2)
        idx.unindex(c2,s2)
        self.assert_(s1 in idx.getSessions(c1))
        self.assert_(len(idx.getSessions(c1))==1)
        self.assert_(s1 in idx.getSessions(c2))
        self.assert_(s2 not in idx.getSessions(c2))
        self.assert_(len(idx.getSessions(c2))==1)


def testsuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicManagement))
    suite.addTest(unittest.makeSuite(TestSchedule))
    suite.addTest(unittest.makeSuite(TestPosterSchedule))
    suite.addTest(unittest.makeSuite(TestCoordinatorsIndexComponent))
    return suite


if __name__=="__main__":
    import sys
    sys.path.append("c:/development/indico/code/code")
    unittest.TextTestRunner(verbosity=2).run(unittest.makeSuite(TestSchedule))
