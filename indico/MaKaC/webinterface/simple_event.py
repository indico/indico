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
from MaKaC.plugins.base import Observable

import urllib
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.linking as linking
import MaKaC.webinterface.pages.category as category
import MaKaC.common.Configuration as Configuration
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.material as material
import MaKaC.webinterface.navigation as navigation
import MaKaC.webinterface.displayMgr as displayMgr
from indico.core.config import Config
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.general import WebFactory
from MaKaC.webinterface.pages.category import WPConferenceCreationMainData
from MaKaC.webinterface.materialFactories import ConfMFRegistry
from MaKaC.webinterface import meeting
from MaKaC.webinterface.pages import evaluations
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util.date_time import format_date
import MaKaC.common.timezoneUtils as timezoneUtils
from pytz import timezone


class WebFactory(WebFactory):
    id = "simple_event"
    iconURL = Configuration.Config.getInstance().getSystemIconURL( "lecture" )
    name = "Lecture"
    description = """select this type if you want to set up a simple event thing without schedule, sessions, contributions, ... """

    def getConferenceDisplayPage( rh, conf, params):
        return WPSimpleEventDisplay( rh, conf )
    getConferenceDisplayPage = staticmethod( getConferenceDisplayPage )

    def getEventCreationPage( rh, targetCateg ):
        return WPSimpleEventCreation( rh, targetCateg )
    getEventCreationPage = staticmethod( getEventCreationPage )

    def getIconURL():
        return WebFactory.iconURL
    getIconURL = staticmethod( getIconURL )

    @staticmethod
    def customiseSideMenu( webPageWithSideMenu ):
        webPageWithSideMenu._programMenuItem.setVisible(False)
        webPageWithSideMenu._timetableMenuItem.setVisible(False)
        webPageWithSideMenu._abstractMenuItem.setVisible(False)
        webPageWithSideMenu._layoutMenuItem.setVisible(False)
        webPageWithSideMenu._contribListMenuItem.setVisible(False)
        webPageWithSideMenu._regFormMenuItem.setVisible(False)
        webPageWithSideMenu._listingsMenuItem.setVisible(False)

    @staticmethod
    def customiseToolsTabCtrl( tabCtrl ):
        tabCtrl.getTabById("clone").enable()
        tabCtrl.getTabById("alarms").enable()
        tabCtrl.getTabById("posters").enable()
        tabCtrl.getTabById("close").enable()
        tabCtrl.getTabById("delete").enable()
        tabCtrl.getTabById("badges").disable()

    def getConfModif(rh, conf):
        return WPSEConfModif(rh, conf)
    getConfModif = staticmethod(getConfModif)

    def getConfModifAC(rh, conf):
        return WPSEConfModifAC(rh, conf)
    getConfModifAC = staticmethod(getConfModifAC)

    def getConfClone(rh, conf):
        return WPSEConfClone(rh, conf)
    getConfClone = staticmethod(getConfClone)

    def getMaterialDisplay( rh, material):
        return WPMMaterialDisplay(rh, material)
    getMaterialDisplay = staticmethod(getMaterialDisplay)

    @staticmethod
    def getDisplayFullMaterialPackage(rh, conf):
        return WPSEDisplayFullMaterialPackage(rh,conf)

#################### Participants #####################################

    def getConfModifParticipantsNewPending(rh, conf):
        return WPSEConfModifParticipantsNewPending(rh, conf)
    getConfModifParticipantsNewPending = staticmethod(getConfModifParticipantsNewPending)

#################### Evaluation #####################################

    def getEvaluationDisplay(rh, conf):
        return WPSEEvaluationDisplay(rh, conf)
    getEvaluationDisplay = staticmethod(getEvaluationDisplay)

    def getEvaluationDisplayModif(rh, conf):
        return WPSEEvaluationDisplayModif(rh, conf)
    getEvaluationDisplayModif = staticmethod(getEvaluationDisplayModif)

    def getEvaluationSubmitted(rh, conf, mode):
        return WPSEEvaluationSubmitted(rh, conf, mode)
    getEvaluationSubmitted = staticmethod(getEvaluationSubmitted)

    def getEvaluationFull(rh, conf):
        return WPSEEvaluationFull(rh, conf)
    getEvaluationFull = staticmethod(getEvaluationFull)

    def getEvaluationClosed(rh, conf):
        return WPSEEvaluationClosed(rh, conf)
    getEvaluationClosed = staticmethod(getEvaluationClosed)

    def getEvaluationSignIn(rh, conf):
        return WPSEEvaluationSignIn(rh, conf)
    getEvaluationSignIn = staticmethod(getEvaluationSignIn)

    def getEvaluationInactive(rh, conf):
        return WPSEEvaluationInactive(rh, conf)
    getEvaluationInactive = staticmethod(getEvaluationInactive)

