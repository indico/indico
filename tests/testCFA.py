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

"""Contains tests about some typical "call for abstracts" scenarios.
"""

import unittest

import MaKaC.user as user
import MaKaC.conference as conference
import MaKaC.review as review
import MaKaC.errors as errors

from datetime import datetime
from pytz import timezone


class TestCFADirectives( unittest.TestCase ):
    """Tests the setting of the main CFA directives.
    """

    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._tz=timezone('UTC')
        self._conf.setTimezone('UTC')

    def tearDown( self ):
        pass

    def testEnableCFA( self ):
        cfa = self._conf.getAbstractMgr()
        #by default the CFA must be disabled
        self.assert_( not cfa.isActive() )
        #we enable it, so it must be enabled
        cfa.activeCFA()
        self.assert_( cfa.isActive() )
        #and now we deactivate it
        cfa.desactiveCFA()
        self.assert_( not cfa.isActive() )

    def testSubmissionPeriod( self ):
        cfa = self._conf.getAbstractMgr()
        #we set up the submission period 
        startDate = datetime(2004, 01, 01, tzinfo=self._tz)
        endDate = datetime(2004, 01, 03, tzinfo=self._tz)
        cfa.setStartSubmissionDate( startDate )
        cfa.setEndSubmissionDate( endDate )
        #we check a date within the submission period
        id = datetime(2004, 01, 02, tzinfo=self._tz)
        self.assert_( cfa.inSubmissionPeriod( id ) )
        #check for a date in the limit of the submission period
        id = datetime(2004, 01, 01, 0, 0, 0, tzinfo=self._tz)
        self.assert_( cfa.inSubmissionPeriod( id ) )
        id = datetime(2004, 01, 03, 23, 59, 59, tzinfo=self._tz)
        self.assert_( cfa.inSubmissionPeriod( id ) )
        #check for dates outside the submission period
        id = datetime(2003, 12, 31, 23, 59, 59, tzinfo=self._tz)
        self.assert_( not cfa.inSubmissionPeriod( id ) )
        id = datetime(2004, 01, 04, 00, 00, 00, tzinfo=self._tz)
        self.assert_( not cfa.inSubmissionPeriod( id ) )
        id = datetime(2005, 01, 04, 00, 00, 00, tzinfo=self._tz)
        self.assert_( not cfa.inSubmissionPeriod( id ) )


class TestAbstractSubmission( unittest.TestCase ):
    """Tests different abstract submission scenarios
    """

    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
    
    def testSimpleSubmission( self ):
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        #creation of a new abstract
        a = self._conf.getAbstractMgr().newAbstract( submitter )
        #setting of abstract tracks
        a.setTracks( [self._track1, self._track2] )
        #checking that the abstract is in the conference and its status is
        # submitted
        self.assert_( a in self._conf.getAbstractMgr().getAbstractList() )
        self.assert_( isinstance( a.getCurrentStatus(), review.AbstractStatusSubmitted ) )
        #checking that the abstract tracks are correctly set up
        self.assert_( a.isProposedForTrack( self._track1 ) )
        self.assert_( a.isProposedForTrack( self._track2 ) )
        self.assert_( not a.isProposedForTrack( self._track3 ) )
        #checking that the abstract is included in the track abstract list
        self.assert_( a.isProposedForTrack( self._track1 ) )
        self.assert_( a.isProposedForTrack( self._track2 ) )
        self.assert_( not a.isProposedForTrack( self._track3 ) )
        #checking that the submitter is the abstract submitter
        self.assert_( a.isSubmitter( submitter ) )
        #checking access privileges
        #checking modification privileges
    

