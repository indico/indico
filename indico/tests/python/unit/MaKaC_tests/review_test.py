# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
Contains tests about some typical "call for abstracts" scenarios.
"""

from datetime import datetime
from pytz import timezone
from indico.tests.env import *

from MaKaC.user import Avatar
from MaKaC.review import NotificationTemplate, NotifTplCondAccepted
from indico.tests.python.unit.util import IndicoTestCase, with_context
from MaKaC.conference import AvatarHolder, AdminList, Conference, Contribution, ConferenceHolder

import MaKaC.conference as conference
import MaKaC.review as review
import MaKaC.errors as errors


class TestCFADirectives(IndicoTestCase):
    """Tests the setting of the main CFA directives.
    """
    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestCFADirectives, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._stopDBReq()

    @with_context('database')
    def testEnableCFA(self):
        cfa = self._conf.getAbstractMgr()
        #by default the CFA must be disabled
        self.assertFalse(cfa.isActive())
        #we enable it, so it must be enabled
        cfa.activeCFA()
        self.assertTrue(cfa.isActive())
        #and now we deactivate it
        cfa.desactiveCFA()
        self.assertFalse(cfa.isActive())

    @with_context('database')
    def testSubmissionPeriod(self):
        cfa = self._conf.getAbstractMgr()
        #we set up the submission period
        startDate = datetime(2004, 01, 01, tzinfo=timezone('UTC'))
        endDate = datetime(2004, 01, 03, tzinfo=timezone('UTC'))
        cfa.setStartSubmissionDate(startDate)
        cfa.setEndSubmissionDate(endDate)
        #we check a date within the submission period
        id = datetime(2004, 01, 02, tzinfo=timezone('UTC'))
        self.assertTrue(cfa.inSubmissionPeriod(id))
        #check for a date in the limit of the submission period
        id = datetime(2004, 01, 01, 0, 0, 0, tzinfo=timezone('UTC'))
        self.assertTrue(cfa.inSubmissionPeriod(id))
        id = datetime(2004, 01, 03, 23, 59, 59, tzinfo=timezone('UTC'))
        self.assertTrue(cfa.inSubmissionPeriod(id))
        #check for dates outside the submission period
        id = datetime(2003, 12, 31, 23, 59, 59, tzinfo=timezone('UTC'))
        self.assertFalse(cfa.inSubmissionPeriod(id))
        id = datetime(2004, 01, 04, 00, 00, 00, tzinfo=timezone('UTC'))
        self.assertFalse(cfa.inSubmissionPeriod(id))
        id = datetime(2005, 01, 04, 00, 00, 00, tzinfo=timezone('UTC'))
        self.assertFalse(cfa.inSubmissionPeriod(id))


class TestAbstractSubmission(IndicoTestCase):
    """Tests different abstract submission scenarios
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractSubmission, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()

        self._stopDBReq()

    @with_context('database')
    def testSimpleSubmission(self):
        #creation of a new abstract
        a = self._conf.getAbstractMgr().newAbstract(self._avatar)
        #setting of abstract tracks
        a.setTracks([self._track1, self._track2])
        #checking that the abstract is in the conference and its status is
        # submitted
        self.assertIn(a, self._conf.getAbstractMgr().getAbstractList())
        self.assertIsInstance(a.getCurrentStatus(), review.AbstractStatusSubmitted)
        #checking that the abstract tracks are correctly set up
        self.assertTrue(a.isProposedForTrack(self._track1))
        self.assertTrue(a.isProposedForTrack(self._track2))
        self.assertFalse(a.isProposedForTrack(self._track3))
        #checking that the abstract is included in the track abstract list
        self.assertTrue(a.isProposedForTrack(self._track1))
        self.assertTrue(a.isProposedForTrack(self._track2))
        self.assertFalse(a.isProposedForTrack(self._track3))
        #checking that the submitter is the abstract submitter
        self.assertTrue(a.isSubmitter(self._avatar))
        #checking access privileges
        #checking modification privileges