#################### Alarms #####################################
    def getConfAddAlarm(rh, conf):
        return WPSEConfAddAlarm(rh, conf)
    getConfAddAlarm = staticmethod(getConfAddAlarm)




SimpleEventWebFactory = WebFactory
################ Material Display ###################################
class WPMMaterialDisplayBase( conferences.WPConferenceDefaultDisplayBase):
    def __init__(self, rh, material):
        self._material = material
        conferences.WPConferenceDefaultDisplayBase.__init__( self, rh, self._material.getConference())
        self._navigationTarget = self._material
        self._extraCSS.append(" body { background: #424242; } ")

    def _getNavigationBarHTML(self):
        item = self.navigationEntry
        itemList = []
        while item is not None:
            if itemList == []:
                itemList.insert(0, wcomponents.WTemplated.htmlText(item.getTitle()) )
            else:
                itemList.insert(0, """<a href=%s>%s</a>"""%( quoteattr(str(item.getURL(self._navigationTarget))), wcomponents.WTemplated.htmlText(item.getTitle())  ) )
            item = item.getParent(self._navigationTarget)

        itemList.insert(0, """<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHConferenceDisplay.getURL(self._conf))), self._conf.getTitle() ))
        return " &gt; ".join(itemList)

    def _applyConfDisplayDecoration( self, body ):
        frame = WMConfDisplayFrame( self._getAW(), self._conf )
        frameParams = {\
              "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf), \
                      }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        colspan=""
        imgOpen=""
        padding=""
        padding=""" style="padding:0px" """

        body =  i18nformat("""
                <td class="confBodyBox" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0" valign="top" width="720px">
                        <tr>
                            <td><div class="groupTitle">_("Added Material")</div></td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b>%s</b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </td>""")%(colspan,padding,imgOpen,
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
        tzUtil = timezoneUtils.DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        adjusted_sDate = self._conf.getStartDate().astimezone(timezone(tz))
        adjusted_eDate = self._conf.getEndDate().astimezone(timezone(tz))

        vars["confDateInterval"] = i18nformat("""_("from") %s _("to") %s (%s)""")%(format_date(adjusted_sDate, format='long'), format_date(adjusted_eDate, format='long'), tz)

        if self._conf.getStartDate().strftime("%d%B%Y") == \
                self._conf.getEndDate().strftime("%d%B%Y"):
            vars["confDateInterval"] = format_date(adjusted_sDate, format='long') + " (" + tz + ")"
        elif self._conf.getStartDate().month == self._conf.getEndDate().month:
            vars["confDateInterval"] = "%s-%s %s %s"%(adjusted_sDate.day, adjusted_eDate.day, format_date(adjusted_sDate, format='MMMM yyyy'), tz)
        vars["body"] = self._body
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
            vars["supportEmail"] = ""
        if self._conf.getSupportInfo().hasEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportInfo().getEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] =  i18nformat("""<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email">  _("support")</a>""")%(mailto, Config.getInstance().getSystemIconURL("mail") )
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
    navigationEntry = navigation.NEMaterialDisplay

    def _getBody( self, params ):
        wc = WMMaterialDisplay( self._getAW(), self._material )
        return wc.getHTML()

#################Conference Modification#############################

##Main##
class WPSEConfModif(conferences.WPConferenceModification):
    def _getPageContent( self, params ):
        wc = WSEConfModifMainData( self._conf, ConfMFRegistry, self._ct, self._rh )
        pars = { "type": params.get("type",""), "conferenceId": self._conf.getId() }
        return wc.getHTML( pars )


class WSEConfModifMainData(meeting.WMConfModifMainData):
    pass


