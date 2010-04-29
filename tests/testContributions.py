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

"""Contains tests regarding some scenarios related to contribution management.
"""
import unittest
import os

from datetime import datetime
from pytz import timezone
from MaKaC.user import Avatar
from MaKaC.conference import Conference,Contribution,Track,Session, Category
from MaKaC.conference import ContributionParticipation,SessionSlot
from MaKaC.errors import MaKaCError



class TestBasicManagement(unittest.TestCase):
    """Tests the basic contribution management functions
    """

    def setUp( self ):
        a = Avatar()
        a.setId("creator")
        self._categ = Category()
        self._conf = Conference( a )
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


class TestWithdrawal(unittest.TestCase):
    """Tests different scenarios concerning the contribution withdrawal
    """

    def setUp( self ):
        self._creator=Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
        self._conf.setTimezone('UTC')
        sd=datetime(2004, 01, 01, 10, 00, tzinfo=timezone("UTC"))
        ed=datetime(2004, 01, 05, 10, 00, tzinfo=timezone("UTC"))
        self._conf.setDates(sd,ed)

    def testBasicWithdrawal(self):
        c1,c2=Contribution(),Contribution()
        auth1,auth2=ContributionParticipation(),ContributionParticipation()
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
        s1=Session()
        sd=datetime(2004, 01, 01, 12, 00, tzinfo=timezone("UTC"))
        ed=datetime(2004, 01, 01, 19, 00, tzinfo=timezone("UTC"))
        s1.setDates(sd,ed)
        slot1=SessionSlot(s1)
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

class TestSubmissionPrivileges(unittest.TestCase):
    """Tests different scenarios concerning the material submission privileges
    """

    def setUp( self ):
        self._creator=Avatar()
        self._creator.setId("creator")
        self._conf=Conference(self._creator)
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


def testsuite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicManagement))
    suite.addTest(unittest.makeSuite(TestWithdrawal))
    suite.addTest(unittest.makeSuite(TestSubmissionPrivileges))
    return suite
