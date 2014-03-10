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

#from indico.tests.env import *

from MaKaC.user import Avatar
from MaKaC.conference import AvatarHolder, AdminList, Contribution,\
    timezone, datetime, ContributionParticipation, Session, SessionSlot, ConferenceHolder
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.services import SetSpeakerEmailAddress, SendElectronicAgreement,\
    RejectElectronicAgreement, AcceptElectronicAgreement
from MaKaC import conference
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from indico.core.index import Catalog
from indico.tests.python.unit.util import IndicoTestFeature, IndicoTestCase, with_context

class Collaboration_Feature(IndicoTestFeature):
    _requires = ['plugins.Plugins']

    def start(self, obj):
        super(Collaboration_Feature, self).start(obj)
        with obj._context('database'):
            obj._ph.getPluginType('Collaboration').toggleActive()

    def destroy(self, obj):
        super(Collaboration_Feature, self).destroy(obj)


class TestElectronicAgreement(IndicoTestCase):

    _requires = ['db.Database', 'util.RequestEnvironment', Collaboration_Feature]

    def setUp(self):
        '''
        Create a conference, 0
        Add 2 contributions to this conference, 0 and 1
        To contribution 0 - Add 2 speakers, person1 and person2
        To contribution 1 - Add 1 speaker, person1
        '''
        super(TestElectronicAgreement, self).setUp()
        with self._context('database', 'request'):

            # Create few users
            self._creator = Avatar({"name":"God", "email":"test@epfl.ch"})
            self._creator.setId("creator")
                # Set God as admin
            AdminList.getInstance().getList().append(self._creator)

            self.person1 = Avatar({"name":"giuseppe", "email":"12@hispeed.ch"})
            self.person1.setId("spk1")
            self.person2 = Avatar({"name":"gabriele", "email":"34@hispeed.ch"})
            self.person1.setId("spk2")
            self.person3 = Avatar({"name":"lorenzo", "email":"56@hispeed.ch"})
            self.person1.setId("spk3")
            self.person4 = Avatar({"name":"silvio", "email":"78@hispeed.ch"})
            self.person1.setId("spk4")

            ah = AvatarHolder()
            ah.add(self.person1)
            ah.add(self.person2)
            ah.add(self.person3)
            ah.add(self.person4)

            # Create a conference
            category = conference.CategoryManager().getById('0')
            self._conf = category.newConference(self._creator)
            self._conf.setTimezone('UTC')
            sd=datetime(2011, 06, 01, 10, 00, tzinfo=timezone("UTC"))
            ed=datetime(2011, 06, 05, 10, 00, tzinfo=timezone("UTC"))
            self._conf.setDates(sd,ed,)
            ch = ConferenceHolder()
            ch.add(self._conf)

            # Create contributions and add to the conference
            c1, c2 = Contribution(), Contribution()
            self.speaker1, self.speaker2 = ContributionParticipation(), ContributionParticipation()

            self.speaker1.setDataFromAvatar(self.person1)
            self.speaker2.setDataFromAvatar(self.person2)

            self._conf.addContribution(c2)
            self._conf.addContribution(c1)

            # Add speakers to contributions
            c1.addPrimaryAuthor(self.speaker1)
            c2.addPrimaryAuthor(self.speaker2)
            c1.addSpeaker(self.speaker1)
            c2.addSpeaker(self.speaker1)
            c2.addSpeaker(self.speaker2)

            self._conf.enableSessionSlots()

            # Create session and schedule the contributions
            s1 = Session()
            sd = datetime(2011, 06, 02, 12, 00, tzinfo=timezone("UTC"))
            ed = datetime(2011, 06, 02, 19, 00, tzinfo=timezone("UTC"))
            s1.setDates(sd, ed)

            slot1 = SessionSlot(s1)
            self._conf.addSession(s1)
            slot1.setValues({"sDate":sd})
            s1.addSlot(slot1)

            s1.addContribution(c1)
            s1.addContribution(c2)
            slot1.getSchedule().addEntry(c1.getSchEntry())
            slot1.getSchedule().addEntry(c2.getSchEntry())
            self.createAndAcceptBooking()

    @with_context('database')
    def testRightsFiltering(self):
        '''
        Test if the managing rights are respected.
        '''
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())

        # Test that person3 has not access to webcasted talks
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self.person3)
        contributions = manager.getContributionSpeakerByType(requestType)
        for cont in contributions:
            for spk in contributions[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, spk.getId()))
                self.assert_(sw.getRequestType() == "recording" or sw.getRequestType() == "both")

        # Test that person4 has not access to recorded talks
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self.person4)
        contributions = manager.getContributionSpeakerByType(requestType)
        for cont in contributions:
            for spk in contributions[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, spk.getId()))
                self.assert_(sw.getRequestType() == "webcast" or sw.getRequestType() == "both")

    @with_context('database')
    @with_context('request')
    def testNOEMAILStatus(self):
        '''
        Test if the status of the SpeakerWrapper is correctly updated to NOEMAIL.\n
        '''
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())

        contributions = manager.getContributionSpeakerByType("both")

        ''' Check change to NOEMAIL status, when delete the email of a speaker (here: speaker1)
            Should change to this status only if the previous status is NOTSIGNED or PENDING
        '''
        for cont in contributions:
            sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, self.speaker1.getId()))
            if sw:
                #remove the email from NOTSIGNED to NOEMAIL
                self.changeEmailService(cont, self.speaker1.getId(), "")
                self.assert_(sw.getStatus() == SpeakerStatusEnum.NOEMAIL)

                #reset email, then remove email from PENDING to NOEMAIL
                self.changeEmailService(cont, self.speaker1.getId(), "test@test.ch")
                sw.setStatus(SpeakerStatusEnum.PENDING)
                self.changeEmailService(cont, self.speaker1.getId(), "")
                self.assert_(sw.getStatus() == SpeakerStatusEnum.NOEMAIL)

                #reset email, then remove email from SIGNED to SIGNED (no changes)
                self.changeEmailService(cont, self.speaker1.getId(), "test@test.ch")
                sw.setStatus(SpeakerStatusEnum.SIGNED)
                self.changeEmailService(cont, self.speaker1.getId(), "")
                self.assert_(sw.getStatus() == SpeakerStatusEnum.SIGNED)

                #reset email, then remove email from FROMFILE to FROMFILE (no changes)
                self.changeEmailService(cont, self.speaker1.getId(), "test@test.ch")
                sw.setStatus(SpeakerStatusEnum.FROMFILE)
                self.changeEmailService(cont, self.speaker1.getId(), "")
                self.assert_(sw.getStatus() == SpeakerStatusEnum.FROMFILE)

                #reset email, then remove email from REFUSED to REFUSED (no changes)
                self.changeEmailService(cont, self.speaker1.getId(), "test@test.ch")
                sw.setStatus(SpeakerStatusEnum.REFUSED)
                self.changeEmailService(cont, self.speaker1.getId(), "")
                self.assert_(sw.getStatus() == SpeakerStatusEnum.REFUSED)

    @with_context('database')
    @with_context('request')
    def testPENDINGStatus(self):
        '''
        Test if the status of the SpeakerWrapper is correctly updated to PENDING.\n
        '''
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        contributions = manager.getContributionSpeakerByType("both")

        uniqueIdList = []

        for cont in contributions:
            for spk in contributions[cont]:
                uniqueIdList.append("%s.%s"%(cont, spk.getId()))

        self.sendEmailService(uniqueIdList)

        for cont in contributions:
            for spk in contributions[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, spk.getId()))
                self.assert_(sw.getStatus() == SpeakerStatusEnum.PENDING)

    @with_context('database')
    @with_context('request')
    def testSIGNEDStatus(self):
        '''
        Test if the status of the SpeakerWrapper is correctly updated to SIGNED.\n
        '''
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        contributions = manager.getContributionSpeakerByType("both")

        for cont in contributions:
            for spk in contributions[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, spk.getId()))
                self.submitAgreementService(sw, 'accept')
                self.assert_(sw.getStatus() == SpeakerStatusEnum.SIGNED)

    @with_context('database')
    @with_context('request')
    def testREFUSEDStatus(self):
        '''
        Test if the status of the SpeakerWrapper is correctly updated to REFUSED.\n
        '''
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        contributions = manager.getContributionSpeakerByType("both")

        for cont in contributions:
            for spk in contributions[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, spk.getId()))
                self.submitAgreementService(sw, 'reject')
                self.assert_(sw.getStatus() == SpeakerStatusEnum.REFUSED)