#####Access Control # stays the same as conference for now
class WPSEConfModifAC(conferences.WPConfModifAC):
    pass

class WSEConfModifAC(conferences.WConfModifAC):
    pass  #Depends which frames we need inside of AC


#####Tools # Stays the same as conference for now
class WPSEConfModifToolsBase (conferences.WPConfModifToolsBase):

    def __init__(self, rh, conf):
        conferences.WPConfModifToolsBase.__init__(self, rh, conf)

class WPSEConfClone(WPSEConfModifToolsBase, Observable):

    def _setActiveTab( self ):
        self._tabCloneEvent.setActive()

    def _getTabContent( self, params ):
        p = conferences.WConferenceClone( self._conf )
        pars = {
            "cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
            "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
            "cloneOptions": i18nformat("""
    <li><input type="checkbox" name="cloneParticipants" id="cloneParticipants" value="1" >
        _("Participants")</li>
    <li><input type="checkbox" name="cloneEvaluation" id="cloneEvaluation" value="1" >
        _("Evaluation")</li>
           """)
        }
        #let the plugins add their own elements
        self._notify('addCheckBox2CloneConf', pars)
        return p.getHTML( pars )


#################### Event Creation #####################################
class WPSimpleEventCreation( WPConferenceCreationMainData):

    def _getWComponent( self ):
        return WSimpleEventCreation( self._target, rh = self._rh )


class WSimpleEventCreation(category.WConferenceCreation):
    def __init__( self, targetCateg, type="simple_event", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh

    def getVars( self ):
        vars = category.WConferenceCreation.getVars( self )
        vars["event_type"] = WebFactory.getId()
        return vars

##################### Event Display ###################################

class WPSimpleEventDisplay( conferences.WPConferenceDisplayBase ):

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WMenuSimpleEventHeader( self._getAW(),self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(),\
                             "currentView": "static",\
                             "type": WebFactory.getId(),\
                             "dark": True } )

    def _getBody( self, params ):
        wc = WSimpleEventDisplay( self._getAW(), self._conf )
        pars = { \
    "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
    "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
    "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
    "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
    "materialURLGen": urlHandlers.UHMaterialDisplay.getURL }
        return wc.getHTML( pars )


class WSimpleEventDisplay:

    def __init__( self, aw, conference ):
        self._aw = aw
        self._conf = conference

    def getHTML( self, params ):
        if self._conf.canAccess( self._aw ):
            return WSimpleEventFullDisplay( self._aw, self._conf ).getHTML( params )
        else:
            return WSimpleEventMinDisplay( self._aw, self._conf ).getHTML( params )


