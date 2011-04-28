# -*- coding: utf-8 -*-
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

import zope.interface

from indico.core.extpoint.base import Component
from indico.core.extpoint.events import IEventDisplayContributor
from indico.util.date_time import now_utc

from MaKaC.common import Config
from MaKaC.common import info
from MaKaC.common.utils import formatTwoDates
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from MaKaC.webinterface.simple_event import WPSimpleEventDisplay
from MaKaC.webinterface.pages.collaboration import WPConfModifCollaboration
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.plugins import Collaboration
from MaKaC.plugins.Collaboration import urlHandlers as collaborationUrlHandlers
from MaKaC.plugins.Collaboration.output import OutputGenerator
from xml.sax.saxutils import quoteattr


class IMEventDisplayComponent(Component):

    zope.interface.implements(IEventDisplayContributor)

    # EventDisplayContributor
    def injectCSSFiles(self, obj):
        return []

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
        vars['getBookingType'] = WEventDetailBanner.getBookingType
        vars['formatTwoDates'] = formatTwoDates


# Extra WP and W classes for the Electronic Agreement page

# Here the form page
class WPCollaborationElectronicAgreementForm(WPSimpleEventDisplay):
    def __init__(self, rh, conf, authKey):
        WPSimpleEventDisplay.__init__(self, rh, conf)
        self.authKey = authKey

    def getCSSFiles(self):
        return WPSimpleEventDisplay.getCSSFiles(self) + \
                   ['Collaboration/Style.css']

    def getJSFiles(self):
        return WPSimpleEventDisplay.getJSFiles(self) + self._includeJSPackage('Collaboration')

    def _getBody(self, params):
        wc = WCollaborationElectronicAgreementForm.forModule(Collaboration, self._conf, self.authKey)
        return wc.getHTML()


class WPCollaborationElectronicAgreementFormConference(WPConferenceDefaultDisplayBase):
    def __init__(self, rh, conf, authKey):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self.authKey = authKey

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
                   ['Collaboration/Style.css']

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + self._includeJSPackage('Collaboration')

    def _getBody( self, params ):
        wc = WCollaborationElectronicAgreementForm.forModule(Collaboration, self._conf, self.authKey)
        return wc.getHTML()


