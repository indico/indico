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

import urllib
from datetime import datetime, timedelta
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.linking as linking
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.schedule as schedule
import MaKaC.conference as conference
import MaKaC.webinterface.pages.category as category
import MaKaC.common.Configuration as Configuration
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.contributions as contributions
import MaKaC.webinterface.pages.subContributions as subContributions
import MaKaC.webinterface.pages.material as material
import MaKaC.webinterface.timetable as timetable
import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.webinterface.displayMgr as displayMgr
import MaKaC.webinterface.navigation as navigation
from MaKaC.common import Config
from xml.sax.saxutils import quoteattr, escape
from MaKaC.common.general import *
from MaKaC.webinterface.general import WebFactory
from MaKaC.webinterface.pages.category import WPConferenceCreationMainData
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase
from MaKaC.webinterface.materialFactories import ConfMFRegistry, ContribMFRegistry
from MaKaC.webinterface.pages import evaluations
from MaKaC.i18n import _
import MaKaC.common.timezoneUtils as timezoneUtils

class WebFactory(WebFactory):
    ##Don't remove this commentary. Its purpose is to be sure that those words/sentences are in the dictionary after extraction. It also prevents the developper to create an init for this class and update the 283 Webfactory occurences...
    ##_("Meeting")
    ##_("""this type is meant for events which contain several contributions or talks and that require schedulling and eventually organising of those contributions in sessions""")
    id = "meeting"
    iconURL = Configuration.Config.getInstance().getSystemIconURL( "meeting" )
    name = "Meeting"
    description = """this type is meant for events which contain several contributions or talks and that require schedulling and eventually organising of those contributions in sessions"""


######### Conference Creation/Display/Modifications ##########################

    @staticmethod
    def getEventCreationPage( rh, targetCateg ):
        return WPMeetingEventCreation( rh, targetCateg )

    @staticmethod
    def getConferenceDisplayPage( rh, conference, params ):
        return conferences.WPMeetingTimeTable(rh,conference, "static", "meeting", {})

    @staticmethod
    def getIconURL():
        return WebFactory.iconURL

    @staticmethod
    def customiseSideMenu( webPageWithSideMenu ):
        webPageWithSideMenu._programMenuItem.setVisible(False)
        webPageWithSideMenu._abstractMenuItem.setVisible(False)
        webPageWithSideMenu._layoutMenuItem.setVisible(False)
        webPageWithSideMenu._contribListMenuItem.setVisible(False)
        webPageWithSideMenu._regFormMenuItem.setVisible(False)

    @staticmethod
    def customiseToolsTabCtrl( tabCtrl ):
        tabCtrl.getTabById("clone").enable()
        tabCtrl.getTabById("matPackage").enable()
        tabCtrl.getTabById("offlineSite").enable()
        tabCtrl.getTabById("close").enable()
        tabCtrl.getTabById("delete").enable()
        tabCtrl.getTabById("badges").disable()
        tabCtrl.getTabById("alarms").enable()
        tabCtrl.getTabById("posters").enable()
        tabCtrl.getTabById("badges").disable()


    @staticmethod
    def getConfModif(rh, conf):
        return WPMConfModif(rh, conf)

    @staticmethod
    def getConfModifAC(rh, conf):
        return WPMConfModifAC(rh, conf)

    @staticmethod
    def getConfModifTools(rh, conf):
        return conferences.WPConfDisplayAlarm(rh, conf)

    @staticmethod
    def getConfModifBookings(rh, conf, bs):
        return WPMConfModifBookings(rh, conf, bs)

    @staticmethod
    def getConfModifListings(rh, conf):
        return WPMConfModifListings(rh, conf)

    @staticmethod
    def getConfClone(rh, conf):
        return WPMConfClone(rh, conf)

    @staticmethod
    def getConfModifSchedule (rh, conf):
        return WPMConfModifSchedule(rh, conf)

    @staticmethod
    def getConfAddContribution(rh, conf, targetday):
        return WPMConfAddContribution(rh,conf, targetday)

    @staticmethod
    def getTimeTableCustomizePDF(rh, conf, view):
        return WPMTimeTableCustomizePDF(rh, conf, view)

    @staticmethod
    def getConferenceDisplayWriteMinutes(rh, contrib):
        return WPMConferenceDisplayWriteMinutes(rh,contrib)

    @staticmethod
    def getDisplayFullMaterialPackage(rh, conf):
        return WPMDisplayFullMaterialPackage(rh,conf)

########### Material Display #################################################

    def getMaterialDisplay( rh, material):
        return WPMMaterialDisplay(rh, material)
    getMaterialDisplay = staticmethod(getMaterialDisplay)

    def getMaterialDisplayRemoveResourceConfirm(rh, conf, res):
        return WPMMaterialDisplayRemoveResourceConfirm(rh, conf, res)
    getMaterialDisplayRemoveResourceConfirm = staticmethod(getMaterialDisplayRemoveResourceConfirm)

############# Subcontribution Display##########################################

    def getSubContributionDisplay(rh, subcontrib):
        return WPMSubContributionDisplay(rh, subcontrib)
    getSubContributionDisplay = staticmethod(getSubContributionDisplay)

    def getSubContributionDisplayWriteMinutes(rh, session):
        return WPMSubContributionDisplayWriteMinutes(rh,session)
    getSubContributionDisplayWriteMinutes = staticmethod(getSubContributionDisplayWriteMinutes)

############# Contribution Display #############################################

    def getContributionDisplay(rh, contrib):
        return WPMContributionDisplay(rh,contrib)
    getContributionDisplay = staticmethod(getContributionDisplay)

############# Contribution modification #########################################
    def getContributionModification(rh, contrib):
        return WPMContributionModification(rh,contrib)
    getContributionModification = staticmethod(getContributionModification)

    def getContribModifSC(rh,contrib):
        return WPMContributionModifSC(rh,contrib)
    getContribModifSC = staticmethod(getContribModifSC)

    def getContribModifAC(rh, contrib):
        return WPMContribModifAC(rh,contrib)
    getContribModifAC = staticmethod(getContribModifAC)

    def getContributionModifTools(rh, contrib):
        return WPMContributionModifTools (rh,contrib)
    getContributionModifTools = staticmethod(getContributionModifTools)

    def getContributionEditData(rh, contrib):
        return WPMContribEditData(rh, contrib)
    getContributionEditData = staticmethod (getContributionEditData)

    def getContributionNewspeaker(rh, contrib):
        return WPMModNewSpeaker (rh,contrib)
    getContributionNewspeaker = staticmethod(getContributionNewspeaker)

    def getContribAddMaterial(rh,contrib, mf):
        return WPMContribAddMaterial (rh,contrib,mf)
    getContribAddMaterial = staticmethod(getContribAddMaterial)

    def getModSpeaker (rh, contrib):
        return WPMModSpeaker(rh, contrib)
    getModSpeaker = staticmethod(getModSpeaker)

    def getContribAddSC(rh, contrib):
        return WPMContribAddSC(rh,contrib)
    getContribAddSC = staticmethod(getContribAddSC)

    def getContributionDisplayWriteMinutes(rh, contrib):
        return WPMContributionDisplayWriteMinutes(rh,contrib)
    getContributionDisplayWriteMinutes = staticmethod(getContributionDisplayWriteMinutes)

########## Session Display###########################################

    def getSessionDisplay(rh,session):
        return WPMSessionDisplay (rh,session)
    getSessionDisplay = staticmethod(getSessionDisplay)

    def getSessionDisplayWriteMinutes(rh, session):
        return WPMSessionDisplayWriteMinutes(rh,session)
    getSessionDisplayWriteMinutes = staticmethod(getSessionDisplayWriteMinutes)