class TestAbstractModification( unittest.TestCase ):
    """Tests different abstract modification scenarios
    """
    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        self._abstract = self._conf.getAbstractMgr().newAbstract( submitter )


    def testTrackAssignment( self ):
        #checks that abstract deal correclty with assigned tracks
        #setting the track assignment
        self._abstract.setTracks( [self._track1, self._track2] )
        self.assert_( self._abstract.isProposedForTrack( self._track1 ) )
        self.assert_( self._abstract.isProposedForTrack( self._track2 ) )
        #changing the track assignment
        self._abstract.setTracks( [self._track3, self._track2] )
        self.assert_( not self._abstract.isProposedForTrack( self._track1 ) )
        self.assert_( self._abstract.isProposedForTrack( self._track2 ) )
        self.assert_( self._abstract.isProposedForTrack( self._track3 ) )
        #removing of single tracks
        self._abstract.removeTrack( self._track1 )
        self.assert_( len( self._abstract.getTrackList() ) == 2 )
        self._abstract.removeTrack( self._track2 )
        self.assert_( not self._abstract.isProposedForTrack( self._track1 ) )
        self.assert_( not self._abstract.isProposedForTrack( self._track2 ) )
        self.assert_( self._track3 in self._abstract.getTrackList() )
        #adding single tracks
        self._abstract.addTrack( self._track3 )
        self.assert_( len( self._abstract.getTrackList() ) == 1 )
        self._abstract.addTrack( self._track1 )
        self.assert_( self._abstract.isProposedForTrack( self._track1 ) )
        self.assert_( not self._abstract.isProposedForTrack( self._track2 ) )
        self.assert_( self._abstract.isProposedForTrack( self._track3 ) )


class TestAbstractAcceptation( unittest.TestCase ):
    """Tests different abstract acceptation scenarios
    """
    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._ctOral = conference.ContributionType("oral", "", self._conf)
        self._ctPoster = conference.ContributionType("poster", "", self._conf)
        self._conf.addContribType( self._ctOral )
        self._conf.addContribType( self._ctPoster )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        self._abstract = self._conf.getAbstractMgr().newAbstract( submitter )

    def testBasicAcceptation( self ):
        self._abstract.setTitle( "test_title" )
        self._abstract.setField("content", "test_content" )
        self._abstract.setContribType( self._ctPoster )
        auth1 = self._abstract.newPrimaryAuthor()
        auth1.setData( firstName="test1_fn", surName="test1_sn",
                        email="test1_email", affiliation="test1_af",
                        address="test1_add", telephone="test1_phone",
                        fax = "test1_fax", title="test1_title" )
        self._abstract.addSpeaker( auth1 )
        auth2 = self._abstract.newCoAuthor()
        auth2.setData( firstName="test2_fn", surName="test2_sn",
                        email="test2_email", affiliation="test2_af",
                        address="test2_add", telephone="test2_phone",
                        fax = "test2_fax", title="test2_title" )
        #accepting an abstract for a certain track
        self._abstract.setTracks( [self._track1, self._track2] )
        res1 = user.Avatar()
        res1.setId( "res1" )
        self._abstract.accept( res1, self._track1, self._ctOral )
        #check the status is changed to accept
        status = self._abstract.getCurrentStatus()
        self.assert_( isinstance(status, review.AbstractStatusAccepted) )
        #check the track
        self.assert_( status.getTrack() == self._track1 )
        #check that a contribution has been created and has exactly the same
        #   data
        contrib = status.getContribution()
        self.assert_( contrib.getId() == self._abstract.getId() )
        self.assert_( contrib.getConference() == self._conf )
        self.assert_( contrib.getAbstract() == self._abstract )
        self.assert_( contrib in self._conf.getContributionList() )
        self.assert_( contrib.getTrack() == status.getTrack() )
        self.assert_( contrib.getTitle() == "test_title" )
        self.assert_( contrib.getDescription() == "test_content" )
        self.assert_( contrib.getType() == self._ctOral )
        c_auth = contrib.getPrimaryAuthorList()[0]
        self.assert_( c_auth.getTitle() == auth1.getTitle() )
        self.assert_( c_auth.getFirstName() == auth1.getFirstName() )
        self.assert_( c_auth.getFamilyName() == auth1.getSurName() )
        self.assert_( c_auth.getEmail() == auth1.getEmail() )
        self.assert_( c_auth.getAffiliation() == auth1.getAffiliation() )
        self.assert_( c_auth.getAddress() == auth1.getAddress() )
        self.assert_( c_auth.getPhone() == auth1.getTelephone() )
        self.assert_( len( contrib.getSpeakerList() ) == 1 )
        self.assert_( contrib.isSpeaker( c_auth )  )
        c_auth = contrib.getCoAuthorList()[0]
        self.assert_( c_auth.getTitle() == auth2.getTitle() )
        self.assert_( c_auth.getFirstName() == auth2.getFirstName() )
        self.assert_( c_auth.getFamilyName() == auth2.getSurName() )
        self.assert_( c_auth.getEmail() == auth2.getEmail() )
        self.assert_( c_auth.getAffiliation() == auth2.getAffiliation() )
        self.assert_( c_auth.getAddress() == auth2.getAddress() )
        self.assert_( c_auth.getPhone() == auth2.getTelephone() )

    def testIdCollission( self ):
        #checks that no collission with contributions can happen regarding 
        #   the ids
        contrib=conference.Contribution()
        self._conf.addContribution(contrib)
        res1=user.Avatar()
        res1.setId("res1")
        abstract=self._conf.getAbstractMgr().newAbstract(res1)
        #accepting an abstract for a certain track
        self._abstract.accept(res1,self._track1,self._ctOral)
        self.assert_(contrib.getId()!=abstract.getId())

    def testAcceptForNonProposedTrack( self ):
        #an abstract can be accepted for a track for which it is not proposed
        self._abstract.setTracks( [self._track1, self._track2] )
        self.assert_( not self._track3.hasAbstract( self._abstract ) )
        res1 = user.Avatar()
        res1.setId( "res1" )
        self._abstract.accept( res1, self._track3, self._ctOral )
        #check the status is changed to accept
        status = self._abstract.getCurrentStatus()
        self.assert_( isinstance(status, review.AbstractStatusAccepted) )
        #check the track
        self.assert_( status.getTrack() == self._track3 )
        #check the track list contains the track for which it was accepted
        self.assert_( self._track3.hasAbstract( self._abstract ) )