class TestAbstractModification(IndicoTestCase):
    """Tests different abstract modification scenarios
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractModification, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._abstract = self._conf.getAbstractMgr().newAbstract(avatar)

        self._stopDBReq()

    @with_context('database')
    def testTrackAssignment(self):
        #checks that abstract deal correclty with assigned tracks
        #setting the track assignment
        self._abstract.setTracks([self._track1, self._track2])
        self.assertTrue(self._abstract.isProposedForTrack(self._track1))
        self.assertTrue(self._abstract.isProposedForTrack(self._track2))
        #changing the track assignment
        self._abstract.setTracks([self._track3, self._track2])
        self.assertFalse(self._abstract.isProposedForTrack(self._track1))
        self.assertTrue(self._abstract.isProposedForTrack(self._track2))
        self.assertTrue(self._abstract.isProposedForTrack(self._track3))
        #removing of single tracks
        self._abstract.removeTrack(self._track1)
        self.assertEqual(len(self._abstract.getTrackList()), 2)
        self._abstract.removeTrack(self._track2)
        self.assertFalse(self._abstract.isProposedForTrack(self._track1))
        self.assertFalse(self._abstract.isProposedForTrack(self._track2))
        self.assertIn(self._track3, self._abstract.getTrackList())
        #adding single tracks
        self._abstract.addTrack(self._track3)
        self.assertEqual(len(self._abstract.getTrackList()), 1)
        self._abstract.addTrack(self._track1)
        self.assertTrue(self._abstract.isProposedForTrack(self._track1))
        self.assertFalse(self._abstract.isProposedForTrack(self._track2))
        self.assertTrue(self._abstract.isProposedForTrack(self._track3))


class TestAbstractAcceptation(IndicoTestCase):
    """Tests different abstract acceptation scenarios
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractAcceptation, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._ctOral = conference.ContributionType("oral", "", self._conf)
        self._ctPoster = conference.ContributionType("poster", "", self._conf)
        self._conf.addContribType(self._ctOral)
        self._conf.addContribType(self._ctPoster)
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._abstract = self._conf.getAbstractMgr().newAbstract(avatar)

        self._stopDBReq()

    @with_context('database')
    def testBasicAcceptation(self):
        self._abstract.setTitle("test_title")
        self._abstract.setField("content", "test_content")
        self._abstract.setContribType(self._ctPoster)
        auth1 = self._abstract.newPrimaryAuthor()
        auth1.setData(firstName="test1_fn", surName="test1_sn",
                      email="test1_email", affiliation="test1_af",
                      address="test1_add", telephone="test1_phone",
                      fax="test1_fax", title="test1_title")
        self._abstract.addSpeaker(auth1)
        auth2 = self._abstract.newCoAuthor()
        auth2.setData(firstName="test2_fn", surName="test2_sn",
                      email="test2_email", affiliation="test2_af",
                      address="test2_add", telephone="test2_phone",
                      fax="test2_fax", title="test2_title")
        #accepting an abstract for a certain track
        self._abstract.setTracks([self._track1, self._track2])
        res1 = self._avatar
        self._abstract.accept(res1, self._track1, self._ctOral)
        #check the status is changed to accept
        status = self._abstract.getCurrentStatus()
        self.assertIsInstance(status, review.AbstractStatusAccepted)
        #check the track
        self.assertEqual(status.getTrack(), self._track1)
        #check that a contribution has been created and has exactly the same
        #   data
        contrib = status.getContribution()
        self.assertEqual(contrib.getId(), self._abstract.getId())
        self.assertEqual(contrib.getConference(), self._conf)
        self.assertEqual(contrib.getAbstract(), self._abstract)
        self.assertIn(contrib, self._conf.getContributionList())
        self.assertEqual(contrib.getTrack(), status.getTrack())
        self.assertEqual(contrib.getTitle(), "test_title")
        self.assertEqual(contrib.getDescription(), "test_content")
        self.assertEqual(contrib.getType(), self._ctOral)
        c_auth = contrib.getPrimaryAuthorList()[0]
        self.assertEqual(c_auth.getTitle(), auth1.getTitle())
        self.assertEqual(c_auth.getFirstName(), auth1.getFirstName())
        self.assertEqual(c_auth.getFamilyName(), auth1.getSurName())
        self.assertEqual(c_auth.getEmail(), auth1.getEmail())
        self.assertEqual(c_auth.getAffiliation(), auth1.getAffiliation())
        self.assertEqual(c_auth.getAddress(), auth1.getAddress())
        self.assertEqual(c_auth.getPhone(), auth1.getTelephone())
        self.assertEqual(len(contrib.getSpeakerList()), 1)
        self.assertTrue(contrib.isSpeaker(c_auth))
        c_auth = contrib.getCoAuthorList()[0]
        self.assertEqual(c_auth.getTitle(), auth2.getTitle())
        self.assertEqual(c_auth.getFirstName(), auth2.getFirstName())
        self.assertEqual(c_auth.getFamilyName(), auth2.getSurName())
        self.assertEqual(c_auth.getEmail(), auth2.getEmail())
        self.assertEqual(c_auth.getAffiliation(), auth2.getAffiliation())
        self.assertEqual(c_auth.getAddress(), auth2.getAddress())
        self.assertEqual(c_auth.getPhone(), auth2.getTelephone())

    @with_context('database')
    def testIdCollission(self):
        #checks that no collission with contributions can happen regarding
        #   the ids
        contrib = conference.Contribution()
        self._conf.addContribution(contrib)
        res1 = self._avatar
        abstract = self._conf.getAbstractMgr().newAbstract(res1)
        #accepting an abstract for a certain track
        self._abstract.accept(res1, self._track1, self._ctOral)
        self.assertNotEqual(contrib.getId(), abstract.getId())

    @with_context('database')
    def testAcceptForNonProposedTrack(self):
        #an abstract can be accepted for a track for which it is not proposed
        self._abstract.setTracks([self._track1, self._track2])
        self.assertFalse(self._track3.hasAbstract(self._abstract))
        res1 = self._avatar
        self._abstract.accept(res1, self._track3, self._ctOral)
        #check the status is changed to accept
        status = self._abstract.getCurrentStatus()
        self.assertIsInstance(status, review.AbstractStatusAccepted)
        #check the track
        self.assertEqual(status.getTrack(), self._track3)
        #check the track list contains the track for which it was accepted
        self.assertTrue(self._track3.hasAbstract(self._abstract))