############Session Modificiations###########################################
    def getModSlotEdit(rh, slotData):
        return WPMModSlotEdit(rh, slotData)
    getModSlotEdit = staticmethod(getModSlotEdit)

    def getSessionAddBreak(rh, slot):
        return WPMSessionAddBreak(rh,slot)
    getSessionAddBreak = staticmethod(getSessionAddBreak)

    def getSessionDataModification(self, session):
        return WPMSessionDataModification (self,session)
    getSessionDataModification = staticmethod(getSessionDataModification)

    def getSessionModifMaterials():
        return WPMSessionModifMaterials
    getSessionModifMaterials = staticmethod(getSessionModifMaterials)

    def getModSlotRemConfirmation(self, slot):
        return WPMModSlotRemConfirmation(self,slot)
    getModSlotRemConfirmation = staticmethod(getModSlotRemConfirmation)

    def getModConvenerNew(self,session):
        return WPMModConvenerNew(self,session)
    getModConvenerNew = staticmethod(getModConvenerNew)

    def getSessionAddMaterial(self,session,mf):
        return WPMSessionAddMaterial(self,session,mf)
    getSessionAddMaterial = staticmethod(getSessionAddMaterial)

    def getSessionModification(rh,session):
        return WPMSessionModification(rh,session)
    getSessionModification = staticmethod(getSessionModification)

    def getSessionModifAC(rh, session):
        return WPMSessionModifAC(rh,session)
    getSessionModifAC = staticmethod(getSessionModifAC)

    def getSessionModifTools(rh, session):
        return WPMSessionModifTools(rh,session)
    getSessionModifTools = staticmethod(getSessionModifTools)

    def getSessionModifComm(rh, session):
        return WPMSessionModifComm(rh,session)
    getSessionModifComm = staticmethod(getSessionModifComm)

    def getSessionModifCommEdit(rh, session):
        return WPMSessionModifCommEdit(rh,session)
    getSessionModifCommEdit = staticmethod(getSessionModifCommEdit)

    def getSessionModifSchedule(rh,session):
        return WPMSessionModifSchedule(rh,session)
    getSessionModifSchedule = staticmethod(getSessionModifSchedule)

    def getModConvenerEdit(rh, session):
        return WPMModConvenerEdit(rh, session)
    getModConvenerEdit = staticmethod (getModConvenerEdit)

#################### Participants #####################################

    def getConfModifParticipantsNewPending(rh, conf):
        return WPMConfModifParticipantsNewPending(rh, conf)
    getConfModifParticipantsNewPending = staticmethod(getConfModifParticipantsNewPending)

#################### Evaluation #####################################

    def getEvaluationDisplay(rh, conf):
        return WPMEvaluationDisplay(rh, conf)
    getEvaluationDisplay = staticmethod(getEvaluationDisplay)

    def getEvaluationDisplayModif(rh, conf):
        return WPMEvaluationDisplayModif(rh, conf)
    getEvaluationDisplayModif = staticmethod(getEvaluationDisplayModif)

    def getEvaluationSubmitted(rh, conf, mode):
        return WPMEvaluationSubmitted(rh, conf, mode)
    getEvaluationSubmitted = staticmethod(getEvaluationSubmitted)

    def getEvaluationFull(rh, conf):
        return WPMEvaluationFull(rh, conf)
    getEvaluationFull = staticmethod(getEvaluationFull)

    def getEvaluationClosed(rh, conf):
        return WPMEvaluationClosed(rh, conf)
    getEvaluationClosed = staticmethod(getEvaluationClosed)

    def getEvaluationSignIn(rh, conf):
        return WPMEvaluationSignIn(rh, conf)
    getEvaluationSignIn = staticmethod(getEvaluationSignIn)

    def getEvaluationInactive(rh, conf):
        return WPMEvaluationInactive(rh, conf)
    getEvaluationInactive = staticmethod(getEvaluationInactive)

#################### Alarms #####################################

    def getConfAddAlarm(rh, conf):
        return WPMConfAddAlarm(rh, conf)
    getConfAddAlarm = staticmethod(getConfAddAlarm)

MeetingWebFactory = WebFactory

#################### Event Creation #####################################
class WPMeetingEventCreation( WPConferenceCreationMainData):

    def _getWComponent( self ):
        return WMeetingCreation( self._target, rh = self._rh )

class WMeetingCreation(category.WConferenceCreation):
    def __init__( self, targetCateg, type="meeting", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh

    def getVars( self ):
        vars = category.WConferenceCreation.getVars( self )
        vars["event_type"] = WebFactory.getId()
        return vars


################# Minutes #########################################

class WPMConferenceDisplayWriteMinutes(conferences.WPConferenceDefaultDisplayBase):

    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf), \
                      }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body = _("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("Minutes") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._conf )
        pars = {"postURL": urlHandlers.UHConferenceDisplayWriteMinutes.getURL(self._conf) }
        return wc.getHTML( pars )

################# Subcontribution Display ##############################

class WPMSubContributionDisplay(subContributions.WPSubContributionDisplay):
    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf), \
                      }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body = _("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("SubContribution View") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody(self,params):
        wc=WMSubContributionDisplay(self._getAW(),self._subContrib)
        return wc.getHTML()


class WMSubContributionDisplayBase(subContributions.WSubContributionDisplayBase):
    def getVars( self ):
        vars = subContributions.WSubContributionDisplayBase.getVars( self )
        vars["modifyIcon"] = Config.getInstance().getSystemIconURL( "modify" )
        vars ["modifyURL"]= urlHandlers.UHSubContributionModification.getURL(self._subContrib)
        return vars

class WMSubContributionDisplay(subContributions.WSubContributionDisplay):
    def getHTML(self,params={}):
        if self._subContrib.canModify( self._aw ):
            c = WMSubContributionDisplayFull( self._aw, self._subContrib)
            return c.getHTML( params )
        if self._subContrib.canView( self._aw ):
            c = WMSubContributionDisplayMin( self._aw, self._subContrib)
            return c.getHTML( params )
        return ""

class WMSubContributionDisplayFull(WMSubContributionDisplayBase):
    pass

class WMSubContributionDisplayMin (WMSubContributionDisplayBase):
    pass

class WPMSubContributionDisplayWriteMinutes(WPMSubContributionDisplay):
    navigationEntry=navigation.NESubContributionDisplay

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._subContrib )
        pars = {"postURL": urlHandlers.UHSubContributionDisplayWriteMinutes.getURL(self._subContrib) }
        return wc.getHTML( pars )


################# Contribution Display ################################

class WPMContributionDisplay(contributions.WPContributionDisplay):
    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf), \
                      }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body =  _("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("Contribution View") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody(self,params):
        wc=WMContributionDisplay(self._getAW(),self._contrib)
        return wc.getHTML()


class WMContributionDisplay(contributions.WContributionDisplay):
    def getHTML(self,params={}):
        if self._contrib.canAccess( self._aw ):
            c = WMContributionDisplayFull( self._aw, self._contrib)
            return c.getHTML( params )
        if self._contrib.canView( self._aw ):
            c = WMContributionDisplayMin( self._aw, self._contrib)
            return c.getHTML( params )
        return ""

class WMContributionDisplayBase(contributions.WContributionDisplayBase):
    def getVars( self ):
        vars = contributions.WContributionDisplayBase.getVars( self )
        return vars

class WMContributionDisplayFull(WMContributionDisplayBase):
    pass

class WMContributionDisplayMin (WMContributionDisplayBase):
    pass

class WPMContributionDisplayWriteMinutes(WPMContributionDisplay):

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._contrib )
        pars = {"postURL": urlHandlers.UHContributionDisplayWriteMinutes.getURL(self._contrib) }
        return wc.getHTML( pars )

#################Session Display ######################################