class WCollaborationElectronicAgreementForm(wcomponents.WTemplated):
    def __init__(self, conf, authKey):
        self._conf = conf
        self.authKey = authKey
        self.spkWrapper = None

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        manager = self._conf.getCSBookingManager()

        if self._conf.getType() != 'conference':
            vars['addStyle'] = """ style="margin: 0 10%;" """
        else:
            vars['addStyle'] = ""

        for sw in manager.getSpeakerWrapperList():
            if sw.getUniqueIdHash() == self.authKey:
                self.spkWrapper = sw

        if self.spkWrapper:
            speaker = self.spkWrapper.getObject()

            if self.spkWrapper.getStatus() == SpeakerStatusEnum.SIGNED or\
                 self.spkWrapper.getStatus() == SpeakerStatusEnum.FROMFILE or \
                    self.spkWrapper.getStatus() == SpeakerStatusEnum.REFUSED:

                vars['error'] = 'Already Submitted'

                if self.spkWrapper.getStatus() == SpeakerStatusEnum.SIGNED:
                    from datetime import datetime
                    date = datetime.utcfromtimestamp(self.spkWrapper.getDateAgreementSigned())
                    decision = 'accepted it on %s (UTC).'%date.strftime("%A, %d. %B %Y at %I:%M%p")
                else:
                    decision = 'refused it.'


                detailsAlreadySub = _("""
                                    Dear %s,<br/>
                                    You have already submitted your electronic agreement, it appears that you %s<br/>
                                    Thus, you don't have access to this page anymore.<br/>Therefore, if you want to modify your choice, you have to contact the manager.
                                    """%(speaker.getDirectFullName(), decision))

                vars['detailsAlreadySub'] = detailsAlreadySub

            else:
                vars['error'] = None
                vars['authKey'] = self.authKey
                vars['conf'] = self._conf
                showContributionInfo = True
                if self._conf.getType() == 'simple_event':
                    '''
                    Get over this difference...
                    if it's a lecture we consider the _conf object as the normal contribution
                    and trigger a flag, in order to not print contributions detail...
                    '''
                    showContributionInfo = False
                    cont = self._conf
                else:
                    cont = self._conf.getContributionById(self.spkWrapper.getContId())

                if self.spkWrapper.getRequestType() == "recording":
                    requestType = "Recorded"
                elif self.spkWrapper.getRequestType() == "webcast":
                    requestType = "Webcasted"
                else:
                    requestType = "Recorded and Webcasted"

                location = cont.getLocation()
                room = cont.getRoom()
                if location and location.getName() and location.getName().strip():
                    locationText = location.getName().strip()
                    if room and room.getName() and room.getName().strip():
                        locationText += ". Room: " + room.getName().strip()
                    else:
                        locationText += " (room not defined)"
                else:
                    locationText = "location/room not defined"

                tz = self._conf.getTimezone()
                confDate = "%s (%s)"%(formatTwoDates(self._conf.getStartDate(), self._conf.getEndDate(), tz = tz, showWeek = True), tz)
                contDate = "%s (%s)"%(formatTwoDates(cont.getStartDate(), cont.getEndDate(), tz = tz, showWeek = True), tz)

                vars['linkToEvent'] = urlHandlers.UHConferenceDisplay.getURL(self._conf)

                if cont.getDescription():
                    contDetails = """
                                    <tr>
                                        <td class="EAInfo">Description:</td>
                                        <td>%s</td>
                                    </tr>
                                   """%cont.getDescription()
                else:
                    contDetails = ""

                detailsContent = _("""
                                 Dear %s,<br/>
                                you have been contacted because you have been scheduled to give a talk for the following event:<br/>

                                <table class="EATable">
                                    <tr>
                                        <td class="EAInfo">Event Title:</td>
                                        <td>%s</td>
                                    </tr>
                                    <tr>
                                        <td class="EAInfo">Holding on:</td>
                                        <td>%s</td>
                                    </tr>
                                """%(speaker.getDirectFullName(), self._conf.getTitle(), confDate))

                if showContributionInfo:
                    detailsContent += _("""
                        </table>
                        <br/>
                        Your contribution details are the following:<br/>
                        <table class="EATable">
                            <tr>
                                <td class="EAInfo">Talk:</td>
                                <td>%s</td>
                            </tr>
                            %s
                            <tr>
                                <td class="EAInfo">Scheduled on:</td>
                                <td>%s</td>
                            </tr>
                            <tr>
                                <td class="EAInfo">Place:</td>
                                <td>%s</td>
                            </tr>
                        </table>
                         """%(cont.getTitle(), contDetails, contDate, locationText))
                else:
                    detailsContent += _("""
                            <tr>
                                <td class="EAInfo">Place:</td>
                                <td>%s</td>
                            </tr>
                        </table>"""%(locationText))

                vars["detailsContent"] = detailsContent

                detailsAgreement = _("""
                                    <div>
                                        Your talk will be %s, thus we will need your agreement to allow us to publish your contribution.<br/>
                                        [blablablabla]
                                    </div>
                                    <br/>
                                    <form name="choiceButton" class="EAChoiceButton">
                                        <input type="radio" name="EAChoice" value="accept">I confirm that I read the Electronic Agreement form and <strong>accept</strong>.</input><br/>
                                        <input type="radio" name="EAChoice" value="refuse">I confirm that I read the Electronic Agreement form but I <strong>refuse</strong>.</input><br/><br/>
                                        <input type="button" name="sendChoice" value="Submit" onclick="return signEA()"/>
                                    </form>
                                </div>
                                   """%(requestType))

                vars['detailsAgreement'] = detailsAgreement
        else:
            vars['error'] = 'Error'

        return vars


