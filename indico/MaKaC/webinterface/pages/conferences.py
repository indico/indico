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

import collections
from flask import session, request
import os
import random
import time
import urllib
from indico.util import json

from datetime import timedelta, datetime
from xml.sax.saxutils import quoteattr, escape

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
from MaKaC.common.utils import isStringHTML, formatDateTime, formatDate
import MaKaC.common.utils
import MaKaC.review as review
from MaKaC.review import AbstractTextField
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.pages.signIn import WPResetPasswordBase
from MaKaC.webinterface.common.tools import strip_ml_tags, escape_html
from MaKaC.webinterface.materialFactories import ConfMFRegistry,PaperFactory,SlidesFactory,PosterFactory
from indico.core.config import Config
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.common.output import outputGenerator
from MaKaC.webinterface.general import strfFileSize
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.PDFinterface.base import PDFSizes
from pytz import timezone
from MaKaC.common.timezoneUtils import nowutc, DisplayTZ
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface.pages import main
from MaKaC.webinterface.pages import base
from MaKaC.webinterface.materialFactories import MaterialFactoryRegistry
import MaKaC.common.info as info
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util.date_time import format_time, format_date, format_datetime
from indico.util.string import safe_upper
import MaKaC.webcast as webcast
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import IConferenceEventInfoFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.common.logger import Logger
from MaKaC.plugins.base import OldObservable
from MaKaC.plugins.base import extension_point
from indico.core import config as Configuration
from indico.modules import ModuleHolder
from MaKaC.paperReviewing import ConferencePaperReview as CPR
from MaKaC.conference import Session, Contribution, LocalFile
from indico.core.config import Config
from MaKaC.common.utils import formatDateTime
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.general import WebFactory
from MaKaC.common.TemplateExec import render


def stringToDate(str):

    # Don't delete this dictionary inside comment. Its purpose is to
    # add the dictionary in the language dictionary during the extraction!
    # months = { _("January"): 1, _("February"): 2, _("March"): 3, _("April"): 4,
    #            _("May"): 5, _("June"): 6, _("July"): 7, _("August"): 8,
    #            _("September"): 9, _("October"): 10, _("November"): 11, _("December"): 12 }

    months = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }
    [day, month, year] = str.split("-")
    return datetime(int(year), months[month], int(day))


class WPConferenceBase(base.WPDecorated):

    def __init__(self, rh, conference):
        WPDecorated.__init__(self, rh)
        self._navigationTarget = self._conf = conference
        tz = self._tz = DisplayTZ(rh._aw, self._conf).getDisplayTZ()
        sDate = self.sDate = self._conf.getAdjustedScreenStartDate(tz)
        eDate = self.eDate = self._conf.getAdjustedScreenEndDate(tz)
        dates = " (%s)" % format_date(sDate, format='long')
        if sDate.strftime("%d%B%Y") != eDate.strftime("%d%B%Y"):
            if sDate.strftime("%B%Y") == eDate.strftime("%B%Y"):
                dates = " (%s-%s)" % (sDate.strftime("%d"), format_date(eDate, format='long'))
            else:
                dates = " (%s - %s)" % (format_date(sDate, format='long'), format_date(eDate, format='long'))
        self._setTitle("%s %s" % (strip_ml_tags(self._conf.getTitle()), dates))

    def _getFooter(self):
        """
        """
        wc = wcomponents.WFooter()

        p = {"modificationDate": format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),
             "subArea": self._getSiteArea()
             }
        return wc.getHTML(p)

    def getLoginURL( self ):
        wf = self._rh.getWebFactory()
        if wf:
            return WPDecorated.getLoginURL(self)

        return urlHandlers.UHConfSignIn.getURL(self._conf, request.url)

    def getLogoutURL( self ):
        return urlHandlers.UHSignOut.getURL(str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))


class WPConferenceDisplayBase(WPConferenceBase, OldObservable):

    def getCSSFiles(self):
        # flatten returned list

        return WPConferenceBase.getCSSFiles(self) + \
               sum(self._notify('injectCSSFiles'), [])

class WPConferenceDefaultDisplayBase( WPConferenceBase):
    navigationEntry = None

    def getJSFiles(self):
        return WPConferenceBase.getJSFiles(self) + self._includeJSPackage('Display') + \
               self._includeJSPackage('MaterialEditor') + sum(self._notify('injectJSFiles'), [])

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"modificationDate": format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),
                "subArea": self._getSiteArea()}

        cid = self._conf.getUrlTag().strip() or self._conf.getId()
        p["shortURL"] =  Config.getInstance().getShortEventURL() + cid

        self._notify('eventDetailFooter', p)

        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WConferenceHeader( self._getAW(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
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
        if not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            self._cfaOpt.setVisible(False)
            self._abstractsBookOpt.setVisible(False)
        else:
            self._cfaOpt.setVisible(True)
            self._abstractsBookOpt.setVisible(True)
        self._trackMgtOpt = self._sectionMenu.getLinkByName("manageTrack")

        #registration form
        self._regFormOpt = self._sectionMenu.getLinkByName("registrationForm")
        self._viewRegFormOpt = self._sectionMenu.getLinkByName("ViewMyRegistration")
        self._eTicketOpt = self._sectionMenu.getLinkByName("downloadETicket")
        self._newRegFormOpt = self._sectionMenu.getLinkByName("NewRegistration")
        if awUser:
            self._viewRegFormOpt.setVisible(awUser.isRegisteredInConf(self._conf))
            if self._conf.getRegistrationForm().getETicket().isEnabled() and \
                    self._conf.getRegistrationForm().getETicket().isShownInConferenceMenu():
                self._eTicketOpt.setVisible(awUser.isRegisteredInConf(self._conf))
            else:
                self._eTicketOpt.setVisible(False)
            self._newRegFormOpt.setVisible(not awUser.isRegisteredInConf(self._conf))
        else:
            self._viewRegFormOpt.setVisible(False)
            self._eTicketOpt.setVisible(False)
            self._newRegFormOpt.setVisible(True)
        self._registrantsListOpt = self._sectionMenu.getLinkByName("registrants")
        if not self._conf.getRegistrationForm().isActivated() or not self._conf.hasEnabledSection("regForm"):
            self._regFormOpt.setVisible(False)
            self._registrantsListOpt.setVisible(False)
        else:
            self._regFormOpt.setVisible(True)
            self._registrantsListOpt.setVisible(True)


        #instant messaging
        self._notify('confDisplaySMShow', {})

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
        ls = set(self._conf.getCoordinatedSessions(awUser)) | set(self._conf.getManagedSession(awUser))
        self._mySessionsOpt.setVisible(len(ls)>0)
        self._myTracksOpt=self._sectionMenu.getLinkByName("mytracks")
        lt=self._conf.getCoordinatedTracks(awUser)
        self._myTracksOpt.setVisible(len(lt)>0)
        if not self._conf.getAbstractMgr().isActive():
            self._myTracksOpt.setVisible(False)
        self._myContribsOpt=self._sectionMenu.getLinkByName("mycontribs")
        lc=self._conf.getContribsForSubmitter(awUser)
        self._myContribsOpt.setVisible(len(lc)>0)
        self._trackMgtOpt.setVisible(len(lt)>0)
        if not self._conf.getAbstractMgr().isActive():
            self._trackMgtOpt.setVisible(False)

        #paper reviewing related
        self._paperReviewingOpt = self._sectionMenu.getLinkByName("paperreviewing")
        self._paperReviewingMgtOpt=self._sectionMenu.getLinkByName("managepaperreviewing")
        self._paperReviewingMgtOpt.setVisible(False)

        self._assignContribOpt=self._sectionMenu.getLinkByName("assigncontributions")
        self._assignContribOpt.setVisible(False)

        self._judgeListOpt=self._sectionMenu.getLinkByName("judgelist")
        self._judgeListOpt.setVisible(False)
        self._judgereviewerListOpt=self._sectionMenu.getLinkByName("judgelistreviewer")

        self._judgereviewerListOpt.setVisible(False)
        self._judgeeditorListOpt=self._sectionMenu.getLinkByName("judgelisteditor")
        self._judgeeditorListOpt.setVisible(False)

        self._uploadPaperOpt = self._sectionMenu.getLinkByName("uploadpaper")
        self._downloadTemplateOpt = self._sectionMenu.getLinkByName("downloadtemplate")

        if self._conf.getConfPaperReview().hasReviewing():
            self._paperReviewingOpt.setVisible(True)
            # These options are shown if there is any contribution of this user
            self._uploadPaperOpt.setVisible(len(lc)>0)
            self._downloadTemplateOpt.setVisible(len(lc)>0)
        else:
            self._paperReviewingOpt.setVisible(False)
            self._uploadPaperOpt.setVisible(False)
            self._downloadTemplateOpt.setVisible(False)


        if awUser != None:

            conferenceRoles = awUser.getLinkedTo()["conference"]

            if "paperReviewManager" in conferenceRoles:
                if self._conf in awUser.getLinkedTo()["conference"]["paperReviewManager"]:
                    self._paperReviewingMgtOpt.setVisible(True)
                    self._assignContribOpt.setVisible(True)
                    self._uploadPaperOpt.setVisible(len(lc)>0)
                    self._downloadTemplateOpt.setVisible(True)

            if "referee" in conferenceRoles and "editor" in conferenceRoles and "reviewer" in conferenceRoles:
                showrefereearea = self._conf in awUser.getLinkedTo()["conference"]["referee"]
                showreviewerarea = self._conf in awUser.getLinkedTo()["conference"]["reviewer"]
                showeditorarea = self._conf in awUser.getLinkedTo()["conference"]["editor"]

                if showrefereearea and (self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING):
                    self._assignContribOpt.setVisible(True)
                    self._judgeListOpt.setVisible(True)

                if showreviewerarea and (self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING):
                    self._judgereviewerListOpt.setVisible(True)

                if showeditorarea and (self._conf.getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING):
                    self._judgeeditorListOpt.setVisible(True)

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
        itemList.insert(0, i18nformat("""<a href=%s> _("Home")</a>""")%quoteattr(str(urlHandlers.UHConferenceDisplay.getURL(self._conf))) )
        return " &gt; ".join(itemList)

    def _getToolBarHTML(self):
        drawer=wcomponents.WConfTBDrawer(self._toolBar)
        return drawer.getHTML()

    def _applyConfDisplayDecoration( self, body ):
        drawer = wcomponents.WConfTickerTapeDrawer(self._conf, self._tz)
        frame = WConfDisplayFrame( self._getAW(), self._conf )

        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()

        onAirURL = wm.isOnAir(self._conf)
        if onAirURL:
            webcastURL = onAirURL
        else:
            wc = wm.getForthcomingWebcast(self._conf)
            webcastURL = wm.getWebcastServiceURL(wc)
        forthcomingWebcast = not onAirURL and wm.getForthcomingWebcast(self._conf)

        frameParams = {
            "confModifURL": urlHandlers.UHConferenceModification.getURL(self._conf),
            "logoURL": urlHandlers.UHConferenceLogo.getURL(self._conf),
            "currentURL": request.url,
            "nowHappening": drawer.getNowHappeningHTML(),
            "simpleTextAnnouncement": drawer.getSimpleText(),
            "onAirURL": onAirURL,
            "webcastURL": webcastURL,
            "forthcomingWebcast": forthcomingWebcast
        }
        if self._conf.getLogo():
            frameParams["logoURL"] = urlHandlers.UHConferenceLogo.getURL(self._conf)

        body = """
            <div class="confBodyBox clearfix">

                                    <div>
                                        <div></div>
                                        <div class="breadcrumps">%s</div>
                                        <div style="float:right;">%s</div>
                                    </div>
                <!--Main body-->
                                    <div class="mainContent">
                                        <div class="col2">
                                        %s
                                        </div>
                                  </div>
            </div>""" % (
                    self._getNavigationBarHTML(),
                    self._getToolBarHTML().strip(),
                    body)
        return frame.getHTML( self._sectionMenu, body, frameParams)

    def _getHeadContent( self ):
        #This is used for fetching the default css file for the conference pages
        #And also the modificated uploaded css

        dmgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        path = self._getBaseURL()
        timestamp = os.stat(__file__).st_mtime
        printCSS = """
        <link rel="stylesheet" type="text/css" href="%s/css/Conf_Basic.css?%d" >
            """ % (path, timestamp)
        confCSS = dmgr.getStyleManager().getCSS()

        if confCSS:
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s">"""%(confCSS.getURL())

        return printCSS

    def _applyDecoration( self, body ):
        body = self._applyConfDisplayDecoration( body )
        return WPConferenceBase._applyDecoration( self, body )


class WConfMetadata(wcomponents.WTemplated):
    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        v = wcomponents.WTemplated.getVars( self )
        minfo =  info.HelperMaKaCInfo.getMaKaCInfoInstance()

        v['site_name'] = minfo.getTitle()
        v['fb_config'] = minfo.getSocialAppConfig().get('facebook', {})

        if self._conf.getLogo():
            v['image'] = urlHandlers.UHConferenceLogo.getURL(self._conf)
        else:
            v['image'] = Config.getInstance().getSystemIconURL("indico_co")

        v['description'] = strip_ml_tags(self._conf.getDescription()[:500])
        return v


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

        vars["timezone"] = tz
        vars["confDateInterval"] = i18nformat("""_("from") %s _("to") %s""") % (
            format_date(adjusted_sDate, format='long'), format_date(adjusted_eDate, format='long'))
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
            vars["confDateInterval"] = format_date(adjusted_sDate, format='long')
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
            vars["confDateInterval"] = "%s-%s %s"%(adjusted_sDate.day, adjusted_eDate.day, format_date(adjusted_sDate, format='MMMM yyyy'))
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
        vars["body"] = self._body
        vars["supportEmail"] = ""
        vars["supportTelephone"] = ""

        sinfo = self._conf.getSupportInfo()

        p = {"menu": self._menu,
             "support_info": sinfo,
             "event": self._conf}
        vars["menu"] = WConfDisplayMenu(self._menu).getHTML(p)

        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf, False)
        format = dm.getFormat()
        vars["bgColorCode"] = format.getFormatOption("titleBgColor")["code"].replace("#","")
        vars["textColorCode"] = format.getFormatOption("titleTextColor")["code"].replace("#","")

        vars['searchBox']= ""
        vars["confId"] = self._conf.getId()
        vars["dm"] = dm
        extension_point("fillConferenceHeader", vars)
        return vars


class WConfDisplayMenu(wcomponents.WTemplated):

    def __init__(self, menu):
        wcomponents.WTemplated.__init__(self)
        self._menu = menu


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


class WPConfResetPassword(WPResetPasswordBase, WPConferenceDefaultDisplayBase):
    pass


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

    def _getMaterialHTML( self ):
        l = []
        for mat in self._conf.getAllMaterialList():
            if mat.getTitle() != _("Internal Page Files"):
                temp = wcomponents.WMaterialDisplayItem()
                url = urlHandlers.UHMaterialDisplay.getURL( mat )
                l.append( temp.getHTML( self._aw, mat, url ) )
        return l

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        vars["timezone"] = tz

        description = self._conf.getDescription()
        vars["description_html"] = isStringHTML(description)
        vars["description"] = description

        sdate, edate = self._conf.getAdjustedScreenStartDate(tz), self._conf.getAdjustedScreenEndDate(tz)
        fsdate, fedate = format_date(sdate, format='medium'), format_date(edate, format='medium')
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")

        vars["dateInterval"] = (fsdate, fstime, fedate, fetime)

        vars["location"] = None
        vars["address"] = None
        vars["room"] = None

        location = self._conf.getLocation()
        if location:
            vars["location"] = location.getName()
            vars["address"] = location.getAddress()

            room = self._conf.getRoom()
            if room and room.getName():
                roomLink = linking.RoomLinker().getHTMLLink(room, location)
                vars["room"] = roomLink

        vars["chairs"] = self._conf.getChairList()
        vars["material"] = self._getMaterialHTML()
        vars["conf"] = self._conf

        info = self._conf.getContactInfo()
        vars["moreInfo_html"] = isStringHTML(info)
        vars["moreInfo"] = info
        vars["actions"] = ''
        vars["isSubmitter"] = self._conf.getAccessController().canUserSubmit(self._aw.getUser()) or self._conf.canModify(self._aw)
        return vars


class WConfDetailsFull(WConfDetailsBase):
    pass


#---------------------------------------------------------------------------


class WConfDetails:

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getHTML( self, params ):
        return WConfDetailsFull( self._aw, self._conf ).getHTML( params )


class WPConferenceDisplay(WPConferenceDefaultDisplayBase):

    def _getBody(self, params):

        wc = WConfDetails(self._getAW(), self._conf)
        pars = {"modifyURL": urlHandlers.UHConferenceModification.getURL(self._conf),
                "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL,
                "contribModifyURLGen": urlHandlers.UHContributionModification.getURL,
                "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL,
                "materialURLGen": urlHandlers.UHMaterialDisplay.getURL}
        return wc.getHTML(pars)

    def _getHeadContent(self):
        printCSS = WPConferenceDefaultDisplayBase._getHeadContent(self)
        confMetadata = WConfMetadata(self._conf).getHTML()
        return printCSS + confMetadata

    def _getFooter(self):
        wc = wcomponents.WEventFooter(self._conf)
        return wc.getHTML()

    def _defineSectionMenu(self):
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

    def __init__(self,conf,user,toUsers):
        self._conf = conf
        self._from = user
        self._to = toUsers

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        if vars.get("from", None) is None :
            vars["FromName"] = self._from
        vars["fromUser"] = self._from
        vars["toUsers"] =  self._to
        if vars.get("postURL",None) is None :
            vars["postURL"]=urlHandlers.UHConferenceSendEmail.getURL(self._to)
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

class WPXSLConferenceDisplay(WPConferenceBase):
    """
    Use this class just to transform to XML
    """

    def __init__(self, rh, conference, view, type, params):
        WPConferenceBase.__init__(self, rh, conference)
        self._params = params
        self._view = view
        self._conf = conference
        self._type = type
        self._firstDay = params.get("firstDay")
        self._lastDay = params.get("lastDay")
        self._daysPerRow = params.get("daysPerRow")
        self._webcastadd = False
        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        if wm.isManager(self._getAW().getUser()):
            self._webcastadd = True

    def _getFooter(self):
        """
        """
        return ""

    def _getHTMLHeader(self):
        return ""

    def _applyDecoration(self, body):
        """
        """
        return body

    def _getHTMLFooter(self):
        return ""

    def _getBodyVariables(self):
        pars = { \
        "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
        "iCalURL": urlHandlers.UHConferenceToiCal.getURL(self._conf), \
        "cloneURL": urlHandlers.UHConfClone.getURL( self._conf ), \
        "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
        "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
        "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
        "materialURLGen": urlHandlers.UHMaterialDisplay.getURL, \
        "resourceURLGen": urlHandlers.UHFileAccess.getURL }

        pars.update({ 'firstDay' : self._firstDay, 'lastDay' : self._lastDay, 'daysPerRow' : self._daysPerRow })

        if self._webcastadd:
            urladdwebcast = urlHandlers.UHWebcastAddWebcast.getURL()
            urladdwebcast.addParam("eventid",self._conf.getId())
            pars['webcastAdminURL'] = urladdwebcast
        return pars

    def _getBody(self, params):
        body_vars = self._getBodyVariables()
        view = self._view
        outGen = outputGenerator(self._getAW())
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if styleMgr.existsXSLFile(self._view):
            if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                includeContribution = 1
            else:
                includeContribution = 0
            body = outGen.getFormattedOutput(self._rh, self._conf, styleMgr.getXSLPath(self._view), body_vars, 1,
                                             includeContribution, 1, 1, self._params.get("showSession", ""),
                                             self._params.get("showDate", ""))
            return body
        else:
            return _("Cannot find the %s stylesheet") % view

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._overviewOpt)