class WPMSessionDisplay(sessions.WPSessionDisplay):
    navigationEntry =  navigation.NEMeetingSessionDisplay
    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf), \
                      }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body =  _("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("Session View") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody(self,params):
        wc=WMSessionDisplay(self._getAW(),self._session)
        return wc.getHTML({"activeTab":params["activeTab"],
                            "sortingCrit":params.get("sortingCrit",None)})

class WMSessionDisplay(sessions.WSessionDisplay):
    def getHTML(self,params={}):
        if self._session.canAccess( self._aw ):
            c=WMSessionDisplayFull(self._aw,self._session,params["activeTab"],
                    params.get("sortingCrit",None))
            return c.getHTML( params )
        if self._session.canView( self._aw ):
            c = WMSessionDisplayMin(self._aw,self._session,params["activeTab"],
                    params.get("sortingCrit",None))
            return c.getHTML( params )
        return ""



class WMSessionDisplayBase(sessions.WSessionDisplayBase):
    pass


class WMSessionDisplayMin(WMSessionDisplayBase ):
    pass

class WMSessionDisplayFull(WMSessionDisplayBase ):
    def _createTabCtrl( self ):
        self._tabCtrl=wcomponents.TabControl()
        url=urlHandlers.UHSessionDisplay.getURL(self._session)
        url.addParam("tab","contribs")
        self._tabContribs=self._tabCtrl.newTab("contribs", \
                                                _("Contribution List"),str(url))
        self._tabCtrl.getTabById("contribs").disable()
        url.addParam("tab","time_table")
        self._tabTimeTable=self._tabCtrl.newTab("time_table", \
                                                _("Time Table"),str(url))
        if self._session.getScheduleType()=="poster":
            self._tabTimeTable.setEnabled(False)
            self._tabCtrl.getTabById("contribs").setActive()
        else:
            self._tabTimeTable.setEnabled(True)
            tab=self._tabCtrl.getTabById(self._activeTab)
            if tab is None:
                tab=self._tabCtrl.getTabById("time_table")
            tab.setActive()

class WPMSessionDisplayWriteMinutes(WPMSessionDisplay):

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._session )
        pars = {"postURL": urlHandlers.UHSessionDisplayWriteMinutes.getURL(self._session) }
        return wc.getHTML( pars )

#################Contribution Modification##############################

##Taking subContribTabs out and changing link at top##
#class ContribModifTabsFrame:
#
#    @staticmethod
#    def _getBody( self, params ):
#        self._createTabCtrl()
#
#        banner = wcomponents.WBannerModif().getHTML(self._target)
#        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
#        return banner + body

class WPMContributionModification(contributions.WPContributionModification):

    def _getTabContent( self, params ):
        from MaKaC.webinterface.pages.contributions import WContribModifMain
        wc = WContribModifMain( self._contrib, ContribMFRegistry(), eventType = "meeting" )
        return wc.getHTML()

class WPMModSpeaker(contributions.WPModSpeaker):
    pass
    #def _getBody( self, params ):
    #    return ContribModifTabsFrame._getBody(self, params)

class WPMContribAddMaterial(contributions.WPContribAddMaterial):
    pass
#    def _getBody( self, params ):
#        return ContribModifTabsFrame._getBody(self, params)

class WPMModNewSpeaker(contributions.WPModNewSpeaker):
    pass
#    def _getBody( self, params ):
#        return ContribModifTabsFrame._getBody(self, params)

class WPMContribEditData(contributions.WPEditData):
    pass

class WPMContributionModifSC(contributions.WPContribModifSC):
    pass

class WPMContribModifAC(contributions.WPContribModifAC):
    pass

class WPMContributionModifTools(contributions.WPContributionModifTools):
    pass
#    def _getBody( self, params ):
#        return ContribModifTabsFrame._getBody(self, params)

class WMContribModifMain(contributions.WContribModifMain):
    pass


class WPMContribAddSC(contributions.WPContribAddSC):
    pass

################ Material Display #############################


class WPMMaterialDisplayBase( material.WPMaterialDisplayBase):

    def __init__( self, rh, materialObj ):
        material.WPMaterialDisplayBase.__init__(self, rh, materialObj)
        self._extraCSS.append(" body { background: #424242; } ")

    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf) }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        confTitle = self._conf.getTitle()
        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body =  _("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td><div class="groupTitle">_("Added Material") - %s</div></td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen, confTitle,
                        self._getNavigationBarHTML(),
                        body)
        return frame.getHTML( body, frameParams)

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

class WMConfDisplayFrame(conferences.WConfDisplayFrame):
    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["logo"] = ""
        if self._conf.getLogo():
            vars["logo"] = "<img src=\"%s\" alt=\"%s\" border=\"0\">"%(vars["logoURL"], self._conf.getTitle())
        vars["confTitle"] = self._conf.getTitle()
        vars["displayURL"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        vars["imgConferenceRoom"] = Config.getInstance().getSystemIconURL( "conferenceRoom" )
        #################################
        # Fermi timezone awareness      #
        #################################
        #vars["confDateInterval"] = "from %s to %s"%(self._conf.getStartDate().strftime("%d %B %Y"), self._conf.getEndDate().strftime("%d %B %Y"))
        #if self._conf.getStartDate().strftime("%d%B%Y") == \
        #        self._conf.getEndDate().strftime("%d%B%Y"):
        #    vars["confDateInterval"] = self._conf.getStartDate().strftime("%d %B %Y")
        #elif self._conf.getStartDate().month == self._conf.getEndDate().month:
        #    vars["confDateInterval"] = "%s-%s %s"%(self._conf.getStartDate().day, self._conf.getEndDate().day, self._conf.getStartDate().strftime("%B %Y"))
        vars["confDateInterval"] = "from %s to %s"%(self._conf.getStartDate().strftime("%d %B %Y"), self._conf.getEndDate().strftime("%d %B %Y"))
        if self._conf.getStartDate().strftime("%d%B%Y") == \
                self._conf.getEndDate().strftime("%d%B%Y"):
            vars["confDateInterval"] = self._conf.getStartDate().strftime("%d %B %Y")
        elif self._conf.getStartDate().month == self._conf.getEndDate().month:
            vars["confDateInterval"] = "%s-%s %s"%(self._conf.getStartDate().day, self._conf.getEndDate().day, self._conf.getStartDate().strftime("%B %Y"))
        #################################
        # Fermi timezone awareness(end) #
        #################################
        vars["body"] = self._body
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
            vars["supportEmail"] = ""
        if self._conf.hasSupportEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] =  _("""<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email"> %s</a>""")%(mailto,
                                                        Config.getInstance().getSystemIconURL("mail"),
                                                        displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getSupportEmailCaption())
        format = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
        vars["bgColorCode"] = format.getFormatOption("titleBgColor")["code"]
        vars["textColorCode"] = format.getFormatOption("titleTextColor")["code"]
        return vars

    def getHTML( self, body, params ):
        self._body = body
        return wcomponents.WTemplated.getHTML( self, params )

class WMMaterialDisplay(material.WMaterialDisplay):
        def __init__(self, aw, material, modif):
            self._material=material
            self._aw=aw
            self._modif = modif

        def getVars( self ):
            vars=material.WMaterialDisplay.getVars( self )
            vars["modif"]=""
            if self._modif==1:
                vars["modif"] = """<a href="%s"><img class="imglink" src="%s" alt="Modify"></a>"""%(urlHandlers.UHMaterialModification.getURL(self._material),Config.getInstance().getSystemIconURL( "modify" ))
            return vars

class WPMMaterialDisplay( WPMMaterialDisplayBase):
    navigationEntry = navigation.NEMeetingMaterialDisplay
    def __init__(self, rh, material):
        WPMMaterialDisplayBase.__init__(self, rh, material)

    def _getBody( self, params ):
        self._modif=0
        if self._target.canModify(self._getAW()):
            self._modif = 1
        wc = WMMaterialDisplay( self._getAW(), self._material, self._modif )
        pars = { "fileAccessURLGen": urlHandlers.UHFileAccess.getURL }
        return wc.getHTML( pars )

class WPMMaterialDisplayRemoveResourceConfirm(WPMMaterialDisplayBase, material.WPMaterialDisplayRemoveResourceConfirm):
    navigationEntry=navigation.NEMeetingMaterialDisplay

    def __init__(self,rh,conf,res):
        WPMMaterialDisplayBase.__init__(self,rh,res.getOwner())
        self._res=res

    def _getBody(self,params):
        return material.WPMaterialDisplayRemoveResourceConfirm._getBody(self, params)

#################Conference Modification#############################