class TestAbstractDisplay(unittest.TestCase):
    """tests different abstract displaying scenarios.
    """
    
    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._track4 = self._conf.newTrack()
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        self._abstract = self._conf.getAbstractMgr().newAbstract( submitter )

    def testTrackOrder( self ):
        #tests the track sorting functions
        self._abstract.addTrack( self._track3 )
        self._abstract.addTrack( self._track1 )
        self._abstract.addTrack( self._track2 )
        l = self._abstract.getTrackListSorted()
        self.assert_( l[0] == self._track1 and l[1] == self._track2 \
                        and l[2] == self._track3 )


class TestAbstractWithdrawal(unittest.TestCase):
    """tests different abstract withdrawal scenarios.
    """
    
    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._ctOral = conference.ContributionType( "oral", "", self._conf )
        self._conf.addContribType( self._ctOral )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        self._abstract = self._conf.getAbstractMgr().newAbstract( submitter )

    def testNormal( self ):
        #tests the normal flow of events of the withdrawal TC
        av=user.Avatar()
        self._abstract.withdraw( av,"hola" )
        self.assert_( isinstance( self._abstract.getCurrentStatus(), review.AbstractStatusWithdrawn ) )

    def testCannotAccWithdrawn( self ):
        #tests that a withdrawn abstract cannot be accepted
        self._abstract.withdraw( None,"hola" )
        cm = user.Avatar()
        cm.setId("cm")
        self.assertRaises( errors.MaKaCError, self._abstract.accept, cm, self._track1, self._ctOral )

    def testCannotRejWithdrawn( self ):
        #tests that a withdrawn abstract cannot be rejected
        self._abstract.withdraw( None,"hola" )
        cm = user.Avatar()
        cm.setId("cm")
        self.assertRaises( errors.MaKaCError, self._abstract.reject, cm )

    def testAccepted(self):
        #tests that it is possible to withdraw an accepted abstract and that it
        #   provokes the withdrawal of the associated contribution
        av=user.Avatar()
        self._abstract.accept(av,self._track1,self._ctOral)
        contrib=self._abstract.getContribution()
        self.assert_(not isinstance(contrib,conference.ContribStatusWithdrawn))
        self._abstract.withdraw(av,"hola")
        absStatus=self._abstract.getCurrentStatus()
        contribStatus=contrib.getCurrentStatus()
        self.assert_(isinstance(absStatus,review.AbstractStatusWithdrawn))
        self.assert_(isinstance(contribStatus,conference.ContribStatusWithdrawn))