class WPTPLConferenceDisplay(WPXSLConferenceDisplay, object):
    """
    Overrides XSL related functions in WPXSLConferenceDisplay
    class and re-implements them using normal Indico templates.
    """

    def __init__(self, rh, conference, view, type, params):
        WPXSLConferenceDisplay.__init__(self, rh, conference, view, type, params)
        imagesBaseURL = Config.getInstance().getImagesBaseURL()
        self._types = {
            "pdf"   :{"mapsTo" : "pdf",   "imgURL" : os.path.join(imagesBaseURL, "pdf_small.png"),  "imgAlt" : "pdf file"},
            "doc"   :{"mapsTo" : "doc",   "imgURL" : os.path.join(imagesBaseURL, "word.png"),       "imgAlt" : "word file"},
            "docx"  :{"mapsTo" : "doc",   "imgURL" : os.path.join(imagesBaseURL, "word.png"),       "imgAlt" : "word file"},
            "ppt"   :{"mapsTo" : "ppt",   "imgURL" : os.path.join(imagesBaseURL, "powerpoint.png"), "imgAlt" : "powerpoint file"},
            "pptx"  :{"mapsTo" : "ppt",   "imgURL" : os.path.join(imagesBaseURL, "powerpoint.png"), "imgAlt" : "powerpoint file"},
            "xls"   :{"mapsTo" : "xls",   "imgURL" : os.path.join(imagesBaseURL, "excel.png"),      "imgAlt" : "excel file"},
            "xlsx"  :{"mapsTo" : "xls",   "imgURL" : os.path.join(imagesBaseURL, "excel.png"),      "imgAlt" : "excel file"},
            "sxi"   :{"mapsTo" : "odp",   "imgURL" : os.path.join(imagesBaseURL, "impress.png"),    "imgAlt" : "presentation file"},
            "odp"   :{"mapsTo" : "odp",   "imgURL" : os.path.join(imagesBaseURL, "impress.png"),    "imgAlt" : "presentation file"},
            "sxw"   :{"mapsTo" : "odt",   "imgURL" : os.path.join(imagesBaseURL, "writer.png"),     "imgAlt" : "writer file"},
            "odt"   :{"mapsTo" : "odt",   "imgURL" : os.path.join(imagesBaseURL, "writer.png"),     "imgAlt" : "writer file"},
            "sxc"   :{"mapsTo" : "ods",   "imgURL" : os.path.join(imagesBaseURL, "calc.png"),       "imgAlt" : "spreadsheet file"},
            "ods"   :{"mapsTo" : "ods",   "imgURL" : os.path.join(imagesBaseURL, "calc.png"),       "imgAlt" : "spreadsheet file"},
            "other" :{"mapsTo" : "other", "imgURL" : os.path.join(imagesBaseURL, "file_small.png"), "imgAlt" : "unknown type file"},
            "link"  :{"mapsTo" : "link",  "imgURL" : os.path.join(imagesBaseURL, "link.png"),       "imgAlt" : "link"}
        }

    def _getVariables(self, conf):
        wvars = {}
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        wvars['INCLUDE'] = '../include'

        wvars['accessWrapper'] = accessWrapper = self._rh._aw
        wvars['conf'] = conf
        if conf.getOwnerList():
            wvars['category'] = conf.getOwnerList()[0].getName()
        else:
            wvars['category'] = ''

        timezoneUtil = DisplayTZ(accessWrapper, conf)
        tz = timezoneUtil.getDisplayTZ()
        wvars['startDate'] = conf.getAdjustedStartDate(tz)
        wvars['endDate'] = conf.getAdjustedEndDate(tz)
        wvars['timezone'] = tz

        if conf.getParticipation().displayParticipantList() :
            wvars['participants']  = conf.getParticipation().getPresentParticipantListText()

        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        wvars['webcastOnAirURL'] = wm.isOnAir(conf)
        forthcomingWebcast = wm.getForthcomingWebcast(conf)
        wvars['forthcomingWebcast'] = forthcomingWebcast
        if forthcomingWebcast:
            wvars['forthcomingWebcastURL'] = wm.getWebcastServiceURL(forthcomingWebcast)

        wvars['files'] = {}
        lectureTitles = ['part%s' % nr for nr in xrange(1, 11)]
        materials, lectures, minutesText = [], [], []
        for material in conf.getAllMaterialList():
            if not material.canView(accessWrapper):
                continue
            if material.getTitle() in lectureTitles:
                lectures.append(material)
            elif material.getTitle() != "Internal Page Files":
                materials.append(material)

        wvars['materials'] = materials
        wvars['minutesText'] = minutesText
        byTitleNumber = lambda x, y: int(x.getTitle()[4:]) - int(y.getTitle()[4:])
        wvars['lectures'] = sorted(lectures, cmp=byTitleNumber)

        if (conf.getType() in ("meeting", "simple_event")
                and conf.getParticipation().isAllowedForApplying()
                and conf.getStartDate() > nowutc()
                and not conf.getParticipation().isFull()):
            wvars['registrationOpen'] = True
        evaluation = conf.getEvaluation()
        if evaluation.isVisible() and evaluation.inEvaluationPeriod() and evaluation.getNbOfQuestions() > 0:
            wvars['evaluationLink'] = urlHandlers.UHConfEvaluationDisplay.getURL(conf)
        wvars['supportEmailCaption'] = conf.getSupportInfo().getCaption()

        wvars['types'] = self._types

        wvars['entries'] = []
        confSchedule = conf.getSchedule()
        showSession = self._params.get("showSession","all")
        detailLevel = self._params.get("detailLevel", "contribution")
        showDate = self._params.get("showDate", "all")
        # Filter by day
        if showDate == "all":
            entrylist = confSchedule.getEntries()
        else:
            entrylist = confSchedule.getEntriesOnDay(timezone(tz).localize(stringToDate(showDate)))
        # Check entries filters and access rights
        for entry in entrylist:
            sessionCand = entry.getOwner().getOwner()
            # Filter by session
            if isinstance(sessionCand, Session) and (showSession != "all" and sessionCand.getId() != showSession):
                continue
            # Hide/Show contributions
            if isinstance(entry.getOwner(), Contribution) and detailLevel != "contribution":
                continue
            if entry.getOwner().canView(accessWrapper):
                if type(entry) is schedule.BreakTimeSchEntry:
                    newItem = entry
                else:
                    newItem = entry.getOwner()
                wvars['entries'].append(newItem)

        wvars['entries'].sort(key=lambda entry: entry.getEndDate(), reverse=True)
        wvars['entries'].sort(key=lambda entry: entry.getStartDate())

        wvars["pluginDetails"] = "".join(self._notify('eventDetailBanner', self._conf))
        pluginDetailsSessionContribs = {}
        self._notify('detailSessionContribs', self._conf, pluginDetailsSessionContribs)
        wvars["pluginDetailsSessionContribs"] = pluginDetailsSessionContribs
        wvars["daysPerRow"] = self._daysPerRow
        wvars["firstDay"] = self._firstDay
        wvars["lastDay"] = self._lastDay
        wvars["currentUser"] = self._rh._aw.getUser()
        wvars["reportNumberSystems"] = Config.getInstance().getReportNumberSystems()

        return wvars

    def _getMaterialFiles(self, material):
        files = []
        for res in material.getResourceList():
            if isinstance(res, LocalFile):
                fileType = res.getFileType().lower()
                try:
                    fileType = self._types[fileType]["mapsTo"]
                except KeyError:
                    fileType = "other"
                filename = res.getName() or res.getFileName()
                fileURL = str(urlHandlers.UHFileAccess.getURL(res))
            else:
                filename, fileType, fileURL = str(res.getName() or res.getURL()), "link", str(res.getURL())
            files.append({'id': res.getId(),
                          'name': filename,
                          'description': res.getDescription(),
                          'type': fileType,
                          'url': fileURL,
                          'pdfConversionStatus': res.getPDFConversionStatus()})
        return files

    def _getItemType(self, item):
        itemClass = item.__class__.__name__
        if itemClass == 'BreakTimeSchEntry':
            return 'Break'
        elif itemClass == 'SessionSlot':
            return 'Session'
        elif itemClass == 'AcceptedContribution':
            return 'Contribution'
        else:
            # return Conference, Contribution or SubContribution
            return itemClass

    def _generateMaterialList(self, obj):
        """
        Generates a list containing all the materials, with the
        corresponding Ids for those that already exist
        """
        # yes, this may look a bit redundant, but materialRegistry isn't
        # bound to a particular target
        materialRegistry = obj.getMaterialRegistry()
        return materialRegistry.getMaterialList(obj.getConference())

    def _extractInfoForButton(self, item):
        info = {}
        for key in ['sessId', 'slotId', 'contId', 'subContId']:
            info[key] = 'null'
        info['confId'] = self._conf.getId()

        itemType = self._getItemType(item)
        info['uploadURL'] = 'Indico.Urls.UploadAction.%s' % itemType.lower()

        if itemType != 'Session':
            info['materialList'] = self._generateMaterialList(item)
        else:
            info['materialList'] = self._generateMaterialList(item.getSession())

        if itemType == 'Conference':
            info['parentProtection'] = item.getAccessController().isProtected()
            if item.canModify(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHConferenceModification.getURL(item)
                info["minutesLink"] = True
                info["materialLink"] = True
                info["cloneLink"] = urlHandlers.UHConfClone.getURL(item)
            if item.getAccessController().canUserSubmit(self._rh._aw.getUser()):
                info["minutesLink"] = True
                info["materialLink"] = True

        elif itemType == 'Session':
            session = item.getSession()
            info['parentProtection'] = session.getAccessController().isProtected()
            if session.canModify(self._rh._aw) or session.canCoordinate(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHSessionModification.getURL(item)
            info['slotId'] = item.getId()
            info['sessId'] = session.getId()
            if session.canModify(self._rh._aw) or session.canCoordinate(self._rh._aw):
                info["minutesLink"] = True
                info["materialLink"] = True
                url = urlHandlers.UHSessionModifSchedule.getURL(session)
                ttLink = "%s#%s.s%sl%s" % (url, session.getStartDate().strftime('%Y%m%d'), session.getId(), info['slotId'])
                info["sessionTimetableLink"] = ttLink

        elif itemType == 'Contribution':
            info['parentProtection'] = item.getAccessController().isProtected()
            if item.canModify(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHContributionModification.getURL(item)
            if item.canModify(self._rh._aw) or item.canUserSubmit(self._rh._aw.getUser()):
                info["minutesLink"] = True
                info["materialLink"] = True
            info["contId"] = item.getId()
            owner = item.getOwner()
            if self._getItemType(owner) == 'Session':
                info['sessId'] = owner.getId()

        elif itemType == 'SubContribution':
            info['parentProtection'] = item.getContribution().getAccessController().isProtected()
            if item.canModify(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHSubContributionModification.getURL(item)
            if item.canModify(self._rh._aw) or item.canUserSubmit(self._rh._aw.getUser()):
                info["minutesLink"] = True
                info["materialLink"] = True
            info["subContId"] = item.getId()
            info["contId"] = item.getContribution().getId()
            owner = item.getOwner()
            if self._getItemType(owner) == 'Session':
                info['sessId'] = owner.getId()

        return info

    def _getHTMLHeader( self ):
        return WPConferenceBase._getHTMLHeader(self)

    def _getHeadContent( self ):
        config = Config.getInstance()
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        htdocs = config.getHtdocsDir()
        baseurl = self._getBaseURL()
        # First include the default Indico stylesheet
        timestamp = os.stat(__file__).st_mtime
        styleText = """<link rel="stylesheet" href="%s/css/%s?%d">\n""" % \
            (baseurl, Config.getInstance().getCssStylesheetName(), timestamp)
        # Then the common event display stylesheet
        if os.path.exists("%s/css/events/common.css" % htdocs):
            styleText += """        <link rel="stylesheet" href="%s/css/events/common.css?%d">\n""" % (baseurl,
                                                                                                       timestamp)

        # And finally the specific display stylesheet
        if styleMgr.existsCSSFile(self._view):
            cssPath = os.path.join(baseurl, 'css', 'events', styleMgr.getCSSFilename(self._view))
            styleText += """        <link rel="stylesheet" href="%s?%d">\n""" % (cssPath, timestamp)

        confMetadata = WConfMetadata(self._conf).getHTML()

        mathJax = render('js/mathjax.config.js.tpl') + \
                  '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url) for url in
                             self._asset_env['mathjax_js'].urls()])

        return styleText + confMetadata + mathJax

    def _getFooter( self ):
        """
        """
        wc = wcomponents.WEventFooter(self._conf)
        p = {"modificationDate":format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),"subArea": self._getSiteArea(),"dark":True}
        if Config.getInstance().getShortEventURL():
            id=self._conf.getUrlTag().strip()
            if not id:
                id = self._conf.getId()
            p["shortURL"] =  Config.getInstance().getShortEventURL() + id
        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        if self._type == "simple_event":
            wc = wcomponents.WMenuSimpleEventHeader( self._getAW(), self._conf )
        elif self._type == "meeting":
            wc = wcomponents.WMenuMeetingHeader( self._getAW(), self._conf )
        else:
            wc = wcomponents.WMenuConferenceHeader( self._getAW(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(),\
                             "currentView": self._view,\
                             "type": self._type,\
                             "selectedDate": self._params.get("showDate",""),\
                             "selectedSession": self._params.get("showSession",""),\
                             "detailLevel": self._params.get("detailLevel",""),\
                             "filterActive": self._params.get("filterActive",""),\
                            "dark": True } )

    def getCSSFiles(self):
        # flatten returned list

        return WPConferenceBase.getCSSFiles(self) + \
               sum(self._notify('injectCSSFiles'), [])

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
        modules += sum(self._notify('injectJSFiles'), [])
        return modules

    def _applyDecoration( self, body ):
        """
        """
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
                return WPrintPageFrame().getHTML({"content":body})
        return WPConferenceBase._applyDecoration(self, body)

    def _getHTMLFooter( self ):
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
            return ""
        return WPConferenceBase._getHTMLFooter(self)

    def _getBody(self, params):
        """Return main information about the event."""

        if self._view != 'xml':
            vars = self._getVariables(self._conf)
            vars['getTime'] = lambda date : format_time(date.time(), format="HH:mm")
            vars['isTime0H0M'] = lambda date : (date.hour, date.minute) == (0,0)
            vars['getDate'] = lambda date : format_date(date, format='yyyy-MM-dd')
            vars['prettyDate'] = lambda date : format_date(date, format='full')
            vars['prettyDuration'] = MaKaC.common.utils.prettyDuration
            vars['parseDate'] = MaKaC.common.utils.parseDate
            vars['isStringHTML'] = MaKaC.common.utils.isStringHTML
            vars['getMaterialFiles'] = lambda material : self._getMaterialFiles(material)
            vars['extractInfoForButton'] = lambda item : self._extractInfoForButton(item)
            vars['getItemType'] = lambda item : self._getItemType(item)
            vars['getLocationInfo'] = MaKaC.common.utils.getLocationInfo
            vars['dumps'] = json.dumps
            vars['timedelta'] = timedelta
        else:
            outGen = outputGenerator(self._rh._aw)
            varsForGenerator = self._getBodyVariables()
            vars = {}
            vars['xml'] = outGen._getBasicXML(self._conf, varsForGenerator, 1, 1, 1, 1)

        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if styleMgr.existsTPLFile(self._view):
            fileName = os.path.splitext(styleMgr.getTemplateFilename(self._view))[0]
            body = wcomponents.WTemplated(os.path.join("events", fileName)).getHTML(vars)
        else:
            return _("Template could not be found.")
        return body


class WPrintPageFrame (wcomponents.WTemplated):
    pass


class WText(wcomponents.WTemplated):

    def __init__(self):
        wcomponents.WTemplated("events/Text")


class WConfDisplayBodyBase(wcomponents.WTemplated):

    def _getTitle(self):
        default_caption = displayMgr.SystemLinkData().getLinkData()[self._linkname]["caption"]
        caption = self._conf.getDisplayMgr().getMenu().getLinkByName(self._linkname).getCaption()
        return _(caption) if caption == default_caption else caption


class WConfProgram(WConfDisplayBodyBase):

    _linkname = "programme"

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def buildTrackData(self, track):
        """
        Returns a dict representing the data of the track and its Sub-tracks
        should it have any.
        """
        description = track.getDescription()

        formattedTrack = {
            'title': track.getTitle(),
            'description': description
        }

        if track.getConference().getAbstractMgr().isActive() and \
           track.getConference().hasEnabledSection("cfa") and \
           track.canCoordinate(self._aw):

            if track.getConference().canModify(self._aw):
                formattedTrack['url'] = urlHandlers.UHTrackModification.getURL(track)
            else:
                formattedTrack['url'] = urlHandlers.UHTrackModifAbstracts.getURL(track)

        return formattedTrack

    def getVars(self):
        pvars = wcomponents.WTemplated.getVars(self)
        pvars["body_title"] = self._getTitle()
        pvars['description'] = self._conf.getProgramDescription()
        pvars['program'] = [self.buildTrackData(t) for t in self._conf.getTrackList()]
        pvars['pdf_url'] = urlHandlers.UHConferenceProgramPDF.getURL(self._conf)

        return pvars


class WPConferenceProgram(WPConferenceDefaultDisplayBase):

    def _getBody(self, params):
        wc = WConfProgram(self._getAW(), self._conf)
        return wc.getHTML()

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._programOpt)


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


class WConferenceTimeTable(WConfDisplayBodyBase):

    _linkname = "timetable"

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        tz = DisplayTZ(self._aw, self._conf).getDisplayTZ()
        sf = schedule.ScheduleToJson.process(self._conf.getSchedule(),
                                             tz, self._aw,
                                             useAttrCache=True,
                                             hideWeekends=True)
        # TODO: Move to beginning of file when proved useful
        try:
            import ujson
            jsonf = ujson.encode
        except ImportError:
            jsonf = json.dumps
        wvars["ttdata"] = jsonf(sf)
        eventInfo = fossilize(self._conf, IConferenceEventInfoFossil, tz=tz)
        eventInfo['isCFAEnabled'] = self._conf.getAbstractMgr().isActive()
        wvars['eventInfo'] = eventInfo
        wvars['timetableLayout'] = wvars.get('ttLyt', '')
        return wvars


class WPConferenceTimeTable(WPConferenceDefaultDisplayBase):
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
        baseurl = self._getBaseURL()
        timestamp = os.stat(__file__).st_mtime
        return """
                 %s
                 <link rel="stylesheet" type="text/css" href="%s/css/timetable.css?%d">
                """ % ( headContent, baseurl, timestamp)