##Main##
class WPMConfModif(conferences.WPConferenceModification):
    def _getPageContent( self, params ):
        wc = WMConfModifMainData( self._conf, ConfMFRegistry, self._ct, self._rh )
        pars = { "type": params.get("type",""), "conferenceId": self._conf.getId() }
        return wc.getHTML( pars )

class WMConfModifMainData(conferences.WConfModifMainData):
    def getVars(self):
        vars = conferences.WConfModifMainData.getVars( self )

        #enable Evaluation by default
        self._conf.enableSection('evaluation')

        return vars

##Access Control ##
class WPMConfModifAC(conferences.WPConfModifAC):
    pass

class WMConfModifAC(conferences.WConfModifAC):
    pass  #Depends which frames we need inside of AC


##Tools ##
class WPMConfModifTools (conferences.WPConfModifToolsBase):

    def _getTabContent( self, params ):
        wc = WMConfModifTools( self._conf, self._rh._getUser() )
        p = {
            "deleteConferenceURL": urlHandlers.UHConfDeletion.getURL( self._conf ), \
            "cloneConferenceURL": urlHandlers.UHConfClone.getURL( self._conf ), \
            "addAlarmURL": urlHandlers.UHConfAddAlarm.getURL( self._conf ), \
            "deleteAlarmURL": urlHandlers.UHConfDeleteAlarm.getURL(), \
            "modifyAlarmURL": urlHandlers.UHConfModifyAlarm.getURL(), \
            }
        return wc.getHTML( p )

class WMConfModifTools (conferences.WConfModifTools):
    pass

#Bookings#

class WPMConfModifBookings(conferences.WPConfModifBookings):
    pass

class WMConfModifBookings (conferences.WConfModifBookings):
    pass

##

class WPMConfModifListings (conferences.WPConfModifListings):

    def _getTabContent( self, params ):
        wc = WMConfModifListings( self._conf )
        return wc.getHTML()

class WMConfModifListings (conferences.WConfModifListings):
    pass

class WPMConfClone(conferences.WPConfClone):

    def _getTabContent( self, params ):
        p = conferences.WConferenceClone( self._conf )
        pars = { \
"cancelURL": urlHandlers.UHConfModifTools.getURL( self._conf ), \
"cloneOnce": urlHandlers.UHConfPerformCloneOnce.getURL( self._conf ), \
"cloneInterval": urlHandlers.UHConfPerformCloneInterval.getURL( self._conf ), \
"cloneday": urlHandlers.UHConfPerformCloneDays.getURL( self._conf ), \
"cloning" : urlHandlers.UHConfPerformCloning.getURL( self._conf ),
"cloneOptions": _("""<li><input type="checkbox" name="cloneTimetable" id="cloneTimetable" value="1" checked="checked" />_("Full timetable")</li>
                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneSessions" id="cloneSessions" value="1" />_("Sessions")</li></ul></li>
                     <li><input type="checkbox" name="cloneParticipants" id="cloneParticipants" value="1" checked="checked" />_("Participants")</li>
                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneAddedInfo" id="cloneAddedInfo" value="1" />_("send email to the participants of the created event")</li></ul></li>
                     <li><input type="checkbox" name="cloneEvaluation" id="cloneEvaluation" value="1" />_("Evaluation")</li>
               """) }
        return p.getHTML( pars )

##TimeTable view##
class WPMConfModifSchedule(conferences.WPConfModifScheduleGraphic):
    pass

## Add Contributions to main meeting ##
class WPMConfAddContribution(conferences.WPModScheduleNewContrib):

    def __init__(self, rh, conf, targetDay):
        conferences.WPModScheduleNewContrib.__init__(self, rh, conf)
        self._targetDay = targetDay


    def _getTabContent( self, params ):
        p = WMContributionCreation( self._conf, self._targetDay )
        pars = {"postURL": urlHandlers.UHMConfPerformAddContribution.getURL(), \
        "calendarIconURL": Config.getInstance().getSystemIconURL( "calendar" ), \
        "calendarSelectURL":  urlHandlers.UHSimpleCalendar.getURL(), \
        "targetDay": self._targetDay.strftime("%Y-%m-%d") \
        }
        return p.getHTML(pars)


class WMContributionCreation(conferences.WContributionCreation):

    def __init__( self, target, targetDay):
        conferences.WContributionCreation.__init__(self, target)
        self._targetDay=targetDay

    def getVars( self ):
        vars = conferences.WContributionCreation.getVars( self )
        vars["sHour"]=self._targetDay.hour
        vars["sMinute"]=self._targetDay.minute
        vars["durationHours"],vars["durationMinutes"]="0","20"
        return vars

######################### Session View #######################

##TabControl####
class WPMSessionAddMaterial(sessions.WPSessionAddMaterial):
    def _setupTabCtrl(self):
        self._tabContribs.disable()


class WPMModConvenerEdit(sessions.WPModConvenerEdit):
    def _setupTabCtrl(self):
        self._tabContribs.disable()


class WPMModConvenerNew(sessions.WPModConvenerNew):
    def _setupTabCtrl(self):
        self._tabContribs.disable()


class WPMModSlotRemConfirmation(sessions.WPModSlotRemConfirmation):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionDataModification(sessions.WPSessionDataModification):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionAddBreak(sessions.WPSessionAddBreak):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMModSlotEdit(sessions.WPModSlotEdit):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModification( sessions.WPSessionModification ):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifMaterials( sessions.WPSessionModifMaterials ):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifAC(sessions.WPSessionModifAC):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifTools(sessions.WPSessionModifTools):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifComm(sessions.WPSessionModifComm):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifCommEdit(sessions.WPSessionCommEdit):
    def _setupTabCtrl(self):
        self._tabContribs.disable()

class WPMSessionModifSchedule(sessions.WPSessionModifSchedule):
    pass

################# Session Modification ###################################