class TestAbstractDisplay(IndicoTestCase):
    """tests different abstract displaying scenarios.
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractDisplay, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._track4 = self._conf.newTrack()
        self._abstract = self._conf.getAbstractMgr().newAbstract(avatar)

        self._stopDBReq()

    @with_context('database')
    def testTrackOrder(self):
        #tests the track sorting functions
        self._abstract.addTrack(self._track3)
        self._abstract.addTrack(self._track1)
        self._abstract.addTrack(self._track2)
        l = self._abstract.getTrackListSorted()
        self.assertTrue(l[0] == self._track1 and l[1] == self._track2
                        and l[2] == self._track3)


class TestAbstractWithdrawal(IndicoTestCase):
    """tests different abstract withdrawal scenarios.
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractWithdrawal, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._ctOral = conference.ContributionType("oral", "", self._conf)
        self._conf.addContribType(self._ctOral)
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._abstract = self._conf.getAbstractMgr().newAbstract(avatar)

        self._stopDBReq()

    @with_context('database')
    def testNormal(self):
        #tests the normal flow of events of the withdrawal TC
        self._abstract.withdraw(self._avatar, "hola")
        self.assertIsInstance(self._abstract.getCurrentStatus(), review.AbstractStatusWithdrawn)

    @with_context('database')
    def testCannotAccWithdrawn(self):
        #tests that a withdrawn abstract cannot be accepted
        self._abstract.withdraw(None, "hola")
        self.assertRaises(errors.MaKaCError, self._abstract.accept, self._avatar, self._track1, self._ctOral)

    @with_context('database')
    def testCannotRejWithdrawn(self):
        #tests that a withdrawn abstract cannot be rejected
        self._abstract.withdraw(None, "hola")
        self.assertRaises(errors.MaKaCError, self._abstract.reject, self._avatar)

    @with_context('database')
    def testAccepted(self):
        #tests that it is possible to withdraw an accepted abstract and that it
        #   provokes the withdrawal of the associated contribution
        self._abstract.accept(self._avatar, self._track1, self._ctOral)
        contrib = self._abstract.getContribution()
        self.assertNotIsInstance(contrib, conference.ContribStatusWithdrawn)
        self._abstract.withdraw(self._avatar, "hola")
        absStatus = self._abstract.getCurrentStatus()
        contribStatus = contrib.getCurrentStatus()
        self.assertIsInstance(absStatus, review.AbstractStatusWithdrawn)
        self.assertIsInstance(contribStatus, conference.ContribStatusWithdrawn)