class WPMeetingTimeTable( WPTPLConferenceDisplay ):

    def getJSFiles(self):
        return WPXSLConferenceDisplay.getJSFiles(self) + \
               self._includeJSPackage('Timetable')

    def _getBody( self, params ):
        wc = WConferenceTimeTable( self._conf, self._getAW()  )
        return wc.getHTML(params)

class WPConferenceModifBase( main.WPMainBase, OldObservable ):

    _userData = ['favorite-user-ids']

    def __init__( self, rh, conference ):
        main.WPMainBase.__init__( self, rh )
        self._navigationTarget = self._conf = conference

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
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())) } )

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

        self._regFormMenuItem = wcomponents.SideMenuItem(_("Registration"),
            urlHandlers.UHConfModifRegForm.getURL( self._conf ))
        self._generalSection.addItem( self._regFormMenuItem)

        self._abstractMenuItem = wcomponents.SideMenuItem(_("Abstracts"),
            urlHandlers.UHConfModifCFA.getURL( self._conf ))
        self._generalSection.addItem( self._abstractMenuItem)

        self._contribListMenuItem = wcomponents.SideMenuItem(_("Contributions"),
            urlHandlers.UHConfModifContribList.getURL( self._conf ))
        self._generalSection.addItem( self._contribListMenuItem)

        self._reviewingMenuItem = wcomponents.SideMenuItem(_("Paper Reviewing"),
            urlHandlers.UHConfModifReviewingAccess.getURL( target = self._conf ) )
        self._generalSection.addItem( self._reviewingMenuItem)

        self._participantsMenuItem = wcomponents.SideMenuItem(_("Participants"),
            urlHandlers.UHConfModifParticipants.getURL( self._conf ) )
        self._generalSection.addItem( self._participantsMenuItem)

        self._evaluationMenuItem = wcomponents.SideMenuItem(_("Evaluation"),
            urlHandlers.UHConfModifEvaluation.getURL( self._conf ) )
        self._generalSection.addItem( self._evaluationMenuItem)

        self._pluginsDictMenuItem = {}
        self._notify('fillManagementSideMenu', self._pluginsDictMenuItem)
        for element in self._pluginsDictMenuItem.values():
            try:
                self._generalSection.addItem( element)
            except Exception, e:
                Logger.get('Conference').error("Exception while trying to access the plugin elements of the side menu: %s" %str(e))

        self._sideMenu.addSection(self._generalSection)

        # The section containing all advanced options
        self._advancedOptionsSection = wcomponents.SideMenuSection(_("Advanced options"))

        self._listingsMenuItem = wcomponents.SideMenuItem(_("Lists"),
            urlHandlers.UHConfAllSpeakers.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._listingsMenuItem)

        self._ACMenuItem = wcomponents.SideMenuItem(_("Protection"),
            urlHandlers.UHConfModifAC.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._ACMenuItem)

        self._toolsMenuItem = wcomponents.SideMenuItem(_("Tools"),
            urlHandlers.UHConfModifTools.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._toolsMenuItem)

        self._layoutMenuItem = wcomponents.SideMenuItem(_("Layout"),
            urlHandlers.UHConfModifDisplay.getURL(self._conf))
        self._advancedOptionsSection.addItem( self._layoutMenuItem)

        self._logMenuItem = wcomponents.SideMenuItem(_("Logs"),
            urlHandlers.UHConfModifLog.getURL( self._conf ) )
        self._advancedOptionsSection.addItem( self._logMenuItem)

        self._sideMenu.addSection(self._advancedOptionsSection)

        #we decide which side menu item appear and which don't
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCReviewingStaff

        canModify = self._conf.canModify(self._rh.getAW())
        isReviewingStaff = RCReviewingStaff.hasRights(self._rh)
        isPRM = RCPaperReviewManager.hasRights(self._rh)
        #isAM = RCAbstractManager.hasRights(self._rh)
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

        #if not (self._conf.hasEnabledSection("cfa") and (canModify or isAM)):
        if not (self._conf.hasEnabledSection("cfa") and (canModify)):
            self._abstractMenuItem.setVisible(False)

        if not (canModify or isPRM):
            self._contribListMenuItem.setVisible(False)

        if not (self._conf.hasEnabledSection("regForm") and (canModify or isRegistrar)):
            self._regFormMenuItem.setVisible(False)

        if not (self._conf.getType() == "conference" and (canModify or isReviewingStaff)):
            self._reviewingMenuItem.setVisible(False)
        else: #reviewing tab is enabled
            if isReviewingStaff and not canModify:
                self._reviewingMenuItem.setVisible(True)
        # For now we don't want the paper reviewing to be displayed
        #self._reviewingMenuItem.setVisible(False)

        #we hide the Advanced Options section if it has no items
        if not self._advancedOptionsSection.hasVisibleItems():
            self._advancedOptionsSection.setVisible(False)

        # we disable the Participants section for events of type conference
        if self._conf.getType() == 'conference':
            self._participantsMenuItem.setVisible(False)

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
        self._tabAbstractList = self._tabCtrl.newTab( "abstractList", _("List of Abstracts"), urlHandlers.UHConfAbstractList.getURL( self._conf ) )
        self._tabBOA = self._tabCtrl.newTab("boa", _("Book of Abstracts Setup"), urlHandlers.UHConfModAbstractBook.getURL(self._conf))
        self._tabCFAR = self._tabCtrl.newTab("reviewing", _("Reviewing"), urlHandlers.UHAbstractReviewingSetup.getURL(self._conf))

        # Create subtabs for the reviewing
        self._subTabARSetup = self._tabCFAR.newSubTab( "revsetup", _("Settings"),\
                    urlHandlers.UHAbstractReviewingSetup.getURL(self._conf))
        self._subTabARTeam = self._tabCFAR.newSubTab( "revteam", _("Team"),\
                    urlHandlers.UHAbstractReviewingTeam.getURL(self._conf))
        self._subTabARNotifTpl = self._tabCFAR.newSubTab( "notiftpl", _("Notification templates"),\
                    urlHandlers.UHAbstractReviewingNotifTpl.getURL(self._conf))

        if not self._conf.hasEnabledSection("cfa"):
            self._tabBOA.disable()
            self._tabCFA.disable()
            self._tabAbstractList.disable()
            self._tabCFAPreview.disable()
            self._tabCFAR.disable()

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


class WConfModifMainData(wcomponents.WTemplated):

    def __init__(self,conference,mfRegistry,ct,rh):
        self._conf=conference
        self.__mfr=mfRegistry
        self._ct=ct
        self._rh = rh

    def _getChairPersonsList(self):
        result = fossilize(self._conf.getChairList())
        for chair in result:
            av = AvatarHolder().match({"email": chair['email']},
                                  searchInAuthenticators=False, exact=True)
            chair['showManagerCB'] = True
            chair['showSubmitterCB'] = True
            if not av:
                if self._conf.getPendingQueuesMgr().getPendingConfSubmittersByEmail(chair['email']):
                    chair['showSubmitterCB'] = False
            elif (av[0] in self._conf.getAccessController().getSubmitterList()):
                chair['showSubmitterCB'] = False
            if (av and self._conf.getAccessController().canModify(av[0])) or chair['email'] in self._conf.getAccessController().getModificationEmail():
                chair['showManagerCB'] = False
        return result

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        type = vars["type"]
        vars["defaultStyle"] = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getDefaultStyle()
        vars["visibility"] = self._conf.getVisibility()
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
        vars["supportEmailCaption"] = self._conf.getSupportInfo().getCaption()
        vars["supportEmail"] = i18nformat("""--_("not set")--""")
        if self._conf.getSupportInfo().hasEmail():
            vars["supportEmail"] = self.htmlText(self._conf.getSupportInfo().getEmail())
        typeList = []
        for type in self._conf.getContribTypeList():
            typeList.append("""<input type="checkbox" name="types" value="%s"><a href="%s">%s</a><br>
<table><tr><td width="30"></td><td><font><pre>%s</pre></font></td></tr></table>"""%( \
                type.getId(), \
                str(urlHandlers.UHConfEditContribType.getURL(type)), \
                type.getName(), \
                type.getDescription()))
        vars["typeList"] = "".join(typeList)
        #------------------------------------------------------
        vars["reportNumbersTable"]=wcomponents.WReportNumbersTable(self._conf).getHTML()
        vars["eventType"] = self._conf.getType()
        vars["keywords"] = self._conf.getKeywords()
        vars["shortURLBase"] = Config.getInstance().getShortEventURL()
        vars["shortURLTag"] = self._conf.getUrlTag()
        vars["screenDatesURL"] = urlHandlers.UHConfScreenDatesEdit.getURL(self._conf)
        ssdate = format_datetime(self._conf.getAdjustedScreenStartDate(), format='EEEE d MMMM yyyy H:mm')
        if self._conf.getScreenStartDate() == self._conf.getStartDate():
            ssdate += i18nformat(""" <i> _("(normal)")</i>""")
        else:
            ssdate += i18nformat(""" <font color='red'>_("(modified)")</font>""")
        sedate = format_datetime(self._conf.getAdjustedScreenEndDate(), format='EEEE d MMMM yyyy H:mm')
        if self._conf.getScreenEndDate() == self._conf.getEndDate():
            sedate += i18nformat(""" <i> _("(normal)")</i>""")
        else:
            sedate += i18nformat(""" <font color='red'> _("(modified)")</font>""")
        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
        vars["screenDates"] = "%s -> %s" % (ssdate, sedate)
        vars["timezoneList"] = TimezoneRegistry.getList()
        vars["chairpersons"] = self._getChairPersonsList()

        loc = self._conf.getLocation()
        room = self._conf.getRoom()
        vars["currentLocation"] = { 'location': loc.getName() if loc else "",
                                    'room': room.name if room else "",
                                    'address': loc.getAddress() if loc else "" }
        return vars

class WPConferenceModificationClosed( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

    def _getPageContent( self, params ):
        message = _("The event is currently locked and you cannot modify it in this status. ")
        if self._conf.canModify(self._rh.getAW()):
            message += _("If you unlock the event, you will be able to modify its details again.")
        return wcomponents.WClosed().getHTML({"message": message,
                                             "postURL": urlHandlers.UHConferenceOpen.getURL(self._conf),
                                             "showUnlockButton": self._conf.canModify(self._rh.getAW()),
                                             "unlockButtonCaption": _("Unlock event")})


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
        vars["conf_start_date"]=self.htmlText(format_datetime(csd, format='EEEE d MMMM yyyy H:mm'))
        vars["conf_end_date"]=self.htmlText(format_datetime(ced, format='EEEE d MMMM yyyy H:mm'))
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
        vis = [ i18nformat("""<option value="0" %s> _("Nowhere")</option>""") % selected]
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
        vis.append( i18nformat("""<option value="999" %s> _("Everywhere")</option>""") % selected)
        vis.reverse()
        return "".join(vis)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        navigator = ""
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        type = self._conf.getType()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(self._conf.getTimezone())
        styles=styleMgr.getExistingStylesForEventType(type)
        styleoptions = ""
        defStyle = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getDefaultStyle()
        if defStyle not in styles:
            defStyle = ""
        for styleId in styles:
            if styleId == defStyle or (defStyle == "" and styleId == "static"):
                selected = "selected"
            else:
                selected = ""
            styleoptions += "<option value=\"%s\" %s>%s</option>" % (styleId,selected,styleMgr.getStyleName(styleId))
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

        vars["supportCaption"] = quoteattr(self._conf.getSupportInfo().getCaption())
        vars["supportEmail"] = quoteattr( self._conf.getSupportInfo().getEmail() )
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
            "postURL": urlHandlers.UHConfPerformDataModif.getURL(self._conf),
            "type": params.get("type")
        }
        return p.getHTML( pars )


class WConfModifScheduleGraphic(wcomponents.WTemplated):

    def __init__(self, conference, customLinks, **params):
        wcomponents.WTemplated.__init__(self, **params)
        self._conf = conference
        self._customLinks = customLinks

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

        vars['ttdata'] = schedule.ScheduleToJson.process(self._conf.getSchedule(), tz, None,
                                                         days = None, mgmtMode = True)

        vars['customLinks'] = self._customLinks

        eventInfo = fossilize(self._conf, IConferenceEventInfoFossil, tz = tz)
        eventInfo['isCFAEnabled'] = self._conf.getAbstractMgr().isActive()
        vars['eventInfo'] = eventInfo

        return vars

class WPConfModifScheduleGraphic( WPConferenceModifBase ):

    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._contrib = None

    def _setActiveSideMenuItem( self ):
        self._timetableMenuItem.setActive()

    def getJSFiles(self):
        pluginJSFiles = {"paths" : []}
        self._notify("includeTimetableJSFiles", pluginJSFiles)
        return WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSPackage('Timetable') + \
               pluginJSFiles['paths']

    def _getSchedule(self):
        self._customLinks = {}
        self._notify("customTimetableLinks", self._customLinks)
        return WConfModifScheduleGraphic( self._conf, self._customLinks )

    def _getTTPage( self, params ):
        wc = self._getSchedule()
        return wc.getHTML(params)

    def _getHeadContent(self):

        baseurl = self._getBaseURL()
        pluginCSSFiles = {"paths": []}
        self._notify("includeTimetableCSSFiles", pluginCSSFiles)
        return ".".join(["""<link rel="stylesheet" href="%s">""" % path for path in pluginCSSFiles['paths']])

    def _getPageContent(self, params):
        return self._getTTPage(params)

#------------------------------------------------------------------------------
class WPConfModifSchedule( WPConferenceModifBase ):

    def _setActiveTab( self ):
        self._tabSchedule.setActive()

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

    def __init__(self, conference, eventType, user):
        self.__conf = conference
        self._eventType = eventType
        self.__user = user

    def getHTML( self, params ):
        ac = wcomponents.WConfAccessControlFrame().getHTML( self.__conf,\
                                            params["setVisibilityURL"])
        dc = ""
        if not self.__conf.isProtected():
            dc = "<br>%s"%wcomponents.WDomainControlFrame( self.__conf ).getHTML()

        mc = wcomponents.WConfModificationControlFrame().getHTML( self.__conf) + "<br>"

        if self._eventType == "conference":
            rc = wcomponents.WConfRegistrarsControlFrame().getHTML(self.__conf) + "<br>"
        else:
            rc = ""

        tf = ""
        if self._eventType in ["conference", "meeting"]:
            tf = "<br>%s" % wcomponents.WConfProtectionToolsFrame(self.__conf).getHTML()
        cr = ""
        if self._eventType == "conference":
            cr = "<br>%s" % WConfModifACSessionCoordinatorRights(self.__conf).getHTML()

        return """<br><table width="100%%" class="ACtab"><tr><td>%s%s%s%s%s%s<br></td></tr></table>""" % (mc, rc, ac, dc, tf, cr)


class WPConfModifAC(WPConferenceModifBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType = "conference"
        if self._rh.getWebFactory() is not None:
            self._eventType = self._rh.getWebFactory().getId()
        self._user = self._rh._getUser()

    def _setActiveSideMenuItem(self):
        self._ACMenuItem.setActive()

    def _getPageContent(self, params):
        wc = WConfModifAC(self._conf, self._eventType, self._user)
        p = {
            'setVisibilityURL': urlHandlers.UHConfSetVisibility.getURL(self._conf)
        }
        return wc.getHTML(p)

class WPConfModifToolsBase(WPConferenceModifBase):

    def _setActiveSideMenuItem(self):
        self._toolsMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabAlarms = self._tabCtrl.newTab("alarms", _("Alarms"), \
                urlHandlers.UHConfDisplayAlarm.getURL(self._conf))
        self._tabCloneEvent = self._tabCtrl.newTab("clone", _("Clone Event"), \
                urlHandlers.UHConfClone.getURL(self._conf))
        self._tabPosters = self._tabCtrl.newTab("posters", _("Posters"), \
                urlHandlers.UHConfModifPosterPrinting.getURL(self._conf))
        self._tabBadges = self._tabCtrl.newTab("badges", _("Badges/Tablesigns"), \
                urlHandlers.UHConfModifBadgePrinting.getURL(self._conf))
        self._tabClose = self._tabCtrl.newTab("close", _("Lock"), \
                urlHandlers.UHConferenceClose.getURL(self._conf))
        self._tabDelete = self._tabCtrl.newTab("delete", _("Delete"), \
                urlHandlers.UHConfDeletion.getURL(self._conf))
        self._tabMatPackage = self._tabCtrl.newTab("matPackage", _("Material Package"), \
                urlHandlers.UHConfModFullMaterialPackage.getURL(self._conf))
        if Config.getInstance().getOfflineStore():
            self._tabOffline = self._tabCtrl.newTab("offline", _("Offline version"),
                                                    urlHandlers.UHConfOffline.getURL(self._conf))

        self._setActiveTab()

        wf = self._rh.getWebFactory()
        if wf:
            wf.customiseToolsTabCtrl(self._tabCtrl)

    def _getPageContent(self, params):
        self._createTabCtrl()

        html = wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))
        return html

    def _setActiveTab(self):
        pass

    def _getTabContent(self, params):
        return "nothing"