##Change slot options##
class WMSessionModifSchedule(sessions.WSessionModifSchedule):

    def _getFitSlotLink( self, container, linkColor ):
        """
        returns a link to the "fit slot" action if and only if
        the time slot has a son and its limits are larger than its sons'
        """
        fitSlotLink = ""
        entries = container.getSessionSlot().getSchedule().getEntries()
        if len(entries) > 0:
            if container.getStartDate()<entries[0].getStartDate() or container.getEndDate()>entries[-1].getEndDate():
                fitSlotLink =  _("""<input type="submit" value="_("fit slot")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlHandlers.UHSessionFitSlot.getURL(container.getSessionSlot()))
        return fitSlotLink

    def _getCompactSlotLink( self, container, linkColor ):
        """
        returns a link to the "compact slot" action if and only if
        the time slot has sons which have space between them
        """
        compactSlotLink = ""
        sch = container.getSessionSlot().getSchedule()
        if sch.hasGap():
            compactSlotLink =  _("""<input type="submit" value="_("compact slot")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlHandlers.UHSessionModSlotCompact.getURL(container.getSessionSlot()))
        return compactSlotLink

    def _getAddContribLink( self, container, linkColor ):
        """
        returns a link to the "add contribution" action if and only if
        contributions exists in the current session which are not yet scheduled
        """
        l=[]
        for contrib in self._session.getContributionList():
            if contrib.isScheduled() or \
                isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn):
                continue
            l.append(contrib)
        if len(l)>0:
            addContrib =  _("""<input type="submit" value="_("add contribution")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlHandlers.UHSessionAddContribution.getURL(container.getSessionSlot()))
        else:
            addContrib = ""
        return addContrib

    def _getContainerHeaderHTML(self, container, bgcolorSlot, colspan, width, eventType):
        # header is displayed just in the first slot of a container:
        room=""
        if container.getRoom() is not None and container.getRoom().getName().strip()!="":
            room="at %s"%container.getRoom().getName()

        orginURL = urlHandlers.UHSessionModifSchedule.getURL(self._session.getOwner())
        orginURL.addParam("sessionId", self._session.getId())
        urlNewContrib = urlHandlers.UHConfModScheduleNewContrib.getURL(self._session.getOwner())
        urlNewContrib.addParam("sessionId", self._session.getId())
        urlNewContrib.addParam("slotId", container.getSessionSlot().getId())
        urlNewContrib.addParam("orginURL",orginURL)
        urlNewContrib.addParam("eventType",eventType)

        urlAddBreak = urlHandlers.UHSessionAddBreak.getURL(container.getSessionSlot())
        urlDelSlot = urlHandlers.UHSessionModSlotRem.getURL(container.getSessionSlot())
        urlEditSlot = urlHandlers.UHSessionModSlotEdit.getURL(container.getSessionSlot())
        urlCalSlot = urlHandlers.UHSessionModSlotCalc.getURL(container.getSessionSlot())
        sdate = self.htmlText(container.getAdjustedStartDate().strftime("%Y-%b-%d %H:%M"))
        edate = self.htmlText(container.getEndDate().strftime("%Y-%b-%d %H:%M"))
        if container.getAdjustedStartDate().strftime("%Y-%b-%d") == container.getEndDate().strftime("%Y-%b-%d"):
            sdate = self.htmlText(container.getAdjustedStartDate().strftime("%H:%M"))
            edate = self.htmlText(container.getAdjustedEndDate().strftime("%H:%M"))
        linkColor=""
        if self._session.isTextColorToLinks():
            linkColor="color:%s"%self._session.getTextColor()
        addContrib = ""#self._getAddContribLink(container, linkColor)
        fitSlotLink = self._getFitSlotLink(container, linkColor)
        compactSlotLink = self._getCompactSlotLink(container, linkColor)
        editSlotLink,delSlotLink="",""
        if self._session.canModify(self._aw) or self._session.canCoordinate(self._aw, "unrestrictedSessionTT"):
            if self._session.getConference().getEnableSessionSlots() :
                editSlotLink= _("""<input type="submit" value="_("edit slot")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlEditSlot)
                if len(self._session.getSlotList()) > 1:
                    delSlotLink= _("""<input type="submit" value="_("delete slot")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlDelSlot)
        title = self.htmlText(container.getTitle())
        duration = container.getDuration()
        conveners=""
        convenerList=[]
        if container.getConvenerList()!=[]:
            for conv in container.getConvenerList():
                convenerList.append(conv.getFullName())
        elif container.getSessionSlot().getSession().getConvenerList()!=[]:
            for conv in container.getSessionSlot().getSession().getConvenerList():
                convenerList.append(conv.getFullName())
        if convenerList != []:
            conveners = _("""
                        <tr>
                            <td width="100%%" align="center" style="color:%s"><small> _("Conveners"): %s</small></td>
                        </tr>
                    """)%(self._session.getTextColor(), "; ".join(convenerList))
        return  _("""
        <td colspan="%s" bgcolor="%s" align="center" valign="middle" width="%s%%" style="color: black; border-top: 2px solid #E6E6E6; margin-left:1px;">
                        <table width="100%%">
                            <tr>
                                <td align="right">
                                    %s
                                    <input type="submit" value="_("new contribution")" onClick="self.location.href='%s';return false;" class="smallbtn"><input type="submit" value="_("new break")" onClick="self.location.href='%s';return false;" class="smallbtn">%s%s%s%s<input type="submit" value="_("reschedule")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                </td>
                            </tr>
                            <tr>
                                <td width="100%%" align="center" style="color:%s"><b>%s</b></td>
                            </tr>
                            %s
                            <tr>
                                <td width="100%%" align="center" style="color:%s"><b>%s-%s (%s) %s</b></td>
                            </tr>
                        </table>
                    </td>
                        """)%(colspan, \
                             bgcolorSlot, \
                             width, \
                             addContrib, \
                             str(urlNewContrib),\
                             str(urlAddBreak),\
                             editSlotLink,delSlotLink,fitSlotLink,compactSlotLink,str(urlCalSlot),\
                             self._session.getTextColor(), title,\
                             conveners,\
                             self._session.getTextColor(), \
                             sdate,\
                             edate, \
                             self.htmlText((datetime(1900,1,1)+duration).strftime("%Hh%M'")), \
                             room or "&nbsp;")

    def _getContainerFooterHTML(self, container, bgcolorSlot, colspan, width, eventType):
        # footer is displayed just in the last slot of a container:

        orginURL = urlHandlers.UHSessionModifSchedule.getURL(self._session.getOwner())
        orginURL.addParam("sessionId", self._session.getId())
        urlNewContrib = urlHandlers.UHConfModScheduleNewContrib.getURL(self._session.getOwner())
        urlNewContrib.addParam("sessionId", self._session.getId())
        urlNewContrib.addParam("slotId", container.getSessionSlot().getId())
        urlNewContrib.addParam("orginURL",orginURL)
        urlNewContrib.addParam("eventType",eventType)

        urlAddBreak = urlHandlers.UHSessionAddBreak.getURL(container.getSessionSlot())
        urlDelSlot = urlHandlers.UHSessionModSlotRem.getURL(container.getSessionSlot())
        urlEditSlot = urlHandlers.UHSessionModSlotEdit.getURL(container.getSessionSlot())
        urlCalSlot = urlHandlers.UHSessionModSlotCalc.getURL(container.getSessionSlot())
        editSlotLink,delSlotLink="",""
        linkColor=""
        if self._session.isTextColorToLinks():
            linkColor="color:%s"%self._session.getTextColor()
        addContrib = ""#self._getAddContribLink(container, linkColor)
        fitSlotLink = self._getFitSlotLink(container, linkColor)
        compactSlotLink = self._getCompactSlotLink(container, linkColor)
        if self._session.canModify(self._aw) or self._session.canCoordinate(self._aw, "unrestrictedSessionTT"):
            if self._session.getConference().getEnableSessionSlots() :
                editSlotLink= _("""<input type="submit" value="_("edit slot")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlEditSlot)
                if len(self._session.getSlotList()) > 1:
                    delSlotLink= _("""<input type="submit" value="_("delete slot")" onClick="self.location.href='%s';return false;" class="smallbtn">""")%str(urlDelSlot)

        return  _("""
        <td colspan="%s" bgcolor="%s" align="center" valign="middle" width="%s%%" style="color: black;">
        <table width="100%%">
                            <tr>
                                <td align="right">
                                    %s
                                    <input type="submit" value="_("new contribution")" onClick="self.location.href='%s';return false;" class="smallbtn"><input type="submit" value="_("new break")" onClick="self.location.href='%s';return false;" class="smallbtn">%s%s%s%s<input type="submit" value="_("reschedule")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                </td>
                            </tr>
                        </table>
                    </td>
                        """)%(colspan, \
                             bgcolorSlot, \
                             width, \
                             addContrib, \
                             str(urlNewContrib), \
                             str(urlAddBreak), \
                             editSlotLink,delSlotLink,fitSlotLink,compactSlotLink, str(urlCalSlot))


    def _getSlotsDisabledScheduleHTML(self):
        tz = self._session.getConference().getTimezone()
        timeTable=timetable.TimeTable(self._session.getSlotList()[0].getSchedule(),tz)
        sDate=self._session.getSlotList()[0].getSchedule().getAdjustedStartDate()
        eDate=self._session.getSlotList()[0].getSchedule().getAdjustedEndDate()
        conf = self._session.getConference()
        tzUtil = timezoneUtils.DisplayTZ(self._aw,conf)
        tz = tzUtil.getDisplayTZ()
        timeTable.setStartDate(sDate)
        timeTable.setEndDate(eDate)
        timeTable.mapEntryList(self._session.getSlotList()[0].getSchedule().getEntries())
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/timeTable.getSlotLength().seconds)
        for day in timeTable.getDayList():
            slotList=[]
            lastEntries=[]
            maxOverlap=day.getNumMaxOverlaping()
            width="100"
            if maxOverlap!=0:
                width=100/maxOverlap
            else:
                maxOverlap=1
            for slot in day.getSlotList():
                remColSpan=maxOverlap
                temp=[]
                for entry in slot.getEntryList():
                    if len(slot.getEntryList()):
                        remColSpan=0
                    else:
                        remColSpan-=1
                    if entry in lastEntries:
                        continue
                    bgcolor=self._getColor(entry)
                    colspan=""
                    if not day.hasEntryOverlaps(entry):
                        colspan=""" colspan="%s" """%maxOverlap
                    temp.append("""<td valign="top" rowspan="%i" align="center" bgcolor="%s" width="%i%%"%s>%s</td>"""%(day.getNumSlots(entry),bgcolor,width,colspan,self._getEntryHTML(entry)))
                    lastEntries.append(entry)
                if remColSpan>0:
                    temp.append("""<td width="100%%" colspan="%i"></td>"""%(remColSpan))
                if slot.getStartDate().minute==0:
                    temp="""
                        <tr>
                            <td valign="top" rowspan="%s" bgcolor="white" width="40"><font color="gray" size="-1">%s</font></td>
                            %s
                        </tr>
                        """%(num_slots_in_hour,\
                                slot.getAdjustedStartDate().strftime("%H:%M"),\
                                "".join(temp))
                else:
                    temp="""<tr>%s</tr>"""%"".join(temp)
                slotList.append(temp)
            orginURL = urlHandlers.UHConfModifSchedule.getURL(self._session)
            reducedScheduleActionURL = urlHandlers.UHReducedSessionScheduleAction.getURL(self._session)
            reducedScheduleActionURL.addParam("slotId",0)
            reducedScheduleActionURL.addParam("orginURL",orginURL)
            res= _("""
        <a href="" name="%s"></a>
        <table align="center" width="100%%">
            <tr>
                <td width="60%%">
                    <table align="center" border="0" width="100%%"
                            celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                        <tr>
                            <td colspan="%i" align="center"
                                                    bgcolor="white">
                                <table cellspacing="0" cellpadding="0"
                                        width="100%%">
                                    <tr>
                                        <td align="center" width="100%%">
                                            <b>%s</b>
                                        </td>
                                        <td align="right">
                                            &nbsp;
                                        </td>
                                        <td align="right">
                                            &nbsp;
                                        </td>
                                        <form action=%s method="POST">
                                        <td align="right">
                                            <input type="submit" class="btn" name="newContrib" value="_("new contribution")">
                                        </td>
                                        <td align="right">
                                            <input type="submit" class="btn" name="newBreak" value="_("new break")">
                                        </td>
                                        <td align="right">
                                            <input type="submit" class="btn" name="reschedule" value="_("reschedule")">
                                        </td>
                                        </form>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        %s
                    </table>
                </td>
            </tr>
        </table>
                """)%(day.getDate().strftime("%Y-%m-%d"),maxOverlap+2,
                        day.getDate().strftime("%A, %d %B %Y"),
                        quoteattr(str(reducedScheduleActionURL)),
                        "".join(slotList))
            daySch.append(res)
        return "<br>".join(daySch)


    def _getScheduleHTML(self, eventType="conference"):
        if self._session.getConference().getEnableSessionSlots() :
            return sessions.WSessionModifSchedule._getScheduleHTML(self,"meeting")
        else :
            return self._getSlotsDisabledScheduleHTML()


    def getVars( self ):
        vars = sessions.WSessionModifSchedule.getVars(self)
        if self._session.getConference().getEnableSessionSlots() :
            vars["fitToInnerSlots"] =  _("""<input type="submit" class="btn" value="_("fit inner timetable")">""")
        else :
            editURL = urlHandlers.UHSessionDatesModification.getURL(self._session)
            vars["fitToInnerSlots"] =  _("""<input type="submit" class="btn" value="_("fit inner timetable")"><input type="submit" class="btn" value="_("modify dates")" onClick="this.form.action='%s';">""") % editURL
        return vars

######################################################################
class WPMeetingDisplay( WPConferenceDisplayBase ):

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

    def _getHeader( self ):
        """
        """

        if hasattr(self, "_view"):
            currentView = self._view
        else:
            currentView = "static"

        wc = wcomponents.WMenuMeetingHeader( self._getAW(),self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(),\
                             "currentView": currentView,\
                             "type": WebFactory.getId(),\
                             "filterActive": False,\
                             "dark": True,\
                             "loginAsURL": self.getLoginAsURL()} )

    def _getBody( self, params ):

        wc = WMeetingDisplay( self._getAW(), self._conf )
        pars = { \
    "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
    "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
    "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
    "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
    "materialURL": urlHandlers.UHMaterialDisplay.getURL }
        return wc.getHTML( pars )


