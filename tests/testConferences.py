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

"""Contains tests regarding some scenarios related to conference management.
"""
import unittest
import os

from datetime import datetime,timedelta
from pytz import timezone

from MaKaC.user import Avatar
from MaKaC.conference import Conference, Category
from MaKaC.conference import Session,Contribution,SessionSlot
from MaKaC.conference import ContributionParticipation
from MaKaC.errors import MaKaCError
from MaKaC.schedule import BreakTimeSchEntry


class TestBasicManagement(unittest.TestCase):
    """Tests the basic conference management functions
    """

    def setUp( self ):
        self._creator=Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
        self._conf.setTimezone('UTC')

        confTZ = self._conf.getTimezone()
        sd = timezone(confTZ).localize(datetime(2000, 1, 1))
        sdUTC = sd.astimezone(timezone('UTC'))
        ed = timezone(confTZ).localize(datetime(2020, 1, 1))
        edUTC = ed.astimezone(timezone('UTC'))
        self._conf.setDates(sdUTC,edUTC)

    def testAddRemoveSessions(self):
        s1,s2=Session(),Session()
        self._conf.addSession(s1)
        self._conf.addSession(s2)
        self.assert_(s1 in self._conf.getSessionList())
        self.assert_(s1==self._conf.getSessionById(s1.getId()))
        self.assert_(s2 in self._conf.getSessionList())
        self.assert_(s2==self._conf.getSessionById(s2.getId()))
        self._conf.removeSession(s1)
        self.assert_(s1 not in self._conf.getSessionList())
        self.assert_(None==self._conf.getSessionById(s1.getId()))
        self.assert_(s2 in self._conf.getSessionList())
        self.assert_(s2==self._conf.getSessionById(s2.getId()))
        c1,c2,c3=Contribution(),Contribution(),Contribution()
        self._conf.addSession(s1)
        s1.addContribution(c1)
        s1.addContribution(c2)
        s2.addContribution(c3)
        self.assert_(s1 in self._conf.getSessionList())
        self.assert_(s1==self._conf.getSessionById(s1.getId()))
        self.assert_(s2 in self._conf.getSessionList())
        self.assert_(s2==self._conf.getSessionById(s2.getId()))
        self.assert_(c1 in self._conf.getContributionList())
        self.assert_(c2 in self._conf.getContributionList())
        self.assert_(c3 in self._conf.getContributionList())
        self.assert_(c1 in s1.getContributionList())
        self.assert_(c2 in s1.getContributionList())
        self.assert_(c3 in s2.getContributionList())
        self._conf.removeSession(s1)
        self.assert_(s1 not in self._conf.getSessionList())
        self.assert_(s2 in self._conf.getSessionList())
        self.assert_(c1 in self._conf.getContributionList())
        self.assert_(c2 in self._conf.getContributionList())
        self.assert_(c3 in self._conf.getContributionList())
        self.assert_(c1 not in s1.getContributionList())
        self.assert_(c1.getSession()==None)
        self.assert_(c2.getSession()==None)
        self.assert_(c2 not in s1.getContributionList())
        self.assert_(c3 in s2.getContributionList())


class TestModifyConferenceDates(unittest.TestCase):
    """Tests different scenarios which can occur when modifying conference start
        and end dates
    """
    def setUp(self):
        a = Avatar()
        a.setId("creator")
        self._conf=Conference(a)
        self._conf.setTimezone('UTC')
        sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        ed=datetime(2004, 01, 05, 10, 00, tzinfo=timezone('UTC'))
        self._conf.setDates(sd,ed)

    def testSessions(self):
        s1=Session()
        s1.setDates(datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')),datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC')))
        self._conf.addSession(s1)
        s2=Session()
        s2.setDates(datetime(2004, 01, 01, 15, 00, tzinfo=timezone('UTC')),datetime(2004, 01, 01, 18, 00, tzinfo=timezone('UTC')))
        self._conf.addSession(s2)
        #checks that modifying conference dates which does not affect to 
        #   sessions is allowed
        self._conf.setStartDate(datetime(2004, 01, 01, 9, 00, tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2004, 01, 01, 19, 00, tzinfo=timezone('UTC')))
        #if a session is affected an error should be reported
        #self.assertRaises(MaKaCError,self._conf.setStartDate,datetime(2004, 01, 01, 10, 01, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.setEndDate,datetime(2004, 01, 01, 17, 00, tzinfo=timezone('UTC')))

    def testEntries(self):
        c1,c2=Contribution(),Contribution()
        b=BreakTimeSchEntry()
        self._conf.addContribution(c1)
        self._conf.addContribution(c2)
        self._conf.getSchedule().addEntry(c1.getSchEntry())
        self._conf.getSchedule().addEntry(b)
        self._conf.getSchedule().addEntry(c2.getSchEntry())
        #checks that modifying conference dates which does not affect to 
        #   entries is allowed
        self._conf.setStartDate(datetime(2004, 01, 01, 9, 00, tzinfo=timezone('UTC')))
        self._conf.setEndDate(datetime(2004, 01, 01, 19, 00, tzinfo=timezone('UTC')))
        #if any entry is affected an error should be reported
        #self.assertRaises(MaKaCError,self._conf.setStartDate,datetime(2004, 01, 01, 10, 01, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.setEndDate,datetime(2004, 01, 01, 10, 20, tzinfo=timezone('UTC')))

    