class WPConfClosing(WPConfModifToolsBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType = "conference"
        if self._rh.getWebFactory() is not None:
            self._eventType = self._rh.getWebFactory().getId()

    def _setActiveTab(self):
        self._tabClose.setActive()

    def _getTabContent(self, params):
        msg = {'challenge': _("Are you sure that you want to lock the event?"),
               'target': self._conf.getTitle(),
               'subtext': _("Note that if you lock the event, you will not be able to change its details any more. "
                "Only the creator of the event or an administrator of the system / category can unlock an event."),
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
                          urlHandlers.UHConferenceClose.getURL(self._conf),
                          {},
                          severity="warning",
                          confirmButtonCaption=_("Yes, lock this event"),
                          cancelButtonCaption=_("No"))


class WPConfDeletion(WPConfModifToolsBase):

    def _setActiveTab(self):
        self._tabDelete.setActive()

    def _getTabContent(self, params):
        msg = {'challenge': _("Are you sure that you want to delete the conference?"),
               'target': self._conf.getTitle(),
               'subtext': _("Note that if you delete the conference, all the items below it will also be deleted")
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
                          urlHandlers.UHConfDeletion.getURL(self._conf),
                          {},
                          severity="danger",
                          confirmButtonCaption=_("Yes, I am sure"),
                          cancelButtonCaption=_("No"))


class WPConfCloneConfirm(WPConfModifToolsBase):

    def __init__(self, rh, conf, nbClones):
        WPConfModifToolsBase.__init__(self, rh, conf)
        self._nbClones = nbClones

    def _setActiveTab(self):
        self._tabCloneEvent.setActive()

    def _getTabContent(self, params):

        msg = _("This action will create {0} new events. Are you sure you want to proceed").format(self._nbClones)

        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfPerformCloning.getURL(self._conf)
        params = self._rh._getRequestParams()
        for key in params.keys():
            url.addParam(key, params[key])
        return wc.getHTML( msg, \
                        url, {}, True, \
                        confirmButtonCaption=_("Yes"), cancelButtonCaption=_("No"))

#---------------------------------------------------------------------------


class WPConferenceModifParticipantBase(WPConferenceModifBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabParticipantsSetup = self._tabCtrl.newTab("participantsetup", _("Setup"), urlHandlers.UHConfModifParticipantsSetup.getURL(self._conf))
        self._tabParticipantsList = self._tabCtrl.newTab("participantsList", _("Participants"), urlHandlers.UHConfModifParticipants.getURL(self._conf))
        self._tabStatistics = self._tabCtrl.newTab("statistics", _("Statistics"), urlHandlers.UHConfModifParticipantsStatistics.getURL(self._conf))
        if self._conf.getParticipation().getPendingParticipantList() and nowutc() < self._conf.getStartDate():
            self._tabParticipantsPendingList = self._tabCtrl.newTab("pendingList", _("Pending"), urlHandlers.UHConfModifParticipantsPending.getURL(self._conf), className="pendingTab")
        if self._conf.getParticipation().getDeclinedParticipantList():
            self._tabParticipantsDeclinedList = self._tabCtrl.newTab("declinedList", _("Declined"), urlHandlers.UHConfModifParticipantsDeclined.getURL(self._conf))

        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()

        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSPackage('Display')

    def _setActiveSideMenuItem(self):
        self._participantsMenuItem.setActive()

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveTab(self):
        pass


class WConferenceParticipant(wcomponents.WTemplated):

    def __init__(self, conference, participant):
        self._conf = conference
        self._participant = participant

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["conference"] = self._conf
        vars["participant"] = self._participant
        return vars


class WConferenceParticipantPending(wcomponents.WTemplated):

    def __init__(self, conference, id, pending):
        self._conf = conference
        self._id = id
        self._pending = pending

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["conference"] = self._conf
        vars["id"] = self._id
        vars["pending"] = self._pending
        return vars


class WConferenceParticipantsSetup(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confId"] = self._conf.getId()
        vars["isObligatory"] = self._conf.getParticipation().isObligatory()
        vars["allowDisplay"] = self._conf.getParticipation().displayParticipantList()
        vars["addedInfo"] = self._conf.getParticipation().isAddedInfo()
        vars["allowForApply"] = self._conf.getParticipation().isAllowedForApplying()
        vars["autoAccept"] = self._conf.getParticipation().isAutoAccept()
        vars["numMaxParticipants"] = self._conf.getParticipation().getNumMaxParticipants()
        vars["notifyMgrNewParticipant"] = self._conf.getParticipation().isNotifyMgrNewParticipant()
        return vars


class WPConfModifParticipantsSetup(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsSetup.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsSetup(self._conf)
        return p.getHTML(params)


class WConferenceParticipants(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")

        vars["participantsAction"] = str(urlHandlers.UHConfModifParticipantsAction.getURL(self._conf))
        vars["hasStarted"] = nowutc() < self._conf.getStartDate()
        vars["currentUser"] = self._rh._aw.getUser()
        vars["numberParticipants"] = len(self._conf.getParticipation().getParticipantList())
        vars["conf"] = self._conf
        vars["excelIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))

        return vars


class WPConfModifParticipants(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsList.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipants(self._conf)
        return p.getHTML(params)


class WConferenceParticipantsPending(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")
        vars["pending"] = self._getPendingParticipantsList()
        vars["numberPending"] = self._conf.getParticipation().getPendingNumber()
        vars["conf"] = self._conf
        vars["conferenceStarted"] = nowutc() > self._conf.getStartDate()
        vars["currentUser"] = self._rh._aw.getUser()

        return vars

    def _getPendingParticipantsList(self):
        l = []

        for k in self._conf.getParticipation().getPendingParticipantList().keys():
            p = self._conf.getParticipation().getPendingParticipantByKey(k)
            l.append((k, p))
        return l


class WPConfModifParticipantsPending(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsPendingList.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsPending(self._conf)
        return p.getHTML()


class WConferenceParticipantsDeclined(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["declined"] = self._getDeclinedParticipantsList()
        vars["numberDeclined"] = self._conf.getParticipation().getDeclinedNumber()
        return vars

    def _getDeclinedParticipantsList(self):
        l = []

        for k in self._conf.getParticipation().getDeclinedParticipantList().keys():
            p = self._conf.getParticipation().getDeclinedParticipantByKey(k)
            l.append((k, p))
        return l


class WPConfModifParticipantsDeclined(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsDeclinedList.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsDeclined(self._conf)
        return p.getHTML()


class WConferenceParticipantsStatistics(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["invited"] = self._conf.getParticipation().getInvitedNumber()
        vars["rejected"] = self._conf.getParticipation().getRejectedNumber()
        vars["added"] = self._conf.getParticipation().getAddedNumber()
        vars["refused"] = self._conf.getParticipation().getRefusedNumber()
        vars["pending"] = self._conf.getParticipation().getPendingNumber()
        vars["declined"] = self._conf.getParticipation().getDeclinedNumber()
        vars["conferenceStarted"] = nowutc() > self._conf.getStartDate()
        vars["present"] = self._conf.getParticipation().getPresentNumber()
        vars["absent"] = self._conf.getParticipation().getAbsentNumber()
        vars["excused"] = self._conf.getParticipation().getExcusedNumber()
        return vars


class WPConfModifParticipantsStatistics(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabStatistics.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsStatistics(self._conf)
        return p.getHTML(params)


class WPConfModifParticipantsInvitationBase(WPConferenceDisplayBase):

    def _getHeader(self):
        """
        """
        wc = wcomponents.WMenuSimpleEventHeader(self._getAW(), self._conf)
        return wc.getHTML({"loginURL": self.getLoginURL(),\
                            "logoutURL": self.getLogoutURL(),\
                            "confId": self._conf.getId(),\
                            "currentView": "static",\
                            "type": WebFactory.getId(),\
                            "dark": True})

    def _getBody(self, params):
        return '<div style="margin:10px">{0}</div>'.format(self._getContent(params))


class WPConfModifParticipantsInvite(WPConfModifParticipantsInvitationBase):

    def _getContent(self, params):
        msg = _("Please indicate whether you want to accept or reject the invitation to '{0}'").format(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfParticipantsInvitation.getURL(self._conf)
        url.addParam("participantId",params["participantId"])
        return wc.getHTML(msg,
                          url,
                          {},
                          confirmButtonCaption=_("Accept"),
                          cancelButtonCaption=_("Reject"),
                          severity="accept")

#---------------------------------------------------------------------------

class WPConfModifParticipantsRefuse(WPConfModifParticipantsInvitationBase):

    def _getContent( self, params ):
        msg = i18nformat("""
        <font size="+2"> _("Are you sure you want to refuse to attend the '%s'")?</font>
              """)%(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfParticipantsRefusal.getURL( self._conf )
        url.addParam("participantId",params["participantId"])
        return wc.getHTML( msg, url, {}, \
                        confirmButtonCaption= _("Refuse"), cancelButtonCaption= _("Cancel") )

#---------------------------------------------------------------------------

class WConferenceLog(wcomponents.WTemplated):

    def __init__(self, conference):
        wcomponents.WTemplated.__init__(self)
        self.__conf = conference
        self._tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        if not self._tz:
            self._tz = 'UTC'

    def getVars(self):
        log_vars = wcomponents.WTemplated.getVars(self)
        log_vars["log_dict"] = self._getLogDict()
        log_vars["timezone"] = timezone(self._tz)
        return log_vars

    def _getLogDict(self):
        """Return a dictionary of log entries per day."""
        log = self.__conf.getLogHandler().getLogList()
        log_dict = collections.defaultdict(list)
        for line in log:
            date = line.getLogDate().date()
            log_dict[date].append(line)
        return log_dict


class WPConfModifLog(WPConferenceModifBase):

    def _setActiveSideMenuItem(self):
        self._logMenuItem.setActive()

    def _getPageContent(self, params):
        p = WConferenceLog(self._conf)
        return p.getHTML(params)

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
        return vars


class WPConfModifListings(WPConferenceModifBase):

    def __init__(self, rh, conference):
        WPConferenceModifBase.__init__(self, rh, conference)
        self._createTabCtrl()

    def _setActiveSideMenuItem(self):
        self._listingsMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        self._subTabSpeakers = self._tabCtrl.newTab('speakers',
            _('All Contribution Speakers'),
            urlHandlers.UHConfAllSpeakers.getURL(self._conf))
        self._subTabConveners = self._tabCtrl.newTab('conveners',
            _('All Session Conveners'),
            urlHandlers.UHConfAllSessionsConveners.getURL(self._conf))
        self._subTabUsers = self._tabCtrl.newTab('users',
            _('People Pending'),
            urlHandlers.UHConfModifPendingQueues.getURL(self._conf))

    def _getPageContent(self, params):
        self._setActiveTab()
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))

    def _setActiveTab(self):
        self._subTabUsers.setActive()

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
        return vars


class WPConfClone( WPConfModifToolsBase, OldObservable ):

    def _setActiveTab( self ):
        self._tabCloneEvent.setActive()

    def _getTabContent( self, params ):
        p = WConferenceClone( self._conf )
        pars = {"cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
                "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
                "cloneOptions": i18nformat("""<li><input type="checkbox" name="cloneTracks" id="cloneTracks" value="1" />_("Tracks")</li>
                                     <li><input type="checkbox" name="cloneTimetable" id="cloneTimetable" value="1" />_("Full timetable")</li>
                                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneSessions" id="cloneSessions" value="1" />_("Sessions")</li></ul></li>
                                     <li><input type="checkbox" name="cloneRegistration" id="cloneRegistration" value="1" >_("Registration")</li>
                                     <li><input type="checkbox" name="cloneEvaluation" id="cloneEvaluation" value="1" />_("Evaluation")</li>""") }
        #let the plugins add their own elements
        self._notify('addCheckBox2CloneConf', pars)
        return p.getHTML(pars)

#---------------------------------------------------------------------------------------

class WPConfOffline(WPConfModifToolsBase):

    def _setActiveTab(self):
        self._tabOffline.setActive()

    def _getTabContent(self, params):
        p = WConfOffline(self._conf)
        return p.getHTML(params)


class WConfOffline(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confId"] = self._conf.getId()
        vars["avatarId"] = self._rh._aw.getUser().getId()
        vars["offlineTasks"] = ModuleHolder().getById("offlineEvents").getOfflineEventByConfId(self._conf.getId())
        return vars

#---------------------------------------------------------------------------------------


class WConferenceAllSessionsConveners(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()
        vars["convenerSelectionAction"] = quoteattr(str(urlHandlers.UHConfAllSessionsConvenersAction.getURL(self.__conf)))
        vars["contribSetIndex"] = 'index'
        vars["convenerNumber"] = str(len(self.__conf.getAllSessionsConvenerList()))
        vars["conveners"] = self._getAllConveners()
        return vars

    def _getTimetableURL(self, convener):
        url = urlHandlers.UHSessionModifSchedule.getURL(self.__conf)
        url.addParam("sessionId", convener.getSession().getId())
        if hasattr(convener, "getSlot"):
            timetable = "#" + str(convener.getSlot().getStartDate().strftime("%Y%m%d")) + ".s%sl%s" % (convener.getSession().getId(), convener.getSlot().getId())
        else:
            timetable = "#" + str(convener.getSession().getStartDate().strftime("%Y%m%d"))

        return "%s%s" % (url, timetable)

    def _getAllConveners(self):
        convenersFormatted = []
        convenersDict = self.__conf.getAllSessionsConvenerList()

        for key, conveners in convenersDict.iteritems():
            data = None

            for convener in convenersDict[key]:

                if not data:
                    data = {
                        'email': convener.getEmail(),
                        'name': convener.getFullName() or '',
                        'sessions': []
                    }

                sessionData = {
                    'title': '',
                    'urlTimetable': self._getTimetableURL(convener),
                    'urlSessionModif': None
                }

                if isinstance(convener, conference.SlotChair):
                    title = convener.getSlot().getTitle() or "Block %s" % convener.getSlot().getId()
                    sessionData['title'] = convener.getSession().getTitle() + ': ' + title
                else:
                    url = urlHandlers.UHSessionModification.getURL(self.__conf)
                    url.addParam('sessionId', convener.getSession().getId())

                    sessionData['urlSessionModif'] = str(url)
                    sessionData['title'] = convener.getSession().getTitle() or ''

                data['sessions'].append(sessionData)

            convenersFormatted.append(data)

        return convenersFormatted


class WPConfAllSessionsConveners(WPConfModifListings):

    def _setActiveTab(self):
        self._subTabConveners.setActive()

    def _getTabContent(self, params):
        p = WConferenceAllSessionsConveners(self._conf)
        return p.getHTML()

#---------------------------------------------------------------------------------------


class WConfModifAllContribParticipants(wcomponents.WTemplated):

    def __init__(self, conference, partIndex):
        self._title = _("All participants list")
        self._conf = conference
        self._order = ""
        self._dispopts = ["Email", "Contributions"]
        self._partIndex = partIndex

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        self._url = vars["participantMainPageURL"]
        vars["speakers"] = self._getAllParticipants()
        vars["participantNumber"] = str(len(self._partIndex.getParticipationKeys()))

        return vars

    def _getAllParticipants(self):
        speakers = []

        for key in self._partIndex.getParticipationKeys():
            participationList = self._partIndex.getById(key)

            if participationList:
                participant = participationList[0]

                pData = {
                    'name': participant.getFullName(),
                    'email': participant.getEmail(),
                    'contributions': []
                }

                for participation in participationList:
                    contribution = participation.getContribution()

                    if contribution:
                        pData['contributions'].append({
                            'title': contribution.getTitle(),
                            'url': str(urlHandlers.UHContributionModification.getURL(contribution))
                        })

                speakers.append(pData)

        return speakers

    def _getURL(self):
        return self._url


class WPConfAllSpeakers(WPConfModifListings):

    def _setActiveTab(self):
        self._subTabSpeakers.setActive()

    def _getTabContent(self, params):
        p = WConfModifAllContribParticipants( self._conf, self._conf.getSpeakerIndex() )
        return p.getHTML({"title": _("All speakers list"), \
                          "participantMainPageURL":urlHandlers.UHConfAllSpeakers.getURL(self._conf), \
                          "participantSelectionAction":quoteattr(str(urlHandlers.UHConfAllSpeakersAction.getURL(self._conf)))})


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
        vars["From"] = self._fromemail
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

    def _getPageContent(self,params):
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
        vars["From"] = self._fromemail
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

class WPConvenerSentEmail( WPConfModifListings ):
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

class WConfDisplayAlarm( wcomponents.WTemplated ):

    def __init__(self, conference, aw):
        self.__conf = self.__target = conference
        self._aw=aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["locator"] = self.__target.getLocator().getWebForm()
        vars["dtFormat"]= "%Y-%m-%d %H:%M"
        vars["confTZ"]= timezone(self.__target.getTimezone())
        vars["alarmList"] = self.__target.getAlarmList()
        vars["timezone"] = self.__target.getTimezone()
        vars["addAlarmURL"] = urlHandlers.UHConfAddAlarm.getURL( self.__conf )
        return vars

class WPConfDisplayAlarm( WPConfModifToolsBase ):

    def _getTabContent( self, params ):
        wc = WConfDisplayAlarm( self._conf, self._rh._getUser() )
        return wc.getHTML()

#---------------------------------------------------------------------------------------

class WSetAlarm(wcomponents.WTemplated):

    def __init__(self, conference, aw):
        self.__conf = conference
        self._aw=aw

    def _getFromList(self):
        fromList = {}
        for ch in self.__conf.getChairList():
            if not fromList.has_key(ch.getEmail().strip()):
                fromList[ch.getEmail().strip()] = ch.getFullName()
        if self.__conf.getSupportInfo().getEmail().strip()!="" and not fromList.has_key(self.__conf.getSupportInfo().getEmail().strip()):
            fromList[self.__conf.getSupportInfo().getEmail().strip()] = self.__conf.getSupportInfo().getEmail().strip()
        if self._aw.getUser() is not None and not fromList.has_key(self._aw.getUser().getEmail().strip()):
            fromList[self._aw.getUser().getEmail().strip()] = self._aw.getUser().getFullName()
        if self.__conf.getCreator() is not None and not fromList.has_key(self.__conf.getCreator().getEmail().strip()):
            fromList[self.__conf.getCreator().getEmail().strip()] = self.__conf.getCreator().getFullName()
        return fromList

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        if vars.has_key("alarmId"):
            vars["formTitle"] =  _("Create a new alarm email")
        else:
            vars["formTitle"] =  _("Modify alarm data")
        vars["timezone"] = self.__conf.getTimezone()
        vars["conference"] = self.__conf
        vars["today"] = datetime.today()
        vars["fromList"] = self._getFromList()
        vars["date_format"] = '%d/%m/%Y %H:%M'

        try:
            vars["alarm_date"] = datetime(vars['year'], vars['month'], vars['day'],
                                          int(vars['hour']), int(vars['minute']))
        except ValueError:
            vars["alarm_date"] = self.__conf.getAdjustedStartDate()
        return vars

class WPConfAddAlarm( WPConfModifToolsBase ):

    def _setActiveTab( self ):
        self._tabAlarms.setActive()

    def _getTabContent( self, params ):
        wc = WSetAlarm( self._conf, self._getAW() )
        pars = {}
        pars["alarmId"] = self._rh._reqParams.get("alarmId","")
        pars["alarm"] = None
        pars["user"] = self._rh._getUser()
        pars["fromAddr"] = self._rh._reqParams.get("fromAddr","")
        pars["Emails"] = self._rh._reqParams.get("Emails","")
        pars["note"] = self._rh._reqParams.get("note","")
        pars["includeConf"] = (self._rh._reqParams.get("includeConf","")=="1")
        pars["toAllParticipants"] =  (self._rh._reqParams.get("toAllParticipants",False) == "on")
        pars["dateType"] = int(self._rh._reqParams.get("dateType",-1))
        tz=self._conf.getTimezone()
        now = nowutc().astimezone(timezone(tz))
        pars["year"]=self._rh._reqParams.get("year",now.year)
        pars["month"] = self._rh._reqParams.get("month",now.month)
        pars["day"] = self._rh._reqParams.get("day",now.day)
        pars["hour"] = self._rh._reqParams.get("hour","08")
        pars["minute"] = self._rh._reqParams.get("minute","00")
        pars["timeBefore"] = int(self._rh._reqParams.get("_timeBefore",0))
        pars["timeTypeBefore"] = self._rh._reqParams.get("dayBefore","")
        return wc.getHTML( pars )

#--------------------------------------------------------------------

class WPConfModifyAlarm( WPConfModifToolsBase ):

    def __init__(self, caller, conf, alarm):
        WPConfModifToolsBase.__init__(self, caller, conf)
        self._alarm = alarm

    def _getTabContent( self, params ):
        wc = WSetAlarm(self._conf, self._getAW())
        pars ={}
        pars["alarmId"] = self._alarm.getConfRelativeId()
        pars["alarm"] = self._alarm
        pars["timeBeforeType"] = ""
        timeBefore=0
        year = month = day = hour = minute = -1
        if self._alarm.getTimeBefore():
            pars["dateType"] = 2
            #the date is calculated from the conference startdate
            if self._alarm.getTimeBefore() < timedelta(days=1):
                pars["timeBeforeType"] = "hours"
                timeBefore = int(self._alarm.getTimeBefore().seconds/3600)
            else:
                #time before upper to 1 day
                pars["timeBeforeType"] = "days"
                timeBefore = int(self._alarm.getTimeBefore().days)
        else:
            #the date is global
            pars["dateType"] = 1
            startOn = self._alarm.getStartOn().astimezone(timezone(self._conf.getTimezone()))
            if startOn != None:
                month = startOn.month
                day = startOn.day
                hour = startOn.hour
                minute = startOn.minute
                year = startOn.year
        pars["day"] = day
        pars["month"] = month
        pars["year"] = year
        pars["hour"] = hour
        pars["minute"] = minute
        pars["timeBefore"] = timeBefore
        pars["subject"] = self._alarm.getSubject()
        pars["Emails"] = ", ".join(self._alarm.getToAddrList())
        pars["fromAddr"] = self._alarm.getFromAddr()
        pars["text"] = self._alarm.getText()
        pars["note"] = self._alarm.getNote()
        pars["toAllParticipants"] =  self._alarm.getToAllParticipants()
        pars["includeConf"] = self._alarm.getConfSummary()
        return wc.getHTML( pars )

#----------------------------------------------------------------------------------


class WConfModifCFA(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def _getAbstractFieldsHTML(self, vars):
        abMgr = self._conf.getAbstractMgr()
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")
        laf = []
        urlRemove = str(urlHandlers.UHConfModifCFARemoveOptFld.getURL(self._conf))
        laf.append("""<form action="" method="POST">""")
        for af in abMgr.getAbstractFieldsMgr().getFields():
            urlUp = urlHandlers.UHConfModifCFAAbsFieldUp.getURL(self._conf)
            urlUp.addParam("fieldId", af.getId())
            urlDown = urlHandlers.UHConfModifCFAAbsFieldDown.getURL(self._conf)
            urlDown.addParam("fieldId", af.getId())
            if af.isMandatory():
                mandatoryText = _("mandatory")
            else:
                mandatoryText = _("optional")
            maxCharText = ""
            if isinstance(af, AbstractTextField):
                maxCharText = " - "
                if int(af.getMaxLength()) != 0:
                    maxCharText += _("max: %s %s.") % (af.getMaxLength(), af.getLimitation())
                else:
                    maxCharText += _("not limited")
            addInfo = "(%s%s)" % (mandatoryText, maxCharText)
            url = urlHandlers.UHConfModifCFAOptFld.getURL(self._conf)
            url.addParam("fieldId", af.getId())
            url = quoteattr("%s#optional" % str(url))
            if self._conf.getAbstractMgr().hasEnabledAbstractField(af.getId()):
                icon = vars["enablePic"]
                textIcon = enabledText
            else:
                icon = vars["disablePic"]
                textIcon = disabledText
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
                                  &nbsp;<a class="edit-field" href="#" data-id=%s data-fieldType=%s>%s</a> %s
                                </td>
                            </tr>
                            """ % (
                                url,
                                icon,
                                textIcon,
                                quoteattr(str(urlUp)),
                                quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))),
                                quoteattr(str(urlDown)),
                                quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))),
                                removeButton,
                                af.getId(),
                                af.getType(),
                                af.getCaption(),
                                addInfo))
        laf.append(i18nformat("""
    <tr>
      <td align="right" colspan="3">
        <input type="submit" value="_("remove")" onClick="this.form.action='%s';" class="btn">
        <input id="add-field-button" type="submit" value="_("add")" class="btn">
      </td>
    </tr>
    </form>""") % urlRemove)
        laf.append("</form>")
        return "".join(laf)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        abMgr = self._conf.getAbstractMgr()

        vars["iconDisabled"] = str(Config.getInstance().getSystemIconURL("disabledSection"))
        vars["iconEnabled"] = str(Config.getInstance().getSystemIconURL("enabledSection"))

        vars["multipleTracks"] = abMgr.getMultipleTracks()
        vars["areTracksMandatory"] = abMgr.areTracksMandatory()
        vars["canAttachFiles"] = abMgr.canAttachFiles()
        vars["showSelectAsSpeaker"] = abMgr.showSelectAsSpeaker()
        vars["isSelectSpeakerMandatory"] = abMgr.isSelectSpeakerMandatory()
        vars["showAttachedFilesContribList"] = abMgr.showAttachedFilesContribList()

        vars["multipleUrl"] = urlHandlers.UHConfCFASwitchMultipleTracks.getURL(self._conf)
        vars["mandatoryUrl"] = urlHandlers.UHConfCFAMakeTracksMandatory.getURL(self._conf)
        vars["attachUrl"] = urlHandlers.UHConfCFAAllowAttachFiles.getURL(self._conf)
        vars["showSpeakerUrl"] = urlHandlers.UHConfCFAShowSelectAsSpeaker.getURL(self._conf)
        vars["speakerMandatoryUrl"] = urlHandlers.UHConfCFASelectSpeakerMandatory.getURL(self._conf)
        vars["showAttachedFilesUrl"] = urlHandlers.UHConfCFAAttachedFilesContribList.getURL(self._conf)

        vars["setStatusURL"] = urlHandlers.UHConfCFAChangeStatus.getURL(self._conf)
        vars["dataModificationURL"] = urlHandlers.UHCFADataModification.getURL(self._conf)
        if abMgr.getCFAStatus():
            vars["changeTo"] = "False"
            vars["status"] = _("ENABLED")
            vars["changeStatus"] = _("DISABLE")
            vars["startDate"] = format_date(abMgr.getStartSubmissionDate(), format='full')
            vars["endDate"] = format_date(abMgr.getEndSubmissionDate(), format='full')
            vars["announcement"] = abMgr.getAnnouncement()
            vars["disabled"] = ""
            modifDL = abMgr.getModificationDeadline()
            vars["modifDL"] = i18nformat("""--_("not specified")--""")
            if modifDL:
                vars["modifDL"] = format_date(modifDL, format='full')
            vars["notification"] = i18nformat("""
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
                        """) % (", ".join(abMgr.getSubmissionNotification().getToList()) or i18nformat("""--_("no TO list")--"""), ", ".join(abMgr.getSubmissionNotification().getCCList()) or i18nformat("""--_("no CC list")--"""))
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
            vars["notification"] = ""
        vars["enablePic"] = quoteattr(str(Config.getInstance().getSystemIconURL("enabledSection")))
        vars["disablePic"] = quoteattr(str(Config.getInstance().getSystemIconURL("disabledSection")))
        vars["abstractFields"] = self._getAbstractFieldsHTML(vars)
        vars["addNotifTplURL"] = urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)
        vars["remNotifTplURL"] = urlHandlers.UHAbstractModNotifTplRem.getURL(self._conf)
        vars["confId"] = self._conf.getId()
        vars["lateAuthUsers"] = fossilize(self._conf.getAbstractMgr().getAuthorizedSubmitterList())
        return vars


class WPConfModifCFAPreview(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabCFAPreview.setActive()

    def _getHeadContent(self):
        return WPConferenceModifAbstractBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def getCSSFiles(self):
        return WPConferenceModifAbstractBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifAbstractBase.getJSFiles(self) + \
            self._asset_env['abstracts_js'].urls()

    def _getTabContent(self, params):
        import MaKaC.webinterface.pages.abstracts as abstracts
        wc = abstracts.WAbstractDataModification(self._conf)
        # Simulate fake abstract
        from MaKaC.webinterface.common.abstractDataWrapper import AbstractData
        ad = AbstractData(self._conf.getAbstractMgr(), {}, 9999)
        params = ad.toDict()
        params["postURL"] = ""
        params["origin"] = "management"
        return wc.getHTML(params)


class WPConfModifCFA(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabCFA.setActive()

    def _getTabContent(self, params):
        wc = WConfModifCFA(self._conf)
        return wc.getHTML()


class WCFADataModification(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
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
        vars["postURL"] = urlHandlers.UHCFAPerformDataModification.getURL(self._conf)
        return vars


class WPCFADataModification(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabCFA.setActive()

    def _getTabContent(self, params):
        p = WCFADataModification(self._conf)
        return p.getHTML()


class WConfModifProgram(wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["deleteItemsURL"]=urlHandlers.UHConfDelTracks.getURL(self._conf)
        vars["addTrackURL"]=urlHandlers.UHConfAddTrack.getURL( self._conf )
        vars["conf"] = self._conf
        return vars


class WPConfModifProgram( WPConferenceModifBase ):

    def _setActiveSideMenuItem( self ):
        self._programMenuItem.setActive()

    def _getPageContent( self, params ):
        wc = WConfModifProgram( self._conf )
        return wc.getHTML()


class WTrackCreation( wcomponents.WTemplated ):

    def __init__( self, targetConf ):
        self.__conf = targetConf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars['title'] = ''
        vars['description'] = ''
        return vars



class WPConfAddTrack( WPConfModifProgram ):

    def _setActiveSideMenuItem(self):
        self._programMenuItem.setActive()

    def _getPageContent( self, params ):
        p = WTrackCreation( self._conf )
        pars = {"postURL": urlHandlers.UHConfPerformAddTrack.getURL(self._conf)}
        return p.getHTML( pars )

class WFilterCriteriaAbstracts(wcomponents.WFilterCriteria):
    """
    Draws the options for a filter criteria object
    This means rendering the actual table that contains
    all the HTML for the several criteria
    """

    def __init__(self, options, filterCrit, extraInfo=""):
        wcomponents.WFilterCriteria.__init__(self, options, filterCrit, extraInfo)

    def _drawFieldOptions(self, id, data):
        page = WFilterCriterionOptionsAbstracts(id, data)

        # TODO: remove when we have a better template system
        return page.getHTML()

class WFilterCriterionOptionsAbstracts(wcomponents.WTemplated):

    def __init__(self, id, data):
        self._id = id
        self._data = data

    def getVars(self):

        vars = wcomponents.WTemplated.getVars( self )

        vars["id"] = self._id
        vars["title"] = self._data["title"]
        vars["options"] = self._data["options"]
        vars["selectFunc"] = self._data.get("selectFunc", True)

        return vars

class WAbstracts( wcomponents.WTemplated ):

    # available columns
    COLUMNS = ["ID", "Title", "PrimaryAuthor", "Tracks", "Type", "Status", "Rating", "AccTrack", "AccType", "SubmissionDate", "ModificationDate"]

    def __init__( self, conference, filterCrit, sortingCrit, order, display, filterUsed):
        self._conf = conference
        self._filterCrit = filterCrit
        self._sortingCrit = sortingCrit
        self._order = order
        self._display = display
        self._filterUsed = filterUsed

    def _getURL( self, sortingField, column ):
        url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)
        url.addParam("sortBy", column)
        if sortingField and sortingField.getId() == column:
            if self._order == "down":
                url.addParam("order","up")
            elif self._order == "up":
                url.addParam("order","down")
        return url


    def _getTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="trackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and t.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="track" value=%s%s> (%s) %s\n"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="typeShowNoValue"%s> --_("not specified")--""")%checked]
        for contribType in self._conf.getContribTypeList():
            checked = ""
            if field is not None and contribType.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="type" value=%s%s> %s"""%(quoteattr(contribType.getId()), checked, self.htmlText(contribType.getName())) )
        return l

    def _getAccTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="accTrackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and t.getId() in field.getValues():
                checked=" checked"
            l.append("""<input type="checkbox" name="acc_track" value=%s%s> (%s) %s"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getAccContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="accTypeShowNoValue"%s> --_("not specified")--""")%checked]
        for contribType in self._conf.getContribTypeList():
            checked = ""
            if field is not None and contribType.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="acc_type" value=%s%s> %s"""%(quoteattr(contribType.getId()),checked,self.htmlText(contribType.getName())))
        return l

    def _getStatusFilterItemList( self ):
        l = []
        for status in AbstractStatusList.getInstance().getStatusList():
            checked = ""
            statusId = AbstractStatusList.getInstance().getId( status )
            statusCaption = AbstractStatusList.getInstance().getCaption( status )
            statusCode=AbstractStatusList.getInstance().getCode(status)
            statusIconURL= AbstractStatusList.getInstance().getIconURL( status )
            field=self._filterCrit.getField("status")
            if field is not None and statusId in field.getValues():
                checked = "checked"
            imgHTML = """<img src=%s border="0" alt="">"""%(quoteattr(str(statusIconURL)))
            l.append( """<input type="checkbox" name="status" value=%s%s>%s (%s) %s"""%(quoteattr(statusId),checked,imgHTML,self.htmlText(statusCode),self.htmlText(statusCaption)))
        return l

    def _getOthersFilterItemList( self ):
        checkedShowMultiple, checkedShowComments = "", ""
        track_field=self._filterCrit.getField("track")
        if track_field is not None and track_field.onlyMultiple():
            checkedShowMultiple = " checked"
        if self._filterCrit.getField("comment") is not None:
            checkedShowComments = " checked"
        l = [ i18nformat("""<input type="checkbox" name="trackShowMultiple"%s> _("only multiple tracks")""")%checkedShowMultiple,
                i18nformat("""<input type="checkbox" name="comment"%s> _("only with comments")""")%checkedShowComments]
        return l

    def _getFilterMenu(self):

        options = [
            ('Tracks', {"title": _("tracks"),
                        "options": self._getTrackFilterItemList()}),
            ('Types', {"title": _("types"),
                       "options": self._getContribTypeFilterItemList()}),
            ('Status', {"title": _("status"),
                       "options": self._getStatusFilterItemList()}),
            ('AccTracks', {"title": _("(proposed to be) accepted for tracks"),
                       "options": self._getAccTrackFilterItemList()}),
            ('AccTypes', {"title": _("(proposed to be) accepted for types"),
                       "options": self._getAccContribTypeFilterItemList()}),
            ('Others', {"title": _("others"),
                       "selectFunc": False,
                       "options": self._getOthersFilterItemList()})
            ]

        extraInfo = ""
        if self._conf.getRegistrationForm().getStatusesList():
            extraInfo = i18nformat("""<table align="center" cellspacing="10" width="100%%">
                                <tr>
                                    <td colspan="5" class="titleCellFormat"> _("Author search") <input type="text" name="authSearch" value=%s></td>
                                </tr>
                            </table>
                        """)%(quoteattr(str(self._authSearch)))

        p = WFilterCriteriaAbstracts(options, None, extraInfo)

        return p.getHTML()


    def _getColumnTitlesDict(self):
        """
            Dictionary with the translation from "ids" to "name to display" for each of the options you can choose for the display.
            This method complements the method "_setDispOpts" in which we get a dictonary with "ids".
        """
        if not hasattr(self, "_columns"):
            self._columns = {"ID": "ID","Title": "Title", "PrimaryAuthor": "Primary Author", "Tracks": "Tracks", "Type": "Type", "Status":"Status", \
                      "Rating":" Rating", "AccTrack": "Acc. Track", "AccType": "Acc. Type", "SubmissionDate": "Submission Date", "ModificationDate": "Modification Date"}
        return self._columns

    def _getDisplay(self):
        """
            These are the 'display' options selected by the user. In case no options were selected we add some of them by default.
        """
        display = self._display[:]

        if display == []:
            display = self.COLUMNS
        return display

    def _getAccType(self, abstract):
        status = abstract.getCurrentStatus()
        if isinstance(status,(review.AbstractStatusAccepted, review.AbstractStatusProposedToAccept)) and status.getType() is not None:
            return self.htmlText(status.getType().getName())
        return ""

    def _getAccTrack(self, abstract):
        status = abstract.getCurrentStatus()
        if isinstance(status,(review.AbstractStatusAccepted, review.AbstractStatusProposedToAccept)) and status.getTrack() is not None:
            return self.htmlText(status.getTrack().getCode())
        return ""

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["abstractSelectionAction"]=quoteattr(str(urlHandlers.UHAbstractConfSelectionAction.getURL(self._conf)))
        vars["confId"] = self._conf.getId()
        self._authSearch=vars.get("authSearch","")

        vars["filterMenu"] = self._getFilterMenu()

        sortingField=None
        if self._sortingCrit is not None:
            sortingField=self._sortingCrit.getField()

        vars["sortingField"] = sortingField.getId()
        vars["order"] = self._order
        vars["downArrow"] = Config.getInstance().getSystemIconURL("downArrow")
        vars["upArrow"] = Config.getInstance().getSystemIconURL("upArrow")
        vars["getSortingURL"] = lambda column: self._getURL(sortingField, column)
        vars["getAccType"] = lambda abstract: self._getAccType(abstract)
        vars["getAccTrack"] = lambda abstract: self._getAccTrack(abstract)

        f = filters.SimpleFilter( self._filterCrit, self._sortingCrit )
        abstractList=f.apply(self._conf.getAbstractMgr().getAbstractsMatchingAuth(self._authSearch))
        if self._order =="up":
            abstractList.reverse()
        vars["abstracts"] = abstractList

        vars["totalNumberAbstracts"] = str(len(self._conf.getAbstractMgr().getAbstractList()))
        vars["filteredNumberAbstracts"] = str(len(abstractList))
        vars["filterUsed"] = self._filterUsed
        vars["accessAbstract"] = quoteattr(str(urlHandlers.UHAbstractDirectAccess.getURL(self._conf)))

        url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)
        url.setSegment( "results" )
        vars["filterPostURL"] = quoteattr(str(url))
        vars["excelIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars["pdfIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["xmlIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("xml")))
        vars["displayColumns"] = self._getDisplay()
        vars["columnsDict"] = self._getColumnTitlesDict()
        vars["columns"] = self.COLUMNS

        return vars

class WPConfAbstractList( WPConferenceModifAbstractBase ):

    def __init__(self, rh, conf, msg, filterUsed = False ):
        self._msg = msg
        self._filterUsed = filterUsed
        WPConferenceModifAbstractBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        order = params.get("order","down")
        wc = WAbstracts( self._conf, params.get("filterCrit", None ),
                            params.get("sortingCrit", None),
                            order,
                            params.get("display",None),
                            self._filterUsed )
        p = {"authSearch":params.get("authSearch","")}
        return wc.getHTML( p )

    def _setActiveTab(self):
        self._tabAbstractList.setActive()


class WPModNewAbstract(WPConfAbstractList):

    def __init__(self, rh, conf, abstractData):
        WPConfAbstractList.__init__(self, rh, conf, "")

    def _getTabContent(self, params):
        from MaKaC.webinterface.pages.abstracts import WAbstractDataModification
        params["postURL"] = urlHandlers.UHConfModNewAbstract.getURL(self._conf)
        params["origin"] = "management"
        wc = WAbstractDataModification(self._conf)
        return wc.getHTML(params)

    def getCSSFiles(self):
        return WPConfAbstractList.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConfAbstractList.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._asset_env['abstracts_js'].urls()

    def _getHeadContent(self):
        return WPConfAbstractList._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])


class WConfModAbstractsMerge(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
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

    def __init__(self, rh, conf):
        WPConfAbstractList.__init__(self, rh, conf, "")

    def _getTabContent(self, params):
        wc = WConfModAbstractsMerge(self._conf)
        p = {"absIdList": params.get("absIdList", []),
             "targetAbsId": params.get("targetAbsId", ""),
             "inclAuth": params.get("inclAuth", False),
             "comments": params.get("comments", ""),
             "notify": params.get("notify", True),
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
        vars["conf"]=self._conf
        vars["saveLogo"]=urlHandlers.UHSaveLogo.getURL(self._conf)
        vars["logoURL"]=""
        if self._conf.getLogo():
            vars["logoURL"] = urlHandlers.UHConferenceLogo.getURL(self._conf, _=int(time.time()))

        vars["formatTitleTextColor"] = WFormatColorOptionModif("titleTextColor", self._format, self._conf, 3).getHTML()
        vars["formatTitleBgColor"] = WFormatColorOptionModif("titleBgColor", self._format, self._conf, 4).getHTML()

        # Set up the logo of the conference
        vars["logoIconURL"] = Config.getInstance().getSystemIconURL("logo")
        if vars["logoURL"]:
            vars["logo"] = """<img heigth=\"95\" width=\"150\" src="%s" alt="%s" border="0">"""%(vars["logoURL"], self._conf.getTitle())
            vars["removeLogo"] = i18nformat("""<form action=%s method="POST"><input type="submit" class="btn" value="_("remove")"></form>""")%quoteattr(str(urlHandlers.UHRemoveLogo.getURL(self._conf)))
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
                name = self._link.getName()
                if name == "timetable":
                    vars["linkEdition"] = WTimetableModif(self._link).getHTML(p)
                else:
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
            vars["linkEdition"] = i18nformat("""<center><b> _("Click on an item of the menu to edit it")</b></center>""")

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
            vars["modifiedText"]= i18nformat("""<font color="green"> _("(text saved)")</font>""")

        #enable or disable the contribution search feature
        urlSB=urlHandlers.UHConfModifToggleSearch.getURL(self._conf)
        if self._searchEnabled:
            vars["searchBoxIcon"]=vars["enablePic"]
            vars["searchBoxTextIcon"]=enabledText
        else:
            vars["searchBoxIcon"]=vars["disablePic"]
            vars["searchBoxTextIcon"]=disabledText
        vars["searchBoxURL"]=quoteattr(str(urlSB))

        #enable or disable navigation icons
        vars["confType"] = self._conf.getType()
        urlSB=urlHandlers.UHConfModifToggleNavigationBar.getURL(self._conf)
        if displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getDisplayNavigationBar():
            vars["navigationBoxIcon"]=vars["enablePic"]
            vars["navigationBoxTextIcon"]=enabledText
        else:
            vars["navigationBoxIcon"]=vars["disablePic"]
            vars["navigationBoxTextIcon"]=disabledText
        vars["navigationBoxURL"]=quoteattr(str(urlSB))

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

        vars["changeColorURL"] = str(urlChangeColor)
        vars["colorCode"] = value["code"]
        vars["formatOption"] = self._formatOption

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
            disabled = i18nformat("""<font size="-1" color="red"> _("(disabled)")</font>""")
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

class WTimetableModif(WSystemLinkModif):

    def getVars(self):
        wvars = WSystemLinkModif.getVars(self)
        # Timetable detailed view
        wvars["viewMode"] = _("Generic")
        wvars["changeViewModeTo"] = _("Detailed")
        if self._link.getMenu().is_timetable_detailed_view():
            wvars["viewMode"] = _("Detailed")
            wvars["changeViewModeTo"] = _("Generic")
        wvars["toggleTimetableViewURL"] = str(urlHandlers.UHConfModifDisplayToggleTimetableView.getURL(self._link))
        # Timeable Layout
        wvars["defaultTTLayout"] = _("Normal")
        wvars["changedefaultTTLayoutTo"] = _("By room")
        if self._link.getMenu().get_timetable_layout() == 'room':
            wvars["defaultTTLayout"] = _("By room")
            wvars["changedefaultTTLayoutTo"] = _("Normal")
        wvars["toggleTTDefaultLayoutURL"] = str(urlHandlers.UHConfModifDisplayToggleTTDefaultLayout.getURL(self._link))
        return wvars


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
        return WConfModifDisplayAddPage( self._conf, self._linkId ).getHTML()


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
        return wc.getHTML( p )

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
        vars["content"] = self._link.getPage().getContent().replace('"','\\"').replace("'","\\'").replace('\r\n','\\n').replace('\n','\\n')
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

        msg = {
            'challenge': _("Are you sure that you want to delete this link?"),
            'target': self._link.getName()
            }

        postURL = quoteattr(str(urlHandlers.UHConfModifDisplayRemoveLink.getURL(self._link)))
        return wcomponents.WConfirmation().getHTML( msg, postURL, {})


class WPConfParticipantList( WPConfAbstractList ):

    def __init__(self, rh, conf, emailList, displayedGroups, abstracts):
        WPConfAbstractList.__init__(self, rh, conf, None)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._abstracts = abstracts

    def _getTabContent( self, params ):
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

    def __init__(self,conf,filterCrit, sortingCrit, order, filterUsed=False, filterUrl=None):
        self._conf=conf
        self._filterCrit=filterCrit
        self._sortingCrit=sortingCrit
        self._order = order
        self._totaldur =timedelta(0)
        self._filterUsed = filterUsed
        self._filterUrl = filterUrl


    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHConfModifContribList.getURL(self._conf)

        #save params in websession
        dict = session.setdefault('ContributionFilterConf%s' % self._conf.getId(), {})
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
        session.modified = True

        return url


    def _getMaterialsHTML(self, contrib):
        materials=[]
        if contrib.getPaper() is not None:
            url= urlHandlers.UHContribModifMaterialBrowse.getURL(contrib.getPaper())
            #url.addParams({'contribId' : contrib.getId(), 'confId' : contrib.getConference().getId(), 'materialId' : 'paper'})
            materials.append("""<a href=%s>%s</a>"""%(quoteattr(str(url)),self.htmlText(PaperFactory().getTitle().lower())))
        if contrib.getSlides() is not None:
            url= urlHandlers.UHContribModifMaterialBrowse.getURL(contrib.getSlides())
            #url.addParams({'contribId' : contrib.getId(), 'confId' : contrib.getConference().getId(), 'materialId' : 'slides'})
            materials.append("""<a href=%s>%s</a>"""%(quoteattr(str(url)),self.htmlText(SlidesFactory().getTitle().lower())))
        if contrib.getPoster() is not None:
            url= urlHandlers.UHContribModifMaterialBrowse.getURL(contrib.getPoster())
            #url.addParams({'contribId' : contrib.getId(), 'confId' : contrib.getConference().getId(), 'materialId' : 'poster'})
            materials.append("""<a href=%s>%s</a>"""%(quoteattr(str(url)),self.htmlText(PosterFactory().getTitle().lower())))
        if contrib.getVideo() is not None:
            materials.append("""<a href=%s>%s</a>"""%(
                quoteattr(str(urlHandlers.UHContribModifMaterials.getURL(contrib))),
                self.htmlText(materialFactories.VideoFactory.getTitle())))
        if contrib.getMinutes() is not None:
            materials.append("""<a href=%s>%s</a>"""%(
                quoteattr(str(urlHandlers.UHContribModifMaterials.getURL(contrib))),
                self.htmlText(materialFactories.MinutesFactory.getTitle())))
        for material in contrib.getMaterialList():
            url=urlHandlers.UHContribModifMaterials.getURL(contrib)
            materials.append("""<a href=%s>%s</a>"""%(
                quoteattr(str(url)),self.htmlText(material.getTitle())))
        return "<br>".join(materials)

    def _getContribHTML( self, contrib ):
        try:
            sdate=contrib.getAdjustedStartDate().strftime("%d-%b-%Y %H:%M" )
        except AttributeError:
            sdate = ""
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionModification.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        strdur = ""
        if contrib.getDuration() is not None and contrib.getDuration().seconds != 0:
            strdur = (datetime(1900,1,1)+ contrib.getDuration()).strftime("%Hh%M'")
            dur = contrib.getDuration()
            self._totaldur = self._totaldur + dur

        l = [self.htmlText( spk.getFullName() ) for spk in contrib.getSpeakerList()]
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            if contrib.getSession().getCode() != "no code":
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
            <tr id="contributions%s" style="background-color: transparent;" onmouseout="javascript:onMouseOut('contributions%s')" onmouseover="javascript:onMouseOver('contributions%s')">
                <td valign="top" align="right" nowrap><input onchange="javascript:isSelected('contributions%s')" type="checkbox" name="contributions" value=%s></td>
                <td valign="top" nowrap class="CRLabstractDataCell">%s</td>
                <td valign="top" nowrap class="CRLabstractDataCell">%s</td>
                <td valign="top" nowrap class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell" nowrap>%s</td>
            </tr>
                """%(contrib.getId(), contrib.getId(), contrib.getId(),
                    contrib.getId(), contrib.getId(),
                    self.htmlText(contrib.getId()),
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
        res=[ i18nformat("""<input type="checkbox" name="typeShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getContribTypeList():
            checked=""
            if t.getId() in self._filterCrit.getField("type").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="types" value=%s%s> %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getName())))
        return res

    def _getSessionItemsHTML(self):
        checked=""
        if self._filterCrit.getField("session").getShowNoValue():
            checked=" checked"
        res=[ i18nformat("""<input type="checkbox" name="sessionShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for s in self._conf.getSessionListSorted():
            checked=""
            l = self._filterCrit.getField("session").getValues()
            if not isinstance(l, list):
                l = [l]
            if s.getId() in l:
                checked=" checked"
            res.append("""<input type="checkbox" name="sessions" value=%s%s> (%s) %s"""%(quoteattr(str(s.getId())),checked,self.htmlText(s.getCode()),self.htmlText(s.getTitle())))
        return res

    def _getTrackItemsHTML(self):
        checked=""
        if self._filterCrit.getField("track").getShowNoValue():
            checked=" checked"
        res=[ i18nformat("""<input type="checkbox" name="trackShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked=""
            if t.getId() in self._filterCrit.getField("track").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="tracks" value=%s%s> (%s) %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return res

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
        return res

    def _getMaterialItemsHTML(self):
        res=[]
        for (id,caption) in [(PaperFactory().getId(),PaperFactory().getTitle()),\
                        (SlidesFactory().getId(),SlidesFactory().getTitle()),\
                        ("--other--", _("other")),("--none--", i18nformat("""--_("no material")--"""))]:
            checked=""
            if id in self._filterCrit.getField("material").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="material" value=%s%s> %s"""%(quoteattr(str(id)),checked,self.htmlText(caption)))
        return res

    def _getFilterMenu(self):

        options = [
            ('Types', {"title": _("Types"),
                       "options": self._getTypeItemsHTML()}),
            ('Sessions', {"title": _("Sessions"),
                        "options": self._getSessionItemsHTML()}),
            ('Tracks', {"title": _("Tracks"),
                        "options": self._getTrackItemsHTML()}),
            ('Status', {"title": _("Status"),
                       "options": self._getStatusItemsHTML()}),
            ('Materials', {"title": _("Materials"),
                        "options": self._getMaterialItemsHTML()})
        ]

        extraInfo = i18nformat("""<table align="center" cellspacing="10" width="100%%">
                            <tr>
                                <td colspan="5" class="titleCellFormat"> _("Author search") <input type="text" name="authSearch" value=%s></td>
                            </tr>
                        </table>
                    """)%(quoteattr(str(self._authSearch)))

        p = WFilterCriteriaContribs(options, None, extraInfo)

        return p.getHTML()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["filterUrl"] = str(self._filterUrl).replace('%', '%%')
        vars["quickSearchURL"]=quoteattr(str(urlHandlers.UHConfModContribQuickAccess.getURL(self._conf)))
        vars["filterPostURL"]=quoteattr(str(urlHandlers.UHConfModifContribList.getURL(self._conf)))
        self._authSearch=vars.get("authSearch","").strip()
        cl=self._conf.getContribsMatchingAuth(self._authSearch)

        sortingField = self._sortingCrit.getField()
        self._currentSorting=""

        if sortingField is not None:
            self._currentSorting=sortingField.getId()
        vars["currentSorting"]=""

        url=self._getURL()
        url.addParam("sortBy","number")
        vars["numberImg"]=""
        if self._currentSorting == "number":
                vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value="_("number")">""")
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
            vars["currentSorting"]= i18nformat("""<input type="hidden" name="sortBy" value="_("date")">""")
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
            vars["currentSorting"]= i18nformat("""<input type="hidden" name="sortBy" value="_("name")">""")
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
            vars["currentSorting"]= i18nformat("""<input type="hidden" name="sortBy" value="_("type")">""")
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
            vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value='_("session")'>""")
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
            vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value="_("speaker")">""")
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
            vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value="_("track")">""")
            if self._order == "down":
                vars["trackImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["trackImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["trackSortingURL"] = quoteattr( str( url ) )

        f=filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        filteredContribs = f.apply(cl)
        l = [self._getContribHTML(contrib) for contrib in filteredContribs]
        contribsToPrint = ["""<input type="hidden" name="contributions" value="%s">"""%contrib.getId() for contrib in filteredContribs]
        numContribs = len(filteredContribs)

        if self._order =="up":
            l.reverse()
        vars["contribsToPrint"] = "\n".join(contribsToPrint)
        vars["contributions"] = "".join(l)
        orginURL = urlHandlers.UHConfModifContribList.getURL(self._conf)
        vars["numContribs"]=str(numContribs)

        vars["totalNumContribs"] = str(len(self._conf.getContributionList()))
        vars["filterUsed"] = self._filterUsed

        vars["contributionsPDFURL"]=quoteattr(str(urlHandlers.UHContribsConfManagerDisplayMenuPDF.getURL(self._conf)))
        vars["contribSelectionAction"]=quoteattr(str(urlHandlers.UHContribConfSelectionAction.getURL(self._conf)))

        totaldur = self._totaldur
        days = totaldur.days
        hours = (totaldur.seconds)/3600
        dayhours = (days * 24)+hours
        mins = ((totaldur.seconds)/60)-(hours*60)
        vars["totaldur" ]="""%sh%sm"""%(dayhours,mins)
        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
        vars["bookings"] = Conversion.reservationsList(self._conf.getRoomBookingList())
        vars["filterMenu"] = self._getFilterMenu()
        vars["sortingOptions"]="""<input type="hidden" name="sortBy" value="%s">
                                  <input type="hidden" name="order" value="%s">"""%(self._sortingCrit.getField().getId(), self._order)
        vars["pdfIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["excelIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars["xmlIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("xml")))
        return vars

class WFilterCriteriaContribs(wcomponents.WFilterCriteria):
    """
    Draws the options for a filter criteria object
    This means rendering the actual table that contains
    all the HTML for the several criteria
    """

    def __init__(self, options, filterCrit, extraInfo=""):
        wcomponents.WFilterCriteria.__init__(self, options, filterCrit, extraInfo)

    def _drawFieldOptions(self, id, data):

        page = WFilterCriterionOptionsContribs(id, data)

        # TODO: remove when we have a better template system
        return page.getHTML().replace('%','%%')

class WFilterCriterionOptionsContribs(wcomponents.WTemplated):

    def __init__(self, id, data):
        self._id = id
        self._data = data

    def getVars(self):

        vars = wcomponents.WTemplated.getVars( self )

        vars["id"] = self._id
        vars["title"] = self._data["title"]
        vars["options"] = self._data["options"]
        vars["selectFunc"] = self._data.get("selectFunc", True)

        return vars

class WPModifContribList( WPConferenceModifBase ):

    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, conference, filterUsed=False):
        WPConferenceModifBase.__init__(self, rh, conference)
        self._filterUsed = filterUsed

    def _setActiveSideMenuItem(self):
        self._contribListMenuItem.setActive(True)

    def _getPageContent( self, params ):
        filterCrit=params.get("filterCrit",None)
        sortingCrit=params.get("sortingCrit",None)
        order = params.get("order","down")

        filterParams = {}
        fields = getattr(filterCrit, '_fields')
        for field in fields.values():
            id = field.getId()
            showNoValue = field.getShowNoValue()
            values = field.getValues()
            if showNoValue:
                filterParams['%sShowNoValue' % id] = '--none--'
            filterParams[id] = values

        requestParams = self._rh.getRequestParams()

        operationType = requestParams.get('operationType')
        if operationType != 'resetFilters':
            operationType = 'filter'
        urlParams = dict(isBookmark='y', operationType=operationType)

        urlParams.update(self._rh.getRequestParams())
        urlParams.update(filterParams)
        filterUrl = self._rh._uh.getURL(None, **urlParams)

        wc = WConfModifContribList(self._conf,filterCrit, sortingCrit, order, self._filterUsed, filterUrl)
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
            if not session.isClosed():
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
                participant = "%s %s %s <%s>"%(subm.getTitle(), subm.getFirstName(), safe_upper(subm.getFamilyName()), subm.getEmail())
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
                participant = "%s %s %s <%s>"%(pAuth.getTitle(), pAuth.getFirstName(), safe_upper(pAuth.getFamilyName()), pAuth.getEmail())
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
                    participant = "%s %s %s"%(cAuth.getTitle(), cAuth.getFirstName(), safe_upper(cAuth.getFamilyName()))
                else:
                    participant = "%s %s %s <%s>"%(cAuth.getTitle(), cAuth.getFirstName(), safe_upper(cAuth.getFamilyName()), cAuthEmail)
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
        return i18nformat("""
<table align="center"><tr><td align="center">
<b> _("The submitters of the selected abstracts will nearly recieve the notification mail").<br>
<br>
_("You can now close this window.")</b>
</td></tr></table>

""")


class WPContributionList( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEContributionList

    def _getBody( self, params ):
        wc = WConfContributionList( self._getAW(), self._conf, params["filterCrit"], params.get("filterText",""))
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._contribListOpt)


class WConfContributionList (WConfDisplayBodyBase):

    _linkname = "contributionList"

    def __init__(self, aw, conf, filterCrit, filterText):
        self._aw = aw
        self._conf = conf
        self._filterCrit = filterCrit
        self._filterText = filterText

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)

        wvars["body_title"] = self._getTitle()
        wvars["contributions"] = self._conf.getContributionListSorted(includeWithdrawn=False, key="title")
        wvars["showAttachedFiles"] = self._conf.getAbstractMgr().showAttachedFilesContribList()
        wvars["conf"] = self._conf
        wvars["accessWrapper"] = self._aw
        wvars["filterCriteria"] = self._filterCrit
        wvars["filterText"] = self._filterText
        wvars["formatDate"] = lambda date: format_date(date, "d MMM yyyy")
        wvars["formatTime"] = lambda time: format_time(time, format="short", timezone=timezone(DisplayTZ(self._aw, self._conf).getDisplayTZ()))
        return wvars


class WConfAuthorIndex(WConfDisplayBodyBase):

    _linkname = "authorIndex"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = dict(enumerate(self._getItems()))
        return wvars

    def _getItems(self):
        res = []

        for key, authors in self._conf.getAuthorIndex().iteritems():
            # get the first identity that matches the author
            if len(authors) == 0:
                continue
            else:
                auth = authors[0]

            authorURL = urlHandlers.UHContribAuthorDisplay.getURL(auth.getContribution(),
                                                                  authorId=auth.getId())
            contribs = []
            res.append({'fullName': auth.getFullNameNoTitle(),
                        'affiliation': auth.getAffiliation(),
                        'authorURL': authorURL,
                        'contributions': contribs
                        })

            for auth in authors:
                contrib = auth.getContribution()
                if contrib is not None:
                    contribs.append({
                        'title': contrib.getTitle(),
                        'url': str(urlHandlers.UHContributionDisplay.getURL(auth.getContribution())),
                        'materials': fossilize(contrib.getAllMaterialList())
                    })
        return res


class WPAuthorIndex(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEAuthorIndex

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._asset_env['indico_authors'].urls()

    def _getBody(self, params):
        wc = WConfAuthorIndex(self._conf)
        return wc.getHTML()

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._authorIndexOpt)


class WConfSpeakerIndex(WConfDisplayBodyBase):

    _linkname = "speakerIndex"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        res = collections.defaultdict(list)
        for index, key in enumerate(self._conf.getSpeakerIndex().getParticipationKeys()):
            pl = self._conf.getSpeakerIndex().getById(key)
            try:
                speaker = pl[0]
            except IndexError:
                continue
            res[index].append({'fullName': speaker.getFullNameNoTitle(), 'affiliation': speaker.getAffiliation()})
            for speaker in pl:
                if isinstance(speaker, conference.SubContribParticipation):
                    participation = speaker.getSubContrib()
                    if participation is None:
                        continue
                    url = urlHandlers.UHSubContributionDisplay.getURL(participation)
                else:
                    participation = speaker.getContribution()
                    if participation is None:
                        continue
                    url = urlHandlers.UHContributionDisplay.getURL(participation)
                res[index].append({'title': participation.getTitle(), 'url': str(url), 'materials': fossilize(participation.getAllMaterialList())})
        wvars["body_title"] = self._getTitle()
        wvars["items"] = res
        return wvars


class WPSpeakerIndex(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NESpeakerIndex

    def _getBody(self, params):
        wc=WConfSpeakerIndex(self._conf)
        return wc.getHTML()

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._asset_env['indico_authors'].urls()

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
        vars["ConfReviewingChoice"] = self._conf.getConfPaperReview().getChoice()
        return vars


class WConfMyStuffMySessions(WConfDisplayBodyBase):

    _linkname = "mysessions"

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getSessionsHTML(self):
        if self._aw.getUser() is None:
            return ""
        #ls=self._conf.getCoordinatedSessions(self._aw.getUser())+self._conf.getManagedSession(self._aw.getUser())
        ls = set(self._conf.getCoordinatedSessions(self._aw.getUser()))
        ls = list(ls | set(self._conf.getManagedSession(self._aw.getUser())))
        if len(ls) <= 0:
            return ""
        res = []
        iconURL = Config.getInstance().getSystemIconURL("conf_edit")
        for s in ls:
            modURL = urlHandlers.UHSessionModification.getURL(s)
            dispURL = urlHandlers.UHSessionDisplay.getURL(s)
            res.append("""
                <tr class="infoTR">
                    <td class="infoTD" width="100%%">%s</td>
                    <td nowrap class="infoTD"><a href=%s>Edit</a><span class="horizontalSeparator">|</span><a href=%s>View</a></td>
                </tr>""" % (self.htmlText(s.getTitle()),
                            quoteattr(str(modURL)),
                            quoteattr(str(dispURL))))
        return """
            <table class="infoTable" cellspacing="0" width="100%%">
                <tr>
                    <td nowrap class="tableHeader"> %s </td>
                    <td nowrap class="tableHeader" style="text-align:right;"> %s </td>
                </tr>
                <tr>
                    <td>%s</td>
                </tr>
            </table>
            """ % (_("Session"),
                   _("Actions"),
                   "".join(res))

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getSessionsHTML()
        return wvars


class WPConfMyStuffMySessions(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff

    def _getBody(self,params):
        wc=WConfMyStuffMySessions(self._getAW(),self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._myStuffOpt)


class WConfMyStuffMyContributions(WConfDisplayBodyBase):

    _linkname = "mycontribs"

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getContribsHTML(self):
        return WConfMyContributions(self._aw, self._conf).getHTML({})

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getContribsHTML()
        return wvars


class WPConfMyStuffMyContributions(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff

    def _getBody(self,params):
        wc=WConfMyStuffMyContributions(self._getAW(),self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._myContribsOpt)


class WConfMyStuffMyTracks(WConfDisplayBodyBase):

    _linkname = "mytracks"

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getTracksHTML(self):
        if self._aw.getUser() is None or not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            return ""
        lt = self._conf.getCoordinatedTracks(self._aw.getUser())
        if len(lt) <= 0:
            return ""
        res = []
        iconURL = Config.getInstance().getSystemIconURL("conf_edit")
        for t in lt:
            modURL = urlHandlers.UHTrackModifAbstracts.getURL(t)
            res.append("""
                <tr class="infoTR">
                    <td class="infoTD" width="100%%">%s</td>
                    <td nowrap class="infoTD"><a href=%s>Edit</a></td>
                </tr>""" % (self.htmlText(t.getTitle()),
                            quoteattr(str(modURL))))
        return """
            <table class="infoTable" cellspacing="0" width="100%%">
                <tr>
                    <td nowrap class="tableHeader"> %s </td>
                    <td nowrap class="tableHeader" style="text-align:right;"> %s </td>
                </tr>
                <tr>
                    <td>%s</td>
                </tr>
            </table>
            """ % (_("Track"),
                   _("Actions"),
                   "".join(res))

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getTracksHTML()
        return wvars

class WPConfMyStuffMyTracks(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff

    def _getBody(self,params):
        wc=WConfMyStuffMyTracks(self._getAW(),self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._myTracksOpt)


class WConfMyStuff(WConfDisplayBodyBase):

    _linkname = "mystuff"

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


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
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        boaConfig = self._conf.getBOAConfig()
        vars["sortByList"] = boaConfig.getSortByTypes()
        vars["modURL"] = quoteattr(str(urlHandlers.UHConfModAbstractBook.getURL(self._conf)))
        vars["previewURL"] = quoteattr(str(urlHandlers.UHConfAbstractBook.getURL(self._conf)))
        vars["sortBy"] = boaConfig.getSortBy()
        vars["boaConfig"] = boaConfig
        vars["urlToogleShowIds"] = str(urlHandlers.UHConfModAbstractBookToogleShowIds.getURL(self._conf))
        vars["conf"] = self._conf
        vars["bookOfAbstractsActive"] = self._conf.getAbstractMgr().getCFAStatus()
        vars["bookOfAbstractsMenuActive"] = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(
            self._conf).getMenu().getLinkByName('abstractsBook').isEnabled()
        vars["correspondingAuthorList"] = boaConfig.getCorrespondingAuthorTypes()
        vars["correspondingAuthor"] = boaConfig.getCorrespondingAuthor()
        return vars


class WPModAbstractBook(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabBOA.setActive()

    def _getTabContent(self, params):
        wc = WConfModAbstractBook(self._conf)
        return wc.getHTML()

    def getCSSFiles(self):
        return WPConferenceModifAbstractBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifAbstractBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._asset_env['abstracts_js'].urls()

    def _getHeadContent(self):
        return WPConferenceModifAbstractBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])


class WPFullMaterialPackage(WPConfModifToolsBase):

    def _setActiveTab(self):
        self._tabMatPackage.setActive()

    def _getTabContent(self, params):
        wc = WFullMaterialPackage(self._conf)
        return wc.getHTML()


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
                  """%(format_date(sDate, format='dMMMMyyyy'), format_date(sDate, format='long') ) )
            sDate += timedelta(days=1)
        vars["dayList"] = "".join(htmlDay)
        vars["sessionList"] = ""
        if len(self._conf.getSessionList()) == 0:
            vars["sessionList"] = "No session in this event"
        for session in self._conf.getSessionList():
            vars["sessionList"] += i18nformat("""
                 <input name="sessionList" type="checkbox" value="%s" checked="checked">%s _("(last modified: %s)")<br>""") % (session.getId(),session.getTitle(), format_datetime(session.getModificationDate(), format='d MMMM yyyy H:mm'))

        vars["materialTypes"] = MaterialFactoryRegistry.getAllowed(self._conf)
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
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
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


class WConfStaticDetails(WConfDisplayBodyBase):

    _linkname = "overview"

    def __init__(self, aw, conf, staticPars):
        self._conf = conf
        self._aw = aw
        self._staticPars = staticPars

    def _getChairsHTML(self):
        l = []
        for chair in self._conf.getChairList():
            mailToURL = """mailto:%s""" % urllib.quote(chair.getEmail())
            l.append("""<a href=%s>%s</a>""" % (quoteattr(mailToURL), self.htmlText(chair.getFullName())))
        res = ""
        if len(l) > 0:
            res = i18nformat("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Chairs"):</b></td>
        <td>%s</td>
    </tr>
                """) % "<br>".join(l)
        return res

    def _getMaterialHTML(self):
        l = []
        for mat in self._conf.getAllMaterialList():
            temp = wcomponents.WMaterialDisplayItem()
            url = urlHandlers.UHStaticMaterialDisplay.getRelativeURL(mat)
            l.append(temp.getHTML(self._aw, mat, url, self._staticPars["material"]))
        res = ""
        if l:
            res = i18nformat("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Material"):</b></td>
        <td align="left" width="100%%">%s</td>
    </tr>""") % "<br>".join(l)
        return res

    def _getMoreInfoHTML(self):
        res = ""
        if self._conf.getContactInfo() != "":
            res = i18nformat("""
    <tr>
        <td align="right" valign="top" class="displayField"><b> _("Additional info"):</b>
        </td>
        <td>%s</td>
    </tr>""") % self._conf.getContactInfo()
        return res

    def getVars( self ):
        wvars = wcomponents.WTemplated.getVars( self )
        wvars["description"] = self._conf.getDescription()
        sdate, edate = self._conf.getAdjustedStartDate(), self._conf.getAdjustedEndDate()
        fsdate, fedate = format_date(sDate, format='long'), format_date(eDate, format='long')
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")
        wvars["dateInterval"] = i18nformat("""_("from") %s %s _("to") %s %s""") % (fsdate, fstime,
                                                                                   fedate, fetime)
        if sdate.strftime("%d%B%Y") == edate.strftime("%d%B%Y"):
            timeInterval = fstime
            if sdate.strftime("%H%M") != edate.strftime("%H%M"):
                timeInterval = "%s-%s" % (fstime, fetime)
            wvars["dateInterval"] = "%s (%s)" % (fsdate, timeInterval)
        wvars["location"] = ""
        location = self._conf.getLocation()
        if location:
            wvars["location"] = "<i>%s</i><br><pre>%s</pre>" % (location.getName(), location.getAddress())
            room = self._conf.getRoom()
            if room:
                roomLink = linking.RoomLinker().getHTMLLink(room, location)
                wvars["location"] += i18nformat("""<small> _("Room"):</small> %s""") % roomLink
        wvars["chairs"] = self._getChairsHTML()
        wvars["material"] = self._getMaterialHTML()
        wvars["moreInfo"] = self._getMoreInfoHTML()
        wvars["actions"] = ''

        return wvars


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
                         _(link.getCaption()))]
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
                            %(sublink.getName(), url, target,  _(sublink.getCaption())))
                else:
                    url="%s%s"%(parentDir, sublink.getStaticURL())
                    html.append( """<li id="menuLink_%s" class="menuConfMiddleCell" nowrap><a class="confSubSection" href="%s"%s>\
                            <img border="0" src="%s" alt="">&nbsp;%s</a></li>"""%(sublink.getName(), url, target,\
                            params["bulletMenuConf"], _(sublink.getCaption()) ))
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
        vars["confDateInterval"] = i18nformat("""_("from") %s _("to") %s""")%(format_date(adjusted_sDate, format='long'), format_date(adjusted_eDate, format='long'))
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
           vars["confDateInterval"] = format_date(adjusted_sDate, format='long')
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
           vars["confDateInterval"] = "%s-%s %s"%(adjusted_sDate.day, adjusted_eDate.day, format_date(adjusted_sDate, format='MMMM yyyy'))
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
        vars["body"] = self._body
        vars["supportEmail"] = ""
        if self._conf.getSupportInfo().hasEmail():
            mailto = quoteattr("""mailto:%s?subject=%s"""%(self._conf.getSupportInfo().getEmail(), urllib.quote( self._conf.getTitle() ) ))
            vars["supportEmail"] = i18nformat("""<a href=%s class="confSupportEmail"><img src="%s" border="0" alt="email"> _("support")</a>""")%(mailto, self._staticPars["smallEmail"] )
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
            vars["subtracks"] = i18nformat("""<i> _("Sub-tracks") </i>: %s""")%", ".join( subtracks )
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
        authCaption = safe_upper(auth.getFamilyName())
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
        vars["startDate"] = i18nformat("""--_("not yet scheduled")--""")
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
            vars["location"]= i18nformat("""%s <small> _("Room"):</small> %s""")%(\
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
                       <link rel="stylesheet" href="%s/css/events/common.css">""" % \
                    (self.getRootDir(self._target), Config.getInstance().getCssStylesheetName(), self.getRootDir(self._target))
        try:
            if os.path.exists("%s.css" % (os.path.join(path,self._view))):
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
            <meta http-equiv="X-UA-Compatible" content="IE=edge" />
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
        self._staticPars = staticPars

    def _getBody( self, params ):
        pars = { \
    "modifyURL": "", \
        "materialURL":  "", \
        "cloneURL": "", \
    "sessionModifyURLGen": "", \
    "contribModifyURLGen": "", \
        "contribMaterialURLGen": "", \
        "subContribMaterialURLGen": "", \
        "sessionMaterialURLGen": "", \
    "subContribModifyURLGen":  "", \
    "materialURLGen": urlHandlers.UHMStaticMaterialDisplay.getRelativeURL, \
    "resourceURLGen": urlHandlers.UHMStaticResourceDisplay.getRelativeURL}
        view = self._view
        from MaKaC.accessControl import AccessWrapper
        outGen = outputGenerator(AccessWrapper())
        path = Config.getInstance().getStylesheetsDir()
        stylepath = "%s.xsl" % (os.path.join(path, view))
        if os.path.exists(stylepath):
            if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                includeContribution = 1
            else:
                includeContribution = 0
            return outGen.getFormattedOutput(self._rh, self._conf, stylepath, pars, 1, includeContribution, 1, 1, self._params.get("showSession",""), self._params.get("showDate",""))
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
        body = i18nformat("""
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
                timeInterval = i18nformat("""<br>(%s_("until") %s)""")%(room, eDate.strftime("%H:%M"))
        else:
            if session.getAdjustedEndDate().strftime("%d%B%Y") != \
                                        refDay.getDate().strftime("%d%B%Y") :
                timeInterval = i18nformat("""<br>(%s_("from") %s)""")%(room, sDate.strftime("%H:%M"))

        #################################
        # Fermi timezone awareness(end)   #
        #################################
        conveners=""
        l=[]
        for conv in session.getConvenerList():
            l.append("""%s"""%(self.htmlText(conv.getDirectFullName())))
        if len(l)>0:
            conveners= i18nformat("""<br><small> _("Conveners"): %s</small>""")%"; ".join(l)
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
                                    i18nformat(""" _("Session"): <i>%s </i>""")%session.getTitle())
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
                            format_date(day.getDate(), format='full'), \
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
            speakers = i18nformat("""<br><small> _("by") %s</small>""")%"; ".join(speakerList)
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
                        format_date(day.getDate(), format='full'),
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
            vars["dateInterval"]=format_datetime(sDate, format='EEEE d MMMM yyyy H:mm')
        else:
            vars["dateInterval"]=i18nformat("""_("from") %s _("to") %s""")%(
                format_datetime(sDate, format='EEEE d MMMM yyyy H:mm'),
                format_datetime(eDate, format='EEEE d MMMM yyyy H:mm'))
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
            vars["location"]= i18nformat("""%s<br><small> _("Room"):</small> %s""")%(vars["location"],
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


class WPSessionStaticDisplay(WPConferenceStaticDefaultDisplayBase):

    def __init__(self, rh, target, staticPars):
        WPConferenceStaticDefaultDisplayBase.__init__(self, rh, target.getConference())
        self._session = target
        self._staticPars = staticPars

    def _defineSectionMenu(self):
        WPConferenceStaticDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._timetableOpt)

    def _getBody(self,params):
        wc = WSessionStaticDisplay(self._getAW(), self._session)
        return wc.getHTML()

#------------------------ End Static ---------------------------------------------------------------

class WTimeTableCustomizePDF(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        url = urlHandlers.UHConfTimeTablePDF.getURL(self._conf)
        vars["getPDFURL"] = quoteattr(str(url))
        vars["showDays"] = vars.get("showDays", "all")
        vars["showSessions"] = vars.get("showSessions", "all")

        wc = WConfCommonPDFOptions(self._conf)
        vars["commonPDFOptions"] = wc.getHTML()

        return vars


class WPTimeTableCustomizePDF(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NETimeTableCustomizePDF

    def _getBody(self, params):
        wc = WTimeTableCustomizePDF(self._conf)
        return wc.getHTML(params)

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._timetableOpt)


class WConfModifPendingQueuesList(wcomponents.WTemplated):

    def __init__(self, url, title, target, list, pType):
        self._postURL = url
        self._title = title
        self._target = target
        self._list = list
        self._pType = pType

    def _cmpByConfName(self, cp1, cp2):
        if cp1 is None and cp2 is not None:
            return -1
        elif cp1 is not None and cp2 is None:
            return 1
        elif cp1 is None and cp2 is None:
            return 0
        return cmp(cp1.getTitle(), cp2.getTitle())

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

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["postURL"] = self._postURL
        vars["title"] = self._title
        vars["target"] = self._target
        vars["list"] = self._list
        vars["pType"] = self._pType

        return vars


class WConfModifPendingQueues(wcomponents.WTemplated):

    def __init__(self, conf, aw, activeTab="submitters"):
        self._conf = conf
        self._aw = aw
        self._activeTab = activeTab
        self._pendingConfManagers = self._conf.getPendingQueuesMgr().getPendingConfManagers()
        self._pendingConfSubmitters = self._conf.getPendingQueuesMgr().getPendingConfSubmitters()
        self._pendingSubmitters = self._conf.getPendingQueuesMgr().getPendingSubmitters()
        self._pendingManagers = self._conf.getPendingQueuesMgr().getPendingManagers()
        self._pendingCoordinators = self._conf.getPendingQueuesMgr().getPendingCoordinators()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        url = urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab", "conf_submitters")
        self._tabConfSubmitters = self._tabCtrl.newTab("conf_submitters", \
                                                _("Pending Conference Submitters"),str(url))
        url.addParam("tab", "conf_managers")
        self._tabConfManagers = self._tabCtrl.newTab("conf_managers", \
                                                _("Pending Conference Managers"),str(url))
        url.addParam("tab", "submitters")
        self._tabSubmitters = self._tabCtrl.newTab("submitters", \
                                                _("Pending Contribution Submitters"),str(url))
        url.addParam("tab", "managers")
        self._tabManagers = self._tabCtrl.newTab("managers", \
                                                _("Pending Managers"),str(url))
        url.addParam("tab", "coordinators")
        self._tabCoordinators = self._tabCtrl.newTab("coordinators", \
                                                _("Pending Coordinators"),str(url))
        self._tabSubmitters.setEnabled(True)
        tab = self._tabCtrl.getTabById(self._activeTab)
        if tab is None:
            tab = self._tabCtrl.getTabById("conf_submitters")
        tab.setActive()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        self._createTabCtrl()
        list = []
        url = ""
        title = ""

        if self._tabConfSubmitters.isActive():
            # Pending conference submitters
            keys = self._conf.getPendingQueuesMgr().getPendingConfSubmittersKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionConfSubm.getURL(self._conf)
            url.addParam("tab","conf_submitters")
            title = _("Pending chairpersons/speakers to become submitters")
            target = _("Conference")
            pType = "ConfSubmitters"

            for key in keys:
                list.append((key, self._pendingConfSubmitters[key][:]))

        elif self._tabConfManagers.isActive():
            # Pending conference managers
            keys = self._conf.getPendingQueuesMgr().getPendingConfManagersKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionConfMgr.getURL(self._conf)
            url.addParam("tab","conf_managers")
            title = _("Pending chairpersons to become managers")
            target = _("Conference")
            pType = "ConfManagers"

            for key in keys:
                list.append((key, self._pendingConfManagers[key][:]))

        elif self._tabSubmitters.isActive():
            # Pending submitters
            keys = self._conf.getPendingQueuesMgr().getPendingSubmittersKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
            url.addParam("tab", "submitters")
            title = _("Pending authors/speakers to become submitters")
            target = _("Contribution")
            pType = "Submitters"

            for key in keys:
                list.append((key, self._pendingSubmitters[key][:]))

        elif self._tabManagers.isActive():
            # Pending managers
            keys = self._conf.getPendingQueuesMgr().getPendingManagersKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
            url.addParam("tab", "managers")
            title = _("Pending conveners to become managers")
            target = _("Session")
            pType = "Managers"

            for key in keys:
                list.append((key, self._pendingManagers[key][:]))
                #list.sort(conference.SessionChair._cmpFamilyName)

        elif self._tabCoordinators.isActive():
            # Pending coordinators
            keys = self._conf.getPendingQueuesMgr().getPendingCoordinatorsKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
            url.addParam("tab", "coordinators")
            title = _("Pending conveners to become coordinators")
            target = _("Session")
            pType = "Coordinators"

            for key in keys:
                list.append((key, self._pendingCoordinators[key][:]))
                list.sort(conference.ConferenceParticipation._cmpFamilyName)

        html = WConfModifPendingQueuesList(str(url), title, target, list, pType).getHTML()
        vars["pendingQueue"] = wcomponents.WTabControl(self._tabCtrl, self._aw).getHTML(html)

        return vars


class WPConfModifPendingQueuesBase(WPConfModifListings):

    def __init__(self, rh, conf, activeTab=""):
        WPConfModifListings.__init__(self, rh, conf)
        self._activeTab = activeTab

    def _setActiveSideMenuItem(self):
        self._listingsMenuItem.setActive(True)


class WPConfModifPendingQueues(WPConfModifPendingQueuesBase):

    def _getTabContent(self, params):
        wc = WConfModifPendingQueues(self._conf, self._getAW(), self._activeTab)
        return wc.getHTML()


class WPConfModifPendingQueuesRemoveConfMgrConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingConfMgrs):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfMgrs = pendingConfMgrs

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfMgrs))

        msg = {'challenge': _("Are you sure you want to delete the following users pending to become conference managers?"),
               'target': "<ul>{0}</ul>".format(psubs),
               'subtext': _("Please note that they will still remain as user"),
               }

        url = urlHandlers.UHConfModifPendingQueuesActionConfMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingConfMgrs, "remove": _("remove")})