class TestAbstractRecovery(unittest.TestCase):
    """tests different abstract recovery scenarios.
    """
    
    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        self._abstract = self._conf.getAbstractMgr().newAbstract( submitter )
        self._abstract.addTrack( self._track1 )
        self._abstract.addTrack( self._track2 )
        self._abstract.addTrack( self._track3 )

    def testNormal( self ):
        #tests the abstract recovery normal flow
        av=user.Avatar()
        self._abstract.withdraw(av)
        self._abstract.recover()
        self.assert_( isinstance( self._abstract.getCurrentStatus(), review.AbstractStatusSubmitted ) )

    def testTackJudgementClearing( self ):
        #tests that after recovering an abstract which had some judgements
        #   they are cleared.
        tc = user.Avatar()
        tc.setId( "tc" )
        self._abstract.proposeToAccept( tc, self._track1, "oral" )
        self._abstract.proposeToAccept( tc, self._track3, "oral" )
        self._abstract.withdraw(tc)
        self._abstract.recover()
        self.assert_( self._abstract.hasTrack( self._track1 ) )
        self.assert_( self._abstract.hasTrack( self._track3 ) )
        self.assert_( self._track1.hasAbstract( self._abstract ) )
        self.assert_( self._track3.hasAbstract( self._abstract ) )
        self.assert_( self._abstract.getNumJudgements() == 2 )


class TestAbstractReallocation(unittest.TestCase):
    """tests different abstract reallocation scenarios.
    """
    
    def setUp( self ):
        av = user.Avatar()
        self._conf = conference.Conference( av )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        submitter = user.Avatar()
        submitter.setId( "submitter" )
        self._abstract = self._conf.getAbstractMgr().newAbstract( submitter )
        self._abstract.addTrack( self._track1 )
    
    def testSimpleReallocation( self ):
        tc1 = user.Avatar()
        tc1.setId( "tc1" )
        self._abstract.proposeForOtherTracks( tc1, self._track1, "test", \
            [self._track2, self._track3] )
        self.assert_( self._abstract.hasTrack( self._track1 ) )
        self.assert_( self._abstract.hasTrack( self._track2 ) )
        self.assert_( self._abstract.hasTrack( self._track3 ) )
        self.assert_( self._abstract.getNumJudgements() == 1 )
        t1jud = self._abstract.getTrackJudgement( self._track1 )
        self.assert_( isinstance( t1jud, review.AbstractReallocation ) )
        self.assert_( t1jud.getResponsible() == tc1 )
        self.assert_( self._track2 in t1jud.getProposedTrackList() )
        self.assert_( self._track3 in t1jud.getProposedTrackList() )
        self.assert_( self._track1 not in t1jud.getProposedTrackList() )
        status = self._abstract.getCurrentStatus()
        self.assert_( isinstance( status, review.AbstractStatusUnderReview ) )
        t2_tl = self._abstract.getReallocationTargetedList( self._track2 )
        self.assert_( t1jud in t2_tl )
        t3_tl = self._abstract.getReallocationTargetedList( self._track3 )
        self.assert_( t1jud in t3_tl )
        t1_tl = self._abstract.getReallocationTargetedList( self._track1 )
        self.assert_( t1jud not in t1_tl )
        
   
