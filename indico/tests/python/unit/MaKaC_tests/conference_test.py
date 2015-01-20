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

import unittest
from indico.tests.env import *

from datetime import datetime
from pytz import timezone
from MaKaC.user import Avatar

from MaKaC.conference import Conference, Category, Session, Contribution, \
     SessionSlot, ContributionParticipation, SCIndex
from MaKaC.schedule import BreakTimeSchEntry
from MaKaC import conference
from MaKaC.errors import MaKaCError


#From testCategories.py
class _Needs_Rewriting_TestCategories(unittest.TestCase):

    def testBasicAddAndRemoveConferences(self):

        #creation of basic category structure over which perform the tests
        croot=conference.Category()
        c1=conference.Category()
        croot._addSubCategory(c1)
        c2=conference.Category()
        croot._addSubCategory(c2)
        c1_1=conference.Category()
        c1._addSubCategory(c1_1)
        #checks adding a conference increases the conference number of the
        #   involved categories
        from MaKaC.user import Avatar
        creator=Avatar()
        conf1=conference.Conference(creator)
        print conf1,creator
        conf1.setId("0")
        c1_1._addConference(conf1)
        assert (c1_1.getNumConferences()==1)
        assert (c1.getNumConferences()==1)
        assert (c2.getNumConferences()==0)
        assert (croot.getNumConferences()==1)
        conf2=conference.Conference(creator)
        conf2.setId("1")
        c2._addConference(conf2)
        assert (c1_1.getNumConferences()==1)
        assert (c1.getNumConferences()==1)
        assert (c2.getNumConferences()==1)
        assert (croot.getNumConferences()==2)
        c1_1.removeConference(conf1)
        assert (c1_1.getNumConferences()==0)
        assert (c1.getNumConferences()==0)
        assert (c2.getNumConferences()==1)
        assert (croot.getNumConferences()==1)
        c2.removeConference(conf2)
        assert (c1_1.getNumConferences()==0)
        assert (c1.getNumConferences()==0)
        assert (c2.getNumConferences()==0)
        assert (croot.getNumConferences()==0)

    def testAddAndRemoveSubCategories(self):
        #checks that the conference counter works fine when adding a new
        #   sub-category
        croot=conference.Category()
        c1=conference.Category()
        c2=conference.Category()
        croot._addSubCategory(c2)
        from MaKaC.user import Avatar
        creator=Avatar()
        conf0=conference.Conference(creator)
        conf0.setId("0")
        conf1=conference.Conference(creator)
        conf1.setId("1")
        c1._addConference(conf0)
        c1._addConference(conf1)
        assert (croot.getNumConferences()==0)
        assert (c1.getNumConferences()==2)
        assert (c2.getNumConferences()==0)
        croot._addSubCategory(c1)
        assert (croot.getNumConferences()==2)
        assert (c1.getNumConferences()==2)
        assert (c2.getNumConferences()==0)
        c1_1=conference.Category()
        c1._addSubCategory(c1_1)
        assert (croot.getNumConferences()==2)
        assert (c1.getNumConferences()==2)
        assert (c1_1.getNumConferences()==2)
        assert (c2.getNumConferences()==0)
        c1_1.move(c2)
        assert (croot.getNumConferences()==2)
        assert (c1.getNumConferences()==0)
        assert (c1_1.getNumConferences()==2)

        assert (c2.getNumConferences()==2)
        croot._removeSubCategory(c1)
        assert (croot.getNumConferences()==2)
        assert (c1.getNumConferences()==0)
        assert (c1_1.getNumConferences()==2)
        assert (c2.getNumConferences()==2)
        c2._removeSubCategory(c1_1)
        assert (croot.getNumConferences()==0)
        assert (c1.getNumConferences()==0)
        assert (c1_1.getNumConferences()==2)
        assert (c2.getNumConferences()==0)

#from testConferences.py
class _Needs_Rewriting_TestBasicManagement(unittest.TestCase):
    """Tests the basic conference management functions
    """

    def setUp( self ):
        self._creator=Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
        self._conf.setTimezone('UTC')

        category=conference.Category()
        self._conf.addOwner(category)

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

class _Needs_Rewriting_TestModifyConferenceDates(unittest.TestCase):
    """Tests different scenarios which can occur when modifying conference start
        and end dates
    """
    def setUp(self):
        a = Avatar()
        a.setId("creator")
        self._conf=Conference(a)
        self._conf.setTimezone('UTC')

        category=conference.Category()
        self._conf.addOwner(category)

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