class WMeetingContribBaseDisplayItem(wcomponents.WTemplated):

    def getHTML( self, contribution, aw, modifyURLGen, materialsURLGen, subContribModifyURLGen ):
        self.__contrib = contribution
        self.__modifyURLGen = modifyURLGen
        self.__aw = aw
        self.__materialsURLGen = materialsURLGen
        self.__subContribModifyURLGen = subContribModifyURLGen
        return wcomponents.WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"]=self.__contrib.getTitle()
        sl = []
        if self.__contrib.getSpeakerText() != "":
            sl.append( self.__contrib.getSpeakerText() )
        for speaker in self.__contrib.getSpeakerList():
            sl.append("%s (%s)"%(speaker.getFullName(), speaker.getAffiliation()))
        vars["speakerList"] = ";<br>".join(sl)
        vars["description"] = self.__contrib.getDescription()
        owner = self.__contrib.getOwner()
        vars["place"] = ""
        location = self.__contrib.getOwnLocation()
        if location:
            vars["place"] = "%s"%location.getName().upper()
            if location.getAddress().strip() != "":
                vars["place"] += "(%s)"%location.getAddress()

        room = self.__contrib.getOwnRoom()
        if room:
            location = self.__contrib.getLocation()
            roomLink = linking.RoomLinker().getHTMLLink( room , location )
            if vars["place"].strip() != "":
                vars["place"] += ", "
            vars["place"] += "room: %s"%roomLink
        if vars["place"].strip() != "":
            vars["place"] = "<br>&nbsp;&nbsp;at %s"%vars["place"]
        vars["startDate"] = self.__contrib.getStartDate().strftime("%d-%b-%Y %H:%M")
        if self.__contrib.getParent().getStartDate().strftime("%Y%B%d") ==\
           self.__contrib.getParent().getEndDate().strftime("%Y%B%d"):
            if self.__contrib.getParent().getStartDate().strftime("%Y%B%d") ==\
               self.__contrib.getStartDate().strftime("%Y%B%d"):
                vars["startDate"] = self.__contrib.getStartDate().strftime("%H:%M")
        vars["endDate"] = self.__contrib.getEndDate().strftime("%A %d %B %Y")
        vars["endTime"] = self.__contrib.getEndDate().strftime("%H:%M")
        vars["duration"] = (datetime(1900,1,1)+self.__contrib.getDuration()).strftime("%M'")
        if self.__contrib.getDuration()>timedelta(seconds=3600):
            vars["duration"] = (datetime(1900,1,1)+self.__contrib.getDuration()).strftime("%Hh%M'")
        vars["modifyURL"] = self.__modifyURLGen( self.__contrib )
        ml = []
        for mat in self.__contrib.getAllMaterialList():
            str = wcomponents.WMaterialDisplayItem().getHTML(\
                                                self.__aw, mat, \
                                                self.__materialsURLGen( mat ) )
            if str == "":
                continue
            ml.append(str)
        if len(ml) == 0:
            vars["materials"] = ""
        else:
            vars["materials"] = "(%s)"%", ".join( ml )

        vars["materialURLGen"] = self.__materialsURLGen
        scl = []
        for sc in self.__contrib.getSubContributionList():
            str = WSubContributionMeetingDisplay(self.__aw, sc).getHTML({"modifyURL":self.__subContribModifyURLGen(sc), "materialURLGen":self.__materialsURLGen} )
            if str == "":
                continue
            scl.append(str)
        if len(scl) == 0:
            vars["subConts"] = ""
        else:
            vars["subConts"] = "%s"%" ".join( scl )
        vars["modifyItem"] = ""
        if self.__contrib.canModify( self.__aw ):
            vars["modifyItem"] = """<a href="%s"><img src="%s" border="0" alt="Jump to the modification interface"></a> """%(self.__modifyURLGen( self.__contrib ), Configuration.Config.getInstance().getSystemIconURL("modify") )
        return vars


