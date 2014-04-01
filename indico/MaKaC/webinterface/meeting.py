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
from indico.util.string import safe_upper

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
from indico.core.config import Config
from xml.sax.saxutils import quoteattr, escape
from MaKaC.webinterface.general import WebFactory
from MaKaC.webinterface.pages.category import WPConferenceCreationMainData
from MaKaC.webinterface.pages.conferences import WPConferenceDisplayBase
from MaKaC.webinterface.materialFactories import ConfMFRegistry, ContribMFRegistry
from MaKaC.webinterface.pages import evaluations
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util.date_time import format_date
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
    def getConfModifListings(rh, conf):
        return WPMConfModifListings(rh, conf)

    @staticmethod
    def getConfClone(rh, conf):
        return WPMConfClone(rh, conf)

    @staticmethod
    def getConfModifSchedule (rh, conf):
        return WPMConfModifSchedule(rh, conf)

    @staticmethod
    def getTimeTableCustomizePDF(rh, conf, view):
        return WPMTimeTableCustomizePDF(rh, conf, view)

    @staticmethod
    def getDisplayFullMaterialPackage(rh, conf):
        return WPMDisplayFullMaterialPackage(rh,conf)

########### Material Display #################################################

    def getMaterialDisplay( rh, material):
        return WPMMaterialDisplay(rh, material)
    getMaterialDisplay = staticmethod(getMaterialDisplay)

############# Subcontribution Display##########################################

    def getSubContributionDisplay(rh, subcontrib):
        return WPMSubContributionDisplay(rh, subcontrib)
    getSubContributionDisplay = staticmethod(getSubContributionDisplay)

############# Contribution Display #############################################

    def getContributionDisplay(rh, contrib, hideFull = 0 ):
        return WPMContributionDisplay(rh,contrib, hideFull)
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

    def getContribAddSC(rh, contrib):
        return WPMContribAddSC(rh,contrib)
    getContribAddSC = staticmethod(getContribAddSC)

########## Session Display###########################################

    def getSessionDisplay(rh,session):
        return WPMSessionDisplay (rh,session)
    getSessionDisplay = staticmethod(getSessionDisplay)

############Session Modificiations###########################################

    def getSessionDataModification(self, session):
        return WPMSessionDataModification (self,session)
    getSessionDataModification = staticmethod(getSessionDataModification)

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
        padding=""" style="padding:0px" """

        body = i18nformat("""
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

        body =  i18nformat("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%">%s</td>
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

        body =  i18nformat("""
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

    def _getBody(self, params):
        wc = WMSessionDisplay(self._getAW(), self._session)
        return wc.getHTML()

class WMSessionDisplay(sessions.WSessionDisplay):
    def getHTML(self):
        if self._session.canAccess( self._aw ):
            c = WMSessionDisplayFull(self._aw,self._session)
            return c.getHTML()
        return ""



class WMSessionDisplayBase(sessions.WSessionDisplayBase):
    pass

class WMSessionDisplayFull(WMSessionDisplayBase):
    pass

#################Contribution Modification##############################


class WPMContributionModification(contributions.WPContributionModification):

    def _getTabContent( self, params ):
        from MaKaC.webinterface.pages.contributions import WContribModifMain
        wc = WContribModifMain( self._contrib, ContribMFRegistry(), eventType = "meeting" )
        return wc.getHTML()

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

        body =  i18nformat("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0" valign="top" width="720px">
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
        vars["confDateInterval"] = i18nformat("""_("from") %s _("to") %s""")%(format_date(self._conf.getStartDate(), format='long'), format_date(self._conf.getEndDate(), format='long'))
        if self._conf.getStartDate().strftime("%d%B%Y") == \
                self._conf.getEndDate().strftime("%d%B%Y"):
            vars["confDateInterval"] = format_date(self._conf.getStartDate(), format='long')
        elif self._conf.getStartDate().month == self._conf.getEndDate().month:
            vars["confDateInterval"] = "%s-%s %s"%(self._conf.getStartDate().day, self._conf.getEndDate().day, format_date(self._conf.getStartDate(), format='MMMM yyyy'))
        #################################
        # Fermi timezone awareness(end) #
        #################################
        vars["body"] = self._body
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
            vars["supportEmail"] = ""
        if self._conf.getSupportInfo().hasEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportInfo().getEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] =  _("""<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email"> %s</a>""")%(mailto,
                                                        Config.getInstance().getSystemIconURL("mail"),
                                                        self._conf.getSupportInfo().getCaption())
        format = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
        vars["bgColorCode"] = format.getFormatOption("titleBgColor")["code"]
        vars["textColorCode"] = format.getFormatOption("titleTextColor")["code"]
        return vars

    def getHTML( self, body, params ):
        self._body = body
        return wcomponents.WTemplated.getHTML( self, params )

class WMMaterialDisplay(material.WMaterialDisplay):
    pass

class WPMMaterialDisplay( WPMMaterialDisplayBase):
    navigationEntry = navigation.NEMeetingMaterialDisplay

    def _getBody( self, params ):
        wc = WMMaterialDisplay( self._getAW(), self._material)
        return wc.getHTML(  )

#################Conference Modification#############################

##Main##
class WPMConfModif(conferences.WPConferenceModification):
    def _getPageContent( self, params ):
        wc = WMConfModifMainData( self._conf, ConfMFRegistry, self._ct, self._rh )
        pars = { "type": params.get("type",""), "conferenceId": self._conf.getId() }
        return wc.getHTML( pars )


class WMConfModifMainData(conferences.WConfModifMainData):
    pass


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
            }
        return wc.getHTML( p )