class _Needs_Rewriting_TestSchedule(unittest.TestCase):
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
        pass

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


class _Needs_Rewriting_TestAuthorIndex(unittest.TestCase):
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


class _Needs_Rewriting_TestAuthorSearch(unittest.TestCase):
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


class _Needs_Rewriting_TestContributionSubmitterIndex(unittest.TestCase):
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



class _Needs_Rewriting_TestBasicManagement(unittest.TestCase):
    """Tests the basic contribution management functions
    """

    def setUp( self ):
        a = Avatar()
        a.setId("creator")
        self._categ = Category()
        self._conf = Conference( a )
        category=conference.Category()
        self._conf.addOwner(category)
        self._conf.setId('a')
        self._conf.setDates(datetime(2000, 01, 01, tzinfo=timezone("UTC")),datetime(2020, 01, 01, tzinfo=timezone("UTC")))
        self._categ._addConference(self._conf)

    def testBasicAddAndRemove( self ):
        contrib1 = Contribution()
        contrib2 = Contribution()
        contrib3 = Contribution()
        self._conf.addContribution( contrib1 )
        self.assert_( self._conf.getContributionById( contrib1.getId() ) == contrib1 )
        self._conf.removeContribution( contrib2 )
        self.assert_( self._conf.getContributionById( contrib1.getId() ) == contrib1 )
        self._conf.removeContribution( contrib1 )
        self.assert_( self._conf.getContributionById( contrib1.getId() ) == None )
        self._conf.addContribution( contrib2 )
        contrib2.delete()
        self.assert_( self._conf.getContributionById( contrib2.getId() ) == None )

    def testTrackDefinition( self ):
        #tests the definition of the track of a contribution
        contrib1 = Contribution()
        track1 = self._conf.newTrack()
        track2 = self._conf.newTrack()
        self._conf.addContribution( contrib1 )
        contrib1.setTrack( track1 )
        self.assert_( contrib1.getTrack() == track1 )
        self.assert_( track1.hasContribution( contrib1 ) )
        contrib1.setTrack( None )
        self.assert_( contrib1.getTrack() == None )
        self.assert_( not track1.hasContribution( contrib1 ) )

    def testSessionInclusion(self):
        session1,session2=Session(),Session()
        self._conf.addSession(session1)
        self._conf.addSession(session2)
        contrib1=Contribution()
        self._conf.addContribution(contrib1)
        contrib1.setTitle("debug")
        contrib1.setSession(session1)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(session1.hasContribution(contrib1))
        self.assert_(not session2.hasContribution(contrib1))
        contrib1.setSession(session2)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(not session1.hasContribution(contrib1))
        self.assert_(session2.hasContribution(contrib1))
        contrib1.setSession(None)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(not session1.hasContribution(contrib1))
        self.assert_(not session2.hasContribution(contrib1))
        contrib1.setSession(session1)
        self.assert_(self._conf.hasContribution(contrib1))
        self.assert_(session1.hasContribution(contrib1))
        self.assert_(not session2.hasContribution(contrib1))
        self._conf.removeContribution(contrib1)
        self.assert_(not self._conf.hasContribution(contrib1))
        self.assert_(not session1.hasContribution(contrib1))
        self.assert_(contrib1 not in session1.getContributionList())
        self.assert_(not session2.hasContribution(contrib1))
        self.assert_(contrib1 not in session2.getContributionList())

    def testCustomIds(self):
        #tests that adding a contribution with a custom id does not cause any
        #   trouble
        contrib1 = Contribution()
        self._conf.addContribution(contrib1,"test")
        self.assert_(contrib1.getId()=="test")
        self.assert_(self._conf.getContributionById("test")==contrib1)
        contrib2 = Contribution()
        self._conf.addContribution(contrib2)
        self.assert_(contrib2.getId()=="0")
        self.assert_(self._conf.getContributionById("0")==contrib2)
        contrib3 = Contribution()
        self._conf.addContribution(contrib3,"12")
        self.assert_(contrib3.getId()=="12")
        self.assert_(self._conf.getContributionById("12")==contrib3)
        contrib4 = Contribution()
        self._conf.addContribution(contrib4)
        self.assert_(contrib4.getId()=="1")
        self.assert_(self._conf.getContributionById("1")==contrib4)
        contrib5 = Contribution()
        self.assertRaises(MaKaCError,self._conf.addContribution,contrib5,"0")
        self._conf.addContribution(contrib5,"2")
        self.assert_(contrib5.getId()=="2")
        self.assert_(self._conf.getContributionById("2")==contrib5)
        contrib6 = Contribution()
        self._conf.addContribution(contrib6)
        self.assert_(contrib6.getId()=="3")
        self.assert_(self._conf.getContributionById("3")==contrib6)