class TestNotification(unittest.TestCase):
    """
    """
    
    def setUp( self ):
        from MaKaC.user import Avatar
        av = Avatar()
        from MaKaC.conference import Conference
        self._conf = Conference( av )
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        absMgr=self._conf.getAbstractMgr()
        self._contribTypeOral="oral"
        self._contribTypePoster="poster"
        #absMgr.addContribType(self._contribTypeOral)
        #absMgr.addContribType(self._contribTypePoster)
        #from MaKaC.user import Avatar
        #self._submitter = Avatar()
        #self._submitter.setId( "submitter" )
        #self._abstract=self._conf.getAbstractMgr().newAbstract(self._submitter)
        #self._abstract.addTrack(self._track1)
    
    def testBasicManagement( self ):
        #test adding and removing notification templates
        from MaKaC.review import NotificationTemplate
        tpl1=NotificationTemplate()
        absMgr=self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        self.assert_(tpl1 in absMgr.getNotificationTplList())
        tpl2=NotificationTemplate()
        absMgr.addNotificationTpl(tpl2)
        absMgr.removeNotificationTpl(tpl1)
        self.assert_(tpl2 in absMgr.getNotificationTplList())
        self.assert_(tpl1 not in absMgr.getNotificationTplList())
        self.assert_(tpl1!=absMgr.getNotificationTplById(tpl1.getId()))
        self.assert_(tpl2==absMgr.getNotificationTplById(tpl2.getId()))
    
    def testTplConditions(self):
        #test adding and removing conditions to templates
        from MaKaC.review import NotificationTemplate
        tpl1=NotificationTemplate()
        tpl2=NotificationTemplate()
        absMgr=self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        absMgr.addNotificationTpl(tpl2)
        from MaKaC.review import NotifTplCondAccepted,NotifTplCondRejected
        cond1=NotifTplCondAccepted(contribType=self._contribTypeOral)
        cond2=NotifTplCondRejected()
        tpl1.addCondition(cond1)
        tpl2.addCondition(cond2)
        from MaKaC.user import Avatar
        submitter=Avatar()
        submitter.setId("submitter")
        abs1=absMgr.newAbstract(submitter)
        tplRes=absMgr.getNotifTplForAbstract(abs1)
        self.assert_(tplRes is None)
        abs1.accept(submitter,self._track1,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs1)==tpl1)
        abs2=absMgr.newAbstract(submitter)
        abs2.accept(submitter,self._track1,self._contribTypePoster)
        self.assert_(not absMgr.getNotifTplForAbstract(abs2))
        abs3=absMgr.newAbstract(submitter)
        abs3.reject(submitter)
        self.assert_(absMgr.getNotifTplForAbstract(abs3)==tpl2)

    def testTplCondAccTrack(self):
        #test different possibilities when a condition has been stablished for
        #   a certain track
        from MaKaC.review import NotificationTemplate
        tpl1=NotificationTemplate()
        absMgr=self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        from MaKaC.review import NotifTplCondAccepted
        cond1=NotifTplCondAccepted(track=self._track1,contribType=self._contribTypeOral)
        tpl1.addCondition(cond1)
        from MaKaC.user import Avatar
        submitter=Avatar()
        submitter.setId("submitter")
        abs1=absMgr.newAbstract(submitter)
        abs1.accept(submitter,self._track1,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs1)==tpl1)
        abs2=absMgr.newAbstract(submitter)
        abs2.accept(submitter,self._track1,self._contribTypePoster)
        self.assert_(absMgr.getNotifTplForAbstract(abs2) is None)
        abs3=absMgr.newAbstract(submitter)
        abs3.accept(submitter,self._track2,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs3) is None)

    def testTplCondAccAnyTrack(self):
        #test different possibilities when a condition has been stablished for
        #   a notif tpl on any track
        from MaKaC.review import NotificationTemplate
        tpl1=NotificationTemplate()
        absMgr=self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        from MaKaC.review import NotifTplCondAccepted
        cond1=NotifTplCondAccepted(contribType=self._contribTypeOral)
        tpl1.addCondition(cond1)
        from MaKaC.user import Avatar
        submitter=Avatar()
        submitter.setId("submitter")
        abs1=absMgr.newAbstract(submitter)
        abs1.accept(submitter,self._track1,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs1)==tpl1)
        abs2=absMgr.newAbstract(submitter)
        abs2.accept(submitter,self._track1,self._contribTypePoster)
        self.assert_(absMgr.getNotifTplForAbstract(abs2) is None)
        abs3=absMgr.newAbstract(submitter)
        abs3.accept(submitter,self._track2,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs3)==tpl1)
        abs4=absMgr.newAbstract(submitter)
        abs4.accept(submitter,None,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs4)==tpl1)

    def testTplCondAccNoneTrack(self):
        #test different possibilities when a condition has been stablished for
        #   a notif tpl on none track
        from MaKaC.review import NotificationTemplate
        tpl1=NotificationTemplate()
        absMgr=self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        from MaKaC.review import NotifTplCondAccepted
        cond1=NotifTplCondAccepted(track=None,contribType=self._contribTypeOral)
        tpl1.addCondition(cond1)
        from MaKaC.user import Avatar
        submitter=Avatar()
        submitter.setId("submitter")
        abs1=absMgr.newAbstract(submitter)
        abs1.accept(submitter,self._track1,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs1) is None)
        abs2=absMgr.newAbstract(submitter)
        abs2.accept(submitter,self._track1,self._contribTypePoster)
        self.assert_(absMgr.getNotifTplForAbstract(abs2) is None)
        abs3=absMgr.newAbstract(submitter)
        abs3.accept(submitter,None,self._contribTypeOral)
        self.assert_(absMgr.getNotifTplForAbstract(abs3)==tpl1)