# Here the administration page
class WPCollaborationElectronicAgreement(WPConfModifCollaboration):

    def _setActiveTab(self):
        self._tabs[self._activeTabName].setActive()
    #only for tests...
    def getJSFiles(self):
        return WPConfModifCollaboration.getJSFiles(self) + self._includeJSPackage("MaterialEditor")

    def _getPageContent(self, params):
        if len(self._tabNames) > 0:
            self._createTabCtrl()

            wc = WCollaborationElectronicAgreement.forModule(Collaboration, self._conf, self._rh.getAW().getUser(), self._activeTabName, self._tabPlugins, params.get("sortCriteria"), params.get("order"))
            return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(wc.getHTML({}))
        else:
            return _("No available plugins, or no active plugins")


class WCollaborationElectronicAgreement(wcomponents.WTemplated):
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

    def createContextHelp(self):
        # Request Type context help
        contextHelp = """
                    <div id="tooltipPool" style="display: none">
                        <div id="requestType" class="tip">"""
        contextHelp +=_("""<b>Request type involved for Electronic Agreement</b><br/>
            - <b>REC</b>: Only the recording has been requested.<br/>
            - <b>WEBC</b>: Only the webcast has been requested.<br/>
            - <b>REC/WEBC</b>: Both recording and webcast have been requested.<br/>
            - <b>NA</b>: Information not available.""")
        contextHelp += """</div></div>"""

        # Status context help
        contextHelp += """
                   <div id="tooltipPool" style="display: none">
                       <div id="status" class="tip">"""
        contextHelp += _("""<b>Status Legend</b><br>
           - <b>No Email</b>: Speaker does not have an Email address.<br/>
           - <b>Not Signed</b>: Agreement not signed.<br/>
           - <b>Pending...</b>: Email sent to the speakers, waiting for signature.<br/>
           - <b>Signed</b>: Agreement signed electronically.<br/>
           - <b>Uploaded</b>: Agreement signed uploading the form.<br/>
           - <b>Refused</b>: Agreement refused.""")
        contextHelp += """</div></div>"""

        return contextHelp

    def addEntries(self, contentList):
        ''' For a given booking type (Recording request or Webcast request) and its
        corresponding dict of contribution/speaker, build html for every entry in the dict.
        '''
        vars = wcomponents.WTemplated.getVars(self)
        entries = []
        manager = self._conf.getCSBookingManager()

        cssColorCode = {
                        SpeakerStatusEnum.NOEMAIL:"#881122",
                        SpeakerStatusEnum.NOTSIGNED:"#881122",
                        SpeakerStatusEnum.REFUSED: "#881122",
                        SpeakerStatusEnum.PENDING: "#FF7F00", # dotorange
                        SpeakerStatusEnum.SIGNED: "#118822", # dotgreen
                        SpeakerStatusEnum.FROMFILE: "#118822"
                    }

        requestTypeCode = {
                           "recording": "REC",
                           "webcast": "WEBC",
                           "both": "REC/WEBC",
                           "NA": "NA"
                           }
        for item in contentList:
            '''  item[0]: speakerId
                 item[1]: speaker Name
                 item[2]: status
                 item[3]: contributionId '''

            spkId = item[0]
            contId = item[3]
            tableEntry = ""
            contribution = self._conf.getContributionById(contId)
            if contribution:
                name = contribution.getTitle()
            else:
                name = self._conf.getTitle()

            spkWrapper = manager.getSpeakerWrapperByUniqueId("%s.%s"%(contId, spkId))
            status = "NA"
            colorStatus = ""
            type = "NA"
            disable = ""
            uploadLink = ""

            if spkWrapper:
                uniqueId = spkWrapper.getUniqueId()

                #Here the checkbox
                if spkWrapper.getStatus() == SpeakerStatusEnum.SIGNED or \
                        spkWrapper.getStatus() == SpeakerStatusEnum.FROMFILE or \
                            spkWrapper.getStatus() == SpeakerStatusEnum.NOEMAIL:
                    disable = "disabled"
                else:
                    disable = ""
                tableEntry += """<tr id="row%s" onmouseover="javascript:onMouseOver('row%s')" onmouseout="javascript:onMouseOut('row%s')">
                                <td valign="middle" align="right" width="3%%">
                                    <input %s id="%s" onchange="javascript:isSelected('row%s')" type="checkbox" name="cont" style="background-color: transparent;">
                                </td>
                          """%(uniqueId, uniqueId, uniqueId, disable, uniqueId, uniqueId)


                # Here the Speaker Name
                tableEntry +="""
                                <td class="CRLabstractLeftDataCell" nowrap>
                                    %s
                                </td>
                             """%(spkWrapper.getObject().getFullName())

                # Here the Email Address
                tableEntry +="""
                                <td class="CRLabstractLeftDataCell" nowrap>
                                    <img style="cursor:pointer;margin-right:5px;" src="%s" alt="%s" title="%s" onclick="new EditSpeakerEmail('%s','%s', '%s','%s', '%s', '%s').open()" />
                                     %s
                                </td>
                             """%(Config.getInstance().getSystemIconURL("edit"), _("Edit Email"), _("Edit Email"),
                                  self._conf.getType(), spkWrapper.getObject().getFullName(), spkId, spkWrapper.getObject().getEmail(), self._conf.getId(),
                                  contId, spkWrapper.getObject().getEmail())

                #Here the EA status and request type
                status = spkWrapper.getStatusString()
                type = spkWrapper.getRequestType()
                colorStatus = "style='color:%s;'"%cssColorCode[spkWrapper.getStatus()]
                if spkWrapper.getStatus() == SpeakerStatusEnum.REFUSED:
                    status = """%s
                                <img id="reject%s" name="%s" alt="Tooltip" src="%s" style="vertical-align:text-bottom; border:None;">
                                <script>$E('reject%s').dom.onmouseover = showRejectReason</script>
                             """%(spkWrapper.getStatusString(),uniqueId, spkWrapper.getRejectReason(), Config.getInstance().getSystemIconURL("help"), uniqueId)
                tableEntry += """
                                <td class="CRLabstractLeftDataCell" nowrap %s>
                                    %s
                                </td>
                                <td class="CRLabstractLeftDataCell" nowrap>
                                    %s
                                </td>
                            """%(colorStatus, status, requestTypeCode[type])

                # Here the contribution name
                from MaKaC.common.TemplateExec import truncateTitle
                from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin

                isAdminUser = RCCollaborationAdmin.hasRights(user = self._user)
                if isAdminUser or manager.isVideoServicesManager(self._user):
                    contLink = urlHandlers.UHContributionModification.getURL(self._conf.getContributionById(contId))
                else:
                    contLink = urlHandlers.UHContributionDisplay.getURL(self._conf.getContributionById(contId))

                tableEntry += """
                                <td class="CRLabstractLeftDataCell">
                                    <a href = "%s" id='name%s' name="%s">%s</a>
                                    <script>$E('name%s').dom.onmouseover = contFullTitle;</script>
                                </td>
                              """%(contLink, uniqueId, name,truncateTitle(name, 10), uniqueId)


                # Here the upload field
                if spkWrapper.getLocalFile():
                    path = collaborationUrlHandlers.UHCollaborationElectronicAgreementGetFile.getURL( self._conf, spkWrapper.getUniqueId() )
                else:
                    path = ""

                if path != "":
                    uploadLink = """
                                    <a href="%s">
                                        <img style="cursor:pointer;margin-right:5px;" src="%s" alt="%s" title="%s" />
                                    </a>
                                 """%(path, Config.getInstance().getSystemIconURL("pdf"), _("Paper Agreement"), _("Paper Agreement"))
                tableEntry += """
                                <td class="CRLabstractLeftDataCell" nowrap>
                                    <a href="" onclick="new UploadElectronicAgreementPopup('%s','%s','%s').open();return false;" id="upload%s">Upload</a> %s
                                </td>
                            """%(self._conf.getId(), uniqueId, collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf) ,uniqueId, uploadLink)

            entries.append(tableEntry)

        return entries

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
                if sw:
                    status = sw.getStatusString()
                    reqType = sw.getRequestType()

                list.append([id.getId(), id.getFullNameNoTitle(), status, cont, reqType])

        return sorted(list, key=lambda list: list[sortMap[self.sortCriteria]], reverse=reverse)

    def getTableContent(self):

        manager = self._conf.getCSBookingManager()
        # Here we check the rights again, and chose what contributions we should show
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self._user)

        self._fromList = self._user.getEmails()

        contributions = manager.getContributionSpeakerByType(requestType)

        entryList = self.getListSorted(contributions)
        table = self.addEntries(entryList)

        return "".join(table)

    def getPaperAgreementURL(self):
        recordingFormURL = CollaborationTools.getOptionValue("RecordingRequest", "ConsentFormURL")
        webcastFormURL = CollaborationTools.getOptionValue("WebcastRequest", "ConsentFormURL")
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, self._user)
        #return recordingFormURL
        if requestType == 'recording' and recordingFormURL != '':
            return _("""<a href="%s">here</a>."""%recordingFormURL)
        elif requestType == 'webcast' and webcastFormURL != '':
            return _("""<a href="%s">here</a>."""%webcastFormURL)
        elif requestType == 'both':
            if recordingFormURL == webcastFormURL and recordingFormURL != '': #same link, same file
                return _("""<a href="%s">here</a>."""%recordingFormURL)
            elif recordingFormURL != '' and webcastFormURL != '':
                return _("""<a href="%s">here</a> for the recording request or
                        <a href="%s">here</a> for the webcast request."""%(recordingFormURL, webcastFormURL))
            elif recordingFormURL != '':
                return _("""<a href="%s">here</a>."""%recordingFormURL)
            elif webcastFormURL != '':
                return _("""<a href="%s">here</a>."""%webcastFormURL)
            else:
                return _("""<No agreement link available>.""")
        else:
            return _("""<No agreement link available>.""")

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        sortingField = None
        if self.sortCriteria in self.sortFields:
            sortingField = self.sortCriteria

        url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
        url.addParam("sortBy", "speaker")
        vars["speakerImg"] = ""
        if sortingField == "speaker":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="speaker">"""
            if self.order == "down":
                vars["speakerImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self.order == "up":
                vars["speakerImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["speakerSortingURL"] = quoteattr( str( url ) )

        url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
        url.addParam("sortBy", "status")
        vars["statusImg"] = ""
        if sortingField == "status":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="status">"""
            if self.order == "down":
                vars["statusImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self.order == "up":
                vars["statusImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["statusSortingURL"] = quoteattr( str( url ) )

        url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
        url.addParam("sortBy", "cont")
        vars["contImg"] = ""
        if sortingField == "cont":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="cont">"""
            if self.order == "down":
                vars["contImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self.order == "up":
                vars["contImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["contSortingURL"] = quoteattr( str( url ) )

        url = collaborationUrlHandlers.UHCollaborationElectronicAgreement.getURL(self._conf)
        url.addParam("sortBy", "reqType")
        vars["reqTypeImg"] = ""
        if sortingField == "reqType":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="reqType">"""
            if self.order == "down":
                vars["reqTypeImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self.order == "up":
                vars["reqTypeImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["reqTypeSortingURL"] = quoteattr( str( url ) )


        vars["conf"] = self._conf
        vars["contextHelpContent"] = self.createContextHelp()
        vars["items"] = self.getTableContent()
        self._fromList.append(info.HelperMaKaCInfo.getMaKaCInfoInstance().getNoReplyEmail(returnSupport=False))
        vars['fromList'] = self._fromList
        manager = self._conf.getCSBookingManager()
        vars['manager'] = manager
        vars['user'] = self._user

        if hasattr(manager, "_speakerWrapperList"):
            vars['signatureCompleted'] = manager.areSignatureCompleted()
        else:
            vars['signatureCompleted'] = None

        vars['canShow'] = manager.isAnyRequestAccepted()

        vars['urlPaperAgreement'] = self.getPaperAgreementURL()
        return vars