class _Needs_Rewriting_TestWithdrawal(unittest.TestCase):
    """Tests different scenarios concerning the contribution withdrawal
    """

    def setUp( self ):
        self._creator=Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
        category=conference.Category()
        self._conf.addOwner(category)
        self._conf.setTimezone('UTC')
        sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone("UTC"))
        ed=datetime(2004, 01, 05, 10, 00, tzinfo=timezone("UTC"))
        self._conf.setDates(sd,ed)

    def testBasicWithdrawal(self):
        c1, c2 = Contribution(),Contribution()
        auth1, auth2 = ContributionParticipation(), ContributionParticipation()
        self._conf.addContribution(c1)
        self._conf.addContribution(c2)

        auth1.setFirstName("a")
        auth1.setFamilyName("a")
        auth1.setEmail("a")
        auth2.setFirstName("b")
        auth2.setFamilyName("b")
        auth2.setEmail("b")

        c1.addPrimaryAuthor(auth1)
        c2.addPrimaryAuthor(auth2)

        s1 = Session()
        sd = datetime(2004, 01, 01, 12, 00, tzinfo=timezone("UTC"))
        ed = datetime(2004, 01, 01, 19, 00, tzinfo=timezone("UTC"))
        s1.setDates(sd,ed)

        slot1 = SessionSlot(s1)
        self._conf.addSession(s1)
        s1.addSlot(slot1)

        s1.addContribution(c1)
        s1.addContribution(c2)
        slot1.getSchedule().addEntry(c1.getSchEntry())
        slot1.getSchedule().addEntry(c2.getSchEntry())
        self.assert_(c1.isScheduled())
        self.assert_(c2.isScheduled())
        authIdx=self._conf.getAuthorIndex()
        self.assert_(auth1 in authIdx.getParticipations()[0])
        self.assert_(auth2 in authIdx.getParticipations()[1])
        c1.withdraw(self._creator,"test")
        self.assert_(not c1.isScheduled())
        self.assert_(c2.isScheduled())
        self.assert_(auth1 not in authIdx.getParticipations()[0])
        self.assert_(auth2 in authIdx.getParticipations()[0])
        auth1.setFirstName("aa")
        self.assert_(auth1 not in authIdx.getParticipations()[0])
        self.assert_(auth2 in authIdx.getParticipations()[0])
        auth3,auth4=ContributionParticipation(),ContributionParticipation()
        auth3.setFirstName("c")
        auth3.setFamilyName("c")
        auth3.setEmail("c")
        auth4.setFirstName("d")
        auth4.setFamilyName("d")
        auth4.setEmail("d")
        c1.addPrimaryAuthor(auth3)
        c2.addPrimaryAuthor(auth4)
        self.assert_(auth2 in authIdx.getParticipations()[0])
        self.assert_(auth4 in authIdx.getParticipations()[1])
        self.assertRaises(MaKaCError,slot1.getSchedule().addEntry,c1.getSchEntry())

