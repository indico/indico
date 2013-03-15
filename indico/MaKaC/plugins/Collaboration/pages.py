# -*- coding: utf-8 -*-
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

import zope.interface

from indico.core.extpoint.base import Component
from indico.core.extpoint.events import IEventDisplayContributor
from indico.util.date_time import now_utc

from MaKaC.common import Config
from MaKaC.common import info
from MaKaC.common.utils import formatTwoDates
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from MaKaC.plugins.Collaboration.output import OutputGenerator
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface.simple_event import WPSimpleEventDisplay
from MaKaC.webinterface.pages.collaboration import WPConfModifCollaboration
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.plugins import Collaboration
from MaKaC.plugins.Collaboration import urlHandlers as collaborationUrlHandlers

from indico.util.i18n import  L_
from indico.util.date_time import format_datetime


STATUS_STRING = {
    SpeakerStatusEnum.NOEMAIL: L_("No Email"),
    SpeakerStatusEnum.NOTSIGNED: L_("Not Signed"),
    SpeakerStatusEnum.SIGNED: L_("Signed"),
    SpeakerStatusEnum.FROMFILE: L_("Uploaded"),
    SpeakerStatusEnum.PENDING: L_("Pending..."),
    SpeakerStatusEnum.REFUSED: L_("Refused")
        }


class IMEventDisplayComponent(Component):

    zope.interface.implements(IEventDisplayContributor)

    # EventDisplayContributor

    def injectCSSFiles(self, obj):
        return ['Collaboration/Style.css']

    def injectJSFiles(self, obj):
        return ['/Collaboration/bookings.js']

    def eventDetailBanner(self, obj, conf):
        vars = OutputGenerator.getCollaborationParams(conf)
        return WEventDetailBanner.forModule(Collaboration).getHTML(vars)


class WEventDetailBanner(wcomponents.WTemplated):

    @staticmethod
    def getBookingType(booking):
        if booking.canBeStarted():
            return "ongoing"
        elif booking.hasStartDate() and booking.getStartDate() > now_utc():
            return "scheduled"
        else:
            return ""

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["getBookingType"] = WEventDetailBanner.getBookingType
        vars["formatTwoDates"] = formatTwoDates
        vars["conf"] = self._rh._conf
        return vars


# Extra WP and W classes for the Electronic Agreement page
# Here the form page
class WPElectronicAgreementForm(WPSimpleEventDisplay):
    def __init__(self, rh, conf, authKey):
        WPSimpleEventDisplay.__init__(self, rh, conf)
        self.authKey = authKey

    def getCSSFiles(self):
        return WPSimpleEventDisplay.getCSSFiles(self) + \
                   ['Collaboration/Style.css']

    def getJSFiles(self):
        return WPSimpleEventDisplay.getJSFiles(self) + self._includeJSPackage("Display") + self._includeJSPackage('Collaboration')

    def _getBody(self, params):
        wc = WElectronicAgreementForm.forModule(Collaboration, self._conf, self.authKey)
        return wc.getHTML()

class WPElectronicAgreementFormConference(WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, authKey):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self.authKey = authKey

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
                   ['Collaboration/Style.css']

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + self._includeJSPackage("Display") + self._includeJSPackage('Collaboration')

    def _getBody( self, params ):
        wc = WElectronicAgreementForm.forModule(Collaboration, self._conf, self.authKey)
        return wc.getHTML()