class WSimpleEventBaseDisplay(wcomponents.WTemplated):

    def __init__( self, aw, conference ):
        self._aw = aw
        self._conf = conference

    def __getHTMLRow( self, title, body, allowEmptyBody=1 ):
        str = """
                <tr>
                    <td align="right" valign="top" nowrap>
                        <b><strong>%s:</strong></b>
                    </td>
                    <td>
                        <font size="-1" face="arial" color="#333333">%s</font>
                    </td>
                </tr>"""%(title, body)
        if not allowEmptyBody:
            if body.strip() == "":
                return ""
        return str

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tzUtil = timezoneUtils.DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        sdate = self._conf.getStartDate().astimezone(timezone(tz))
        edate = self._conf.getEndDate().astimezone(timezone(tz))
        fsdate, fedate = format_date(sdate, format='full'), format_date(edate, format='full')
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        if sdate.strftime("%Y%B%d") == edate.strftime("%Y%B%d"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s - %s"%(fstime, fetime)
            vars["dateInterval"] = "<b>%s (%s) (%s)</b>"%( fsdate, timeInterval, tz )
        else:
            vars["dateInterval"] = "from <b>%s (%s)</b> to <b>%s (%s) (%s)</b>"%(\
                                fsdate, fstime, fedate, fetime, tz)
        vars["title"] = self._conf.getTitle()
        vars["description"] =  self.__getHTMLRow(  _("Description"), self._conf.getDescription(), 0 )
        vars["location"] = ""
        location = self._conf.getLocation()
        if location:
            vars["location"] = self.__getHTMLRow(  _("Location"), "%s<br><small>%s</small>"%(location.getName(), location.getAddress()) )
        vars["room"] = ""
        room = self._conf.getRoom()
        if room:
            roomLink = linking.RoomLinker().getHTMLLink( room, location )
            vars["room"] = self.__getHTMLRow( _("Room"), roomLink )
        vars["moreInfo"] = self.__getHTMLRow(  _("Additional Info"), self._conf.getContactInfo(), 0 )
        ml = []
        for mat in self._conf.getAllMaterialList():
            ml.append( wcomponents.WMaterialDisplayItem().getHTML(\
                                                self._aw, mat, \
                                                vars["materialURLGen"](mat) ) )
        vars["material"] =  self.__getHTMLRow( _("Material"), "<br>".join(ml), 0)
        al = []
        if self._conf.getChairmanText() != "":
            al.append( self._conf.getChairmanText() )
        for organiser in self._conf.getChairList():
            al.append( """<a href="mailto:%s">%s</a>"""%(organiser.getEmail(),\
                                                     organiser.getFullName() ) )
        vars["contact"] = self.__getHTMLRow("Contact", "<br>".join( al ), 0 )
        vars["modifyItem"] = ""
        if self._conf.canModify( self._aw ):
            vars["modifyItem"] = """<a href="%s"><img src="%s" border="0" alt="Jump to the modification interface"></a> """%(vars["modifyURL"], Configuration.Config.getInstance().getSystemIconURL("popupMenu") )
        return vars


class WSimpleEventFullDisplay(WSimpleEventBaseDisplay):
    pass


class WSimpleEventMinDisplay(WSimpleEventBaseDisplay):
    pass

#################### Evaluation #####################################

class WPSEEvaluationBase( WPSimpleEventDisplay ):
    """[DisplayArea] Base class."""

class WPSEEvaluationDisplay (WPSEEvaluationBase, evaluations.WPEvaluationDisplay):
    """[Meeting] Evaluation default display."""

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)
        # An hack to make sure that the background is the same as the header
        self._extraCSS.append("body { background: #424242; } ")

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

    def _getBody(self, params):
        html = """<div class="evaluationForm">%s</div>"""
        return html%evaluations.WPEvaluationDisplay._getBody(self, params)

class WPSEEvaluationDisplayModif (WPSEEvaluationBase, evaluations.WPEvaluationDisplayModif):
    """[Meeting] The user can modify his already submitted evaluation."""

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationDisplayModif._getBody(self, params)

class WPSEEvaluationSubmitted (WPSEEvaluationBase, evaluations.WPEvaluationSubmitted):
    """[Meeting] Submitted evaluation."""

    def __init__(self, rh, conf, mode):
        self._mode = mode
        WPSimpleEventDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationSubmitted._getBody(self, params)

class WPSEEvaluationFull (WPSEEvaluationBase, evaluations.WPEvaluationFull):
    """[Meeting] Evaluation is full."""

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationFull._getBody(self, params)

class WPSEEvaluationClosed (WPSEEvaluationBase, evaluations.WPEvaluationClosed):
    """[Meeting] Evaluation is closed."""

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationClosed._getBody(self, params)

class WPSEEvaluationSignIn (WPSEEvaluationBase, evaluations.WPEvaluationSignIn):
    """[Meeting] Invite user to login/signin."""

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationSignIn._getBody(self, params)

class WPSEEvaluationInactive (WPSEEvaluationBase, evaluations.WPEvaluationInactive):
    """[Meeting] Inactive evaluation."""

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)

    def _getBody(self, params):
        return evaluations.WPEvaluationInactive._getBody(self, params)


######################## Get file package ######################
class WPSEDisplayFullMaterialPackage(WPSimpleEventDisplay, conferences.WPDisplayFullMaterialPackage):

    def __init__(self, rh, conf):
        WPSimpleEventDisplay.__init__(self, rh, conf)
        # An hack to make sure that the background is the same as the header
        self._extraCSS.append("body { background: #424242; } ")

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"dark":True}
        return wc.getHTML(p)

    def _getBody(self, params):
        html = """<div class="evaluationForm">%s</div>"""
        return html%conferences.WPDisplayFullMaterialPackage._getBody(self, params)