class TestAbstractWithdrawal(IndicoTestCase):
    """tests different abstract recovery scenarios.
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractWithdrawal, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._abstract = self._conf.getAbstractMgr().newAbstract(avatar)
        self._abstract.addTrack(self._track1)
        self._abstract.addTrack(self._track2)
        self._abstract.addTrack(self._track3)

        self._stopDBReq()

    @with_context('database')
    def testNormal(self):
        #tests the abstract recovery normal flow
        self._abstract.withdraw(self._avatar)
        self._abstract.recover()
        self.assertIsInstance(self._abstract.getCurrentStatus(), review.AbstractStatusSubmitted)

    @with_context('database')
    def testTackJudgementClearing(self):
        #tests that after recovering an abstract which had some judgements
        #   they are cleared.
        self._abstract.proposeToAccept(self._avatar, self._track1, "oral")
        self._abstract.proposeToAccept(self._avatar, self._track3, "oral")
        self._abstract.withdraw(self._avatar)
        self._abstract.recover()
        self.assertTrue(self._abstract.hasTrack(self._track1))
        self.assertTrue(self._abstract.hasTrack(self._track3))
        self.assertTrue(self._track1.hasAbstract(self._abstract))
        self.assertTrue(self._track3.hasAbstract(self._abstract))
        self.assertEqual(self._abstract.getNumJudgements(), 2)


class TestAbstractReallocation(IndicoTestCase):
    """tests different abstract reallocation scenarios.
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractReallocation, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._conf = conference.Conference(avatar)
        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        self._abstract = self._conf.getAbstractMgr().newAbstract(avatar)
        self._abstract.addTrack(self._track1)

        self._stopDBReq()

    @with_context('database')
    def testSimpleReallocation(self):
        self._abstract.proposeForOtherTracks(self._avatar, self._track1, "test",
                                             [self._track2, self._track3])
        self.assertTrue(self._abstract.hasTrack(self._track1))
        self.assertTrue(self._abstract.hasTrack(self._track2))
        self.assertTrue(self._abstract.hasTrack(self._track3))
        self.assertEqual(self._abstract.getNumJudgements(), 1)
        t1jud = self._abstract.getTrackJudgement(self._track1)
        self.assertIsInstance(t1jud, review.AbstractReallocation)
        self.assertEqual(t1jud.getResponsible(), self._avatar)
        self.assertIn(self._track2, t1jud.getProposedTrackList())
        self.assertIn(self._track3, t1jud.getProposedTrackList())
        self.assertNotIn(self._track1, t1jud.getProposedTrackList())
        status = self._abstract.getCurrentStatus()
        self.assertIsInstance(status, review.AbstractStatusUnderReview)
        t2_tl = self._abstract.getReallocationTargetedList(self._track2)
        self.assertIn(t1jud, t2_tl)
        t3_tl = self._abstract.getReallocationTargetedList(self._track3)
        self.assertIn(t1jud, t3_tl)
        t1_tl = self._abstract.getReallocationTargetedList(self._track1)
        self.assertNotIn(t1jud, t1_tl)