class TestAuthorSearch(unittest.TestCase):
    """
    """
    
    def setUp( self ):
        self._creator=user.Avatar()
        self._conf=conference.Conference(self._creator)

    def testBasicSearch(self):
        absMgr=self._conf.getAbstractMgr()
        abs1=absMgr.newAbstract(self._creator)
        auth1=abs1.newPrimaryAuthor(firstName="a",surName="a")
        auth2=abs1.newPrimaryAuthor(firstName="b",surName="b")
        auth3=abs1.newCoAuthor(firstName="b",surName="b")
        abs2=absMgr.newAbstract(self._creator)
        self.assert_(len(absMgr.getAbstractsMatchingAuth(""))==2)
        self.assert_(len(absMgr.getAbstractsMatchingAuth("a"))==1)
        self.assert_(abs1 in absMgr.getAbstractsMatchingAuth("a"))
        self.assert_(len(absMgr.getAbstractsMatchingAuth("B"))==1)
        self.assert_(abs1 in absMgr.getAbstractsMatchingAuth("b"))
        self.assert_(auth3 not in absMgr.getAbstractsMatchingAuth("b"))
        auth1.setSurName("c")
        self.assert_(len(absMgr.getAbstractsMatchingAuth("a"))==1)
        self.assert_(abs1 in absMgr.getAbstractsMatchingAuth("a"))
        self.assert_(len(absMgr.getAbstractsMatchingAuth("B"))==1)
        self.assert_(abs1 in absMgr.getAbstractsMatchingAuth("b"))
        self.assert_(len(absMgr.getAbstractsMatchingAuth("c"))==1)
        self.assert_(abs1 in absMgr.getAbstractsMatchingAuth("C"))
        abs1._removePrimaryAuthor(auth1)
        self.assert_(len(absMgr.getAbstractsMatchingAuth(""))==2)
        self.assert_(len(absMgr.getAbstractsMatchingAuth("a"))==0)
        self.assert_(abs1 not in absMgr.getAbstractsMatchingAuth("a"))
        self.assert_(len(absMgr.getAbstractsMatchingAuth("B"))==1)
        self.assert_(abs1 in absMgr.getAbstractsMatchingAuth("b"))
        abs1.clearAuthors()
        self.assert_(len(absMgr.getAbstractsMatchingAuth(""))==2)
        self.assert_(len(absMgr.getAbstractsMatchingAuth("a"))==0)
        self.assert_(abs1 not in absMgr.getAbstractsMatchingAuth("a"))
        self.assert_(len(absMgr.getAbstractsMatchingAuth("B"))==0)
        self.assert_(abs1 not in absMgr.getAbstractsMatchingAuth("b"))

def testsuite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestCFADirectives) )
    suite.addTest( unittest.makeSuite(TestAbstractSubmission) )
    suite.addTest( unittest.makeSuite(TestAbstractModification) )
    suite.addTest( unittest.makeSuite(TestAbstractAcceptation) )
    suite.addTest( unittest.makeSuite(TestAbstractDisplay) )
    suite.addTest( unittest.makeSuite(TestAbstractWithdrawal) )
    suite.addTest( unittest.makeSuite(TestAbstractRecovery) )
    suite.addTest( unittest.makeSuite(TestAbstractReallocation) )
    suite.addTest( unittest.makeSuite(TestNotification) )
    suite.addTest( unittest.makeSuite(TestAuthorSearch) )
    return suite