class TestSchedule(unittest.TestCase):
    """Tests the schedule management functions
    """

    def setUp( self ):
        a = Avatar()
        a.setId("creator")
        self._conf=Conference(a)
        self._conf.setTimezone('UTC')
        sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        ed=datetime(2004, 01, 05, 10, 00, tzinfo=timezone('UTC'))
        self._conf.setDates(datetime(2000, 01, 01, tzinfo=timezone('UTC')),datetime(2020, 01, 01, tzinfo=timezone('UTC')))
        self._conf.setScreenStartDate(sd)
        self._conf.setScreenEndDate(ed)

    def testAddSessionOutsideBoundaries(self):
        #adding a session outside the conference dates must fail
        #s1=Session()
        #sd=datetime(2004, 01, 01, 9, 00, tzinfo=timezone('UTC'))
        #ed=datetime(2004, 01, 01, 16, 00, tzinfo=timezone('UTC'))
        #s1.setDates(sd,ed)
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        #ed=datetime(2004, 01, 05, 10, 01, tzinfo=timezone('UTC'))
        #s1.setDates(sd,ed)
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        #sd=datetime(2004, 01, 01, 9, 00, tzinfo=timezone('UTC'))
        #ed=datetime(2004, 01, 05, 9, 59, tzinfo=timezone('UTC'))
        #s1.setDates(sd,ed)
        #self.assertRaises(MaKaCError,self._conf.addSession,s1)
        pass

    def testAddEntryOutsideBoundaries(self):
        #adding an entry outside the conference dates must fail
        #c1=Contribution()
        #self._conf.addContribution(c1)
        #c1.setStartDate(datetime(1999, 01, 01, 9, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.getSchedule().addEntry,c1.getSchEntry())
        #b=BreakTimeSchEntry()
        #b.setStartDate(datetime(2004, 01, 01, 9, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.getSchedule().addEntry,b)
        pass

    def testSetScheduleDifferentDates(self):
        self._conf.setDates(datetime(2004, 01, 03, 10, 00, tzinfo=timezone('UTC')),datetime(2004, 01, 05, 10, 00, tzinfo=timezone('UTC')))
        s=Session()
        s.setDates(datetime(2004, 01, 04, 10, 00, tzinfo=timezone('UTC')),datetime(2004, 01, 04, 12, 00, tzinfo=timezone('UTC')))
        self._conf.addSession(s)
        c=Contribution()
        self._conf.addContribution(c)
        c.setStartDate(datetime(2004, 01, 04, 13, 00, tzinfo=timezone('UTC')))
        self._conf.getSchedule().addEntry(c.getSchEntry())
        #checks that everything works fine when changing conference schdule 
        #   dates to ones different from the conference
        #self._conf.setScreenStartDate(datetime(2004, 01, 04, 10, 00, tzinfo=timezone('UTC')))
        #self._conf.setScreenEndDate(datetime(2004, 01, 05, 12, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.setScreenStartDate,datetime(2004, 01, 04, 10, 01, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.setScreenEndDate,datetime(2004, 01, 04, 13, 00, tzinfo=timezone('UTC')))
        #self._conf.setScreenStartDate(datetime(2004, 01, 04, 10, 00, tzinfo=timezone('UTC')))
        #self._conf.setScreenEndDate(datetime(2004, 01, 04, 14, 00, tzinfo=timezone('UTC')))

        #self._conf.setScreenStartDate(datetime(2004, 01, 01, tzinfo=timezone('UTC')))
        #self._conf.setScreenEndDate(datetime(2004, 01, 05, tzinfo=timezone('UTC')))

        #s.setDates(datetime(2004, 01, 02, 10, 00, tzinfo=timezone('UTC')),datetime(2004, 01, 04, 12, 00, tzinfo=timezone('UTC')))
        #c.setStartDate(datetime(2004, 01, 02, 10, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.getSchedule().setDates,None,None)
        #s.setDates(datetime(2004, 01, 04, 10, 00, tzinfo=timezone('UTC')),datetime(2004, 01, 04, 12, 00, tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,self._conf.getSchedule().setDates,None,None)
        #c.setStartDate(datetime(2004, 01, 04, 10, 00, tzinfo=timezone('UTC')))
        #self._conf.getSchedule().setDates(None,None)
        
    def testSessions(self):
        s1=Session()
        self._conf.addSession(s1)
        sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        ed=datetime(2004, 01, 01, 16, 00, tzinfo=timezone('UTC'))
        s1.setDates(sd,ed)
        slot1=SessionSlot(s1)
        s1.addSlot(slot1)
        slot1.setStartDate(datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        slot1.setDuration(hours=2,minutes=0)
        slot2=SessionSlot(s1)
        s1.addSlot(slot2)
        slot2.setStartDate(datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC')))
        slot2.setDuration(hours=2,minutes=0)
        self.assert_(slot1.getConfSchEntry() in self._conf.getSchedule().getEntries())
        self.assert_(slot2.getConfSchEntry() in self._conf.getSchedule().getEntries())
        slot3=SessionSlot(s1)
        s1.addSlot(slot3)
        slot3.setStartDate(datetime(2004, 01, 01, 13, 00, tzinfo=timezone('UTC')))
        slot3.setDuration(hours=2,minutes=0)
        self.assert_(slot3.getConfSchEntry() in self._conf.getSchedule().getEntries())
        slot3.delete()
        self.assert_(slot1.getConfSchEntry() in self._conf.getSchedule().getEntries())
        self.assert_(slot2.getConfSchEntry() in self._conf.getSchedule().getEntries())
        self.assert_(slot3.getConfSchEntry() not in self._conf.getSchedule().getEntries())

    def testContributions(self):
        c1,c2=Contribution(),Contribution()
        self._conf.addContribution(c1)
        self._conf.addContribution(c2)
        sDate=datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC'))
        eDate=datetime(2004, 01, 01, 12, 00, tzinfo=timezone('UTC'))
        self._conf.setStartDate(sDate)
        self._conf.setEndDate(eDate)
        c1.setDuration(0,10)
        c2.setDuration(0,30)
        self._conf.getSchedule().addEntry(c1.getSchEntry())
        self._conf.getSchedule().addEntry(c2.getSchEntry())
        self.assert_(c1.getSchEntry() in self._conf.getSchedule().getEntries())
        self.assert_(c1.getStartDate()==datetime(2004, 01, 01, 10, 00, tzinfo=timezone('UTC')))
        self.assert_(c2.getSchEntry() in self._conf.getSchedule().getEntries())
        self.assert_(c2.getStartDate()==datetime(2004, 01, 01, 10, 10, tzinfo=timezone('UTC')))


class TestAuthorIndex(unittest.TestCase):
    """Tests the author index
    """

    def setUp( self ):
        self._creator = Avatar()
        self._creator.setId("creator")
        self._categ = Category()
        self._conf=Conference(self._creator)
        self._conf.setId('a')
        self._conf.setTimezone('UTC')
        self._categ._addConference(self._conf)

    def testBasicIndexing(self):
        #Tests adding a contribution with some authors already on it
        c1=Contribution()
        self._conf.addContribution(c1)
        auth1,auth2=ContributionParticipation(),ContributionParticipation()
        auth1.setFirstName("hector")
        auth1.setFamilyName("sanchez sanmartin")
        auth1.setEmail("hector.sanchez@cern.ch")
        auth2.setFirstName("jose benito")
        auth2.setFamilyName("gonzalez lopez")
        auth2.setEmail("jose.benito.gonzalez@cern.ch")
        c1.addPrimaryAuthor(auth1)
        c1.addPrimaryAuthor(auth2)
        idx=self._conf.getAuthorIndex()
        self.assert_(auth1 in idx.getParticipations()[1])
        self.assert_(len(idx.getParticipations()[1])==1)
        self.assert_(auth2 in idx.getParticipations()[0])
        self.assert_(len(idx.getParticipations()[0])==1)
        c2=Contribution()
        self._conf.addContribution(c2)
        auth3,auth4=ContributionParticipation(),ContributionParticipation()
        auth3.setFirstName("hector")
        auth3.setFamilyName("sanchez sanmartin")
        auth3.setEmail("hector.sanchez@cern.ch")
        auth4.setFirstName("jose benito")
        auth4.setFamilyName("gonzalez lopez2")
        auth4.setEmail("jose.benito.gonzalez@cern.ch")
        c2.addPrimaryAuthor(auth3)
        c2.addPrimaryAuthor(auth4)
        #Tests removing a contribution from a conference updates the author 
        #   index correctly
        #self.assert_(auth3 in idx.getParticipations()[2])
        #self.assert_(len(idx.getParticipations()[2])==2)
        #self.assert_(auth4 in idx.getParticipations()[1])
        #self.assert_(len(idx.getParticipations()[1])==1)
        #self._conf.removeContribution(c2)
        #self.assert_(auth1 in idx.getParticipations()[1])
        #self.assert_(len(idx.getParticipations()[1])==1)
        #self.assert_(auth2 in idx.getParticipations()[0])
        #self.assert_(len(idx.getParticipations()[0])==1)
        #Tests adding additional authors to a contribution which is already
        #   included in a conference updates the author index correctly
        #auth5=ContributionParticipation()
        #auth5.setFirstName("jean-yves")
        #auth5.setFamilyName("le meur")
        #auth5.setEmail("jean-yves.le.meur@cern.ch")
        #c1.addPrimaryAuthor(auth5)
        #self.assert_(auth1 in idx.getParticipations()[2])
        #self.assert_(len(idx.getParticipations()[2])==1)
        #self.assert_(auth2 in idx.getParticipations()[0])
        #self.assert_(len(idx.getParticipations()[0])==1)
        #self.assert_(auth5 in idx.getParticipations()[1])
        #self.assert_(len(idx.getParticipations()[1])==1)
        #Tests removing authors from a contribution which is already
        #   included in a conference updates the author index correctly
        #c1.removePrimaryAuthor(auth5)
        #self.assert_(auth1 in idx.getParticipations()[1])
        #self.assert_(len(idx.getParticipations()[1])==1)
        #self.assert_(auth2 in idx.getParticipations()[0])
        #self.assert_(len(idx.getParticipations()[0])==1)

    def testChangesInAuthorData(self):
        #Checks that changes in the author data updates the author index 
        #   correctly
        c1=Contribution()
        self._conf.addContribution(c1)
        auth1,auth2=ContributionParticipation(),ContributionParticipation()
        auth1.setFirstName("zFN")
        auth1.setFamilyName("zSN")
        auth1.setEmail("zM")
        auth2.setFirstName("AFN")
        auth2.setFamilyName("ASN")
        auth2.setEmail("aM")
        c1.addPrimaryAuthor(auth1)
        c1.addPrimaryAuthor(auth2)
        
        idx=self._conf.getAuthorIndex()
        self.assert_(auth1 in idx.getParticipations()[1])
        self.assert_(len(idx.getParticipations()[1])==1)
        self.assert_(auth2 in idx.getParticipations()[0])
        self.assert_(len(idx.getParticipations()[0])==1)
        auth2.setFamilyName("ZZSN")
        self.assert_(auth1 in idx.getParticipations()[0])
        self.assert_(len(idx.getParticipations()[0])==1)
        self.assert_(auth2 in idx.getParticipations()[1])
        self.assert_(len(idx.getParticipations()[1])==1)


class TestAuthorSearch(unittest.TestCase):
    """Tests the author search
    """

    def setUp( self ):
        self._creator = Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
        self._conf.setTimezone('UTC')

    def testBasicSearch(self):
        c1=Contribution()
        self._conf.addContribution(c1)
        auth1,auth2=ContributionParticipation(),ContributionParticipation()
        auth1.setFamilyName("a")
        auth1.setFirstName("a")
        auth2.setFamilyName("b")
        auth2.setFirstName("b")
        c1.addPrimaryAuthor(auth1)
        c1.addPrimaryAuthor(auth2)
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("a"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("a"))
        self.assert_(c1 in self._conf.getContribsMatchingAuth("B"))
        self.assert_(len(self._conf.getContribsMatchingAuth("B"))==1)
        auth3=ContributionParticipation()
        auth3.setFamilyName("c")
        auth3.setFirstName("c")
        c1.addCoAuthor(auth3)
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("c"))==0)

    def testAddAuthor(self):
        c1=Contribution()
        self._conf.addContribution(c1)
        auth1,auth2=ContributionParticipation(),ContributionParticipation()
        auth1.setFamilyName("a")
        auth1.setFirstName("a")
        auth2.setFamilyName("b")
        auth2.setFirstName("b")
        c1.addPrimaryAuthor(auth1)
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("a"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("a"))
        c1.addPrimaryAuthor(auth2)
        self.assert_(len(self._conf.getContribsMatchingAuth("b"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("b"))
        c1.removePrimaryAuthor(auth1)
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("a"))==0)
        self.assert_(c1 not in self._conf.getContribsMatchingAuth("a"))
        self.assert_(len(self._conf.getContribsMatchingAuth("b"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("b"))

    def testWithdrawnContrib(self):
        #Withdrawn contributions authors must be searchable
        c1=Contribution()
        self._conf.addContribution(c1)
        auth1=ContributionParticipation()
        auth1.setFamilyName("a")
        auth1.setFirstName("a")
        c1.addPrimaryAuthor(auth1)
        c1.withdraw(self._creator,"ll")
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("a"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("a"))
        auth2=ContributionParticipation()
        auth2.setFamilyName("b")
        auth2.setFirstName("b")
        c1.addPrimaryAuthor(auth2)
        #self._conf.getContribsMatchingAuth("b")
        #self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        #self.assert_(len(self._conf.getContribsMatchingAuth("b"))==1)
        #self.assert_(c1 in self._conf.getContribsMatchingAuth("b"))

    def testAuthorsWithSameName(self):
        #one contribution could have 2 authors with the same name
        c1=Contribution()
        self._conf.addContribution(c1)
        auth1=ContributionParticipation()
        auth1.setFamilyName("a")
        auth1.setFirstName("a")
        c1.addPrimaryAuthor(auth1)
        auth2=ContributionParticipation()
        auth2.setFamilyName("a")
        auth2.setFirstName("a")
        c1.addPrimaryAuthor(auth2)
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("a"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("a"))
        c1.removePrimaryAuthor(auth1)
        self.assert_(len(self._conf.getContribsMatchingAuth(""))==1)
        self.assert_(len(self._conf.getContribsMatchingAuth("a"))==1)
        self.assert_(c1 in self._conf.getContribsMatchingAuth("a"))


class TestContributionSubmitterIndex(unittest.TestCase):
    """
    """

    def setUp( self ):
        self._creator = Avatar()
        self._creator.setId("creator")
        self._categ = Category()
        self._conf=Conference(self._creator)
        self._conf.setId('a')
        self._conf.setTimezone('UTC')
        self._categ._addConference(self._conf)

    def testBasic(self):
        c1,c2=Contribution(),Contribution()
        av1,av2=Avatar(),Avatar()
        av1.setId("1")
        av2.setId("2")
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==0)
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==0)
        self._conf.addContribution(c1)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==0)
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==0)
        c1.grantSubmission(av1)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==1)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av1))
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==0)
        c2.grantSubmission(av2)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==1)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av1))
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==0)
        self._conf.addContribution(c2)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==1)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av1))
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==1)
        self.assert_(c2 in self._conf.getContribsForSubmitter(av2))
        c1.grantSubmission(av2)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==1)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av1))
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==2)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av2))
        self.assert_(c2 in self._conf.getContribsForSubmitter(av2))
        c1.revokeSubmission(av2)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==1)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av1))
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==1)
        self.assert_(c1 not in self._conf.getContribsForSubmitter(av2))
        self.assert_(c2 in self._conf.getContribsForSubmitter(av2))
        self._conf.removeContribution(c2)
        self.assert_(len(self._conf.getContribsForSubmitter(av1))==1)
        self.assert_(c1 in self._conf.getContribsForSubmitter(av1))
        self.assert_(len(self._conf.getContribsForSubmitter(av2))==0)
        self.assert_(c1 not in self._conf.getContribsForSubmitter(av2))
        self.assert_(c2 not in self._conf.getContribsForSubmitter(av2))



def testsuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicManagement))
    suite.addTest(unittest.makeSuite(TestSchedule))
    suite.addTest(unittest.makeSuite(TestAuthorIndex))
    suite.addTest(unittest.makeSuite(TestAuthorSearch))
    suite.addTest(unittest.makeSuite(TestContributionSubmitterIndex))
    suite.addTest(unittest.makeSuite(TestModifyConferenceDates))
    return suite