class WElectronicAgreementForm(wcomponents.WTemplated):
    def __init__(self, conf, authKey):
        self._conf = conf
        self.authKey = authKey
        self.spkWrapper = None

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        agreement_name = CollaborationTools.getOptionValue("RecordingRequest", "AgreementName")
        manager = self._conf.getCSBookingManager()

        for sw in manager.getSpeakerWrapperList():
            if sw.getUniqueIdHash() == self.authKey:
                self.spkWrapper = sw

        if self.spkWrapper:
            speaker = self.spkWrapper.getObject()
            vars['speaker'] = speaker
            vars['conf'] = self._conf

            if self.spkWrapper.getStatus() in [SpeakerStatusEnum.SIGNED,
                                               SpeakerStatusEnum.FROMFILE,
                                               SpeakerStatusEnum.REFUSED]:

                vars['error'] = 'Already Submitted'

                if self.spkWrapper.getStatus() == SpeakerStatusEnum.SIGNED:
                    dtagree = self.spkWrapper.getDateAgreementSigned()
                    vars['outcomeText'] = _("You have already submitted your electronic agreement, it appears that you accepted it on <strong>%s</strong>.") % format_datetime(dtagree)
                elif self.spkWrapper.getStatus() == SpeakerStatusEnum.REFUSED:
                    vars['outcomeText'] = _("You have already submitted your electronic agreement, it appears that you refused it.")
                else:
                    vars['outcomeText'] = _("The organizer has already uploaded a scanned copy of {0}. No electronic signature is needed.").format(
                        CollaborationTools.getOptionValue("RecordingRequest", "AgreementName"))

            else:
                vars['error'] = None
                vars['authKey'] = self.authKey

                if self._conf.getType() == 'simple_event':
                    # if it's a lecture we consider the _conf object as the normal
                    # contribution and trigger a flag, in order to not print
                    # contributions detail...
                    showContributionInfo = False
                    cont = self._conf
                else:
                    showContributionInfo = True
                    cont = self._conf.getContributionById(self.spkWrapper.getContId())

                vars['cont'] = cont
                vars['showContributionInfo'] = self.authKey

                location = cont.getLocation()
                room = cont.getRoom()
                if location and location.getName() and location.getName().strip():
                    locationText = location.getName().strip()
                    if room and room.getName() and room.getName().strip():
                        locationText += ". " + _("Room: %s" % room.getName().strip())
                    else:
                        locationText += " " + _("(room not defined)")
                else:
                    locationText = _("location/room not defined")

                vars['locationText'] = locationText

                tz = self._conf.getTimezone()
                vars['confDate'] = "%s (%s)" % (formatTwoDates(self._conf.getStartDate(), self._conf.getEndDate(), tz = tz, showWeek = True), tz)
                vars['contDate'] = "%s (%s)"%(formatTwoDates(cont.getStartDate(), cont.getEndDate(), tz = tz, showWeek = True), tz)

                vars['linkToEvent'] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
                vars['agreementName'] = agreement_name
        else:
            vars['error'] = 'Error'

        return vars


# Here the administration page
class WPElectronicAgreement(WPConfModifCollaboration):

    def getCSSFiles(self):
        return WPConfModifCollaboration.getCSSFiles(self) + \
                   ['Collaboration/Style.css']

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()
    #only for tests...
    def getJSFiles(self):
        return WPConfModifCollaboration.getJSFiles(self) + self._includeJSPackage("MaterialEditor")

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()

            wc = WElectronicAgreement.forModule(Collaboration, self._conf, self._rh.getAW().getUser(), self._activeTabName, self._tabPlugins, params.get("sortCriteria"), params.get("order"))
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")