class _Needs_Rewriting_TestSubmissionPrivileges(unittest.TestCase):
    """Tests different scenarios concerning the material submission privileges
    """

    def setUp( self ):
        self._creator=Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
        category=conference.Category()
        self._conf.addOwner(category)
        sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone("UTC"))
        ed=datetime(2004, 01, 05, 10, 00, tzinfo=timezone("UTC"))
        self._conf.setDates(sd,ed)

    def testBasic(self):
        c1=Contribution()
        self._conf.addContribution(c1)
        av1,av2=Avatar(),Avatar()
        av1.setId("1")
        av2.setId("2")
        self.assert_(not c1.canUserSubmit(av1))
        self.assert_(not c1.canUserSubmit(av2))
        self.assert_(len(c1.getSubmitterList())==0)
        c1.grantSubmission(av1)
        self.assert_(c1.canUserSubmit(av1))
        self.assert_(not c1.canUserSubmit(av2))
        self.assert_(len(c1.getSubmitterList())==1)
        self.assert_(av1 in c1.getSubmitterList())
        self.assert_(av2 not in c1.getSubmitterList())
        c1.revokeSubmission(av2)
        self.assert_(c1.canUserSubmit(av1))
        self.assert_(not c1.canUserSubmit(av2))
        self.assert_(len(c1.getSubmitterList())==1)
        self.assert_(av1 in c1.getSubmitterList())
        self.assert_(av2 not in c1.getSubmitterList())
        c1.revokeSubmission(av1)
        self.assert_(not c1.canUserSubmit(av1))
        self.assert_(not c1.canUserSubmit(av2))
        self.assert_(len(c1.getSubmitterList())==0)

    def testAccContrib(self):
        #tests that when a contribution comes from an accepted abstract the
        #   abstract submitters are also granted with submission privileges
        #   for the contribution
        av1=Avatar()
        av1.setId("1")
        av2=Avatar()
        av2.setId("2")
        abs=self._conf.getAbstractMgr().newAbstract(av1)
        abs.accept(self._creator,None,None)
        c=abs.getContribution()
        self.assert_(c.canUserSubmit(av1))
        self.assert_(not c.canUserSubmit(av2))
        c.grantSubmission(av2)
        self.assert_(c.canUserSubmit(av1))
        self.assert_(c.canUserSubmit(av2))