class WPMConfModifListings (conferences.WPConfModifListings):

    def _getTabContent( self, params ):
        wc = WMConfModifListings( self._conf )
        return wc.getHTML()


class WMConfModifListings (conferences.WConfModifListings):
    pass


class WPMConfClone(conferences.WPConfClone):

    def _getTabContent( self, params ):
        p = conferences.WConferenceClone( self._conf )
        pars = {
            "cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
            "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
            "cloneOptions": i18nformat("""<li><input type="checkbox" name="cloneTimetable" id="cloneTimetable" value="1" checked="checked" />_("Full timetable")</li>
                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneSessions" id="cloneSessions" value="1" />_("Sessions")</li></ul></li>
                     <li><input type="checkbox" name="cloneParticipants" id="cloneParticipants" value="1" checked="checked" />_("Participants")</li>
                     <li><input type="checkbox" name="cloneEvaluation" id="cloneEvaluation" value="1" />_("Evaluation")</li>
               """)
        }
        #let the plugins add their own elements
        self._notify('addCheckBox2CloneConf', pars)
        return p.getHTML( pars )

##TimeTable view##
class WPMConfModifSchedule(conferences.WPConfModifScheduleGraphic):
    pass

######################### Session View #######################

##TabControl####
class WPMSessionDataModification(sessions.WPSessionDataModification):
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
                             "dark": True } )

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
            vars["place"] = safe_upper(location.getName())
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
        vars["endDate"] = format_date(self.__contrib.getEndDate(), format='full')
        vars["endTime"] = self.__contrib.getEndDate().strftime("%H:%M")
        vars["duration"] = (datetime(1900,1,1)+self.__contrib.getDuration()).strftime("%M'")
        if self.__contrib.getDuration()>timedelta(seconds=3600):
            vars["duration"] = (datetime(1900,1,1)+self.__contrib.getDuration()).strftime("%Hh%M'")
        vars["modifyURL"] = self.__modifyURLGen( self.__contrib )
        ml = []
        for mat in self.__contrib.getAllMaterialList():
            s = wcomponents.WMaterialDisplayItem().getHTML(self.__aw, mat, self.__materialsURLGen(mat))
            if not s:
                continue
            ml.append(s)
        if len(ml) == 0:
            vars["materials"] = ""
        else:
            vars["materials"] = "(%s)"%", ".join( ml )

        vars["materialURLGen"] = self.__materialsURLGen
        scl = []
        for sc in self.__contrib.getSubContributionList():
            s = WSubContributionMeetingDisplay(self.__aw, sc).getHTML({"modifyURL":self.__subContribModifyURLGen(sc), "materialURLGen":self.__materialsURLGen} )
            if not s:
                continue
            scl.append(s)
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
        vars["startDate"] = format_date(self.__session.getStartDate(), format='full')
        vars["startTime"] = self.__session.getStartDate().strftime("%H:%M")
        vars["endDate"] = format_date(self.__session.getEndDate(), format='full')
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
        fsdate, fedate = format_date(sdate, format='long'), format_date(edate, format='long')
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        vars["dateInterval"] = i18nformat("""_("from") %s %s _("to") %s %s""")%(fsdate, fstime, \
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