class WElectronicAgreement(wcomponents.WTemplated):
    def __init__(self, conference, user, activeTab, tabPlugins, sortBy, order):
        self._conf = conference
        self._user = user
        self._activeTab = activeTab
        self._tabPlugins = tabPlugins
        self.sortFields = ["speaker", "status", "cont", "reqType"] # Sorting fields allowed
        self.orderFields = ["up", "down"] # order fields allowed
        self._fromList = []
        self.sortCriteria = sortBy
        self.order = order

    def getListSorted(self, dict):
        '''
        Function used to sort the dictionary containing the contributions and speakers of the single booking.
        It returns a sorted list of list with only the necessary information:
        [[spkId, spkName, spkStatus, contId], [spkId, spkName, spkStatus, contId], ...]
        '''
        manager = self._conf.getCSBookingManager()
        list = []

        sortMap = {'speaker':1, 'status':2, 'cont':3, 'reqType':4}
        reverse = False if self.order == 'down' else True

        for cont in dict:
            for id in dict[cont]:
                sw = manager.getSpeakerWrapperByUniqueId("%s.%s"%(cont, id.getId()))
                status = ""
                reqType = "NA"
                enabled = False
                if sw:
                    status = STATUS_STRING[sw.getStatus()]
                    reqType = sw.getRequestType()
                    enabled = sw.getStatus() not in [SpeakerStatusEnum.SIGNED, SpeakerStatusEnum.FROMFILE, SpeakerStatusEnum.NOEMAIL]

                list.append([id.getId(), id.getFullNameNoTitle(), status, cont, reqType, enabled])

        return sorted(list, key=lambda list: list[sortMap[self.sortCriteria]], reverse=reverse)

    def getTableContent(self):

        manager = self._conf.getCSBookingManager()
        # Here we check the rights again, and chose what contributions we should show
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self._user)

        self._fromList = [{"name": self._user.getStraightFullName() , "email": email} for email in self._user.getEmails()]

        contributions = manager.getContributionSpeakerByType(requestType)

        return self.getListSorted(contributions)

    def getPaperAgreementURL(self):
        recordingFormURL = CollaborationTools.getOptionValue("RecordingRequest", "ConsentFormURL")
        webcastFormURL = CollaborationTools.getOptionValue("WebcastRequest", "ConsentFormURL")
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self._user)
        #return recordingFormURL
        if requestType == 'recording' and recordingFormURL != '':
            return _("""<a href="%s">Paper version</a>."""%recordingFormURL)
        elif requestType == 'webcast' and webcastFormURL != '':
            return _("""<a href="%s">Paper version</a>."""%webcastFormURL)
        elif requestType == 'both':
            if recordingFormURL == webcastFormURL and recordingFormURL != '': #same link, same file
                return _("""<a href="%s">Paper version</a>."""%recordingFormURL)
            elif recordingFormURL != '' and webcastFormURL != '':
                return _("""<a href="%s">Paper version</a> for the recording request or
                        <a href="%s">Paper version</a> for the webcast request."""%(recordingFormURL, webcastFormURL))
            elif recordingFormURL != '':
                return _("""<a href="%s">Paper version</a>."""%recordingFormURL)
            elif webcastFormURL != '':
                return _("""<a href="%s">Paper version</a>."""%webcastFormURL)
            else:
                return _("""<No agreement link available>.""")
        else:
            return _("""<No agreement link available>.""")

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        sortingField = None
        if self.sortCriteria in self.sortFields:
            sortingField = self.sortCriteria

        for crit in ["speaker", "status", "cont", "reqType"]:
            url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
            vars["%sImg" % crit] = ""
            url.addParam("sortBy", crit)

            if sortingField == crit:
                if self.order == "up":
                    vars["%sImg" % crit] = '<img src="%s" alt="up">' % (Config.getInstance().getSystemIconURL("upArrow"))
                    url.addParam("order","down")
                elif self.order == "down":
                    vars["%sImg" % crit] = '<img src="%s" alt="down">' % (Config.getInstance().getSystemIconURL("downArrow"))
                    url.addParam("order","up")

            vars["%sSortingURL" % crit] = str(url)

        vars["conf"] = self._conf
        vars["contributions"] = self.getTableContent()

        self._fromList.append({"name": "Indico Mailer",
                               "email": Config.getInstance().getNoReplyEmail()})
        vars['fromList'] = self._fromList
        manager = self._conf.getCSBookingManager()
        vars['manager'] = manager
        vars['user'] = self._user

        if hasattr(manager, "_speakerWrapperList"):
            vars['signatureCompleted'] = manager.areSignatureCompleted()
        else:
            vars['signatureCompleted'] = None

        vars['STATUS_STRING'] = STATUS_STRING
        vars['canShow'] = manager.isAnyRequestAccepted()
        vars['SpeakerStatusEnum'] = SpeakerStatusEnum
        vars['user'] = self._user
        vars['collaborationUrlHandlers'] = collaborationUrlHandlers
        vars['urlPaperAgreement'] = self.getPaperAgreementURL()
        vars['agreementName'] = CollaborationTools.getOptionValue("RecordingRequest", "AgreementName")
        vars["notifyElectronicAgreementAnswer"] = manager.notifyElectronicAgreementAnswer()
        vars["emailIconURL"]=(str(Config.getInstance().getSystemIconURL("mail_grey")))
        vars["canModify"] = self._conf.canModify( self._rh.getAW() )
        return vars
