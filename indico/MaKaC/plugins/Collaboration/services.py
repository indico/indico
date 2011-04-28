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
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
"""
Services for Collaboration plugins
"""

from MaKaC.services.implementation.contribution import ContributionDisplayBase
from MaKaC.services.implementation.conference import ConferenceModifBase, ConferenceDisplayBase
from MaKaC.plugins.Collaboration.urlHandlers import UHCollaborationElectronicAgreementForm
from MaKaC.plugins.Collaboration.mail import ElectroniAgreementNotification
from MaKaC.common.mail import GenericMailer

#TODO: Need to verify if the ContributionDisplayBase is the good parent to inherit from
class SetSpeakerEmailAddress(ContributionDisplayBase):

    def _checkParams(self):
        ContributionDisplayBase._checkParams(self)

        self.newEmailAddress = self._params['value']
        self.spkId = self._params['spkId']

    def _getAnswer(self):
        self._contribution.getSpeakerById(self.spkId).setEmail(self.newEmailAddress)
        self._contribution.notifyModification()

class SetChairEmailAddress(ConferenceModifBase):

    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        self.newEmailAddress = self._params['value']
        self.spkId = self._params['spkId']

    def _getAnswer(self):
        self._conf.getChairById(self.spkId).setEmail(self.newEmailAddress)

class GetSpeakerEmailListByCont(ConferenceModifBase):
    def _checkParams(self):
        ConferenceModifBase._checkParams(self)
        self.contList = self._params['contList']
        self.userId = self._params['userId']

    def _getAnswer(self):
        manager = self._conf.getCSBookingManager()
        resultList = []
        for cont in self.contList:
            resultList.extend(manager.getSpeakerEmailListByContribution(cont, self.userId))

        return resultList

class SendElectronicAgreement(ConferenceModifBase):
    def _checkParams(self):
        ConferenceModifBase._checkParams(self)

        self.uniqueIdList = self._params['uniqueIdList']

        self.emailToList = []

        self.fromEmail = self._params['from']
        self.content = self._params['content']
        manager = self._conf.getCSBookingManager()
        for uniqueId in self.uniqueIdList:
            self.emailToList.extend(manager.getSpeakerEmailByUniqueId(uniqueId, self._aw.getUser()))

    def processContent(self, speakerWrapper):
        #newContent = self.content
        fullUrl = UHCollaborationElectronicAgreementForm().getURL(self._conf.getId(), speakerWrapper.getUniqueIdHash())
        url = "<a href='%s'>%s</a>"%(fullUrl, fullUrl)

        return self.content.format(url=url, name= speakerWrapper.getObject().getDirectFullName())

        #newContent = newContent.replace("[url]", "<a href='%s'>%s</a>"%(url, url))
        #newContent = newContent.replace("[name]", "%s"%speakerWrapper.getObject().getDirectFullName())

        #cont = self._conf.getContributionById(speakerWrapper.getContId())
        #=======================================================================
        # newContent.replace("[contTitle]","%s"%cont.getTitle())
        # newContent.replace("[contDate]", "%s"%formatTwoDates(cont.getStartDate(), cont.getEndDate(), tz = cont.getTimezone(), showWeek = True))
        # newContent.replace("[contRoom]", "%s"%cont.getRoom())
        #=======================================================================
        #return newContent

    def _getAnswer(self):
        report = ""
        i = 0
        for email in self.emailToList:
            i += 1
            if i != len(self.emailToList):
                report += "%s, "%email
            else:
                report += "%s."%email

        if self.content.find('{url}') > -1: #{url} is mandatory to send the EA link
            manager = self._conf.getCSBookingManager()
            for uniqueId in self.uniqueIdList:
                sw = manager.getSpeakerWrapperByUniqueId(uniqueId)
                sw.setStatus(SpeakerStatusEnum.PENDING)
                subject = """[Indico] Electronic Agreement: %s (event id: %s)"""%(self._conf.getTitle(), self._conf.getId())
                notification = ElectroniAgreementNotification([sw.getObject().getEmail()], self.fromEmail, self.processContent(sw), subject)

                GenericMailer.sendAndLog(notification, self._conf,
                                         "MaKaC/plugins/Collaboration/RecordingRequest/collaboration.py",
                                         None)
        else:
            report = "url_error"

        return report

class RejectElectronicAgreement(ConferenceDisplayBase):
    def _checkParams(self):
        ConferenceDisplayBase._checkParams(self)
        self.authKey = self._params["authKey"]
        self.reason = self._params["reason"]

    def _getAnswer(self):
        spkWrapper = None
        manager = self._conf.getCSBookingManager()
        for sw in manager.getSpeakerWrapperList():
            if sw.getUniqueIdHash() == self.authKey:
                spkWrapper = sw

        if spkWrapper:
            spkWrapper.setStatus(SpeakerStatusEnum.REFUSED)
            spkWrapper.setRejectReason(self.reason)

class AcceptElectronicAgreement(ConferenceDisplayBase):
    def _checkParams(self):
        ConferenceDisplayBase._checkParams(self)
        self.authKey = self._params["authKey"]

    def _getAnswer(self):
        spkWrapper = None
        manager = self._conf.getCSBookingManager()
        for sw in manager.getSpeakerWrapperList():
            if sw.getUniqueIdHash() == self.authKey:
                spkWrapper = sw

        if spkWrapper:
            spkWrapper.setStatus(SpeakerStatusEnum.SIGNED, self._req.get_remote_ip())

methodMap = {
    "collaboration.setEmailSpeaker": SetSpeakerEmailAddress,
    "collaboration.setEmailChair": SetChairEmailAddress,
    "collaboration.sendElectronicAgreement": SendElectronicAgreement,
    "collaboration.getSpeakerEmailList": GetSpeakerEmailListByCont,
    "collaboration.rejectElectronicAgreement": RejectElectronicAgreement,
    "collaboration.acceptElectronicAgreement": AcceptElectronicAgreement
}