class WMeetingContribFullDisplayItem(WMeetingContribBaseDisplayItem):
    pass


class WMeetingContribMinimalDisplayItem(WMeetingContribBaseDisplayItem):
    pass


class WMeetingContribDisplayItem:

    def getHTML(self, contrib, aw, modifyURLGen, materialsURLGen, subContribModifyURLGen):
        if not contrib.canView( aw ):
            return ""
        if not contrib.canAccess( aw ):
            return WMeetingContribMinimalDisplayItem().getHTML( contrib, aw, \
                                                modifyURLGen, materialsURLGen, subContribModifyURLGen )
        return WMeetingContribFullDisplayItem().getHTML( contrib, aw, \
                                                modifyURLGen, materialsURLGen, subContribModifyURLGen )

class WMeetingSessionSlotBaseDisplayItem(wcomponents.WTemplated):

    def getHTML( self, slot, aw, modifyURLGen, contribModifyURLGen, materialURLGen, subContribModifyURLGen ):
        self.__session  = slot.getSession()
        self.__slot = slot
        self.__aw = aw
        self.__modifyURLGen = modifyURLGen
        self.__contribModifyURLGen = contribModifyURLGen
        self.__materialURLGen = materialURLGen
        self.__subContribModifyURLGen = subContribModifyURLGen
        html = wcomponents.WTemplated.getHTML( self, {} )
        return html

    def __getSchedule( self, contribModifURLGen, materialURLGen, subContribModifyURLGen ):
        l = []
        for entry in self.__slot.getSchedule().getEntries():
            if type( entry ) == schedule.BreakTimeSchEntry:
                l.append( WMeetingBreakDisplayItem().getHTML(entry, \
                                                      self.__aw) )
            else:
                owner = entry.getOwner()
                if type(owner) is conference.AcceptedContribution or type(owner) is conference.Contribution:
                    l.append( WMeetingContribDisplayItem().getHTML(owner, \
                                                            self.__aw, \
                                                            contribModifURLGen, \
                                                            materialURLGen, \
                                                            subContribModifyURLGen ) )
        return "".join( l )

    def __getHTMLRow( self, title, body ):
        str = """
                <tr>
                    <td valign="top"><strong>%s:</strong></td>
                    <td valign="top" nowrap><small>%s</small></td>
                </tr>"""%(title, body)
        if str.strip() == "":
            return ""
        return str

    def __getConvenersHTML( self, convList ):
        cl = []
        if self.__session.getConvenerText()!="":
            cl.append( self.__session.getConvenerText() )
        for conv in convList:
            cl.append(conv.getFullName())
        html = ""
        if len(cl) > 0:
            html = self.__getHTMLRow( _("Conveners"), "<br>".join(cl) )
        return html

    def __getMaterialHTML( self, matList ):
        ml = []
        for mat in matList:
            str = wcomponents.WMaterialDisplayItem().getHTML(\
                                            self.__aw, mat,\
                                            self.__materialURLGen( mat ) )
            if str == "":
                continue
            ml.append(str)
        str = ""
        if len(ml) > 0:
            str = self.__getHTMLRow( _("Material"), "<br>".join( ml ) )
        return str

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"]=self.__session.getTitle()
        vars["description"] = self.__session.getDescription()
        conf = self.__session.getConference()
        vars["location"] = ""
        location = self.__session.getOwnLocation()
        if location:
            vars["location"] = self.__getHTMLRow( _("Location"), "%s<br>%s"%( location.getName(), location.getAddress() ) )
        vars["room"] = ""
        room = self.__session.getOwnRoom()
        if room:
            location = self.__session.getLocation()
            roomLink = linking.RoomLinker().getHTMLLink( room, location )
            vars["room"] = self.__getHTMLRow( "Room", roomLink )
        vars["startDate"] = self.__session.getStartDate().strftime("%A %d %B %Y")
        vars["startTime"] = self.__session.getStartDate().strftime("%H:%M")
        vars["endDate"] = self.__session.getEndDate().strftime("%A %d %B %Y")
        vars["endTime"] = self.__session.getEndDate().strftime("%H:%M")
        if vars["startDate"] == vars["endDate"]:
            vars["dateInterval"] = "%s (%s -> %s)"%(vars["startDate"],\
                                                    vars["startTime"],\
                                                    vars["endTime"] )
            if conf.getStartDate().strftime("%d%B%Y") == \
                        self.__session.getStartDate().strftime("%d%B%Y") and \
                            conf.getEndDate().strftime("%d%B%Y") == \
                                self.__session.getEndDate().strftime("%d%B%Y"):
                vars["dateInterval"] = "%s -> %s"%( vars["startTime"],\
                                                    vars["endTime"] )
        else:
            vars["dateInterval"] = "%s %s -> %s %s"%(vars["startDate"],\
                                                    vars["startTime"],\
                                                    vars["endDate"],\
                                                    vars["endTime"] )
        vars["modifyURL"] = self.__modifyURLGen( self.__session )
        vars["conveners"] = self.__getConvenersHTML( self.__session.getConvenerList() )
        vars["modifyItem"] = ""
        if self.__session.canModify( self.__aw ):
            vars["modifyItem"] = """<a href="%s"><img src="%s" border="0" alt="Jump to the modification interface"></a> """%(self.__modifyURLGen( self.__session ), Configuration.Config.getInstance().getSystemIconURL("modify") )
        vars["expandIcon"] = ""
        vars["schedule"] = self.__getSchedule(self.__contribModifyURLGen, \
                                              self.__materialURLGen,
                                              self.__subContribModifyURLGen )
        vars["material"] = self.__getMaterialHTML( self.__session.getAllMaterialList() )
        return vars

class WMeetingSessionSlotFullDisplayItem(WMeetingSessionSlotBaseDisplayItem):
    pass

class WMeetingSessionSlotDisplayItem:

    def getHTML(self, slot, aw, modifyURLGen, contribModifyURLGen, materialURLGen, subContribModifyURLGen ):
        session = slot.getSession()
        if not session.canView( aw ):
            return ""
        if not session.canAccess( aw ):
            return WMeetingSessionSlotMinimalDisplayItem().getHTML( slot, aw,\
                                            modifyURLGen, contribModifyURLGen, \
                                            materialURLGen, subContribModifyURLGen )
        return WMeetingSessionSlotFullDisplayItem().getHTML( slot, aw, \
                                            modifyURLGen, contribModifyURLGen, \
                                            materialURLGen, subContribModifyURLGen )