class TestNotification(IndicoTestCase):
    """
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestNotification, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()
        absMgr = self._conf.getAbstractMgr()
        self._contribTypeOral = "oral"
        self._contribTypePoster = "poster"

        self._stopDBReq()
        #absMgr.addContribType(self._contribTypeOral)
        #absMgr.addContribType(self._contribTypePoster)
        #from MaKaC.user import Avatar
        #self._submitter = Avatar()
        #self._submitter.setId( "submitter" )
        #self._abstract=self._conf.getAbstractMgr().newAbstract(self._submitter)
        #self._abstract.addTrack(self._track1)

    @with_context('database')
    def testBasicManagement(self):
        #test adding and removing notification templates
        tpl1 = NotificationTemplate()
        absMgr = self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        self.assertIn(tpl1, absMgr.getNotificationTplList())
        tpl2 = NotificationTemplate()
        absMgr.addNotificationTpl(tpl2)
        absMgr.removeNotificationTpl(tpl1)
        self.assertIn(tpl2, absMgr.getNotificationTplList())
        self.assertNotIn(tpl1, absMgr.getNotificationTplList())
        self.assertNotEqual(tpl1, absMgr.getNotificationTplById(tpl1.getId()))
        self.assertEqual(tpl2, absMgr.getNotificationTplById(tpl2.getId()))

    @with_context('database')
    def testTplConditions(self):
        #test adding and removing conditions to templates
        from MaKaC.review import NotificationTemplate
        tpl1 = NotificationTemplate()
        tpl2 = NotificationTemplate()
        absMgr = self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        absMgr.addNotificationTpl(tpl2)
        from MaKaC.review import NotifTplCondAccepted, NotifTplCondRejected
        cond1 = NotifTplCondAccepted(contribType=self._contribTypeOral)
        cond2 = NotifTplCondRejected()
        tpl1.addCondition(cond1)
        tpl2.addCondition(cond2)
        from MaKaC.user import Avatar
        abs1 = absMgr.newAbstract(self._avatar)
        tplRes = absMgr.getNotifTplForAbstract(abs1)
        self.assertIsNone(tplRes)
        abs1.accept(self._avatar, self._track1, self._contribTypeOral)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs1), tpl1)
        abs2 = absMgr.newAbstract(self._avatar)
        abs2.accept(self._avatar, self._track1, self._contribTypePoster)
        self.assertFalse(absMgr.getNotifTplForAbstract(abs2))
        abs3 = absMgr.newAbstract(self._avatar)
        abs3.reject(self._avatar)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs3), tpl2)

    @with_context('database')
    def testTplCondAccTrack(self):
        #test different possibilities when a condition has been stablished for
        #   a certain track
        tpl1 = NotificationTemplate()
        absMgr = self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        cond1 = NotifTplCondAccepted(track=self._track1, contribType=self._contribTypeOral)
        tpl1.addCondition(cond1)
        abs1 = absMgr.newAbstract(self._avatar)
        abs1.accept(self._avatar, self._track1, self._contribTypeOral)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs1), tpl1)
        abs2 = absMgr.newAbstract(self._avatar)
        abs2.accept(self._avatar, self._track1, self._contribTypePoster)
        self.assertIsNone(absMgr.getNotifTplForAbstract(abs2))
        abs3 = absMgr.newAbstract(self._avatar)
        abs3.accept(self._avatar, self._track2, self._contribTypeOral)
        self.assertIsNone(absMgr.getNotifTplForAbstract(abs3))

    @with_context('database')
    def testTplCondAccAnyTrack(self):
        #test different possibilities when a condition has been stablished for
        #   a notif tpl on any track
        tpl1 = NotificationTemplate()
        absMgr = self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        cond1 = NotifTplCondAccepted(contribType=self._contribTypeOral)
        tpl1.addCondition(cond1)
        abs1 = absMgr.newAbstract(self._avatar)
        abs1.accept(self._avatar, self._track1, self._contribTypeOral)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs1), tpl1)
        abs2 = absMgr.newAbstract(self._avatar)
        abs2.accept(self._avatar, self._track1, self._contribTypePoster)
        self.assertIsNone(absMgr.getNotifTplForAbstract(abs2))
        abs3 = absMgr.newAbstract(self._avatar)
        abs3.accept(self._avatar, self._track2, self._contribTypeOral)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs3), tpl1)
        abs4 = absMgr.newAbstract(self._avatar)
        abs4.accept(self._avatar, None, self._contribTypeOral)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs4), tpl1)

    @with_context('database')
    def testTplCondAccNoneTrack(self):
        #test different possibilities when a condition has been stablished for
        #   a notif tpl on none track
        tpl1 = NotificationTemplate()
        absMgr = self._conf.getAbstractMgr()
        absMgr.addNotificationTpl(tpl1)
        cond1 = NotifTplCondAccepted(track=None, contribType=self._contribTypeOral)
        tpl1.addCondition(cond1)
        abs1 = absMgr.newAbstract(self._avatar)
        abs1.accept(self._avatar, self._track1, self._contribTypeOral)
        self.assertIsNone(absMgr.getNotifTplForAbstract(abs1))
        abs2 = absMgr.newAbstract(self._avatar)
        abs2.accept(self._avatar, self._track1, self._contribTypePoster)
        self.assertIsNone(absMgr.getNotifTplForAbstract(abs2))
        abs3 = absMgr.newAbstract(self._avatar)
        abs3.accept(self._avatar, None, self._contribTypeOral)
        self.assertEqual(absMgr.getNotifTplForAbstract(abs3), tpl1)


class TestAuthorSearch(IndicoTestCase):

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAuthorSearch, self).setUp()

        self._startDBReq()

        # Get dummy user
        ah = AvatarHolder()
        avatar = ah.getById(0)
        setattr(self, '_avatar', avatar)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._stopDBReq()

    @with_context('database')
    def testBasicSearch(self):
        absMgr = self._conf.getAbstractMgr()
        abs1 = absMgr.newAbstract(self._avatar)
        auth1 = abs1.newPrimaryAuthor(firstName="a", surName="a")
        auth2 = abs1.newPrimaryAuthor(firstName="b", surName="b")
        auth3 = abs1.newCoAuthor(firstName="b", surName="b")
        abs2 = absMgr.newAbstract(self._avatar)
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("")), 2)
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("a")), 1)
        self.assertIn(abs1, absMgr.getAbstractsMatchingAuth("a"))
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("B")), 1)
        self.assertIn(abs1, absMgr.getAbstractsMatchingAuth("b"))
        self.assertNotIn(auth3, absMgr.getAbstractsMatchingAuth("b"))
        auth1.setSurName("c")
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("a")), 1)
        self.assertIn(abs1, absMgr.getAbstractsMatchingAuth("a"))
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("B")), 1)
        self.assertIn(abs1, absMgr.getAbstractsMatchingAuth("b"))
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("c")), 1)
        self.assertIn(abs1, absMgr.getAbstractsMatchingAuth("C"))
        abs1._removePrimaryAuthor(auth1)
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("")), 2)
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("a")), 0)
        self.assertNotIn(abs1, absMgr.getAbstractsMatchingAuth("a"))
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("B")), 1)
        self.assertIn(abs1, absMgr.getAbstractsMatchingAuth("b"))
        abs1.clearAuthors()
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("")), 2)
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("a")), 0)
        self.assertNotIn(abs1, absMgr.getAbstractsMatchingAuth("a"))
        self.assertEqual(len(absMgr.getAbstractsMatchingAuth("B")), 0)
        self.assertNotIn(abs1, absMgr.getAbstractsMatchingAuth("b"))

class TestAbstractJudgements(IndicoTestCase):
    """Tests different abstract judgements scenarios
    """

    _requires = ['db.Database', 'db.DummyUser']

    def setUp(self):
        super(TestAbstractJudgements, self).setUp()

        self._startDBReq()

        # Get dummy user and create another one
        ah = AvatarHolder()
        avatar1 = ah.getById(0)
        avatar2 = Avatar()
        avatar2.setName("fake-2")
        avatar2.setSurName("fake")
        avatar2.setOrganisation("fake")
        avatar2.setLang("en_GB")
        avatar2.setEmail("fake2@fake.fake")
        avatar2.setId("fake-2")
        ah.add(avatar2)
        setattr(self, '_avatar1', avatar1)
        setattr(self, '_avatar2', avatar2)

        # Create a conference
        category = conference.CategoryManager().getById('0')
        self._conf = category.newConference(self._avatar1)
        self._conf.setTimezone('UTC')
        sd = datetime(2011, 11, 1, 10, 0, tzinfo=timezone('UTC'))
        ed = datetime(2011, 11, 1, 18, 0, tzinfo=timezone('UTC'))
        self._conf.setDates(sd, ed)
        ch = ConferenceHolder()
        ch.add(self._conf)

        self._ctOral = conference.ContributionType("oral", "", self._conf)
        self._conf.addContribType(self._ctOral)

        self._track1 = self._conf.newTrack()
        self._track2 = self._conf.newTrack()
        self._track3 = self._conf.newTrack()

        self._abstract1 = self._conf.getAbstractMgr().newAbstract(self._avatar1)
        self._abstract2 = self._conf.getAbstractMgr().newAbstract(self._avatar1)
        self._abstract3 = self._conf.getAbstractMgr().newAbstract(self._avatar1)
        self._abstract4 = self._conf.getAbstractMgr().newAbstract(self._avatar1)
        self._abstract5 = self._conf.getAbstractMgr().newAbstract(self._avatar1)

        self._abstract1.setTracks([self._track1, self._track2, self._track3])
        self._abstract2.setTracks([self._track1, self._track2])
        self._abstract3.setTracks([self._track1])
        self._abstract4.setTracks([self._track2, self._track3])
        self._abstract5.setTracks([self._track3])

        self._stopDBReq()

    @with_context('database')
    def testJudgementStatus(self):
        self.assertIsNone(self._abstract1.getLastJudgementPerReviewer(self._avatar1, self._track1))
        self.assertIsNone(self._abstract1.getLastJudgementPerReviewer(self._avatar2, self._track1))
        self.assertIsNone(self._abstract1.getTrackJudgement(self._track1))
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusSubmitted)

        self._abstract1.proposeToAccept(self._avatar1, self._track1, "oral")

        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar1, self._track1), review.AbstractAcceptance)
        self.assertIsNone(self._abstract1.getLastJudgementPerReviewer(self._avatar2, self._track1))
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusUnderReview)

        self._abstract1.proposeToReject(self._avatar2, self._track1, "oral")

        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar1, self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar2, self._track1), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractInConflict)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusInConflict)

        self._abstract1.proposeToAccept(self._avatar2, self._track1, "oral")

        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar1, self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar2, self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusUnderReview)

        self._abstract1.proposeToReject(self._avatar1, self._track1, "oral")
        self._abstract1.proposeToReject(self._avatar2, self._track1, "oral")

        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar1, self._track1), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getLastJudgementPerReviewer(self._avatar2, self._track1), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusUnderReview)

        self._abstract1.proposeToReject(self._avatar1, self._track2, "oral")
        self._abstract1.proposeToReject(self._avatar1, self._track3, "oral")

        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track2), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track3), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusProposedToReject)

        self._abstract1.proposeToAccept(self._avatar1, self._track1, "oral")
        self._abstract1.proposeToAccept(self._avatar2, self._track1, "oral")

        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusProposedToAccept)

        self._abstract1.proposeToAccept(self._avatar1, self._track2, "oral")

        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track2), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusInConflict)

        self._abstract1.proposeToReject(self._avatar1, self._track2, "oral")

        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track2), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusProposedToAccept)

        self._abstract1.proposeForOtherTracks(self._avatar1, self._track2, comment="", propTracks=[self._track1])
        self._abstract1.proposeForOtherTracks(self._avatar2, self._track2, comment="", propTracks=[self._track3])

        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track1), review.AbstractAcceptance)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track2), review.AbstractReallocation)
        self.assertIsInstance(self._abstract1.getTrackJudgement(self._track3), review.AbstractRejection)
        self.assertIsInstance(self._abstract1.getCurrentStatus(), review.AbstractStatusProposedToAccept)