#from testSciProgramme.py
"""Contains tests about some typical "scientific programme" scenarios.
"""
class _Needs_Rewriting_TestTCIndex( unittest.TestCase ):
    """Makes sure the track coordinators index is working properly as standalone
        component
    """

    def setUp( self ):
        #Build an index
        from MaKaC.conference import TCIndex
        self._idx = TCIndex()

    def tearDown( self ):
        pass

    def testSimpleIndexing( self ):
        #adding a simple object to the index
        from MaKaC.user import Avatar
        av = Avatar()
        av.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t = Track()
        t.setId( "1" )
        self._idx.indexCoordinator( av , t )
        self.assert_( len(self._idx.getTracks( av )) == 1 )
        self.assert_( t in self._idx.getTracks( av ) )

    def testIndexingSeveralCoordinators( self ):
        #adding 2 coordinators for the same track
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        av2 = Avatar()
        av2.setId( "2" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t = Track()
        t.setId( "1" )
        self._idx.indexCoordinator( av1 , t )
        self._idx.indexCoordinator( av2 , t )
        self.assert_( t in self._idx.getTracks( av1 ) )
        self.assert_( t in self._idx.getTracks( av2 ) )

    def testIndexingSeveralTracks( self ):
        #adding 1 coordinator for 2 tracks
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t1 = Track()
        t1.setId( "1" )
        t2 = Track()
        t2.setId( "2" )
        self._idx.indexCoordinator( av1 , t1 )
        self._idx.indexCoordinator( av1 , t2 )
        self.assert_( t1 in self._idx.getTracks( av1 ) )
        self.assert_( t2 in self._idx.getTracks( av1 ) )

    def testSimpleUnidexing( self ):
        #check that unindexing works properly
        from MaKaC.user import Avatar
        av = Avatar()
        av.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t = Track()
        t.setId( "1" )
        self._idx.indexCoordinator( av , t )
        self._idx.unindexCoordinator( av, t )
        self.assert_( len(self._idx.getTracks( av )) == 0 )

    def testUnindexingSeveralCoordinators( self ):
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        av2 = Avatar()
        av2.setId( "2" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t1 = Track()
        t1.setId( "1" )
        self._idx.indexCoordinator( av1 , t1 )
        self._idx.indexCoordinator( av2 , t1 )
        self._idx.unindexCoordinator( av1, t1 )
        self.assert_( t1 not in self._idx.getTracks( av1 ) )
        self.assert_( t1 in self._idx.getTracks( av2 ) )

    def testUnindexingSeveralTracks( self ):
        from MaKaC.user import Avatar
        av1 = Avatar()
        av1.setId( "1" ) #the index needs the avatar to be uniquely identified
        from MaKaC.conference import Track
        t1 = Track()
        t1.setId( "1" )
        t2 = Track()
        t2.setId( "2" )
        self._idx.indexCoordinator( av1 , t1 )
        self._idx.indexCoordinator( av1 , t2 )
        self._idx.unindexCoordinator( av1, t1 )
        self.assert_( t1 not in self._idx.getTracks( av1 ) )
        self.assert_( t2 in self._idx.getTracks( av1 ) )


class _Needs_Rewriting_TestAddTrackCoordinator( unittest.TestCase ):
    """Tests different scenarios of the Define Track Coord use case.
    """

    def setUp( self ):
        from MaKaC.user import Avatar
        cr = Avatar()
        cr.setId( "creator" )
        from MaKaC.conference import Conference, Track
        self._conf = Conference( cr )
        self._track1 = Track()
        self._track1.setId( "1" )
        self._conf.addTrack( self._track1 )


    def tearDown( self ):
        pass

    def testAddTC( self ):
        from MaKaC.user import Avatar
        tc1 = Avatar()
        tc1.setId( "tc1" )
        self._track1.addCoordinator( tc1 )
        self.assert_( len(self._track1.getCoordinatorList()) == 1 )
        self.assert_( tc1 in self._track1.getCoordinatorList() )
        self.assert_( self._track1 in self._conf.getCoordinatedTracks( tc1 ) )


class _Needs_Rewriting_TestRemoveTrackCoordinator( unittest.TestCase ):
    """Tests different scenarios of the Remove Track Coord use case.
    """

    def setUp( self ):
        from MaKaC.user import Avatar
        cr = Avatar()
        cr.setId( "creator" )
        from MaKaC.conference import Conference, Track
        self._conf = Conference( cr )
        self._track1 = Track()
        self._track1.setId( "1" )
        self._conf.addTrack( self._track1 )

    def tearDown( self ):
        pass

    def testRemoveTC( self ):
        from MaKaC.user import Avatar
        tc1 = Avatar()
        tc1.setId( "tc1" )
        tc2 = Avatar()
        tc2.setId( "tc2" )
        self._track1.addCoordinator( tc1 )
        self._track1.addCoordinator( tc2 )
        self._track1.removeCoordinator( tc1 )
        self.assert_( tc1 not in self._track1.getCoordinatorList() )
        self.assert_( tc2 in self._track1.getCoordinatorList() )
        self.assert_( self._track1 not in self._conf.getCoordinatedTracks( tc1 ) )
        self.assert_( self._track1 in self._conf.getCoordinatedTracks( tc2 ) )


class _Needs_Rewriting_TestContributionInclusion( unittest.TestCase ):

    def setUp( self ):
        from MaKaC.user import Avatar
        cr = Avatar()
        cr.setId( "creator" )
        from MaKaC.conference import Conference, Track
        self._conf = Conference( cr )
        self._track1 = Track()
        self._track1.setId( "1" )
        self._conf.addTrack( self._track1 )

    def test( self ):
        from MaKaC.conference import Contribution
        contrib1 = Contribution()
        self._conf.addContribution( contrib1 )
        self._track1.addContribution( contrib1 )
        self.assert_( self._track1.hasContribution( contrib1 ) )
        self.assert_( contrib1.getTrack() == self._track1 )
        self._track1.removeContribution( contrib1 )
        self.assert_( not self._track1.hasContribution( contrib1 ) )
        self.assert_( contrib1.getTrack() == None )

#from testSessions.py
class _Needs_Rewriting_TestBasicManagement(unittest.TestCase):
    """Tests the basic contribution management functions
    """

    def setUp( self ):
        a = Avatar()
        a.setId("creator")
        self._conf = Conference( a )
        category=conference.Category()
        self._conf.addOwner(category)
        self._conf.setDates(datetime(2000,1,1,tzinfo=timezone('UTC')),datetime(2020,1,1,tzinfo=timezone('UTC')))

    def testDates(self):
        session1=Session()
        #self._conf.setStartDate(datetime(2004,1,1,8,0,tzinfo=timezone('UTC')))
        #self._conf.setEndDate(datetime(2005,1,1,8,0,tzinfo=timezone('UTC')))
        session1.setStartDate(datetime(2004,2,15,tzinfo=timezone('UTC')))
        #self.assertRaises(MaKaCError,session1.setEndDate,datetime(2004,2,14,tzinfo=timezone('UTC')))
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


class _Needs_Rewriting_TestSchedule(unittest.TestCase):
    """Tests the schedule management functions
    """

    def setUp( self ):
        from MaKaC.user import Avatar
        a = Avatar()
        a.setId("creator")
        from MaKaC.conference import Conference
        self._conf = Conference( a )
        category=conference.Category()
        self._conf.addOwner(category)
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
        #not true anymore, sessions are automatically extended
#        # Session start date can not be bigger than the first slot start date
#        self.assertRaises(MaKaCError, session1.setStartDate, datetime(2004,1,1,12,0,tzinfo=timezone('UTC')))
#        # Session end date can not be prior than the last slot end date
#        self.assertRaises(MaKaCError, session1.setEndDate, datetime(2004,1,1,11,0,tzinfo=timezone('UTC')))
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

        self._conf.setDates(
            datetime(2004,1,1,9,0,tzinfo=timezone('UTC')),
            datetime(2004,1,5,10,0,tzinfo=timezone('UTC')))

        session1 = Session()
        session1.setStartDate(datetime(2004, 1, 1, 9, 0, tzinfo = timezone('UTC')))
        session1.setDuration(hours = 10, minutes = 0)
        self._conf.addSession(session1)

        slot1 = SessionSlot(session1)
        slot1.setDuration(hours = 2, minutes = 0)
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


class _Needs_Rewriting_TestPosterSchedule(unittest.TestCase):
    """Tests the schedule for posters like schedules management functions
    """

    def setUp( self ):
        a=Avatar()
        a.setId("creator")
        self._conf=Conference(a)
        category=conference.Category()
        self._conf.addOwner(category)
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

class _Needs_Rewriting_TestCoordinatorsIndexComponent(unittest.TestCase):
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


#from testWebInterface.py should be renamed to testContributions.py anyway
"""Contains tests regarding some scenarios related to contribution list display.
"""
class _Needs_Rewriting_TestContributionList(unittest.TestCase):
    """Tests the contribution list functions
    """

    def setUp( self ):
        from MaKaC.user import Avatar
        a = Avatar()
        a.setId("creator")
        from MaKaC.conference import Conference
        self._conf=Conference(a)
        category=conference.Category()
        self._conf.addOwner(category)
        self._conf.setTimezone('UTC')
        self._conf.setDates(datetime(2000,1,1,tzinfo=timezone('UTC')),datetime(2020,1,1,tzinfo=timezone('UTC')))

    def testSorting( self ):
        from MaKaC.conference import Contribution, ContributionType, Session, Track
        from MaKaC.webinterface.common import contribFilters
        from MaKaC.common.filters import SimpleFilter
        contrib1 = Contribution()
        contrib2 = Contribution()
        contrib3 = Contribution()
        self._conf.addContribution( contrib1 )
        self._conf.addContribution( contrib2 )
        self._conf.addContribution( contrib3 )
        # Sorting by ID
        sortingCrit = contribFilters.SortingCriteria( ["number"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib1 )
        self.assert_( contribList[1] == contrib2 )
        self.assert_( contribList[2] == contrib3 )
        #Sorting by Date
        contrib1.setStartDate(datetime(2004, 5, 1, 10, 30,tzinfo=timezone('UTC')))
        contrib2.setStartDate(datetime(2003, 5, 1, 10, 30,tzinfo=timezone('UTC')))
        sortingCrit = contribFilters.SortingCriteria( ["date"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib2 )
        self.assert_( contribList[1] == contrib1 )
        self.assert_( contribList[2] == contrib3 )
        # Sorting by Contribution Type
        contribType1 = ContributionType("oral presentation", "no description", self._conf)
        contribType2 = ContributionType("poster", "no description", self._conf)
        contrib1.setType(contribType1)
        contrib2.setType(contribType2)
        sortingCrit = contribFilters.SortingCriteria( ["type"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib1 )
        self.assert_( contribList[1] == contrib2 )
        self.assert_( contribList[2] == contrib3 )
        # Sorting by Session
        session1 = Session()
        self._conf.addSession(session1)
        session2 = Session()
        self._conf.addSession(session2)
        contrib1.setSession(session1)
        contrib2.setSession(session2)
        sortingCrit = contribFilters.SortingCriteria( ["session"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_(contrib1 in contribList)
        self.assert_(contrib2 in contribList)
        self.assert_(contrib3 in contribList)
        # Sorting by Track
        track1 = Track()
        track1.setTitle("3")
        track1.setConference(self._conf)
        track2 = Track()
        track2.setTitle("1")
        track2.setConference(self._conf)
        contrib1.setTrack(track1)
        contrib2.setTrack(track2)
        sortingCrit = contribFilters.SortingCriteria( ["track"] )
        f = SimpleFilter( None, sortingCrit )
        contribList = f.apply(self._conf.getContributionList())
        self.assert_( len(contribList) == 3 )
        self.assert_( contribList[0] == contrib2 )
        self.assert_( contribList[1] == contrib1 )
        self.assert_( contribList[2] == contrib3 )