class WPConfModifPendingQueuesReminderConfMgrConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingConfMgrs):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfMgrs = pendingConfMgrs

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfMgrs))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(psubs)
               }
        url = urlHandlers.UHConfModifPendingQueuesActionConfMgr.getURL(self._conf)
        return wc.getHTML(
            msg,
            url, {
                "pendingUsers": self._pendingConfMgrs,
                "reminder": _("reminder")
                },
            severity='accept')


class WPConfModifPendingQueuesRemoveConfSubmConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingConfSubms):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfSubms = pendingConfSubms

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfSubms))

        msg = {'challenge': _("Are you sure you want to delete the following users pending to become submitters?"),
               'target': "<ul>{0}</ul>".format(psubs),
               'subtext': _("Please note that they will still remain as user"),
               }

        url = urlHandlers.UHConfModifPendingQueuesActionConfSubm.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingConfSubms, "remove": _("remove")})

class WPConfModifPendingQueuesReminderConfSubmConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingConfSubms):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfSubms = pendingConfSubms

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfSubms))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(psubs)
               }
        url = urlHandlers.UHConfModifPendingQueuesActionConfSubm.getURL(self._conf)
        return wc.getHTML(
            msg,
            url, {
                "pendingUsers": self._pendingConfSubms,
                "reminder": _("reminder")
                },
            severity='accept')

class WPConfModifPendingQueuesRemoveSubmConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingSubms):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingSubms = pendingSubms

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingSubms))

        msg = {'challenge': _("Are you sure you want to delete the following participants pending to become submitters?"),
               'target': "<ul>{0}</ul>".format(psubs),
               'subtext': _("Please note that they will still remain as participants"),
               }

        url = urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
        return wc.getHTML(msg, url, {"pendingUsers": self._pendingSubms, "remove": _("remove")})


class WPConfModifPendingQueuesReminderSubmConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingSubms):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingSubms = pendingSubms

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingSubms))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(psubs)
               }

        url = urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
        return wc.getHTML(
            msg,
            url, {
                "pendingUsers": self._pendingSubms,
                "reminder": _("reminder")
                },
            severity='accept')

class WPConfModifPendingQueuesRemoveMgrConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingMgrs):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingMgrs = pendingMgrs

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pmgrs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure you want to delete the following conveners pending to become managers?"),
               'target': "<ul>{0}</ul>".format(pmgrs),
               'subtext': _("Please note that they will still remain as conveners")
               }

        url = urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingMgrs, "remove": _("remove")})

class WPConfModifPendingQueuesReminderMgrConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingMgrs):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingMgrs = pendingMgrs

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pmgrs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(pmgrs)
               }

        url = urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingMgrs, "reminder": _("reminder")})

class WPConfModifPendingQueuesRemoveCoordConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingCoords):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingCoords = pendingCoords

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pcoords = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure you want to delete the following conveners pending to become coordinators?"),
               'target': "<ul>{0}</ul>".format(pcoords),
               'subtext': _("Please note that they will still remain as conveners")
               }

        url = urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
        return wc.getHTML(msg, url,{
                "pendingUsers": self._pendingCoords,
                "remove": _("remove")
                })

class WPConfModifPendingQueuesReminderCoordConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingCoords):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingCoords = pendingCoords

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pcoords = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(pcoords)
               }

        url = urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
        return wc.getHTML(
            msg, url, {
                "pendingUsers": self._pendingCoords,
                "reminder": _("reminder")
                })

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

class WPConfModifExistingMaterials( WPConferenceModifBase ):

    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _getPageContent( self, pars ):
        wc=wcomponents.WShowExistingMaterial(self._conf)
        return wc.getHTML( pars )

    def _setActiveTab( self ):
        self._tabMaterials.setActive()

    def _setActiveSideMenuItem( self ):
        self._materialMenuItem.setActive()


class WPDisplayFullMaterialPackage(WPConferenceDefaultDisplayBase):

    def _getBody(self, params):
        wc = WFullMaterialPackage(self._conf)
        p = {"getPkgURL": urlHandlers.UHConferenceDisplayMaterialPackagePerform.getURL(self._conf)}
        return wc.getHTML(p)