#==========================================================================
    # Here useful functions called during the tests
    def createAndAcceptBooking(self):
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())

        # Create a booking - Recording Request
        bookingParams =  {
                            'otherComments': '', 'endDate': '', 'talkSelection': ['0'], 'numAttendees': '', 'talks': '',
                            'lectureStyle': 'lecturePresentation', 'numRemoteViewers': '', 'startDate': '', 'postingUrgency': 'withinWeek'
                         }
        # Create a booking - Webcast Request
        bookingParamsWeb =  {
                           'talkSelection': ['0'], 'talks': 'choose'
                        }

        #Give rights to person3(recordingReq) and person4(webcastReq) (... _creator has both)
        manager.addPluginManager("RecordingRequest", self.person3)
        manager.addPluginManager("WebcastRequest", self.person4)

        if manager.canCreateBooking("RecordingRequest"):
            manager.createBooking("RecordingRequest", bookingParams)
        booking = manager.getSingleBooking("RecordingRequest")
        manager.acceptBooking(booking.getId())

        if manager.canCreateBooking("WebcastRequest"):
            manager.createBooking("WebcastRequest", bookingParamsWeb)
        booking = manager.getSingleBooking("WebcastRequest")
        manager.acceptBooking(booking.getId())

    def changeEmailService(self, contId, spkId, value):

        params = {
                  'value':value,
                  'confId':self._conf.getId(),
                  'contribId':contId,
                  'spkId': spkId
                  }
        service = SetSpeakerEmailAddress(params)
        service._checkParams()
        service._getAnswer()

    def sendEmailService(self, uniqueId):
        fromField = {
            "name": "No-reply",
            "email": "no-reply@test.ch"
            }
        content = "This is a test {url} {talkTitle}..."

        params = {
                  'from': fromField,
                  'content': content,
                  'uniqueIdList': uniqueId,
                  'confId': self._conf.getId()
                  }
        service = SendElectronicAgreement(params)
        service._checkParams()
        service._getAnswer()

    def submitAgreementService(self, sw, decision):
        params = {
                  'authKey':sw.getUniqueIdHash(),
                  'confId': self._conf.getId(),
                  'reason': 'because...'
                  }

        if decision == 'accept':
            service = AcceptElectronicAgreement(params)
        else:
            service = RejectElectronicAgreement(params)

        service._checkParams()
        service._getAnswer()
