# -*- coding: utf-8 -*-
##
## $Id: conferences.py,v 1.414 2009/06/26 13:09:59 eragners Exp $
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
import os
import string
import random
import simplejson
import copy

from datetime import timedelta,datetime
from xml.sax.saxutils import quoteattr, escape


from MaKaC import user
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.displayMgr as displayMgr
import MaKaC.webinterface.timetable as timetable
import MaKaC.webinterface.linking as linking
import MaKaC.webinterface.navigation as navigation
import MaKaC.schedule as schedule
import MaKaC.conference as conference
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.common.filters as filters
from MaKaC.common.utils import isStringHTML, formatDateTime
import MaKaC.review as review
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.common.tools import strip_ml_tags, escape_html
from MaKaC.webinterface.materialFactories import ConfMFRegistry,PaperFactory,SlidesFactory,PosterFactory
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
from MaKaC.common import Config
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.common.output import outputGenerator
from MaKaC.webinterface.general import strfFileSize
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC import booking
from MaKaC.PDFinterface.base import PDFSizes
from pytz import timezone
import MaKaC.webinterface.common.timezones as convertTime
from MaKaC.common.timezoneUtils import nowutc, DisplayTZ
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface.pages import main
from MaKaC.webinterface.pages import base
import MaKaC.common.info as info
from MaKaC.common.cache import EventCache
from MaKaC.i18n import _
from MaKaC.plugins import importPlugin
from MaKaC.modules.base import ModulesHolder
import MaKaC.webcast as webcast
from MaKaC.common.PickleJar import DictPickler

def stringToDate( str ):
    #Don't delete this dictionary inside comment. Its purpose is to add the dictionary in the language dictionary during the extraction!
    #months = { _("January"):1, _("February"):2, _("March"):3, _("April"):4, _("May"):5, _("June"):6, _("July"):7, _("August"):8, _("September"):9, _("October"):10, _("November"):11, _("December"):12 }
    months = { "January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12 }
    [ day, month, year ] = str.split("-")
    return datetime(int(year),months[month],int(day))

class WPConferenceBase( base.WPDecorated ):

    def __init__( self, rh, conference ):
        WPDecorated.__init__( self, rh )
        self._navigationTarget = self._conf = conference
        tz = self._tz = DisplayTZ(rh._aw,self._conf).getDisplayTZ()
        sDate = self.sDate = self._conf.getAdjustedScreenStartDate(tz)
        eDate = self.eDate = self._conf.getAdjustedScreenEndDate(tz)
        dates=" (%s)"%sDate.strftime("%d %B %Y")
        if sDate.strftime("%d%B%Y") != eDate.strftime("%d%B%Y"):
            if sDate.strftime("%B%Y") == eDate.strftime("%B%Y"):
                dates=" (%s-%s)"%(sDate.strftime("%d"), eDate.strftime("%d %B %Y"))
            else:
                dates=" (%s - %s)"%(sDate.strftime("%d %B %Y"), eDate.strftime("%d %B %Y"))
        self._setTitle( "%s %s"%(strip_ml_tags(self._conf.getTitle()), dates ))
        self._parentCateg = None
        categId = rh._getSession().getVar("currentCategoryId")
        if categId != None:
            self._parentCateg = self._conf.getOwnerById(categId)

    def _getFooter( self ):
        """
        """
        wc = wcomponents.WFooter()

        p = {"modificationDate":self._conf.getModificationDate().strftime("%d %B %Y %H:%M"),
             "subArea": self._getSiteArea()}
        return wc.getHTML(p)

    def getLoginURL( self ):
        wf = self._rh.getWebFactory()
        if wf:
            return WPDecorated.getLoginURL(self)

        return urlHandlers.UHConfSignIn.getURL(self._conf,"%s"%self._rh.getCurrentURL())

    def getLogoutURL( self ):
        return urlHandlers.UHSignOut.getURL(str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))

class WPConferenceDisplayBase( WPConferenceBase ):

    def getJSFiles(self):
        return WPConferenceBase.getJSFiles(self) + \
               self._includeJSPackage('MaterialEditor')

class WPConferenceDefaultDisplayBase( WPConferenceBase ):
    navigationEntry = None

    def _getFooter( self ):
        """
        """
        wc = wcomponents.WFooter()
        p = {"modificationDate":self._conf.getModificationDate().strftime("%d %B %Y %H:%M"),
                "subArea": self._getSiteArea()}
        if Config.getInstance().getShortEventURL():
            id=self._conf.getUrlTag().strip()
            if not id:
                id = self._conf.getId()
            p["shortURL"] =  Config.getInstance().getShortEventURL() + id
        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WConferenceHeader( self._getAW(), self._getNavigationDrawer(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "loginAsURL": self.getLoginAsURL(), \
                             "confId": self._conf.getId(), \
                             "dark": True} )

    def _defineSectionMenu( self ):
        awUser = self._getAW().getUser()
        self._sectionMenu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        self._overviewOpt = self._sectionMenu.getLinkByName("overview")
        self._programOpt = self._sectionMenu.getLinkByName("programme")
        link = self._programOpt
        self._cfaOpt = self._sectionMenu.getLinkByName("CFA")
        self._cfaNewSubmissionOpt = self._sectionMenu.getLinkByName("SubmitAbstract")
        self._cfaViewSubmissionsOpt = self._sectionMenu.getLinkByName("ViewAbstracts")
        self._abstractsBookOpt = self._sectionMenu.getLinkByName("abstractsBook")
        self._cfaOpt.setVisible(self._conf.getAbstractMgr().isActive())
        if not self._conf.hasEnabledSection("cfa"):
            self._cfaOpt.setVisible(False)
            self._abstractsBookOpt.setVisible(False)
        else:
            self._abstractsBookOpt.setVisible(True)
        self._trackMgtOpt = self._sectionMenu.getLinkByName("manageTrack")

        #registration form
        self._regFormOpt = self._sectionMenu.getLinkByName("registrationForm")
        self._viewRegFormOpt = self._sectionMenu.getLinkByName("ViewMyRegistration")
        self._newRegFormOpt = self._sectionMenu.getLinkByName("NewRegistration")
        self._regFormOpt.setVisible(self._conf.getRegistrationForm().isActivated())
        if awUser != None:
            self._viewRegFormOpt.setVisible(awUser.isRegisteredInConf(self._conf))
            self._newRegFormOpt.setVisible(not awUser.isRegisteredInConf(self._conf))
        else:
            self._viewRegFormOpt.setVisible(False)
            self._newRegFormOpt.setVisible(True)
        self._registrantsListOpt = self._sectionMenu.getLinkByName("registrants")
        if not self._conf.hasEnabledSection("regForm"):
            self._regFormOpt.setVisible(False)
            self._registrantsListOpt.setVisible(False)
        else:
            self._registrantsListOpt.setVisible(True)

        #evaluation
        evaluation = self._conf.getEvaluation()
        self._evaluationOpt = self._sectionMenu.getLinkByName("evaluation")
        self._newEvaluationOpt = self._sectionMenu.getLinkByName("newEvaluation")
        self._viewEvaluationOpt = self._sectionMenu.getLinkByName("viewMyEvaluation")
        self._evaluationOpt.setVisible(self._conf.hasEnabledSection("evaluation") and evaluation.isVisible() and evaluation.getNbOfQuestions()>0)
        if awUser!=None and awUser.hasSubmittedEvaluation(evaluation):
            self._newEvaluationOpt.setVisible(not awUser.hasSubmittedEvaluation(evaluation))
            self._viewEvaluationOpt.setVisible(awUser.hasSubmittedEvaluation(evaluation))
        else:
            self._newEvaluationOpt.setVisible(True)
            self._viewEvaluationOpt.setVisible(False)



        self._sectionMenu.setCurrentItem(None)

        self._timetableOpt = self._sectionMenu.getLinkByName("timetable")
        self._contribListOpt = self._sectionMenu.getLinkByName("contributionList")
        self._authorIndexOpt = self._sectionMenu.getLinkByName("authorIndex")
        self._speakerIndexOpt = self._sectionMenu.getLinkByName("speakerIndex")
        self._myStuffOpt=self._sectionMenu.getLinkByName("mystuff")
        self._myStuffOpt.setVisible(awUser is not None)
        self._mySessionsOpt=self._sectionMenu.getLinkByName("mysessions")
        from sets import Set
        ls = Set(self._conf.getCoordinatedSessions(awUser))
        ls = list(ls | Set(self._conf.getManagedSession(awUser)))
        self._mySessionsOpt.setVisible(len(ls)>0)
        if len(ls)==1:
            self._mySessionsOpt.setCaption( _("My session"))
            self._mySessionsOpt.setURL(urlHandlers.UHSessionModification.getURL(ls[0]))
        self._myTracksOpt=self._sectionMenu.getLinkByName("mytracks")
        lt=self._conf.getCoordinatedTracks(awUser)
        self._myTracksOpt.setVisible(len(lt)>0)
        if len(lt)==1:
            self._myTracksOpt.setCaption( _("My track"))
            self._myTracksOpt.setURL(urlHandlers.UHTrackModifAbstracts.getURL(lt[0]))
        if not self._conf.hasEnabledSection("cfa"):
            self._myTracksOpt.setVisible(False)
        self._myContribsOpt=self._sectionMenu.getLinkByName("mycontribs")
        lc=self._conf.getContribsForSubmitter(awUser)
        self._myContribsOpt.setVisible(len(lc)>0)
        self._trackMgtOpt.setVisible(False)
        tracks = self._conf.getCoordinatedTracks( awUser )
        if tracks:
            if len(tracks)>1:
                self._trackMgtOpt.setCaption( _("Manage my tracks"))
                url = urlHandlers.UHConferenceProgram.getURL( self._conf )
            else:
                url = urlHandlers.UHTrackModifAbstracts.getURL( tracks[0] )
            self._trackMgtOpt.setURL(str(url))
            self._trackMgtOpt.setVisible(True)
            if not self._conf.hasEnabledSection("cfa"):
                self._trackMgtOpt.setVisible(False)


        self._abstractReviewingMgtOpt=self._sectionMenu.getLinkByName("manageabstractreviewing")
        self._abstractReviewingMgtOpt.setVisible(False)

        self._paperReviewingMgtOpt=self._sectionMenu.getLinkByName("managepaperreviewing")
        self._paperReviewingMgtOpt.setVisible(False)

        self._judgeListOpt=self._sectionMenu.getLinkByName("judgelist")
        self._judgeListOpt.setVisible(False)
        self._assignContribOpt=self._sectionMenu.getLinkByName("assigncontributions")
        self._assignContribOpt.setVisible(False)

        if awUser != None and self._conf.hasEnabledSection('paperReviewing'):

            conferenceRoles = awUser.getLinkedTo()["conference"]

            if "abstractManager" in conferenceRoles:
                if self._conf in awUser.getLinkedTo()["conference"]["abstractManager"]:
                    self._abstractReviewingMgtOpt.setVisible(True)

            if "paperReviewManager" in conferenceRoles:
                if self._conf in awUser.getLinkedTo()["conference"]["paperReviewManager"]:
                    self._paperReviewingMgtOpt.setVisible(True)

            if "referee" in conferenceRoles and "editor" in conferenceRoles and "reviewer" in conferenceRoles:
                show = self._conf in awUser.getLinkedTo()["conference"]["referee"] or \
                       self._conf in awUser.getLinkedTo()["conference"]["editor"] or \
                       self._conf in awUser.getLinkedTo()["conference"]["reviewer"]
                if show:
                    self._judgeListOpt.setVisible(True)

                if self._conf in awUser.getLinkedTo()["conference"]["referee"]:
                    self._assignContribOpt.setVisible(True)
        #collaboration related
        self._collaborationOpt = self._sectionMenu.getLinkByName("collaboration")
        self._collaborationOpt.setVisible(False)
        csbm = self._conf.getCSBookingManager()
        if csbm is not None and csbm.hasBookings() and csbm.isCSAllowed():
            self._collaborationOpt.setVisible(True)

    def _defineToolBar(self):
        pass

    def _display( self, params ):
        self._defineSectionMenu()
        self._toolBar=wcomponents.WebToolBar()
        self._defineToolBar()
        return WPConferenceBase._display(self,params)

    def _getNavigationBarHTML(self):
        item=None
        if self.navigationEntry:
            item = self.navigationEntry()
        itemList = []
        while item is not None:
            if itemList == []:
                itemList.insert(0, wcomponents.WTemplated.htmlText(item.getTitle()) )
            else:
                itemList.insert(0, """<a href=%s>%s</a>"""%( quoteattr(str(item.getURL(self._navigationTarget))), wcomponents.WTemplated.htmlText(item.getTitle()) ) )
            item = item.getParent(self._navigationTarget)
        itemList.insert(0, _("""<a href=%s> _("Home")</a>""")%quoteattr(str(urlHandlers.UHConferenceDisplay.getURL(self._conf))) )
        return " &gt; ".join(itemList)

    def _getToolBarHTML(self):
        drawer=wcomponents.WConfTBDrawer(self._toolBar)
        return drawer.getHTML()

    def _applyConfDisplayDecoration( self, body ):
        drawer = wcomponents.WConfTickerTapeDrawer(self._conf, self._tz)
        frame = WConfDisplayFrame( self._getAW(), self._conf )
        urlClose = urlHandlers.UHConferenceDisplayMenuClose.getURL(self._conf)
        urlClose.addParam("currentURL",self._rh.getCurrentURL())
        urlOpen = urlHandlers.UHConferenceDisplayMenuOpen.getURL(self._conf)
        urlOpen.addParam("currentURL",self._rh.getCurrentURL())
        menuStatus = self._rh._getSession().getVar("menuStatus") or "open"

        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()

        onAirURL = wm.isOnAir(self._conf)
        if onAirURL:
            webcastURL = onAirURL
        else:
            webcastURL = wm.getWebcastServiceURL()
        forthcomingWebcast = not onAirURL and wm.getForthcomingWebcast(self._conf)

        frameParams = {\
            "confModifURL": urlHandlers.UHConferenceModification.getURL(self._conf), \
            "logoURL": urlHandlers.UHConferenceLogo.getURL( self._conf), \
            "currentURL":self._rh.getCurrentURL(), \
            "closeMenuURL":  urlClose, \
            "menuStatus": menuStatus, \
            "nowHappening": drawer.getNowHappeningHTML(), \
            "simpleTextAnnouncement": drawer.getSimpleText(), \
            "onAirURL": onAirURL,
            "webcastURL": webcastURL,
            "forthcomingWebcast": forthcomingWebcast }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        colspan=""
        imgOpen=""
        padding=""
        if  menuStatus != "open":
            urlOpen = urlHandlers.UHConferenceDisplayMenuOpen.getURL(self._conf)
            urlOpen.addParam("currentURL",self._rh.getCurrentURL())
            colspan = """ colspan="2" """
            imgOpen = """<table valign="top" align="left" border="0" cellspacing="0" cellpadding="0" style="padding-right:10px;">
                           <tr>
                                <td align="left" valign="top">
                                    <a href=%s><img alt="Show menu" src="%s" class="imglink" style="padding:0px; border:0px"></a>
                                </td>
                           </tr>
                      </table>"""%(quoteattr(str(urlOpen)),Config.getInstance().getSystemIconURL("openMenuIcon"))
            padding=""" style="padding:0px" """

        body = """
            <div class="confBodyBox clearfix" %s %s>

                                    <div>
                                        <div>%s</div>
                                        <div class="breadcrumps">%s</div>
                                        <div style="float:right;">%s</div>
                                    </div>
                <!--Main body-->
                                    <div class="mainContent">
                                        <div class="col2">
                                        %s
                                        </div>
                                  </div>
            </div>"""%(colspan,padding,imgOpen,
                    self._getNavigationBarHTML(),
                    self._getToolBarHTML().strip(),
                    body)
        return frame.getHTML( self._sectionMenu, body, frameParams)

    def _getHeadContent( self ):
        #This is used for fetching the default css file for the conference pages
        #And also the modificated uploaded css

        path = baseurl = self._getBaseURL()
        printCSS = """
        <link rel="stylesheet" type="text/css" href="%s/css/Conf_Basic.css" >
            """ % path
        confCSS = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager().getCSS()
        if confCSS:
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s">"""%(confCSS.getURL())
        return printCSS

    def _applyDecoration( self, body ):
        body = self._applyConfDisplayDecoration( body )
        return WPConferenceBase._applyDecoration( self, body )

class WConfDisplayFrame(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def getHTML( self, menu, body, params ):
        self._body = body
        self._menu = menu
        return wcomponents.WTemplated.getHTML( self, params )

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["logo"] = ""
        if self._conf.getLogo():
            vars["logo"] = "<img src=\"%s\" alt=\"%s\" border=\"0\" class=\"confLogo\" >"%(vars["logoURL"], escape_html(self._conf.getTitle(), escape_quotes = True))
        vars["confTitle"] = self._conf.getTitle()
        vars["displayURL"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        vars["imgConferenceRoom"] = Config.getInstance().getSystemIconURL( "conferenceRoom" )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        adjusted_sDate = self._conf.getAdjustedScreenStartDate(tz)
        adjusted_eDate = self._conf.getAdjustedScreenEndDate(tz)
        vars["confDateInterval"] = "from %s to %s (%s)"%(adjusted_sDate.strftime("%d %B %Y"), adjusted_eDate.strftime("%d %B %Y"), tz)
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
            vars["confDateInterval"] = adjusted_sDate.strftime("%d %B %Y")
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
            vars["confDateInterval"] = "%s-%s %s"%(adjusted_sDate.day, adjusted_eDate.day, adjusted_sDate.strftime("%B %Y"))
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
        vars["body"] = self._body
        vars["supportEmail"] = ""
        if self._conf.hasSupportEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] = """<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email"> %s</a>"""%(mailto,
                                                Config.getInstance().getSystemIconURL("smallEmail"),
                                                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getSupportEmailCaption())
        p={"closeMenuURL": vars["closeMenuURL"], \
            "menuStatus": vars["menuStatus"], \
            "supportEmail": vars["supportEmail"] \
            }
        vars["menu"] = ConfDisplayMenu( self._menu ).getHTML(p)

        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        format = dm.getFormat()
        vars["bgColorCode"] = format.getFormatOption("titleBgColor")["code"]
        vars["textColorCode"] = format.getFormatOption("titleTextColor")["code"]

        if (Config.getInstance().getIndicoSearchServer() != '') and dm.getSearchEnabled():
            vars["searchBox"] = wcomponents.WMiniSearchBox(self._conf.getId()).getHTML()
        else:
            vars["searchBox"] = ""
        return vars

class ConfDisplayMenu:

    def __init__(self, menu):
        self._menu = menu

    def getHTML(self, params):
        html = []
        if params["menuStatus"] == "open" and self._menu:
            html = ["""<!--Left menu-->
                            <div class="conf_leftMenu">
                                        <ul id="outer" class="clearfix">"""]
            html.append("""
                                <li class="menuConfTopCell">
                                    <a href=%s><img alt="Hide menu" src="%s" class="imglink"></a>
                                </li>
                          """%(quoteattr(str(params["closeMenuURL"])),Config.getInstance().getSystemIconURL("closeMenuIcon")))
            for link in self._menu.getEnabledLinkList():
                if link.isVisible():
                    html.append(self._getLinkHTML(link))
            html.append("""<li class="menuConfBottomCell">&nbsp;</li>""")
            html.append("""     </ul>
                                <div class="confSupportEmailBox">%s</div>
                        </div>"""%params["supportEmail"])
        return "".join(html)

    def _getLinkHTML(self, link, indent=""):
        if not link.isVisible():
            return ""

        if link.getType() == "spacer":
            html = """<tr><td><br></td></tr>\n"""
            try:
                index = link.getParent().getLinkList().index(link)-1
                type = link.getParent().getLinkList()[index].getType()
                if (type == "system" or type == "extern") and index!= -1:
                    html = """<li class="menuConfMiddleCell"><br><li>\n"""
            except Exception:
                pass

        else:
            target = ""
            sublinkList=[]
            for sublink in link.getEnabledLinkList():
                if sublink.isVisible():
                    sublinkList.append(sublink)
            if isinstance(link,displayMgr.ExternLink):
                target=""" target="%s" """%link.getDisplayTarget()
            #Commented because 'menuicon' variable is not used
            #if sublinkList:
            #    menuicon=Config.getInstance().getSystemIconURL("arrowBottomMenuConf")
            #else:
            #    menuicon=Config.getInstance().getSystemIconURL("arrowRightMenuConf")
            if self._menu.isCurrentItem(link):
                html = ["""<li id="menuLink_%s" class="menuConfSelected" nowrap><a href="%s"%s>%s</a>\n"""%
                            (link.getName(), link.getURL(), target, link.getCaption())]
            else:
                html = ["""<li id="menuLink_%s" class="menuConfTitle" nowrap><a class="confSection" href="%s"%s>%s</a>\n"""%
                            (link.getName(), link.getURL(), target, link.getCaption())]

            if len(sublinkList) > 0:
                html += """<ul class="inner">"""

            for sublink in sublinkList:
                target = ""
                if isinstance(link, displayMgr.ExternLink):
                    target=""" target="%s" """%link.getDisplayTarget()
                if self._menu.isCurrentItem(sublink):
                    html.append("""<li id="menuLink_%s" class="subMenuConfSelected" nowrap><a href="%s"%s>\
                            %s</a></li>\n"""\
                            %(sublink.getName(), sublink.getURL(), target, sublink.getCaption()))
                else:
                    html.append( """<li id="menuLink_%s" class="menuConfMiddleCell" nowrap><a class="confSubSection" href="%s"%s>\
                            %s</a></li>"""%(sublink.getName(), sublink.getURL(), target,\
                             sublink.getCaption()) )

            if len(sublinkList) > 0:
                html += "</ul>"
            html += "</li>"

        return "".join(html)

class WPConfSignIn( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, login="", msg = ""):
        self._login = login
        self._msg = msg
        WPConferenceBase.__init__( self, rh, conf)

    def _getBody( self, params ):
        wc = wcomponents.WSignIn()
        p = { \
    "postURL": urlHandlers.UHConfSignIn.getURL( self._conf ), \
    "returnURL": params["returnURL"], \
    "createAccountURL": urlHandlers.UHConfUserCreation.getURL( self._conf ), \
    "forgotPassordURL": urlHandlers.UHConfSendLogin.getURL( self._conf ), \
    "login": self._login, \
    "msg": self._msg }
        return wc.getHTML( p )

class WPConfAccountAlreadyActivated( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, av):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )
        self._av = av

    def _getBody( self, params ):
        wc = wcomponents.WAccountAlreadyActivated( self._av)
        params["mailLoginURL"] = urlHandlers.UHConfSendLogin.getURL( self._conf, self._av)
        return wc.getHTML( params )

class WPConfAccountActivated( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, av, returnURL=""):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )
        self._av = av
        self._returnURL=returnURL

    def _getBody( self, params ):
        wc = wcomponents.WAccountActivated( self._av)
        params["mailLoginURL"] = urlHandlers.UHConfSendLogin.getURL(self._conf, self._av)
        params["loginURL"] = urlHandlers.UHConfSignIn.getURL(self._conf)
        if self._returnURL.strip()!="":
            params["loginURL"] = self._returnURL
        return wc.getHTML( params )

class WPConfAccountDisabled( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, av):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )
        self._av = av

    def _getBody( self, params ):
        wc = wcomponents.WAccountDisabled( self._av )
        #params["mailLoginURL"] = urlHandlers.UHSendLogin.getURL(self._av)

        return wc.getHTML( params )

class WPConfUnactivatedAccount( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, av):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )
        self._av = av

    def _getBody( self, params ):
        wc = wcomponents.WUnactivatedAccount( self._av )
        params["mailActivationURL"] = urlHandlers.UHConfSendActivation.getURL( self._conf, self._av)

        return wc.getHTML( params )


class WPConfUserCreation( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, params):
        self._params = params
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)

    def _getBody(self, params ):
        pars = self._params
        p = wcomponents.WUserRegistration()
        postURL = urlHandlers.UHConfUserCreation.getURL( self._conf )
        postURL.addParam("returnURL", self._params.get("returnURL",""))
        pars["postURL"] =  postURL
        if pars["msg"] != "":
            pars["msg"] = "<table bgcolor=\"gray\"><tr><td bgcolor=\"white\">\n<font size=\"+1\" color=\"red\"><b>%s</b></font>\n</td></tr></table>"%pars["msg"]
        return p.getHTML( pars )


class WPConfUserCreated( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, av):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )
        self._av = av

    def _getBody(self, params ):
        p = wcomponents.WUserCreated(self._av)
        pars = {"signInURL" : urlHandlers.UHConfSignIn.getURL( self._conf )}
        return p.getHTML( pars )


class WPConfUserExistWithIdentity( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, av):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._av = av

    def _getBody(self, params ):
        p = wcomponents.WUserSendIdentity(self._av)
        pars = {"postURL" : urlHandlers.UHConfSendLogin.getURL(self._conf, self._av)}
        return p.getHTML( pars )


class WConfDetailsBase( wcomponents.WTemplated ):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def _getChairsHTML( self ):
        chairList = []
        l = []
        for chair in self._conf.getChairList():
            if chair.getEmail():
                mailToURL = """%s"""%urlHandlers.UHConferenceEmail.getURL(chair)
                l.append( """<a href=%s>%s</a>"""%(quoteattr(mailToURL),self.htmlText(chair.getFullName())))
            else:
                l.append(self.htmlText(chair.getFullName()))
        res = ""
        if len(l) > 0:
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Chairs"):</b></td>
        <td>%s</td>
    </tr>
                """)%"<br>".join(l)
        return res

    def _getMaterialHTML( self ):
        l = []
        for mat in self._conf.getAllMaterialList():
            if mat.getTitle() != _("Internal Page Files"):
                temp = wcomponents.WMaterialDisplayItem()
                url = urlHandlers.UHMaterialDisplay.getURL( mat )
                l.append( temp.getHTML( self._aw, mat, url ) )
        res = ""
        if l:
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Material"):</b></td>
        <td align="left" width="100%%">%s</td>
    </tr>""")%"<br>".join( l )
        return res

    def _getMoreInfoHTML( self ):
        res = ""
        if isStringHTML(self._conf.getContactInfo()):
            text = self._conf.getContactInfo()
        else:
            text = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._conf.getContactInfo()
        if self._conf.getContactInfo() != "":
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Additional info"):</b>
        </td>
        <td>%s</td>
    </tr>""")%text
        return res

    def _getActionsHTML( self, showActions = False):
        html=[]
        if showActions:
            html=[ _("""
                <table style="padding-top:40px; padding-left:20px">
                <tr>
                    <td nowrap>
                        <b> _("Conference sections"):</b>
                        <ul>
                """)]
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            for link in menu.getLinkList():
                if link.isVisible() and link.isEnabled():
                    if not isinstance(link, displayMgr.Spacer):
                        html.append(""" <li><a href="%s">%s</a></li>
                                """%( link.getURL(), link.getCaption() ) )
                    else:
                        html.append("%s"%link)
            html.append("""
                        </ul>
                    </td>
                </tr>
                </table>
                """)
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        if isStringHTML(self._conf.getDescription()):
            vars["description"] = self._conf.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._conf.getDescription()
        sdate, edate = self._conf.getAdjustedScreenStartDate(tz), self._conf.getAdjustedScreenEndDate(tz)
        fsdate, fedate = sdate.strftime("%d %B %Y"), edate.strftime("%d %B %Y")
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")

        vars["dateInterval"] = "from %s %s to %s %s "%(fsdate, fstime, \
                                                        fedate, fetime)
        if sdate.strftime("%d%B%Y") == edate.strftime("%d%B%Y"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s-%s"%(fstime, fetime)
            vars["dateInterval"] = "%s (%s)"%( fsdate, timeInterval)
        vars["location"] = ""
        location = self._conf.getLocation()
        if location:
            vars["location"] = "<i>%s</i><br><pre>%s</pre>"%( location.getName(), location.getAddress() )
            room = self._conf.getRoom()
            if room:
                roomLink = linking.RoomLinker().getHTMLLink( room, location )
                vars["location"] += _("""<small> _("Room"):</small> %s""")%roomLink
        vars["chairs"] = self._getChairsHTML()
        vars["material"] = self._getMaterialHTML()
        vars["moreInfo"] = self._getMoreInfoHTML()
        vars["actions"] = self._getActionsHTML(vars.get("menuStatus", "open") != "open")

        return vars


class WConfDetailsFull(WConfDetailsBase):
    pass


class WConfDetailsMin(WConfDetailsBase):
    pass

#---------------------------------------------------------------------------

class WConfDetails:

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getHTML( self, params ):
        if self._conf.canAccess( self._aw ):
            return WConfDetailsFull( self._aw, self._conf ).getHTML( params )
        if self._conf.canView( self._aw ):
            return WConfDetailsMin( self._aw, self._conf ).getHTML( params )
        return ""


class WPConferenceDisplay( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):

        wc = WConfDetails( self._getAW(), self._conf )
        pars = { \
    "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
    "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
    "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
    "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
    "materialURLGen": urlHandlers.UHMaterialDisplay.getURL, \
    "menuStatus": self._rh._getSession().getVar("menuStatus") or "open"}
        return wc.getHTML( pars )

    def _getHeadContent( self ):
        #This is used for fetching the css file for conference page
        path = baseurl = self._getBaseURL()
        printCSS = """
        <link rel="stylesheet" type="text/css" href="%s/css/Conf_Basic.css" >
            """ % path
        confCSS = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager().getCSS()
        if confCSS:
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s">"""%(confCSS.getURL())
        return printCSS


    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._overviewOpt)

class WSentMail  (wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=urlHandlers.UHConferenceDisplay.getURL(self._conf)
        return vars


class WPSentEmail( WPConferenceDefaultDisplayBase ):
    def _getBody(self,params):
        wc = WSentMail(self._conf)
        return wc.getHTML()

class WEmail(wcomponents.WTemplated):

    def __init__(self,conf,user,toEmail):
        self._conf = conf
        try:
            self._fromEmail = user.getEmail()
        except:
            self._fromEmail = ""
        self._toEmail = toEmail

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        if vars.get("from", None) is None :
            vars["from"] = self._fromEmail
        if vars.get("fromDisabled", None) is None or not vars.get("fromDisabled", None):
            vars["fromField"] = """<input type="text" name="from" size="50" value="%s"></text>"""%vars["from"]
        else :
            vars["fromField"] = """<input type="hidden" name="from" value="%s"></input>%s"""%(vars["from"],vars["from"])

        if vars.get("to", None) is None :
            vars["to"] = self._toEmail
        if vars.get("toDisabled",None) is None or not vars.get("toDisabled",None):
            vars["toField"] = """<textarea name="to" cols="50" rows="4">%s</textarea>"""%vars["to"]
        else :
            vars["toField"] = """<input type="hidden" name="to" value="%s"></input>%s"""%(vars["to"],vars["to"])

        if vars.get("cc", None) is None :
            vars["cc"]= ""
        if vars.get("postURL",None) is None :
            vars["postURL"]=urlHandlers.UHConferenceSendEmail.getURL(self._conf)
        if vars.get("subject", None) is None :
            vars["subject"]=""
        if vars.get("body", None) is None :
            vars["body"]=""
        return vars

class WPEMail ( WPConferenceDefaultDisplayBase ):

    def _getBody(self,params):
        toemail = params["emailto"]
        wc = WEmail(self._conf, self._getAW().getUser(), toemail)
        params["fromDisabled"] = True
        params["toDisabled"] = True
        params["ccDisabled"] = True
        return wc.getHTML(params)

class WPXSLConferenceDisplay( WPConferenceBase ):

    def __init__( self, rh, conference, view, type, params ):
        WPConferenceBase.__init__( self, rh, conference )
        self._params = params
        self._view = view
        self._conf = conference
        self._type = type
        self._parentCateg = None
        categId = rh._getSession().getVar("currentCategoryId")
        if categId != None:
            self._parentCateg = self._conf.getOwnerById(categId)
        self._webcastadd = False
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        if wm.isManager(self._getAW().getUser()):
            self._webcastadd = True


    def getJSFiles(self):
        modules = WPConferenceBase.getJSFiles(self)

        # if the user has management powers, include
        # these modules
        #if self._conf.canModify(self._rh.getAW()):

        # TODO: find way to check if the user is able to manage
        # anything inside the conference (sessions, ...)

        modules += self._includeJSPackage('Management')
        modules += self._includeJSPackage('MaterialEditor')
        modules += self._includeJSPackage('Display')
        return modules

    def _getFooter( self ):
        """
        """
        wc = wcomponents.WFooter()
        p = {"modificationDate":self._conf.getModificationDate().strftime("%d %B %Y %H:%M"),"subArea": self._getSiteArea(),"dark":True}
        if Config.getInstance().getShortEventURL():
            id=self._conf.getUrlTag().strip()
            if not id:
                id = self._conf.getId()
            p["shortURL"] =  Config.getInstance().getShortEventURL() + id
        return wc.getHTML(p)

    def _getHeadContent( self ):
        htdocs = Config.getInstance().getHtdocsDir()
        # First include the default Indico stylesheet
        styleText = """<link rel="stylesheet" href="%s/css/%s">\n""" % \
            (self._getBaseURL(), Config.getInstance().getCssStylesheetName())
        # Then the common event display stylesheet
        if os.path.exists("%s/css/common.css" % htdocs):
            styleText += """        <link rel="stylesheet" href="%s/css/common.css">\n""" % self._getBaseURL()
        if self._type == "simple_event":
            styleText += """        <link rel="stylesheet" href="%s/css/lecture.css">\n""" % self._getBaseURL()
        # And finally the specific display stylesheet
        if os.path.exists("%s/css/%s.css" % (htdocs,self._view)):
            styleText += """        <link rel="stylesheet" href="%s/css/%s.css">\n""" % (self._getBaseURL(), self._view)
        return styleText

    def _getHTMLHeader( self ):

        if self._view in ["xml","text","jacow"] and (self._params.get("frame","")=="no" or self._params.get("fr","")=="no"):
            return ""

        tpl = wcomponents.WHTMLHeader();

        return tpl.getHTML({"area": "",
                            "baseurl": self._getBaseURL(),
                            "conf": Config.getInstance(),
                            "page": self,
                            "extraCSSFiles": self._extraCSSFiles,
                            "extraCSS": self._extraCSS,
                            "extraJSFiles": self.getJSFiles(),
                            "extraJS": self._extraJS,
                            "language": self._getAW().getSession().getLang()
                            })

    def _getHeader( self ):
        """
        """
        if self._type == "simple_event":
            wc = wcomponents.WMenuSimpleEventHeader( self._getAW(), self._getNavigationDrawer(), self._conf )
        elif self._type == "meeting":
            wc = wcomponents.WMenuMeetingHeader( self._getAW(), self._getNavigationDrawer(), self._conf )
        else:
            wc = wcomponents.WMenuConferenceHeader( self._getAW(), self._getNavigationDrawer(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(),\
                             "currentView": self._view,\
                             "type": self._type,\
                             "selectedDate": self._params.get("showDate",""),\
                             "selectedSession": self._params.get("showSession",""),\
                             "detailLevel": self._params.get("detailLevel",""),\
                             "filterActive": self._params.get("filterActive",""),\
                             "loginAsURL": self.getLoginAsURL(),
                            "dark": True } )

    def _applyDecoration( self, body ):
        """
        """
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
            if self._view in ["xml","text","jacow"]:
                return body
            else:
                return WPrintPageFrame().getHTML({"content":body})
        return WPConferenceBase._applyDecoration(self, body)

    def _getHTMLFooter( self ):
        if (self._view in ["xml","text","jacow"]) and (self._params.get("frame","")=="no" or self._params.get("fr","")=="no"):
            return ""
        return WPConferenceBase._getHTMLFooter(self)

    def _getBody( self, params ):
        pars = { \
        "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
        "minutesURL":  urlHandlers.UHConferenceDisplayWriteMinutes.getURL(self._conf), \
        "iCalURL": urlHandlers.UHConferenceToiCal.getURL(self._conf), \
        "cloneURL": urlHandlers.UHConfClone.getURL( self._conf ), \
        "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
        "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
        "contribMinutesURLGen": urlHandlers.UHContributionDisplayWriteMinutes.getURL, \
        "sessionMinutesURLGen": urlHandlers.UHSessionDisplayWriteMinutes.getURL, \
        "subContribMinutesURLGen": urlHandlers.UHSubContributionDisplayWriteMinutes.getURL, \
        "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
        "materialURLGen": urlHandlers.UHMaterialDisplay.getURL, \
        "resourceURLGen": urlHandlers.UHFileAccess.getURL, \
        "frame": self._params.get("frame","") or self._params.get("fr","") }

        if self._webcastadd:
            urladdwebcast = urlHandlers.UHWebcastAddWebcast.getURL()
            urladdwebcast.addParam("eventid",self._conf.getId())
            pars['webcastAdminURL'] = urladdwebcast

        frame = self._params.get("frame","") != "no" and self._params.get("fr","") != "no"
        view = self._view
        outGen = outputGenerator(self._getAW())
        path = Config.getInstance().getStylesheetsDir()
        if os.path.exists("%s/%s.xsl" % (path,view)):
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            tz = DisplayTZ(self._getAW(),self._conf).getDisplayTZ()
            useCache = minfo.isCacheActive() and frame and self._params.get("detailLevel", "") in [ "", "contribution" ] and self._view == self._conf.getDefaultStyle() and self._params.get("showSession","all") == "all" and self._params.get("showDate","all") == "all" and tz == self._conf.getTimezone()
            useNormalCache = useCache and self._conf.isFullyPublic() and not self._conf.canModify(self._getAW()) and self._getAW().getUser() == None
            useManagerCache = useCache and self._conf.canModify( self._getAW())
            body = ""
            if useManagerCache:
                cache = EventCache({"id": self._conf.getId(), "type": "manager"})
                body = cache.getCachePage()
            elif useNormalCache:
                cache = EventCache({"id": self._conf.getId(), "type": "normal"})
                body = cache.getCachePage()
            if body == "":
                stylepath = "%s/%s.xsl" % (path,view)
                if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                    includeContribution = 1
                else:
                    includeContribution = 0
                body = outGen.getFormattedOutput(self._conf,stylepath,pars,1,includeContribution,1,self._params.get("showSession",""),self._params.get("showDate",""))
            if useManagerCache or useNormalCache:
                cache.saveCachePage( body )
            if not frame:
                html = body
            else:
                html = """
                %s
                %s
                %s
            """%(wcomponents.WErrorMessage().getHTML(params), \
                wcomponents.WInfoMessage().getHTML(params), \
                body)
            return html
        else:
            return _("Cannot find the %s stylesheet") % view

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._overviewOpt)

class WPrintPageFrame ( wcomponents.WTemplated ):
    pass

class WConfProgramTrack(wcomponents.WTemplated):

    def __init__( self, aw, track ):
        self._aw = aw
        self._track = track

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["bulletURL"] = Config.getInstance().getSystemIconURL( "track_bullet" )
        mgtIconHTML = ""
        if self._track.getConference().hasEnabledSection("cfa") and self._track.canCoordinate( self._aw ):
            url = urlHandlers.UHTrackModifAbstracts.getURL( self._track )
            if self._track.getConference().canModify( self._aw ):
                url = urlHandlers.UHTrackModification.getURL( self._track )
            mgtIconHTML = """<a href="%s"><img src="%s" alt="Enter in track management area" border="0"></a>
                    """%(url, Config.getInstance().getSystemIconURL( "modify" ))
        vars["mgtIcon"] = mgtIconHTML
        vars["title"] = self._track.getTitle()
        vars["coordinators"] = ""
        vars["description"] = self._track.getDescription()
        subtracks = []
        for subtrack in self._track.getSubTrackList():
            subtracks.append( "%s"%subtrack.getTitle() )
        vars["subtracks"] = ""
        if subtracks:
            vars["subtracks"] = _("""<i> _("Sub-tracks")</i>: %s""")%", ".join( subtracks )
        return vars


class WConfProgram(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["description"] = self._conf.getProgramDescription()
        program = []
        for track in self._conf.getTrackList():
            program.append( WConfProgramTrack( self._aw, track ).getHTML() )
        vars["program"] = "".join( program )
        return vars




class WPConferenceProgram( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = WConfProgram( self._getAW(), self._conf )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._programOpt)

    def _defineToolBar(self):
        pdf=wcomponents.WTBItem( _("get PDF of the programme"),
            icon=Config.getInstance().getSystemIconURL("pdf"),
            actionURL=urlHandlers.UHConferenceProgramPDF.getURL(self._conf))
        if len(self._conf.getTrackList()) > 0:
            self._toolBar.addItem(pdf)


class WInternalPageDisplay(wcomponents.WTemplated):

    def __init__(self, conf, page):
        self._conf = conf
        self._page=page

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["content"] = self._page.getContent()
        return vars

class WPInternalPageDisplay( WPConferenceDefaultDisplayBase ):

    def __init__( self, rh, conference, page ):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conference )
        self._page = page

    def _getBody( self, params ):
        wc = WInternalPageDisplay( self._conf, self._page )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)

        for link in self._sectionMenu.getAllLinks():
            if link.getType() == 'page' and link.getPage().getId() == self._page.getId():
                self._sectionMenu.setCurrentItem(link)
                break


class WConferenceTimeTable(wcomponents.WTemplated):

    def __init__( self, conference, aw ):
        self._conf = conference
        self._aw = aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        vars["ttdata"] = simplejson.dumps(schedule.ScheduleToJson.process(self._conf.getSchedule(), tz))
        vars['eventInfo'] = simplejson.dumps(DictPickler.pickle(self._conf, timezone=tz))
        return vars


class WConferenceRoomTimeTable(WConferenceTimeTable):

    def _blankEntryHTML( self ):
        return """ """

    def _getEntryHTML(self,entry,refDay):
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.SessionSlot):
                return self._getSessionHTML(entry.getOwner(),self._sessionURLGen(entry.getOwner()),refDay)
            if isinstance(entry.getOwner(), conference.Contribution):
                return self._getContributionHTML(entry.getOwner(), \
                                                self._contribURLGen(entry.getOwner()))
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            return self._getBreakHTML(entry)
        else:
            return self._blankEntryHTML()



    def _getHTMLTimeTable( self, highDetailLevel=0 ):
        self._sessionColorMap = {}
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/self._timeTable.getSlotLength().seconds)
        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        for day in self._timeTable.getDayList():
            self._sessionColorMap.clear()
            emptyDay=True
            slotList=[]
            lastEntries=[]
            roomList=[]
            maxOverlap=day.getNumMaxOverlaping()
            width="100"
            if maxOverlap!=0:
                width=100/maxOverlap
            else:
                maxOverlap=1

            # Make a list of all the Rooms used in that day
            unknown =False
            for hour in range(day.getStartHour(),day.getEndHour()+1):
                for slot in day.getSlotsOnHour(hour):
                    entryList=slot.getEntryList()
                    for entry in entryList:
                        room = entry.getOwner().getRoom()
                        if room != None:
                            if room.getName() not in roomList:
                                roomList.append(room.getName())
                        if room ==None and not isinstance(entry,schedule.BreakTimeSchEntry):
                            unknown=True
                        else:
                            continue
            if unknown:
                roomList.append( _("Room Unknown"))


            for hour in range(day.getStartHour(),day.getEndHour()+1):
                hourSlots=[]
                emptyHour = True
                #Order the entries based on the room order
                for slot in day.getSlotsOnHour(hour):
                    entryOrder=[]
                    for i in range(0,(len(roomList))):
                        entryOrder.append(i)
                    entryList=slot.getEntryList()
                    remColSpan=maxOverlap
                    temp=[]
                    for ent in entryList:
                        roomname =None
                        room = ent.getOwner().getRoom()
                        if room !=None:
                            roomname = room.getName()
                        elif not isinstance(ent,schedule.BreakTimeSchEntry):
                            roomname = _("Room Unknown")

                        if entryOrder != []:
                            if roomname !=None:
                                if roomname in roomList:
                                    pos =roomList.index(roomname)
                                    try:
                                        entryOrder[pos]=ent
                                    except TypeError,e:
                                        continue
                                    except IndexError,e:
                                        entryOrder
                            if not isinstance(ent,schedule.BreakTimeSchEntry):
                                entryOrder.append(ent)
                            elif isinstance(ent,schedule.BreakTimeSchEntry):
                                entryOrder=[]
                                entryOrder.append(ent)



                     #Create the timetable
                    for entry in entryOrder:
                        emptyHour = False
                        emptyDay = False
                        if entry in lastEntries:
                            continue
                        bgcolor=self._getColor(entry)
                        textcolor=self._getTextColor(entry)
                        colspan=""" colspan="1" """
                        if isinstance(entry,schedule.BreakTimeSchEntry):
                            colspan = """ colspan="%s" """%len(roomList)
                        temp.append("""<td valign="top" rowspan="%i" align="center" bgcolor="%s" %s><font color="%s">%s</font></td>"""%(day.getNumSlots(entry),bgcolor,colspan,textcolor,self._getEntryHTML(entry,day)))
                        if type(entry) != int:
                            lastEntries.append(entry)
                    if slot.getAdjustedStartDate().minute==0:
                        hourSlots.append("""
                            <tr>
                                <td valign="top" rowspan="%s" bgcolor="white"  width="10" style="padding-right: 5px;"><font color="gray" size="-1">%02i:00</font></td>
                                %s
                            </tr>
                            """%(num_slots_in_hour,\
                                    hour,\
                                    "".join(temp)))
                    else:
                        if len(temp) == 0:
                            temp = ["<td></td>"]
                        hourSlots.append("""<tr>%s</tr>"""%"".join(temp))

                if emptyHour:
                    slotList.append("""
                <tr>
                    <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"><font color="gray" size="-1">%02i:00</font></td>
                    <td>&nbsp;</td>
                </tr>""" % hour)
                else:
                    slotList.append("".join(hourSlots))
            legend=""
            roomhtml =[]
            if roomList !=[]:
                roomhtml.append( _("""<td width="10" bgcolor="white"><font color="gray"> _("Room")</font></td>"""))
                for room in roomList:
                    if room != "":
                        roomhtml.append("""<td bgcolor="white" align="center">%s</td>"""%room)
            #if len(roomList) < len(entryOrder):
            #    roomhtml.append("""<td bgcolor="white" align="center">Unknown Room</td>""")
            if highDetailLevel:
                legend=self._getColorLegendHTML()
            if not emptyDay:
                str="""
                    <table align="center" width="100%%">
                        <tr>
                            <td width="100%%">
                                <table align="center" border="0" width="100%%"
                                        celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                                    <tr>
                                        <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"></td>
                                        <td colspan="%i" align="center" bgcolor="white"><b>%s</b></td>
                                   </tr>
                                   <tr>
                                       <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"></td>
                                       <td colspan="%i" align="center" bgcolor="white">%s</td>
                                   </tr>
                                   </tr>


                                     <tr>
                                        %s
                                    </tr>
                                       %s
                                </table>
                            </td>
                        </tr>
                    </table>
                    """%(len(roomList),\
                            day.getDate().strftime("%A, %d %B %Y"),\
                            len(roomList),legend,"".join(roomhtml), \
                            "".join(slotList) )
                daySch.append(str)
        str = "<br>".join( daySch )
        return str

class WConferenceSessionTimeTable(WConferenceTimeTable):

    def _blankEntryHTML( self ):
        return """ """

    def _getEntryHTML(self,entry,refDay):
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.SessionSlot):
                return self._getSessionHTML(entry.getOwner(),self._sessionURLGen(entry.getOwner()),refDay)
            if isinstance(entry.getOwner(), conference.Contribution):
                return self._getContributionHTML(entry.getOwner(), \
                                                self._contribURLGen(entry.getOwner()))
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            return self._getBreakHTML(entry)
        else:
            return self._blankEntryHTML()



    def _getHTMLTimeTable( self, highDetailLevel=0 ):
        self._sessionColorMap = {}
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/self._timeTable.getSlotLength().seconds)
        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        for day in self._timeTable.getDayList():
            self._sessionColorMap.clear()
            emptyDay=True
            slotList=[]
            lastEntries=[]
            sessionList=[]
            maxOverlap=day.getNumMaxOverlaping()
            width="100"
            if maxOverlap!=0:
                width=100/maxOverlap
            else:
                maxOverlap=1

            # Make a list of all the sessions used in that day
            unknown =False
            for hour in range(day.getStartHour(),day.getEndHour()+1):
                for slot in day.getSlotsOnHour(hour):
                    entryList=slot.getEntryList()
                    for entry in entryList:
                        session = entry.getOwner().getSession()
                        if session != None:
                            if session.getTitle() not in sessionList:
                                sessionList.append(session.getTitle())
                        if session ==None and not isinstance(entry,schedule.BreakTimeSchEntry):
                            unknown=True
                        else:
                            continue
            if unknown:
                sessionList.append( _("Session Unknown"))


            for hour in range(day.getStartHour(),day.getEndHour()+1):
                hourSlots=[]
                emptyHour = True
                #Order the entries based on the session order
                for slot in day.getSlotsOnHour(hour):
                    entryOrder=[]
                    for i in range(0,(len(sessionList))):
                        entryOrder.append(i)
                    entryList=slot.getEntryList()
                    remColSpan=maxOverlap
                    temp=[]
                    for ent in entryList:
                        sessionname =None
                        session = ent.getOwner().getSession()
                        if session !=None:
                            sessionname = session.getTitle()
                        elif not isinstance(ent,schedule.BreakTimeSchEntry):
                            sessionname = _("Session Unknown")


                        if entryOrder != []:
                            if sessionname !=None:
                                if sessionname in sessionList:
                                    pos =sessionList.index(sessionname)
                                    try:
                                        entryOrder[pos]=ent
                                    except TypeError,e:
                                        continue
                                    except IndexError,e:
                                        entryOrder
                            if not isinstance(ent,schedule.BreakTimeSchEntry):
                                entryOrder.append(ent)
                            elif isinstance(ent,schedule.BreakTimeSchEntry):
                                entryOrder=[]
                                entryOrder.append(ent)



                     #Create the timetable
                    for entry in entryOrder:
                        emptyHour = False
                        emptyDay = False
                        if entry in lastEntries:
                            continue
                        bgcolor=self._getColor(entry)
                        textcolor=self._getTextColor(entry)
                        colspan=""" colspan="1" """
                        if isinstance(entry,schedule.BreakTimeSchEntry):
                            colspan = """ colspan="%s" """%len(sessionList)
                        temp.append("""<td valign="top" rowspan="%i" align="center" bgcolor="%s" %s><font color="%s">%s</font></td>"""%(day.getNumSlots(entry),bgcolor,colspan,textcolor,self._getEntryHTML(entry,day)))
                        if type(entry) != int:
                            lastEntries.append(entry)
                    if slot.getAdjustedStartDate().minute==0:
                        hourSlots.append("""
                            <tr>
                                <td valign="top" rowspan="%s" bgcolor="white"  width="10" style="padding-right: 5px;"><font color="gray" size="-1">%02i:00</font></td>
                                %s
                            </tr>
                            """%(num_slots_in_hour,\
                                    hour,\
                                    "".join(temp)))
                    else:
                        if len(temp) == 0:
                            temp = ["<td></td>"]
                        hourSlots.append("""<tr>%s</tr>"""%"".join(temp))

                if emptyHour:
                    slotList.append("""
                <tr>
                    <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"><font color="gray" size="-1">%02i:00</font></td>
                    <td>&nbsp;</td>
                </tr>""" % hour)
                else:
                    slotList.append("".join(hourSlots))
            legend=""
            sessionhtml =[]
            if sessionList !=[]:
                sessionhtml.append( _("""<td width="10" bgcolor="white"><font color="gray"> _("session")</font></td>"""))
                for session in sessionList:
                    if session != "":
                        sessionhtml.append("""<td bgcolor="white" align="center">%s</td>"""%session)
            #if len(sessionList) < len(entryOrder):
            #    sessionhtml.append("""<td bgcolor="white" align="center">Unknown session</td>""")
          #  if highDetailLevel:
          #      legend=self._getColorLegendHTML()
            if not emptyDay:
                str="""
                    <table align="center" width="100%%">
                        <tr>
                            <td width="100%%">
                                <table align="center" border="0" width="100%%"
                                        celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                                    <tr>
                                        <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"></td>
                                        <td colspan="%i" align="center" bgcolor="white"><b>%s</b></td>
                                   </tr>
                                   <tr>
                                       <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"></td>
                                       <td colspan="%i" align="center" bgcolor="white">%s</td>
                                   </tr>
                                   </tr>


                                     <tr>
                                        %s
                                    </tr>
                                       %s
                                </table>
                            </td>
                        </tr>
                    </table>
                    """%(len(sessionList),\
                            day.getDate().strftime("%A, %d %B %Y"),\
                            len(sessionList),legend,"".join(sessionhtml), \
                            "".join(slotList) )
                daySch.append(str)
        str = "<br>".join( daySch )
        return str

class WConferencePlainTimeTable(WConferenceTimeTable):

    def _getContributionHTML( self, contribution, URL ):
        speakerList = []
        for speaker in contribution.getSpeakerList():
            spkcapt=speaker.getDirectFullName()
            if speaker.getAffiliation().strip() != "":
                spkcapt="%s (%s)"%(spkcapt, speaker.getAffiliation())
            speakerList.append(spkcapt)
        sDate = contribution.getAdjustedStartDate()
        eDate = contribution.getAdjustedEndDate()
        contrStr = """
                        <tr>
                            <td valign="top" align="left" bgcolor="white" width="150px" nowrap>%s-%s (%s)</td>
                            <td valign="top" align="left" bgcolor="white" width="100%%" style="padding-left:5px">[%s] <a href="%s">%s</a></td>
                            <td align="right" nowrap>%s</td>
                        </tr>
                   """%(sDate.strftime("%H:%M"), \
                           eDate.strftime("%H:%M"), \
                           (datetime(1900,1,1)+contribution.getDuration()).strftime("%Hh%M'"), \
                           self.htmlText(contribution.getId()),
                           URL,
                           self.htmlText(contribution.getTitle()),
                           "<br>".join(speakerList) )
        return contrStr

    def _getSessionSlotHTML(self,event,URL,refDay):
        sesSlot=event.getOwner()
        session=sesSlot.getSession()
        room=""
        if sesSlot.getRoom()!=None:
            room = """<tr>
                        <td valign="top" align="left" style="color:%s"><b>Room: </b></td>
                        <td nowrap align="left" style="color:%s">%s</td>
                    </tr>"""%(session.getTextColor(),session.getTextColor(),sesSlot.getRoom().getName())
        convenerList = []
        for convener in sesSlot.getConvenerList():
            convcapt=convener.getDirectFullName()
            if convener.getAffiliation().strip() != "":
                convcapt="%s (%s)"%(convcapt, convener.getAffiliation())
            convenerList.append(convcapt)
        if len(convenerList)==0:
            for convener in session.getConvenerList():
                convcapt=convener.getDirectFullName()
                if convener.getAffiliation().strip() != "":
                    convcapt="%s (%s)"%(convcapt, convener.getAffiliation())
                convenerList.append(convcapt)
        conveners = ""
        if len(convenerList) != 0:
            conveners = _("""<tr>
                                <td valign="top" align="left" style="color:%s"><b> _("Conveners"): </b></td>
                                <td nowrap align="left" style="color:%s">
                                    %s
                                </td>
                            <tr>""")%(session.getTextColor(),session.getTextColor(),"<br>".join(convenerList))
        materialList = []
        for material in session.getMaterialList():
            materialList.append(material.getTitle())
        materials = ""
        if len(materialList) != 0:
            materials = _("""<tr>
                                <td align="left" valign="top" style="color:%s"><b> _("Material"): </b></td>
                                <td align="left" nowrap style="color:%s">
                                    %s
                                </td>
                            <tr>""")%(session.getTextColor(),session.getTextColor(),"<br>".join(materialList))
        currentUser = self._aw._currentUser
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        sDate = event.getAdjustedStartDate(tz)
        eDate = event.getAdjustedEndDate(tz)
        timeInterval = " (%s-%s)"%( \
                                    sDate.strftime("%H:%M"), \
                                    eDate.strftime("%H:%M") )
        if event.getAdjustedStartDate(tz).strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
            if event.getAdjustedEndDate(tz).strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
                timeInterval = ""
            else:
                timeInterval = "<br>(until %s)"%(eDate.strftime("%H:%M"))
        else:
            if event.getAdjustedEndDate(tz).strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
                timeInterval = "<br>(from %s)"%(sDate.strftime("%H:%M"))
        title = self.htmlText(event.getTitle())
        linkColor=""
        if session.isTextColorToLinks():
            linkColor="color:%s"%session.getTextColor()
        return """
                <table width="100%%">
                    <tr>
                        <td width="75%%" style="color:%s">
                            <a href="%s" style="%s">%s</a><small>%s</small>
                        </td>
                        <td nowrap align="left" valign="bottom"
                            width="25%%">
                            <table align="left">
                                %s
                                %s
                                %s
                            </table>
                        </td>
                    </tr>
                </table>
                  """%(session.getTextColor(), URL, linkColor, title,timeInterval,conveners,room,materials)

    def _getBreakHTML( self, breakEntry ):
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        sDate = breakEntry.getAdjustedStartDate(tz)
        eDate = breakEntry.getAdjustedEndDate(tz)
        return """
                        <tr>
                            <td valign="top" align="left" bgcolor="white" width="150px" nowrap>%s-%s (%s)</td>
                            <td valign="top" align="center" bgcolor="white" width="100%%" style="padding-left:5px"><b><i>%s</i></b></td>
                        </tr>
                   """%(sDate.strftime("%H:%M"), \
                           eDate.strftime("%H:%M"), \
                           (datetime(1900,1,1)+breakEntry.getDuration()).strftime("%Hh%M'"), \
                           breakEntry.getTitle())


    def _getEntryHTML(self,entry,refDay):
        if isinstance(entry,timetable.SessionSlot):
            return self._getSessionSlotHTML(entry,self._sessionURLGen(entry.getOwner()),refDay)
        elif isinstance(entry, timetable.ConfEntry):
            if not entry.isBreak():
                return self._getContributionHTML(entry.getOwner(), \
                                                self._contribURLGen(entry.getOwner()))
            else:
                return self._getBreakHTML(entry)
        elif isinstance(entry, schedule.LinkedTimeSchEntry):
            return self._getContributionHTML(entry.getOwner(), \
                                                self._contribURLGen(entry.getOwner()))
        else:
            return self._getBreakHTML(entry)

    def _getHTMLTimeTable(self,highDetailLevel=0):
        daySch = []
        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        for day in self._timeTable.getDayList():
            emptyDay = True
            eventList=[]
            c=0
            for event in day.getEventList():
                emptyDay = False
                temp=[]
                if isinstance(event,timetable.SessionSlot):
                    entries=[]
                    if highDetailLevel:
                        for entry in event.getEntryList():
                            entries.append(""" %s
                                            <tr>
                                                <td>&nbsp;</td>
                                            </tr>
                                            <tr>
                                                <td style="border-top:1px solid #777777" colspan="3">&nbsp;</td>
                                            </tr>"""%(self._getEntryHTML(entry,day) ) )
                    sesStr = """
                        <tr>
                            <td colspan="3" width="100%%">
                                <table align="center" border="0"
                                        width="100%%" celspacing="0"
                                        cellpadding="0" style="border-left:2px solid #777777;border-top:2px solid #777777;">
                                    <tr>
                                        <td align="center" colspan="3"  bgcolor="%s" style="padding:10px">%s</td>
                                    </tr>
                                    %s
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td>&nbsp;</td>
                        </tr>
                         """%(event.getOwner().getColor(),self._getEntryHTML(event,day),"".join(entries))
                    eventList.append(sesStr)
                else:
                    temp.append("""%s
                                    <tr><td>&nbsp;</td></tr>
                                    <tr><td style="border-top:1px solid #777777" colspan="3">&nbsp;</td></tr>"""%(self._getEntryHTML(event,day) ) )
                    eventList.append("".join(temp))
            if not emptyDay:
                str="""
                    <table align="center" width="100%%">
                        <tr>
                            <td align="left" bgcolor="white" style="border-bottom:2px solid #777777;"><b>%s</b></td>
                        </tr>
                        <tr><td>&nbsp;</td></tr>
                        <tr>
                            <td width="100%%">
                                <table align="center" border="0" width="100%%" celspacing="0" cellpadding="0">
                                    %s
                                </table>
                            </td>
                        </tr>
                    </table>
                    """%(day.getDate().strftime("%A, %d %B %Y"), \
                            "".join(eventList))
                daySch.append(str)
        str = "<br>".join( daySch )
        return str

class ContainerIndexItem:

    def __init__(self, container, day):
        self._overlap = container.getMaxOverlap(day)
        self._startPosition = -1
        self._entryList = []
        for i in range(0,self._overlap):
            self._entryList.append(None)

    def setStartPosition(self, counter):
        self._startPosition = counter

    def getStartPosition(self):
        return self._startPosition

    def setEntryList(self, newEntryList):
        # -- Remove the ones which are not in the new entry list
        i = 0
        for entry in self._entryList:
            if entry not in newEntryList:
                self._entryList[i] = None
            i += 1
        # -- Add the new ones to the new entry list
        for newEntry in newEntryList:
            if newEntry not in self._entryList:
                i = 0
                for entry in self._entryList:
                    if entry == None:
                        self._entryList[i] = newEntry
                        break
                    i += 1

    def getEntryIndex(self, i):
        return self._startPosition + i

    def getEntryByPosition(self, i):
        if i >= 0 and i < len(self._entryList):
            return self._entryList[i]
        return 0

    def getOverlap(self):
        return self._overlap

class ContainerIndex:

    def __init__(self, containerIndex = {}, day = None, hasOverlap = True):
        self._containerIndex = containerIndex
        self._day = day
        self._rowsCounter = 0
        self._hasOverlap = hasOverlap

    def initialization(self, day, hasOverlap = True):
        self._containerIndex={}
        self._day = day
        self._rowsCounter = 0
        self._hasOverlap = hasOverlap

    def hasOverlap(self):
        return self._hasOverlap

    def setHasOverlap(self, hasOverlap):
        self._hasOverlap = hasOverlap

    def addContainer(self, container):
        if not self._containerIndex.has_key(container):
            item = ContainerIndexItem(container, self._day)
            item.setStartPosition(self._rowsCounter)
            if self.hasOverlap():
                self._rowsCounter += item.getOverlap()
            self._containerIndex[container] = item

    def setContainerEntries(self, container, entryList):
        if self._containerIndex.has_key(container):
            self._containerIndex[container].setEntryList(entryList)

    def getEntryIndex(self, container, i):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getEntryIndex(i)
        return 0

    def getEntryByPosition(self, container, i):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getEntryByPosition(i)
        return 0

    def getMaxOverlap(self, container):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getOverlap()
        return 0

    def getStartPosition(self, container):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getStartPosition()
        return 0

    def getLastPosition(self):
        lastPos = 0
        for cont in self._containerIndex.values():
            startPos = cont.getStartPosition()
            if startPos >= lastPos:
                lastPos = startPos + cont.getOverlap()
        return lastPos


class WConferenceHighDetailTimeTable(WConferenceTimeTable):

    def _initTempList(self, max, defaultValue=None):
        t = []
        for i in range(0, max):
            t.append(defaultValue)
        return t

    def _getHTMLTimeTable( self, highDetailLevel=0 ):
        containerIndex = ContainerIndex()
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/self._timeTable.getSlotLength().seconds)
        hourSlots,hourNeedsDisplay = [],False
        for day in self._timeTable.getDayList():
            emptyDay = True
            self._sessionColorMap.clear()
            slotList=[]
            lastEntries=[]
            maxOverlap=day.getContainerMaxOverlap()
            if not day.hasContainerOverlaps():
                maxOverlap = day.getNumMaxOverlaping() or 1
            width="100"
            if maxOverlap!=0:
                width=100/maxOverlap
            numMaxEntriesSlot=maxOverlap#day.getNumMaxOverlaping()
            containerIndex.initialization(day,day.hasContainerOverlaps())
            for slot in day.getSlotList():
                if slot.getAdjustedStartDate().minute==0:
                    if hourNeedsDisplay:
                        slotList.append("".join(hourSlots))
                    hourSlots,hourNeedsDisplay=[],False
                temp=self._initTempList(maxOverlap,"""<td width="%s%%"></td>"""%width)
                for container in slot.getContainerList():
                    emptyDay = False
                    hourNeedsDisplay=True
                    containerIndex.addContainer(container)
                    entryList=slot.getContainerEntries(container)
                    containerIndex.setContainerEntries(container,entryList)
                    maxoverlapContainer=containerIndex.getMaxOverlap(container)
                    for i in range(0,maxoverlapContainer):
                        entry=containerIndex.getEntryByPosition(container,i)
                        entryIndex=containerIndex.getEntryIndex(container,i)
                        if entry and (entry in lastEntries):
                            temp[entryIndex] = ""
                            continue
                        bgcolor=self._getColor(entry)
                        textcolor=self._getTextColor(entry)
                        colspan=""
                        if isinstance(entry,schedule.BreakTimeSchEntry) and \
                                                            len(entryList)==1:
                            colspan=""" colspan="%s" """%maxoverlapContainer
                        if entry:
                            if not day.hasEntryOverlaps(entry) and \
                                                len(slot.getEntryList()) == 1:
                                entryIndex=0
                                colspan=""" colspan="%s" """%(numMaxEntriesSlot)
                                for j in range(0, len(temp)):
                                    temp[j]=""
                            temp[entryIndex] = """<td id="entry" valign="top" rowspan="%s" align="center" bgcolor="%s" style="color:%s" width="%s%%"%s>%s</td>"""%(day.getNumSlots(entry),bgcolor,textcolor,width,colspan,self._getEntryHTML(entry,day))
                        lastEntries.append(entry)
                # --- Entries of the conference which are not inside any container(session slot)
                confEntries = slot.getEntriesWithoutContainer()
                if confEntries != []:
                    hourNeedsDisplay=True
                    if slot.getContainerList() == []:
                        entryIndex=0
                        for j in range(0, len(temp)):
                            temp[j]=""
                    else:
                        entryIndex = containerIndex.getLastPosition()
                        if entryIndex >= len(temp):
                            for entry in confEntries:
                                temp.append("<td></td>")
                    for entry in confEntries:
                        if entry and (entry in lastEntries):
                            temp[entryIndex] = ""
                            continue
                        bgcolor=self._getColor(entry)
                        textcolor=self._getTextColor(entry)
                        colspan=""
                        if not day.hasEntryOverlaps(entry):
                            colspan=""" colspan="%s" """%(numMaxEntriesSlot)
                            for j in range(entryIndex, len(temp)):
                                temp[j] = ""
                        if entry:
                            temp[entryIndex] = """<td id="conf" valign="top" rowspan="%s" align="center" bgcolor="%s" style="color:%s" width="%s%%"%s>%s</td>"""%(day.getNumSlots(entry),bgcolor,textcolor,width,colspan,self._getEntryHTML(entry,day))
                        entryIndex += 1
                        lastEntries.append(entry)
                # ---.
                if slot.getAdjustedStartDate().minute==0:
                    str="""
                        <tr>
                            <td valign="top" rowspan="%s" bgcolor="white" width="40"><font color="gray" size="-1">%s</font></td>
                            %s
                        </tr>
                        """%(num_slots_in_hour,\
                                slot.getAdjustedStartDate().strftime("%H:%M"),\
                                "".join(temp))
                else:
                    if len(temp) == 0:
                        temp = ["<td></td>"]
                    str = """<tr>%s</tr>"""%"".join(temp)
                hourSlots.append(str)
            if hourNeedsDisplay:
                slotList.append("".join(hourSlots))
                hourSlots,hourNeedsDisplay=[],False
            if not emptyDay:
                legend=""
                if highDetailLevel:
                    legend=self._getColorLegendHTML()
                str="""
                    <table align="center" width="100%%">
                        <tr>
                            <td width="100%%">
                                <table align="center" border="0" width="100%%"
                                        celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                                    <tr>
                                        <td colspan="%i" align="center" bgcolor="white"><b>%s</b></td>
                                    </tr>
                                    <tr>
                                        <td colspan="%i">%s</td>
                                    </tr>
                                    %s
                                </table>
                            </td>
                        </tr>
                    </table>
                    """%(maxOverlap+3,\
                            day.getDate().strftime("%A, %d %B %Y"), \
                            maxOverlap+3, legend,\
                            "".join(slotList) )
                daySch.append(str)
        str = "<br>".join( daySch )
        return str


#class WMeetingHighDetailTimeTable(WConferenceTimeTable):
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        self._contribURLGen = vars["contribURLGen"]
#        self._sessionURLGen = vars["sessionURLGen"]
#        vars["title"] = self._conf.getTitle()
#        vars["timetable"] = self._getHTMLTimeTable(1)
#        return vars


class WPConferenceTimeTable( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEConferenceTimeTable

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Timetable')

    def _getBody( self, params ):
        wc = WConferenceTimeTable( self._conf, self._getAW()  )
        return wc.getHTML(params)

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._timetableOpt)

    def _getHeadContent( self ):
        headContent=WPConferenceDefaultDisplayBase._getHeadContent(self)
        baseurl = Config.getInstance().getBaseURL()
        return """
                 %s
                 <link rel="stylesheet" type="text/css" href="%s/css/timetable.css">
                """ % ( headContent, baseurl)

#class WMeetingTimeTable(WConferenceTimeTable):
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        self._contribURLGen = vars["contribURLGen"]
#        self._sessionURLGen = vars["sessionURLGen"]
#        vars["title"] = self._conf.getTitle()
#        vars["timetable"] = self._getHTMLTimeTable(0)
#        return vars

class WPMeetingTimeTable( WPXSLConferenceDisplay ):

    def getJSFiles(self):
        return WPXSLConferenceDisplay.getJSFiles(self) + \
               self._includeJSPackage('Timetable')

    def _getBody( self, params ):
        wc = WConferenceTimeTable( self._conf, self._getAW()  )
        return wc.getHTML(params)

class WPConferenceModifBase( main.WPMainBase ):

    def __init__( self, rh, conference ):
        main.WPMainBase.__init__( self, rh )
        self._navigationTarget = self._conf = conference
        self._parentCateg = None
        categId = rh._getSession().getVar("currentCategoryId")
        if categId != None:
            self._parentCateg = self._conf.getOwnerById(categId)

    def getJSFiles(self):
        return main.WPMainBase.getJSFiles(self) + \
               self._includeJSPackage('Management') + \
               self._includeJSPackage('MaterialEditor')


    def _getSiteArea(self):
        return "ModificationArea"

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WHeader( self._getAW() )
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())),\
                             "loginAsURL": self.getLoginAsURL() } )

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": True }
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _createSideMenu(self):
        self._sideMenu = wcomponents.ManagementSideMenu()

        # The main section containing most menu items
        self._generalSection = wcomponents.SideMenuSection()

        self._generalSettingsMenuItem = wcomponents.SideMenuItem(_("General settings"),
            urlHandlers.UHConferenceModification.getURL( self._conf ))
        self._generalSection.addItem( self._generalSettingsMenuItem)

        self._timetableMenuItem = wcomponents.SideMenuItem(_("Timetable"),
            urlHandlers.UHConfModifSchedule.getURL( self._conf ))
        self._generalSection.addItem( self._timetableMenuItem)

        self._materialMenuItem = wcomponents.SideMenuItem(_("Material"),
            urlHandlers.UHConfModifShowMaterials.getURL( self._conf ))
        self._generalSection.addItem( self._materialMenuItem)

        self._roomBookingMenuItem = wcomponents.SideMenuItem(_("Room booking"),
            urlHandlers.UHConfModifRoomBookingList.getURL( self._conf ))
        self._generalSection.addItem( self._roomBookingMenuItem)

        self._programMenuItem = wcomponents.SideMenuItem(_("Programme"),
            urlHandlers.UHConfModifProgram.getURL( self._conf ))
        self._generalSection.addItem( self._programMenuItem)

        self._abstractMenuItem = wcomponents.SideMenuItem(_("Abstracts"),
            urlHandlers.UHConfAbstractManagment.getURL( self._conf ))
        self._generalSection.addItem( self._abstractMenuItem)

        self._contribListMenuItem = wcomponents.SideMenuItem(_("Contributions"),
            urlHandlers.UHConfModifContribList.getURL( self._conf ))
        self._generalSection.addItem( self._contribListMenuItem)

        self._regFormMenuItem = wcomponents.SideMenuItem(_("Registration"),
            urlHandlers.UHConfModifRegForm.getURL( self._conf ))
        self._generalSection.addItem( self._regFormMenuItem)

        if self._conf.getCSBookingManager() is not None and self._conf.getCSBookingManager().isCSAllowed():
            from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
            self._videoServicesMenuItem = wcomponents.SideMenuItem(_("Video Services"),
                urlHandlers.UHConfModifCollaboration.getURL(self._conf, secure = CollaborationTools.isUsingHTTPS()))
            self._generalSection.addItem( self._videoServicesMenuItem)
        else:
            self._videoServicesMenuItem = wcomponents.SideMenuItem(_("Video Services"), None)
            self._generalSection.addItem( self._videoServicesMenuItem)
            self._videoServicesMenuItem.setVisible(False)

        self._layoutMenuItem = wcomponents.SideMenuItem(_("Layout"),
            urlHandlers.UHConfModifDisplay.getURL(self._conf))
        self._generalSection.addItem( self._layoutMenuItem)

        self._participantsMenuItem = wcomponents.SideMenuItem(_("Participants"),
            urlHandlers.UHConfModifParticipants.getURL( self._conf ) )
        self._generalSection.addItem( self._participantsMenuItem)

        self._evaluationMenuItem = wcomponents.SideMenuItem(_("Evaluation"),
            urlHandlers.UHConfModifEvaluation.getURL( self._conf ) )
        self._generalSection.addItem( self._evaluationMenuItem)

        self._sideMenu.addSection(self._generalSection)

        # The section containing all advanced options
        self._advancedOptionsSection = wcomponents.SideMenuSection(_("Advanced options"))

        self._listingsMenuItem = wcomponents.SideMenuItem(_("Lists"),
            urlHandlers.UHConfModifListings.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._listingsMenuItem)

        self._ACMenuItem = wcomponents.SideMenuItem(_("Protection"),
            urlHandlers.UHConfModifAC.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._ACMenuItem)

        self._reviewingMenuItem = wcomponents.SideMenuItem(_("Reviewing"),
            urlHandlers.UHConfModifReviewingAccess.getURL( target = self._conf ) )
        self._advancedOptionsSection.addItem( self._reviewingMenuItem)

        self._toolsMenuItem = wcomponents.SideMenuItem(_("Tools"),
            urlHandlers.UHConfModifTools.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._toolsMenuItem)

        self._logMenuItem = wcomponents.SideMenuItem(_("Logs"),
            urlHandlers.UHConfModifLog.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._logMenuItem)

        self._sideMenu.addSection(self._advancedOptionsSection)

        #we decide which side menu item appear and which don't
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCAbstractManager, RCReviewingStaff
        from MaKaC.webinterface.rh.collaboration import RCVideoServicesManager, RCCollaborationAdmin, RCCollaborationPluginAdmin

        canModify = self._conf.canModify(self._rh.getAW())
        isReviewingStaff = RCReviewingStaff.hasRights(self._rh)
        isPRM = RCPaperReviewManager.hasRights(self._rh)
        isAM = RCAbstractManager.hasRights(self._rh)
        isRegistrar = self._conf.canManageRegistration(self._rh.getAW().getUser())

        if not canModify:
            self._generalSettingsMenuItem.setVisible(False)
            self._timetableMenuItem.setVisible(False)
            self._materialMenuItem.setVisible(False)
            self._programMenuItem.setVisible(False)
            self._participantsMenuItem.setVisible(False)
            self._listingsMenuItem.setVisible(False)
            self._layoutMenuItem.setVisible(False)
            self._ACMenuItem.setVisible(False)
            self._toolsMenuItem.setVisible(False)
            self._logMenuItem.setVisible(False)
            self._evaluationMenuItem.setVisible(False)

        if not (info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive() and canModify):
            self._roomBookingMenuItem.setVisible(False)

        if not (self._conf.hasEnabledSection("cfa") and (canModify or isAM)):
            self._abstractMenuItem.setVisible(False)

        if not (canModify or isPRM):
            self._contribListMenuItem.setVisible(False)

        if not (self._conf.hasEnabledSection("regForm") and (canModify or isRegistrar)):
            self._regFormMenuItem.setVisible(False)

        if not (self._conf.getType() == "conference" and self._conf.hasEnabledSection('paperReviewing') and (canModify or isReviewingStaff)):
            self._reviewingMenuItem.setVisible(False)
        else: #reviewing tab is enabled
            if isReviewingStaff and not canModify:
                self._reviewingMenuItem.setVisible(True)

        if not (canModify or
                RCVideoServicesManager.hasRights(self._rh, 'any') or
                RCCollaborationAdmin.hasRights(self._rh) or RCCollaborationPluginAdmin.hasRights(self._rh, plugins = 'any')):
            self._videoServicesMenuItem.setVisible(False)

        #we hide the Advanced Options section if it has no items
        if not self._advancedOptionsSection.hasVisibleItems():
            self._advancedOptionsSection.setVisible(False)

        # we disable the Participants section for events of type conference
        if self._conf.getType() == 'conference':
            self._participantsMenuItem.setVisible(False)

        # make sure that the section evaluation is always activated
        # for all conferences
        self._conf.enableSection("evaluation")
        wf = self._rh.getWebFactory()
        if wf:
            wf.customiseSideMenu( self )

    def _setActiveSideMenuItem( self ):
        pass

    def _applyFrame( self, body ):
        frame = wcomponents.WConferenceModifFrame( self._conf, self._getAW())

        sideMenu = self._sideMenu.getHTML()

        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
              "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
              "event": "Conference",
              "sideMenu": sideMenu }
        wf = self._rh.getWebFactory()
        if wf:
            p["event"]=wf.getName()
        return frame.getHTML( body, **p )

    def _getBody( self, params ):
        self._createSideMenu()
        self._setActiveSideMenuItem()

        return self._applyFrame( self._getPageContent( params ) )

    def _getTabContent( self, params ):
        return "nothing"

    def _getPageContent( self, params ):
        return "nothing"

class WPConferenceModifAbstractBase( WPConferenceModifBase ):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabCFA = self._tabCtrl.newTab( "cfasetup", _("Setup"), urlHandlers.UHConfModifCFA.getURL( self._conf ) )
        self._tabCFAPreview = self._tabCtrl.newTab("cfapreview", _("Preview"), urlHandlers.UHConfModifCFAPreview.getURL(self._conf))
        self._tabAbstractList = self._tabCtrl.newTab( "abstractList", _("List of Abstracts"), urlHandlers.UHConfAbstractManagment.getURL( self._conf ) )
        self._tabBOA = self._tabCtrl.newTab("boa", _("Book of Abstracts Setup"), urlHandlers.UHConfModAbstractBook.getURL(self._conf))

        if not self._conf.hasEnabledSection("cfa"):
            self._tabBOA.disable()
            self._tabCFA.disable()
            self._tabAbstractList.disable()
            self._tabCFAPreview.disable()

        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()

        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

    def _setActiveSideMenuItem(self):
        self._abstractMenuItem.setActive()

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveTab(self):
        pass

class WConfModifClosed(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["closedIconURL"] = Config.getInstance().getSystemIconURL("closed")
        return vars

############# Start of old collaboration related ##############################
class WBookingSystems( wcomponents.WTemplated ):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["vrvs"] = "VRVS"
        vars["mcu"] = "MCU"
        return vars

class WBookingsList( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf= conference


    def _getBookingsHTML( self, booking ):
        url = urlHandlers. UHBookingDetail.getURL(booking)
        Title = booking.getTitle()
        Description = booking.getDescription()
        Starts = str(booking.getStartingDate().strftime("%Y-%m-%d") + ' at ' + booking.getStartingDate().strftime("%H:%M"))
        Ends = str(booking.getEndingDate().strftime("%Y-%m-%d") + ' at ' + booking.getEndingDate().strftime("%H:%M"))
        System = booking.getSystem()
        html ="""

            <tr>
                <td valign="top" nowrap><input type="radio" name="bookings" value="%s"></td>
                <td valign="top" nowrap class="abstractLeftDataCell"><a href=%s>%s</a></td>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
            </tr>

               """  %(self.htmlText(booking.getId()),
                    quoteattr(str(url)), self.htmlText(Title),
                    self.htmlText(Description),
                    self.htmlText(Starts), self.htmlText(Ends),
                    self.htmlText(System) or "&nbsp;")
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        l=[]
        for b in self._conf.getBookingsList(True):
            l.append(self._getBookingsHTML(b))
        vars["bookings"] = "".join(l)
        vars["numBookings"]= str(len(l))
        vars["actionPostURL"]=quoteattr(str(urlHandlers.UHConfModifBookingAction.getURL(self._conf)))
        return vars

class WPConfModifBookings( WPConferenceModifBase ):

    def __init__(self, rh, conf, bs):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._bs = bs

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        p={}
        if self._bs.strip() == "":
            wc = WConfModifBookings( self._conf )
            return wc.getHTML(p)
        elif self._bs.strip()=="VRVS":
            wc = WBookingsWarning(self._conf)
            return wc.getHTML(p)
        elif self._bs.strip()=="MCU":
            wc = importPlugin("Collaboration", "Hermes", "CreateComponent")(self._conf)
            if (wc == None):
                wc= WBookingsNotYetAvailable(self._conf)
            return wc.getHTML(p)

class WConfModifBookings( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf= conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        wc1 = WBookingSystems()
        wc2 = WBookingsList(self._conf)
        vars["bookingSystems"] = wc1.getHTML()
        vars["listOfBookings"] = wc2.getHTML()
        vars["bookSystemURL"] =quoteattr(str(urlHandlers.UHConfModifBookings.getURL(self._conf)))
        return vars

class WBookings (wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf= conf

    def getVars (self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"], vars["description"] = self._conf.getTitle(), self._conf.getDescription()
        now = nowutc()
        vars["sDay"] = now.day
        vars["sMonth"] = now.month
        vars["sYear"] = now.year
        vars["sHour"] = ""
        vars["sMinute"] = ""
        vars["eDay"] = now.day
        vars["eMonth"] = now.month
        vars["eYear"] = now.year
        vars["eHour"], vars["eMinute"] = "", ""
        if self._conf.getLocation() and self._conf.getRoom():
            location = self._conf.getLocation()
            room = self._conf.getRoom()
            vars["locationRoom"] = location.getName() + " - " + room.getName()
        else: vars["locationRoom"] = ""
        vars["event_type"] = ""
        vars["calendarIconURL"] = Config.getInstance().getSystemIconURL("calendar")
        vars["calendarSelectURL"] = urlHandlers.UHSimpleCalendar.getURL()
        vars["comments"]=""
        return vars

class WHERMESParticipantList (wcomponents.WTemplated):

      pass

class WHERMESParticipantCreation (wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars (self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["participantName"] = ""
        vars["participantIpAddress"] = ""
        return vars

class WPBookingsHERMES (WPConfModifBookings):

    def __init__( self, rh, conf ):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        p={"UserEmail": self._getAW().getUser().getEmail()}
        wc = WBookingsHERMES (self._conf)
        return wc.getHTML(p)

class WPBookingsVRVS(WPConfModifBookings):

    def __init__( self, rh, conf ):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        if self._getAW().getUser():
            p={"supportEmail": self._getAW().getUser().getEmail()}
        else:
            p={"supportEmail": ""}
        wc = WBookingsVRVS(self._conf)
        return wc.getHTML(p)

class WBookingsVRVS(WBookings):

    def __init__( self, conference ):
        self._conf= conference

    def getVars( self ):
        vars = WBookings.getVars( self )
        vars["vrvsLogin"] = ""
        vars["vrvsPasswd"] = ""
        vars["vrvsCommunity"] = ""
        vars["vrvsEmailAddress"] = ""
        vars["accessPasswd"] = ""
        vars["postURL"] = quoteattr(str(urlHandlers.UHPerformBookingsVRVS.getURL(self._conf)))
        vars["sday"] = ""
        for i in range(1,32):
            sel = ""
            if i == self._conf.getStartDate().day:
                sel = " selected"
            vars["sday"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,2),sel,string.zfill(i,2))
        vars["smonth"] = ""
        for i in range(1,13):
            sel = ""
            if i == self._conf.getStartDate().month:
                sel = " selected"
            vars["smonth"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(i,sel,datetime(1900,i,1).strftime("%B"))
        vars["syear"] = ""
        for i in range(self._conf.getStartDate().year - 1,self._conf.getStartDate().year + 2):
            sel = ""
            if i == self._conf.getStartDate().year:
                sel = " selected"
            vars["syear"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,4),sel,string.zfill(i,4))
        vars["shouroptions"] = ""
        for i in range(1,24):
            sel = ""
            if i == self._conf.getStartDate().hour:
                sel = " selected"
            vars["shouroptions"] += "<option value=\"%02d\"%s>%02d\n" % (i,sel,i)
        vars["sminuteoptions"] = ""
        for i in ["00","30"]:
            vars["sminuteoptions"] += """<option value="%s">%s\n""" % (i,i)
        vars["eday"] = ""
        for i in range(1,32):
            sel = ""
            if i == self._conf.getEndDate().day:
                sel = " selected"
            vars["eday"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,2),sel,string.zfill(i,2))
        vars["emonth"] = ""
        for i in range(1,13):
            sel = ""
            if i == self._conf.getEndDate().month:
                sel = " selected"
            vars["emonth"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(i,sel,datetime(1900,i,1).strftime("%B"))
        vars["eyear"] = ""
        for i in range(self._conf.getEndDate().year - 1, self._conf.getEndDate().year + 2):
            sel = ""
            if i == self._conf.getEndDate().year:
                sel = " selected"
            vars["eyear"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,4),sel,string.zfill(i,4))
        vars["ehouroptions"] = ""
        for i in range(1,24):
            sel = ""
            if i == self._conf.getEndDate().hour:
                sel = " selected"
            vars["ehouroptions"] += "<option value=\"%02d\"%s>%02d\n" % (i,sel,i)
        vars["eminuteoptions"] = ""
        for i in ["28","58"]:
            if i == "58":
                sel = " selected"
            else:
                sel = ""
            vars["eminuteoptions"] += """<option value="%s"%s>%s\n""" % (i,sel,i)
        return vars

class WPBookingsVRVSPerformed(WPConferenceModifBase):

    def __init__( self, rh, conf, booking ):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._booking = booking

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        p={ \
"virtualRoom": self._booking.getVirtualRoom(), \
"listOfBookings": quoteattr(str(urlHandlers.UHConfModifBookings.getURL(self._conf)))}
        wc = WBookingsVRVSPerformed(self._booking)
        return wc.getHTML(p)

class WPBookingsDetail(WPConferenceModifBase):

    def __init__( self, rh, conf, booking ):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._conf = conf
        self._booking=booking

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        if self._booking.getSystem()=="VRVS":
            p={ \
"virtualRoom": self._booking.getVirtualRoom(), \
"listOfBookings": quoteattr(str(urlHandlers.UHConfModifBookings.getURL(self._conf)))}
            wc = WBookingsVRVSDetail(self._booking)
            return wc.getHTML(p)
        elif self._booking.getSystem()=="HERMES":
            wc = importPlugin("Collaboration", "Hermes", "ShowComponent")(self._conf, self._booking)
            if (wc == None):
                wc= WBookingsNotYetAvailable(self._conf)
            return wc.getHTML()

class WBookingsVRVSPerformed(WBookingsVRVS):

    def __init__(self, booking):
        self._b = booking

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["vrvsLogin"] = self._b.getVRVSuser()
        vars["vrvsCommunity"] = self._b.getCommunity()
        vars["accessPasswd"] = self._b.getProtectionPasswd()
        vars["title"] = self._b.getTitle()
        vars["description"] = self._b.getDescription()
        vars["sDate"] = self._b.getStartingDate().strftime("%Y-%m-%d")
        vars["sTime"] = self._b.getStartingDate().strftime("%H:%M")
        vars["eDate"] = self._b.getEndingDate().strftime("%Y-%m-%d")
        vars["eTime"] = self._b.getEndingDate().strftime("%H:%M")
        vars["locationRoom"] = self._b.getRoom()
        vars["supportEmail"] = self._b.getSupportEmail()
        vars["event_type"] = ""
        vars["comments"]= self._b.getComments()
        if vars["accessPasswd"]!="":
            vars["protectionStatus"]= _("Active (password sent in email confirmation)")
        else:
            vars["protectionStatus"]= _("Not Active")
        return vars

class WBookingsVRVSDetail(WBookingsVRVSPerformed):

    def getVars(self):
        vars = WBookingsVRVSPerformed.getVars(self)
        vars ["starting"] = self._b.getStartingDate().strftime("%d-%b-%Y at %H:%M")
        vars ["ending"] =  self._b.getEndingDate().strftime("%d-%b-%Y at %H:%M")
        return vars

class WPBookingsVRVSserverError(WPConferenceModifBase):

    def __init__( self, rh, conf, response):
        WPConferenceModifBase.__init__(self, rh, conf)
        self.response= response

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        p={}
        wc = WBookingsVRVSserverError(self._conf)
        p = { "bookingError": self.response[1] }
        return wc.getHTML(p)

class WBookingsVRVSserverError(WBookings):

    def getVars(self):
        vars = WBookings.getVars(self)
        vars["gobackURL"] = quoteattr(str(urlHandlers.UHBookingsVRVS.getURL(self._conf)))
        return vars

class WPBookingsModifDeleteSuccess(WPConferenceModifBase):

    def __init__( self, rh, conf, msg):
        WPConferenceModifBase.__init__(self, rh, conf)
        self.msg = msg[0] + ": " + msg[1]

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

    def _getTabContent( self, params ):
        p={}
        wc = WBookingsModifDeleteSuccess(self._conf)
        p = { "DeleteMessage": self.msg}
        return wc.getHTML(p)

class WBookingsModifDeleteSuccess(WBookings):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["gobackURL"] = quoteattr(str(urlHandlers.UHConfModifBookings.getURL(self._conf)))
        return vars

class WBookingsNotYetAvailable(WBookings):

    def getVars( self ):
        vars = WBookings.getVars( self )
        vars["gobackURL"] = quoteattr(str(urlHandlers.UHConfModifBookings.getURL(self._conf)))
        return vars

# can be generalize for other systems

class WBookingsWarning (wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["bookingsVRVSURL"] = quoteattr(str(urlHandlers.UHBookingsVRVS.getURL(self._conf)))
        return vars

class WPConfModifBookingListBase( WPConferenceModifBase ):

    def _setActiveTab( self ):
        self._tabVideoServices.setActive()

class WPBookingsModifDeleteConfirmation(WPConfModifBookingListBase):

    def __init__(self,rh, conf, bookingList):
        WPConfModifBookingListBase.__init__(self,rh,conf)
        self._bookingList = bookingList

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        bks=[]
        for bk in self._bookingList:
            bks.append("<li><i>%s</i></li>"%self._conf.getBookingById(bk).getTitle())
        msg= _(""" _("Are you sure you want to delete the following booking(s)")?<br><ul>%s</ul>
        <font color="red">( _("note you will permanently remove the booking(s) and all its related information") )</font><br>""")%("".join(bks))
        url=urlHandlers.UHConfModifBookingPerformDeletion.getURL(self._conf)
        return wc.getHTML(msg,url,{"bookings":self._bookingList})

class WPBookingsModifDeleteError(WPConfModifBookingListBase):

    def __init__(self, rh, conf, deldata):
        WPConfModifBookingListBase.__init__(self,rh,conf)
        self._deldata = deldata

    def _getTabContent(self,params):
        wc = WBookingsModifDeleteError(self._conf)
        return wc.getHTML({"ErrorReason":self._deldata[1]})

class WBookingsModifDeleteError(WBookingsVRVSPerformed):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["gobackURL"] = quoteattr(str(urlHandlers.UHConfModifBookings.getURL(self._conf)))
        return vars


class WConfModifMainData(wcomponents.WTemplated):

    def __init__(self,conference,mfRegistry,ct,rh):
        self._conf=conference
        self.__mfr=mfRegistry
        self._ct=ct
        self._rh = rh

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        type = vars["type"]
        defaultStyle = _("""--_("not set")--""")
        defStyle = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getDefaultStyle()
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        defaultStyle = styleMgr.getStylesheetName(defStyle)
        vars["defaultStyle"] = defaultStyle
        visibility = self._conf.getVisibility()
        categpath = self._conf.getCategoriesPath()[0]
        categpath.reverse()
        if visibility > len(categpath):
            vars["visibility"] = _("Everywhere")
        elif visibility == 0:
            vars["visibility"] = _("Nowhere")
        else:
            categId = categpath[visibility-1]
            cat = conference.CategoryManager().getById(categId)
            vars["visibility"] = cat.getName()
        vars["dataModificationURL"]=quoteattr(str(urlHandlers.UHConfDataModif.getURL(self._conf)))
        vars["addTypeURL"]=urlHandlers.UHConfAddContribType.getURL(self._conf)
        vars["removeTypeURL"]=urlHandlers.UHConfRemoveContribType.getURL(self._conf)
        vars["title"]=self._conf.getTitle()
        if isStringHTML(self._conf.getDescription()):
            vars["description"] = self._conf.getDescription()
        elif self._conf.getDescription():
            vars["description"] = self._conf.getDescription()
        else:
            vars["description"] = ""

        ###################################
        # Fermi timezone awareness        #
        ###################################
        tz = self._conf.getTimezone()
        vars["timezone"] = tz
        vars["startDate"]=formatDateTime(self._conf.getAdjustedStartDate())
        vars["endDate"]=formatDateTime(self._conf.getAdjustedEndDate())
        ###################################
        # Fermi timezone awareness(end)   #
        ###################################
        vars["chairText"] = self.htmlText(self._conf.getChairmanText())
        place=self._conf.getLocation()

        vars["locationName"]=vars["locationAddress"]=""
        if place:
            vars["locationName"]=self.htmlText(place.getName())
            vars["locationAddress"]=self.htmlText(place.getAddress())
        room=self._conf.getRoom()
        vars["locationRoom"]=""
        if room:
            vars["locationRoom"]=self.htmlText(room.getName())
        if isStringHTML(self._conf.getContactInfo()):
            vars["contactInfo"]=self._conf.getContactInfo()
        else:
            vars["contactInfo"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._conf.getContactInfo()
        vars["newChairURL"]=quoteattr(str(urlHandlers.UHConfModChairNew.getURL(self._conf)))
        vars["remChairsURL"]=quoteattr(str(urlHandlers.UHConferenceRemoveChairs.getURL(self._conf)))
        vars["searchChairURL"]=quoteattr(str(urlHandlers.UHConfModifSelectChairs.getURL(self._conf)))
        vars["chairs"] = self._conf.getChairList()
        vars["supportEmailCaption"] = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getSupportEmailCaption()
        vars["supportEmail"] = _("""--_("not set")--""")
        if self._conf.hasSupportEmail():
            vars["supportEmail"] = self.htmlText(self._conf.getSupportEmail())
        typeList = []
        for type in self._conf.getContribTypeList():
            typeList.append("""<input type="checkbox" name="types" value="%s"><a href="%s">%s</a><br>
<table><tr><td width="30"></td><td><font><pre>%s</pre></font></td></tr></table>"""%( \
                type.getId(), \
                str(urlHandlers.UHConfEditContribType.getURL(type)), \
                type.getName(), \
                type.getDescription()))
        vars["typeList"] = "".join(typeList)
        #if not self._conf.isClosed():
        #    vars["status"] = "close"
        #    vars["statusURL"] = urlHandlers.UHConferenceClose.getURL(self._conf)
        #else:
        #    vars["status"] = "open"
        #    vars["statusURL"] = urlHandlers.UHConferenceOpen.getURL(self._conf)
        #-----Setting of the sections of the conference--------
        vars["enablePic"]=Config.getInstance().getSystemIconURL( "enabledSection" )
        vars["disablePic"]=Config.getInstance().getSystemIconURL( "disabledSection" )
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")
        lsect=[]
        for sect in conference.ConfSectionsMgr().getSectionKeys():

            # Videoconference section should not appear in conferences
            if sect in ['collaboration', 'paperReviewing','videoconference']:
                continue

            url=urlHandlers.UHConfSectionsSettings.getURL(self._conf)
            url.addParam("sectionId", sect)
            url=quoteattr("%s#sections"%str(url))
            if self._conf.hasEnabledSection(sect):
                icon=vars["enablePic"]
                textIcon=enabledText
            else:
                icon=vars["disablePic"]
                textIcon=disabledText
            lsect.append("""
                            <tr>
                                <td>
                                    <a href=%s><img src=%s alt="%s" class="imglink"></a>&nbsp;<a href=%s>%s</a>
                                </td>
                            </tr>
                            """%(url, \
                                icon, \
                                textIcon, \
                                url, \
                                conference.ConfSectionsMgr().getSection(sect)))
        vars["sections"]="".join(lsect)
        #------------------------------------------------------
        vars["reportNumbersTable"]=wcomponents.WReportNumbersTable(self._conf).getHTML()
        vars["eventType"] = self._conf.getType()
        if vars["eventType"] == "simple_event":
            vars["eventType"] = "lecture"
        vars["keywords"] = self._conf.getKeywords()
        vars["shortURL"] =  ""
        if self._conf.getUrlTag() and Config.getInstance().getShortEventURL():
            vars["shortURL"] =  Config.getInstance().getShortEventURL() + self._conf.getUrlTag()
        vars["screenDatesURL"] = urlHandlers.UHConfScreenDatesEdit.getURL(self._conf)
        ssdate = self._conf.getAdjustedScreenStartDate().strftime("%A %d %B %Y %H:%M")
        if self._conf.getScreenStartDate() == self._conf.getStartDate():
            ssdate += _(""" <i> _("(normal)")</i>""")
        else:
            ssdate += _(""" <font color='red'>_("(modified)")</font>""")
        sedate = self._conf.getAdjustedScreenEndDate().strftime("%A %d %B %Y %H:%M")
        if self._conf.getScreenEndDate() == self._conf.getEndDate():
            sedate += _(""" <i> _("(normal)")</i>""")
        else:
            sedate += _(""" <font color='red'> _("(modified)")</font>""")
        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
        vars["screenDates"] = "%s -> %s" % (ssdate, sedate)

        return vars
############# End of old collaboration related ##############################

class WPConferenceModificationClosed( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

    def _getPageContent( self, params ):
        wc = WConfModifClosed()
        pars = { "type": params.get("type","") }
        return wc.getHTML( pars )


class WPConferenceModification( WPConferenceModifBase ):

    def __init__(self, rh, target, ct=None):
        WPConferenceModifBase.__init__(self, rh, target)
        self._ct = ct

    def _setActiveSideMenuItem( self ):
        self._generalSettingsMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WConfModifMainData( self._conf, ConfMFRegistry(), self._ct, self._rh )
        pars = { "type": params.get("type","") , "conferenceId": self._conf.getId()}
        return wc.getHTML( pars )

class WConfModScreenDatesEdit(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfScreenDatesEdit.getURL(self._conf)))
        ###################################
        # Fermi timezone awareness        #
        ###################################
        csd = self._conf.getAdjustedStartDate()
        ced = self._conf.getAdjustedEndDate()
        ###################################
        # Fermi timezone awareness(end)   #
        ###################################
        vars["conf_start_date"]=self.htmlText(csd.strftime("%A %d %B %Y %H:%M"))
        vars["conf_end_date"]=self.htmlText(ced.strftime("%A %d %B %Y %H:%M"))
        vars["start_date_own_sel"]=""
        vars["start_date_conf_sel"]=" checked"
        vars["sDay"],vars["sMonth"],vars["sYear"]=csd.day,csd.month,csd.year
        vars["sHour"],vars["sMin"]=csd.hour,csd.minute
        if self._conf.getScreenStartDate() != self._conf.getStartDate():
            vars["start_date_own_sel"]=" checked"
            vars["start_date_conf_sel"]=""
            sd=self._conf.getAdjustedScreenStartDate()
            vars["sDay"]=quoteattr(str(sd.day))
            vars["sMonth"]=quoteattr(str(sd.month))
            vars["sYear"]=quoteattr(str(sd.year))
            vars["sHour"]=quoteattr(str(sd.hour))
            vars["sMin"]=quoteattr(str(sd.minute))
        vars["end_date_own_sel"]=""
        vars["end_date_conf_sel"]=" checked"
        vars["eDay"],vars["eMonth"],vars["eYear"]=ced.day,ced.month,ced.year
        vars["eHour"],vars["eMin"]=ced.hour,ced.minute
        if self._conf.getScreenEndDate() != self._conf.getEndDate():
            vars["end_date_own_sel"]=" checked"
            vars["end_date_conf_sel"]=""
            ed=self._conf.getAdjustedScreenEndDate()
            vars["eDay"]=quoteattr(str(ed.day))
            vars["eMonth"]=quoteattr(str(ed.month))
            vars["eYear"]=quoteattr(str(ed.year))
            vars["eHour"]=quoteattr(str(ed.hour))
            vars["eMin"]=quoteattr(str(ed.minute))
        return vars

class WPScreenDatesEdit(WPConferenceModification):

    def _getPageContent( self, params ):
        wc = WConfModScreenDatesEdit(self._conf)
        return wc.getHTML()

class WConferenceDataModificationAdditionalInfo(wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["contactInfo"] = self._conf.getContactInfo()
        return vars


class WConferenceDataModification(wcomponents.WTemplated):

    def __init__( self, conference, rh ):
        self._conf = conference
        self._rh = rh

    def _getVisibilityHTML(self):
        visibility = self._conf.getVisibility()
        topcat = self._conf.getOwnerList()[0]
        level = 0
        selected = ""
        if visibility == 0:
            selected = "selected"
        vis = [ _("""<option value="0" %s> _("Nowhere")</option>""") % selected]
        while topcat:
            level += 1
            selected = ""
            if level == visibility:
                selected = "selected"
            if topcat.getId() != "0":
                from MaKaC.common.TemplateExec import truncateTitle
                vis.append("""<option value="%s" %s>%s</option>""" % (level, selected, truncateTitle(topcat.getName(), 120)))
            topcat = topcat.getOwner()
        selected = ""
        if visibility > level:
            selected = "selected"
        vis.append( _("""<option value="999" %s> _("Everywhere")</option>""") % selected)
        vis.reverse()
        return "".join(vis)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        navigator = ""
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        type = self._conf.getType()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(self._conf.getTimezone())
        stylesheets=styleMgr.getStylesheetListForEventType(type)
        styleoptions = ""
        defStyle = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getDefaultStyle()
        if defStyle not in stylesheets:
            defStyle = ""
        for stylesheet in stylesheets:
            if stylesheet == defStyle or (defStyle == "" and stylesheet == "static"):
                selected = "selected"
            else:
                selected = ""
            styleoptions += "<option value=\"%s\" %s>%s</option>" % (stylesheet,selected,styleMgr.getStylesheetName(stylesheet))
        vars["conference"] = self._conf
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()
        vars["styleOptions"] = styleoptions
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        types = [ "conference" ]
        for fact in wr.getFactoryList():
            types.append(fact.getId())
        vars["types"] = ""
        for id in types:
            typetext = id
            if typetext == "simple_event":
                typetext = "lecture"
            if self._conf.getType() == id:
                vars["types"] += "<option value=\"%s\" selected>%s" % (id,typetext)
            else:
                vars["types"] += "<option value=\"%s\">%s" % (id,typetext)
        vars["title"] = quoteattr( self._conf.getTitle() )
        vars["description"] = self._conf.getDescription()
        vars["keywords"] = self._conf.getKeywords()
        tz = self._conf.getTimezone()
        vars["sDay"] = str( self._conf.getAdjustedStartDate(tz).day )
        vars["sMonth"] = str( self._conf.getAdjustedStartDate(tz).month )
        vars["sYear"] = str( self._conf.getAdjustedStartDate(tz).year )
        vars["sHour"] = str( self._conf.getAdjustedStartDate(tz).hour )
        vars["sMinute"] = str( self._conf.getAdjustedStartDate(tz).minute )
        vars["eDay"] = str( self._conf.getAdjustedEndDate(tz).day )
        vars["eMonth"] = str( self._conf.getAdjustedEndDate(tz).month )
        vars["eYear"] = str( self._conf.getAdjustedEndDate(tz).year )
        vars["eHour"] = str( self._conf.getAdjustedEndDate(tz).hour )
        vars["eMinute"] = str( self._conf.getAdjustedEndDate(tz).minute )
        vars["chairText"] = quoteattr( self._conf.getChairmanText() )
        vars["orgText"] = quoteattr( self._conf.getOrgText() )
        vars["visibility"] = self._getVisibilityHTML()
        vars["shortURLTag"] = quoteattr( self._conf.getUrlTag() )
        locName, locAddress, locRoom = "", "", ""
        location = self._conf.getLocation()
        if location:
            locName = location.getName()
            locAddress = location.getAddress()
        room = self._conf.getRoom()
        if room:
            locRoom = room.getName()
        vars["locator"] = self._conf.getLocator().getWebForm()

        vars["locationAddress"] = locAddress

        vars["supportCaption"] = quoteattr(displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getSupportEmailCaption())
        vars["supportEmail"] = quoteattr( self._conf.getSupportEmail() )
        vars["locator"] = self._conf.getLocator().getWebForm()
        vars["event_type"] = ""
        vars["navigator"] = navigator
        eventType = self._conf.getType()
        if eventType == "conference":
            vars["additionalInfo"] = WConferenceDataModificationAdditionalInfo(self._conf).getHTML(vars)
        else:
            vars["additionalInfo"] = ""
        return vars


class WPConfDataModif( WPConferenceModification ):

    def _getPageContent( self, params ):
        p = WConferenceDataModification( self._conf, self._rh )
        pars = {
        "postURL": urlHandlers.UHConfPerformDataModif.getURL(),
        "calendarIconURL": Config.getInstance().getSystemIconURL("calendar"),
        "calendarSelectURL":  urlHandlers.UHSimpleCalendar.getURL(),
        "type": params.get("type") }
        return p.getHTML( pars )


class WPModChairNew( WPConferenceModification ):

    def _getPageContent(self,params):
        caption= _("Adding a new chair")
        wc=wcomponents.WConfModParticipEdit(title=caption)
        params["postURL"]=urlHandlers.UHConfModChairNew.getURL(self._conf)
        params["addToManagersList"] = _("""<tr>
            <td nowrap class="titleCellTD">
                <span class="titleCellFormat"> _("Manager")</span>
            </td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                <input type="checkbox" name="manager"> _("Give management rights to the chairperson").</td>
        </tr>
        <tr>
            <td class="titleCellTD" nowrap="nowrap"></td>
            <td class="blacktext" bgcolor="white" valign="top" width="100%"><i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have an Indico account, he or she will be sent an email asking to create an account. After the account creation the user will automatically be given management rights.")</i></td>
        </tr>
            </td>
        </tr>""")
        return wc.getHTML( params )


class WPModChairEdit( WPConferenceModification ):

    def _getPageContent(self,params):
        caption= _("Edit chairperson data")
        chair=part=params["chair"]
        wc=wcomponents.WConfModParticipEdit(part=chair,title=caption)
        params["postURL"]=urlHandlers.UHConfModChairEdit.getURL(chair)
        av = user.AvatarHolder().match({"email":chair.getEmail()})
        if (not av or not av[0] in self._conf.getManagerList()) and not chair.getEmail() in self._conf.getAccessController().getModificationEmail():
            params["addToManagersList"] = _("""<tr>
                <td nowrap class="titleCellTD">
                    <span class="titleCellFormat">Manager</span>
                </td>
                <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                    <input type="checkbox" name="manager"> _("Give management rights to the chairperson").</td>
            </tr>
            <tr>
                <td class="titleCellTD" nowrap="nowrap"></td>
                <td class="blacktext" bgcolor="white" valign="top" width="100%"><i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have an Indico account, he or she will be sent an email asking to create an account. After the account creation the user will automatically be given management rights.")</i></td>
            </tr>
                </td>
            </tr>""")
        return wc.getHTML(params)


class WPConfAddMaterial( WPConferenceModification ):

    def __init__( self, rh, conf, mf ):
        WPConferenceModification.__init__( self, rh, conf )
        self._mf = mf

    def _getTabContent( self, params ):
        if self._mf:
            comp = self._mf.getCreationWC( self._conf )
        else:
            comp = wcomponents.WMaterialCreation( self._conf )
        pars = { "postURL": urlHandlers.UHConferencePerformAddMaterial.getURL() }
        return comp.getHTML( pars )


class WScheduleContribution(wcomponents.WTemplated):

    def __init__(self, contrib, insideSession = False):
        self._contrib = contrib
        self._insideSession = insideSession

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        vars['addSubURL'] = urlHandlers.UHContribAddSubCont.getURL(self._contrib)
        if self._insideSession:
            vars['delURL'] = urlHandlers.UHSessionDelSchItems.getURL(self._contrib.getSchEntry())
        else:
            vars['delURL'] = urlHandlers.UHConfDelSchItems.getURL(self._contrib.getSchEntry())
        vars['modifURL'] = urlHandlers.UHConfModSchEditContrib.getURL(self._contrib)
        vars['relocateURL'] = urlHandlers.UHConfModifScheduleRelocate.getURL(self._contrib)
        vars['relocateURL'].addParam("targetDay",self._contrib.getStartDate().strftime("%Y-%m-%d"))
        vars['moveUpURL'] = urlHandlers.UHConfModScheduleMoveEntryUp.getURL(self._contrib.getSchEntry())
        vars['upArrowURL'] = Config.getInstance().getSystemIconURL("upArrow")
        vars['moveDownURL'] = urlHandlers.UHConfModScheduleMoveEntryDown.getURL(self._contrib.getSchEntry())
        vars['downArrowURL'] = Config.getInstance().getSystemIconURL("downArrow")
        vars['subCont'] = self._contrib.getSubContributionList()

        place=""
        if self._contrib.getRoom() is not None and \
                self._contrib.getRoom().getName().strip()!="":
            place="%s: "%self._contrib.getRoom().getName()
        vars['place'] = place

        return vars

    def getHTML(self, params=None):
        return wcomponents.WTemplated.getHTML( self, params )

class WScheduleSlot(wcomponents.WTemplated):

    def __init__(self, slot):

        self._slot = slot
        self._session = slot.getSession()
        self._conf = slot.getConference()

    def getHTML(self, params=None):
        return wcomponents.WTemplated.getHTML( self, params )

class WConfModifScheduleGraphic(wcomponents.WTemplated):

    def __init__(self, conference, aw, timetable, dayList, **params):
        wcomponents.WTemplated.__init__(self, **params)
        self._conf = conference
        self._aw = aw
        self._timetable = timetable
        self._dayList = dayList

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        ################################
        # Fermi timezone awareness     #
        ################################
        tz = self._conf.getTimezone()
        vars["timezone"]= tz
        vars["start_date"]=self._conf.getAdjustedStartDate().strftime("%a %d/%m")
        vars["end_date"]=self._conf.getAdjustedEndDate().strftime("%a %d/%m")
        #################################
        # Fermi timezone awareness(end) #
        #################################
        vars["editURL"]=quoteattr(str(urlHandlers.UHConfModScheduleDataEdit.getURL(self._conf)))

        # the list of days specified by the user through the option box
        vars["daysParam"] = self._dayList
        # the list of days from the timetable
        vars["dayList"]=self._timetable.getDayList()
        # the first day of the list
        vars["dayDate"]=self._dayList[0].getDate()

        vars["addSessionURL"]=urlHandlers.UHConfAddSession.getURL(self._conf)
        vars["addBreakURL"]=urlHandlers.UHConfAddBreak.getURL(self._conf)

        originURL = urlHandlers.UHConfModifSchedule.getURL(self._conf)
        newContribURL = urlHandlers.UHConfModScheduleNewContrib.getURL(self._conf)
        newContribURL.addParam("originURL",originURL)
        newContribURL.addParam("eventType","meeting")
        vars["newContribURL"] = newContribURL
        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()

        vars['ttdata'] = simplejson.dumps(schedule.ScheduleToJson.process(self._conf.getSchedule(), tz))
        vars['eventInfo'] = simplejson.dumps(DictPickler.pickle(self._conf, timezone=tz))

        return vars

class WPConfModifScheduleGraphic( WPConferenceModifBase ):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._session = None
        self._contrib = None

    def _setActiveSideMenuItem( self ):
        self._timetableMenuItem.setActive()

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSPackage('Timetable')

    def _generateTimetable(self):
        tz = self._conf.getTimezone()
        timeTable = timetable.TimeTable(self._conf.getSchedule(), tz)
        #######################################
        # Fermi timezone awareness            #
        #######################################
        sDate = self._conf.getSchedule().getStartDate(tz)
        eDate = self._conf.getSchedule().getEndDate(tz)
        #######################################
        # Fermi timezone awareness(end)       #
        #######################################
        timeTable.setStartDate(sDate)
        timeTable.setEndDate(eDate)
        #timeTable.setStartDayTime(7,0)
        #timeTable.setEndDayTime(21,59)
        timeTable.mapEntryList(self._conf.getSchedule().getEntries())

        return timeTable

    def _getSchedule(self):
        return WConfModifScheduleGraphic( self._conf, self._getAW(), self._timetable, self._days)

    def _getTTPage( self, params ):

        params["session"] = self._session

        days = params.get("days", None)

        timeTable= self._generateTimetable()

        if days == None or days == 'all':
            dayList = timeTable.getDayList()
        else:
            dayList = [timeTable.getDayList()[int(days)]]

        self._days = dayList
        self._timetable = timeTable

        wc = self._getSchedule()
        return wc.getHTML(params)

    def _getPageContent(self, params):
        return self._getTTPage(params)

#------------------------------------------------------------------------------
class WPConfModifSchedule( WPConferenceModifBase ):

    def _setActiveTab( self ):
        self._tabSchedule.setActive()

    #def _getTabContent( self, params ):
    #    wc = WConfModifSchedule( self._conf )
    #    return wc.getHTML(params)

#------------------------------------------------------------------------------

class WPPConfModifScheduleRemoveEtries(WPConfModifSchedule):

    def __init__(self,rh,conference):
        WPConfModifSchedule.__init__(self,rh,conference)

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        msg = _(""" _("Are you sure you want to remove these entries from the time schedule")?<br/>
        <br />
        <br />
        <table width="100%%" align="center">
                <tr>
                    <th bgcolor="#dddddd">item&nbsp;title</th>
                    <th bgcolor="#eeeeee">item&nbsp;type</th>
                    <th bgcolor="#dddddd">action&nbsp;description</th>
                </tr>
        %s
        </table>""")%self._getEntryInfo(params["entries"])
        url = urlHandlers.UHConfModifScheduleEntriesRemove.getURL(self._conf)
        url.addParam("entries",params["entries"])
        return wc.getHTML(msg,url,{})

    def _getEntryInfo(self, entries):
        html = []

        for eId in entries :
            type = ""
            description = ""
            title = ""
            if eId[0:1] == "c" :
                type = "contribution"
                description = _("remove only from time schedule")
                title = self._conf.getContributionById(eId[1:]).getTitle()
            elif eId[0:1] == "u" :
                type = "sub-contribution"
                description = _("remove premanently from contribution")
                index = eId.find("-")
                contrib = self._conf.getContributionById(eId[1:index])
                title = contrib.getSubContributionById(eId[index+1:]).getTitle()
            elif eId[0:1] == "s" :
                type = "session"
                description = _("remove permanently, all inner contributions will be removed from schedule")
                index = eId.find("-")
                title = self._conf.getSessionById(eId[1:index]).getTitle()
            elif eId[0:1] == "l" :
                type = "slot"
                description = _("remove permanently, all inner contributions will be removed from schedule")
                index = eId.find("-")
                title = "session %s : "%eId[1:index]
                title = title + self._conf.getSessionById(eId[1:index]).getSlotById(eId[index+1:]).getTitle()
            elif eId[0:1] == "b" :
                type = "break"
                description = _("remove permanently")
                index = eId.find("-")
                if index == -1 :
                    title = self._conf.getSchedule().getEntryInPos(eId[1:]).getTitle()
                else :
                    index2 = eId.find("-",index+1)
                    title = _("session %s : slot %s : ")%(eId[1:index],eId[index+1:index2])
                    title = title + self._conf.getSessionById(eId[1:index]).getSlotById(eId[index+1:index2]).getSchedule().getEntryInPos(eId[index2+1:]).getTitle()
            text = """
                <tr>
                    <td bgcolor="#dddddd">%s</td>
                    <td bgcolor="#eeeeee">%s</td>
                    <td bgcolor="#dddddd">%s</td>
                </tr>"""%(title, type, description)
            html.append(text)
        return """
                """.join(html)

##############################################################################
#------------------------------------------------------------------------------
class WConfModScheduleDataEdit(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModScheduleDataEdit.getURL(self._conf)))
        #######################################
        # Fermi timezone awareness            #
        #######################################
        csd = self._conf.getAdjustedStartDate()
        ced = self._conf.getAdjustedEndDate()
        #######################################
        # Fermi timezone awareness(end)       #
        #######################################
        vars["sDay"],vars["sMonth"],vars["sYear"]=str(csd.day),str(csd.month),str(csd.year)
        vars["sHour"],vars["sMin"]=str(csd.hour),str(csd.minute)
        vars["eDay"],vars["eMonth"],vars["eYear"]=str(ced.day),str(ced.month),str(ced.year)
        vars["eHour"],vars["eMin"]=str(ced.hour),str(ced.minute)
        return vars

class WPModScheduleDataEdit(WPConfModifSchedule):

    def _getPageContent( self, params ):
        wc = WConfModScheduleDataEdit(self._conf)
        return wc.getHTML()


class WPModScheduleAddContrib(WPConfModifSchedule):

    def __init__(self,rh,conf,targetDay=None):
        WPConfModifSchedule.__init__(self,rh,conf)
        self._targetDay=targetDay

    def _getTabContent( self, params ):
        l=[]
        for contrib in self._conf.getContributionList():
            if contrib.getSession() is not None or \
                contrib.isScheduled() or \
                isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn):
                continue
            l.append(contrib)
        p=wcomponents.WScheduleAddContributions(l,self._targetDay)
        pars={"postURL":urlHandlers.UHConfModScheduleAddContrib.getURL(self._conf)}
        return p.getHTML(pars)

#---------------------------------------------------------------------------

class WPConfAddSession(WPConfModifSchedule):

    def __init__(self,rh,session,day=None):
        WPConfModifSchedule.__init__(self,rh,session)
        self._targetDay=day

    def _getTabContent( self, params ):
        title="Create a new session"
        p=wcomponents.WSessionModEditData(self._conf,self._getAW(),title,self._targetDay)
        params["colorChartIcon"] = Config.getInstance().getSystemIconURL("colorchart")
        params["postURL"]=urlHandlers.UHConfAddSession.getURL(self._conf)
        urlbg=urlHandlers.UHSimpleColorChart.getURL()
        urlbg.addParam("colorCodeTarget", "backgroundColor")
        urlbg.addParam("colorPreviewTarget", "backgroundColorpreview")
        params["bgcolorChartURL"]=urlbg
        params["bgcolor"] = "#F0C060"
        urltext=urlHandlers.UHSimpleColorChart.getURL()
        urltext.addParam("colorCodeTarget", "textColor")
        urltext.addParam("colorPreviewTarget", "textColorpreview")
        params["textcolorChartURL"]=urltext
        params["textcolor"] = "#777777"
        params["textColorToLinks"]=""

        wconvener = wcomponents.WAddPersonModule("convener")
        params["convenerOptions"] = params.get("convenerOptions",self._getPersonOptions())
        params["convener"] = wconvener.getHTML(params)
        return p.getHTML(params)

    def _getPersonOptions(self):
        html = []
        names = []
        text = {}
        html.append("""<option value=""> </option>""")
        for session in self._conf.getSessionList() :
            for convener in session.getConvenerList() :
                name = convener.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="d%s-%s">%s</option>"""%(session.getId(),convener.getId(),name)
                    names.append(name)
        for contribution in self._conf.getContributionList() :
            for speaker in contribution.getSpeakerList() :
                name = speaker.getFullNameNoTitle()
                if not(name in names) :
                    text[name] = """<option value="s%s-%s">%s</option>"""%(contribution.getId(),speaker.getId(),name)
                    names.append(name)
            for author in contribution.getAuthorList() :
                name = author.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="a%s-%s">%s</option>"""%(contribution.getId(),author.getId(),name)
                    names.append(name)
            for coauthor in contribution.getCoAuthorList() :
                name = coauthor.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="c%s-%s">%s</option>"""%(contribution.getId(),coauthor.getId(),name)
                    names.append(name)
        names.sort()
        for name in names:
            html.append(text[name])
        return "".join(html)

#---------------------------------------------------------------------------

class WPNewSessionConvenerSelect( WPConferenceModifBase ):

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._conf,searchAction, forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPNewSessionConvenerNew( WPConferenceModifBase ):

    def __init__(self, rh, conf, params):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._params = params


    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params ):
        p = wcomponents.WNewPerson()
        if self._params.get("formTitle",None) is None :
            self._params["formTitle"] = _("Define new convener")
        if self._params.get("titleValue",None) is None :
            self._params["titleValue"] = ""
        if self._params.get("surNameValue",None) is None :
            self._params["surNameValue"] = ""
        if self._params.get("nameValue",None) is None :
            self._params["nameValue"] = ""
        if self._params.get("emailValue",None) is None :
            self._params["emailValue"] = ""
        if self._params.get("addressValue",None) is None :
            self._params["addressValue"] = ""
        if self._params.get("affiliationValue",None) is None :
            self._params["affiliationValue"] = ""
        if self._params.get("phoneValue",None) is None :
            self._params["phoneValue"] = ""
        if self._params.get("faxValue",None) is None :
            self._params["faxValue"] = ""

        self._params["disabledRole"] = False
        self._params["roleDescription"] = _(""" _("Coordinator")<br> _("Manager")""")
        self._params["roleValue"] = _(""" <input type="checkbox" name="coordinatorControl"> _("Give coordinator rights to the convener").<br>
                                        <input type="checkbox" name="managerControl"> _("Give management rights to the convener").""")
        self._params["disabledNotice"] = True
        self._params["noticeValue"] = _("""<i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the
         user will automatically be given coordinator/management rights.")</i>""")

        formAction = urlHandlers.UHConfNewSessionPersonAdd.getURL(self._conf)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","convener")
        self._params["formAction"] = formAction

        return p.getHTML(self._params)

#---------------------------------------------------------------------------

class WPConfAddBreak( WPConfModifSchedule ):

    def __init__(self,rh,session,day=None):
        WPConfModifSchedule.__init__(self,rh,session)
        self._targetDay=day

    def _getTabContent( self, params ):
        p=wcomponents.WBreakDataModification(self._conf.getSchedule(),targetDay=self._targetDay,conf=self._conf)
        pars={"postURL": urlHandlers.UHConfPerformAddBreak.getURL(self._conf)}
        return p.getHTML( pars )


class WPConfModifyBreak( WPConfModifScheduleGraphic ):

    def __init__( self, rh, conf, schBreak ):
        WPConfModifScheduleGraphic.__init__( self, rh, conf )
        self._break = schBreak

    def _getScheduleContent( self, params ):
        sch=self._conf.getSchedule()
        wc=wcomponents.WBreakDataModification(sch,self._break,conf=self._conf)
        pars = {"postURL":urlHandlers.UHConfPerformModifyBreak.getURL(self._break)}
        params["body"] = wc.getHTML(pars)
        return wcomponents.WBreakModifHeader( self._break, self._getAW() ).getHTML( params )


class WPModSchEditContrib(WPConfModifSchedule):

    def __init__(self,rh,contrib):
        WPConfModifSchedule.__init__(self,rh,contrib.getConference())
        self._contrib=contrib

    def _getTabContent(self,params):
        wc=wcomponents.WSchEditContrib(self._contrib)
        pars={"postURL":urlHandlers.UHConfModSchEditContrib.getURL(self._contrib)}
        return wc.getHTML(pars)


class WSchEditSlot(wcomponents.WTemplated):

    def __init__(self,slotData, errors=[]):
        self._slotData=slotData
        self._errors = errors

    #def _getTitleItemsHTML(self,selected=""):
    #    titles=["", "Mr.", "Mrs.", "Miss.", "Prof.", "Dr."]
    #    res=[]
    #    for t in titles:
    #        sel=""
    #        if t==selected:
    #            sel=" selected"
    #        res.append("""<option value=%s%s>%s</option>"""%(quoteattr(t),sel,self.htmlText(t)))
    #    return "".join(res)

    def _getConvenersHTML(self):
        res=[]
        for conv in self._slotData.getConvenerList():
            tmp= _("""
                    <tr>
                        <td style="border-top:1px solid #777777;border-left:1px solid #777777;" width="100%%">
                            <input type="checkbox" name="sel_conv" value=%s>
                            <input type="hidden" name="conv_id" value=%s>
                        </td>
                        <td style="border-top:1px solid #777777;padding-top:2px" width="100%%">
                            <table border="0" width="95%%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>&nbsp;</td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                        _("Title") <select name="conv_title">%s</select>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                        _("Family name") <input type="text" size="40" name="conv_family_name" value=%s>
                                        _("First name") <input type="text" size="30" name="conv_first_name" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                        _("Affiliation") <input type="text" size="40" name="conv_affiliation" value=%s>
                                        _("Email") <input type="text" size="39" name="conv_email" value=%s>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr><td colspan="3">&nbsp;</td></tr>
                """)%(quoteattr(str(conv.getId())),\
                    quoteattr(str(conv.getId())),\
                    TitlesRegistry.getSelectItemsHTML(conv.getTitle()), \
                    quoteattr(conv.getFamilyName()),\
                    quoteattr(conv.getFirstName()), \
                    quoteattr(conv.getAffiliation()), \
                    quoteattr(conv.getEmail()) )
            res.append(tmp)
        return "".join(res)

    def _getErrorHTML( self, msgList ):
        if not msgList:
            return ""
        return """
            <table align="center" cellspacing="0" cellpadding="0">
                <tr>
                    <td>
                        <table align="center" valign="middle" style="padding:10px; border:1px solid #5294CC; background:#F6F6F6">
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td><font color="red">%s</font></td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
                """%"<br>".join( msgList )

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)

        slot = self._slotData.getSession().getSlotById(self._slotData.getId())
        vars["title"]=self._slotData.getTitle()
        if vars.get("hideSlot","0") == "1" :
            vars["formTitle"] = _("Modify session schedule data")
            vars["slotTitle"] = ""
            vars["updateParentDates"] = """<input type="hidden" name="check" value="2">"""
        else :
            vars["formTitle"] = _("Modify session slot schedule data")
            vars["updateParentDates"] = ""
            vars["slotTitle"] = _("""
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> _("Slot Title")</span></td>
            <td bgcolor="white" width="100%%">&nbsp;%s</td>
        </tr>""")%vars["title"]

        vars["orginURL"] = vars.get("orginURL","")
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModSchEditSlot.getURL(slot)))
        vars["sessionTitle"]=self.htmlText(self._slotData.getSession().getTitle())
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName = "", "", ""
        confTZ = self._slotData._session.getOwner().getTimezone()
        sd = self._slotData.getStartDate().astimezone(timezone(confTZ))
        vars["sDay"] = sd.day
        vars["sMonth"] = sd.month
        vars["sYear"] = sd.year
        vars["sHour"] = sd.hour
        vars["sMinute"] = sd.minute
        vars["durHours"] = (datetime(1900,1,1)+self._slotData.getDuration()).hour
        vars["durMins"] = (datetime(1900,1,1)+self._slotData.getDuration()).minute
        vars["contribDurHours"] = ""
        vars["contribDurMins"] = ""
        if self._slotData.getContribDuration() != None:
            vars["contribDurHours"] = (datetime(1900,1,1)+self._slotData.getContribDuration()).hour
            vars["contribDurMins"] = (datetime(1900,1,1)+self._slotData.getContribDuration()).minute
        if self._slotData.getLocationName() !="":
            defaultDefinePlace = "checked"
            defaultInheritPlace = ""
            locationName = self._slotData.getLocationName()
            locationAddress = self._slotData.getLocationAddress()
        if self._slotData.getRoomName() != "":
            defaultDefineRoom= "checked"
            defaultInheritRoom = ""
            roomName = self._slotData.getRoomName()
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["confPlace"]=""
        confLocation=slot.getOwner().getLocation()
        if confLocation:
            vars["confPlace"]=confLocation.getName()
        vars["locationName"] = locationName
        vars["locationAddress"] = locationAddress
        vars["defaultInheritRoom"] = defaultInheritRoom
        vars["defaultDefineRoom"] = defaultDefineRoom
        vars["confRoom"]=""
        confRoom=slot.getOwner().getRoom()
        if confRoom:
            vars["confRoom"]=confRoom.getName()
        vars["roomName"] = quoteattr(roomName)
        vars["conveners"]=self._getConvenersHTML()
        vars["errors"]=self._getErrorHTML(self._errors)
        vars["parentType"]="conference"
        if self._slotData.getSession() is not None:
            vars["parentType"]="session"
        return vars

class WPModSchEditSlot(WPConfModifSchedule):

    def __init__(self,rh,slotData, errors=[]):
        WPConfModifSchedule.__init__(self,rh,slotData.getSession().getConference())
        self._slotData=slotData
        self._errors = errors

    def _getTabContent(self,params):
        wc=WSchEditSlot(self._slotData, self._errors)
        return wc.getHTML(params)

class WPModSessionMoveConfirmation(WPConfModifSchedule):

    def __init__(self,rh,session):
        WPConfModifSchedule.__init__(self,rh,session.getConference())
        self._session=session
        self._aw = rh._aw

    def _getTabContent(self,params):
        wc=WSessionMoveConfirmation(self._session, self._aw)
        url=urlHandlers.UHConfModSessionMoveConfirmation.getURL(self._session)
        return wc.getHTML({"postURL":url})

class WSessionMoveConfirmation(wcomponents.WTemplated):

    def __init__(self,session, aw):
        self._session = session
        self._aw = aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["calendarIconURL"] = Config.getInstance().getSystemIconURL("calendar")
        vars["calendarSelectURL"] = urlHandlers.UHSimpleCalendar.getURL()
        conf = self._session.getOwner()
        tz = conf.getTimezone()
        sd = self._session.getAdjustedStartDate()
        if sd is not None:
            vars["currentDate"]=sd.strftime("%A %d %B %Y %H:%M")
            vars["sDay"] = sd.day
            vars["sMonth"] = sd.month
            vars["sYear"] = sd.year
            vars["sHour"] = sd.hour
            vars["sMinute"] = sd.minute
        else:
            vars["currentDate"]= _("""--_("no start date")--""")
            vars["sDay"] = "dd"
            vars["sMonth"] = "mm"
            vars["sYear"] = "yyyy"
            vars["sHour"] = "hh"
            vars["sMinute"] = "mm"
        return vars

class WPModSlotRemConfirmation(WPConfModifSchedule):

    def __init__(self,rh,slot):
        WPConfModifSchedule.__init__(self,rh,slot.getConference())
        self._slot=slot

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        slotCaption="on %s %s-%s"%(
            self._slot.getAdjustedStartDate().strftime("%A %d %B %Y"),
            self._slot.getAdjustedStartDate().strftime("%H:%M"),
            self._slot.getAdjustedEndDate().strftime("%H:%M"))
        if self._slot.getTitle()!="":
            slotCaption=""" "%s" (%s) """%(self._slot.getTitle(),slotCaption)

        msg= _("""Are you sure you want to delete the slot %s
        of the session "%s" (note that any contribution scheduled
        inside will be unscheduled)?""")%(slotCaption,
            self._slot.getSession().getTitle())
        url=urlHandlers.UHConfModSlotRem.getURL(self._slot)
        return wc.getHTML(msg,url,{})


class WPModSessionRemConfirmation(WPConfModifSchedule):

    def __init__(self,rh,session):
        WPConfModifSchedule.__init__(self,rh,session.getConference())
        self._session=session

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg= _("""Are you sure you want to delete the session "%s"
        (note that any contribution scheduled
        inside will be unscheduled)?""")%(self._session.getTitle())
        url=urlHandlers.UHConfModSessionRem.getURL(self._session)
        return wc.getHTML(msg,url,{})

class WConfModifACSessionCoordinatorRights(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        url = urlHandlers.UHConfModifCoordinatorRights.getURL(self._conf)
        html=[]
        scr = conference.SessionCoordinatorRights()
        for rightKey in scr.getRightKeys():
            url = urlHandlers.UHConfModifCoordinatorRights.getURL(self._conf)
            url.addParam("rightId", rightKey)
            if self._conf.hasSessionCoordinatorRight(rightKey):
                imgurl=Config.getInstance().getSystemIconURL("tick")
            else:
                imgurl=Config.getInstance().getSystemIconURL("cross")
            html.append("""
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=%s><img class="imglink" src=%s></a> %s
                        """%(quoteattr(str(url)), quoteattr(str(imgurl)), scr.getRight(rightKey)))
        vars["optionalRights"]="<br>".join(html)
        return vars


class WConfModifAC:

    def __init__( self, conference, eventType, user ):
        self.__conf = conference
        self._eventType = eventType
        self.__user = user

    def getHTML( self, params ):
        ac = wcomponents.WConfAccessControlFrame().getHTML( self.__conf,\
                                            params["setVisibilityURL"],\
                                            params["addAllowedURL"],\
                                            params["removeAllowedURL"],\
                                            params["setAccessKeyURL"] )
        dc = ""
        if not self.__conf.isProtected():
            dc = "<br>%s"%wcomponents.WDomainControlFrame( self.__conf ).getHTML( \
                                                    params["addDomainURL"], \
                                                    params["removeDomainURL"] )


        mc = wcomponents.WConfModificationControlFrame().getHTML( self.__conf,
                                                  params["addManagersURL"],
                                                  params["removeManagersURL"],
                                                  params["setModifKeyURL"] ) + "<br>"

        if self._eventType == "conference":
            rc = wcomponents.WConfRegistrarsControlFrame().getHTML( self.__conf,
                                                  params["addRegistrarsURL"],
                                                  params["removeRegistrarsURL"]) + "<br>"
        else:
            rc = ""

        tf=""
        if self._eventType in ["conference","meeting"]:
            tf = "<br>%s" % wcomponents.WConfProtectionToolsFrame(self.__conf).getHTML()
        cr=""
        if self._eventType == "conference":
            cr = "<br>%s"%WConfModifACSessionCoordinatorRights(self.__conf).getHTML()

        return """<br><table width="100%%" class="ACtab"><tr><td>%s%s%s%s%s%s<br></td></tr></table>"""%( mc, rc, ac, dc, tf, cr )


class WPConfModifAC( WPConferenceModifBase ):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType="conference"
        if self._rh.getWebFactory() is not None:
            self._eventType=self._rh.getWebFactory().getId()
        self._user = self._rh._getUser()

    def _setActiveSideMenuItem( self ):
        self._ACMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WConfModifAC( self._conf, self._eventType, self._user )
        import MaKaC.webinterface.rh.conferenceModif as conferenceModif
        p = {
            "setVisibilityURL": urlHandlers.UHConfSetVisibility.getURL(),
            "setAccessKeyURL": urlHandlers.UHConfSetAccessKey.getURL(),
            "setModifKeyURL": urlHandlers.UHConfSetModifKey.getURL(),
            "addAllowedURL": urlHandlers.UHConfSelectAllowed.getURL(),
            "removeAllowedURL": urlHandlers.UHConfRemoveAllowed.getURL(),
            "addDomainURL": urlHandlers.UHConfAddDomain.getURL(),
            "removeDomainURL": urlHandlers.UHConfRemoveDomain.getURL(),
            "addManagersURL": urlHandlers.UHConfSelectManagers.getURL(),
            "removeManagersURL": urlHandlers.UHConfRemoveManagers.getURL(),
            "addRegistrarsURL": conferenceModif.RHConfSelectRegistrars._uh.getURL(),
            "removeRegistrarsURL": conferenceModif.RHConfRemoveRegistrars._uh.getURL()
        }
        return wc.getHTML( p )





#============================================================

class WPConfSelectAllowed( WPConfModifAC ):

    def _getPageContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectAllowed.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddAllowed.getURL()
        return wc.getHTML( params )


class WPConfSelectManagers( WPConfModifAC ):

    def _getPageContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfSelectManagers.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfAddManagers.getURL()
        return wc.getHTML( params )

class WPConfSelectRegistrars( WPConfModifAC ):

    def _getPageContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True

        from MaKaC.webinterface.rh.conferenceModif import RHConfAddRegistrars
        from MaKaC.webinterface.rh.conferenceModif import RHConfSelectRegistrars

        wc = wcomponents.WPrincipalSelection(RHConfSelectRegistrars._uh.getURL(), forceWithoutExtAuth=searchLocal)

        params["addURL"] = RHConfAddRegistrars._uh.getURL()
        return wc.getHTML( params )


#---------------------------------------------------------------------------

class WConfModifTools( wcomponents.WTemplated ):

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["offlsiteMsg"]=""
        vars["dvdURL"]=quoteattr(str(urlHandlers.UHConfDVDCreation.getURL(self.__conf)))
        if self._user is None:
            vars["offlsiteMsg"]= _("(Please, login if you want to apply for your Offline Website)")
            vars["dvdURL"]=quoteattr("")
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("delete")
        vars["cloneIconURL"] = Config.getInstance().getSystemIconURL("clone")
        vars["matPkgIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("materialPkg")))
        vars["matPkgURL"]=quoteattr(str(urlHandlers.UHConfModFullMaterialPackage.getURL(self.__conf)))
        vars["dvdIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("dvd")))
        vars["closeIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("closeIcon")))
        vars["closeURL"]=quoteattr(str(urlHandlers.UHConferenceClose.getURL(self.__conf)))
        vars["alarmURL"]=quoteattr(str(urlHandlers.UHConfDisplayAlarm.getURL(self.__conf)))
        vars["alarmIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("alarmIcon")))
        vars["badgePrintingURL"]=quoteattr(str(urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf)))
        vars["badgeIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("badge")))
        return vars


class WPConfModifToolsBase( WPConferenceModifBase ):

    def _setActiveSideMenuItem(self):
        self._toolsMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabAlarms = self._tabCtrl.newTab( "alarms", _("Alarms"), \
                urlHandlers.UHConfDisplayAlarm.getURL(self._conf) )
        self._tabCloneEvent = self._tabCtrl.newTab( "clone", _("Clone Event"), \
                urlHandlers.UHConfClone.getURL( self._conf ) )
        self._tabPosters = self._tabCtrl.newTab( "posters", _("Posters"), \
                urlHandlers.UHConfModifPosterPrinting.getURL(self._conf) )
        self._tabBadges = self._tabCtrl.newTab( "badges", _("Badges/Tablesigns"), \
                urlHandlers.UHConfModifBadgePrinting.getURL(self._conf) )
        self._tabClose = self._tabCtrl.newTab( "close", _("Lock"), \
                urlHandlers.UHConferenceClose.getURL( self._conf ) )
        self._tabDelete = self._tabCtrl.newTab( "delete", _("Delete"), \
                urlHandlers.UHConfDeletion.getURL(self._conf) )
        self._tabMatPackage = self._tabCtrl.newTab( "matPackage", _("Material Package"), \
                urlHandlers.UHConfModFullMaterialPackage.getURL(self._conf) )
        self._tabOfflineSite = self._tabCtrl.newTab( "offlineSite", _("Offline Site"), \
                urlHandlers.UHConfDVDCreation.getURL(self._conf) )

        self._tabAlarms.setEnabled(False)
        self._tabOfflineSite.setHidden(True)

        self._setActiveTab()

        wf = self._rh.getWebFactory()
        if wf:
            wf.customiseToolsTabCtrl( self._tabCtrl )

    def _getPageContent( self, params ):
        self._createTabCtrl()

        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return html

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return "nothing"

class WPConfClosing(WPConfModifToolsBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType="conference"
        if self._rh.getWebFactory() is not None:
            self._eventType=self._rh.getWebFactory().getId()

    def _setActiveTab( self ):
        self._tabClose.setActive()

    def _getTabContent( self, params ):
        msg = _("""
        <font size="+2"> _("Are you sure that you want to LOCK the event") <i>"%s"</i>?</font><br>
        (_("Note that if you lock the event, you will not be able to change its details any more <br>Only the administrator of the system can unlock an event"))
              """)%(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        return wc.getHTML( msg, \
                        urlHandlers.UHConferenceClose.getURL( self._conf ), {}, \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption= _("No") )

class WPConfDeletion( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabDelete.setActive()

    def _getTabContent( self, params ):
        msg = _("""
        <font size="+2"> _("Are you sure that you want to DELETE the conference") <i>"%s"</i>?</font><br>( _("Note that if you delete the conference, all the items below it will also be deleted"))
              """)%(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        return wc.getHTML( msg, \
                        urlHandlers.UHConfDeletion.getURL( self._conf ), {}, \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption=_("No") )

class WPConfCloneConfirm( WPConfModifToolsBase ):

    def __init__(self, rh, conf, nbClones):
        WPConfModifToolsBase.__init__(self, rh, conf)
        self._nbClones = nbClones

    def _setActiveTab( self ):
        self._tabCloneEvent.setActive()

    def _getTabContent( self, params ):
        msg = _("""
        <font size="+1"> _("This action will create %s new events. Are you sure you want to proceed")?</font>
              """)%self._nbClones
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfPerformCloning.getURL( self._conf )
        params = self._rh._getRequestParams()
        for key in params.keys():
            url.addParam(key,params[key])
        return wc.getHTML( msg, \
                        url, {}, \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption= _("No") )

#---------------------------------------------------------------------------

class WConferenceParticipants(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self._conf.getTitle()
        vars["confId"] = self._conf.getId()
        vars["contribSetIndex"]='index'

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")

        vars["participants"] = self.getParticipantsList()
        vars["statisticAction"] = str(urlHandlers.UHConfModifParticipantsStatistics.getURL(self._conf))
        vars["sendButton"] = _("""<input type="submit" class="btn" value="_("Send email to")" name="participantsAction" />""")
        vars["excelButton"] = _("""<input type="submit" class="btn" value="_("Export to Excel")" name="participantsAction"/>""")
        vars["participantsAction"] = str(urlHandlers.UHConfModifParticipantsAction.getURL(self._conf))
        if nowutc() < self._conf.getStartDate() :
            vars["inviteButton"] = _("""<input type="submit" class="btn" value="_("Invite participant")" />""")
            vars["inviteAction"] = str(urlHandlers.UHConfModifParticipantsSelectToInvite.getURL(self._conf))
            vars["addButton"] = _("""<input type="submit" class="btn" value="_("Add existing particitant")" />""")
            vars["addAction"] = str(urlHandlers.UHConfModifParticipantsSelectToAdd.getURL(self._conf))
            vars["sendAddedInfoButton"] = _("""<input type="submit" class="btn" value="_("Inform about adding")" name="participantsAction" />""")

            vars["presenceButton"] = vars["absenceButton"] = vars["askButton"] = vars["excuseButton"] = ""

        else :
            vars["absenceButton"] = _("""<input type="submit" class="btn" value="_("Mark absence")" name="participantsAction" />""")
            vars["presenceButton"] = _("""<input type="submit" class="btn" value="_("Mark present")" name="participantsAction" />""")
            vars["askButton"] = _("""<input type="submit" class="btn" value="_("Ask for excuse")" name="participantsAction" />""")
            vars["excuseButton"] = _("""<input type="submit" class="btn" value="_("Excuse absence")" name="participantsAction" />""")

            vars["inviteButton"] = vars["inviteAction"] = ""
            vars["addButton"] = vars["addAction"] = ""
            vars["removeButton"] = vars["sendAddedInfoButton"] = ""

        vars["addButton"] = _("""<input type="submit" class="btn" value="_("Search database")" />""")
        vars["addAction"] = str(urlHandlers.UHConfModifParticipantsSelectToAdd.getURL(self._conf))
        vars["removeButton"] = _("""<input type="submit" class="btn" value="_("Remove participant")" name="participantsAction" />""")

        vars["newParticipantURL"] = urlHandlers.UHConfModifParticipantsNewToAdd.getURL(self._conf)

        return vars

    def getParticipantsList(self):
        html = []
        for p in self._conf.getParticipation().getParticipantList():#.values().list().sort(sortByName):
            presence = "n/a"
            if nowutc() > self._conf.getStartDate() :
                if p.isPresent() :
                    presence = "present"
                else :
                    presence = "absent"
            url = urlHandlers.UHConfModifParticipantsDetails.getURL(self._conf)
            url.addParam("participantId",p.getId())
            text = """
            <tr><td class="abstractDataCell">
                <input type="checkbox" name="participants" value="%s" />&nbsp;
                <a href="%s">%s %s %s</a>
                </td>
                <td class="abstractDataCell">&nbsp;&nbsp;%s</td>
                <td class="abstractDataCell">&nbsp;&nbsp;%s</td>
                </tr>
            """%(p.getId(),str(url),p.getTitle(), p.getFirstName(), p.getFamilyName(), p.getStatus(), presence)
            html.append(text)
        return "".join(html)

class WPConfModifParticipants( WPConferenceModifBase ):

    def _setActiveSideMenuItem( self ):
        self._participantsMenuItem.setActive()

    def _getPageContent( self, params ):
        p = WConferenceParticipants( self._conf )
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WConferenceParticipantsPending(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")

        if len(vars.get("errorMsg", [])) > 0 :
            vars["errorMsg"] = wcomponents.WErrorMessage().getHTML(vars)
        else :
            vars["errorMsg"] = ""

        text = button = action = ""
        action = str(urlHandlers.UHConfModifParticipantsPendingAction.getURL(self.__conf))

        vars["pending"] = self._getPendingParticipantsList()
        vars["pendingAction"] = action
        vars["conf"] = self.__conf
        vars["conferenceStarted"] = nowutc() > self.__conf.getStartDate()

        return vars

    def _getPendingParticipantsList(self):
        l = []

        for k in self.__conf.getParticipation().getPendingParticipantList().keys() :
            p = self.__conf.getParticipation().getPendingParticipantByKey(k)
            l.append((k, p))
        return l

class WPConfModifParticipantsPending( WPConfModifParticipants ):

    def _getPageContent( self, params ):
        banner = wcomponents.WParticipantsBannerModif(self._conf).getHTML()
        p = WConferenceParticipantsPending( self._conf )
        return banner+p.getHTML()

#---------------------------------------------------------------------------

class WConferenceParticipantsStatistics(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()

        vars["invited"] = self.__conf.getParticipation().getInvitedNumber()
        vars["rejected"] = self.__conf.getParticipation().getRejectedNumber()
        vars["added"] = self.__conf.getParticipation().getAddedNumber()
        vars["refused"] = self.__conf.getParticipation().getRefusedNumber()
        vars["pending"] = self.__conf.getParticipation().getPendingNumber()

        if nowutc() < self.__conf.getStartDate() :
            vars["present"] = vars["absent"] = vars["excused"] = ""
        else :
            vars["present"] = _("""
            <tr>
                <td class="titleCellFormat"> _("Present participants") </td>
                <td><b>%s</b></td>
            </tr>
            """)%self.__conf.getParticipation().getPresentNumber()

            vars["absent"] = _("""
            <tr>
                <td class="titleCellFormat"> _("Absent participants") </td>
                <td><b>%s</b></td>
            </tr>
            """)%self.__conf.getParticipation().getAbsentNumber()

            vars["excused"] = _("""
            <tr>
                <td class="titleCellFormat"> _("Excused participants") </td>
                <td><b>%s</b></td>
            </tr>
            """)%self.__conf.getParticipation().getExcusedNumber()

        return vars


class WPConfModifParticipantsStatistics( WPConfModifParticipants ):

    def _getPageContent( self, params ):
        params["action"] = "search"
        banner = wcomponents.WParticipantsBannerModif(self._conf).getHTML()
        p = WConferenceParticipantsStatistics( self._conf )
        return banner+p.getHTML(params)

#---------------------------------------------------------------------------

class WPConfModifParticipantsSelect( WPConfModifParticipants ):

    def _getPageContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._conf,searchAction,forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPConfModifParticipantsNew( WPConfModifParticipants ):

    def _getPageContent( self, params ):
        p = wcomponents.WNewPerson()
        if params.get("formTitle",None) is None :
            params["formTitle"] = _("Define new participant")
        if params.get("titleValue",None) is None :
            params["titleValue"] = ""
        if params.get("surNameValue",None) is None :
            params["surNameValue"] = ""
        if params.get("nameValue",None) is None :
            params["nameValue"] = ""
        if params.get("emailValue",None) is None :
            params["emailValue"] = ""
        if params.get("addressValue",None) is None :
            params["addressValue"] = ""
        if params.get("affiliationValue",None) is None :
            params["affiliationValue"] = ""
        if params.get("phoneValue",None) is None :
            params["phoneValue"] = ""
        if params.get("faxValue",None) is None :
            params["faxValue"] = ""
        return p.getHTML(params)

class WPConfModifParticipantsNewPending( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)

    def _getBody( self, params ):
        p = wcomponents.WNewPerson()
        params["formTitle"] = _("Apply for participation")
        if params.get("titleValue",None) is None :
            params["titleValue"] = ""
        if params.get("surNameValue",None) is None :
            params["surNameValue"] = ""
        if params.get("nameValue",None) is None :
            params["nameValue"] = ""
        if params.get("emailValue",None) is None :
            params["emailValue"] = ""
        if params.get("addressValue",None) is None :
            params["addressValue"] = ""
        if params.get("affiliationValue",None) is None :
            params["affiliationValue"] = ""
        if params.get("phoneValue",None) is None :
            params["phoneValue"] = ""
        if params.get("faxValue",None) is None :
            params["faxValue"] = ""

        params["disabledTitle"] = params.get("disabledTitle",False)
        params["disabledSurName"] = params.get("disabledSurName",False)
        params["disabledName"] = params.get("disabledName",False)
        params["disabledEmail"] = params.get("disabledEmail",False)
        params["disabledAddress"] = params.get("disabledAddress",False)
        params["disabledPhone"] = params.get("disabledPhone",False)
        params["disabledFax"] = params.get("disabledFax",False)
        params["disabledAffiliation"] = params.get("disabledAffiliation",False)

        return p.getHTML(params)


#---------------------------------------------------------------------------

class WPConfModifParticipantsInvite(WPConferenceDefaultDisplayBase):

    def __init__(self, rh, conf):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)

    def _defineSectionMenu(self):
        self._sectionMenu = None

    def _getBody( self, params ):
        msg = _("""
        _("Please indicate whether you want to accept or reject the invitation to the") <i>"%s"</i>?<br>
              """)%(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfParticipantsInvitation.getURL( self._conf )
        url.addParam("participantId",params["participantId"])
        return wc.getHTML( msg, url, {}, \
                        confirmButtonCaption= _("Accept"), cancelButtonCaption= _("Reject") )

#---------------------------------------------------------------------------

class WPConfModifParticipantsRefuse(WPConferenceDefaultDisplayBase):

    def __init__(self, rh, conf):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)

    def _getBody( self, params ):
        msg = _("""
        <font size="+2"> _("Are you sure you want to refuse to attend the "%s"")?</font>
              """)%(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfParticipantsRefusal.getURL( self._conf )
        url.addParam("participantId",params["participantId"])
        return wc.getHTML( msg, url, {}, \
                        confirmButtonCaption= _("Refuse"), cancelButtonCaption= _("Cancel") )

#---------------------------------------------------------------------------

class WPConfModifParticipantsEMail(WPConferenceModifBase):
    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _setActiveTab( self ):
        self._tabParticipants.setActive()

    def _getPageContent( self, params ):
        toemail = params["emailto"]
        params["postURL"] = urlHandlers.UHConfModifParticipantsSendEmail.getURL( self._conf )
        wc = WEmail(self._conf, self._getAW().getUser(), toemail)
        return wc.getHTML(params)

#---------------------------------------------------------------------------

class WConferenceLog(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference
        self._tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        if not self._tz:
            self._tz = 'UTC'

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")

        if len(vars.get("errorMsg", [])) > 0 :
            vars["errorMsg"] = wcomponents.WErrorMessage().getHTML(vars)
        else :
            vars["errorMsg"] = ""

        #default ordering by date
        #default general log list
        order = vars.get("order","date")
        filter = vars.get("filter","general")
        key = vars.get("filterKey","")
        vars["log"] = self._getLogList(order, filter, key)

        orderByDate = urlHandlers.UHConfModifLog.getURL(self.__conf)
        orderByDate.addParam("order","date")
        #orderByType = urlHandlers.UHConfModifLog.getURL(self.__conf)
        #orderByType.addParam("order","type")
        orderByModule = urlHandlers.UHConfModifLog.getURL(self.__conf)
        orderByModule.addParam("order","module")
        orderByResponsible = urlHandlers.UHConfModifLog.getURL(self.__conf)
        orderByResponsible.addParam("order","responsible")
        orderBySubject= urlHandlers.UHConfModifLog.getURL(self.__conf)
        orderBySubject.addParam("order","subject")

        vars["orderByDate"] = orderByDate
        #vars["orderByType"] = orderByType
        vars["orderByModule"] = orderByModule
        vars["orderByResponsible"] = orderByResponsible
        vars["orderBySubject"] = orderBySubject

        logFilterAction = urlHandlers.UHConfModifLog.getURL(self.__conf)
        logFilterAction.addParam("order",order)
        vars["logFilterAction"] = logFilterAction
        vars["logListAction"] = ""
        vars["timezone"] = self._tz

        return vars

    def _getLogList(self, order="date", filter="general", key=""):
        html = []

        logList = self.__conf.getLogHandler().getGeneralLogList(order)
        if filter == "email" :
            logList = self.__conf.getLogHandler().getEmailLogList(order)
        elif filter == "action" :
            logList = self.__conf.getLogHandler().getActionLogList(order)
        elif filter == "custom" :
            logList = self.__conf.getLogHandler().getCustomLogList(key, order)

        for li in logList :
            url = urlHandlers.UHConfModifLogItem.getURL(self.__conf)
            url.addParam("logId",li.getLogId())
            if len(li.getLogSubject()) < 50:
                subject = li.getLogSubject()
            else:
                subject = "%s..." % li.getLogSubject()[0:50]
            text = """
            <tr>
                <td valign="top" nowrap class="abstractDataCell">
                    %s
                </td>
                <td valign="top" nowrap class="abstractDataCell"><a href="%s">&nbsp;%s</a></td>
                <td valign="top" nowrap class="abstractDataCell">&nbsp;%s</td>
                <td valign="top" nowrap class="abstractDataCell">&nbsp;%s</td>
            </tr>"""%(li.getLogDate().astimezone(timezone(self._tz)).strftime("%Y-%m-%d %H:%M:%S"),\
                    url, subject,\
                    li.getResponsibleName(),\
                    li.getModule())
            html.append(text)
        return "".join(html)

class WPConfModifLog( WPConferenceModifBase ):

    def _setActiveSideMenuItem( self ):
        self._logMenuItem.setActive()

    def _getPageContent( self, params ):
        p = WConferenceLog( self._conf )
        return p.getHTML(params)

#---------------------------------------------------------------------------
class WConferenceLogItem(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()

        if len(vars.get("errorMsg", [])) > 0 :
            vars["errorMsg"] = wcomponents.WErrorMessage().getHTML(vars)
        else :
            vars["errorMsg"] = ""

        logId = vars.get("logId","")
        logItem = self.__conf.getLogHandler().getLogItemById(logId)
        vars["logItem"] = self._getLogItemElements(logItem)

        url = urlHandlers.UHConfModifLog.getURL(self.__conf)
        vars["logListAction"] = url

        return vars

    def _getLogItemElements(self, logItem):
        html = []

        text = """
        <tr>
                <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    &nbsp;%s</td>
                <td>&nbsp;%s</td>
        </tr>"""%("Subject", logItem.getLogSubject())
        html.append(text)
        logInfo = logItem.getLogInfo()

        for key in logInfo.keys():
            if key != "subject":
                text = """
        <tr>
                <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    &nbsp;%s</td>
                <td><pre>%s</pre></td>
        </tr>"""%(key, escape(str(logInfo[key])))
                html.append(text)
        return "".join(html)

class WPConfModifLogItem( WPConfModifLog ):

    def _setActiveTab( self ):
        self._tabLog.setActive()

    def _getPageContent( self, params ):
        banner = wcomponents.WConfLogsBannerModif(self._conf).getHTML()
        p = WConferenceLogItem( self._conf )
        return banner+p.getHTML(params)


#---------------------------------------------------------------------------

class WConfModifListings( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self.__conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["pendingQueuesIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["pendingQueuesURL"]=quoteattr(str(urlHandlers.UHConfModifPendingQueues.getURL( self.__conf )))
        vars["allSessionsConvenersIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["allSessionsConvenersURL"]=quoteattr(str(urlHandlers.UHConfAllSessionsConveners.getURL( self.__conf )))
        vars["allSpeakersIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["allSpeakersURL"]=quoteattr(str(urlHandlers.UHConfAllSpeakers.getURL( self.__conf )))
        vars["allPrimaryAuthorsIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["allPrimaryAuthorsURL"]=quoteattr(str(urlHandlers.UHConfAllPrimaryAuthors.getURL( self.__conf )))
        vars["allCoAuthorsIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["allCoAuthorsURL"]=quoteattr(str(urlHandlers.UHConfAllCoAuthors.getURL( self.__conf )))
        return vars

class WPConfModifListings( WPConferenceModifBase ):
    def _setActiveSideMenuItem(self):
        self._listingsMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WConfModifListings( self._conf )
        return wc.getHTML()

#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

class WConferenceClone(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def _getSelectDay(self):
        sd = ""
        for i in range(31) :
            selected = ""
            if datetime.today().day == (i+1) :
                selected = "selected=\"selected\""
            sd += "<OPTION VALUE=\"%d\" %s>%d\n"%(i+1, selected, i+1)
        return sd

    def _getSelectMonth(self):
        sm = ""
        month = [ "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
        for i in range(12) :
            selected = ""
            if datetime.today().month == (i+1) :
                selected = "selected=\"selected\""
            sm += "\t<OPTION VALUE=\"%d\" %s>%s\n"%(i+1, selected, _(month[i]))
        return sm

    def _getSelectYear(self):
        sy = ""
        i = 1995
        while i < 2015 :
            selected = ""
            if datetime.today().year == i :
                selected = "selected=\"selected\""
            sy += "\t<OPTION VALUE=\"%d\" %s>%d\n"%(i, selected, i)
            i += 1
        return sy


    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()
        vars["selectDay"] = self._getSelectDay()
        vars["selectMonth"] = self._getSelectMonth()
        vars["selectYear"] = self._getSelectYear()
        vars["calendarIconURL"] = Config.getInstance().getSystemIconURL( "calendar" )
        vars["calendarSelectURL"] = urlHandlers.UHSimpleCalendar.getURL()
        return vars


class WPConfClone( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabCloneEvent.setActive()

    def _getTabContent( self, params ):
        p = WConferenceClone( self._conf )
        pars = {"cancelURL": urlHandlers.UHConfModifTools.getURL( self._conf ), \
                "cloneOnce": urlHandlers.UHConfPerformCloneOnce.getURL( self._conf ), \
                "cloneInterval": urlHandlers.UHConfPerformCloneInterval.getURL( self._conf ), \
                "cloneday": urlHandlers.UHConfPerformCloneDays.getURL( self._conf ), \
                "cloning" : urlHandlers.UHConfPerformCloning.getURL( self._conf ),
                "cloneOptions": _("""<li><input type="checkbox" name="cloneTracks" id="cloneTracks" value="1" />_("Tracks")</li>
                                     <li><input type="checkbox" name="cloneTimetable" id="cloneTimetable" value="1" />_("Full timetable")</li>
                                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneSessions" id="cloneSessions" value="1" />_("Sessions")</li></ul></li>
                                     <li><input type="checkbox" name="cloneRegistration" id="cloneRegistration" value="1" >_("Registration")</li>
                                     <li><input type="checkbox" name="cloneEvaluation" id="cloneEvaluation" value="1" />_("Evaluation")</li>""") }
        return p.getHTML( pars )

#---------------------------------------------------------------------------------------

class WConferenceAllSessionsConveners(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference
        self._display = []
        self._dispopts = [ "Email", "Session" ]
        self._order = ""

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()
        vars["convenerSelectionAction"]=quoteattr(str(urlHandlers.UHConfAllSessionsConvenersAction.getURL(self.__conf)))
        vars["contribSetIndex"]='index'
        vars["convenerNumber"]=str(len(self.__conf.getAllSessionsConvenerList()))
        vars["conveners"]=self._getAllConvenersHTML()
        vars["columns"] = self._getColumnsHTML(None)
        vars["backURL"]=quoteattr(str(urlHandlers.UHConfModifListings.getURL(self.__conf)))
        return vars

    def _getAllConvenersHTML(self):
        html = ''

        url = urlHandlers.UHSessionModification.getURL(self.__conf)
        convenersDictionary = self.__conf.getAllSessionsConvenerList()

        for key in convenersDictionary.keys() :
            counter = 0
            sessions = []

            for convener in  convenersDictionary[key] :
                if counter == 0 :
                    html = html + """
                    <tr>
                        <td valign="top" nowrap class="abstractDataCell"><input type="checkbox" name="conveners" value="%s">&nbsp;&nbsp;%s</td>
                        <td valign="top" nowrap class="abstractDataCell">&nbsp;&nbsp;%s</td>
                        """    %(convener.getEmail(),\
                        self.htmlText(convener.getFullName()) or "&nbsp;", \
                        self.htmlText(convener.getEmail()) or "&nbsp;" )

                url = urlHandlers.UHSessionModification.getURL(self.__conf)
                url.addParam("sessionId",convener.getSession().getId() )
                sesurl = quoteattr(str(url))
                sestitle = self.htmlText(convener.getSession().getTitle()) or "&nbsp;"
                sessions.append("<a href=%s>%s</a>"%(sesurl,sestitle))

                counter = counter + 1

            sessionlist = "<br/>".join(sessions)
            html = html + """<td valign="top"  class="abstractDataCell">%s"""%sessionlist
            html = html + """</td></tr>"""
        html += _("""
                    <tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
                    <tr><td colspan="3" align="left">&nbsp;<input type="submit" class="btn" value="_("Send an E-mail")" name="sendEmails"></td></tr>
                    </form>
                          """)
        return html

    def _getColumnsHTML(self, sortingField):
        res =[]
        columns ={"Email": _("Email"),"Session": _("Session") }
        currentSorting=""
        if sortingField is not None:
            currentSorting=sortingField.getId()
        currentSortingHTML = ""

        url=self._getURL()
        url.addParam("sortBy","Name")
        nameImg=""
        if currentSorting == "Name":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Name">"""
            if self._order == "down":
                nameImg = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                nameImg = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        nameSortingURL=quoteattr("%s#results"%str(url))
        checkAll = """<img src=%s border="0" alt="Select all" onclick="selectAll()" style="cursor:hand">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        uncheckAll = """<img src=%s border="0" alt="Unselect all" onclick="unselectAll()" style="cursor:hand"">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        checkboxes="%s%s"%(checkAll,uncheckAll)
        res.append("""
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s%s<a href=%s>Name</a></td>"""%(nameImg, checkboxes, nameSortingURL))
        if self._display == []:
            for key in self._dispopts:
                if key in ["Email","Session"]:
                    url=self._getURL()
                    url.addParam("sortBy",key)
                    img=""
                    if currentSorting == key:
                        currentSortingHTML = """<input type="hidden" name="sortBy" value="%s">"""%key
                        if self._order == "down":
                            img = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                            url.addParam("order","up")
                        elif self._order == "up":
                            img = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                            url.addParam("order","down")
                    sortingURL=quoteattr("%s#results"%str(url))
                    res.append("""
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s<a href=%s>%s</a></td>"""%(img, sortingURL, self.htmlText(columns[key])))
        else:
            for key in self._dispopts:
                if key in self._display:
                    url=self._getURL()
                    url.addParam("sortBy",key)
                    img=""
                    if currentSorting == key:
                        currentSortingHTML = """<input type="hidden" name="sortBy" value="%s">"""%key
                        if self._order == "down":
                            img = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                            url.addParam("order","up")
                        elif self._order == "up":
                            img = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                            url.addParam("order","down")

                    sortingURL=quoteattr("%s#results"%str(url))
                    res.append("""<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s<a href=%s>%s</a></td>
                               """%(img, sortingURL, self.htmlText(columns[key])))

        html= """
            <t>
            <!--<td width="1px">%s</td>-->
            %s
            </tr>
             """%(currentSortingHTML, "".join(res))
        return html

    def _getURL( self ):
        url = urlHandlers.UHConfAllSessionsConveners.getURL(self.__conf)

        if self._display == []:
            url.addParam("disp", ["Email","Session"])
        else:
            url.addParam("disp", self._display)

        return url

class WPConfAllSessionsConveners( WPConfModifListings ):

    def _getPageContent( self, params ):
        banner = wcomponents.WListingsBannerModif(self._conf).getHTML()
        p = WConferenceAllSessionsConveners( self._conf )
        return banner+p.getHTML()

#---------------------------------------------------------------------------------------


class WConfModifAllContribParticipants(wcomponents.WTemplated):

    def __init__(self, conference, partIndex):
        self._title= _("All participants list")
        self._conf = conference
        self._order = ""
        self._dispopts = ["Email", "Contributions" ]
        self._partIndex=partIndex

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        self._url=vars["participantMainPageURL"]
        vars["participantNumber"]=str(len(self._partIndex.getParticipationKeys()))
        vars["participants"]=self._getAllParticipantsHTML()
        vars["backURL"]=quoteattr(str(urlHandlers.UHConfModifListings.getURL(self._conf)))
        vars["columns"] = self._getColumnsHTML(None)
        if not vars.has_key("title"):
            vars["title"]=self._title
        return vars

    def _getAllParticipantsHTML(self):
        html = []
        for key in self._partIndex.getParticipationKeys():
            contribPartList=self._partIndex.getById(key)
            if contribPartList != []:
                html.append("""
                <tr>
                    <td valign="top" nowrap class="abstractDataCell"><input type="checkbox" name="participants" value="%s">&nbsp;&nbsp;%s</td>
                    <td valign="top" nowrap class="abstractDataCell">&nbsp;&nbsp;%s</td>
                            """%(contribPartList[0].getEmail(), \
                                self.htmlText(contribPartList[0].getFullName()) or "&nbsp;", \
                                self.htmlText(contribPartList[0].getEmail()) or "&nbsp;" ))
                contribs=[]
                for contribPart in contribPartList:
                    if contribPart.getContribution() is not None:
                        url = quoteattr(str(urlHandlers.UHContributionModification.getURL(contribPart.getContribution())))
                        contribtitle = self.htmlText(contribPart.getContribution().getTitle()) or "&nbsp;"
                        contribs.append("<b>- </b><a href=%s>%s</a>"%(url,contribtitle))
                html.append("""<td valign="top"  class="abstractDataCell">%s</td></tr>"""%("<br>".join(contribs)))
        html.append( _("""
                    <tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
                    <tr><td colspan="3" align="left">&nbsp;<input type="submit" class="btn" value="_("Send an E-mail")" name="sendEmails"></td></tr>
                    </form>
                          """))
        return "".join(html)

    def _getColumnsHTML(self, sortingField):
        res =[]
        currentSorting=""
        if sortingField is not None:
            currentSorting=sortingField.getId()

        # Name
        url=self._getURL()
        url.addParam("sortBy","Name")
        img=""
        if currentSorting == "Name":
            if self._order == "down":
                img = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                img = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        sortingURL=quoteattr("%s#results"%str(url))
        checkAll = """<img src=%s border="0" alt="Select all" onclick="selectAll()" style="cursor:hand">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        uncheckAll = """<img src=%s border="0" alt="Unselect all" onclick="unselectAll()" style="cursor:hand"">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        checkboxes="%s%s"%(checkAll,uncheckAll)
        res.append("""
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s%s<a href=%s>Name</a></td>"""%(img, checkboxes, sortingURL))

        # Others
        for i in self._dispopts:
            url=self._getURL()
            url.addParam("sortBy",i)
            img=""
            if currentSorting == i:
                if self._order == "down":
                    img = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    img = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
            sortingURL=quoteattr("%s#results"%str(url))
            res.append("""<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s<a href=%s>%s</a></td>"""%(img, sortingURL, i))


        html= """
            <t>
            %s
            </tr>
             """%("".join(res))
        return html

    def _getURL( self ):
        return self._url

class WPConfAllSpeakers( WPConfModifListings ):

    def _getPageContent( self, params ):
        banner = wcomponents.WListingsBannerModif(self._conf).getHTML()
        p = WConfModifAllContribParticipants( self._conf, self._conf.getSpeakerIndex() )
        return banner+p.getHTML({"title": _("All speakers list"), \
                          "participantMainPageURL":urlHandlers.UHConfAllSpeakers.getURL(self._conf), \
                          "participantSelectionAction":quoteattr(str(urlHandlers.UHConfAllSpeakersAction.getURL(self._conf)))})

class WPConfAllPrimaryAuthors( WPConfModifListings ):

    def _getPageContent( self, params ):
        p = WConfModifAllContribParticipants( self._conf, self._conf.getPrimaryAuthorIndex() )
        return p.getHTML({"title": _("All primary authors list"), \
                          "participantMainPageURL":urlHandlers.UHConfAllPrimaryAuthors.getURL(self._conf), \
                          "participantSelectionAction":quoteattr(str(urlHandlers.UHConfAllPrimaryAuthorsAction.getURL(self._conf)))})

class WPConfAllCoAuthors( WPConfModifListings ):

    def _getPageContent( self, params ):
        p = WConfModifAllContribParticipants( self._conf, self._conf.getCoAuthorIndex() )
        return p.getHTML({"title": _("All co-authors list"), \
                          "participantMainPageURL":urlHandlers.UHConfAllCoAuthors.getURL(self._conf), \
                          "participantSelectionAction":quoteattr(str(urlHandlers.UHConfAllCoAuthorsAction.getURL(self._conf)))})

class WPEMailContribParticipants ( WPConfModifListings):
    def __init__(self, rh, conf, participantList):
        WPConfModifListings.__init__(self, rh, conf)
        self._participantList = participantList

    def _getPageContent(self,params):
        wc = WEmailToContribParticipants(self._conf, self._getAW().getUser(), self._participantList)
        return wc.getHTML()

class WEmailToContribParticipants(wcomponents.WTemplated):
    def __init__(self,conf,user,contribParticipantList):
        self._conf = conf
        try:
            self._fromemail = user.getEmail()
        except:
            self._fromemail = ""
        self._contribParticipantList = contribParticipantList

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        toEmails=[]
        toIds=[]
        for email in self._contribParticipantList:
            if len(email) > 0 :
                toEmails.append(email)
        vars["from"] = self._fromemail
        vars["toEmails"]= ", ".join(toEmails)
        vars["emails"]= ",".join(toEmails)
        vars["postURL"]=urlHandlers.UHContribParticipantsSendEmail.getURL(self._conf)
        vars["subject"]=""
        vars["body"]=""
        return vars
#---------------------------------------------------------------------------------------

class WPEMailConveners ( WPConfModifListings):
    def __init__(self, rh, conf, convenerList):
        WPConfModifListings.__init__(self, rh, conf)
        self._convenerList = convenerList

    def _getTabContent(self,params):
        wc = WEmailToConveners(self._conf, self._getAW().getUser(), self._convenerList)
        return wc.getHTML()

class WEmailToConveners(wcomponents.WTemplated):
    def __init__(self,conf,user,convenerList):
        self._conf = conf
        try:
            self._fromemail = user.getEmail()
        except:
            self._fromemail = ""
        self._convenerList = convenerList

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        toEmails=[]
        toIds=[]
        for email in self._convenerList:
            if len(email) > 0 :
                toEmails.append(email)
        vars["from"] = self._fromemail
        vars["toEmails"]= ", ".join(toEmails)
        vars["emails"]= ",".join(toEmails)
        vars["postURL"]=urlHandlers.UHConvenersSendEmail.getURL(self._conf)
        vars["subject"]=""
        vars["body"]=""
        return vars

class WPConfAllParticipants( WPConfModifListings ):

    def _getTabContent( self, params ):
        p = wcomponents.WConferenceAllParticipants( self._conf )
        return p.getHTML()

#---------------------------------------------------------------------------------------


class WConvenerSentMail  (wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=quoteattr(str(urlHandlers.UHConfAllSessionsConveners.getURL(self._conf)))
        return vars

class WPSentEmail( WPConfModifListings ):
    def _getTabContent(self,params):
        wc = WConvenerSentMail(self._conf)
        return wc.getHTML()


class WContribParticipationSentMail(wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=quoteattr(str(urlHandlers.UHConfAllSpeakers.getURL(self._conf)))
        return vars


class WPContribParticipationSentEmail( WPConfModifListings ):
    def _getTabContent(self,params):
        wc = WContribParticipationSentMail(self._conf)
        return wc.getHTML()


#---------------------------------------------------------------------------------------

class WSetAlarm(wcomponents.WTemplated):

    def __init__(self, conference, aw):
            self.__conf = conference
            self._aw=aw

    def _getFromOptionsHTML(self, selected=""):
        emails=[]
        foundEmail=False
        selHTML=""
        if selected=="":
            foundEmail=True
            selHTML="selected=\"selected\""
        html=[ _("""<option value=\"\" %s>--_("select a from address")--</option>""")%selHTML]
        for ch in self.__conf.getChairList():
            if ch.getEmail().strip()!="" and ch.getEmail().strip() not in emails:
                selHTML=""
                if selected.strip()==ch.getEmail().strip():
                    foundEmail=True
                    selHTML="selected=\"selected\""
                html.append("<option value=%s %s>%s &#60;%s&#62;</option>"%(quoteattr(ch.getEmail().strip()),selHTML,ch.getFullName(),ch.getEmail().strip()))
                emails.append(ch.getEmail().strip())
        if self.__conf.getSupportEmail().strip()!="" and self.__conf.getSupportEmail().strip() not in emails:
            selHTML=""
            if selected.strip()==self.__conf.getSupportEmail().strip():
                foundEmail=True
                selHTML="selected=\"selected\""
            html.append("<option value=%s %s>%s</option>"%(quoteattr(self.__conf.getSupportEmail().strip()),selHTML,self.__conf.getSupportEmail().strip()))
            emails.append(self.__conf.getSupportEmail().strip())
        if self._aw.getUser() is not None and self._aw.getUser().getEmail().strip() not in emails:
            selHTML=""
            if selected.strip()==self._aw.getUser().getEmail().strip():
                foundEmail=True
                selHTML="selected=\"selected\""
            html.append("<option value=%s %s>%s</option>"%(quoteattr(self._aw.getUser().getEmail().strip()),selHTML,self._aw.getUser().getEmail().strip()))
            emails.append(self._aw.getUser().getEmail().strip())
        if self.__conf.getCreator() is not None and self.__conf.getCreator().getEmail().strip() not in emails:
            selHTML=""
            if selected.strip()==self.__conf.getCreator().getEmail().strip():
                foundEmail=True
                selHTML="selected=\"selected\""
            html.append("<option value=%s %s>%s &#60;%s&#62;</option>"%(quoteattr(self.__conf.getCreator().getEmail().strip()),selHTML,self.__conf.getCreator().getFullName(), self.__conf.getCreator().getEmail().strip()))
        #selHTML=""
        #if selected.strip()==self.__conf.getTitle().strip():
        #    foundEmail=True
        #    selHTML="selected=\"selected\""
        #html.append("<option value=%s %s>%s</option>"%(quoteattr(self.__conf.getTitle().strip()),selHTML,self.__conf.getTitle().strip()))
        if not foundEmail:
            selHTML="selected=\"selected\""
            html.append("<option value=%s %s>%s</option>"%(quoteattr(selected.strip()),selHTML,selected.strip()))
        return "".join(html)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["alarmId"] = vars.get("alarmId","")
        vars["confTitle"] = self.__conf.getTitle()
        vars["formTitle"] = vars.get("formTitle", _("Create a new alarm email"))
        vars["fromOptions"] = self._getFromOptionsHTML(vars.get("fromEmail",""))
        vars["toEmails"] = vars.get("toEmails","")
        if vars["toEmails"] != "" :
            vars["definedRecipients"] = "checked"
            vars["recipientsDisabled"] = ""
        else :
            vars["definedRecipients"] = ""
            vars["recipientsDisabled"] = """disabled="disabled" """
        vars["includeConf"] = vars.get("includeConf","")
        vars["note"] = vars.get("note","")
        vars["timezone"] = self.__conf.getTimezone()
        return vars

#---------------------------------------------------------------------------------------

class WConfDisplayAlarm( wcomponents.WTemplated ):

    def __init__(self, conference, aw):
            self.__conf = conference
            self._aw=aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["alarmFrame"] = wcomponents.WAlarmFrame().getHTML(\
                                            self.__conf,\
                                            vars["addAlarmURL"], \
                                            vars["deleteAlarmURL"],\
                                            vars["modifyAlarmURL"] )
        return vars

class WPConfDisplayAlarm( WPConfModifToolsBase ):

    def _getTabContent( self, params ):
        wc = WConfDisplayAlarm( self._conf, self._rh._getUser() )
        p = {
"addAlarmURL": urlHandlers.UHConfAddAlarm.getURL( self._conf ), \
"deleteAlarmURL": urlHandlers.UHConfDeleteAlarm.getURL(), \
"modifyAlarmURL": urlHandlers.UHConfModifyAlarm.getURL(), \
    }
        return wc.getHTML( p )

class WPConfAddAlarm( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabAlarms.setActive()


    def _getTabContent( self, params ):
        p = WSetAlarm( self._conf, self._getAW() )
        testSendAlarm = _("""<input type="submit" class="btn" value="_("send this alarm email now")" onClick="this.form.action='%s';">""") % urlHandlers.UHSendAlarmNow.getURL( self._conf  )
        if self._rh._getUser():
            testSendAlarm += _(""" <input type="submit" class="btn" value="_("send me this alarm email as a test")" onClick="this.form.action='%s';">""") % urlHandlers.UHTestSendAlarm.getURL( self._conf  )
        thisyear=datetime.today().year
        thismonth=datetime.today().month
        thisday=datetime.today().day
        yearoptions=""
        for i in range(thisyear,thisyear+10):
            yearoptions+="<OPTION VALUE='%s'>%s" % (i,i)
        monthoptions=""
        for i in range(1,13):
            if i==thismonth:
                selecttext=" selected"
            else:
                selecttext=""
            monthoptions+="<OPTION VALUE='%02d'%s>%s" % (i,selecttext,datetime(1900,i,1).strftime("%B"))
        dayoptions=""
        for i in range(1,32):
            if i==thisday:
                selecttext=" selected"
            else:
                selecttext=""
            dayoptions+="<OPTION VALUE='%02d'%s>%02d" %(i,selecttext,i)
        pars = { \
"cancelURL": urlHandlers.UHConfDisplayAlarm.getURL( self._conf ), \
"saveAlarm": urlHandlers.UHSaveAlarm.getURL( self._conf ), \
"confId": self._conf.getId(), \
"yearOptions": yearoptions, \
"monthOptions": monthoptions, \
"dayOptions": dayoptions, \
"testSendAlarm": testSendAlarm }
        pars["toAllParticipants"] = params.get("toAllParticipants","")
        pars["selec1"] = " checked"
        pars["selec2"] = pars["selec3"] = ""
        pars["hour"] = ""
        for i in range(0,24):
            pars["hour"] += "<OPTION VALUE=\"%s\">%sH\n"%(string.zfill(i,2),string.zfill(i,2))
        pars["hourBefore"] = ""
        for i in range(1,24):
            pars["hourBefore"] += "<OPTION VALUE=\"%s\">H-%s\n"%(string.zfill(i,2),i)
        pars["dayBefore"] = ""
        for i in range(1,8):
            pars["dayBefore"] += "<OPTION VALUE=\"%s\">D-%s\n"%(string.zfill(i,2),i)
        return p.getHTML( pars )

#--------------------------------------------------------------------

class WPConfModifyAlarm( WPConfModifToolsBase ):

    def __init__(self, caller, conf, alarm):
        WPConfModifToolsBase.__init__(self, caller, conf)
        self._alarm = alarm


    def _getTabContent( self, params ):

        p = WSetAlarm(self._conf, self._getAW())

        vars = { \
            "cancelURL": urlHandlers.UHConfDisplayAlarm.getURL( self._conf ), \
            "saveAlarm": urlHandlers.UHConfSaveAlarm.getURL(), \
            "confId": self._conf.getId(), \
            "alarmId": self._alarm.getId(), \
            "confTitle": self._conf.getTitle() }
        vars["selec1"] = vars["selec2"] = vars["selec3"] = ""
        year = month = day = hour = dayBefore = hourBefore = -1
        if self._alarm.getTimeBefore():
            #the date is calculated from the conference startdate
            if self._alarm.getTimeBefore() < timedelta(days=1):
                vars["selec3"] = "checked"
                hourBefore = int(self._alarm.getTimeBefore().seconds/3600)
            else:
                #time before upper to 1 day
                vars["selec2"] = "checked"
                dayBefore = int(self._alarm.getTimeBefore().days)
            startyear=datetime.today().year
        else:
            #the date is global
            vars["selec1"] = "checked"
            if self._alarm.getStartDate() != None:
                startyear = year = int(self._alarm.getStartDate().year)
                month = int(self._alarm.getStartDate().month)
                day = int(self._alarm.getStartDate().day)
                hour = int(self._alarm.getStartDate().hour)
        vars["dayOptions"] = ""
        for i in range(1,32):
            sel = ""
            if i == day:
                sel = "selected"
            vars["dayOptions"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,2),sel,string.zfill(i,2))

        vars["monthOptions"] = ""
        for i in range(1,13):
            sel = ""
            if i == month:
                sel = "selected"
            vars["monthOptions"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,2),sel,datetime(1900,i,1).strftime("%B"))

        vars["yearOptions"] = ""
        for i in range(startyear,startyear+10):
            sel = ""
            if i == year:
                sel = "selected"
            vars["yearOptions"] += "<OPTION VALUE=\"%s\"%s>%s\n"%(string.zfill(i,4),sel,string.zfill(i,4))

        vars["hour"] = ""
        for i in range(0,24):
            sel = ""
            if i == hour:
                sel = "selected"
            vars["hour"] += "<OPTION VALUE=\"%s\"%s>%sH\n"%(string.zfill(i,2),sel,string.zfill(i,2))

        vars["hourBefore"] = ""
        for i in range(1,24):
            sel = ""
            if i == hourBefore:
                sel = "selected"
            vars["hourBefore"] += "<OPTION VALUE=\"%s\"%s>H-%s\n"%(string.zfill(i,2),sel,i)

        vars["dayBefore"] = ""
        for i in range(1,8):
            sel = ""
            if i == dayBefore:
                sel = "selected"
            vars["dayBefore"] += "<OPTION VALUE=\"%s\"%s>D-%s\n"%(string.zfill(i,2),sel,i)

        vars["subject"] = self._alarm.getSubject()
        vars["toEmails"] = ", ".join(self._alarm.getToAddrList())
        vars["fromEmail"] = self._alarm.getFromAddr()
        vars["text"] = self._alarm.getText()
        vars["note"] = self._alarm.getNote()
        vars["formTitle"] = _("Modify alarm data")

        if self._alarm.getToAllParticipants() :
            vars["toAllParticipants"] = _("""
        <tr>
            <td>&nbsp;<input type="checkbox" name="toAllParticipants" checked="checked"></td>
            <td> _("Send alarm to all participants of the event.")</td>
        </tr>
        """)
        else :
            vars["toAllParticipants"] = _("""
        <tr>
            <td>&nbsp;<input type="checkbox" name="toAllParticipants" ></td>
            <td> _("Send alarm to all participants of the event.")</td>
        </tr>
        """)

        testSendAlarm = _("""<input type="submit" class="btn" value="_("send this alarm now")" onClick="this.form.action='%s';">""") % urlHandlers.UHSendAlarmNow.getURL( self._conf  )
        if self._rh._getUser():
            testSendAlarm += _(""" <input type="submit" class="btn" value="_("send me this alarm as a test")" onClick="this.form.action='%s';">""") % urlHandlers.UHTestSendAlarm.getURL( self._conf  )

        vars["testSendAlarm"] = testSendAlarm
        if self._alarm.getConfSumary():
            vars["includeConf"] = "checked"

        return p.getHTML( vars )

#----------------------------------------------------------------------------------

class WConfModifCFAAddField( wcomponents.WTemplated ):

    def __init__( self, conference, fieldId ):
        self._conf = conference
        self._fieldId = fieldId

    def getVars (self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"] = quoteattr(str(urlHandlers.UHConfModifCFAPerformAddOptFld.getURL(self._conf)))
        selectedYes = ""
        selectedNo = "checked"
        fieldType = "textarea"
        if self._fieldId != "":
            abf = self._conf.getAbstractMgr().getAbstractFieldsMgr().getFieldById(self._fieldId)
            vars["id"] = quoteattr(abf.getId())
            vars["name"] = quoteattr(abf.getName())
            vars["caption"] = quoteattr(abf.getCaption())
            vars["maxlength"] = quoteattr(str(abf.getMaxLength()))
            vars["action"] = "Edit"
            if abf.isMandatory():
                selectedYes = "checked"
                selectedNo = ""
            fieldType = abf.getType()
        else:
            vars["id"] = vars["name"] = vars["caption"] = quoteattr("")
            vars["maxlength"] = 0
            vars["action"] = "Add"
        #vars["fieldName"] = """<input type="text" name="fieldId" value=%s size="60">""" % quoteattr(self._fieldId)
        #if self._fieldId == "content":
        #    vars["fieldName"] = """%s<input type="hidden" name="fieldId" value=%s size="60">""" % (self._fieldId, quoteattr(self._fieldId))
        vars["selectedYes"] = selectedYes
        vars["selectedNo"] = selectedNo
        vars["fieldTypeOptions"] = ""
        for type in review.AbstractField._fieldTypes:
            selected = ""
            if type == fieldType:
                selected = " selected"
            vars["fieldTypeOptions"] += """<option value="%s"%s>%s\n""" % (type, selected, type)
        vars["errors"] = ""
        return vars


class WConfModifCFA( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getAbstractFieldsHTML(self, vars):
        abMgr = self._conf.getAbstractMgr()
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")
        laf=[]
        urlAdd = str(urlHandlers.UHConfModifCFAAddOptFld.getURL(self._conf))
        urlRemove = str(urlHandlers.UHConfModifCFARemoveOptFld.getURL(self._conf))
        laf.append("""<form action="%s" method="POST">""" % urlAdd)
        for af in abMgr.getAbstractFieldsMgr().getFields():
            urlUp = urlHandlers.UHConfModifCFAAbsFieldUp.getURL(self._conf)
            urlUp.addParam("fieldId",af.getId())
            urlDown = urlHandlers.UHConfModifCFAAbsFieldDown.getURL(self._conf)
            urlDown.addParam("fieldId",af.getId())
            if af.isMandatory():
                mandatoryText = _("mandatory")
            else:
                mandatoryText = _("optional")
            maxCharText = ""
            if int(af.getMaxLength()) != 0:
                maxCharText = _("max: %s char.") % af.getMaxLength()
            else:
                maxCharText = _("no char. limit")
            addInfo = "(%s - %s)" % (mandatoryText,maxCharText)
            url=urlHandlers.UHConfModifCFAOptFld.getURL(self._conf)
            url.addParam("fieldId", af.getId())
            url=quoteattr("%s#optional"%str(url))
            urledit=urlHandlers.UHConfModifCFAEditOptFld.getURL(self._conf)
            urledit.addParam("fieldId", af.getId())
            urledit=quoteattr("%s#optional"%str(urledit))
            if self._conf.getAbstractMgr().hasEnabledAbstractField(af.getId()):
                icon=vars["enablePic"]
                textIcon=enabledText
            else:
                icon=vars["disablePic"]
                textIcon=disabledText
            if af.getId() == "content":
                removeButton = ""
            else:
                removeButton = "<input type=\"checkbox\" name=\"fieldId\" value=\"%s\">" % af.getId()
            laf.append("""
                            <tr>
                                <td>
                                  <a href=%s><img src=%s alt="%s" class="imglink"></a>&nbsp;<a href=%s><img src=%s border="0" alt=""></a><a href=%s><img src=%s border="0" alt=""></a>
                                </td>
                                <td width="1%%">%s</td>
                                <td>
                                  &nbsp;<a href=%s>%s</a> %s
                                </td>
                            </tr>
                            """%(
                                url, \
                                icon, \
                                textIcon, \
                                quoteattr(str(urlUp)),\
                                quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))),\
                                quoteattr(str(urlDown)),\
                                quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))),\
                                removeButton, \
                                urledit, \
                                af.getName(), \
                                addInfo))
        laf.append( _("""
    <tr>
      <td align="right" colspan="3">
        <input type="submit" value="_("remove")" onClick="this.form.action='%s';" class="btn">
        <input type="submit" value="_("add")" class="btn">
      </td>
    </tr>
    </form>""") % urlRemove)
        laf.append("</form>")
        return "".join(laf)

    def _getNotifTplsHTML(self):
        res=[]
        for tpl in self._conf.getAbstractMgr().getNotificationTplList():
            res.append("""
                <tr>
                    <td bgcolor="white" nowrap>
                        <a href=%s><img src=%s border="0" alt=""></a>
                        <a href=%s><img src=%s border="0" alt=""></a>
                        <input type="checkbox" name="selTpls" value=%s>
                    </td>
                    <td bgcolor="white" align="left" nowrap><a href=%s>%s</a></td>
                    <td>&nbsp;<td>
                    <td bgcolor="white" align="left" width="90%%"><font size="-1">%s</font></td>
                </tr>"""%(quoteattr(str(urlHandlers.UHConfModCFANotifTplUp.getURL(tpl))),\
                            quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))),\
                            quoteattr(str(urlHandlers.UHConfModCFANotifTplDown.getURL(tpl))),\
                            quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))),\
                            quoteattr(str(tpl.getId())), \
                            quoteattr(str(urlHandlers.UHAbstractModNotifTplDisplay.getURL(tpl))), \
                            self.htmlText(tpl.getName()), \
                            self.htmlText(tpl.getDescription())))
        return "".join(res)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        abMgr = self._conf.getAbstractMgr()
        iconDisabled = str(Config.getInstance().getSystemIconURL( "disabledSection" ))
        iconEnabled = str(Config.getInstance().getSystemIconURL( "enabledSection" ))
        url = urlHandlers.UHConfCFASwitchMultipleTracks.getURL(self._conf)
        if abMgr.getMultipleTracks():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["miscOptions"] = _("""<a href="%s"><img src="%s" border="0"> _("Allow multiple tracks selection")</a>""") % (str(url), icon)
        url = urlHandlers.UHConfCFAMakeTracksMandatory.getURL(self._conf)
        if abMgr.areTracksMandatory():
            icon = iconEnabled
        else:
            icon = iconDisabled
        vars["miscOptions"] += """<br/><a href="%s"><img src="%s" border="0"> Make track selection mandatory</a>""" % (str(url), icon)
        vars["setStatusURL"]=urlHandlers.UHConfCFAChangeStatus.getURL(self._conf)
        vars["dataModificationURL"]=urlHandlers.UHCFADataModification.getURL(self._conf)
        vars["addTypeURL"]=urlHandlers.UHCFAManagementAddType.getURL(self._conf)
        vars["removeTypeURL"]=urlHandlers.UHCFAManagementRemoveType.getURL(self._conf)
        if abMgr.getCFAStatus():
            vars["changeTo"] = "False"
            vars["status"] = _("ENABLED")
            vars["changeStatus"] = _("DISABLE")
            vars["startDate"]=abMgr.getStartSubmissionDate().strftime("%A %d %B %Y")
            vars["endDate"]=abMgr.getEndSubmissionDate().strftime("%A %d %B %Y")
            vars["announcement"] = abMgr.getAnnouncement()
            vars["disabled"] = ""
            modifDL = abMgr.getModificationDeadline()
            vars["modifDL"] = _("""--_("not specified")--""")
            if modifDL:
                vars["modifDL"] = modifDL.strftime("%A %d %B %Y")
            vars["submitters"] = wcomponents.WPrincipalTable().getHTML(\
                            abMgr.getAuthorizedSubmitterList(), \
                            self._conf, \
                            urlHandlers.UHConfModifCFASelectSubmitter.getURL(),\
                            urlHandlers.UHConfModifCFARemoveSubmitter.getURL(), selectable=False)
            vars["notification"] = _("""
                        <table align="left">
                            <tr>
                                <td align="right"><b> _("To List"):</b></td>
                                <td align="left">%s</td>
                            </tr>
                            <tr>
                                <td align="right"><b> _("Cc List"):</b></td>
                                <td align="left">%s</td>
                            </tr>
                        </table>
                        """)%(", ".join(abMgr.getSubmissionNotification().getToList()) or _("""--_("no TO list")--"""), ", ".join(abMgr.getSubmissionNotification().getCCList()) or _("""--_("no CC list")--"""))
        else:
            vars["changeTo"] = "True"
            vars["status"] = _("DISABLED")
            vars["changeStatus"] = _("ENABLE")
            vars["startDate"] = ""
            vars["endDate"] = ""
            vars["announcement"] = ""
            vars["manage"] = ""
            vars["type"] = ""
            vars["disabled"] = "disabled"
            vars["modifDL"] = ""
            vars["submitters"] = ""
            vars["notification"]=""
        vars["enablePic"]=quoteattr(str(Config.getInstance().getSystemIconURL( "enabledSection" )))
        vars["disablePic"]=quoteattr(str(Config.getInstance().getSystemIconURL( "disabledSection" )))
        vars["abstractFields"]=self._getAbstractFieldsHTML(vars)
        vars["notifTpls"]=self._getNotifTplsHTML()
        vars["addNotifTplURL"]=urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)
        vars["remNotifTplURL"]=urlHandlers.UHAbstractModNotifTplRem.getURL(self._conf)
        return vars


class WPConfModifCFASelectSubmitters(WPConferenceModifAbstractBase):

    def _setActiveTab( self ):
        self._tabCFA.setActive()

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHConfModifCFASelectSubmitter.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfModifCFAAddSubmitter.getURL()
        return wc.getHTML( params )

class WPConfModifSelectChairs(WPConferenceModifBase):

    def _setActiveSideMenuItem(self):
        self._generalSettingsMenuItem.setActive(True)

    def _getPageContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WUserSelection( urlHandlers.UHConfModifSelectChairs.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHConfModifAddChairs.getURL()
        return wc.getHTML( params )

class WPConfModifCFAPreview( WPConferenceModifAbstractBase ):

    def _setActiveTab( self ):
        self._tabCFAPreview.setActive()

    def _getTabContent( self, params ):
        import MaKaC.webinterface.pages.abstracts as abstracts
        wc = abstracts.WAbstractDataModification( self._conf )
        # Simulate fake abstract
        from MaKaC.webinterface.rh.CFADisplay import AbstractData
        ad = AbstractData(self._conf.getAbstractMgr(), {})
        params = ad.toDict()
        params["postURL"] = ""
        return wc.getHTML(params)

class WPConfModifCFA( WPConferenceModifAbstractBase ):

    def _setActiveTab( self ):
        self._tabCFA.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifCFA( self._conf )
        return wc.getHTML()

class WPConfModifCFAAddField( WPConferenceModifAbstractBase ):

    def __init__(self,rh,conf,fieldId):
        WPConferenceModifAbstractBase.__init__(self, rh, conf)
        self._conf = conf
        self._fieldId = fieldId

    def _setActiveTab( self ):
        self._tabCFA.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifCFAAddField( self._conf, self._fieldId )
        return wc.getHTML()

class NotifTplToAddrWrapper:
    _id=""
    _label=""
    _klass=None

    def getId(cls):
        return cls._id
    getId=classmethod(getId)

    def getLabel(cls):
        return _(cls._label)
    getLabel=classmethod(getLabel)

    def getToAddrKlass(cls):
        return cls._klass
    getToAddrKlass=classmethod(getToAddrKlass)

    def addToAddr(cls,tpl):
         tpl.addToAddr(cls._klass())
    addToAddr=classmethod(addToAddr)

    def isSelectedByDefault(cls):
        return False
    isSelectedByDefault = classmethod(isSelectedByDefault)


class NotifTplToAddrSubmitterWrapper(NotifTplToAddrWrapper):

    _id="submitter"
    _klass=review.NotifTplToAddrSubmitter
    _label="Submitters"

    def isSelectedByDefault(cls):
        return True
    isSelectedByDefault = classmethod(isSelectedByDefault)

class NotifTplToAddrPrimaryAuthorsWrapper(NotifTplToAddrWrapper):

    _id="primaryAuthors"
    _label= "Primary authors"
    _klass=review.NotifTplToAddrPrimaryAuthors


class NotifTplToAddrsFactory:

    _avail_toAddrs={
        NotifTplToAddrSubmitterWrapper.getId():NotifTplToAddrSubmitterWrapper,\
        NotifTplToAddrPrimaryAuthorsWrapper.getId():NotifTplToAddrPrimaryAuthorsWrapper}

    def getToAddrList(cls):
        return cls._avail_toAddrs.values()
    getToAddrList=classmethod(getToAddrList)

    def getToAddrById(cls,id):
        return cls._avail_toAddrs.get(id,None)
    getToAddrById=classmethod(getToAddrById)


class WConfModCFANotifTplNew(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def _getErrorHTML(self,errorMsgList):
        if len(errorMsgList)==0:
            return ""
        res=[]
        for error in errorMsgList:
            res.append(self.htmlText(error))
        return """
                <tr align="center">
                    <td bgcolor="white" nowrap colspan="3" style="color:red; padding-bottom:10px; padding-top:10px">
                        <br>
                        <b><font color="red">%s</font></b>
                        <br>
                        <br>
                    </td>
                </tr>"""%"<br>".join(res)

    def _getAvailableTagsHTML(self):
        res=[]
        for var in EmailNotificator.getVarList():
            res.append("""
                <tr>
                    <td width="100%%" nowrap class="blacktext" style="padding-left:10px;padding-right:5px;">%s</td>
                    <td>%s</td>
                </tr>"""%(self.htmlText(var.getLabel()),self.htmlText(var.getDescription())))
        return "".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            res.append("""<input name="toAddrs" type="checkbox" value=%s>%s<br>"""%(quoteattr(toAddr.getId()),self.htmlText(toAddr.getLabel())))
        return "&nbsp;".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)))
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        vars["title"]=quoteattr(str(vars.get("title","")))
        vars["description"]=self.htmlText(vars.get("description",""))
        vars["subject"]=quoteattr(str(vars.get("subject","")))
        vars["body"]=self.htmlText(vars.get("body",""))
        vars["fromAddr"]=quoteattr(str(vars.get("fromAddr","")))
        vars["CCAddrs"]=quoteattr(str(",".join(vars.get("ccList",[]))))
        vars["toAddrs"] = self._getToAddrsHTML()
        vars["vars"]=self._getAvailableTagsHTML()
        return vars


class WConfModCFANotifTplEditData(wcomponents.WTemplated):

    def __init__(self,notifTpl):
        self._notifTpl=notifTpl

    def _getErrorHTML(self,errorMsgList):
        if len(errorMsgList)==0:
            return ""
        res=[]
        for error in errorMsgList:
            res.append(self.htmlText(error))
        return """
                <tr align="center">
                    <td bgcolor="white" nowrap colspan="3" style="color:red; padding-bottom:10px; padding-top:10px">
                        <br>
                        <b><font color="red">%s</font></b>
                        <br>
                        <br>
                    </td>
                </tr>"""%"<br>".join(res)

    def _getAvailableTagsHTML(self):
        res=[]
        for var in EmailNotificator.getVarList():
            res.append("""
                <tr>
                    <td width="100%%" nowrap class="blacktext" style="padding-left:10px;padding-right:5px;">%s</td>
                    <td>%s</td>
                </tr>"""%(self.htmlText(var.getLabel()),self.htmlText(var.getDescription())))
        return "".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            checked = ""
            if self._notifTpl:
                if self._notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                    checked = "checked"
            else:
                if toAddr.isSelectedByDefault():
                    checked = "checked"
            res.append("""<input name="toAddrs" type="checkbox" value=%s %s>%s<br>"""%(quoteattr(toAddr.getId()),checked,self.htmlText(toAddr.getLabel())))
        return "&nbsp;".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplEdit.getURL(self._notifTpl)))
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        if not vars.has_key("title"):
            vars["title"]=quoteattr(str(self._notifTpl.getName()))
        else:
            vars["title"]=quoteattr(str(vars["title"]))
        if not vars.has_key("description"):
            vars["description"]=self.htmlText(self._notifTpl.getDescription())
        else:
            vars["description"]=self.htmlText(vars["description"])
        if not vars.has_key("subject"):
            vars["subject"]=quoteattr(str(self._notifTpl.getTplSubject()))
        else:
            vars["subject"]=quoteattr(str(vars["subject"]))
        if not vars.has_key("body"):
            vars["body"]=self.htmlText(self._notifTpl.getTplBody())
        else:
            vars["body"]=self.htmlText(vars["body"])
        if not vars.has_key("fromAddr"):
            vars["fromAddr"]=quoteattr(str(self._notifTpl.getFromAddr()))
        else:
            vars["fromAddr"]=quoteattr(str(vars["fromAddr"]))
        vars["toAddrs"] = self._getToAddrsHTML()
        if not vars.has_key("ccList"):
            vars["CCAddrs"]=quoteattr(str(",".join(self._notifTpl.getCCAddrList())))
        else:
            vars["CCAddrs"]=quoteattr(str(",".join(vars["ccList"])))
        vars["vars"]=self._getAvailableTagsHTML()
        return vars

class WPModCFANotifTplNew(WPConfModifCFA):

    def _getTabContent(self,params):
        wc = WConfModCFANotifTplNew(self._conf)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)


class WPModCFANotifTplBase(WPConferenceModifBase):

    def __init__(self, rh, notifTpl):
        WPConferenceModifBase.__init__(self, rh, notifTpl.getConference())
        self._notifTpl = notifTpl

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHAbstractModNotifTplDisplay.getURL( self._notifTpl ) )
        self._tabPreview = self._tabCtrl.newTab( "preview", _("Preview"), \
                urlHandlers.UHAbstractModNotifTplPreview.getURL( self._notifTpl ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _setActiveSideMenuItem(self):
        self._abstractMenuItem.setActive(True)

#    def _applyFrame( self, body ):
#        frame = wcomponents.WNotifTPLModifFrame( self._notifTpl, self._getAW() )
#        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
#            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
#            "confModifURLGen": urlHandlers.UHConfModifCFA.getURL}
#        return frame.getHTML( body, **p )

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WNotifTplBannerModif(self._notifTpl).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + body

    def _getTabContent( self, params ):
        return "nothing"


class WPModCFANotifTplDisplay(WPModCFANotifTplBase):

    def __init__(self, rh, notifTpl):
        WPModCFANotifTplBase.__init__(self, rh, notifTpl)
        self._conf = self._notifTpl.getConference()

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent(self, params):
        wc = WConfModCFANotifTplDisplay(self._conf, self._notifTpl)
        return wc.getHTML()


class WPModCFANotifTplEdit(WPModCFANotifTplBase):

    def __init__(self, rh, notifTpl):
        WPConferenceModifBase.__init__(self, rh, notifTpl.getConference())
        self._notifTpl=notifTpl


    def _getTabContent(self, params):
        wc=WConfModCFANotifTplEditData(self._notifTpl)
        params["errorList"]=params.get("errorList",[])
        return wc.getHTML(params)



class WPModCFANotifTplPreview(WPModCFANotifTplBase):

    def _setActiveTab(self):
        self._tabPreview.setActive()

    def _getTabContent(self, params):
        wc = WConfModCFANotifTplPreview(self._notifTpl)
        return wc.getHTML()


class WConfModCFANotifTplPreview(wcomponents.WTemplated):

    def __init__(self,notifTpl):
        self._notifTpl=notifTpl

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        conf=self._notifTpl.getConference()
        if conf.getAbstractMgr().getAbstractList():
            abstract = conf.getAbstractMgr().getAbstractList()[0]
            notif=EmailNotificator().apply(abstract,self._notifTpl)
            vars["from"]=notif.getFromAddr()
            vars["to"]=notif.getToList()
            vars["cc"]=notif.getCCList()
            vars["subject"]=notif.getSubject()
            vars["body"] = notif.getBody()
        else:
            vars["from"] = _("""<center> _("No preview avaible")</center>""")
            vars["to"] = _("""<center> _("No preview avaible")</center>""")
            vars["cc"]= _("""<center> _("No preview avaible")</center>""")
            vars["subject"] = _("""<center> _("No preview avaible")</center>""")
            vars["body"] = _("""<center> _("An abstract must be submitted to display the preview")</center>""")
        vars["cfaURL"]=quoteattr(str(urlHandlers.UHConfModifCFA.getURL(conf)))
        return vars

class NotifTplConditionWrapper:
    _id=""
    _label=""
    _klass=None

    def getId(cls):
        return cls._id
    getId=classmethod(getId)

    def getLabel(cls):
        return _(cls._label)
    getLabel=classmethod(getLabel)

    def getConditionKlass(cls):
        return cls._klass
    getConditionKlass=classmethod(getConditionKlass)

    def addCondition(cls,tpl,**data):
        pass
    addCondition=classmethod(addCondition)

    def needsDialog(cls,**data):
        return False
    needsDialog=classmethod(needsDialog)

    def getDialogKlass(cls):
        return None
    getDialogKlass=classmethod(getDialogKlass)


class NotifTplCondAcceptedWrapper(NotifTplConditionWrapper):

    _id="accepted"
    _label= "in status ACCEPTED"
    _klass=review.NotifTplCondAccepted

    @classmethod
    def addCondition(cls,tpl,**data):
        cType=data.get("contribType","--any--")
        t=data.get("track","--any--")
        tpl.addCondition(cls._klass(track=t,contribType=cType))

    @classmethod
    def needsDialog(cls,**data):
        if data.has_key("contribType") and data["contribType"]!="":
            return False
        return True

    @classmethod
    def getDialogKlass(cls):
        return WPModNotifTplCondAcc


class NotifTplCondRejectedWrapper(NotifTplConditionWrapper):

    _id="rejected"
    _label= "in status REJECTED"
    _klass=review.NotifTplCondRejected

    @classmethod
    def addCondition(cls,tpl,**data):
        tpl.addCondition(cls._klass())

class NotifTplCondMergedWrapper(NotifTplConditionWrapper):

    _id="merged"
    _label= "in status MERGED"
    _klass=review.NotifTplCondMerged

    @classmethod
    def addCondition(cls,tpl,**data):
        tpl.addCondition(cls._klass())


class NotifTplConditionsFactory:

    _avail_conds={
        NotifTplCondAcceptedWrapper.getId():NotifTplCondAcceptedWrapper,\
        NotifTplCondRejectedWrapper.getId():NotifTplCondRejectedWrapper,\
        NotifTplCondMergedWrapper.getId():NotifTplCondMergedWrapper}

    def getConditionList(cls):
        return cls._avail_conds.values()
    getConditionList=classmethod(getConditionList)

    def getConditionById(cls,id):
        return cls._avail_conds.get(id,None)
    getConditionById=classmethod(getConditionById)


class WConfModNotifTplCondAcc(wcomponents.WTemplated):

    def __init__(self,tpl):
        self._notifTpl=tpl

    def _getContribTypeItemsHTML(self):
        res=["""<option value="--any--">--any--</option>""",
                """<option value="--none--">--none--</option>"""]
        for t in self._notifTpl.getConference().getContribTypeList():
            res.append("""<option value=%s>%s</option>"""%(quoteattr(t.getId()),self.htmlText(t.getName())))
        return "".join(res)

    def _getTrackItemsHTML(self):
        res=["""<option value="--any--">--any--</option>""",
                """<option value="--none--">--none--</option>"""]
        for t in self._notifTpl.getConference().getTrackList():
            res.append("""<option value=%s>%s</option>"""%(quoteattr(t.getId()),self.htmlText(t.getTitle())))

        return "".join(res)
    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=urlHandlers.UHConfModNotifTplConditionNew.getURL(self._notifTpl)
        vars["condType"]=quoteattr(str(NotifTplCondAcceptedWrapper.getId()))
        vars["contribTypeItems"]=self._getContribTypeItemsHTML()
        vars["trackItems"]=self._getTrackItemsHTML()
        return vars


class WPModNotifTplCondAcc(WPModCFANotifTplBase):

    def _getTabContent( self, params ):
        wc=WConfModNotifTplCondAcc(self._notifTpl)
        return wc.getHTML()


class WConfModCFANotifTplDisplay(wcomponents.WTemplated):

    def __init__(self, conf, notifTpl):
        self._conf = conf
        self._notifTpl = notifTpl

    def _getConditionItemsHTML(self):
        res=[]
        for cond in NotifTplConditionsFactory.getConditionList():
            res.append("<option value=%s>%s</option>"""%(quoteattr(cond.getId()),self.htmlText(cond.getLabel())))
        return "".join(res)

    def _getConditionsHTML(self):
        res=[]
        for cond in self._notifTpl.getConditionList():
            caption=""
            if isinstance(cond,review.NotifTplCondAccepted):
                track=cond.getTrack()
                if track is None or track=="":
                    track="--none--"
                elif track not in ["--none--","--any--"]:
                    track=track.getTitle()
                cType=cond.getContribType()
                if cType is None or cType=="":
                    cType="--none--"
                elif cType not in ["--none--","--any--"]:
                    cType=cType.getName()
                caption= _("""ACCEPTED - type: %s - track: %s""")%(self.htmlText(cType),self.htmlText(track))
            elif isinstance(cond,review.NotifTplCondRejected):
                caption= _("""REJECTED""")
            elif isinstance(cond,review.NotifTplCondMerged):
                caption= _("""MERGED""")
            res.append("""<input type="checkbox" name="selCond" value=%s>%s"""%(quoteattr(str(cond.getId())),caption))
        return "<br>".join(res)

    def _getToAddrsHTML(self):
        res=[]
        for toAddr in NotifTplToAddrsFactory.getToAddrList():
            if self._notifTpl.hasToAddr(toAddr.getToAddrKlass()):
                res.append("%s"%self.htmlText(toAddr.getLabel()))
        return ", ".join(res)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["name"] = self._notifTpl.getName()
        vars["description"] = self._notifTpl.getDescription()
        vars["from"] = self._notifTpl.getFromAddr()
        vars["toAddrs"] = self._getToAddrsHTML()
        vars["CCAddrs"]=",".join(self._notifTpl.getCCAddrList())
        vars["subject"] = self._notifTpl.getTplSubject()
        vars["body"] = self._notifTpl.getTplBody()
        vars["conditions"]=self._getConditionsHTML()
        vars["availableConditions"]=self._getConditionItemsHTML()
        vars["remConditionsURL"]=quoteattr(str(urlHandlers.UHConfModNotifTplConditionRem.getURL(self._notifTpl)))
        vars["newConditionURL"]=quoteattr(str(urlHandlers.UHConfModNotifTplConditionNew.getURL(self._notifTpl)))
        vars["modifDataURL"]=quoteattr(str(urlHandlers.UHAbstractModNotifTplEdit.getURL(self._notifTpl)))
        return vars


class WCFADataModification(wcomponents.WTemplated):

    def __init__( self, conf ):
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        abMgr = self._conf.getAbstractMgr()
        vars["sDay"] = abMgr.getStartSubmissionDate().day
        vars["sMonth"] = abMgr.getStartSubmissionDate().month
        vars["sYear"] = abMgr.getStartSubmissionDate().year

        vars["eDay"] = abMgr.getEndSubmissionDate().day
        vars["eMonth"] = abMgr.getEndSubmissionDate().month
        vars["eYear"] = abMgr.getEndSubmissionDate().year

        vars["mDay"] = ""
        vars["mMonth"] = ""
        vars["mYear"] = ""
        if abMgr.getModificationDeadline():
            vars["mDay"] = str(abMgr.getModificationDeadline().day)
            vars["mMonth"] = str(abMgr.getModificationDeadline().month)
            vars["mYear"] = str(abMgr.getModificationDeadline().year)

        vars["announcement"] = abMgr.getAnnouncement()
        vars["toList"] = ", ".join(abMgr.getSubmissionNotification().getToList())
        vars["ccList"] = ", ".join(abMgr.getSubmissionNotification().getCCList())
        vars["postURL" ] = urlHandlers.UHCFAPerformDataModification.getURL( self._conf )
        return vars

class WPCFADataModification( WPConferenceModifAbstractBase ):

    def _setActiveTab( self ):
        self._tabCFA.setActive()

    def _getTabContent( self, params ):
        p = WCFADataModification( self._conf )
        return p.getHTML()


class WConfModifProgram(wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        urlGen=urlHandlers.UHTrackModification.getURL
        vars["description"] = self._conf.getProgramDescription()
        vars["modifyDescriptionURL"] = urlHandlers.UHConfModifProgramDescription.getURL(self._conf)
        if len(self._conf.getTrackList()) == 0:
            ht = _("No track defined")
        else:
            ht = []
            upIconURL=Config.getInstance().getSystemIconURL("upArrow")
            downIconURL=Config.getInstance().getSystemIconURL("downArrow")
            for track in self._conf.getTrackList():
                upURL=urlHandlers.UHTrackModMoveUp.getURL(track)
                downURL=urlHandlers.UHTrackModMoveDown.getURL(track)
                ht.append("""
                    <tr>
                        <td style="border-bottom: 1px solid #5294CC;">
                            <table>
                                <tr>
                                    <td>
                                        <a href=%s><img border="0" src=%s alt=""></a>
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <a href=%s><img border="0" src=%s alt=""></a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <td style="border-bottom: 1px solid #5294CC;">
                            <input type="checkbox" name="selTracks" value=%s>
                        </td>
                        <td align="left" style="border-bottom: 1px solid #5294CC;">%s</td>
                        <td align="left" width="30%%" style="border-bottom: 1px solid #5294CC;"><a href=%s>%s</a></td>
                        <td align="left" width="70%%" style="border-bottom: 1px solid #5294CC;">%s</td>
                    </tr>"""%(quoteattr(str(upURL)),quoteattr(str(upIconURL)),\
                                quoteattr(str(downURL)), \
                                quoteattr(str(downIconURL)), \
                                quoteattr(str(track.getId())),\
                                self.htmlText(track.getCode()), \
                                quoteattr(str(urlGen(track))),\
                                self.htmlText(track.getTitle()), \
                                self.htmlText(track.getDescription())))
            ht="""<table cellspacing="0" cellpadding="5" width="100%%">%s</table>"""%"".join(ht)
        vars["listTrack"] = ht
        vars["deleteItemsURL"]=urlHandlers.UHConfDelTracks.getURL(self._conf)
        vars["addTrackURL"]=urlHandlers.UHConfAddTrack.getURL( self._conf )
        return vars


class WPConfModifProgram( WPConferenceModifBase ):

    def _setActiveSideMenuItem( self ):
        self._programMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WConfModifProgram( self._conf )
        return wc.getHTML()


class WConfModifProgramDescription(wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["description"] = self._conf.getProgramDescription()
        vars["submitURL"] = urlHandlers.UHConfModifProgramDescription.getURL(self._conf)
        return vars

class WPConfModifProgramDescription( WPConferenceModifBase ):

    def _setActiveSideMenuItem(self):
        self._programMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WConfModifProgramDescription( self._conf )
        return wc.getHTML()


class WTrackCreation( wcomponents.WTemplated ):

    def __init__( self, targetConf ):
        self.__conf = targetConf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["title"], vars["description"] = "", ""
        vars["locator"] = self.__conf.getLocator().getWebForm()
        return vars



class WPConfAddTrack( WPConfModifProgram ):

    def _setActiveSideMenuItem(self):
        self._programMenuItem.setActive()

    def _getPageContent( self, params ):
        p = WTrackCreation( self._conf )
        pars = {"postURL": urlHandlers.UHConfPerformAddTrack.getURL() }
        return p.getHTML( pars )


class WAbstracts( wcomponents.WTemplated ):

    def __init__( self, conference, filterCrit, sortingCrit, order, fields, menuStatus, websession ):
        self._conf = conference
        self._filterCrit = filterCrit
        self._sortingCrit = sortingCrit
        self._order = order
        self._fields = fields
        self._menuStatus = menuStatus
        self.websession = websession



    def _getURL( self ):
        #builds the URL to the conference management abstract list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)

        #save params in websession
        dict = self.websession.getVar("abstractFilterAndSortingConf%s"%self._conf.getId())
        if not dict:
            dict = {}
        if self._filterCrit.getField( "track" ):
            dict["selTracks"] = self._filterCrit.getField( "track" ).getValues()
            if self._filterCrit.getField( "track" ).getShowNoValue():
                dict["trackShowNoValue"] = "1"
            if self._filterCrit.getField( "track" ).onlyMultiple():
                dict["trackShowMultiple"] = "1"
        #if self._filterCrit.getField( "type" ):
        #    url.addParam( "selTypes", self._filterCrit.getField( "type" ).getValues() )
        if self._filterCrit.getField( "type" ):
            l=[]
            for t in self._filterCrit.getField( "type" ).getValues():
                if t:
                    l.append(t.getId())
            dict["selTypes"] = l
            if self._filterCrit.getField( "type" ).getShowNoValue():
                dict["typeShowNoValue"] = "1"
        if self._filterCrit.getField("acc_track"):
            dict["selAccTracks"] = self._filterCrit.getField("acc_track").getValues()
            if self._filterCrit.getField("acc_track").getShowNoValue():
                dict["accTrackShowNoValue"] = "1"
        if self._filterCrit.getField( "status" ):
            dict["selStatus"] = self._filterCrit.getField( "status" ).getValues()
        if self._filterCrit.getField("acc_type"):
            l=[]
            for t in self._filterCrit.getField("acc_type").getValues():
                if t:
                    l.append(t.getId())
            dict["selAccTypes"] = l
            if self._filterCrit.getField("acc_type").getShowNoValue():
                dict["accTypeShowNoValue"] = "1"
        if self._filterCrit.getField( "comment" ):
            dict["selOnlyComments"] = "1"
        if self._sortingCrit is not None and self._sortingCrit.getField():
            dict["sortBy"] = self._sortingCrit.getField().getId()
        #url.addParam("order","down")
        dict["order"] = self._order
        dict["OK"] =  "1"
        if self._authSearch.strip!="":
            dict["authSearch"] = self._authSearch
        #url.setSegment("abstracts")
        for key in self._fields.keys():
            if self._fields[key][1]:
                dict["show%s"%key] = "checked"
        self.websession.setVar("abstractFilterAndSortingConf%s"%self._conf.getId(), dict)
        return url

    def _getTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="trackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and t.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selTracks" value=%s%s> (%s) %s\n"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="typeShowNoValue"%s> --_("not specified")--""")%checked]
        for type in self._conf.getContribTypeList():
            checked = ""
            if field is not None and type in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selTypes" value=%s%s> %s"""%(quoteattr(type.getId()), checked, self.htmlText(type.getName())) )
        return l

    def _getAccTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="accTrackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and t.getId() in field.getValues():
                checked=" checked"
            l.append("""<input type="checkbox" name="selAccTracks" value=%s%s> (%s) %s"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getAccContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="accTypeShowNoValue"%s> --_("not specified")--""")%checked]
        for type in self._conf.getContribTypeList():
            checked = ""
            if field is not None and type in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selAccTypes" value=%s%s> %s"""%(quoteattr(type.getId()),checked,self.htmlText(type.getName())))
        return l

    def _getStatusFilterItemList( self ):
        l = []
        for status in AbstractStatusList().getStatusList():
            checked = ""
            statusId = AbstractStatusList().getId( status )
            statusCaption = AbstractStatusList().getCaption( status )
            statusCode=AbstractStatusList().getCode(status)
            statusIconURL= AbstractStatusList().getIconURL( status )
            field=self._filterCrit.getField("status")
            if field is not None and statusId in field.getValues():
                checked = "checked"
            imgHTML = """<img src=%s border="0" alt="">"""%(quoteattr(str(statusIconURL)))
            l.append( """<input type="checkbox" name="selStatus" value=%s%s>%s (%s) %s"""%(quoteattr(statusId),checked,imgHTML,self.htmlText(statusCode),self.htmlText(statusCaption)))
        return l

    def _getOthersFilterItemList( self ):
        checkedShowMultiple, checkedShowComments = "", ""
        track_field=self._filterCrit.getField("track")
        if track_field is not None and track_field.onlyMultiple():
            checkedShowMultiple = " checked"
        if self._filterCrit.getField("comment") is not None:
            checkedShowComments = " checked"
        l = [ _("""<input type="checkbox" name="trackShowMultiple"%s> _("only multiple tracks")""")%checkedShowMultiple,
                _("""<input type="checkbox" name="selOnlyComments"%s> _("only with comments")""")%checkedShowComments]
        return l

    def _getFieldToShow(self):
        if not self._fields:
            self._fields = {"ID": [ _("ID"), "checked"],
                            "PrimaryAuthor": [ _("Primary Author"), "checked"],
                            "Tracks": [ _("Tracks"), "checked"],
                            "Type": [ _("Type"), "checked"],
                            "Status": [ _("Status"), "checked"],
                            "AccTrack": [ _("Acc. Track"), "checked"],
                            "AccType": [ _("Acc. Type"), "checked"],
                            "SubmissionDate": [ _("Submission Date"), "checked"]}
        l = []
        for key in ["ID", "PrimaryAuthor", "Tracks", "Type", "Status", "AccTrack", "AccType", "SubmissionDate"]:
            l.append("""<input type="checkbox" name="show%s" %s value="checked">%s"""%(key, self._fields[key][1], self._fields[key][0]))
        return l

    def _getAbstractTitleBar(self):
        l = []
        if self._fields["ID"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href=%(numberSortingURL)s> _("ID")</a> %(numberImg)s</td>"""))
        #if self._fields["Title"] == "checked":
        l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"> _("Title")</td>"""))
        if self._fields["PrimaryAuthor"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"> _("Primary Author(s)")</td>"""))
        if self._fields["Tracks"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"> _("Tracks")</td>"""))
        if self._fields["Type"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"><a href=%(typeSortingURL)s> _("Type")</a> %(typeImg)s</td>"""))
        if self._fields["Status"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"><a href=%(statusSortingURL)s> _("Status")</a><b> %(statusImg)s</td>"""))
        if self._fields["AccTrack"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"> _("Acc. Track")</td>"""))
        if self._fields["AccType"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"> _("Acc. Type")</td>"""))
        if self._fields["SubmissionDate"][1] == "checked":
            l.append( _("""<td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"><a href=%(dateSortingURL)s> _("Submission date")</a> %(dateImg)s</td>"""))

        return "\n".join(l)

    def _getOpenMenuURL(self):
        url = urlHandlers.UHConfAbstractManagmentOpenMenu.getURL(self._conf)
        url.addParam("currentURL", self._getURL())
        return url

    def _getCloseMenuURL(self):
        url = urlHandlers.UHConfAbstractManagmentCloseMenu.getURL(self._conf)
        url.addParam("currentURL", self._getURL())
        return url

    def _getMenu(self):
        if self._menuStatus == "open":
            menu = _("""<table width="100%%" align="center" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td class="groupTitle"><a href="%(closeMenuURL)s"><img src=%(openMenuImg)s alt="_("hide menu")" border="0"></a> _("Filtering criteria")</td>
                    </tr>
                    <tr>
                        <td>
                            <table width="100%%">
                                <tr>
                                    <td>
                                        <table align="center" cellspacing="10" width="100%%">
                                            <tr>
                                                <td colspan="5" class="titleCellFormat"> _("Author search") <input type="text" name="authSearch" value=%(authSearch)s></td>
                                            </tr>
                                            <tr>
                                                <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px"> _("show tracks") %(checkAllTracks)s%(uncheckAllTracks)s</td>
                                                <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("show types") %(checkAllTypes)s%(uncheckAllTypes)s</td>
                                                <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("show in status") %(checkAllStatus)s%(uncheckAllStatus)s</td>
                                                <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("show acc. tracks") %(checkAllAccTracks)s%(uncheckAllAccTracks)s</td>
                                                <td align="left" nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("show acc. types") %(checkAllAccTypes)s%(uncheckAllAccTypes)s</td>
                                                <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("others")</td>
                                            </tr>
                                            <tr>
                                                <td valign="top" style="border-right:1px solid #777777;">%(tracks)s</td>
                                                <td valign="top" style="border-right:1px solid #777777;">%(types)s</td>
                                                <td valign="top" style="border-right:1px solid #777777;">%(status)s</td>
                                                <td valign="top" style="border-right:1px solid #777777;">%(accTracks)s</td>
                                                <td valign="top" style="border-right:1px solid #777777;">%(accTypes)s</td>
                                                <td valign="top" style="border-right:1px solid #777777;">%(others)s</td>
                                            </tr>
                                            <tr>
                                                <td align="left" colspan="6" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("show fields") %(checkAllFields)s%(uncheckAllFields)s</td>
                                            </tr>
                                            <tr>
                                                <td valign="top" colspan="6" style="border-right:1px solid #777777;">%(showFields)s</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="border-top:1px solid #777777;padding:10px"><input type="submit" class="btn" name="OK" value="_("apply filter")"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>""")
        else :
            menu = _("""<table width="100%%" align="center" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td class="groupTitle"><a href="%(openMenuURL)s"><img src=%(closeMenuImg)s alt="Show menu" border="0"></a> _("Filtering criteria")</td>
                    </tr>
                    <tr><td align="left"><small> _("Note that you can open the filtering criteria by clicking in the icon") <img src=%(closeMenuImg)s alt="Show menu" border="0"> _("which is above this line").</small></td></tr>
                </table>""")

        return menu

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["abstractSelectionAction"]=quoteattr(str(urlHandlers.UHAbstractConfSelectionAction.getURL(self._conf)))
        vars["abstractsPDFURL"]=quoteattr(str(urlHandlers.UHAbstractsConfManagerDisplayPDF.getURL(self._conf)))
        vars["abstractsXMLURL"]=quoteattr(str(urlHandlers.UHAbstractsConfManagerDisplayXML.getURL(self._conf)))
        vars["participantListURL"]=quoteattr(str(urlHandlers.UHAbstractsConfManagerDisplayParticipantList.getURL(self._conf)))
        vars["tracks"] = "<br>".join(self._getTrackFilterItemList())
        vars["types"] = "<br>".join(self._getContribTypeFilterItemList())
        vars["status"] = "<br>".join(self._getStatusFilterItemList())
        vars["others"] = "<br>".join(self._getOthersFilterItemList())
        vars["accTypes"]="<br>".join(self._getAccContribTypeFilterItemList())
        vars["accTracks"]="<br>".join(self._getAccTrackFilterItemList())
        vars["confId"] = self._conf.getId()
        self._authSearch=vars.get("authSearch","")
        vars["authSearch"]=quoteattr(str(self._authSearch))

        vars["showFields"] = " ".join(self._getFieldToShow())

        vars["currentSorting"] = ""
        sortingField=None
        if self._sortingCrit is not None:
            sortingField=self._sortingCrit.getField()

        url = self._getURL()
        url.addParam("sortBy", "type")
        vars["typeImg"] = ""
        if sortingField and sortingField.getId() == "type":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="type">"""
            if self._order == "down":
                vars["typeImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["typeImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["typeSortingURL"] = quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy", "status")
        vars["statusImg"] = ""
        if sortingField and sortingField.getId() == "status":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="status">"""
            if self._order == "down":
                vars["statusImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["statusImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["statusSortingURL"] = quoteattr( str( url ) )

        url=self._getURL()
        url.addParam("sortBy","number")
        vars["numberImg"]=""
        if sortingField and sortingField.getId() == "number":
                vars["currentSorting"] = """<input type="hidden" name="sortBy" value="number">"""
                if self._order == "down":
                    vars["numberImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    vars["numberImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
        vars["numberSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "date")

        vars["dateImg"] = ""
        if sortingField and sortingField.getId() == "date":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="date">"""
            if self._order == "down":
                vars["dateImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["dateImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["dateSortingURL"] = quoteattr( str( url ) )




        l = []
        abstractsToPrint = []
        f = filters.SimpleFilter( self._filterCrit, self._sortingCrit )
        abstractList=f.apply(self._conf.getAbstractMgr().getAbstractsMatchingAuth(self._authSearch))
        for abstract in abstractList:
            tracks = []
            for track in abstract.getTrackListSorted():
                tracks.append("%s"%self.htmlText(track.getCode()))

            s=abstract.getCurrentStatus()
            status=AbstractStatusList().getCode(s.__class__ )
            statusColor=AbstractStatusList().getColor(s.__class__)
            statusIconURL=AbstractStatusList().getIconURL(s.__class__)
            statusIconHTML = """<img src=%s border="0" alt="">"""%quoteattr(str(statusIconURL))
            contribType = abstract.getContribType()
            contribTypeName = _("""--_("not specified")--""")
            if contribType:
                contribTypeName = contribType.getName()
            subDate = abstract.getSubmissionDate().strftime("%d %B %Y")
            comments = ""
            if abstract.getComments():
                comments = _(""" <img src=%s alt="_("The submitter filled some comments")">""")%(quoteattr(Config.getInstance().getSystemIconURL("comments")))
            accTrack,accType="&nbsp;","&nbsp;"
            if isinstance(s,review.AbstractStatusAccepted):
                if s.getTrack() is not None:
                    accTrack=self.htmlText(s.getTrack().getCode())
                if s.getType() is not None:
                    accType=self.htmlText(s.getType().getName())
            elif isinstance(s,review.AbstractStatusProposedToAccept):
                if s.getTrack() is not None:
                    accTrack=self.htmlText(s.getTrack().getCode())
                if s.getType() is not None:
                    accType=self.htmlText(s.getType().getName())
            urlGen=urlHandlers.UHCFAAbstractManagment.getURL
            authList = []
            for auth in abstract.getPrimaryAuthorList():
                if auth.getFullName():
                    authList.append(auth.getFullName())
            PAuthors = "<br>".join(authList)

            m = []
            if self._fields["ID"][1] == "checked":
                m.append("""<td class="abstractLeftDataCell" nowrap>%s%s</td>"""%(abstract.getId(), comments))
            #if self._fields["Title"] == "checked":
            m.append("""<td class="abstractDataCell">
                        <input type="checkbox" name="abstracts" value=%s><a href=%s>%s</a></td>"""%(abstract.getId(), quoteattr(str(urlGen(abstract))), self.htmlText(abstract.getTitle())))
            if self._fields["PrimaryAuthor"][1] == "checked":
                m.append("""<td class="abstractDataCell">%s</td>"""%PAuthors)
            if self._fields["Tracks"][1] == "checked":
                m.append("""<td class="abstractDataCell">%s</td>"""%("<br>".join(tracks) or "&nbsp;"))
            if self._fields["Type"][1] == "checked":
                m.append("""<td class="abstractDataCell">%s</td>"""%self.htmlText(contribTypeName))
            if self._fields["Status"][1] == "checked":
                m.append("""<td class="abstractDataCell" nowrap>%s %s</td>"""%(statusIconHTML,status))
            if self._fields["AccTrack"][1] == "checked":
                m.append("""<td class="abstractDataCell">%s</td>"""%accTrack)
            if self._fields["AccType"][1] == "checked":
                m.append("""<td class="abstractDataCell">%s</td>"""%accType)
            if self._fields["SubmissionDate"][1] == "checked":
                m.append("""<td class="abstractDataCell" nowrap>%s</td>"""%subDate)
            if len(m) == 0:
                m = ["<td></td>"]
            l.append("<tr>%s</tr>"%"\n".join(m))
            abstractsToPrint.append("""<input type="hidden" name="abstracts" value="%s">"""%abstract.getId())
        if self._order =="up":
            l.reverse()
        vars["abstracts"] = "".join( l )

        l = []
        for key in self._fields.keys():
            if self._fields[key]:
                l.append("""<input type="hidden" name="fieldsToPrint" value="%s">"""%key)
        vars["fieldsToPrint"] = "".join( l )
        vars["number"] = str(len(abstractList))
        vars["accessAbstract"] = quoteattr(str(urlHandlers.UHAbstractDirectAccess.getURL(self._conf)))
        vars["abstractsToPrint"] = "\n".join(abstractsToPrint)

        url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)
        url.setSegment( "abstracts" )
        vars["filterPostURL"] = quoteattr(str(url))
        vars["newAbstractURL"]=quoteattr(str(urlHandlers.UHConfModNewAbstract.getURL(self._conf)))
        l = []
        for tpl in self._conf.getAbstractMgr().getNotificationTplList():
            l.append("""<option value="%s">%s</option>"""%(tpl.getId(), tpl.getName()))

        vars["closeMenuURL"] = self._getCloseMenuURL()
        vars["closeMenuImg"] = quoteattr(Config.getInstance().getSystemIconURL("openMenu"))
        vars["openMenuURL"] = self._getOpenMenuURL()
        vars["openMenuImg"] = quoteattr(Config.getInstance().getSystemIconURL("closeMenu"))

        vars["checkAllTracks"] = """<img src=%s border="0" alt="Select all" onclick="selecAllTracks()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAllTracks"] = """<img src=%s border="0" alt="Unselect all" onclick="unselecAllTracks()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))

        vars["checkAllTypes"] = """<img src=%s border="0" alt="Select all" onclick="selecAllTypes()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAllTypes"] = """<img src=%s border="0" alt="Unselect all" onclick="unselecAllTypes()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))

        vars["checkAllStatus"] = """<img src=%s border="0" alt="Select all" onclick="selecAllStatus()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAllStatus"] = """<img src=%s border="0" alt="Unselect all" onclick="unselecAllStatus()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))

        vars["checkAllAccTracks"] = """<img src=%s border="0" alt="Select all" onclick="selecAllAccTracks()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAllAccTracks"] = """<img src=%s border="0" alt="Unselect all" onclick="unselecAllAccTracks()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))

        vars["checkAllAccTypes"] = """<img src=%s border="0" alt="Select all" onclick="selecAllAccTypes()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAllAccTypes"] = """<img src=%s border="0" alt="Unselect all" onclick="unselecAllAccTypes()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))

        vars["checkAllFields"] = """<img src=%s border="0" alt="Select all" onclick="selecAllFields()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAllFields"] = """<img src=%s border="0" alt="Unselect all" onclick="unselecAllFields()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))

        vars["menu"] = self._getMenu()%vars
        vars["abstractTitleBar"] = self._getAbstractTitleBar()%vars

        abstracts = []
        for abstract in abstractList :
            abstracts.append(abstract.getId())
        if len(abstracts) > 0 :
            generateExcelIcon = Config.getInstance().getSystemIconURL("excel")
            generateExcelURL = urlHandlers.UHAbstractsConfManagerDisplayExcel.getURL(self._conf)
            hiddenAbstracts=[]
            for abs in abstracts:
                hiddenAbstracts.append("""<input type="hidden" name="abstracts" value="%s">"""%(abs))
            vars["generateExcel"] = """<form action=%s method="POST" style="margin-bottom:0px;">%s<input type="submit" class="btn" value="" style="cursor:pointer;text-decoration: none; background-color:transparent;color: #000000;background-image:url(%s); background-repeat:no-repeat;border:0px; width:100px;"></form>"""%(quoteattr(str(generateExcelURL)),"".join(hiddenAbstracts), generateExcelIcon)
        else :
            vars["generateExcel"] = ""




        return vars

class WPConfAbstractList( WPConferenceModifAbstractBase ):

    def __init__(self, rh, conf, msg):
        self._msg = msg
        WPConferenceModifAbstractBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        order = params.get("order","down")
        websession = self._rh._getSession()
        wc = WAbstracts( self._conf, params.get("filterCrit", None ), \
                            params.get("sortingCrit", None),order, params.get("fields", None), params.get("menuStatus", None), websession )
        p = {"authSearch":params.get("authSearch","")}
        return wc.getHTML( p )

    def _setActiveTab(self):
        self._tabAbstractList.setActive()


class WPModNewAbstract(WPConfAbstractList):

    def __init__(self,rh,conf,abstractData):
        WPConfAbstractList.__init__(self, rh, conf,"")
        self._abstractData=abstractData

    def _getTabContent( self, params ):
        wc=wcomponents.WConfModAbstractEditData(self._conf,self._abstractData)
        p={"postURL": urlHandlers.UHConfModNewAbstract.getURL(self._conf)}
        return _("""
            <table width="95%%" cellpadding="0" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777">
            <tr>
            <td class="groupTitle">
                        _("Submitting a new abstract")
                    </td>
                </tr>
                %s
            </table>
                """)%wc.getHTML(p)
        return wc.getHTML()


class WConfModAbstractsMerge(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def _getErrorHTML(self,errorMsgList):
        if len(errorMsgList)==0:
            return ""
        res=[]
        for error in errorMsgList:
            res.append("- %s"%self.htmlText(error))
        return """
                <tr><td>&nbsp;</td></tr>
                <tr align="center">
                    <td colspan="2">
                        <table align="center" valign="middle" style="padding:10px; border:1px solid #5294CC; background:#F6F6F6">
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td><font color="red">%s</font></td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                        </table>
                    </td>
                </tr>
                <tr><td>&nbsp;</td></tr>"""%"<br>".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["errorMsg"]=self._getErrorHTML(vars.get("errorMsgList",[]))
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModAbstractsMerge.getURL(self._conf)))
        vars["selAbstracts"]=",".join(vars.get("absIdList",[]))
        vars["targetAbs"]=quoteattr(str(vars.get("targetAbsId","")))
        vars["inclAuthChecked"]=""
        if vars.get("inclAuth",False):
            vars["inclAuthChecked"]=" checked"
        vars["comments"]=self.htmlText(vars.get("comments",""))
        vars["notifyChecked"]=""
        if vars.get("notify",False):
            vars["notifyChecked"]=" checked"
        return vars


class WPModMergeAbstracts(WPConfAbstractList):

    def __init__(self,rh,conf):
        WPConfAbstractList.__init__(self, rh, conf,"")

    def _getTabContent(self,params):
        wc=WConfModAbstractsMerge(self._conf)
        p={"absIdList":params.get("absIdList",[]),
            "targetAbsId":params.get("targetAbsId",""),
            "inclAuth":params.get("inclAuth",False),
            "comments":params.get("comments",""),
            "errorMsgList":params.get("errorMsgList",[]),
            "notify":params.get("notify",True),
            }
        return wc.getHTML(p)


class WPConfModifDisplayBase( WPConferenceModifBase ):

    def _createTabCtrl( self ):

        self._tabCtrl = wcomponents.TabControl()

        self._tabDisplayCustomization = self._tabCtrl.newTab( "dispCustomization", _("Layout customization"), \
                urlHandlers.UHConfModifDisplayCustomization.getURL( self._conf ) )
        self._tabDisplayConfHeader = self._tabCtrl.newTab( "displConfHeader", _("Conference header"), \
                urlHandlers.UHConfModifDisplayConfHeader.getURL( self._conf ) )
        self._tabDisplayMenu = self._tabCtrl.newTab( "dispMenu", _("Menu"), \
                urlHandlers.UHConfModifDisplayMenu.getURL( self._conf ) )
        self._tabDisplayResources = self._tabCtrl.newTab( "dispResources", _("Images"), \
                urlHandlers.UHConfModifDisplayResources.getURL( self._conf ) )

        self._setActiveTab()

    def _getPageContent( self, params ):
        self._createTabCtrl()

        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return html

    def _getTabContent( self ):
        return "nothing"

    def _setActiveSideMenuItem( self ):
        self._layoutMenuItem.setActive()

class WPConfModifDisplay( WPConfModifDisplayBase ):

    def __init__(self, rh, conf, linkId, formatOption=None, optionalParams={}):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._linkId = linkId
        self._formatOption = formatOption
        self._menu=displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        if linkId:
            self._link = self._menu.getLinkById(linkId)
        else:
            self._link = self._menu
        self._optionalParams=optionalParams

    def _getTabContent( self, params ):
        wc = WConfModifDisplay( self._conf, self._linkId, self._formatOption )
        return wc.getHTML(self._optionalParams)

    def _getHeadContent( self ):
        #This is used for fetching the css file for management - display
        path = baseurl = self._getBaseURL()
        saveurl = urlHandlers.UHSavePic.getURL(self._conf)
        printCSS = """
        <link rel="stylesheet" type="text/css" href="%s/css/ModifDisplay.css" >
            """ %(path)
        return printCSS

class WPConfModifDisplayCustomization( WPConfModifDisplayBase ):

    def __init__(self, rh, conf):
        WPConfModifDisplayBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        wc = WConfModifDisplayCustom( self._conf )
        return wc.getHTML()

    def _setActiveTab( self ):
        self._tabDisplayCustomization.setActive()

class WConfModifDisplayCustom(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf
        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        self._format = dm.getFormat()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["saveLogo"]=urlHandlers.UHSaveLogo.getURL(self._conf)
        vars["logoURL"]=""
        if self._conf.getLogo():
            vars["logoURL"] = urlHandlers.UHConferenceLogo.getURL( self._conf)

        vars["formatTitleTextColor"] = WFormatColorOptionModif("titleTextColor", self._format, self._conf, 3).getHTML()
        vars["formatTitleBgColor"] = WFormatColorOptionModif("titleBgColor", self._format, self._conf, 4).getHTML()

        #indico-style "checkboxes"
        vars["enablePic"]=quoteattr(str(Config.getInstance().getSystemIconURL( "enabledSection" )))
        vars["disablePic"]=quoteattr(str(Config.getInstance().getSystemIconURL( "disabledSection" )))
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")

        # Set up the logo of the conference
        vars["logoIconURL"] = Config.getInstance().getSystemIconURL("logo")
        if vars["logoURL"]:
            vars["logo"] = """<img heigth=\"95\" width=\"150\" src="%s" alt="%s" border="0">"""%(vars["logoURL"], self._conf.getTitle())
            vars["removeLogo"] = _("""<form action=%s method="POST"><input type="submit" class="btn" value="_("remove")"></form>""")%quoteattr(str(urlHandlers.UHRemoveLogo.getURL(self._conf)))
        else:
            vars["logo"] = "<em>No logo has been saved for this conference</em>"
            vars["removeLogo"] = ""


        #creating css part
        vars["saveCSS"]=urlHandlers.UHSaveCSS.getURL(self._conf)
        sm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()
        if sm.getLocalCSS():
            vars["cssDownload"] = sm.getCSS().getURL()
        else:
            vars["css"] = ""
            vars["cssDownload"] = ""
        vars["removeCSS"] = str(urlHandlers.UHRemoveCSS.getURL(self._conf))
        vars["previewURL"]= urlHandlers.UHConfModifPreviewCSS.getURL(self._conf)


        if sm.getCSS():
            vars["currentCSSFileName"] = sm.getCSS().getFileName()
        else:
            vars["currentCSSFileName"] = ""
        return vars

class WPConfModifDisplayMenu( WPConfModifDisplayBase ):

    def __init__(self, rh, conf, linkId):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._linkId = linkId

    def _getTabContent( self, params ):
        wc = WConfModifDisplayMenu( self._conf, self._linkId )
        return wc.getHTML()

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

class WConfModifDisplayMenu(wcomponents.WTemplated):

    def __init__(self, conf, linkId):
        self._conf = conf
        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        self._menu = dm.getMenu()
        self._link = self._menu.getLinkById(linkId)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["addLinkURL"]=quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._conf)))
        vars["addPageURL"]=quoteattr(str(urlHandlers.UHConfModifDisplayAddPage.getURL(self._conf)))
        vars["addSpacerURL"]=quoteattr(str(urlHandlers.UHConfModifDisplayAddSpacer.getURL(self._conf)))
        vars["menuDisplay"] = ConfEditMenu(self._menu, urlHandlers.UHConfModifDisplayMenu.getURL).getHTML()
        vars["confId"] = self._conf.getId()
        if self._link:
            if isinstance(self._link, displayMgr.SystemLink):
                p = {
                        "dataModificationURL": quoteattr(str(urlHandlers.UHConfModifDisplayModifySystemData.getURL(self._link))), \
                        "moveUpURL": quoteattr(str(urlHandlers.UHConfModifDisplayUpLink.getURL(self._link))), \
                        "imageUpURL": quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))), \
                        "moveDownURL": quoteattr(str(urlHandlers.UHConfModifDisplayDownLink.getURL(self._link))), \
                        "imageDownURL": quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
                    }
                vars["linkEdition"] = WSystemLinkModif(self._link).getHTML(p)
            elif isinstance(self._link, displayMgr.Spacer):
                p = {
                        "removeLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayRemoveLink.getURL(self._link))), \
                        "toggleLinkStatusURL":  quoteattr(str(urlHandlers.UHConfModifDisplayToggleLinkStatus.getURL(self._link))), \
                        "moveUpURL": quoteattr(str(urlHandlers.UHConfModifDisplayUpLink.getURL(self._link))), \
                        "imageUpURL": quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))), \
                        "moveDownURL": quoteattr(str(urlHandlers.UHConfModifDisplayDownLink.getURL(self._link))), \
                        "imageDownURL": quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
                    }
                vars["linkEdition"] = WSpacerModif(self._link).getHTML(p)
            elif isinstance(self._link, displayMgr.ExternLink):
                p = {
                        "dataModificationURL": quoteattr(str(urlHandlers.UHConfModifDisplayModifyData.getURL(self._link))), \
                        "removeLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayRemoveLink.getURL(self._link))), \
                        "addSubLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._link))), \
                        "toggleLinkStatusURL":  quoteattr(str(urlHandlers.UHConfModifDisplayToggleLinkStatus.getURL(self._link))), \
                        "moveUpURL": quoteattr(str(urlHandlers.UHConfModifDisplayUpLink.getURL(self._link))), \
                        "imageUpURL": quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))), \
                        "moveDownURL": quoteattr(str(urlHandlers.UHConfModifDisplayDownLink.getURL(self._link))), \
                        "imageDownURL": quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))) }
                vars["linkEdition"] = WLinkModif(self._link).getHTML(p)
            else:
                p = {
                        "dataModificationURL": quoteattr(str(urlHandlers.UHConfModifDisplayModifyData.getURL(self._link))), \
                        "removeLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayRemoveLink.getURL(self._link))), \
                        "toggleLinkStatusURL":  quoteattr(str(urlHandlers.UHConfModifDisplayToggleLinkStatus.getURL(self._link))), \
                        "toggleHomePageURL":  quoteattr(str(urlHandlers.UHConfModifDisplayToggleHomePage.getURL(self._link))), \
                        "moveUpURL": quoteattr(str(urlHandlers.UHConfModifDisplayUpLink.getURL(self._link))), \
                        "imageUpURL": quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))), \
                        "moveDownURL": quoteattr(str(urlHandlers.UHConfModifDisplayDownLink.getURL(self._link))), \
                        "imageDownURL": quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))) }
                vars["linkEdition"] = WPageLinkModif(self._link).getHTML(p)
        else:
            vars["linkEdition"] = _("""<center><b> _("Click on an item of the menu to edit it")</b></center>""")

        return vars

class WPConfModifDisplayResources( WPConfModifDisplayBase ):

    def __init__(self, rh, conf):
        WPConfModifDisplayBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        wc = WConfModifDisplayResources( self._conf)
        return wc.getHTML()

    def _setActiveTab( self ):
        self._tabDisplayResources.setActive()

class WConfModifDisplayResources(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["savePic"]=urlHandlers.UHSavePic.getURL(self._conf)
        #creating picture items for each saved picture
        vars["picsList"] = []
        im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getImagesManager()
        for pic in im.getPicList().values():
            vars["picsList"].append({"id":pic.getId(),
                                    "picURL": str(urlHandlers.UHConferencePic.getURL(pic))})
        return vars

class WPConfModifDisplayConfHeader( WPConfModifDisplayBase ):

    def __init__(self, rh, conf, optionalParams={}):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._optionalParams=optionalParams

    def _getTabContent( self, params ):
        wc = WConfModifDisplayConfHeader( self._conf)
        return wc.getHTML(self._optionalParams)

    def _setActiveTab( self ):
        self._tabDisplayConfHeader.setActive()

class WConfModifDisplayConfHeader(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf
        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        self._tickerTape=dm.getTickerTape()
        self._searchEnabled = dm.getSearchEnabled()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        #indico-style "checkboxes"
        vars["enablePic"]=quoteattr(str(Config.getInstance().getSystemIconURL( "enabledSection" )))
        vars["disablePic"]=quoteattr(str(Config.getInstance().getSystemIconURL( "disabledSection" )))
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")

        # ------ Ticker Tape: ------
        # general
        vars["tickertapeURL"]=quoteattr(str(urlHandlers.UHTickerTapeAction.getURL(self._conf)))
        status= _("DISABLED")
        btnLabel= _("Enable")
        statusColor = "#612828"
        if self._tickerTape.isSimpleTextEnabled():
            statusColor = "#286135"
            status= _("ENABLED")
            btnLabel= _("Disable")
        vars["status"]= """<span style="color: %s;">%s</span>""" %(statusColor,status)
        vars["statusBtn"]=btnLabel
        # annoucements
        urlNP=urlHandlers.UHTickerTapeAction.getURL(self._conf)
        urlNP.addParam("nowHappening", "action")
        if self._tickerTape.isNowHappeningEnabled():
            vars["nowHappeningIcon"]=vars["enablePic"]
            vars["nowHappeningTextIcon"]=enabledText
        else:
            vars["nowHappeningIcon"]=vars["disablePic"]
            vars["nowHappeningTextIcon"]=disabledText
        vars["nowHappeningURL"]=quoteattr("%s#tickerTape"%str(urlNP))

        urlST=urlHandlers.UHTickerTapeAction.getURL(self._conf)
        urlST.addParam("simpleText", "action")
        vars["simpleTextURL"]=quoteattr("%s#tickerTape"%urlST)
        # simple ext
        vars["text"]=quoteattr(self._tickerTape.getText())
        if not vars.has_key("modifiedText"):
            vars["modifiedText"]=""
        else:
            vars["modifiedText"]= _("""<font color="green"> _("(text saved)")</font>""")

        #enable or disable the contribution search feature
        urlSB=urlHandlers.UHConfModifToggleSearch.getURL(self._conf)
        if self._searchEnabled:
            vars["searchBoxIcon"]=vars["enablePic"]
            vars["searchBoxTextIcon"]=enabledText
        else:
            vars["searchBoxIcon"]=vars["disablePic"]
            vars["searchBoxTextIcon"]=disabledText
        vars["searchBoxURL"]=quoteattr(str(urlSB))


        return vars

class WFormatColorOptionModif(wcomponents.WTemplated):

    def __init__(self, formatOption, format, conf, formId=4):
        self._formatOption = formatOption
        self._format = format
        self._conf = conf

        # The form number on the page... used for the color picker
        self._formId = formId

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        value = self._format.getFormatOption(self._formatOption)

        urlChangeColor = value["url"].getURL(self._conf)
        urlChangeColor.addParam("formatOption",self._formatOption)

        vars["changeColorURL"] = quoteattr(str(urlChangeColor))
        vars["colorCode"] = value["code"]
        vars["formatOption"] = self._formatOption
        vars["colorChartIcon"] = Config.getInstance().getSystemIconURL("colorchart")

        url=urlHandlers.UHSimpleColorChart.getURL()
        url.addParam("colorCodeTarget", "colorCode")
        url.addParam("colorPreviewTarget", "colorpreview")
        url.addParam("formId", self._formId)

        vars["colorChartURL"] = url
        return vars

class ConfEditMenu:

    def __init__(self, menu, modifURLGen=None):
        self._menu = menu
        self._linkModifHandler = modifURLGen

    def getHTML(self):
        html = ["<table>"]
        for link in self._menu.getLinkList():
            html.append(self._getLinkHTML(link))
        html.append("</table>")
        return "".join(html)

    def _getLinkHTML(self, link, indent=""):
        if self._menu.linkHasToBeDisplayed(link):
            disabled = _("""<font size="-1" color="red"> _("(disabled)")</font>""")
            if link.isEnabled():
                disabled = ""
            if link.getType() == "spacer":
                html = """<tr><td></td><td nowrap><a href="%s">[%s]</a>%s</td></tr>\n"""%(self._linkModifHandler(link), link.getName(), disabled)
            else:
                system = "<font size=-1>E </font>"
                home = ""
                if isinstance(link, displayMgr.SystemLink):
                    system = "<font size=-1 color=\"green\">S </font>"
                if isinstance(link, displayMgr.PageLink):
                    if link.getPage().isHome():
                        home = "&nbsp;<font size=-1 color=\"green\">(home)</font>"
                    system = "<font size=-1 color=\"black\">P </font>"
                html = ["""<tr><td>%s</td><td nowrap>%s<a href="%s">%s</a>%s%s</td></tr>\n"""%(system, indent, self._linkModifHandler(link), escape(link.getCaption()), disabled, home)]
                for l in link.getLinkList():
                    html.append( self._getLinkHTML(l, "%s%s"%(indent ,self._menu.getIndent())))
            return "".join(html)
        return ""


class WLinkModif(wcomponents.WTemplated):
    def __init__(self, link):
        self._link = link

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["linkName"] = self._link.getCaption()
        vars["linkURL"] = self._link.getURL()
        vars["displayTarget"] = _("Display in the SAME window")
        if self._link.getDisplayTarget() == "_blank":
            vars["displayTarget"] = _("Display in a NEW window")
        if self._link.isEnabled():
            vars["linkStatus"] = _("Activated")
            vars["changeStatusTo"] = _("Disable")
        else:
            vars["linkStatus"] = _("Disabled")
            vars["changeStatusTo"] = _("Activate")

        return vars

class WPageLinkModif(wcomponents.WTemplated):

    def __init__(self, link):
        self._link = link

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["linkName"] = self._link.getCaption()
        vars["linkContent"] = self.htmlText("%s..."%self._link.getPage().getContent()[0:50])
        vars["displayTarget"] = _("Display in the SAME window")
        if self._link.getDisplayTarget() == "_blank":
            vars["displayTarget"] = _("Display in a NEW window")
        if self._link.isEnabled():
            vars["linkStatus"] = _("Activated")
            vars["changeStatusTo"] = _("Disable")
        else:
            vars["linkStatus"] = _("Disabled")
            vars["changeStatusTo"] = _("Activate")
        if self._link.getPage().isHome():
            vars["homeText"] = _("Default conference home page")
            vars["changeHomeTo"] = _("Normal page")
        else:
            vars["homeText"] = _("Normal page")
            vars["changeHomeTo"] = _("Default conference home page")
        return vars

class WSystemLinkModif(wcomponents.WTemplated):

    def __init__(self, link):
        self._link = link

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["linkName"] = self._link.getCaption()
        vars["linkURL"] = self._link.getURL()
        vars["linkStatus"] = _("Disabled")
        vars["changeStatusTo"] = _("Activate")
        if self._link.isEnabled():
            vars["linkStatus"] = _("Activated")
            vars["changeStatusTo"] = _("Disable")
        url=urlHandlers.UHConfModifDisplayToggleLinkStatus.getURL(self._link)
        vars["toggleLinkStatusURL"]=quoteattr(str(url))
        return vars


class WSpacerModif(wcomponents.WTemplated):
    def __init__(self, link):
        self._link = link

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["linkName"] = self._link.getName()
        if self._link.isEnabled():
            vars["linkStatus"] = _("Activated")
            vars["changeStatusTo"] = _("Disable")
        else:
            vars["linkStatus"] = _("Disabled")
            vars["changeStatusTo"] = _("Activate")
        return vars

class WPConfModifDisplayAddPage( WPConfModifDisplayBase ):

    def __init__(self, rh, conf, linkId):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._linkId = linkId
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        if linkId:
            self._link = self._menu.getLinkById(linkId)
        else:
            self._link = self._menu

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifDisplayAddPage( self._conf, self._linkId )
        return wcomponents.WHTMLEditorWrapper(wc.getHTML(),self._conf).getHTML()


class WConfModifDisplayAddPage(wcomponents.WTemplated):

    def __init__(self, conf, linkId):
        self._conf = conf
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        if linkId:
            self._link = self._menu.getLinkById(linkId)
        else:
            self._link = self._menu

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["saveLinkURL"] = quoteattr(str(urlHandlers.UHConfModifDisplayAddPage.getURL(self._link)))
        vars["content"]=""
        return vars

class WPConfModifDisplayAddLink( WPConfModifDisplayBase ):
    def __init__(self, rh, conf, linkId):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._linkId = linkId
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        if linkId:
            self._link = self._menu.getLinkById(linkId)
        else:
            self._link = self._menu

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifDisplayAddLink( self._conf, self._linkId )
        p = {"addLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._conf))), \
             "addPageURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddPage.getURL(self._conf))), \
             "addSpacerURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddSpacer.getURL(self._conf))) }
        return wc.getHTML( p )


class WConfModifDisplayAddLink(wcomponents.WTemplated):

    def __init__(self, conf, linkId):
        self._conf = conf
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        if linkId:
            self._link = self._menu.getLinkById(linkId)
        else:
            self._link = self._menu

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["menuDisplay"] = ConfEditMenu(self._menu, urlHandlers.UHConfModifDisplay.getURL).getHTML()
        vars["saveLinkURL"] = quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._link)))
        return vars


class WPConfModifDisplayModifyData( WPConfModifDisplayBase ):
    def __init__(self, rh, conf, link):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._link = link
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifDisplayModifyData( self._conf, self._link )
        p = {
                "modifyDataURL": quoteattr(str(urlHandlers.UHConfModifDisplayModifyData.getURL(self._link))), \
                "addLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._conf))), \
                "addPageURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddPage.getURL(self._conf))), \
                "addSpacerURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddSpacer.getURL(self._conf))) }
        return wc.getHTML( p )

class WConfModifDisplayModifyData(wcomponents.WTemplated):

    def __init__(self, conf, link):
        self._conf = conf
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        self._link = link


    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["menuDisplay"] = ConfEditMenu(self._menu, urlHandlers.UHConfModifDisplay.getURL).getHTML()
        vars["saveLinkURL"] = quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._link)))
        vars["name"] = self._link.getCaption()
        vars["value_name"] = quoteattr(self._link.getCaption())
        vars["url"] = self._link.getURL()
        if self._link.getDisplayTarget() == "_blank":
            vars["newChecked"] = _("""CHECKED""")
            vars["sameChecked"] = ""
        else:
            vars["newChecked"] = ""
            vars["sameChecked"] = _("""CHECKED""")

        return vars



class WPConfModifDisplayModifyPage( WPConfModifDisplayBase ):
    def __init__(self, rh, conf, link):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._link = link
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifDisplayModifyPage( self._conf, self._link )
        p = {
                "modifyDataURL": quoteattr(str(urlHandlers.UHConfModifDisplayModifyData.getURL(self._link))) }
        return wcomponents.WHTMLEditorWrapper(wc.getHTML( p ),self._conf).getHTML()

class WConfModifDisplayModifyPage(wcomponents.WTemplated):

    def __init__(self, conf, link):
        self._conf = conf
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        self._link = link


    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["saveLinkURL"] = quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._link)))
        vars["name"] = self._link.getCaption()
        vars["value_name"] = quoteattr(self._link.getCaption())
        vars["content"] = self._link.getPage().getContent()
        if self._link.getDisplayTarget() == "_blank":
            vars["newChecked"] = _("""CHECKED""")
            vars["sameChecked"] = ""
        else:
            vars["newChecked"] = ""
            vars["sameChecked"] = _("""CHECKED""")
        return vars

class WPConfModifDisplayModifySystemData( WPConfModifDisplayBase ):
    def __init__(self, rh, conf, link):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._link = link
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifDisplayModifySystemData( self._conf, self._link )
        p = {
                "modifyDataURL": quoteattr(str(urlHandlers.UHConfModifDisplayModifySystemData.getURL(self._link))), \
                "addLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddLink.getURL(self._conf))), \
                "addPageURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddPage.getURL(self._conf))), \
                "addSpacerURL": quoteattr(str(urlHandlers.UHConfModifDisplayAddSpacer.getURL(self._conf))) }
        return wc.getHTML( p )

class WConfModifDisplayModifySystemData(wcomponents.WTemplated):

    def __init__(self, conf, link):
        self._conf = conf
        self._menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        self._link = link


    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["menuDisplay"] = ConfEditMenu(self._menu, urlHandlers.UHConfModifDisplay.getURL).getHTML()
        vars["saveLinkURL"] = quoteattr(str(urlHandlers.UHConfModifDisplayModifySystemData.getURL(self._link)))
        vars["name"] = self._link.getCaption()
        vars["value_name"] = quoteattr(self._link.getCaption())
        return vars

class WPConfModifDisplayRemoveLink( WPConfModifDisplayBase ):
    def __init__(self, rh, conf, link):
        WPConfModifDisplayBase.__init__(self, rh, conf)
        self._link = link

    def _setActiveTab( self ):
        self._tabDisplayMenu.setActive()

    def _getTabContent( self, params ):
        msg = _("""<font size=\"+2\"> _("Are you sure that you want to DELETE the link") \"%s\"</font><br>( _("Note that if you delete the link, all the links below it will also be deleted"))""")%self._link.getName()
        postURL = quoteattr(str(urlHandlers.UHConfModifDisplayRemoveLink.getURL(self._link)))
        return wcomponents.WConfirmation().getHTML( msg, postURL, {})
        #wc = WConfModifDisplayRemoveLink( self._conf, link )
        #p = {"removeLinkURL": quoteattr(str(urlHandlers.UHConfModifDisplayRemoveLink.getURL(self._link)))}
        #return wc.getHTML( p )


class WPConfParticipantList( WPConferenceBase ):

    def __init__(self, rh, conf, emailList, displayedGroups, abstracts):
        WPConferenceBase.__init__(self, rh, conf)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._abstracts = abstracts

    def _getBody( self, params ):
        WPConferenceBase._getBody(self, params)
        wc = WAbstractsParticipantList(self._conf, self._emailList, self._displayedGroups, self._abstracts)
        return wc.getHTML()

class WPConfModifParticipantList( WPConferenceBase ):

    def __init__(self, rh, conf, emailList, displayedGroups, contribs):
        WPConferenceBase.__init__(self, rh, conf)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._contribs = contribs

    def _getBody( self, params ):
        WPConferenceBase._getBody(self, params)
        wc = WContribParticipantList(self._conf, self._emailList, self._displayedGroups, self._contribs)
        params = {"urlDisplayGroup":urlHandlers.UHContribsConfManagerDisplayParticipantList.getURL(self._conf)}
        return wc.getHTML(params)


class WConfModifContribList(wcomponents.WTemplated):

    def __init__(self,conf,filterCrit, sortingCrit, order, websession):
        self._conf=conf
        self._filterCrit=filterCrit
        self._sortingCrit=sortingCrit
        self._order = order
        self._totaldur =timedelta(0)
        self._menuStatus = websession.getVar("ContribListMenuStatusConf%s"%conf.getId())
        self.websession = websession


    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHConfModifContribList.getURL(self._conf)

        #save params in websession
        dict = self.websession.getVar("ContributionFilterConf%s"%self._conf.getId())
        if not dict:
            dict = {}
        if self._filterCrit.getField("type"):
            l=[]
            for t in self._filterCrit.getField("type").getValues():
                if t!="":
                    l.append(t)
            dict["types"] = l
            if self._filterCrit.getField("type").getShowNoValue():
                dict["typeShowNoValue"] = "1"

        if self._filterCrit.getField("track"):
            dict["tracks"] = self._filterCrit.getField("track").getValues()
            if self._filterCrit.getField("track").getShowNoValue():
                dict["trackShowNoValue"] = "1"

        if self._filterCrit.getField("session"):
            dict["sessions"] = self._filterCrit.getField("session").getValues()
            if self._filterCrit.getField("session").getShowNoValue():
                dict["sessionShowNoValue"] = "1"

        if self._filterCrit.getField("status"):
            dict["status"] = self._filterCrit.getField("status").getValues()

        if self._filterCrit.getField("material"):
            dict["material"] = self._filterCrit.getField("material").getValues()

        if self._sortingCrit.getField():
            dict["sortBy"] = self._sortingCrit.getField().getId()
            dict["order"] = "down"
        dict["OK"] = "1"
        self.websession.setVar("ContributionFilterConf%s"%self._conf.getId(), dict)

        return url

    def _getMaterialsHTML(self, contrib):
        materials=[]
        if contrib.getPaper() is not None:
            url=urlHandlers.UHMaterialModification.getURL(contrib.getPaper())
            iconHTML="""<img border="0" src=%s alt="paper">"""%quoteattr(str(PaperFactory().getIconURL()))
            if len(contrib.getPaper().getResourceList())>0:
                r=contrib.getPaper().getResourceList()[0]
                if isinstance(r,conference.Link):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(r.getURL())),iconHTML)
                elif isinstance(r,conference.LocalFile):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHFileAccess.getURL(r))),iconHTML)
            materials.append("""%s<a href=%s>%s</a>"""%(iconHTML,quoteattr(str(url)),self.htmlText(PaperFactory().getTitle().lower())))
        if contrib.getSlides() is not None:
            url=urlHandlers.UHMaterialModification.getURL(contrib.getSlides())
            iconHTML="""<img border="0" src=%s alt="slides">"""%quoteattr(str(SlidesFactory().getIconURL()))
            if len(contrib.getSlides().getResourceList())>0:
                r=contrib.getSlides().getResourceList()[0]
                if isinstance(r,conference.Link):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(r.getURL())),iconHTML)
                elif isinstance(r,conference.LocalFile):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHFileAccess.getURL(r))),iconHTML)
            materials.append("""%s<a href=%s>%s</a>"""%(iconHTML,quoteattr(str(url)),self.htmlText(SlidesFactory().getTitle().lower())))
        if contrib.getPoster() is not None:
            url=urlHandlers.UHMaterialModification.getURL(contrib.getPoster())
            iconHTML="""<img border="0" src=%s alt="slides">"""%quoteattr(str(PosterFactory().getIconURL()))
            if len(contrib.getPoster().getResourceList())>0:
                r=contrib.getPoster().getResourceList()[0]
                if isinstance(r,conference.Link):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(r.getURL())),iconHTML)
                elif isinstance(r,conference.LocalFile):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHFileAccess.getURL(r))),iconHTML)
            materials.append("""%s<a href=%s>%s</a>"""%(iconHTML,quoteattr(str(url)),self.htmlText(PosterFactory.getTitle().lower())))
        video=contrib.getVideo()
        if video is not None:
            materials.append("""<a href=%s><img src=%s border="0" alt="video"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialModification.getURL(video))),
                quoteattr(str(materialFactories.VideoFactory.getIconURL())),
                self.htmlText(materialFactories.VideoFactory.getTitle())))
        minutes=contrib.getMinutes()
        if minutes is not None:
            materials.append("""<a href=%s><img src=%s border="0" alt="minutes"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialModification.getURL(minutes))),
                quoteattr(str(materialFactories.MinutesFactory.getIconURL())),
                self.htmlText(materialFactories.MinutesFactory.getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        for material in contrib.getMaterialList():
            url=urlHandlers.UHMaterialModification.getURL(material)
            materials.append("""<a href=%s><img src=%s border="0" alt=""> %s</a>"""%(
                quoteattr(str(url)),iconURL,self.htmlText(material.getTitle())))
        return "<br>".join(materials)

    def _getContribHTML( self, contrib ):
        sdate = ""
        if contrib.isScheduled():
            sdate=contrib.getAdjustedStartDate().strftime("%d-%b-%Y %H:%M" )
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionModification.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        strdur = ""
        if contrib.getDuration() is not None and contrib.getDuration().seconds != 0:
            strdur = (datetime(1900,1,1)+ contrib.getDuration()).strftime("%Hh%M'")
            dur = contrib.getDuration()
            self._totaldur = self._totaldur + dur
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            if contrib.getSession().getCode() != "not assigned":
                session=self.htmlText(contrib.getSession().getCode())
            else:
                session=self.htmlText(contrib.getSession().getId())
        track = ""
        if contrib.getTrack() is not None:
            if contrib.getTrack().getCode() is not None:
                track = self.htmlText( contrib.getTrack().getCode() )
            else:
                track = self.htmlText( contrib.getTrack().getId() )
        cType=""
        if contrib.getType() is not None:
            cType=self.htmlText(contrib.getType().getName())
        status=contrib.getCurrentStatus()
        statusCaption=ContribStatusList().getCode(status.__class__)
        html = """
            <tr>
                <td valign="top" nowrap><input type="checkbox" name="contributions" value=%s></td>
                <td valign="top" nowrap class="abstractLeftDataCell">%s</td>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell" nowrap>%s</td>
            </tr>
                """%(contrib.getId(), self.htmlText(contrib.getId()),
                    sdate or "&nbsp;",strdur or "&nbsp;",cType or "&nbsp;",
                    title or "&nbsp;",
                    speaker or "&nbsp;",session or "&nbsp;",
                    track or "&nbsp;",statusCaption or "&nbsp;",
                    self._getMaterialsHTML(contrib) or "&nbsp;")
        return html

    def _getTypeItemsHTML(self):
        checked=""
        if self._filterCrit.getField("type").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="typeShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getContribTypeList():
            checked=""
            if t.getId() in self._filterCrit.getField("type").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="types" value=%s%s> %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getName())))
        return "<br>".join(res)

    def _getSessionItemsHTML(self):
        checked=""
        if self._filterCrit.getField("session").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="sessionShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for s in self._conf.getSessionListSorted():
            checked=""
            l = self._filterCrit.getField("session").getValues()
            if not isinstance(l, list):
                l = [l]
            if s.getId() in l:
                checked=" checked"
            res.append("""<input type="checkbox" name="sessions" value=%s%s> (%s) %s"""%(quoteattr(str(s.getId())),checked,self.htmlText(s.getCode()),self.htmlText(s.getTitle())))
        return "<br>".join(res)

    def _getTrackItemsHTML(self):
        checked=""
        if self._filterCrit.getField("track").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="trackShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked=""
            if t.getId() in self._filterCrit.getField("track").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="tracks" value=%s%s> (%s) %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return "<br>".join(res)

    def _getStatusItemsHTML(self):
        res=[]
        for st in ContribStatusList().getList():
            id=ContribStatusList().getId(st)
            checked=""
            if id in self._filterCrit.getField("status").getValues():
                checked=" checked"
            code=ContribStatusList().getCode(st)
            caption=ContribStatusList().getCaption(st)
            res.append("""<input type="checkbox" name="status" value=%s%s> (%s) %s"""%(quoteattr(str(id)),checked,self.htmlText(code),self.htmlText(caption)))
        return "<br>".join(res)

    def _getMaterialItemsHTML(self):
        res=[]
        for (id,caption) in [(PaperFactory().getId(),PaperFactory().getTitle()),\
                        (SlidesFactory().getId(),SlidesFactory().getTitle()),\
                        ("--other--", _("other")),("--none--", _("""--_("no material")--"""))]:
            checked=""
            if id in self._filterCrit.getField("material").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="material" value=%s%s> %s"""%(quoteattr(str(id)),checked,self.htmlText(caption)))
        return "<br>".join(res)

    def _getOpenMenuURL(self):
        url = urlHandlers.UHConfModifContribListOpenMenu.getURL(self._conf)
        url.addParam("currentURL", self._getURL())
        return url

    def _getCloseMenuURL(self):
        url = urlHandlers.UHConfModifContribListCloseMenu.getURL(self._conf)
        url.addParam("currentURL", self._getURL())
        return url

    def _getMenu(self):
        if self._menuStatus == "open":
            menu = _("""<form action=%(filterPostURL)s method="post">
    <table width="100%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"><a href="%(closeMenuURL)s"><img src=%(openMenuImg)s alt="_("hide menu")" border="0"></a> _("Filtering criteria")</td>
        </tr>
        <tr>
            <td>
                <table width="100%%">
                    <tr>
                        <td>
                            <table align="center" cellspacing="10" width="100%%">
                                <tr>
                                    <td class="titleCellFormat"> _("Author search") <input type="text" name="authSearch" value=%(authSearch)s></td>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" cellspacing="10" width="100%%">
                                <tr>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px"> _("types")</td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("sessions")</td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("tracks")</td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("status")</td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("material")</td>
                                </tr>
                                <tr>
                                    <td valign="top" style="border-right:1px solid #777777;">%(types)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(sessions)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(tracks)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(status)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(materials)s</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="border-top:1px solid #777777;padding:10px"><input type="submit" class="btn" name="OK" value="_("apply filter")"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>""")
        else :
            menu = _("""<form action=%(filterPostURL)s method="post">
    <table width="100%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"><a href="%(openMenuURL)s"><img src=%(closeMenuImg)s alt="Show menu" border="0"></a> _("Filtering criteria")</td>
        </tr>
    </table>
</form>
""")

        return menu

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["quickSearchURL"]=quoteattr(str(urlHandlers.UHConfModContribQuickAccess.getURL(self._conf)))
        vars["filterPostURL"]=quoteattr(str(urlHandlers.UHConfModifContribList.getURL(self._conf)))
        authSearch=vars.get("authSearch","").strip()
        vars["authSearch"]=quoteattr(str(authSearch))
        vars["types"]=self._getTypeItemsHTML()
        vars["sessions"]=self._getSessionItemsHTML()
        vars["tracks"]=self._getTrackItemsHTML()
        vars["status"]=self._getStatusItemsHTML()
        vars["materials"]=self._getMaterialItemsHTML()
        cl=self._conf.getContribsMatchingAuth(authSearch)

        sortingField = self._sortingCrit.getField()
        self._currentSorting=""

        if sortingField is not None:
            self._currentSorting=sortingField.getId()
        vars["currentSorting"]=""

        url=self._getURL()
        url.addParam("sortBy","number")
        vars["numberImg"]=""
        if self._currentSorting == "number":
                vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value="_("number")">""")
                if self._order == "down":
                    vars["numberImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    vars["numberImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
        vars["numberSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "date")
        vars["dateImg"] = ""
        if self._currentSorting == "date":
            vars["currentSorting"]= _("""<input type="hidden" name="sortBy" value="_("date")">""")
            if self._order == "down":
                vars["dateImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["dateImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["dateSortingURL"]=quoteattr(str(url))


        url = self._getURL()
        url.addParam("sortBy", "name")
        vars["titleImg"] = ""
        if self._currentSorting == "name":
            vars["currentSorting"]= _("""<input type="hidden" name="sortBy" value="_("name")">""")
            if self._order == "down":
                vars["titleImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["titleImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["titleSortingURL"]=quoteattr(str(url))


        url = self._getURL()
        url.addParam("sortBy", "type")
        vars["typeImg"] = ""
        if self._currentSorting == "type":
            vars["currentSorting"]= _("""<input type="hidden" name="sortBy" value="_("type")">""")
            if self._order == "down":
                vars["typeImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["typeImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["typeSortingURL"] = quoteattr( str( url ) )
        url = self._getURL()
        url.addParam("sortBy", "session")
        vars["sessionImg"] = ""
        if self._currentSorting == "session":
            vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value='_("session")'>""")
            if self._order == "down":
                vars["sessionImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["sessionImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["sessionSortingURL"] = quoteattr( str( url ) )
        url = self._getURL()
        url.addParam("sortBy", "speaker")
        vars["speakerImg"]=""
        if self._currentSorting=="speaker":
            vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value="_("speaker")">""")
            if self._order == "down":
                vars["speakerImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["speakerImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["speakerSortingURL"]=quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy","track")
        vars["trackImg"] = ""
        if self._currentSorting == "track":
            vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value="_("track")">""")
            if self._order == "down":
                vars["trackImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["trackImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["trackSortingURL"] = quoteattr( str( url ) )

        l=[]
        numContribs=0
        f=filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        contribsToPrint = []
        for contrib in f.apply(cl):
            l.append(self._getContribHTML(contrib))
            numContribs+=1
            contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib.getId())
        if self._order =="up":
            l.reverse()
        vars["contribsToPrint"] = "\n".join(contribsToPrint)
        vars["contributions"] = "".join(l)
        orginURL = urlHandlers.UHConfModifContribList.getURL(self._conf)
        newContribURL = urlHandlers.UHConfModScheduleNewContrib.getURL(self._conf)
        newContribURL.addParam("orginURL",orginURL)
        newContribURL.addParam("targetDay",self._conf.getAdjustedStartDate().date())
        vars["newContribURL"] = newContribURL
        #vars["newContribURL"] = urlHandlers.UHConfAddContribution.getURL( self._conf )
        vars["numContribs"]=str(numContribs)
        vars["contribSelectionAction"]=quoteattr(str(urlHandlers.UHContribConfSelectionAction.getURL(self._conf)))
        vars["contributionsPDFURL"]=quoteattr(str(urlHandlers.UHContribsConfManagerDisplayMenuPDF.getURL(self._conf)))
        vars["participantListURL"]=quoteattr(str(urlHandlers.UHContribsConfManagerDisplayParticipantList.getURL(self._conf)))
        vars["moveURL"]=quoteattr(str(urlHandlers.UHConfModMoveContribsToSession.getURL(self._conf)))
        vars["materialPkgURL"]=quoteattr(str(urlHandlers.UHConfModMaterialPackage.getURL(self._conf)))
        vars["proceedingsURL"]=quoteattr(str(urlHandlers.UHConfModProceedings.getURL(self._conf)))

        vars["closeMenuURL"] = self._getCloseMenuURL()
        vars["closeMenuImg"] = quoteattr(Config.getInstance().getSystemIconURL("openMenu"))
        vars["openMenuURL"] = self._getOpenMenuURL()
        vars["openMenuImg"] = quoteattr(Config.getInstance().getSystemIconURL("closeMenu"))

        vars["menu"] = self._getMenu()%vars

        totaldur = self._totaldur
        days = totaldur.days
        hours = (totaldur.seconds)/3600
        dayhours = (days * 24)+hours
        mins = ((totaldur.seconds)/60)-(hours*60)
        vars["totaldur" ]="""%sh%sm"""%(dayhours,mins)
        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
        return vars

class WPModifContribList( WPConferenceModifBase ):

    def _setActiveSideMenuItem(self):
        self._contribListMenuItem.setActive(True)

    def _getPageContent( self, params ):
        filterCrit=params.get("filterCrit",None)
        sortingCrit=params.get("sortingCrit",None)
        order = params.get("order","down")
        websession = self._rh._getSession()
        wc = WConfModifContribList(self._conf,filterCrit, sortingCrit ,order, websession)
        p={"authSearch":params.get("authSearch","")}

        return wc.getHTML(p)

class WPConfModifContribToPDFMenu( WPModifContribList ):

    def __init__(self, rh, conf, contribIds):
        WPModifContribList.__init__(self, rh, conf)
        self._contribIds = contribIds

    def _getPageContent(self, params):

        wc = WConfModifContribToPDFMenu(self._conf, self._contribIds)
        return wc.getHTML(params)

class WConfModifContribToPDFMenu(wcomponents.WTemplated):
    def __init__(self, conf, contribIds):
        self._conf = conf
        self.contribIds = contribIds

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["createPDFURL"] = urlHandlers.UHContribsConfManagerDisplayMenuPDF.getURL(self._conf)
        l = []
        for id in self.contribIds:
            l.append("""<input type="hidden" name="contributions" value="%s">"""%id)
        vars["contribIdsList"] = "\n".join(l)
        return vars

class WContributionCreation(wcomponents.WTemplated):

    def __init__( self, target):
        self.__owner = target

    def _getTypeItemsHTML(self):
        res = ["""<option value=""></option>"""]
        for type in self.__owner.getConference().getContribTypeList():
            selected=""
            res.append("""<option value=%s%s>%s</option>"""%(\
                quoteattr(str(type.getId())),selected,\
                self.htmlText(type.getName())))
        return "".join(res)

    def _getAdditionalFieldsHTML(self):
        html=""
        if self.__owner.getConference().hasEnabledSection("cfa") and self.__owner.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
            for f in self.__owner.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields():
                if f.isActive():
                    id = f.getId()
                    caption = f.getName()
                    html+="""
                    <tr>
                        <td nowrap class="titleCellTD"><span class="titleCellFormat">%s</span></td>
                        <td bgcolor="white" width="100%%">&nbsp;
                                    <textarea name="%s" cols="85" rows="10"></textarea></td>
                    </tr>
                    """ % (caption,"f_%s"%id)
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName, defaultExistRoom = "", "", "",""
        vars["title"], vars["description"], vars["additionalFields"] = "", "", self._getAdditionalFieldsHTML()
        refDate = self.__owner.getSchedule().calculateEndDate()
        vars["day"],vars["month"],vars["year"]="","",""
        vars["sHour"],vars["sMinute"]="",""
        vars["durationHours"],vars["durationMinutes"]="",""
        vars["locator"] = self.__owner.getLocator().getWebForm()
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["confPlace"] = ""
        if not type(self.__owner) == conference.Session:
            xLocation = self.__owner.getConference().getLocation()
        else:
            xLocation = self.__owner.getLocation()
        if xLocation:
            vars["confPlace"] = xLocation.getName()
        vars["locationName"] = locationName
        vars["locationAddress"] = locationAddress
        vars["defaultInheritRoom"] = defaultInheritRoom
        vars["defaultDefineRoom"] = defaultDefineRoom
        vars["defaultExistRoom"] = defaultExistRoom
        rx=[]
        roomsexist = self.__owner.getConference().getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            sel=""
            rx.append("""<option value=%s%s>%s</option>"""%(quoteattr(str(room)),
                        sel,self.htmlText(room)))
        vars ["roomsexist"] = "".join(rx)
        vars["confRoom"] = ""
        if not type(self.__owner) == conference.Session:
            xRoom = self.__owner.getConference().getRoom()
        else:
            xRoom = self.__owner.getRoom()
        if xRoom:
            vars["confRoom"] = xRoom.getName()
        vars["roomName"] = quoteattr(roomName)
        vars["parentType"] = "session"
        if not type(self.__owner) == conference.Session:
            vars["parentType"] = "conference"
        vars["speakers"] = ""
        vars["boardNumber"]=""
        vars["type"]=self._getTypeItemsHTML()
        return vars

class WPConfAddContribution(WPModifContribList):

    def _getTabContent( self, params ):
        p = WContributionCreation( self._conf )
        pars = {"postURL": urlHandlers.UHConfPerformAddContribution.getURL(), \
        "calendarIconURL": Config.getInstance().getSystemIconURL( "calendar" ), \
        "calendarSelectURL":  urlHandlers.UHSimpleCalendar.getURL() }
        return p.getHTML( pars )



class WContributionSchCreation(WContributionCreation):

    def __init__(self, target, targetDay):
        WContributionCreation.__init__(self, target)
        self._conf = target.getConference()
        self._target = target
        self._targetDay=targetDay

    def _getAdditionalFieldsHTML(self):
        html=""
        if self._conf.hasEnabledSection("cfa") and \
                self._conf.getType() == "conference" and \
                self._conf.getAbstractMgr().hasAnyEnabledAbstractField():
            for f in self._conf.getAbstractMgr().getAbstractFieldsMgr().getFields():
                if f.isActive():
                    id = f.getId()
                    caption = f.getName()
                    html+="""
                    <tr>
                        <td nowrap class="titleCellTD">
                            <span class="titleCellFormat">%s</span>
                        </td>
                        <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                            <textarea name="%s" cols="65" rows="10"></textarea>
                        </td>
                    </tr>"""%(caption, "f_%s"%id)
        return html

    def getVars(self):
        params = wcomponents.WTemplated.getVars( self )
        vars=WContributionCreation.getVars(self)
        vars.update(params)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        session = None
        slot = None
        if params.get("sessionId", None):
            sessionId = params.get("sessionId")
            if isinstance(sessionId, list):
                sessionId = sessionId[0]
            session = self._conf.getSessionById(sessionId)
        if session and params.get("slotId", None):

            slot = session.getSlotById(params.get("slotId"))

        vars["title"] = quoteattr(vars.get("title",""))
        vars["conference"] = self._conf
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()

        #######################################
        # Fermi timezone awareness            #
        #  targetDay is UTC.  Should we set   #
        #  earlier to conf tz?                #
        #######################################
        if self._targetDay is not None:
            sd = convertTime.convertTime(self._targetDay,self._conf.getTimezone())
            #######################################
            # Fermi timezone awareness            #
            #######################################
            vars["day"]=sd.day
            vars["month"]=sd.month
            vars["year"]=sd.year
            vars["sHour"]=sd.hour
            vars["sMinute"]=sd.minute
            if slot and slot.getContribDuration() and slot.getContribDuration()!=timedelta(0):
                duration = slot.getContribDuration()
                hour = int(duration.seconds/3600)
                min = int( (duration.seconds - hour*3600)/60 )
                vars["durationHours"],vars["durationMinutes"]= hour, min
            elif session:
                duration = session.getContribDuration()
                hour = int(duration.seconds/3600)
                min = int( (duration.seconds - hour*3600)/60 )
                vars["durationHours"],vars["durationMinutes"]= hour, min
            else:
                vars["durationHours"],vars["durationMinutes"]="0","20"
        else :
            vars["day"] = params.get("sDay","")
            vars["month"] = params.get("sMonth","")
            vars["year"] = params.get("sYear","")
            vars["durationHours"] = params.get("durHours","0")
            vars["durationMinutes"] = params.get("durMins","20")
        if params.get("locationAction","inherit") == "define":
            vars["defaultDefinePlace"] = "checked"
            vars["defaultInheritPlace"] = ""
        else:
            vars["defaultDefinePlace"] = ""
            vars["defaultInheritPlace"] = "checked"
        if params.get("roomAction","inherit") == "define":
            vars["defaultDefineRoom"] = "checked"
            vars["defaultExistRoom"] = ""
            vars["defaultInheritRoom"] = ""
        elif params.get("roomAction","inherit") == "exist":
            vars["defaultDefineRoom"] = ""
            vars["defaultExistRoom"] = "checked"
            vars["defaultInheritRoom"] = ""
        else :
            vars["defaultDefineRoom"] = ""
            vars["defaultExistRoom"] = ""
            vars["defaultInheritRoom"] = "checked"
        vars["locationName"] = params.get("locationName","")
        vars["locationAdress"] = params.get("locationAddress","")
        vars["roomName"] = quoteattr(params.get("roomName",""))
        vars["newPresenterAction"] = urlHandlers.UHConfModSchedulePresenterSearch.getURL(self._target)
        vars["newAuthorAction"] = urlHandlers.UHConfModScheduleAuthorSearch.getURL(self._target)
        vars["newCoauthorAction"] = urlHandlers.UHConfModScheduleCoauthorSearch.getURL(self._target)
        vars["author"] = vars.get("author","")
        vars["coauthor"] = vars.get("coauthor","")
        vars["typeModule"] = ""
        vars["boardModule"] = ""
        vars["keywords"] = vars.get("keywords","")
        vars["presenterFreeText"] = ""
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        if vars.get("eventType","conference") != "conference":
            vars["presenterFreeText"] = _("""
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> _("Presenter (free text)")</span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <input size="50" name="presenterFreeText">
            </td>
        </tr>""")
        if vars.get("eventType","conference") == "conference" :
            vars["typeModule"] = _("""
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> _("Type")</span></td>
            <td bgcolor="white" width="100%%">&nbsp;
                <select name="type">%s</select></td>
        </tr>
        """)%vars["type"]
            vars["boardModule"] = _("""
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> _("Board #")</span></td>
            <td bgcolor="white" width="100%%">&nbsp;
            <input type="text" name="boardNumber" size="10" value=%s></td>
        </tr>
            """)%vars["boardNumber"]

        vars["autoUpdate"]=""
        return vars

#---------------------------------------------------------------------------

class WPModScheduleNewContribBase(WPConfModifSchedule):

    def __init__(self, rh, conf, targetDay, contributionCreatedFrom = "other"):
        WPConfModifSchedule.__init__(self, rh, conf)
        self._targetDay = targetDay
        ##################################
        # Fermi timezone awareness       #
        ##################################
        self._confTimezone = conf.getTimezone()
        self._contributionCreatedFrom = contributionCreatedFrom

    def _setActiveSideMenuItem(self):
        if self._contributionCreatedFrom == "contributionList":
            self._contribListMenuItem.setActive(True)
        else:
            self._timetableMenuItem.setActive(True)

    def _getPageContent( self, params ):
        p = WContributionSchCreation( self._conf, self._targetDay )
        td=""
        if self._targetDay is not None:
            td=self._targetDay.strftime("%Y-%m-%d")

        params["postURL"] = urlHandlers.UHConfModSchedulePerformNewContrib.getURL()
        params["calendarIconURL"] = Config.getInstance().getSystemIconURL( "calendar" )
        params["calendarSelectURL"] =  urlHandlers.UHSimpleCalendar.getURL()
        params["targetDay"] = td
        params["eventType"] = params.get("eventType","conference")

        wpresenter = wcomponents.WAddPersonModule("presenter")
        wauthor = wcomponents.WAddPersonModule("author")
        wcoauthor = wcomponents.WAddPersonModule("coauthor")

        params["presenterOptions"] = params.get("presenterOptions",self._getPersonOptions())
        params["coauthorOptions"] =  params.get("coauthorOptions",self._getPersonOptions())
        params["authorOptions"] =  params.get("authorOptions",self._getPersonOptions())

        if params.get("eventType","conference") == "conference" :
            params["author"] = wauthor.getHTML(params)
            params["coauthor"] = wcoauthor.getHTML(params)

        params["submission"] = "true"
        params["presenter"] = wpresenter.getHTML(params)

        params["contributionCreatedFrom"] = self._contributionCreatedFrom

        return p.getHTML( params )

    def _getPersonOptions(self):
        html = []
        names = []
        text = {}
        html.append("""<option value=""> </option>""")
        for contribution in self._conf.getContributionList() :
            for speaker in contribution.getSpeakerList() :
                name = speaker.getFullNameNoTitle()
                if not(name in names) :
                    text[name] = """<option value="s%s-%s">%s</option>"""%(contribution.getId(),speaker.getId(),name)
                    names.append(name)
            for author in contribution.getAuthorList() :
                name = author.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="a%s-%s">%s</option>"""%(contribution.getId(),author.getId(),name)
                    names.append(name)
            for coauthor in contribution.getCoAuthorList() :
                name = coauthor.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="c%s-%s">%s</option>"""%(contribution.getId(),coauthor.getId(),name)
                    names.append(name)
        names.sort()
        for name in names:
            html.append(text[name])
        return "".join(html)

class WPModScheduleNewContrib(WPModScheduleNewContribBase, WPConfModifSchedule):

    def __init__(self, rh, conf, targetDay, contributionCreatedFrom = "other"):
        WPConfModifSchedule.__init__(self, rh, conf)
        WPModScheduleNewContribBase.__init__(self, rh, conf, targetDay, contributionCreatedFrom)

#---------------------------------------------------------------------------

class WPNewContributionAuthorSelect( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target.getConference())
        self._target = target

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._target,searchAction,forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPNewContributionAuthorNew( WPConferenceModifBase ):

    def __init__(self, rh, target, params):
        WPConferenceModifBase.__init__(self, rh, target.getConference())
        self._params = params
        self._target = target

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params):
        p = wcomponents.WNewPerson()

        if self._params.get("formTitle",None) is None :
                self._params["formTitle"] = _("Define new author")
        if self._params.get("titleValue",None) is None :
                self._params["titleValue"] = ""
        if self._params.get("surNameValue",None) is None :
                self._params["surNameValue"] = ""
        if self._params.get("nameValue",None) is None :
                self._params["nameValue"] = ""
        if self._params.get("emailValue",None) is None :
                self._params["emailValue"] = ""
        if self._params.get("addressValue",None) is None :
                self._params["addressValue"] = ""
        if self._params.get("affiliationValue",None) is None :
                self._params["affiliationValue"] = ""
        if self._params.get("phoneValue",None) is None :
                self._params["phoneValue"] = ""
        if self._params.get("faxValue",None) is None :
                self._params["faxValue"] = ""


        #self._params["disabledSubmission"] = False
        self._params["disabledRole"] = False
        self._params["roleDescription"] = _("""Submitter""")
        #if self._params.has_key("submissionControlValue"):
        #    self._params["submissionValue"] = _(""" <input type="checkbox" name="submissionControl" CHECKED> _("Give submission rights to the presenter").""")
        #else:
        #    self._params["submissionValue"] = """ <input type="checkbox" name="submissionControl"> Give submission rights to the presenter."""
        self._params["roleValue"] = _(""" <input type="checkbox" name="submissionControl" CHECKED onchange="if (!this.checked){this.form.warning_email.type='hidden';}  else {if(this.form.email.value.length==0){this.form.warning_email.type='text'}else{this.form.warning_email.type='hidden';}}"> _("Give submission rights to the presenter").""")
        self._params["disabledNotice"] = False
        self._params["noticeValue"] = _("""<i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the
         user will automatically be given submission rights.")</i>""")

        formAction = urlHandlers.UHConfModSchedulePersonAdd.getURL(self._target)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","author")
        self._params["formAction"] = formAction

        return p.getHTML(self._params)

#---------------------------------------------------------------------------

class WPNewContributionCoauthorSelect( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target.getConference())
        self._target = target

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._conf,searchAction,forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPNewContributionCoauthorNew( WPConferenceModifBase ):

    def __init__(self, rh, target, params):
        WPConferenceModifBase.__init__(self, rh, target.getConference())
        self._target = target
        self._params = params

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params):
        p = wcomponents.WNewPerson()

        if self._params.get("formTitle",None) is None :
                self._params["formTitle"] = _("Define new co-author")
        if self._params.get("titleValue",None) is None :
                self._params["titleValue"] = ""
        if self._params.get("surNameValue",None) is None :
                self._params["surNameValue"] = ""
        if self._params.get("nameValue",None) is None :
                self._params["nameValue"] = ""
        if self._params.get("emailValue",None) is None :
                self._params["emailValue"] = ""
        if self._params.get("addressValue",None) is None :
                self._params["addressValue"] = ""
        if self._params.get("affiliationValue",None) is None :
                self._params["affiliationValue"] = ""
        if self._params.get("phoneValue",None) is None :
                self._params["phoneValue"] = ""
        if self._params.get("faxValue",None) is None :
                self._params["faxValue"] = ""

        #self._params["disabledSubmission"] = False
        self._params["disabledRole"] = False
        self._params["roleDescription"] = _("""Submitter""")
        #if self._params.has_key("submissionControlValue"):
        #    self._params["submissionValue"] = """ <input type="checkbox" name="submissionControl" CHECKED> Give submission rights to the presenter."""
        #else:
        #    self._params["submissionValue"] = """ <input type="checkbox" name="submissionControl"> Give submission rights to the presenter."""
        self._params["roleValue"] = _(""" <input type="checkbox" name="submissionControl" CHECKED onchange="if (!this.checked){this.form.warning_email.type='hidden';}  else {if(this.form.email.value.length==0){this.form.warning_email.type='text'}else{this.form.warning_email.type='hidden';}}"> _("Give submission rights to the presenter").""")
        self._params["disabledNotice"] = False
        self._params["noticeValue"] = """<i><font color="black"><b>Note: </b></font>If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the
         user will automatically be given submission rights.</i>"""

        formAction = urlHandlers.UHConfModSchedulePersonAdd.getURL(self._target)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","coauthor")
        self._params["formAction"] = formAction

        return p.getHTML(self._params)


#---------------------------------------------------------------------------

class WPNewContributionPresenterSelect( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target.getConference())
        self._target = target

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._conf,"New presenter",searchAction, forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPNewContributionPresenterNew( WPConferenceModifBase ):

    def __init__(self, rh, target, params):
        WPConferenceModifBase.__init__(self, rh, target.getConference())
        self._target = target
        self._params = params

    def _setActiveTab( self ):
        self._tabContribList.setActive()

    def _getTabContent( self, params):
        p = wcomponents.WNewPerson()

        if self._params.get("formTitle",None) is None :
                self._params["formTitle"] = _("Define new presenter")
        if self._params.get("titleValue",None) is None :
                self._params["titleValue"] = ""
        if self._params.get("surNameValue",None) is None :
                self._params["surNameValue"] = ""
        if self._params.get("nameValue",None) is None :
                self._params["nameValue"] = ""
        if self._params.get("emailValue",None) is None :
                self._params["emailValue"] = ""
        if self._params.get("addressValue",None) is None :
                self._params["addressValue"] = ""
        if self._params.get("affiliationValue",None) is None :
                self._params["affiliationValue"] = ""
        if self._params.get("phoneValue",None) is None :
                self._params["phoneValue"] = ""
        if self._params.get("faxValue",None) is None :
                self._params["faxValue"] = ""


        self._params["disabledRole"] = False
        self._params["roleDescription"] = """Submitter"""
        #if self._params.has_key("submissionControlValue"):
        self._params["roleValue"] = _(""" <input type="checkbox" name="submissionControl" CHECKED onchange="if (!this.checked){this.form.warning_email.type='hidden';}  else {if(this.form.email.value.length==0){this.form.warning_email.type='text'}else{this.form.warning_email.type='hidden';}}"> _("Give submission rights to the presenter").""")
        #else:
        #    self._params["roleValue"] = """ <input type="checkbox" name="submissionControl"> Give submission rights to the presenter."""
        self._params["disabledNotice"] = False
        self._params["noticeValue"] = _("""<i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the
         user will automatically be given submission rights.")</i>""")

        formAction = urlHandlers.UHConfModSchedulePersonAdd.getURL(self._target)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","presenter")
        self._params["formAction"] = formAction

        return p.getHTML(self._params)


#---------------------------------------------------------------------------

class WConfModMoveContribsToSession(wcomponents.WTemplated):

    def __init__(self,conf,contribIdList=[]):
        self._conf=conf
        self._contribIdList=contribIdList

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModMoveContribsToSession.getURL(self._conf)))
        vars["contribs"]=",".join(self._contribIdList)
        s=["""<option value="--none--">--none--</option>"""]
        for session in self._conf.getSessionListSorted():
            s.append("""<option value=%s>%s</option>"""%(
                quoteattr(str(session.getId())),
                self.htmlText(session.getTitle())))
        vars["sessions"]="".join(s)
        return vars


class WPModMoveContribsToSession(WPModifContribList):

    def _getPageContent(self,params):
        wc=WConfModMoveContribsToSession(self._conf,params.get("contribIds",[]))
        return wc.getHTML()


class WPModMoveContribsToSessionConfirmation(WPModifContribList):

    def _getPageContent(self,params):
        wc=wcomponents.WConfModMoveContribsToSessionConfirmation(self._conf,params.get("contribIds",[]),params.get("targetSession",None))
        p={"postURL":urlHandlers.UHConfModMoveContribsToSession.getURL(self._conf),}
        return wc.getHTML(p)


class WPConfEditContribType(WPConferenceModifBase):

    def __init__(self, rh, ct):
        self._conf = ct.getConference()
        self._contribType = ct
        WPConferenceModifBase.__init__(self, rh, self._conf)

    def _setActiveSideMenuItem(self):
        self._generalSettingsMenuItem.setActive(True)

    def _getPageContent( self, params ):
        wc = WConfEditContribType(self._contribType)
        params["saveURL"] = quoteattr(str(urlHandlers.UHConfEditContribType.getURL(self._contribType)))
        return wc.getHTML(params)


class WConfEditContribType(wcomponents.WTemplated):

    def __init__(self, contribType):
        self._contribType = contribType

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["ctName"] = self._contribType.getName()
        vars["ctDescription"] = self._contribType.getDescription()

        return vars

class WPConfAddContribType(WPConferenceModifBase):

    def _setActiveSideMenuItem(self):
        self._generalSettingsMenuItem.setActive(True)

    def _getPageContent( self, params ):
        wc = WConfAddContribType()
        params["saveURL"] = quoteattr(str(urlHandlers.UHConfAddContribType.getURL(self._conf)))
        return wc.getHTML(params)


class WConfAddContribType(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars

class WAbstractsParticipantList(wcomponents.WTemplated):

    def __init__(self, conf, emailList, displayedGroups, abstracts):
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._conf = conf
        self._abstracts = abstracts

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["submitterEmails"] = ",".join(self._emailList["submitters"]["emails"])
        vars["primaryAuthorEmails"] = ",".join(self._emailList["primaryAuthors"]["emails"])
        vars["coAuthorEmails"] = ",".join(self._emailList["coAuthors"]["emails"])

        urlDisplayGroup = urlHandlers.UHAbstractsConfManagerDisplayParticipantList.getURL(self._conf)
        abstractsToPrint = []
        for abst in self._abstracts:
            abstractsToPrint.append("""<input type="hidden" name="abstracts" value="%s">"""%abst)
        abstractsList = "".join(abstractsToPrint)
        displayedGroups = []
        for dg in self._displayedGroups:
            displayedGroups.append("""<input type="hidden" name="displayedGroups" value="%s">"""%dg)
        groupsList = "".join(displayedGroups)

        # Submitters
        text = _("show list")
        vars["submitters"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "submitters" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for subm in self._emailList["submitters"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s <%s>"%(subm.getFullName(), subm.getEmail())
                l.append("<tr>\
                        <td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["submitters"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "submitters")
        vars["showSubmitters"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), abstractsList,groupsList, text)

        # Primary authors
        text = _("show list")
        vars["primaryAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "primaryAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for pAuth in self._emailList["primaryAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s <%s>"%(pAuth.getFullName(), pAuth.getEmail())
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" \
                        class=\"blacktext\">&nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["primaryAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "primaryAuthors")
        vars["showPrimaryAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), abstractsList,groupsList, text)

        # Co-Authors
        text = _("show list")
        vars["coAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "coAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for cAuth in self._emailList["coAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                cAuthEmail = cAuth.getEmail()
                if cAuthEmail.strip() == "":
                    participant = "%s"%cAuth.getFullName()
                else:
                    participant = "%s <%s>"%(cAuth.getFullName(), cAuthEmail)
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["coAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "coAuthors")
        vars["showCoAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), abstractsList,groupsList, text)
        return vars

class WContribParticipantList(wcomponents.WTemplated):

    def __init__(self, conf, emailList, displayedGroups, contribs):
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._conf = conf
        self._contribs = contribs

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["speakerEmails"] = ", ".join(self._emailList["speakers"]["emails"])
        vars["primaryAuthorEmails"] = ", ".join(self._emailList["primaryAuthors"]["emails"])
        vars["coAuthorEmails"] = ", ".join(self._emailList["coAuthors"]["emails"])

        urlDisplayGroup = vars["urlDisplayGroup"]
        contribsToPrint = []
        for contrib in self._contribs:
            contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib)
        contribsList = "".join(contribsToPrint)
        displayedGroups = []
        for dg in self._displayedGroups:
            displayedGroups.append("""<input type="hidden" name="displayedGroups" value="%s">"""%dg)
        groupsList = "".join(displayedGroups)

        # Speakers
        text = _("show list")
        vars["speakers"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "speakers" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for speaker in self._emailList["speakers"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s <%s>"%(speaker.getFullName(), speaker.getEmail())
                l.append("<tr>\
                        <td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["speakers"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "speakers")
        vars["showSpeakers"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), contribsList,groupsList, text)

        # Primary authors
        text = _("show list")
        vars["primaryAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "primaryAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for pAuth in self._emailList["primaryAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s <%s>"%(pAuth.getFullName(), pAuth.getEmail())
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" \
                        class=\"blacktext\">&nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["primaryAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "primaryAuthors")
        vars["showPrimaryAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), contribsList,groupsList, text)

        # Co-Authors
        text = _("show list")
        vars["coAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "coAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for cAuth in self._emailList["coAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                cAuthEmail = cAuth.getEmail()
                if cAuthEmail.strip() == "":
                    participant = "%s"%cAuth.getFullName()
                else:
                    participant = "%s <%s>"%(cAuth.getFullName(), cAuthEmail)
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["coAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "coAuthors")
        vars["showCoAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), contribsList,groupsList, text)
        return vars


class WPAbstractSendNotificationMail(WPConferenceBase):

    def __init__(self, rh, conf, count):
        WPConferenceBase.__init__(self, rh, conf)
        self._count = count

    def _getBody( self, params ):
        return _("""
<table align="center"><tr><td align="center">
<b> _("The submitters of the selected abstracts will nearly recieve the notification mail").<br>
<br>
_("You can now close this window.")</b>
</td></tr></table>

""")


class WPContributionList( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEContributionList

    def _getBody( self, params ):
        wc = WConfContributionList( self._getAW(), self._conf, params["sortingCrit"], params["filterCrit"],  params.get("order","down"),params.get("sc",1), params.get("nc",20) )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._contribListOpt)


class WConfContributionList ( wcomponents.WTemplated ):

    def __init__(self,aw,conf,sortingCrit,filterCrit,order,sContrib=1,displayContribs=20):
        self._aw = aw
        self._conf = conf
        self._sortingCrit = sortingCrit
        self._filterCrit = filterCrit
        self._startContrib=int(sContrib)
        self._displayContribs=int(displayContribs)
        self._order = order
        if len(self._conf.getTrackList()) > 0:
            self._displayTrackFilter = True
        else:
            self._displayTrackFilter = False
        if len(self._conf.getContribTypeList()) > 0:
            self._displayTypeFilter = True
        else:
            self._displayTypeFilter = False

    def _getMaterialIcon(self, iconURL, alt):
        return """
                <img src="%s" alt="%s" border="0">
               """%(iconURL, alt)

    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHContributionList.getURL( self._conf )
        if self._filterCrit.getField( "type" ):
            l=[]
            for t in self._filterCrit.getField( "type" ).getValues():
                if t!="":
                    l.append(t)
            url.addParam( "selTypes", l )
            if self._filterCrit.getField( "type" ).getShowNoValue():
                url.addParam( "typeShowNoValue", "1" )
        if self._filterCrit.getField( "track" ):
            url.addParam( "selTracks", self._filterCrit.getField( "track" ).getValues() )
            if self._filterCrit.getField( "track" ).getShowNoValue():
                url.addParam("trackShowNoValue", "1")
        if self._filterCrit.getField( "session" ):
            url.addParam( "selSessions", self._filterCrit.getField( "session" ).getValues() )
            if self._filterCrit.getField( "session" ).getShowNoValue():
                url.addParam("sessionShowNoValue", "1")
        if self._sortingCrit.getField():
            url.addParam( "sortBy", self._sortingCrit.getField().getId() )
            url.addParam("order",self._order)
        url.addParam("OK", "1")
        return url

    def _getContribFullHTML( self, contrib ):
        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        sdate = ""
        if contrib.isScheduled():
           sdate=contrib.getAdjustedStartDate(tz).strftime("%d-%b-%Y %H:%M" )
           sdate = sdate
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionDisplay.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        contribType = ""
        if contrib.getType() is not None:
            contribType = contrib.getType().getName()
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            if contrib.getSession().getCode() != "no code":
                session=self.htmlText(contrib.getSession().getCode())
            else:
                session=self.htmlText(contrib.getSession().getTitle())
        track = ""
        if contrib.getTrack() is not None:
            track = self.htmlText( contrib.getTrack().getCode() )
        trackHTML = typeHTML = ""
        if self._displayTrackFilter:
            trackHTML = """
                <td class="abstractDataCell">%s</td>""" % (track or "&nbsp;")
        if self._displayTypeFilter:
            typeHTML = """
                <td class="abstractDataCell">%s</td>""" % (contribType or "&nbsp;")
        mat = []
        if contrib.getSlides():
            if contrib.getSlides().canView(self._aw):
                url = urlHandlers.UHMaterialDisplay.getURL(contrib.getSlides())
                mat.append("<a href=%s>%s</a>" % ( quoteattr(str(url)),self._getMaterialIcon(Config.getInstance().getSystemIconURL( "slides" ), "Slides")))
        if contrib.getPaper():
            if contrib.getPaper().canView(self._aw):
                url = urlHandlers.UHMaterialDisplay.getURL(contrib.getPaper())
                mat.append("<a href=%s>%s</a>" % ( quoteattr(str(url)),self._getMaterialIcon(Config.getInstance().getSystemIconURL( "paper" ), "Paper")))
        material = "".join(mat)
        html = """
            <tr>
                <td valign="top" nowrap><input type="checkbox" name="contributions" value=%s></td>
                <td class="abstractLeftDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                %s
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                %s
                <td class="abstractDataCell">%s</td>
            </tr>
                """%(contrib.getId(), self.htmlText( contrib.getId() ),
                    sdate or "&nbsp;", typeHTML,
                    title or "&nbsp;", speaker or "&nbsp;",
                    session or "&nbsp;", trackHTML, material or "&nbsp;" )
        return html

    def _getContribMinHTML( self, contrib ):
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionDisplay.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        mat = []
        if contrib.getSlides():
            if contrib.getSlides().canView(self._aw):
                mat.append(self._getMaterialIcon(Config.getInstance().getSystemIconURL( "slides" ), _("Slides")))
        if contrib.getPaper():
            if contrib.getPaper().canView(self._aw):
                mat.append(self._getMaterialIcon(Config.getInstance().getSystemIconURL( "paper" ), _("Paper")))
        material = "".join(mat)
        trackHTML = typeHTML = ""
        if self._displayTrackFilter:
            trackHTML = """
                <td class="abstractDataCell"></td>"""
        if self._displayTypeFilter:
            typeHTML = """
                <td class="abstractDataCell"></td>"""
        html = """
            <tr>
                <td><input type="checkbox" name="contributions" value=%s></td>
                <td class="abstractLeftDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                %s
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                %s
                <td class="abstractDataCell">%s</td>
            </tr>
                """%(self.htmlText( contrib.getId() ), "&nbsp;", "&nbsp;", typeHTML, title or "&nbsp;", "&nbsp;", "&nbsp;", trackHTML,  material or "&nbsp;" )
        return html

    def _getTypeFilterItemList( self ):
        checked = ""
        if self._filterCrit.getField("type").getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="typeShowNoValue"%s> --_("not specified")--""")%checked]
        for type in self._conf.getContribTypeList():
            checked = ""
            if type.getId() in self._filterCrit.getField("type").getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selTypes" value=%s%s> %s"""%(quoteattr(type.getId()), checked, self.htmlText(type.getName())) )
        return l

    def _getTrackFilterItemList( self ):
        checked = ""
        if self._filterCrit.getField("track").getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="trackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if t.getId() in self._filterCrit.getField("track").getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selTracks" value=%s%s> (%s) %s"""%(quoteattr(t.getId()), checked, self.htmlText(t.getCode()), self.htmlText(t.getTitle()) ) )
        return l

    def _getSessionFilterItemList( self ):
        checked = ""
        if self._filterCrit.getField("session").getShowNoValue():
            checked = " checked"
        l = [ _("""<input type="checkbox" name="sessionShowNoValue"%s> --_("not specified")--""")%checked]
        for s in self._conf.getSessionListSorted():
            checked = ""
            if s.getCode() != "no code":
                codeText = "(%s) " % self.htmlText(s.getCode())
            else:
                codeText = ""
            if s.getId() in self._filterCrit.getField("session").getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="selSessions" value=%s%s>%s%s"""%(quoteattr(s.getId()), checked, codeText, self.htmlText(s.getTitle()) ) )
        return l

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["types"] = vars["tracks"] = ""
        vars["typeFilterHeader"] = vars["trackFilterHeader"] = ""
        if self._displayTypeFilter:
            vars["typeFilterHeader"] = _("""<td align="center" class="titleCellFormat" style="padding-right:10px"> _("show contribution types")</td>""")
            vars["types"] = """<td valign="top" style="border-right:1px solid #777777;">%s</td>""" % "<br>".join( self._getTypeFilterItemList() )
        if self._displayTrackFilter:
            vars["trackFilterHeader"] = _("""<td align="center" class="titleCellFormat"> _("show tracks")</td>""")
            vars["tracks"] = """<td valign="top">%s</td>""" % "<br>".join( self._getTrackFilterItemList() )
        vars["sessions"] = "<br>".join( self._getSessionFilterItemList() )
        l = []
        contribsToPrint = []
        f = filters.SimpleFilter( self._filterCrit, self._sortingCrit )
        contribList = f.apply( self._conf.getContributionList() )
        num=1
        self._endContrib=(self._startContrib+self._displayContribs)-1
        for contrib in contribList:
            if num<self._startContrib:
                num+=1
                continue
            elif num>self._endContrib:
                break
            else:
                num+=1
            if contrib.canAccess( self._aw ):
                l.append( self._getContribFullHTML( contrib ) )
                contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib.getId())
            #elif contrib.canView( self._aw ):
            else:
                l.append( self._getContribMinHTML( contrib ) )
                contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib.getId())
        if self._order =="up":
            l.reverse()
        vars["numContribs"]=len(contribList)
        vars["contribSetIndex"]=_("showing")+" %s-%s "%(self._startContrib,self._endContrib)
        if self._startContrib!=1:
            iconURL=Config.getInstance().getSystemIconURL("arrow_previous")
            url=self._getURL()
            newSc=self._startContrib-self._displayContribs
            if newSc<1:
                newSc=1
            url.addParam("sc",newSc)
            url.setSegment("contribs")
            vars["contribSetIndex"]="""<a href=%s><img src=%s border="0" style="vertical-align:middle" alt=""></a>%s"""%(quoteattr(str(url)),quoteattr(str(iconURL)),vars["contribSetIndex"])
        if self._endContrib<vars["numContribs"]:
            iconURL=Config.getInstance().getSystemIconURL("arrow_next")
            url=self._getURL()
            url.setSegment("contribs")
            url.addParam("sc",num)
            vars["contribSetIndex"]="""%s<a href=%s><img src=%s border="0" style="vertical-align:middle" alt=""></a>"""%(vars["contribSetIndex"],quoteattr(str(url)),quoteattr(str(iconURL)))

        vars["contributions"] = "".join(l)
        vars["contribsToPrint"] = "\n".join(contribsToPrint)

        vars["newContribURL"] = urlHandlers.UHConfAddContribution.getURL( self._conf )

        sortingField = self._sortingCrit.getField()
        vars["currentSorting"]=""

        url=self._getURL()

        url.addParam("sortBy","number")
        vars["numberImg"]=""
        url.addParam("sc",(num-self._displayContribs))
        if sortingField and sortingField.getId() == "number":

            vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value="_("number")">""")
            if self._order == "down":
                vars["numberImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["numberImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")

        vars["numberSortingURL"]=quoteattr(str(url))
        url = self._getURL()
        url.addParam("sortBy", "date")
        vars["dateImg"] = ""
        url.addParam("sc",(num-self._displayContribs))
        if sortingField and sortingField.getId() == "date":

            vars["currentSorting"]= _("""<input type="hidden" name="sortBy" value="_("date")">""")
            if self._order == "down":
                vars["dateImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["dateImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["dateSortingURL"]=quoteattr(str(url))

        if self._displayTypeFilter:
            url = self._getURL()
            url.addParam("sortBy", "type")
            typeImg = ""
            url.addParam("sc",(num-self._displayContribs))
            if sortingField and sortingField.getId() == "type":
                vars["currentSorting"]= _("""<input type="hidden" name="sortBy" value="_("type")">""")
                if self._order == "down":
                    typeImg="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    typeImg="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
            typeSortingURL = quoteattr( str( url ) )
            vars["typeHeader"] = """<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> %s<a href=%s>Type</a></td>""" % (typeImg,typeSortingURL)
        else:
            vars["typeHeader"] = ""

        url = self._getURL()
        url.addParam("sortBy", "name")
        vars["titleImg"] = ""
        url.addParam("sc",(num-self._displayContribs))
        if sortingField and sortingField.getId() == "name":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="name">"""
            if self._order == "down":
                vars["titleImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["titleImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["titleSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "speaker")
        vars["speakerImg"] = ""
        url.addParam("sc",(num-self._displayContribs))
        if sortingField and sortingField.getId() == "speaker":
            vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value="_("speaker")">""")
            if self._order == "down":
                vars["speakerImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["speakerImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["speakerSortingURL"]=quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy", "session")
        vars["sessionImg"] = ""
        url.addParam("sc",(num-self._displayContribs))
        if sortingField and sortingField.getId() == "session":
            vars["currentSorting"] = _("""<input type="hidden" name="sortBy" value="_("session")">""")
            if self._order == "down":
                vars["sessionImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["sessionImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["sessionSortingURL"]=quoteattr( str( url ) )

        if self._displayTrackFilter:
            url = self._getURL()
            url.addParam("sortBy", "track")
            trackImg = ""
            url.addParam("sc",(num-self._displayContribs))
            if sortingField and sortingField.getId() == "track":
                vars["currentSorting"]= _("""<input type="hidden" name="sortBy" value="_("track")">""")
                if self._order == "down":
                    trackImg="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    trackImg="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
            trackSortingURL = quoteattr( str( url ) )
            vars["trackHeader"] = _("""<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> %s<a href=%s> _("Track")</a></td>""") % (trackImg,trackSortingURL)
        else:
            vars["trackHeader"] = ""

        url = urlHandlers.UHContributionList.getURL( self._conf )
        url.setSegment( "contributions" )
        vars["filterPostURL"] = quoteattr( str( url ) )

        vars["contribSelectionAction"]=quoteattr(str(urlHandlers.UHContributionListAction.getURL(self._conf)))
        vars["contributionsPDFURL"]=quoteattr(str(urlHandlers.UHContributionListToPDF.getURL(self._conf)))

        return vars


class WConfAuthorIndex(wcomponents.WTemplated):

    def __init__(self,aw,conf,view,selLetter="[all]"):
        self._aw=aw
        self._conf=conf
        self._view=view
        self._selLetter=selLetter


    def _getContribMinView(self,contrib):
        return """<a href=%s>#%s</a>"""%(quoteattr(str(self._urlGen(contrib))),self.htmlText(contrib.getId()))

    def _getContribFullView(self,contrib):
        return """<p style="text-indent: -3em;margin-left:3em"><a href=%s">%s-%s</a></p>"""%(quoteattr(str(self._urlGen(contrib))),self.htmlText(contrib.getId()),self.htmlText(contrib.getTitle()))

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPaper" ))),
                self.htmlText("paper")))
        slides=contrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slides"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallSlides" ))),
                self.htmlText("slides")))
        poster=contrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(poster))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPoster" ))),
                self.htmlText("poster")))
        slides=contrib.getSlides()
        video=contrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallVideo" ))),
                self.htmlText("video")))
        return ", ".join(lm)

    def _getItemHTML(self,pl, key):

        if len(pl)<=0:
            return ""
        auth=pl[0]
        authCaption="%s"%auth.getFamilyName().upper()
        #if authCaption.strip()=="":
        #    return ""
        #if self._selLetter!='[all]' and authCaption[0].lower()!=self._selLetter:
        #    return ""
        if auth.getFirstName()!="":
            authCaption="%s, %s"%(authCaption,auth.getFirstName())
        itemFormatFunc=self._getContribMinView
        if self._view=="full":
            itemFormatFunc=self._getContribFullView

        self._urlGen=urlHandlers.UHContributionDisplay.getURL
        contribList=[itemFormatFunc(auth.getContribution()) for auth in pl]
        if authCaption.strip()=="":
            return ""
        authId = key
        authorURL = urlHandlers.UHContribAuthorDisplay.getURL(self._conf)
        authorURL.addParam( "authorId", authId )
        contribList=[]
        for auth in pl:
            contrib=auth.getContribution()
            url=urlHandlers.UHContributionDisplay.getURL(contrib)
            if self._view=="full":
                material = self._getMaterialHTML(contrib)
                if material.strip()!="":
                    material = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;( %s )"%material
                contribList.append("""<p style="text-indent: -3em;margin-left:3em"><a href=%s">%s-%s</a>%s</p>"""%(quoteattr(str(url)),self.htmlText(contrib.getId()),self.htmlText(contrib.getTitle()), material ))
            else:
                contribList.append("""<a href=%s>#%s</a>"""%(quoteattr(str(url)),self.htmlText(contrib.getId())))
        if self._view=="full":
            res="""
                <tr>
                    <td valign="top" nowrap><a href=%s>%s</a></td>
                    <td width="100%%">%s</td>
                </tr>
                <tr>
                    <td colspan="2" style="border-bottom: 1px solid; border-color: #EAEAEA">&nbsp;</td>
                </tr>"""%(quoteattr(str(authorURL)), self.htmlText(authCaption),"".join(contribList))
        else:
            res="""
                <tr>
                    <td valign="top"><a href=%s>%s</a></td>
                    <td width="100%%">%s</td>
                </tr>
                """%(quoteattr(str(authorURL)), self.htmlText(authCaption),", ".join(contribList))
        return res

    def _getLetterIndex(self):
        url=urlHandlers.UHConfAuthorIndex.getURL(self._conf)
        res=[]
        for letter in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','[all]']:
            url.addParam("letter",letter)
            url.addParam("view",self._view)
            res.append("""<a href=%s>%s</a> """%(quoteattr(str(url)),letter))
        return " | ".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        availViewModes=[["full", _("use contribution ids and titles")],
                        ["onlyIds", _("use contribution ids")]]
        res=[]

        for vm in availViewModes:
            sel=""
            if self._view==vm[0]:
                sel=" selected"

            res.append("""<option value=%s%s>%s</option>"""%(
                    quoteattr(str(vm[0])),sel,self.htmlText(vm[1])))
        vars["viewModes"]="".join(res)
        displayURL = urlHandlers.UHConfAuthorIndex.getURL(self._conf)
        displayURL.addParam("letter", self._selLetter)
        vars["displayURL"]=quoteattr(str(displayURL))
        vars["letterIndex"]=self._getLetterIndex()
        res=[]
        for key in self._conf.getAuthorIndex().getParticipationKeys():
            pl = self._conf.getAuthorIndex().getById(key)
            try:
                auth=pl[0]
            except IndexError:
                continue
            authCaption="%s"%auth.getFamilyName().upper()
            if authCaption.strip()=="":
                continue
            if self._selLetter!='[all]':
                if authCaption[0].lower()>self._selLetter:
                    break
                elif authCaption[0].lower()!=self._selLetter:
                    continue
            res.append(self._getItemHTML(pl, key))
        vars["items"]="".join(res)
        return vars


class WPAuthorIndex(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEAuthorIndex

    def _getBody(self,params):
        view = params.get("viewMode","full")
        wc=WConfAuthorIndex(self._getAW(),self._conf,view,params.get("selLetter","a"))
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._authorIndexOpt)

class WConfSpeakerIndex(wcomponents.WTemplated):

    def __init__(self,aw,conf,view,selLetter="[all]"):
        self._aw=aw
        self._conf=conf
        self._view=view
        self._selLetter=selLetter


    def _getContribMinView(self,contrib):
        return """<a href=%s>#%s</a>"""%(quoteattr(str(self._urlGen(contrib))),self.htmlText(contrib.getId()))

    def _getContribFullView(self,contrib):
        if contrib is not None:
            return """<p style="text-indent: -3em;margin-left:3em"><a href=%s">%s-%s</a></p>"""%(quoteattr(str(self._urlGen(contrib))),self.htmlText(contrib.getId()),self.htmlText(contrib.getTitle()))
        return ""

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPaper" ))),
                self.htmlText("paper")))
        slides=contrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slides"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallSlides" ))),
                self.htmlText("slides")))
        poster=contrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(poster))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPoster" ))),
                self.htmlText("poster")))
        slides=contrib.getSlides()
        video=contrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallVideo" ))),
                self.htmlText("video")))
        return ", ".join(lm)

    def _getItemHTML(self,pl, key):
        if len(pl)<=0:
                return ""
        auth=pl[0]
        authCaption="%s"%auth.getFamilyName().upper()
        #if authCaption.strip()=="":
        #    return ""
        #if self._selLetter!='[all]' and authCaption[0].lower()!=self._selLetter:
        #    return ""
        if auth.getFirstName()!="":
            authCaption="%s, %s"%(authCaption,auth.getFirstName())
        itemFormatFunc=self._getContribMinView
        if self._view=="full":
            itemFormatFunc=self._getContribFullView

        self._urlGen=urlHandlers.UHContributionDisplay.getURL
        participationList=[itemFormatFunc(auth.getContribution()) for auth in pl]
        if authCaption.strip()=="":
                return ""
        authId = key
        #authorURL = urlHandlers.UHContribAuthorDisplay.getURL(self._conf)
        #authorURL.addParam( "authorId", authId )
        participationList=[]
        for auth in pl:
            participationId=""
            if isinstance(auth, conference.SubContribParticipation):
                participation=auth.getSubContrib()
                if participation is None:
                    continue
                url=urlHandlers.UHSubContributionDisplay.getURL(participation)
                participationId="%s-%s"%(participation.getContribution().getId(), participation.getId())
            else:
                participation=auth.getContribution()
                if participation is None:
                    continue
                url=urlHandlers.UHContributionDisplay.getURL(participation)
                participationId="%s"%(participation.getId())
            if self._view=="full":
                material = self._getMaterialHTML(participation)
                if material.strip()!="":
                        material = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;( %s )"%material
                participationList.append("""<p style="text-indent: -3em;margin-left:3em"><a href=%s">%s-%s</a>%s</p>"""%(quoteattr(str(url)),self.htmlText(participationId),self.htmlText(participation.getTitle()), material ))
            else:
                participationList.append("""<a href=%s>#%s</a>"""%(quoteattr(str(url)),self.htmlText(participationId)))
        if self._view=="full":
            res="""
                    <tr>
                            <td valign="top" nowrap>%s</td>
                            <td width="100%%">%s</td>
                    </tr>
                    <tr>
                            <td colspan="2" style="border-bottom: 1px solid; border-color: #EAEAEA">&nbsp;</td>
                    </tr>"""%(self.htmlText(authCaption),"".join(participationList))
        else:
            res="""
                    <tr>
                            <td valign="top">%s</td>
                            <td width="100%%">%s</td>
                    </tr>
                    """%(self.htmlText(authCaption),", ".join(participationList))
        return res

    def _getLetterIndex(self):
        url=urlHandlers.UHConfSpeakerIndex.getURL(self._conf)
        res=[]
        for letter in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','[all]']:
            url.addParam("letter",letter)
            url.addParam("view",self._view)
            res.append("""<a href=%s>%s</a> """%(quoteattr(str(url)),letter))
        return " | ".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        availViewModes=[["full", _("use contribution ids and titles")],
                        ["onlyIds", _("use contribution ids")]]
        res=[]

        for vm in availViewModes:
            sel=""
            if self._view==vm[0]:
                sel=" selected"

            res.append("""<option value=%s%s>%s</option>"""%(
                    quoteattr(str(vm[0])),sel,self.htmlText(vm[1])))
        vars["viewModes"]="".join(res)
        displayURL = urlHandlers.UHConfSpeakerIndex.getURL(self._conf)
        displayURL.addParam("letter", self._selLetter)
        vars["displayURL"]=quoteattr(str(displayURL))
        vars["letterIndex"]=self._getLetterIndex()
        res=[]
        for key in self._conf.getSpeakerIndex().getParticipationKeys():
            pl = self._conf.getSpeakerIndex().getById(key)
            try:
                auth=pl[0]
            except IndexError:
                continue
            authCaption="%s"%auth.getFamilyName().upper()
            if authCaption.strip()=="":
                continue
            if self._selLetter!='[all]':
                if authCaption[0].lower()>self._selLetter:
                    break
                elif authCaption[0].lower()!=self._selLetter:
                    continue
            res.append(self._getItemHTML(pl, key))
        vars["items"]="".join(res)
        return vars

class WPSpeakerIndex(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NESpeakerIndex

    def _getBody(self,params):
        view = params.get("viewMode","full")
        wc=WConfSpeakerIndex(self._getAW(),self._conf,view,params.get("selLetter","a"))
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._speakerIndexOpt)

class WConfMyContributions(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw=aw
        self._conf=conf

    def getHTML(self, params):
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["User"] = self._aw.getUser()
        vars["Conference"] = self._conf
        return vars


class WConfMyStuff(wcomponents.WTemplated):

    def __init__(self,aw,conf):
        self._aw=aw
        self._conf=conf

    def _getSessionsHTML(self):
        if self._aw.getUser() is None:
            return ""
        #ls=self._conf.getCoordinatedSessions(self._aw.getUser())+self._conf.getManagedSession(self._aw.getUser())
        from sets import Set
        ls = Set(self._conf.getCoordinatedSessions(self._aw.getUser()))
        ls = list(ls | Set(self._conf.getManagedSession(self._aw.getUser())))
        if len(ls)<=0:
            return ""
        res=[]
        iconURL=Config.getInstance().getSystemIconURL("modify")
        for s in ls:
            modURL=urlHandlers.UHSessionModification.getURL(s)
            dispURL=urlHandlers.UHSessionDisplay.getURL(s)
            res.append("""
                <tr>
                    <td>&nbsp;&nbsp;</td>
                    <td nowrap><a href=%s><img src=%s border="0" alt=""></a></td>
                    <td width="100%%"><a href=%s>%s</a></td>
                </tr>"""%(quoteattr(str(modURL)),
                            quoteattr(str(iconURL)),
                            quoteattr(str(dispURL)),
                            self.htmlText(s.getTitle())))
        return """<br>
            <table style="border-left:1px solid #777777;border-top:1px solid #777777;" width="70%%" align="center" cellspacing="0">
                <tr>
                    <td class="groupTitle" colspan="4" style="background:#E5E5E5; color:gray; border-top:2px solid #FFFFFF; border-left:2px solid #FFFFFF">&nbsp;&nbsp;&nbsp;Sessions</td>
                </tr>
                <tr>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td>%s</td>
                </tr>
            </table>
            """%"".join(res)

    def _getTracksHTML(self):
        if self._aw.getUser() is None or not self._conf.hasEnabledSection("cfa"):
            return ""
        lt=self._conf.getCoordinatedTracks(self._aw.getUser())
        if len(lt)<=0:
            return ""
        res=[]
        iconURL=Config.getInstance().getSystemIconURL("modify")
        for t in lt:
            modURL=urlHandlers.UHTrackModifAbstracts.getURL(t)
            res.append("""
                <tr>
                    <td>&nbsp;&nbsp;</td>
                    <td nowrap><a href=%s><img src=%s border="0" alt=""></a></td>
                    <td width="100%%">%s</td>
                </tr>"""%(quoteattr(str(modURL)),
                            quoteattr(str(iconURL)),
                            self.htmlText(t.getTitle())))
        return """<br>
            <table style="border-left:1px solid #777777;border-top:1px solid #777777;" width="70%%" align="center" cellspacing="0">
                <tr>
                    <td class="groupTitle" colspan="4" style="background:#E5E5E5; color:gray; border-top:2px solid #FFFFFF; border-left:2px solid #FFFFFF">&nbsp;&nbsp;&nbsp;Tracks</td>
                </tr>
                <tr>
                    <td>&nbsp;</td>
                </tr>
                <tr>
                    <td>%s</td>
                </tr>
            </table>
            """%"".join(res)

    def _getContribsHTML(self):
        return WConfMyContributions(self._aw, self._conf).getHTML({})

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["items"]="%s%s%s"%(self._getSessionsHTML(),
            self._getTracksHTML(),self._getContribsHTML())

        import reviewing
        vars["hasPaperReviewing"] = self._conf.hasEnabledSection('paperReviewing')
        vars["ContributionReviewingTemplatesList"] = reviewing.WContributionReviewingTemplatesList(self._conf).getHTML({"CanDelete" : False})
        return vars


class WPMyStuff(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff

    def _getBody(self,params):
        wc=WConfMyStuff(self._getAW(),self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._myStuffOpt)


class WConfModAbstractBook(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        boaConfig=self._conf.getBOAConfig()
        vars["modURL"]=quoteattr(str(urlHandlers.UHConfModAbstractBookEdit.getURL(self._conf)))
        vars["text"]=boaConfig.getText()
        return vars


class WPModAbstractBook(WPConferenceModifAbstractBase):

    def _setActiveTab( self ):
        self._tabBOA.setActive()

    def _getTabContent( self, params ):
        wc=WConfModAbstractBook(self._conf)
        return wc.getHTML()


class WConfModAbstractBookEdit(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        boaConfig=self._conf.getBOAConfig()
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModAbstractBookEdit.getURL(self._conf)))
        vars["text"]=self.htmlText(boaConfig.getText())
        return vars


class WPModAbstractBookEdit(WPConferenceModifAbstractBase):

    def _setActiveTab( self ):
        self._tabBOA.setActive()

    def _getTabContent( self, params ):
        wc=WConfModAbstractBookEdit(self._conf)
        return wc.getHTML()

class WPFullMaterialPackage( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabMatPackage.setActive()

    def _getTabContent( self, params ):
        wc = WFullMaterialPackage( self._conf )
        p = {"errors": params.get("errors","")}
        return wc.getHTML(p)

class WFullMaterialPackage(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        if not vars.has_key("getPkgURL"):
            vars["getPkgURL"] = quoteattr(str(urlHandlers.UHConfModFullMaterialPackagePerform.getURL(self._conf)))

        #######################################
        # Fermi timezone awareness            #
        #######################################
        sDate = self._conf.getSchedule().getAdjustedStartDate()
        eDate = self._conf.getSchedule().getAdjustedEndDate()
        #######################################
        # Fermi timezone awareness(end)       #
        #######################################
        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")
        htmlDay = []
        while sDate <= eDate:
            htmlDay.append("""
                    <tr>
                        <td nowrap="nowrap" valign="top"><input name="days" type="checkbox" checked="checked" value="%s">%s</td>
                    </tr>
                  """%(sDate.strftime("%d%B%Y"), sDate.strftime("%d %B %Y") ) )
            sDate += timedelta(days=1)
        vars["dayList"] = "".join(htmlDay)
        vars["sessionList"] = ""
        if len(self._conf.getSessionList()) == 0:
            vars["sessionList"] = "No session in this event"
        for session in self._conf.getSessionList():
            vars["sessionList"] += _("""
                 <input name="sessionList" type="checkbox" value="%s" checked="checked">%s _("(last modified: %s)")<br>""") % (session.getId(),session.getTitle(),session.getModificationDate().strftime("%d %B %Y %H:%M"))
        vars["materialType"] = _("""
                                <tr>
            <td>
                <input name="materialType" type="checkbox" value="paper" checked="checked"> _("Papers")
                <br>
                <input name="materialType" type="checkbox" value="slides" checked="checked"> _("Slides")
                <br>
                <input name="materialType" type="checkbox" value="video" checked="checked"> _("Videos")
                <br>
                <input name="materialType" type="checkbox" value="poster" checked="checked"> _("Posters")
                <br>
                <input name="materialType" type="checkbox" value="minutes" checked="checked"> _("Minutes")
                <br>
                <input name="materialType" type="checkbox" value="other" checked="checked"> _("Other types")
            </td>
        </tr>
        """)
        return vars

# ------------------ Static web pages ------------------

class WPConferenceStaticDefaultDisplayBase( WPConferenceDefaultDisplayBase ):

    def _getHTMLHeader( self ):
        cssDir="./css"
        if len(self._staticPars) > 0 and self._staticPars.values()[0].startswith(".."):
            cssDir="../css"
        return """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
    <head>
        <title>%s</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <link rel="shortcut icon" href=%s>
        <link rel="stylesheet" type="text/css"  href="%s/%s">
    </head>
    <body>
        %s
                """%(self._getTitle(), quoteattr(self._staticPars["addressBarIcon"]),
                        cssDir, Config.getInstance().getCssStylesheetName(),
                        self._getWarningMessage())

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WStaticWebHeader()
        params = {}
        params["imgLogo"] = self._staticPars["miniLogo"]
        return wc.getHTML( params )

    def _applyConfDisplayDecoration( self, body ):
        frame = WConfStaticDisplayFrame( self._getAW(), self._conf, self._staticPars)
        frameParams = {}
        body = """
                <div class="confBodyBox clearfix">
                 <div style="width: 100%;">
                    <!--Main body-->
                    %s
                 </div>
                </div>"""%( body )
        return frame.getHTML( self._sectionMenu, body, frameParams)

class WConfStaticDetails( wcomponents.WTemplated ):

    def __init__(self, aw, conf, staticPars):
        self._conf = conf
        self._aw = aw
        self._staticPars = staticPars

    def _getChairsHTML( self ):
        chairList = []
        l = []
        for chair in self._conf.getChairList():
            mailToURL = """mailto:%s"""%urllib.quote(chair.getEmail())
            l.append( """<a href=%s>%s</a>"""%(quoteattr(mailToURL),self.htmlText(chair.getFullName())))
        res = ""
        if len(l) > 0:
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Chairs"):</b></td>
        <td>%s</td>
    </tr>
                """)%"<br>".join(l)
        return res

    def _getMaterialHTML( self ):
        l = []
        for mat in self._conf.getAllMaterialList():
            temp = wcomponents.WMaterialDisplayItem()
            url = urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat)
            l.append( temp.getHTML( self._aw, mat, url, self._staticPars["material"] ) )
        res = ""
        if l:
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Material"):</b></td>
        <td align="left" width="100%%">%s</td>
    </tr>""")%"<br>".join( l )
        return res

    def _getMoreInfoHTML( self ):
        res = ""
        if self._conf.getContactInfo() != "":
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Additional info"):</b>
        </td>
        <td>%s</td>
    </tr>""")%self._conf.getContactInfo()
        return res

    def _getActionsHTML( self, showActions = False):
        html=[]
        if showActions:
            html=[ _("""
                <table style="padding-top:40px; padding-left:20px">
                <tr>
                    <td nowrap>
                        <b> _("Conference sections"):</b>
                        <ul>
                """)]
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            for link in menu.getLinkList():
                if link.isVisible() and link.isEnabled():
                    html.append(""" <li><a href="%s">%s</a></li>
                            """%( link.getURL(), link.getCaption() ) )
            html.append("""
                        </ul>
                    </td>
                </tr>
                </table>
                """)
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["description"] = self._conf.getDescription()
        sdate, edate = self._conf.getAdjustedStartDate(), self._conf.getAdjustedEndDate()
        fsdate, fedate = sdate.strftime("%d %B %Y"), edate.strftime("%d %B %Y")
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        vars["dateInterval"] = "from %s %s to %s %s"%(fsdate, fstime, \
                                                        fedate, fetime)
        if sdate.strftime("%d%B%Y") == edate.strftime("%d%B%Y"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s-%s"%(fstime, fetime)
            vars["dateInterval"] = "%s (%s)"%( fsdate, timeInterval)
        vars["location"] = ""
        location = self._conf.getLocation()
        if location:
            vars["location"] = "<i>%s</i><br><pre>%s</pre>"%( location.getName(), location.getAddress() )
            room = self._conf.getRoom()
            if room:
                roomLink = linking.RoomLinker().getHTMLLink( room, location )
                vars["location"] += _("""<small> _("Room"):</small> %s""")%roomLink
        vars["chairs"] = self._getChairsHTML()
        vars["material"] = self._getMaterialHTML()
        vars["moreInfo"] = self._getMoreInfoHTML()
        vars["actions"] = self._getActionsHTML(vars.get("menuStatus", "open") != "open")

        return vars

class ConfStaticDisplayMenu:

    def __init__(self, menu, linkList):
        self._menu = menu
        self._linkList = linkList

    def getHTML(self, params):
        html = []
        html = ["""<!--Left menu-->
                        <div class="conf_leftMenu">
                                    <ul>
                                            <li class="menuConfTopCell">
                                                &nbsp;
                                            </li>
                                        """]
        for link in self._linkList:
            if link.isVisible():
                html.append(self._getLinkHTML(link, params))
        html.append("""<li class="menuConfBottomCell">&nbsp;</li>""")
        html.append("""             </ul>
                                <div align="left" class="confSupportEmailBox">%s</div>
                    </div>"""%params["supportEmail"])
        return "".join(html)

    def _getLinkHTML(self, link, params, indent=""):
        if not link.isVisible():
            return ""
        if link.getType() == "spacer":
            html = """<tr><td><br></td></tr>\n"""
        else:
            parentDir = ""
            if len(params) > 0 and params.values()[0].startswith(".."):
                parentDir = "."
            target = ""
            sublinkList=[]

            for sublink in link.getEnabledLinkList():
                if sublink.isVisible():
                    sublinkList.append(sublink)

            if isinstance(link,displayMgr.ExternLink):
                target=""" target="_blank" """
            #Commented because menuicon variable is not used anymore
            #if sublinkList:
            #    menuicon=params["arrowBottomMenuConf"]
            #else:
            #    menuicon=params["arrowRightMenuConf"]

            #TODO: eventually change this so that it's the same as the non-static menu
            if self._menu.isCurrentItem(link):
                url="%s%s"%(parentDir, link.getStaticURL())
                html = ["""<li id="menuLink_%s" class="menuConfSelected" nowrap><a href="%s"%s>%s</a></li>\n"""%(sublink.getName(), url, target, \
                         link.getCaption())]
            else:
                url="%s%s"%(parentDir, link.getStaticURL())
                html = ["""<li id="menuLink_%s" class="menuConfTitle" nowrap><a class="confSection" href="%s"%s>%s</a></li>\n"""%(sublink.getName(), url, target, link.getCaption())]

            for sublink in sublinkList:
                target = ""
                if isinstance(link, displayMgr.ExternLink):
                    target =  " target=\"_blank\""
                if self._menu.isCurrentItem(sublink):
                    url="%s%s"%(parentDir, sublink.getStaticURL())
                    html.append("""<li id="menuLink_%s" class="menuConfSelected" nowrap><a href="%s"%s>\
                            %s</a></li>\n"""\
                            %(sublink.getName(), url, target,  sublink.getCaption()))
                else:
                    url="%s%s"%(parentDir, sublink.getStaticURL())
                    html.append( """<li id="menuLink_%s" class="menuConfMiddleCell" nowrap><a class="confSubSection" href="%s"%s>\
                            <img border="0" src="%s" alt="">&nbsp;%s</a></li>"""%(sublink.getName(), url, target,\
                            params["bulletMenuConf"], sublink.getCaption()) )
        return "".join(html)

class WConfStaticDisplayFrame(wcomponents.WTemplated):

    def __init__(self, aw, conf, staticPars):
        self._aw = aw
        self._conf = conf
        self._staticPars = staticPars

    def getHTML( self, menu, body, params ):
        self._body = body
        self._menu = menu
        return wcomponents.WTemplated.getHTML( self, params )

    def _getMenuList(self, menuIds):
        l = []
        for id in menuIds:
            link = self._menu.getLinkByName(id)
            if link is not None:
                l.append(link)
        return l

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["logo"] = ""
        if self._conf.getLogo():
            vars["logo"] = "<img src=\"%s\" alt=\"%s\" border=\"0\" class=\"\" >"%(self._staticPars["logo"], self._conf.getTitle())
        vars["confTitle"] = self._conf.getTitle()
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        adjusted_sDate = self._conf.getAdjustedStartDate(tz)
        adjusted_eDate = self._conf.getAdjustedEndDate(tz)
        vars["confDateInterval"] = "from %s to %s"%(adjusted_sDate.strftime("%d %B %Y"), adjusted_eDate.strftime("%d %B %Y"))
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
           vars["confDateInterval"] = adjusted_sDate.strftime("%d %B %Y")
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
           vars["confDateInterval"] = "%s-%s %s"%(adjusted_sDate.day, adjusted_eDate.day, adjusted_sDate.strftime("%B %Y"))
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
        vars["body"] = self._body
        vars["supportEmail"] = ""
        if self._conf.hasSupportEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] = _("""<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email"> _("support")</a>""")%(mailto, self._staticPars["smallEmail"] )
        p=self._staticPars
        p["supportEmail"] = vars["supportEmail"]
        menuList = self._getMenuList(["overview", "programme", "timetable", "contributionList", "authorIndex", "abstractsBook"])
        vars["menu"] = ConfStaticDisplayMenu( self._menu, menuList ).getHTML(p)
        format = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
        vars["bgColorCode"] = format.getFormatOption("titleBgColor")["code"]
        vars["textColorCode"] = format.getFormatOption("titleTextColor")["code"]
        return vars

class WPConferenceStaticDisplay( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars

    def _getBody( self, params ):
        wc = WConfStaticDetails( self._getAW(), self._conf, self._staticPars )
        return wc.getHTML({})

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._overviewOpt)

class WConfStaticProgramTrack(wcomponents.WTemplated):

    def __init__( self, aw, track, staticPars ):
        self._aw = aw
        self._track = track
        self._staticPars=staticPars

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["bulletURL"] = self._staticPars["track_bullet"]
        vars["title"] = """%s """%(self._track.getTitle() )#"""<a href=%s>%s</a> """%(quoteattr(str(urlHandlers.UHStaticTrackContribList.getRelativeURL(self._track))), self._track.getTitle() )
        vars["description"] = self._track.getDescription()
        subtracks = []
        for subtrack in self._track.getSubTrackList():
            subtracks.append( "%s"%subtrack.getTitle() )
        vars["subtracks"] = ""
        if subtracks:
            vars["subtracks"] = _("""<i> _("Sub-tracks") </i>: %s""")%", ".join( subtracks )
        return vars

class WConfStaticProgram(wcomponents.WTemplated):

    def __init__(self, aw, conf, staticPars):
        self._conf = conf
        self._aw = aw
        self._staticPars = staticPars

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        program = []
        for track in self._conf.getTrackList():
            program.append( WConfStaticProgramTrack( self._aw, track, self._staticPars ).getHTML() )
        vars["program"] = "".join( program )
        return vars

class WPConferenceStaticProgram( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars

    def _getBody( self, params ):
        wc = WConfStaticProgram( self._getAW(), self._conf, self._staticPars )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._programOpt)

class WConfStaticAuthorIndex(wcomponents.WTemplated):

    def __init__(self,aw,conf, staticPars):
        self._aw=aw
        self._conf=conf
        self._staticPars=staticPars
        self._lastLetter = "-1"

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        track=contrib.getTrack()
        trackFolder="./other_contributions"
        if track is not None:
            trackFolder=track.getTitle().replace(" ","_")
        for mat in contrib.getAllMaterialList():
            url="%s/%s"%(trackFolder, str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat)))
            lm.append("""<a href=%s><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                    quoteattr(url),
                    self.htmlText(mat.getTitle().lower())))
        return ", ".join(lm)

    def _getLetterIndex(self):
        url=urlHandlers.UHStaticConfAuthorIndex.getRelativeURL()
        res=[]
        for letter in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']:
            res.append("""<a href="%s#letter_%s">%s</a>"""%(str(url),letter, letter))
        return " | ".join(res)

    def _getItemHTML(self,pl):
        if len(pl)<=0:
            return ""
        auth=pl[0]
        authCaption="%s"%auth.getFamilyName().upper()
        htmlLetter = ""
        letter = "-1"
        if len(auth.getFamilyName()) > 0:
            letter = auth.getFamilyName()[0].lower()
        if self._lastLetter != letter:
            self._lastLetter = letter
            htmlLetter = """<a href="" name="letter_%s"></a>"""%letter
        if auth.getFirstName()!="":
            authCaption="%s, %s"%(authCaption,auth.getFirstName())
        if authCaption.strip()=="":
            return ""
        contribList=[]
        for auth in pl:
            contrib=auth.getContribution()
            url=urlHandlers.UHStaticContributionDisplay.getRelativeURL(contrib)
            material = self._getMaterialHTML(contrib)
            if material.strip()!="":
                material = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;( %s )"%material
            contribList.append("""<p style="text-indent: -3em;margin-left:3em"><a href=%s>%s-%s</a>%s</p>"""%(quoteattr(str(url)), self.htmlText(contrib.getId()),self.htmlText(contrib.getTitle()), material ))
        res="""
            <tr>
                <td valign="top">%s%s</td>
                <td width="100%%">%s</td>
            </tr>
            <tr>
                <td colspan="2" style="border-bottom: 1px solid; border-color: #EAEAEA">&nbsp;</td>
            </tr>"""%(htmlLetter, self.htmlText(authCaption),"".join(contribList))
        return res

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        res=[]
        for partList in self._conf.getAuthorIndex().getParticipations():
            res.append(self._getItemHTML(partList))
        vars["letterIndex"] = self._getLetterIndex()
        vars["items"]="".join(res)
        return vars

class WPStaticAuthorIndex(WPConferenceStaticDefaultDisplayBase):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars

    def _getBody(self,params):
        wc=WConfStaticAuthorIndex(self._getAW(),self._conf,self._staticPars)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._authorIndexOpt)

class WConfStaticContributionList ( wcomponents.WTemplated ):

    def __init__( self, conf, trackDict ):
        self._conf = conf
        self._trackDict = trackDict

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        track=contrib.getTrack()
        trackFolder="./other_contributions"
        if track is not None:
            trackFolder=track.getTitle().replace(" ","_")
        for mat in contrib.getAllMaterialList():
            url="%s/%s"%(trackFolder, str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat)))
            lm.append("""<a href=%s><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                    quoteattr(url),
                    self.htmlText(mat.getTitle().lower())))
        return ", ".join(lm)

    def _getTrackHTML(self, track):
        return """
                    <tr><td colspan="5">&nbsp;</td></tr>
                    <tr>
                        <td class="groupTitle" colspan="5" style="background:#E5E5E5; color:gray">%s</td>
                    </tr>
                    <tr><td colspan="5">&nbsp;</td></tr>
                """%(track.getTitle())

    def _getContribHTML( self, contrib ):
        sdate = ""
        if contrib.isScheduled():
            sdate=contrib.getAdjustedStartDate().strftime("%d-%b-%Y %H:%M" )
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHStaticContributionDisplay.getRelativeURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        contribType = ""
        if contrib.getType() is not None:
            contribType = contrib.getType().getName()
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            if contrib.getSession().getCode() != "no code":
                session=self.htmlText(contrib.getSession().getCode())
            else:
                session=self.htmlText(contrib.getSession().getTitle())
        track = ""
        if contrib.getTrack() is not None:
            track = self.htmlText( contrib.getTrack().getCode() )
        html = """
            <tr>
                <td class="abstractLeftDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
            </tr>
                """%(title or "&nbsp;", speaker or "&nbsp;",
                    self._getMaterialHTML(contrib) or "&nbsp;",
                    contribType or "&nbsp;",
                    self.htmlText( contrib.getId() )
                    )
        return html

    def _cmpContribTitle(c1, c2):
        o1=c1.getTitle().lower().strip()
        o2=c2.getTitle().lower().strip()
        return cmp( o1, o2 )
    _cmpContribTitle=staticmethod(_cmpContribTitle)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        l = []
        #for track in self._conf.getTrackList():
        #    l.append(self._getTrackHTML(track))
        #    for contrib in self._trackDict[track.getId()]:
        #        l.append( self._getContribHTML( contrib ) )
        contList=self._conf.getContributionList()
        contList.sort(WConfStaticContributionList._cmpContribTitle)
        for contrib in contList:
            l.append( self._getContribHTML( contrib ) )
        vars["contributions"] = "".join(l)

        return vars

class WPStaticContributionList( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars, trackDict):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars
        self._trackDict = trackDict

    def _getBody( self, params ):
        wc = WConfStaticContributionList( self._conf, self._trackDict)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._contribListOpt)

class WPContributionStaticDisplay( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target.getConference())
        self._staticPars = staticPars
        self._contrib = target

    def _getBody( self, params ):
        wc=WContributionStaticDisplay( self._getAW(), self._contrib, self._staticPars )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._contribListOpt)

class WContributionStaticDisplay(wcomponents.WTemplated):

    def __init__(self, aw, contrib, staticPars):
        self._aw = aw
        self._contrib = contrib
        self._staticPars=staticPars

    def _getHTMLRow( self, title, body):
        if body.strip() == "":
            return ""
        str = """
                <tr>
                    <td align="right" valign="top" class="displayField" nowrap><b>%s:</b></td>
                    <td width="100%%">%s</td>
                </tr>"""%(title, body)
        return str

    def _getMaterialHTML(self):
        lm=[]
        paper=self._contrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(paper))),
                quoteattr(str(self._staticPars["paper"])),
                self.htmlText(materialFactories.PaperFactory().getTitle())))
        slides=self._contrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slides"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(slides))),
                quoteattr(str(self._staticPars["slides"])),
                self.htmlText(materialFactories.SlidesFactory().getTitle())))
        poster=self._contrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(poster))),
                quoteattr(str(self._staticPars["poster"])),
                self.htmlText(materialFactories.PosterFactory().getTitle())))
        video=self._contrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(video))),
                quoteattr(str(self._staticPars["video"])),
                self.htmlText(materialFactories.VideoFactory().getTitle())))
        iconURL=quoteattr(str(self._staticPars["material"]))
        minutes=self._contrib.getMinutes()
        if minutes is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="minutes"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(minutes))),
                iconURL,
                self.htmlText(materialFactories.MinutesFactory().getTitle())))
        iconURL=quoteattr(str(self._staticPars["material"]))
        for material in self._contrib.getMaterialList():
            url=urlHandlers.UHStaticMaterialDisplay.getRelativeURL(material)
            lm.append("""<a href=%s><img src=%s border="0" alt=""> %s</a>"""%(
                quoteattr(str(url)),iconURL,self.htmlText(material.getTitle())))
        return self._getHTMLRow("Material","<br>".join(lm))

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["title"] = self.htmlText(self._contrib.getTitle())
        vars["description"] = self._contrib.getDescription()
        vars["id"]=self.htmlText(self._contrib.getId())
        vars["startDate"] = _("""--_("not yet scheduled")--""")
        vars["startTime"] = ""
        if self._contrib.isScheduled():
            vars["startDate"]=self.htmlText(self._contrib.getAdjustedStartDate().strftime("%d-%b-%Y"))
            vars["startTime"]=self.htmlText(self._contrib.getAdjustedStartDate().strftime("%H:%M"))
        vars["location"]=""
        loc=self._contrib.getLocation()
        if loc is not None:
            vars["location"]="<i>%s</i>"%(self.htmlText(loc.getName()))
            if loc.getAddress() is not None and loc.getAddress()!="":
                vars["location"]="%s <pre>%s</pre>"%(vars["location"],loc.getAddress())
        room=self._contrib.getRoom()
        if room is not None:
            roomLink=linking.RoomLinker().getHTMLLink(room,loc)
            vars["location"]= _("""%s <small> _("Room"):</small> %s""")%(\
                vars["location"],roomLink)
        vars["location"]=self._getHTMLRow( _("Place"),vars["location"])
        l=[]
        for speaker in self._contrib.getSpeakerList():
            l.append(self.htmlText(speaker.getFullName()))
        vars["speakers"]=self._getHTMLRow( _("Presenters"),"<br>".join(l))

        pal = []
        for pa in self._contrib.getPrimaryAuthorList():
            authCaption="%s"%pa.getFullName()
            if pa.getAffiliation()!="":
                authCaption="%s (%s)"%(authCaption,pa.getAffiliation())
            pal.append(self.htmlText(authCaption))
        vars["primaryAuthors"]=self._getHTMLRow( _("Primary Authors"),"<br>".join(pal))
        cal = []
        for ca in self._contrib.getCoAuthorList():
            authCaption="%s"%ca.getFullName()
            if ca.getAffiliation()!="":
                authCaption="%s (%s)"%(authCaption,ca.getAffiliation())
            cal.append(self.htmlText(authCaption))
        vars["coAuthors"]=self._getHTMLRow( _("Co-Authors"),"<br>".join(cal))
        vars["contribType"]=""
        if self._contrib.getType() != None:
            vars["contribType"]=self._getHTMLRow( _("Contribution type"),self.htmlText(self._contrib.getType().getName()))
        vars["material"]=self._getMaterialHTML()
        vars["duration"]=""
        if self._contrib.getDuration() is not None:
            vars["duration"]=(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%M'")
            if (datetime(1900,1,1)+self._contrib.getDuration()).hour>0:
                vars["duration"]=(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%Hh%M'")
        vars["inTrack"]=""
        if self._contrib.getTrack():
            trackCaption=self._contrib.getTrack().getTitle()
            vars["inTrack"]="""%s"""%(self.htmlText(trackCaption))
        vars["inTrack"]=self._getHTMLRow( _("Included in track"),vars["inTrack"])
        return vars

class WMaterialStaticDisplay(wcomponents.WTemplated):

    def __init__(self, aw, material, staticPars):
        self._material=material
        self._aw=aw
        self._staticPars = staticPars

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars( self )
        if isinstance(self._material, conference.Paper):
            vars["icon"]=quoteattr(str(self._staticPars["paper"]))
        elif isinstance(self._material, conference.Slides):
            vars["icon"]=quoteattr(str(self._staticPars["slides"]))
        else:
            vars["icon"]=quoteattr(str(self._staticPars["material"]))
        vars["title"]=self._material.getTitle()
        vars["description"]=self._material.getDescription()
        rl = []
        for res in self._material.getResourceList():
            # TODO: remove the check "isinstance", it is only for CHEP04
            if isinstance(res ,conference.Link):# and not isinstance(self._material, conference.Video):
                rl.append("""<tr><td align="left">[LINK]</td><td width="100%%" align="left"><b>%s</b> <small>(<a href="%s">%s</a>)</small)</td></tr>"""%(res.getName(), res.getURL(), res.getURL()))
            else:
                rl.append("""
                    <tr>
                        <td align="left">&nbsp;</td>
                        <td width="100%%" align="left"><b>%s</b> <small>(<a href="%s/%s">%s</a> %s)</small></td>
                    </tr>"""%(res.getName(),
                                vars["rootDir"], vars["fileAccessURLGen"](res),
                                res.getFileName(),strfFileSize(res.getSize())))
        vars["resources"] = """
                    <table border="0" width="100%%" align="left">
                    %s
                    </table>"""%"".join(rl)
        return vars


class WPMaterialStaticDisplay( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, material, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, material.getConference())
        self._material=material
        self._staticPars = staticPars

    def _getBody( self, params ):
        wc = WMaterialStaticDisplay( self._getAW(), self._material, self._staticPars )
        pars = {"rootDir":".", "fileAccessURLGen": urlHandlers.UHStaticResourceDisplay.getRelativeURL }
        return wc.getHTML( pars )

class WTrackStaticContribList ( wcomponents.WTemplated ):

    def __init__( self, track, trackDict ):
        self._track = track
        self._conf = track.getConference()
        self._trackDict = trackDict

    def _getTrackHTML(self, track):
        return """
                    <tr><td colspan="5">&nbsp;</td></tr>
                    <tr>
                        <td class="groupTitle" colspan="5" style="background:#E5E5E5; color:gray">%s</td>
                    </tr>
                    <tr><td colspan="5">&nbsp;</td></tr>
                """%(track.getTitle())

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        track=contrib.getTrack()
        trackFolder="./other_contributions"
        if track is not None:
            trackFolder=track.getTitle().replace(" ","_")
        for mat in self._conf.getAllMaterialList():
            url="%s/%s"%(trackFolder, str(urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat)))
            lm.append("""<a href=%s><span style="font-style: italic;"><small> %s</small></span></a>"""%(
                    quoteattr(url),
                    self.htmlText(mat.getTitle().lower())))
        return ", ".join(lm)

    def _getContribHTML( self, contrib ):
        sdate = ""
        if contrib.isScheduled():
            sdate=contrib.getAdjustedStartDate().strftime("%d-%b-%Y %H:%M" )
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHStaticContributionDisplay.getRelativeURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        contribType = ""
        if contrib.getType() is not None:
            contribType = contrib.getType().getName()
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            if contrib.getSession().getCode() != "no code":
                session=self.htmlText(contrib.getSession().getCode())
            else:
                session=self.htmlText(contrib.getSession().getTitle())
        track = ""
        if contrib.getTrack() is not None:
            track = self.htmlText( contrib.getTrack().getCode() )
        html = """
            <tr>
                <td class="abstractLeftDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
                <td class="abstractDataCell">%s</td>
            </tr>
                """%(title or "&nbsp;", speaker or "&nbsp;",
                    self._getMaterialHTML(contrib) or "&nbsp;",
                    contribType or "&nbsp;",
                    self.htmlText( contrib.getId() )
                    )
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        l = []
        l.append(self._getTrackHTML(self._track))
        for contrib in self._trackDict[self._track.getId()]:
            l.append( self._getContribHTML( contrib ) )
        vars["contributions"] = "".join(l)

        return vars

class WPTrackStaticContribList( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars, trackDict):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target.getConference())
        self._staticPars = staticPars
        self._track = target
        self._trackDict = trackDict

    def _getBody( self, params ):
        wc = WTrackStaticContribList( self._track, self._trackDict)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._programOpt)

class WPStaticMeetingBase(WPConferenceStaticDefaultDisplayBase):

    def getRootDir(self, target):
        rootDir="."
        if not isinstance(target, conference.Conference):
            rootDir="%s/.."%rootDir
            owner=target.getOwner()
            while not isinstance(owner, conference.Conference):
                rootDir="%s/.."%rootDir
                owner=owner.getOwner()
        return rootDir

    def _getHTMLHeader( self ):
        path = Config.getInstance().getStylesheetsDir()
        # if a css file is associated with the XSL stylesheet, then we include it in the header
        styleText = """<link rel="stylesheet" href="%s/css/%s">
                       <link rel="stylesheet" href="%s/css/common.css">""" % \
                    (self.getRootDir(self._target), Config.getInstance().getCssStylesheetName(), self.getRootDir(self._target))
        try:
            if os.path.exists("%s/%s.css" % (path,self._view)):
                styleText += """
                     <style type="text/css">
                        %s
                     </style>""" % open("%s/%s.css" % (path,self._view),"r").read()
        except AttributeError, e:
            pass
        return """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
    <html>
        <head>
            <title>%s</title>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <link rel="shortcut icon" href=%s>
            %s
        </head>
        <body>"""%(self._getTitle(),
                    quoteattr(self._staticPars["addressBarIcon"]),
                    styleText)

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WStaticWebHeader()
        params = {}
        params["imgLogo"] = self._staticPars["miniLogo"]
        return wc.getHTML( params )

    def _applyConfDisplayDecoration( self, body ):
        return body


class WPXSLMeetingStaticDisplay( WPStaticMeetingBase ):

    def __init__(self, rh, target, staticPars):
        WPStaticMeetingBase.__init__(self, rh, target.getConference())
        self._view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(target.getConference()).getDefaultStyle()
        if self._view =="static":
            self._view="standard"
        self._type = "meeting"
        self._params={}
        self._params["showDate"] = "all"
        self._params["showSession"] = "all"
        self._params["detailLevel"] = "contribution"
        self._conf = self._target=target
        self._parentCateg = None
        categId = rh._getSession().getVar("currentCategoryId")
        if categId != None:
            self._parentCateg = self._conf.getOwnerById(categId)
        self._staticPars = staticPars

    def _getBody( self, params ):
        pars = { \
    "modifyURL": "", \
        "minutesURL":  "", \
        "materialURL":  "", \
        "cloneURL": "", \
    "sessionModifyURLGen": "", \
    "contribModifyURLGen": "", \
        "contribMinutesURLGen": "", \
        "contribMaterialURLGen": "", \
        "subContribMaterialURLGen": "", \
        "sessionMinutesURLGen": "", \
        "sessionMaterialURLGen": "", \
        "subContribMinutesURLGen": "", \
    "subContribModifyURLGen":  "", \
    "materialURLGen": urlHandlers.UHMStaticMaterialDisplay.getRelativeURL, \
    "resourceURLGen": urlHandlers.UHMStaticResourceDisplay.getRelativeURL}
        view = self._view
        from MaKaC.accessControl import AccessWrapper
        outGen = outputGenerator(AccessWrapper())
        path = Config.getInstance().getStylesheetsDir()
        if os.path.exists("%s/%s.xsl" % (path,view)):
            stylepath = "%s/%s.xsl" % (path,view)
            if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                includeContribution = 1
            else:
                includeContribution = 0
            return outGen.getFormattedOutput(self._conf,stylepath,pars,1,includeContribution,1,self._params.get("showSession",""),self._params.get("showDate",""))
        else:
            return "Cannot find the %s stylesheet" % view

class WPMMaterialStaticDisplay( WPStaticMeetingBase ):

    def __init__(self, rh, material, staticPars):
            WPStaticMeetingBase.__init__(self, rh, material.getConference())
            self._material=self._target=material
            self._staticPars = staticPars

    def _applyConfDisplayDecoration( self, body ):
        from MaKaC.webinterface.meeting import WMConfDisplayFrame
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
        urlIndex=str(urlHandlers.UHStaticConferenceDisplay.getRelativeURL())
        urlIndex="%s/%s"%(self.getRootDir(self._material), urlIndex)
        body = _("""
                <div class="confBodyBox clearfix" %s %s>
                    %s
                    <table border="0" cellpadding="0" cellspacing="0"
                                align="center" valign="top" width="95%%">
                        <tr>
                            <td class="formTitle" width="100%%"> _("Added Material") - %s</td>
                        </tr>
                        <tr>
                            <td align="left" valign="middle" width="100%%">
                                <b><br><a href=%s> _("Home")</a></b>
                            </td>
                       </tr>
                    </table>
                     <!--Main body-->
                    %s
                </div>""")%(colspan,padding,imgOpen, confTitle,
                        quoteattr(urlIndex),
                        body)
        return frame.getHTML( body, frameParams)

    def _getBody( self, params ):
            wc = WMaterialStaticDisplay( self._getAW(), self._material, self._staticPars )
            pars = { "rootDir":self.getRootDir(self._material), "fileAccessURLGen": urlHandlers.UHMStaticResourceDisplay.getRelativeURL }
            return wc.getHTML( pars )


class WConferenceStaticTimeTable(wcomponents.WTemplated):

    def __init__( self, timeTable, conference, aw ):
        self._aw = aw
        self._timeTable = timeTable
        self._conf = conference
        self._sessionColorMap = {}

    def _getRandomColor( self, color=1 ):
        if color==0:
            r=g=b = random.randint(130,255)
        else:
            r = random.randint(130,255)
            g = random.randint(130,255)
            b = random.randint(130,255)
        return "#%X%X%X"%(r,g,b)

    def _generateColor( self, color=1, colorMap={} ):
        """
        This function generates a color which does not already exist in the passed colormap
        params:
            color: indicates whether the returned color should be gray-level or colored
            colormap: returned color must not be in this dict.
        """
        color = self._getRandomColor(color)
        while(color in colorMap.values()):
            color = self._getRandomColor(color)
        return color

    def _getSessionColor( self, session ):
        if session.getId() not in self._sessionColorMap.keys():
            color = session.getColor()
            # if color=="#F0C060" and color in self._sessionColorMap.values():
               # color = self._generateColor(1,self._sessionColorMap)
            self._sessionColorMap[session.getId()] = color
        return self._sessionColorMap[session.getId()]

    def _getColor( self, entry ):
        bgcolor = "#E6E6E6"
        if isinstance(entry, schedule.LinkedTimeSchEntry) and \
                      isinstance(entry.getOwner(), conference.SessionSlot):
            bgcolor = self._getSessionColor( entry.getOwner().getSession() )
        elif isinstance(entry, schedule.LinkedTimeSchEntry) and \
                  isinstance(entry.getOwner(), conference.Contribution):
            contrib = entry.getOwner()
            if contrib.getSession():
                bgcolor = self._getSessionColor( contrib.getSession() )
            else:
                bgcolor = "#F6F6F6"
        elif isinstance(entry, schedule.BreakTimeSchEntry):
            owner = entry.getSchedule().getOwner()
            if isinstance(owner,conference.Session):
                bgcolor = self._getSessionColor( owner )
            else:
                bgcolor = "#90C0F0"
                if entry.getColor()!="":
                    bgcolor=entry.getColor()
        return bgcolor

    def _getTextColor( self, entry ):
        textcolor = "#777777"
        if isinstance(entry, schedule.LinkedTimeSchEntry) and \
                      isinstance(entry.getOwner(), conference.SessionSlot):
            textcolor = entry.getOwner().getSession().getTextColor()
        elif isinstance(entry, schedule.LinkedTimeSchEntry) and \
                  isinstance(entry.getOwner(), conference.Contribution):
            contrib = entry.getOwner()
            if contrib.getSession():
                textcolor = contrib.getSession().getTextColor()
        elif isinstance(entry, schedule.BreakTimeSchEntry):
            owner = entry.getSchedule().getOwner()
            if isinstance(owner,conference.Session):
                textcolor = owner.getTextColor()
            else:
                if entry.getTextColor()!="":
                    textcolor=entry.getTextColor()
        return textcolor

    def _getContributionHTML( self, contribution, URL ):
        room = ""
        if contribution.getRoom() != None:
            room = "%s: "%contribution.getRoom().getName()
        speakerList = []
        for spk in contribution.getSpeakerList():
            spkcapt=spk.getFullName()
            if spk.getAffiliation().strip() != "":
                spkcapt="%s (%s)"%(spkcapt, spk.getAffiliation())
            speakerList.append(spkcapt)
        speakers =""
        if speakerList != []:
            speakers = "<br><small>by %s</small>"%"; ".join(speakerList)
        linkColor=""
        if contribution.getSession() is not None:
            if contribution.getSession().isTextColorToLinks():
                linkColor="color:%s"%contribution.getSession().getTextColor()
        return """<table width="100%%">
                        <tr>
                            <td width="100%%" align="center" style="%s">
                                [%s] <a href="%s" style="%s">%s</a>%s<br><small>(%s%s - %s)</small>
                            </td>
                        </tr>
                    </table>"""%(linkColor, self.htmlText(contribution.getId()),URL, linkColor,
                                self.htmlText(contribution.getTitle()),
                                speakers, room,
                                contribution.getAdjustedStartDate().strftime("%H:%M"),
                                contribution.getAdjustedEndDate().strftime("%H:%M") )

    def _getSessionHTML( self, session, URL, refDay ):
        room = ""
        if session.getRoom() != None:
            room = "%s: "%session.getRoom().getName()
        #################################
        # Fermi timezone awareness        #
        #################################
        sDate = session.getAdjustedStartDate()
        eDate = session.getAdjustedEndDate()
        timeInterval = "<br>(%s%s - %s)"%(room, \
                                    sDate.strftime("%H:%M"), \
                                    eDate.strftime("%H:%M") )
        if session.getAdjustedStartDate().strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
            if session.getAdjustedEndDate().strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
                timeInterval = ""
            else:
                timeInterval = _("""<br>(%s_("until") %s)""")%(room, eDate.strftime("%H:%M"))
        else:
            if session.getAdjustedEndDate().strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
                timeInterval = _("""<br>(%s_("from") %s)""")%(room, sDate.strftime("%H:%M"))

        #################################
        # Fermi timezone awareness(end)   #
        #################################
        conveners=""
        l=[]
        for conv in session.getConvenerList():
            l.append("""%s"""%(self.htmlText(conv.getDirectFullName())))
        if len(l)>0:
            conveners= _("""<br><small> _("Conveners"): %s</small>""")%"; ".join(l)
        title = self.htmlText(session.getSession().getTitle())
        if session.getTitle().strip() != "":
            title = "%s: %s"%(title, session.getTitle())
        linkColor=""
        if session.getSession().isTextColorToLinks():
            linkColor="color:%s"%session.getSession().getTextColor()
        return """<a href="%s" style="%s">%s</a>%s<small>%s</small>"""%(URL, linkColor,\
                                title, conveners, timeInterval )

    def _getBreakHTML( self, breakEntry ):
        room = ""
        if breakEntry.getRoom() != None:
            room = "%s: "%breakEntry.getRoom().getName()

        ################################
        # Fermi timezone awareness       #
        ################################
        sDate = breakEntry.getAdjustedStartDate()
        eDate = breakEntry.getAdjustedEndDate()
        return """<b>%s</b><br><small>(%s%s - %s)</small>"""%( breakEntry.getTitle(),\
                                room, \
                                sDate.strftime("%H:%M"),\
                                eDate.strftime("%H:%M") )
        ################################
        # Fermi timezone awareness(end)  #
        ################################

    def _getEntryHTML(self,entry,refDay):
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.SessionSlot):
                return self._getSessionHTML(entry.getOwner(),self._sessionURLGen(entry.getOwner().getSession()),refDay)
            if isinstance(entry.getOwner(), conference.Contribution):
                return self._getContributionHTML(entry.getOwner(), \
                                                self._contribURLGen(entry.getOwner()))
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            return self._getBreakHTML(entry)

    def _getColorLegendItemHTML( self, color, descrip ):
        str = """   <span height="10px" width="20px" style="background:%s; border:1px solid black;font-size: 10px;">&nbsp;&nbsp;</span>
                    <span align="left" style="font-size: 10px;">%s</span>
                """%(color, descrip)
        return str

    def _getColorLegendHTML( self ):
        html = """<table bgcolor="white" cellpadding="0" cellspacing="1" width="100%%" style="padding:3px; border-top:1px solid #E6E6E6;border-bottom:1px solid #E6E6E6;">
                    <tr>
                        <td bgcolor="white" width="100%%" align="center">
                            &nbsp;
                            %s
                        </td>
                    </tr>
                  </table>
                """
        l = []
        l.append( self._getColorLegendItemHTML( "#90C0F0", _("Conference break")) )
        l.append( self._getColorLegendItemHTML( "#F6F6F6", _("Conference contribution")) )
        for sessionId in self._sessionColorMap.keys():
            session = self._conf.getSessionById( sessionId )
            str = self._getColorLegendItemHTML(\
                                    self._sessionColorMap[ sessionId ],\
                                    _(""" _("Session"): <i>%s </i>""")%session.getTitle())
            l.append( str )
        return html%" - ".join( l )

    def _getHTMLTimeTable( self, highDetailLevel=0 ):
        self._sessionColorMap = {}
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/self._timeTable.getSlotLength().seconds)
        for day in self._timeTable.getDayList():
            self._sessionColorMap.clear()
            emptyDay=True
            slotList=[]
            lastEntries=[]
            maxOverlap=day.getNumMaxOverlaping()
            width="100"
            if maxOverlap!=0:
                width=100/maxOverlap
            else:
                maxOverlap=1
            for hour in range(day.getStartHour(),day.getEndHour()+1):
                hourSlots=[]
                emptyHour = True
                for slot in day.getSlotsOnHour(hour):
                    remColSpan=maxOverlap
                    temp=[]
                    entryList=slot.getEntryList()
                    entryList.sort(timetable.sortEntries)
                    for entry in entryList:
                        emptyHour = False
                        emptyDay = False
                        if len(slot.getEntryList()):
                            remColSpan=0
                        else:
                            remColSpan-=1
                        if entry in lastEntries:
                            continue
                        bgcolor=self._getColor(entry)
                        textcolor=self._getTextColor(entry)
                        colspan=""
                        if not day.hasEntryOverlaps(entry):
                            colspan=""" colspan="%s" """%maxOverlap
                        temp.append("""<td valign="top" rowspan="%i" align="center" bgcolor="%s" width="%i%%"%s><font color="%s">%s</font></td>"""%(day.getNumSlots(entry),bgcolor, width, colspan, textcolor, self._getEntryHTML(entry,day)))
                        lastEntries.append(entry)
                    if remColSpan>0:
                        temp.append("""<td width="100%%" colspan="%i"></td>"""%(remColSpan))
                    if slot.getAdjustedStartDate().minute==0:
                        hourSlots.append("""
                            <tr>
                                <td valign="top" rowspan="%s" bgcolor="white"  width="10" style="padding-right: 5px;"><font color="gray" size="-1">%02i:00</font></td>
                                %s
                            </tr>
                            """%(num_slots_in_hour,\
                                    hour,\
                                    "".join(temp)))
                    else:
                        if len(temp) == 0:
                            temp = ["<td></td>"]
                        hourSlots.append("""<tr>%s</tr>"""%"".join(temp))
                if emptyHour:
                    slotList.append("""
                <tr>
                    <td valign="top" bgcolor="white"  width="10" style="padding-right: 5px;"><font color="gray" size="-1">%02i:00</font></td>
                    <td>&nbsp;</td>
                </tr>""" % hour)
                else:
                    slotList.append("".join(hourSlots))
            legend=""
            if highDetailLevel:
                legend=self._getColorLegendHTML()
            if not emptyDay:
                str="""
                    <table align="center" width="100%%">
                        <tr>
                            <td width="100%%">
                                <table align="center" border="0" width="100%%"
                                        celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                                    <tr>
                                        <td colspan="%i" align="center" bgcolor="white"><b>%s</b></td>
                                    </tr>
                                    <tr>
                                        <td colspan="%i">%s</td>
                                    </tr>
                                    %s
                                </table>
                            </td>
                        </tr>
                    </table>
                    """%(maxOverlap+2,\
                            day.getDate().strftime("%A, %d %B %Y"), \
                            maxOverlap+2, legend, \
                            "".join(slotList) )
                daySch.append(str)
        str = "<br>".join( daySch )
        return str

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        self._contribURLGen = vars["contribURLGen"]
        self._sessionURLGen = vars["sessionURLGen"]
        vars["timetable"] = self._getHTMLTimeTable(vars.get("detailLevel", "") == "contribution")
        return vars



class WPConferenceStaticTimeTable( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars

    def _getEntryList(self):
        lsessions = self._conf.getSchedule().getEntries()
        res = []
        for entry in lsessions:
            if isinstance(entry,schedule.LinkedTimeSchEntry):
                owner = entry.getOwner()
                if isinstance(owner, conference.SessionSlot):
                    if owner.canAccess(self._getAW()):
                            res.append( entry )
                    elif owner.canView(self._getAW()):
                        if isinstance(owner,conference.SessionSlot):
                            slot=owner
                            for slotEntry in slot.getSchedule().getEntries():
                                if isinstance(slotEntry.getOwner(),conference.Contribution):
                                    if slotEntry.getOwner().canAccess(self._getAW()):
                                            res.append(slotEntry)
                else:
                    if owner.canAccess(self._getAW()):
                        res.append( entry )
            else:
                res.append( entry )
        return res

    def _getParallelTimeTable( self, params ):
        tz = DisplayTZ(self._getAW(),self._conf).getDisplayTZ()
        tt = timetable.TimeTable( self._conf.getSchedule(), tz )
        #####################################
        # Fermi timezone awareness            #
        #####################################
        sDate = self._conf.getSchedule().getStartDate(tz)
        eDate = self._conf.getSchedule().getEndDate(tz)
        #####################################
        # Fermi timezone awareness(end)       #
        #####################################
        tt.setStartDate( sDate )
        tt.setEndDate( eDate )
        tt.mapEntryList(self._getEntryList())
        return tt

    def _getBody( self, params ):
        tt = self._getParallelTimeTable( params )
        wc = WConferenceStaticTimeTable( tt, self._conf, self._getAW()  )
        pars = {"contribURLGen": urlHandlers.UHStaticContributionDisplay.getRelativeURL, \
                "sessionURLGen": urlHandlers.UHStaticSessionDisplay.getRelativeURL }
        return wc.getHTML( pars )

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._timetableOpt)

class WSessionStaticDisplay(wcomponents.WTemplated):

    def __init__(self,aw,session):
        self._aw=aw
        self._session=session

    def _getHTMLRow(self,title,body):
        str = """
                <tr>
                    <td nowrap class="displayField" valign="top"><b>%s:</b></td>
                    <td>%s</td>
                </tr>"""%(title,body)
        if body.strip() == "":
            return ""
        return str

    def _getColor(self,entry):
        bgcolor = "white"
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.Contribution):
                bgcolor = entry.getOwner().getSession().getColor()
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            bgcolor = entry.getColor()
        return bgcolor

    def _getContributionHTML(self,contrib):
        URL=urlHandlers.UHStaticContributionDisplay.getRelativeURL(contrib, "..")
        room = ""
        if contrib.getRoom() != None:
            room = "%s: "%contrib.getRoom().getName()
        speakerList = []
        for spk in contrib.getSpeakerList():
            speakerList.append(spk.getDirectFullName())
        speakers =""
        if speakerList != []:
            speakers = _("""<br><small> _("by") %s</small>""")%"; ".join(speakerList)
        linkColor=""
        if contrib.getSession().isTextColorToLinks():
            linkColor="color:%s"%contrib.getSession().getTextColor()
        return """<table width="100%%">
                        <tr>
                            <td width="100%%" align="center" style="color:%s">
                                [%s] <a href="%s" style="%s">%s</a>%s<br><small>(%s%s - %s)</small>
                            </td>
                        </tr>
                    </table>"""%(
                contrib.getSession().getTextColor(),contrib.getId(),URL,\
                linkColor, contrib.getTitle(),speakers,room,
                contrib.getAdjustedStartDate().strftime("%H:%M"),
                contrib.getAdjustedEndDate().strftime("%H:%M") )

    def _getBreakHTML(self,breakEntry):
        return """
                <font color="%s">%s<br><small>(%s - %s)</small></font>
                """%(\
                    breakEntry.getTextColor(),\
                    self.htmlText(breakEntry.getTitle()),\
                    self.htmlText(breakEntry.getAdjustedStartDate().strftime("%H:%M")),\
                    self.htmlText(breakEntry.getAdjustedEndDate().strftime("%H:%M")))

    def _getSchEntries(self):
        res=[]
        for slot in self._session.getSlotList():
            for entry in slot.getSchedule().getEntries():
                res.append(entry)
        return res

    def _getEntryHTML(self,entry):
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.Contribution):
                return self._getContributionHTML(entry.getOwner())
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            return self._getBreakHTML(entry)

    def _getTimeTableHTML(self):
        tz = DisplayTZ(self._aw,self._session.getConference()).getDisplayTZ()
        timeTable=timetable.TimeTable(self._session.getSchedule(), tz)
        sDate,eDate=self._session.getAdjustedStartDate(tz),self._session.getAdjustedEndDate(tz)
        timeTable.setStartDate(sDate)
        timeTable.setEndDate(eDate)
        timeTable.mapEntryList(self._getSchEntries())
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/timeTable.getSlotLength().seconds)
        hourSlots,hourNeedsDisplay=[],False
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
                if slot.getAdjustedStartDate().minute==0:
                    if hourNeedsDisplay:
                        slotList.append("".join(hourSlots))
                    hourSlots,hourNeedsDisplay=[],False
                remColSpan=maxOverlap
                temp=[]
                for entry in slot.getEntryList():
                    hourNeedsDisplay=True
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
                if slot.getAdjustedStartDate().minute==0:
                    str="""
                        <tr>
                            <td valign="top" rowspan="%s" bgcolor="white" width="40"><font color="gray" size="-1">%s</font></td>
                            %s
                        </tr>
                        """%(num_slots_in_hour,\
                                slot.getAdjustedStartDate().strftime("%H:%M"),\
                                "".join(temp))
                else:
                    if len(temp) == 0:
                        temp = ["<td></td>"]
                    str = """<tr>%s</tr>"""%"".join(temp)
                hourSlots.append(str)
            str="""
                <a name="%s">
                <table align="center" width="100%%">
                    <tr>
                        <td width="100%%">
                            <table align="center" border="0" width="100%%"
                                    celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                                <tr>
                                    <td colspan="%i" align="center" bgcolor="white"><b>%s</b></td>
                                </tr>
                                %s
                            </table>
                        </td>
                    </tr>
                </table>
                """%(day.getDate().strftime("%Y-%m-%d"),maxOverlap+2,
                        day.getDate().strftime("%A, %d %B %Y"),
                        "".join(slotList) )
            daySch.append(str)
        str = "<br>".join( daySch )
        return str

    def getVars(self):
        vars=wcomponents.WTemplated.getVars( self )

        vars["title"]=self.htmlText(self._session.getTitle())

        if self._session.getDescription():
            desc = self._session.getDescription().strip()
        else:
            desc = ""

        if desc!="":
            vars["description"]="""
                <tr>
                    <td colspan="2">%s</td>
                </tr>
                                """%desc
        else:
            vars["description"] = ""

        #################################
        # Fermi timezone awareness      #
        #################################
        sDate=self._session.getAdjustedStartDate()
        eDate=self._session.getAdjustedEndDate()
        if sDate.strftime("%d%b%Y")==eDate.strftime("%d%b%Y"):
            vars["dateInterval"]=sDate.strftime("%A %d %B %Y %H:%M")
        else:
            vars["dateInterval"]="from %s to %s"%(
                sDate.strftime("%A %d %B %Y %H:%M"),
                eDate.strftime("%A %d %B %Y %H:%M"))
        #################################
        # Fermi timezone awareness(end) #
        #################################

        vars["location"]=""
        loc=self._session.getLocation()
        if loc is not None and loc.getName().strip()!="":
            vars["location"]="""<i>%s</i>"""%self.htmlText(loc.getName())
            if loc.getAddress().strip()!="":
                vars["location"]="""%s<pre>%s</pre>"""%(vars["location"],
                                                        loc.getAddress())
        room = self._session.getRoom()
        if room is not None:
            roomLink=linking.RoomLinker().getHTMLLink(room,loc)
            vars["location"]= _("""%s<br><small> _("Room"):</small> %s""")%(vars["location"],
                                                            roomLink)
        vars["location"]=self._getHTMLRow("Place", vars["location"])

        sessionConvs=[]
        for convener in self._session.getConvenerList():
            sessionConvs.append("""<a href="mailto:%s">%s</a>"""%(convener.getEmail(),
                                        self.htmlText(convener.getFullName())))
        slotConvsHTML=""
        for entry in self._session.getSchedule().getEntries():
            slot=entry.getOwner()
            l=[]
            for convener in slot.getOwnConvenerList():
                l.append("""<a href="mailto:%s">%s</a>"""%(convener.getEmail(),
                                        self.htmlText(convener.getFullName())))
            if len(l)>0:
                slotConvsHTML+="""
                    <tr>
                        <td valign="top">%s (<small>%s-%s</small>):</td>
                        <td>%s</td>
                    </tr>
                      """%(self.htmlText(slot.getTitle()),
                      slot.getAdjustedStartDate().strftime("%d-%b-%y %H:%M"),
                      slot.getAdjustedEndDate().strftime("%d-%b-%y %H:%M"),
                      "; ".join(l))
        convs=""
        if len(sessionConvs)>0 or slotConvsHTML.strip()!="":
            convs="""
                <table>
                    <tr>
                        <td valign="top" colspan="2">%s</td>
                    </tr>
                    %s
                </table>"""%("<br>".join(sessionConvs),slotConvsHTML)
        vars["conveners"]=self._getHTMLRow( _("Conveners"),convs)
        lm = []
        for material in self._session.getAllMaterialList():
            url=urlHandlers.UHStaticMaterialDisplay.getRelativeURL(material)
            lm.append(wcomponents.WMaterialDisplayItem().getHTML(self._aw,material,url))
        vars["material"] = self._getHTMLRow( _("Material"), "<br>".join( lm ) )
        vars["contribs"]= ""
        if self._session.getContributionList() != []:
            vars["contribs"]=self._getTimeTableHTML()
        return vars

class WPSessionStaticDisplay( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target.getConference())
        self._session=target
        self._staticPars = staticPars

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._timetableOpt)

    def _getBody(self,params):
        wc=WSessionStaticDisplay(self._getAW(),self._session)
        return wc.getHTML()

#------------------------ End Static ---------------------------------------------------------------

class WDVDDone( wcomponents.WTemplated ):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["supportAddr"]=info.HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
        return vars

class WPDVDDone( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabOfflineSite.setActive()

    def _getTabContent( self, params ):
        w = WDVDDone()
        p={}
        p["url"]=quoteattr(str(params.get("url")))
        return w.getHTML(p)

class WPConfModifDVDCreationConfirm( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabOfflineSite.setActive()

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg="""<br>Please confirm that you want to create an "Offline Website" for your event<br>
        <font color="red">(note if you confirm you cannot stop the creation of the website )</font><br>"""
        url=urlHandlers.UHConfDVDCreation.getURL(self._conf)
        return wc.getHTML(msg,url,{})

class WTimeTableCustomizePDF(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        url=urlHandlers.UHConfTimeTablePDF.getURL(self._conf)
        vars["getPDFURL"]=quoteattr(str(url))

        wc = WConfCommonPDFOptions(self._conf)
        vars["commonPDFOptions"] = wc.getHTML()

        return vars


class WPTimeTableCustomizePDF( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NETimeTableCustomizePDF

    def _getBody( self, params ):
        wc = WTimeTableCustomizePDF( self._conf )
        return wc.getHTML(params)

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._timetableOpt)


class WConfModifPendingQueuesList ( wcomponents.WTemplated ):

    def __init__(self, url, title, target, list, pType) :
        self._postURL = url;
        self._title = title;
        self._target = target
        self._list = list
        self._pType = pType

    def _cmpByContribName(self, cp1, cp2):
        if cp1 is None and cp2 is not None:
            return -1
        elif cp1 is not None and cp2 is None:
            return 1
        elif cp1 is None and cp2 is None:
            return 0
        return cmp(cp1.getContribution().getTitle(), cp2.getContribution().getTitle())

    def _cmpBySessionName(self, cp1, cp2):
        if cp1 is None and cp2 is not None:
            return -1
        elif cp1 is not None and cp2 is None:
            return 1
        elif cp1 is None and cp2 is None:
            return 0
        return cmp(cp1.getSession().getTitle(), cp2.getSession().getTitle())

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["postURL"] = self._postURL
        vars["title"] = self._title
        vars["target"] = self._target
        vars["list"] = self._list
        vars["pType"] = self._pType

        return vars

class WConfModifPendingQueues( wcomponents.WTemplated ):

    def __init__(self, conf, aw, activeTab="submitters"):
        self._conf = conf
        self._aw = aw
        self._activeTab=activeTab
        self._pendingSubmitters=self._conf.getPendingQueuesMgr().getPendingSubmitters()
        self._pendingManagers=self._conf.getPendingQueuesMgr().getPendingManagers()
        self._pendingCoordinators=self._conf.getPendingQueuesMgr().getPendingCoordinators()

    def _createTabCtrl( self ):
        self._tabCtrl=wcomponents.TabControl()
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","submitters")
        self._tabSubmitters=self._tabCtrl.newTab("submitters", \
                                                _("Pending Submitters"),str(url))
        url.addParam("tab","managers")
        self._tabManagers=self._tabCtrl.newTab("managers", \
                                                _("Pending Managers"),str(url))
        url.addParam("tab","coordinators")
        self._tabCoordinators=self._tabCtrl.newTab("coordinators", \
                                                _("Pending Coordinators"),str(url))
        self._tabSubmitters.setEnabled(True)
        tab=self._tabCtrl.getTabById(self._activeTab)
        if tab is None:
            tab=self._tabCtrl.getTabById("submitters")
        tab.setActive()


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        self._createTabCtrl()
        list=[]
        url=""
        title=""

        if self._tabSubmitters.isActive():
            # Pending submitters
            keys = self._conf.getPendingQueuesMgr().getPendingSubmittersKeys(True)

            url=urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
            url.addParam("tab","submitters")
            title= _("Pending authors/speakers to become submitters")
            target= _("Contribution")
            pType=_("Submitters")

            for key in keys:
                list.append((key, self._pendingSubmitters[key][:]))
                list.sort(conference.ContributionParticipation._cmpFamilyName)

        elif self._tabManagers.isActive():
            # Pending managers
            keys = self._conf.getPendingQueuesMgr().getPendingManagersKeys(True)

            url=urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
            url.addParam("tab","managers")
            title= _("Pending conveners to become managers")
            target= _("Session")
            pType="Managers"

            for key in keys:
                list.append((key, self._pendingManagers[key][:]))
                list.sort(conference.SessionChair._cmpFamilyName)

        elif self._tabCoordinators.isActive():
            # Pending coordinators
            keys = self._conf.getPendingQueuesMgr().getPendingCoordinatorsKeys(True)

            url=urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
            url.addParam("tab","coordinators")
            title= _("Pending conveners to become coordinators")
            target= _("Session")
            pType="Coordinators"

            for key in keys:
                list.append((key, self._pendingCoordinators[key][:]))
                list.sort(conference.SessionCoordinator._cmpFamilyName)

        html = WConfModifPendingQueuesList(str(url), title, target, list, pType).getHTML()
        vars["pendingQueue"]=wcomponents.WTabControl(self._tabCtrl, self._aw).getHTML(html)
        vars["backURL"]=quoteattr(str(urlHandlers.UHConfModifListings.getURL(self._conf)))

        return vars

class WPConfModifPendingQueuesBase( WPConferenceModifBase ):

    def __init__(self, rh, conf, activeTab=""):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._activeTab=activeTab

    def _getPageContent(self, params):
        banner = wcomponents.WListingsBannerModif(self._conf).getHTML()
        return banner+self._getTabContent( params )

    def _setActiveSideMenuItem(self):
        self._listingsMenuItem.setActive(True)

class WPConfModifPendingQueues( WPConfModifPendingQueuesBase ):

    def _getTabContent( self, params ):
        wc = WConfModifPendingQueues( self._conf, self._getAW(), self._activeTab )
        return wc.getHTML()

class WPConfModifPendingQueuesRemoveSubmConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingSubms):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingSubms = pendingSubms

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        pss=[]
        for i in self._pendingSubms:
           pss.append("""<li>%s</li>"""%i)
        msg= _(""" _("Are you sure you want to delete the following participants pending to become submitters")?<br>
        <ul>
        %s
        </ul>
        <font color="red">( _("note they will not become submitters of their contributions but you will still keep them as participants"))</font><br>""")%"".join(pss)
        url=urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingSubmitters":self._pendingSubms, "remove": _("remove")})

class WPConfModifPendingQueuesReminderSubmConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingSubms):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingSubms = pendingSubms

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        pss=[]
        for i in self._pendingSubms:
           pss.append("""<li>%s</li>"""%i)
        msg= _(""" _("Please confirm that you want to send an email with the reminder to create an account in Indico")?<br><br> _("The email will be sent to"):<br>
        <ul>
        %s
        </ul>
        <br>""")%"".join(pss)
        url=urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingSubmitters":self._pendingSubms, "reminder": _("reminder")})

class WPConfModifPendingQueuesRemoveMgrConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingMgrs):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingMgrs = pendingMgrs

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        pss=[]
        for i in self._pendingMgrs:
           pss.append("""<li>%s</li>"""%i)
        msg= _(""" _("Are you sure you want to delete the following conveners pending to become managers")?<br>
        <ul>
        %s
        </ul>
        <font color="red">( _("note they will not become managers of their sessions but you will still keep them as coveners"))</font><br>""")%"".join(pss)
        url=urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingManagers":self._pendingMgrs, "remove": _("remove")})

class WPConfModifPendingQueuesReminderMgrConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingMgrs):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingMgrs = pendingMgrs

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        pss=[]
        for i in self._pendingMgrs:
           pss.append("""<li>%s</li>"""%i)
        msg= _(""" _("Please confirm that you want to send an email with the reminder to create an account in Indico")?<br><br> _("The email will be sent to"):<br>
        <ul>
        %s
        </ul>
        <br>""")%"".join(pss)
        url=urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingManagers":self._pendingMgrs, "reminder": _("reminder")})

class WPConfModifPendingQueuesRemoveCoordConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingCoords):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingCoords = pendingCoords

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        pss=[]
        for i in self._pendingCoords:
           pss.append("""<li>%s</li>"""%i)
        msg= _(""" _("Are you sure you want to delete the following conveners pending to become coordinators")?<br>
        <ul>
        %s
        </ul>
        <font color="red">( _("note they will not become coordinators of their sessions but you will still keep them as coveners"))</font><br>""")%"".join(pss)
        url=urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingCoordinators":self._pendingCoords, "remove": _("remove")})

class WPConfModifPendingQueuesReminderCoordConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingCoords):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingCoords = pendingCoords

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        pss=[]
        for i in self._pendingCoords:
           pss.append("""<li>%s</li>"""%i)
        msg= _(""" _("Please confirm that you want to send an email with the reminder to create an account in Indico")?<br><br> _("The email will be sent to"):<br>
        <ul>
        %s
        </ul>
        <br>""")%"".join(pss)
        url=urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingCoordinators":self._pendingCoords, "reminder": _("reminder")})

class WAbstractBookCustomise(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        url=urlHandlers.UHConfAbstractBookPerform.getURL(self._conf)
        vars["getPDFURL"]=quoteattr(str(url))
        return vars

class WPAbstractBookCustomise( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEAbstractBookCustomise

    def _getBody( self, params ):
        wc = WAbstractBookCustomise( self._conf )
        return wc.getHTML(params)

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._abstractsBookOpt)

##################################################################################3

class WPMeetingStaticDisplay( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars

    def _getBody( self, params ):
        wc = WMeetingStaticDetails( self._getAW(), self._conf, self._staticPars )
        return wc.getHTML({})

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._overviewOpt)


class WPMeetiStaticProgram( WPConferenceStaticDefaultDisplayBase ):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target)
        self._staticPars = staticPars

    def _getBody( self, params ):
        wc = WConfStaticProgram( self._getAW(), self._conf, self._staticPars )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._programOpt)


class WMConfStaticDetails( wcomponents.WTemplated ):

    def __init__(self, aw, conf, staticPars):
        self._conf = conf
        self._aw = aw
        self._staticPars = staticPars

    def _getChairsHTML( self ):
        chairList = []
        l = []
        for chair in self._conf.getChairList():
            mailToURL = """mailto:%s"""%urllib.quote(chair.getEmail())
            l.append( """<a href=%s>%s</a>"""%(quoteattr(mailToURL),self.htmlText(chair.getFullName())))
        res = ""
        if len(l) > 0:
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Chairs"):</b></td>
        <td>%s</td>
    </tr>
                """)%"<br>".join(l)
        return res

    def _getMaterialHTML( self ):
        l = []
        for mat in self._conf.getAllMaterialList():
            temp = wcomponents.WMaterialDisplayItem()
            url = urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat)
            l.append( temp.getHTML( self._aw, mat, url, self._staticPars["material"] ) )
        res = ""
        if l:
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Material"):</b></td>
        <td align="left" width="100%%">%s</td>
    </tr>""")%"<br>".join( l )
        return res

    def _getMoreInfoHTML( self ):
        res = ""
        if self._conf.getContactInfo() != "":
            res = _("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Additional info"):</b>
        </td>
        <td>%s</td>
    </tr>""")%self._conf.getContactInfo()
        return res

    def _getActionsHTML( self, showActions = False):
        html=[]
        if showActions:
            html=[ _("""
                <table style="padding-top:40px; padding-left:20px">
                <tr>
                    <td nowrap>
                        <b> _("Conference sections"):</b>
                        <ul>
                """)]
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            for link in menu.getLinkList():
                if link.isVisible() and link.isEnabled():
                    html.append(""" <li><a href="%s">%s</a></li>
                            """%( link.getURL(), link.getCaption() ) )
            html.append("""
                        </ul>
                    </td>
                </tr>
                </table>
                """)
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["description"] = self._conf.getDescription()
        sdate, edate = self._conf.getAdjustedStartDate(), self._conf.getAdjustedEndDate()
        fsdate, fedate = sdate.strftime("%d %B %Y"), edate.strftime("%d %B %Y")
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        vars["dateInterval"] = "from %s %s to %s %s"%(fsdate, fstime, \
                                                        fedate, fetime)
        if sdate.strftime("%d%B%Y") == edate.strftime("%d%B%Y"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s-%s"%(fstime, fetime)
            vars["dateInterval"] = "%s (%s)"%( fsdate, timeInterval)
        vars["location"] = ""
        location = self._conf.getLocation()
        if location:
            vars["location"] = "<i>%s</i><br><pre>%s</pre>"%( location.getName(), location.getAddress() )
            room = self._conf.getRoom()
            if room:
                roomLink = linking.RoomLinker().getHTMLLink( room, location )
                vars["location"] += _("""<small> _("Room"):</small> %s""")%roomLink
        vars["chairs"] = self._getChairsHTML()
        vars["material"] = self._getMaterialHTML()
        vars["moreInfo"] = self._getMoreInfoHTML()
        vars["actions"] = self._getActionsHTML(vars.get("menuStatus", "open") != "open")

        return vars

class WConfStaticProgram(wcomponents.WTemplated):

    def __init__(self, aw, conf, staticPars):
        self._conf = conf
        self._aw = aw
        self._staticPars = staticPars

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        program = []
        for track in self._conf.getTrackList():
            program.append( WConfStaticProgramTrack( self._aw, track, self._staticPars ).getHTML() )
        vars["program"] = "".join( program )
        return vars

class WConfModifReschedule(wcomponents.WTemplated):

    def __init__(self, targetDay):
        self._targetDay = targetDay

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["targetDay"]=quoteattr(str(self._targetDay))
        return vars

class WPConfModifReschedule(WPConferenceModifBase):

    def __init__(self, rh, conf, targetDay):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._targetDay=targetDay

    def _getPageContent( self, params):
        wc=WConfModifReschedule(self._targetDay)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifReschedule.getURL(self._conf)))}
        return wc.getHTML(p)

class WPConfDisplayWriteMinutes( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._conf )
        pars = {"postURL": urlHandlers.UHConferenceDisplayWriteMinutes.getURL(self._conf) }
        return wc.getHTML( pars )

class WPConfModifRelocate(WPConferenceModifBase):

    def __init__(self, rh, conf, entry, targetDay):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._targetDay=targetDay
        self._entry=entry

    def _getPageContent( self, params):
        wc=wcomponents.WSchRelocate(self._entry)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifScheduleRelocate.getURL(self._entry))), \
                "targetDay":quoteattr(str(self._targetDay))}
        return wc.getHTML(p)


class WPConfModifReportNumberEdit(WPConferenceModifBase):

    def __init__(self, rh, conf, reportNumberSystem):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._reportNumberSystem=reportNumberSystem

    def _getPageContent( self, params):
        wc=wcomponents.WModifReportNumberEdit(self._conf, self._reportNumberSystem)
        return wc.getHTML()


class WPConfModifExistingMaterials( WPConferenceModifBase ):
    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _getPageContent( self, pars ):
        wc=wcomponents.WShowExistingMaterial(self._conf)
        return wc.getHTML( pars )

    def _setActiveTab( self ):
        self._tabMaterials.setActive()

    def _setActiveSideMenuItem( self ):
        self._materialMenuItem.setActive()

class WPConfModifDisplayImageBrowser (wcomponents.WTemplated):

    def __init__(self, conf, req):
        self._conf = conf
        self._req = req

    def _getFileHTML(self, file):
        return """<td>&nbsp;<a href="#" onClick="OpenFile('%s');return false;"><img src="%s" height="80"></a></td>""" % (str(urlHandlers.UHFileAccess.getURL(file)),str(urlHandlers.UHFileAccess.getURL(file)))

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"] = Config.getInstance().getBaseURL()
        vars["body"] = ""
        materialName = _("Internal Page Files")
        mats = self._conf.getMaterialList()
        mat = None
        existingFiles = []
        for m in mats:
            if m.getTitle() == materialName:
                mat = m
        if mat != None:
            existingFiles = mat.getResourceList()
        if len(existingFiles) == 0:
            vars["body"] = _("""<br><br>&nbsp;&nbsp;&nbsp; _("no image found")...""")
        else:
            vars["body"] += "<table><tr>"
            for file in existingFiles:
                vars["body"] += self._getFileHTML(file)
            vars["body"] += "</tr></table>"
        return vars


class WPDisplayFullMaterialPackage( WPConferenceDefaultDisplayBase ):

    def _getBody(self,params):
        wc = WFullMaterialPackage( self._conf )
        p = {"errors": params.get("errors",""),\
             "getPkgURL": urlHandlers.UHConferenceDisplayMaterialPackagePerform.getURL(self._conf)}
        return wc.getHTML(p)

# ============================================================================
# === Room booking related ===================================================
# ============================================================================

#from MaKaC.webinterface.pages.roomBooking import WPRoomBookingBase0
class WPConfModifRoomBookingBase( WPConferenceModifBase ):

    def getJSFiles(self):
        return [ 'js/prototype/prototype.js',
                 'js/scriptaculous/scriptaculous.js' ] + \
                WPConferenceModifBase.getJSFiles(self)

    def _getHeadContent( self ):
        """
        !!!! WARNING
        If you update the following, you will need to do
        the same update in:
        roomBooking.py / WPRoomBookingBase0  AND
        conferences.py / WPConfModifRoomBookingBase

        For complex reasons, these two inheritance chains
        should not have common root, so this duplication is
        necessary evil. (In general, one chain is for standalone
        room booking and second is for conference-context room
        booking.)
        """
        baseurl = self._getBaseURL()
        return """
        <!-- Lightbox -->
        <link rel="stylesheet" href="%s/js/lightbox/lightbox.css"> <!--lightbox.css-->
        <script type="text/javascript" src="%s/js/lightbox/lightbox.js"></script>

        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js"></script>

        """ % ( baseurl, baseurl, baseurl )

    def _setActiveSideMenuItem(self):
        self._roomBookingMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabExistBookings = self._tabCtrl.newTab( "existing", "Existing Bookings", \
                urlHandlers.UHConfModifRoomBookingList.getURL( self._conf ) )
        self._tabNewBooking = self._tabCtrl.newTab( "new", "New Booking", \
                urlHandlers.UHConfModifRoomBookingChooseEvent.getURL( self._conf ) )

        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

    def _getTabContent(self, params):
        return "nothing"


# 0. Choosing an "event" (conference / session / contribution)...

class WPConfModifRoomBookingChooseEvent( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf )

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingChooseEvent( self._rh )
        return wc.getHTML( params )

    def _setActiveTab( self ):
        self._tabNewBooking.setActive()

# 1. Searching...

class WPConfModifRoomBookingSearch4Rooms( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf )


    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingSearch4Rooms( self._rh )
        return wc.getHTML( params )

    def _setActiveTab( self ):
        self._tabNewBooking.setActive()

# 2. List of...

class WPConfModifRoomBookingRoomList( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, self._rh._conf )

    def _setActiveTab( self ):
        self._tabNewBooking.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingRoomList( self._rh )
        return wc.getHTML( params )



class WPConfModifRoomBookingList( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf )

    def _setActiveTab( self ):
        self._tabExistBookings.setActive()

    def _getTabContent( self, pars ):
        wc = wcomponents.WRoomBookingList( self._rh )
        return wc.getHTML( pars )


# 3. Details of...

class WPConfModifRoomBookingRoomDetails( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf )

    def _setActiveTab( self ):
        self._tabNewBooking.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingRoomDetails( self._rh )
        return wc.getHTML( params )

class WPConfModifRoomBookingDetails( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf )

    def _setActiveTab( self ):
        self._tabExistBookings.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingDetails( self._rh )
        return wc.getHTML( params )

# 4. New booking

class WPConfModifRoomBookingBookingForm( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf )

    def _setActiveTab( self ):
        self._tabNewBooking.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingBookingForm( self._rh )
        return wc.getHTML( params )


# ============================================================================
# === Badges related =========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Badge Printing classes
"""
class WConfModifBadgePrinting( wcomponents.WTemplated ):
    """ This class corresponds to the screen where badge templates are
        listed and can be created, edited, deleted, and tried.
    """

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def _getBaseTemplatesHTML( self ):
        dconf = conference.CategoryManager().getDefaultConference()
        templates = dconf.getBadgeTemplateManager().getTemplates()

        html = _("""<option value="blank">&lt; _("Blank Page")&gt;</option>""")

        for id,template in templates.iteritems():
            html += '<option value="'+id+'">'+template.getName()+'</option>'

        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["NewTemplateURL"]=str(urlHandlers.UHConfModifBadgeDesign.getURL(self.__conf,self.__conf.getBadgeTemplateManager().getNewTemplateId(),new = True))
        vars["CreatePDFURL"]=str(urlHandlers.UHConfModifBadgePrintingPDF.getURL(self.__conf))

        vars["TryTemplateDisabled"] = ""
        if len(self.__conf.getBadgeTemplateManager().getTemplates()) == 0:
            vars["TryTemplateDisabled"] = "disabled"

        templateListHTML = []
        first = True
        sortedTemplates = self.__conf.getBadgeTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))
        for templateId, template in sortedTemplates:
            templateListHTML.append("""              <tr>""")
            templateListHTML.append("""                <td>""")
            radio = []
            radio.append("""                  <input type="radio" name="templateId" value='""")
            radio.append(str(templateId))
            radio.append("""' id='""")
            radio.append(str(templateId))
            radio.append("""'""")
            if first:
                first = False
                radio.append( _(""" CHECKED """))
            radio.append(""">""")
            templateListHTML.append("".join(radio))
            templateListHTML.append("".join (["""                  """,
                                              """<label for='""",
                                              str(templateId),
                                              """'>""",
                                              template.getName(),
                                              """</label>""",
                                              """&nbsp;&nbsp;&nbsp;"""]))
            edit = []
            edit.append("""                  <a href='""")
            edit.append(str(urlHandlers.UHConfModifBadgeDesign.getURL(self.__conf, templateId)))
            edit.append("""'><img src='""")
            edit.append(str(Config.getInstance().getSystemIconURL("file_edit")))
            edit.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(edit))
            delete = []
            delete.append("""                  <a href='""")
            delete.append(str(urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, deleteTemplateId=templateId)))
            delete.append( _("""' onClick="return confirm('""" + _("Are you sure you want to delete this template?") + """');"><img src='"""))
            delete.append(str(Config.getInstance().getSystemIconURL("smallDelete")))
            delete.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(delete))
            copy = []
            copy.append("""                  <a href='""")
            copy.append(str(urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, copyTemplateId=templateId)))
            copy.append("""'><img src='""")
            copy.append(str(Config.getInstance().getSystemIconURL("smallCopy")))
            copy.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(copy))

            templateListHTML.append("""                </td>""")
            templateListHTML.append("""              </tr>""")

        vars["templateList"] = "\n".join(templateListHTML)

        wcPDFOptions = WConfModifBadgePDFOptions(self.__conf)
        vars['PDFOptions'] = wcPDFOptions.getHTML()
        vars['baseTemplates'] = self._getBaseTemplatesHTML()


        return vars

class WConfModifBadgePDFOptions( wcomponents.WTemplated ):

    def __init__( self, conference, showKeepValues = True, showTip = True ):
        self.__conf = conference
        self.__showKeepValues = showKeepValues
        self.__showTip = showTip

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        vars['PagesizeNames'] = pagesizeNames

        vars['PDFOptions'] = self.__conf.getBadgeTemplateManager().getPDFOptions()
        vars['ShowKeepValues'] = self.__showKeepValues
        vars['ShowTip'] = self.__showTip

        return vars


class WPConfModifBadgePrinting( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabBadges.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifBadgePrinting( self._conf )
        return wc.getHTML()



##------------------------------------------------------------------------------------------------------------
"""
Badge Design classes
"""
class WConfModifBadgeDesign( wcomponents.WTemplated ):
    """ This class corresponds to the screen where a template
        is designed inserting, dragging and editing items.
    """

    def __init__( self, conference, templateId, new = False, user = None ):
        self.__conf = conference
        self.__templateId = templateId
        self.__new = new
        self._user=user

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"]=Config.getInstance().getBaseURL() ##base url of the application, used for the ruler images
        vars["cancelURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, templateId = self.__templateId, cancel = True)
        vars["saveBackgroundURL"]=urlHandlers.UHConfModifBadgeSaveBackground.getURL(self.__conf, self.__templateId)
        vars["loadingIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("loading")))
        vars["templateId"]=self.__templateId

        badgeDesignConfiguration = BadgeDesignConfiguration()
        from MaKaC.services.interface.rpc.json import encode as jsonEncode
        vars["translateName"]= jsonEncode(dict([(key, value[0]) for key, value in badgeDesignConfiguration.items_actions.iteritems()]))

        cases = []
        for itemKey in badgeDesignConfiguration.items_actions.keys():
            case = []
            case.append('case "')
            case.append(itemKey)
            case.append('":')
            case.append('\n')
            case.append('items[itemId] = new Item(itemId, "')
            case.append(itemKey)
            case.append('");')
            case.append('\n')
            case.append('newDiv.innerHTML = items[itemId].toHTML();')
            case.append('\n')
            case.append('break;')
            cases.append("".join(case))

        vars['switchCases'] = "\n".join(cases)

        optgroups = []
        for optgroupName, options in badgeDesignConfiguration.groups:
            optgroup = []
            optgroup.append('<optgroup label="')
            optgroup.append(optgroupName)
            optgroup.append('">')
            optgroup.append('\n')
            for optionName in options:
                optgroup.append('<option value="%s">'%optionName)
                optgroup.append(badgeDesignConfiguration.items_actions[optionName][0])
                optgroup.append('</option>')
                optgroup.append('\n')
            optgroup.append('</optgroup>')
            optgroups.append("".join(optgroup))

        vars['selectOptions'] = "\n".join(optgroups)


        if self.__new:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, new=True)
            vars["titleMessage"]= _("Creating new badge template")
            vars["editingTemplate"]="false"
            vars["templateData"]="''"
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1

        elif self.__templateId is None:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf)
            vars["titleMessage"]= _("No template id given")
            vars["editingTemplate"]="false"
            vars["templateData"]="''"
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1

        else:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf)
            vars["titleMessage"]= _("Editing badge template")
            vars["editingTemplate"]="true"

            templateDataString = jsonEncode(self.__conf.getBadgeTemplateManager().getTemplateData(self.__templateId))
            vars["templateData"]= templateDataString

            usedBackgroundId = self.__conf.getBadgeTemplateManager().getTemplateById(self.__templateId).getUsedBackgroundId()
            vars["backgroundId"] = usedBackgroundId
            if usedBackgroundId != -1:
                vars["hasBackground"]="true"
                vars["backgroundURL"]=str(urlHandlers.UHConfModifBadgeGetBackground.getURL(self.__conf, self.__templateId, usedBackgroundId))
            else:
                vars["hasBackground"]="false"
                vars["backgroundURL"]="false"


        return vars


class WPConfModifBadgeDesign( WPConfModifToolsBase ):

    def __init__(self, rh, conf, templateId = None, new = False, baseTemplateId = "blank"):
        WPConferenceModifBase.__init__(self, rh, conf)

        self.__templateId = templateId

        self.__new = new
        self.__baseTemplate = baseTemplateId

        if baseTemplateId != 'blank':
            dconf = conference.CategoryManager().getDefaultConference()
            templMan = conf.getBadgeTemplateManager()
            newId = templateId
            dconf.getBadgeTemplateManager().getTemplateById(baseTemplateId).clone(templMan, newId)
            # now, let's pretend nothing happened, and let the code
            # handle the template as if it existed before
            self.__new = False

    def getJSFiles(self):
        return [ 'js/prototype/prototype.js',
                 'js/scriptaculous/scriptaculous.js' ] + \
                WPConfModifToolsBase.getJSFiles(self)

    def _setActiveTab( self ):
        self._tabBadges.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifBadgeDesign( self._conf, self.__templateId, self.__new )
        return wc.getHTML()

##------------------------------------------------------------------------------------------------------------
"""
Common PDF Options classes
"""
class WConfCommonPDFOptions( wcomponents.WTemplated ):
    """ This class corresponds to a section of options
        that are common to each PDF in Indico.
    """

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        pagesizeOptions = []
        for pagesizeName in pagesizeNames:
            pagesizeOptions.append('<option')
            if pagesizeName == 'A4':
                pagesizeOptions.append( _("SELECTED"))
            pagesizeOptions.append('>')
            pagesizeOptions.append(pagesizeName)
            pagesizeOptions.append('</option>')

        vars['pagesizes'] = "".join(pagesizeOptions)

        fontsizeOptions = []
        for fontsizeName in PDFSizes().PDFfontsizes:
            fontsizeOptions.append('<option')
            if fontsizeName == 'normal':
                fontsizeOptions.append( _("SELECTED"))
            fontsizeOptions.append('>')
            fontsizeOptions.append(fontsizeName)
            fontsizeOptions.append('</option>')

        vars['fontsizes'] = "".join(fontsizeOptions)

        return vars


# ============================================================================
# === Posters related ========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Poster Printing classes
"""
class WConfModifPosterPrinting( wcomponents.WTemplated ):
    """ This class corresponds to the screen where poster templates are
        listed and can be created, edited, deleted, and tried.
    """

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def _getFullTemplateListHTML( self ):
        globaltemplates = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplates()
        localtemplates = self.__conf.getPosterTemplateManager().getTemplates()
        html = ''
        for id,template in globaltemplates.iteritems():
            html += '<option value="global'+id+'">'+template.getName()+' (global)</option>'
        for id,template in localtemplates.iteritems():
            html += '<option value="'+id+'">'+template.getName()+' (local)</option>'
        return html

    def _getBaseTemplateListHTML( self ):
        globaltemplates = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplates()
        html = '<option value="blank">Blank Page</option>'
        for id,template in globaltemplates.iteritems():
            html += '<option value="'+id+'">'+template.getName()+'</option>'
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["NewTemplateURL"]=str(urlHandlers.UHConfModifPosterDesign.getURL(self.__conf, self.__conf.getPosterTemplateManager().getNewTemplateId(),new = True))
        vars["CreatePDFURL"]=str(urlHandlers.UHConfModifPosterPrintingPDF.getURL(self.__conf))
        templateListHTML = []
        first = True
        sortedTemplates = self.__conf.getPosterTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))
        for templateId, template in sortedTemplates:
            templateListHTML.append("""              <tr>""")
            templateListHTML.append("""                <td>""")
            templateListHTML.append("".join (["""                  """,
                                              """<label for='""",
                                              str(templateId),
                                              """'>""",
                                              template.getName(),
                                              """</label>""",
                                              """&nbsp;&nbsp;&nbsp;"""]))

            edit = []
            edit.append("""                  <a href='""")
            edit.append(str(urlHandlers.UHConfModifPosterDesign.getURL(self.__conf, templateId)))
            edit.append("""'><img src='""")
            edit.append(str(Config.getInstance().getSystemIconURL("file_edit")))
            edit.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(edit))
            delete = []
            delete.append("""                  <a href='""")
            delete.append(str(urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, deleteTemplateId=templateId)))
            delete.append("""'><img src='""")
            delete.append(str(Config.getInstance().getSystemIconURL("smallDelete")))
            delete.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(delete))
            copy = []
            copy.append("""                  <a href='""")
            copy.append(str(urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, copyTemplateId=templateId)))
            copy.append("""'><img src='""")
            copy.append(str(Config.getInstance().getSystemIconURL("smallCopy")))
            copy.append("""' border='0'></a>&nbsp;""")
            templateListHTML.append("".join(copy))
            templateListHTML.append("""                </td>""")
            templateListHTML.append("""              </tr>""")

        vars["templateList"] = "\n".join(templateListHTML)

        wcPDFOptions = WConfModifPosterPDFOptions(self.__conf)
        vars['PDFOptions'] = wcPDFOptions.getHTML()

        vars['baseTemplateList'] = self._getBaseTemplateListHTML()
        vars['fullTemplateList'] = self._getFullTemplateListHTML()

        return vars

class WConfModifPosterPDFOptions( wcomponents.WTemplated ):

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        pagesizeOptions = []
        for pagesizeName in pagesizeNames:
            pagesizeOptions.append('<option')
            if pagesizeName == 'A4':
                pagesizeOptions.append(" SELECTED")
            pagesizeOptions.append('>')
            pagesizeOptions.append(pagesizeName)
            pagesizeOptions.append('</option>')

        vars['pagesizes'] = "".join(pagesizeOptions)

        return vars

class WPConfModifPosterPrinting( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabPosters.setActive()

    def _getTabContent( self, params ):

        wc = WConfModifPosterPrinting( self._conf )

        return wc.getHTML()

##------------------------------------------------------------------------------------------------------------
"""
Poster Design classes
"""
class WConfModifPosterDesign( wcomponents.WTemplated ):
    """ This class corresponds to the screen where a template
        is designed inserting, dragging and editing items.
    """

    def __init__( self, conference, templateId, new = False, user = None):
        self.__conf = conference
        self.__templateId = templateId
        self.__new = new
        self._user=user


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"]=Config.getInstance().getBaseURL() ##base url of the application, used for the ruler images
        vars["cancelURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, templateId = self.__templateId, cancel = True)
        vars["saveBackgroundURL"]=urlHandlers.UHConfModifPosterSaveBackground.getURL(self.__conf, self.__templateId)
        vars["loadingIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("loading")))
        vars["templateId"]=self.__templateId

        posterDesignConfiguration = PosterDesignConfiguration()
        from MaKaC.services.interface.rpc.json import encode as jsonEncode
        vars["translateName"]= jsonEncode(dict([(key, value[0]) for key, value in posterDesignConfiguration.items_actions.iteritems()]))


        cases = []
        for itemKey in posterDesignConfiguration.items_actions.keys():
            case = []
            case.append('case "')
            case.append(itemKey)
            case.append('":')
            case.append('\n')
            case.append('items[itemId] = new Item(itemId, "')
            case.append(itemKey)
            case.append('");')
            case.append('\n')
            case.append('newDiv.innerHTML = items[itemId].toHTML();')
            case.append('\n')
            case.append('break;')
            cases.append("".join(case))

        vars['switchCases'] = "\n".join(cases)

        optgroups = []
        for optgroupName, options in posterDesignConfiguration.groups:
            optgroup = []
            optgroup.append('<optgroup label="')
            optgroup.append(optgroupName)
            optgroup.append('">')
            optgroup.append('\n')
            for optionName in options:
                optgroup.append('<option value="%s">'%optionName)
                optgroup.append(posterDesignConfiguration.items_actions[optionName][0])
                optgroup.append('</option>')
                optgroup.append('\n')
            optgroup.append('</optgroup>')
            optgroups.append("".join(optgroup))

        vars['selectOptions'] = "\n".join(optgroups)

        if self.__new:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, new=True)
            vars["titleMessage"]= _("Creating new poster template")
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1
            vars["backgroundPos"]="Stretch"
            vars["templateData"]="''"
            vars["editingTemplate"]="false"


        elif self.__templateId is None:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf)
            vars["titleMessage"]= _("No template id given")
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1
            vars["backgroundPos"]="Stretch"
            vars["templateData"] = "''"
            vars["editingTemplate"]="false"


        else:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf)
            vars["titleMessage"]= _("Editing poster template")
            vars["editingTemplate"]="true"
            templateDataString = jsonEncode(self.__conf.getPosterTemplateManager().getTemplateData(self.__templateId))
            vars["templateData"]=quoteattr(templateDataString)

            usedBackgroundId = self.__conf.getPosterTemplateManager().getTemplateById(self.__templateId).getUsedBackgroundId()
            vars["backgroundId"] = usedBackgroundId

            if usedBackgroundId != -1:
                vars["hasBackground"]="true"
                vars["backgroundURL"]=str(urlHandlers.UHConfModifPosterGetBackground.getURL(self.__conf, self.__templateId, usedBackgroundId))
                vars["backgroundPos"]=self.__conf.getPosterTemplateManager().getTemplateById(self.__templateId).getBackgroundPosition(usedBackgroundId)
            else:
                vars["hasBackground"]="false"
                vars["backgroundURL"]="false"
                vars["backgroundPos"]="Stretch"

        return vars


class WPConfModifPosterDesign( WPConfModifToolsBase ):

    def __init__(self, rh, conf, templateId = None, new = False, baseTemplateId = "blank"):
        WPConferenceModifBase.__init__(self, rh, conf)
        self.__templateId = templateId
        self.__new = new
        self.__baseTemplate = baseTemplateId

    def getJSFiles(self):
        return [ 'js/prototype/prototype.js',
                 'js/scriptaculous/scriptaculous.js' ] + \
                WPConfModifToolsBase.getJSFiles(self)

    def _setActiveTab( self ):
        self._tabPosters.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifPosterDesign( self._conf, self.__templateId, self.__new)
        return wc.getHTML()

    def sortByName(x,y):
        return cmp(x.getFamilyName(),y.getFamilyName())

class WPConfModifPreviewCSS( WPConferenceDefaultDisplayBase ):
    #from MaKaC.webinterface.pages import base
   # from MaKaC.webinterface import wcomponents

    def __init__( self, rh, conf, selectedCSSId):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )

        self._conf = conf
        self._cssTplsModule = ModulesHolder().getById("cssTpls")
        self._styleMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()

        self._selectedCSS = None
        if selectedCSSId == "css": # local uploaded file choice
            self._selectedCSS = self._styleMgr.getLocalCSS()
        elif selectedCSSId:
            self._selectedCSS = self._cssTplsModule.getCssTplById(selectedCSSId)

    def _applyDecoration( self, body ):
        """
        """
        return "%s%s%s"%( self._getHeader(), body, self._getFooter() )

    def _getBody( self, params ):
        path = self._getBaseURL()
        htdocs = Config.getInstance().getHtdocsDir()
        params["URL2Back"] = urlHandlers.UHConfModifDisplay.getURL(self._conf)
        params["cssurl"] = ""
        params['selectedCSSId'] = ""
        if self._selectedCSS:
            params["cssurl"] = self._selectedCSS.getURL()
            params['selectedCSSId'] = self._selectedCSS.getId()
        elif self._styleMgr.getCSS():
            params["cssurl"] = self._styleMgr.getCSS().getURL()
            params['selectedCSSId'] = self._styleMgr.getCSS().getId()
        params["saveCSS"]=urlHandlers.UHUseCSS.getURL(self._conf)
        params['confId'] = self._conf.getId()
        params["previewURL"]= urlHandlers.UHConfModifPreviewCSS.getURL(self._conf)
        params["templatesList"]=[]
        if self._styleMgr.getLocalCSS():
            params["templatesList"].append(self._styleMgr.getLocalCSS())
        params["templatesList"].extend(self._cssTplsModule.getCssTplsList())

        ###############################
        # injecting ConferenceDisplay #
        ###############################
        p = WPConferenceDisplay( self._rh, self._conf )
        p._defineSectionMenu()
        p._toolBar=wcomponents.WebToolBar()
        p._defineToolBar()
        params["bodyConf"] = p._applyConfDisplayDecoration( p._getBody( params ) )
        ###############################
        ###############################

        wc = WPreviewPage()
        return wc.getHTML(params)

    def _getHeadContent( self ):
        path = self._getBaseURL()
        printCSS = """
        <link rel="stylesheet" type="text/css" href="%s/css/Conf_Basic.css" >
            """ % path

        if self._selectedCSS:
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s" >"""%self._selectedCSS.getURL()
        elif self._styleMgr.getCSS():
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s" >"""%self._styleMgr.getCSS().getURL()
        return printCSS


class WPreviewPage( wcomponents.WTemplated ):
    pass