# ============================================================================
# === Room booking related ===================================================
# ============================================================================

#from MaKaC.webinterface.pages.roomBooking import WPRoomBookingBase0
class WPConfModifRoomBookingBase( WPConferenceModifBase ):

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSPackage('RoomBooking')

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['roombooking_sass'].urls()

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
        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js?%d"></script>

        """ % (baseurl, os.stat(__file__).st_mtime)

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
        wc = wcomponents.WRoomBookingDetails( self._rh, self._rh._conf )
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

class WPConfModifRoomBookingConfirmBooking( WPConfModifRoomBookingBase ):

    def __init__( self, rh ):
        self._rh = rh
        WPConfModifRoomBookingBase.__init__( self, rh, rh._conf)

    def _setActiveTab( self ):
        self._tabNewBooking.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WRoomBookingConfirmBooking( self._rh, standalone = False )
        return wc.getHTML( params )

# ============================================================================
# === Badges related =========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Badge Printing classes
"""
class WConfModifBadgePrinting(wcomponents.WTemplated):
    """ This class corresponds to the screen where badge templates are
        listed and can be created, edited, deleted, and tried.
    """

    def __init__(self, conference, user=None):
        self.__conf = conference
        self._user = user

    def _getBaseTemplateOptions(self):
        dconf = conference.CategoryManager().getDefaultConference()
        templates = dconf.getBadgeTemplateManager().getTemplates()

        options = [{'value': 'blank', 'label': _('Blank Page')}]

        for id, template in templates.iteritems():
            options.append({'value': id, 'label': template.getName()})

        return options

    def getVars(self):
        uh = urlHandlers
        templates = []
        sortedTemplates = self.__conf.getBadgeTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda x, y: cmp(x[1].getName(), y[1].getName()))

        for templateId, template in sortedTemplates:

            data = {
                'id': templateId,
                'name': template.getName(),
                'urlEdit': str(uh.UHConfModifBadgeDesign.getURL(self.__conf, templateId)),
                'urlDelete': str(uh.UHConfModifBadgePrinting.getURL(self.__conf, deleteTemplateId=templateId)),
                'urlCopy': str(uh.UHConfModifBadgePrinting.getURL(self.__conf, copyTemplateId=templateId))
            }

            templates.append(data)

        wcPDFOptions = WConfModifBadgePDFOptions(self.__conf)
        vars = wcomponents.WTemplated.getVars(self)
        vars['NewTemplateURL'] = str(uh.UHConfModifBadgeDesign.getURL(self.__conf,
                                    self.__conf.getBadgeTemplateManager().getNewTemplateId(),new = True))
        vars['CreatePDFURL'] = str(uh.UHConfModifBadgePrintingPDF.getURL(self.__conf))
        vars['templateList'] = templates
        vars['PDFOptions'] = wcPDFOptions.getHTML()
        vars['baseTemplates'] = self._getBaseTemplateOptions()

        return vars


class WConfModifBadgePDFOptions(wcomponents.WTemplated):

    def __init__(self, conference, showKeepValues=True, showTip=True):
        self.__conf = conference
        self.__showKeepValues = showKeepValues
        self.__showTip = showTip

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        vars['PagesizeNames'] = pagesizeNames
        vars['PDFOptions'] = self.__conf.getBadgeTemplateManager().getPDFOptions()
        vars['ShowKeepValues'] = self.__showKeepValues
        vars['ShowTip'] = self.__showTip

        return vars


class WPBadgeBase(WPConfModifToolsBase):

    def getCSSFiles(self):
        return WPConfModifToolsBase.getCSSFiles(self) + self._asset_env['indico_badges_css'].urls()

    def getJSFiles(self):
        return WPConfModifToolsBase.getJSFiles(self) + self._includeJSPackage('badges_js')


class WPConfModifBadgePrinting(WPBadgeBase):

    def _setActiveTab(self):
        self._tabBadges.setActive()

    def _getTabContent(self, params):
        wc = WConfModifBadgePrinting(self._conf)
        return wc.getHTML()



##------------------------------------------------------------------------------------------------------------
"""
Badge Design classes
"""
class WConfModifBadgeDesign(wcomponents.WTemplated):
    """ This class corresponds to the screen where a template
        is designed inserting, dragging and editing items.
    """

    def __init__(self, conference, templateId, new=False, user=None):
        self.__conf = conference
        self.__templateId = templateId
        self.__new = new
        self._user = user

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"] = Config.getInstance().getBaseURL() ##base url of the application, used for the ruler images
        vars["cancelURL"] = urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, templateId = self.__templateId, cancel = True)
        vars["saveBackgroundURL"] = urlHandlers.UHConfModifBadgeSaveBackground.getURL(self.__conf, self.__templateId)
        vars["loadingIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("loading")))
        vars["templateId"] = self.__templateId

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
            case.append('newDiv.html(items[itemId].toHTML());')
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
        vars["backgroundPos"] = "Stretch"

        if self.__new:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, new=True)
            vars["titleMessage"]= _("Creating new badge template")
            vars["editingTemplate"]="false"
            vars["templateData"]="[]"
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1

        elif self.__templateId is None:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf)
            vars["titleMessage"]= _("No template id given")
            vars["editingTemplate"]="false"
            vars["templateData"]="[]"
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


class WPConfModifBadgeDesign(WPBadgeBase):

    def __init__(self, rh, conf, templateId=None, new=False, baseTemplateId="blank"):
        WPBadgeBase.__init__(self, rh, conf)
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

    def _setActiveTab(self):
        self._tabBadges.setActive()

    def _getTabContent(self, params):
        wc = WConfModifBadgeDesign(self._conf, self.__templateId, self.__new)
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
            pagesizeOptions.append('<option ')
            if pagesizeName == 'A4':
                pagesizeOptions.append('selected="selected"')
            pagesizeOptions.append('>')
            pagesizeOptions.append(pagesizeName)
            pagesizeOptions.append('</option>')

        vars['pagesizes'] = "".join(pagesizeOptions)

        fontsizeOptions = []
        for fontsizeName in PDFSizes().PDFfontsizes:
            fontsizeOptions.append('<option ')
            if fontsizeName == 'normal':
                fontsizeOptions.append('selected="selected"')
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
class WConfModifPosterPrinting(wcomponents.WTemplated):
    """ This class corresponds to the screen where poster templates are
        listed and can be created, edited, deleted, and tried.
    """

    def __init__(self, conference, user=None):
        self.__conf = conference
        self._user = user

    def _getFullTemplateListOptions(self):
        templates = {}
        templates['global'] = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplates()
        templates['local'] = self.__conf.getPosterTemplateManager().getTemplates()
        options = []

        def _iterTemplatesToObjectList(key, templates):
            newList = []

            for id, template in templates.iteritems():
                pKey = ' (' + key + ')'
                # Only if the template is 'global' should it have the word prefixed.
                value = key + str(id) if key == 'global' else str(id)
                newList.append({'value': value,
                                'label': template.getName() + pKey})

            return newList

        for k, v in templates.iteritems():
            options.extend(_iterTemplatesToObjectList(k, v))

        return options

    def _getBaseTemplateListOptions(self):
        templates = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplates()
        options = [{'value': 'blank', 'label': _('Blank Page')}]

        for id, template in templates.iteritems():
            options.append({'value': id, 'label': template.getName()})

        return options

    def getVars(self):
        uh = urlHandlers
        templates = []
        wcPDFOptions = WConfModifPosterPDFOptions(self.__conf)
        sortedTemplates = self.__conf.getPosterTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))

        for templateId, template in sortedTemplates:

            data = {
                'id': templateId,
                'name': template.getName(),
                'urlEdit': str(uh.UHConfModifPosterDesign.getURL(self.__conf, templateId)),
                'urlDelete': str(uh.UHConfModifPosterPrinting.getURL(self.__conf, deleteTemplateId=templateId)),
                'urlCopy': str(uh.UHConfModifPosterPrinting.getURL(self.__conf, copyTemplateId=templateId))
            }

            templates.append(data)

        vars = wcomponents.WTemplated.getVars(self)
        vars["NewTemplateURL"] = str(uh.UHConfModifPosterDesign.getURL(self.__conf, self.__conf.getPosterTemplateManager().getNewTemplateId(),new=True))
        vars["CreatePDFURL"]= str(uh.UHConfModifPosterPrintingPDF.getURL(self.__conf))
        vars["templateList"] = templates
        vars['PDFOptions'] = wcPDFOptions.getHTML()
        vars['baseTemplates'] = self._getBaseTemplateListOptions()
        vars['fullTemplateList'] = self._getFullTemplateListOptions()

        return vars

class WConfModifPosterPDFOptions(wcomponents.WTemplated):

    def __init__(self, conference, user=None):
        self.__conf = conference
        self._user= user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        pagesizeOptions = []

        for pagesizeName in pagesizeNames:
            pagesizeOptions.append('<option ')

            if pagesizeName == 'A4':
                pagesizeOptions.append('selected="selected"')

            pagesizeOptions.append('>')
            pagesizeOptions.append(pagesizeName)
            pagesizeOptions.append('</option>')

        vars['pagesizes'] = "".join(pagesizeOptions)

        return vars

class WPConfModifPosterPrinting(WPBadgeBase):

    def _setActiveTab(self):
        self._tabPosters.setActive()

    def _getTabContent(self, params):
        wc = WConfModifPosterPrinting(self._conf)
        return wc.getHTML()

##------------------------------------------------------------------------------------------------------------
"""
Poster Design classes
"""
class WConfModifPosterDesign( wcomponents.WTemplated ):
    """ This class corresponds to the screen where a template
        is designed inserting, dragging and editing items.
    """

    def __init__(self, conference, templateId, new=False, user=None):
        self.__conf = conference
        self.__templateId = templateId
        self.__new = new
        self._user = user


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"] = Config.getInstance().getBaseURL()  # base url of the application, used for the ruler images
        vars["cancelURL"] = urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, templateId = self.__templateId, cancel = True)
        vars["saveBackgroundURL"] = urlHandlers.UHConfModifPosterSaveBackground.getURL(self.__conf, self.__templateId)
        vars["loadingIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("loading")))
        vars["templateId"] = self.__templateId

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
            case.append('newDiv.html(items[itemId].toHTML());')
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
            vars["templateData"]="[]"
            vars["editingTemplate"]="false"


        elif self.__templateId is None:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf)
            vars["titleMessage"]= _("No template id given")
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1
            vars["backgroundPos"]="Stretch"
            vars["templateData"] = "[]"
            vars["editingTemplate"]="false"


        else:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf)
            vars["titleMessage"]= _("Editing poster template")
            vars["editingTemplate"]="true"
            templateDataString = jsonEncode(self.__conf.getPosterTemplateManager().getTemplateData(self.__templateId))
            vars["templateData"]= templateDataString

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


class WPConfModifPosterDesign(WPBadgeBase):

    def __init__(self, rh, conf, templateId=None, new=False, baseTemplateId="blank"):
        WPBadgeBase.__init__(self, rh, conf)
        self.__templateId = templateId
        self.__new = new
        self.__baseTemplate = baseTemplateId

    def _setActiveTab(self):
        self._tabPosters.setActive()

    def _getTabContent(self, params):
        wc = WConfModifPosterDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()

    def sortByName(x,y):
        return cmp(x.getFamilyName(),y.getFamilyName())

class WPConfModifPreviewCSS( WPConferenceDefaultDisplayBase ):

    def __init__( self, rh, conf, selectedCSSId):
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )

        self._conf = conf
        self._cssTplsModule = ModuleHolder().getById("cssTpls")
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
        path = Config.getInstance().getCssBaseURL()
        timestamp = os.stat(__file__).st_mtime
        printCSS = """
        <link rel="stylesheet" type="text/css" href="%s/Conf_Basic.css?%d" >
            """ % (path, timestamp)

        if self._selectedCSS:
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s" >"""%self._selectedCSS.getURL()
        elif self._styleMgr.getCSS():
            printCSS = printCSS + """<link rel="stylesheet" type="text/css" href="%s" >"""%self._styleMgr.getCSS().getURL()
        return printCSS


class WPreviewPage( wcomponents.WTemplated ):
    pass