class WMeetingBaseDisplay(wcomponents.WTemplated):

    def getHTML(self, aw, conference, params=None):
        self.__conf = conference
        self.__aw = aw
        return wcomponents.WTemplated.getHTML(self, params)

    def __getSchedule( self, sessionModifURLGen, contribModifURLGen, materialURLGen, subContribModifyURLGen ):
        l = []
        for entry in self.__conf.getSchedule().getEntries():
            if type( entry ) == schedule.LinkedTimeSchEntry and \
               type( entry.getOwner() ) == conference.SessionSlot:
                l.append( WMeetingSessionSlotDisplayItem().getHTML(entry.getOwner(), \
                                                        self.__aw, \
                                                        sessionModifURLGen, \
                                                        contribModifURLGen, \
                                                        materialURLGen,\
                                                        subContribModifyURLGen) )
            elif type( entry ) == schedule.LinkedTimeSchEntry and \
                 type( entry.getOwner() ) == conference.Contribution:
                l.append( WMeetingContribDisplayItem().getHTML(entry.getOwner(), \
                                                        self.__aw, \
                                                        contribModifURLGen, \
                                                        materialURLGen,\
                                                        subContribModifyURLGen ) )
            elif type( entry ) == schedule.BreakTimeSchEntry:
                l.append( WMeetingBreakDisplayItem().getHTML(entry, \
                                                      self.__aw ) )
            elif type(entry) is conference.ContribSchEntry:
                owner = entry.getOwner()
                l.append( WMeetingContribDisplayItem().getHTML(entry.getOwner(), \
                                                        self.__aw, \
                                                        contribModifURLGen, \
                                                        materialURLGen,\
                                                        subContribModifyURLGen ) )
        return "".join( l )

    def __getHTMLRow( self, title, body, printIfEmpty=0 ):
        str = """
                    <tr>
                        <td valign="top" align="right">
                            <b><strong>%s:</strong></b>
                        </td>
                        <td>
                            <small>%s</small>
                        </td>
                    </tr>"""%(title, body)
        if not printIfEmpty:
            if body.strip() == "":
                return ""
        return str

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.__conf.getTitle()
        vars["meetingIcon"] = Configuration.Config.getInstance().getSystemIconURL("meetingIcon")
        vars["modifyIcon"] = ""
        if self.__conf.canModify( self.__aw ):
            vars["modifyIcon"] = """<a href="%s"><img src="%s" border="0" alt="Jump to the modification interface"></a>
                                 """%(vars["modifyURL"], Configuration.Config.getInstance().getSystemIconURL("modify"))
        vars["description"] =  self.__getHTMLRow( _("Description"), self.__conf.getDescription() )
        vars["location"] = ""
        location = self.__conf.getLocation()
        if location:
            vars["location"] = self.__getHTMLRow( _("Location"), "%s<br>%s"%(location.getName(), location.getAddress() ) )
        vars["room"] = ""
        room = self.__conf.getRoom()
        if room:
            roomLink = linking.RoomLinker().getHTMLLink( room, location )
            vars["room"] = self.__getHTMLRow( _("Room"), roomLink )
        sdate, edate = self.__conf.getStartDate(), self.__conf.getEndDate()
        fsdate, fedate = sdate.strftime("%d %B %Y"), edate.strftime("%d %B %Y")
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        vars["dateInterval"] = "from %s %s to %s %s"%(fsdate, fstime, \
                                                        fedate, fetime)
        if sdate.strftime("%d%B%Y") == edate.strftime("%d%B%Y"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s-%s"%(fstime, fetime)
            vars["dateInterval"] = "%s (%s)"%( fsdate, timeInterval)
        vars["startDate"] = sdate
        vars["endDate"] = edate
        vars["moreInfo"] = self.__getHTMLRow( _("Additional Info"), self.__conf.getContactInfo() )
        chairs = []
        if self.__conf.getChairmanText() != "":
            chairs.append( self.__conf.getChairmanText() )
        for chair in self.__conf.getChairList():
            chairs.append( "<a href=\"mailto: %s\">%s</a>"%(chair.getEmail(), chair.getFullName() ) )
        vars["chairs"] = self.__getHTMLRow( _("Chairmen"), "; ".join( chairs ) )
        ml = []
        for mat in self.__conf.getAllMaterialList():
            str = wcomponents.WMaterialDisplayItem().getHTML(\
                            self.__aw, mat, vars["materialURL"]( mat ))
            if str == "":
                continue
            ml.append(str)
        vars["material"] =  self.__getHTMLRow(  _("Material"), "<br>".join( ml ) )
        vars["schedule"] = self.__getSchedule( vars["sessionModifyURLGen"], \
                                                vars["contribModifyURLGen"], \
                                                vars["materialURL"],\
                                                vars["subContribModifyURLGen"] )
        return vars



class WMeetingDisplay(object):
    def __init__( self, aw, conference ):
        self._aw = aw
        self._conf = conference

    def getHTML(self, params):
        if self._conf.canAccess( self._aw ):
            return WMeetingFullDisplay().getHTML( self._aw, \
                                                        self._conf, \
                                                        params)
        return WMeetingMinimalDisplay().getHTML( self._aw, \
                                                        self._conf, \
                                                        params )


class WMeetingFullDisplay(WMeetingBaseDisplay):
    pass


class WMeetingMinimalDisplay(WMeetingBaseDisplay):
    pass

#################### Participants #####################################

class WPMConfModifParticipantsNewPending(WPMeetingDisplay,conferences.WPConfModifParticipantsNewPending):

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return conferences.WPConfModifParticipantsNewPending._getBody(self, params)

#################### Evaluation #####################################

class WPMEvaluationBase( WPMeetingDisplay ):
    """[DisplayArea] Base class."""
    pass

class WPMEvaluationDisplay (WPMEvaluationBase, evaluations.WPEvaluationDisplay):
    """[Meeting] Evaluation default display."""

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)
        # An hack to make sure that the background is the same as the header
        self._extraCSS.append("body { background: #424242; } ")

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

    def _getBody(self, params):
        html = """<div class="evaluationForm">%s</div>"""
        return html%evaluations.WPEvaluationDisplay._getBody(self, params)

class WPMEvaluationDisplayModif (WPMEvaluationBase, evaluations.WPEvaluationDisplayModif):
    """[Meeting] The user can modify his already submitted evaluation."""

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationDisplayModif._getBody(self, params)

class WPMEvaluationSubmitted (WPMEvaluationBase, evaluations.WPEvaluationSubmitted):
    """[Meeting] Submitted evaluation."""

    def __init__(self, rh, conf, mode):
        self._mode = mode
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationSubmitted._getBody(self, params)

class WPMEvaluationFull (WPMEvaluationBase, evaluations.WPEvaluationFull):
    """[Meeting] Evaluation is full."""

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationFull._getBody(self, params)

class WPMEvaluationClosed (WPMEvaluationBase, evaluations.WPEvaluationClosed):
    """[Meeting] Evaluation is closed."""

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationClosed._getBody(self, params)

class WPMEvaluationSignIn (WPMEvaluationBase, evaluations.WPEvaluationSignIn):
    """[Meeting] Invite user to login/signin."""

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationSignIn._getBody(self, params)

class WPMEvaluationInactive (WPMEvaluationBase, evaluations.WPEvaluationInactive):
    """[Meeting] Inactive evaluation."""

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationInactive._getBody(self, params)

#################### Alarms #####################################

class WPMConfAddAlarm(WPMConfModifTools, conferences.WPConfAddAlarm):

    def __init__(self, rh, conf):
        WPMConfModifTools.__init__(self, rh, conf)

    def _setActiveTab( self ):
        self._tabAlarms.setActive()

    def _getTabContent(self, params):
        params["toAllParticipants"] =  _("""
        <tr>
            <td>&nbsp;<input type="checkbox" name="toAllParticipants"></td>
            <td> _("Send alarm to all participants of the event.")</td>
        </tr>
        """)
        return conferences.WPConfAddAlarm._getTabContent(self, params)

class WPMTimeTableCustomizePDF(WPMeetingDisplay):

    def __init__(self, rh, conf, view):
        WPMeetingDisplay.__init__(self, rh, conf)
        # We keep track of the view so that we can return to the meeting
        # display page with the same layout when cancelling the pdf export
        self._view = view
        # An hack to make sure that the background is the same as the header
        self._extraCSS.append("body { background: #424242; } ")

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

    def _getBody( self, params ):
        wc = WMTimeTableCustomizePDF( self._conf, self._view )
        return wc.getHTML(params)

class WMTimeTableCustomizePDF(wcomponents.WTemplated):

    def __init__(self, conf, view):
        self._conf = conf
        self._view = view

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        url=urlHandlers.UHConfTimeTablePDF.getURL(self._conf)
        # Add the view as a parameter so we can keep track of it
        # when the pdf export is cancelled.
        url.addParam("view", self._view)
        vars["getPDFURL"]=quoteattr(str(url))
        return vars


######################## Get file package ######################
class WPMDisplayFullMaterialPackage(WPMeetingDisplay, conferences.WPDisplayFullMaterialPackage):

    def __init__(self, rh, conf):
        WPMeetingDisplay.__init__(self, rh, conf)
        # An hack to make sure that the background is the same as the header
        self._extraCSS.append("body { background: #424242; } ")

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

    def _getBody(self, params):
        html = """<div class="evaluationForm">%s</div>"""
        return html%conferences.WPDisplayFullMaterialPackage._getBody(self, params)
