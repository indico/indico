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
from flask import request, session

from indico.util.translations import LazyProxy

from MaKaC.plugins import OldObservable
from MaKaC.plugins.base import extension_point

import os
import sys
import types
import exceptions
import urllib
import pkg_resources
import binascii
from lxml import etree
from operator import attrgetter
from pytz import timezone
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from xml.sax.saxutils import escape, quoteattr

from MaKaC.i18n import _
from MaKaC.plugins import PluginsHolder, OldObservable
from MaKaC.plugins.base import extension_point
from MaKaC import conference
from MaKaC import user
from MaKaC import schedule
from MaKaC.common import info
from MaKaC import domain
from MaKaC.webinterface import urlHandlers
from indico.core import config as Configuration
from MaKaC import webcast
from MaKaC.accessControl import AdminList
from MaKaC.common.url import URL
from indico.core.config import Config
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.conference import Conference, Category
from MaKaC.webinterface.common.timezones import TimezoneRegistry, DisplayTimezoneRegistry
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc, utctimestamp2date
from MaKaC.webinterface.common import contribFilters
from MaKaC.common import filters, utils
from MaKaC.common.TemplateExec import escapeHTMLForJS
from MaKaC.errors import MaKaCError
from MaKaC.webinterface import displayMgr
from MaKaC.common.ContextHelp import ContextHelp
from MaKaC.rb_tools import FormMode, overlap
from MaKaC.authentication.AuthenticationMgr import AuthenticatorMgr
from MaKaC.common.TemplateExec import truncateTitle
from MaKaC.fossils.user import IAvatarFossil
from MaKaC.common.fossilize import fossilize
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.Announcement import getAnnoucementMgrInstance
from MaKaC.roomMapping import RoomMapperHolder
import MaKaC.common.TemplateExec as templateEngine

from indico.core.db import DBMgr
from indico.util.i18n import i18nformat, parseLocale, getLocaleDisplayNames
from indico.util.date_time import utc_timestamp, is_same_month
from indico.core.index import Catalog
from indico.web.http_api import API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED
from indico.web.http_api.util import generate_public_auth_request

MIN_PRESENT_EVENTS = 6
OPTIMAL_PRESENT_EVENTS = 10


class WTemplated(OldObservable):
    """This class provides a basic implementation of a web component (an
       object which generates HTML related to a certain feature or
       functionality) which relies in a template file for generating the
       HTML it's in charge of.
       By templating file we mean that there will be a file in the file
       system (uniquely identified) which will contain HTML code plus some
       "variables" (dynamic values). The class will take care of opening
       this file, parsing the HTML and replacing the variables by the
       corresponding values.
    """
    tplId = None

    @classmethod
    def forModule(cls, module, *args):
        tplobj = cls(*args)
        tplobj._for_module = module
        return tplobj

    def __init__(self, tpl_name=None):
        if tpl_name is not None:
            self.tplId = tpl_name

        self._rh = ContextManager.get('currentRH', None)

    def _getSpecificTPL(self, dir, tplId, extension="tpl"):
        """
            Checks if there is a defined set of specific templates (i.e. CERN),
            and if there is a specific file for this page, for this template set.
            Returns the file that should be used.
        """


        if DBMgr.getInstance().isConnected():
            template = info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultTemplateSet()

            if template != None :
                specTpl = "%s.%s.%s" % (tplId, template, extension)

                if os.path.exists(os.path.join(dir,specTpl)):
                    return specTpl


        return "%s.%s" % (tplId, extension)

    def _setTPLFile(self):
        """Sets the TPL (template) file for the object. It will try to get
            from the configuration if there's a special TPL file for it and
            if not it will look for a file called as the class name+".tpl"
            in the configured TPL directory.
        """
        cfg = Configuration.Config.getInstance()

        #file = cfg.getTPLFile(self.tplId)

        # because MANY classes skip the constructor...
        tplDir = cfg.getTPLDir()
        if hasattr(self, '_for_module') and self._for_module:
            self.tplFile = pkg_resources.resource_filename(self._for_module.__name__,
                                                          'tpls/{0}.tpl'.format(self.tplId))
        else:
            self.tplFile = self._getSpecificTPL(tplDir, self.tplId)

        hfile = self._getSpecificTPL(os.path.join(tplDir,'chelp'),
                                              self.tplId,
                                              extension='wohl')

        self.helpFile = os.path.join('chelp', hfile)

    def getVars( self ):
        """Returns a dictionary containing the TPL variables that will
            be passed at the TPL formating time. For this class, it will
            return the configuration user defined variables.
           Classes inheriting from this one will have to take care of adding
            their variables to the ones returned by this method.
        """
        self._rh = ContextManager.get('currentRH', None)

        cfg = Configuration.Config.getInstance()
        vars = cfg.getTPLVars()

        for paramName in self.__params:
            vars[ paramName ] = self.__params[ paramName ]

        return vars

    def getHTML( self, params=None ):
        """Returns the HTML resulting of formating the text contained in
            the corresponding TPL file with the variables returned by the
            getVars method.
            Params:
                params -- additional paramters received from the caller
        """

        self._rh = ContextManager.get('currentRH', None)
        if self.tplId == None:
            self.tplId = self.__class__.__name__[1:]
        self._setTPLFile()
        self.__params = {}
        if params != None:
            self.__params = params

        # include context help info, if it exists
        helpText = None
        if os.path.exists(self.helpFile):
            try:
                fh = open( self.helpFile, "r")
                helpText = fh.read()
                fh.close()
            except exceptions.IOError:
                pass

        vars = self.getVars()

        vars['__rh__'] = self._rh
        vars['self_'] = self

        tempHTML = templateEngine.render(self.tplFile, vars, self)

        if self._rh and request.is_secure:
            imagesBaseURL = Config.getInstance().getImagesBaseURL()
            imagesBaseSecureURL = urlHandlers.setSSLPort(Config.getInstance().getImagesBaseSecureURL())
            tempHTML = tempHTML.replace(imagesBaseURL, imagesBaseSecureURL)
            tempHTML = tempHTML.replace(escapeHTMLForJS(imagesBaseURL), escapeHTMLForJS(imagesBaseSecureURL))

        if helpText == None:
            return tempHTML
        else:
            try:
                return ContextHelp().merge(self.tplId, tempHTML, helpText)
            except etree.LxmlError, e:
                if tempHTML.strip() == '':
                    raise MaKaCError(_("Template " + str(self.tplId) + " produced empty output, and it has a .wohl file. Error: " + str(e)))
                else:
                    raise

    @staticmethod
    def htmlText(param):
        if not param:
            return ''
        if not isinstance(param, (basestring, LazyProxy)):
            param = repr(param)
        if isinstance(param, unicode):
            param = param.encode('utf-8')
        return escape(param)

    @staticmethod
    def textToHTML(param):
        if param != "":
            if param.lower().find("<br>") == -1 and param.lower().find("<p>") == -1 and param.lower().find("<li>") == -1 and param.lower().find("<table") == -1:
                param=param.replace("\r\n", "<br>")
                param=param.replace("\n","<br>")
            return param
        return "&nbsp;"

    def _escapeChars(self, text):
        # Does nothing right now - it used to replace % with %% for the old-style templates
        return text


class WHTMLHeader(WTemplated):

    def __init__(self, tpl_name=None):
        WTemplated.__init__(self)

    def getVars(self):
        tvars = WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        tvars["analyticsActive"] = minfo.isAnalyticsActive()
        tvars["analyticsCode"] = minfo.getAnalyticsCode()
        tvars["analyticsCodeLocation"] = minfo.getAnalyticsCodeLocation()
        tvars['timestamp'] = "%d" % os.stat(__file__).st_mtime
        return tvars


class WHeader(WTemplated):
    """Templating web component for generating a common HTML header for
        the web interface.
    """
    def __init__(self, aw, locTZ="", isFrontPage=False, currentCategory=None, tpl_name=None):
        WTemplated.__init__(self, tpl_name=tpl_name)
        self._currentuser = aw.getUser()
        self._locTZ = locTZ
        self._aw = aw
        self._isFrontPage = isFrontPage
        self.__currentCategory = currentCategory

    """
        Returns timezone string that is show to the user.
    """
    def _getTimezoneDisplay( self, timezone ):
        if timezone == 'LOCAL':
            if self._locTZ:
                return self._locTZ
            else:
                return info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        else:
            return timezone

    """
        Returns an array with the status (Public, Protected, Restricted) and extra info(domain list)
    """
    def _getProtection(self, target):
        if target.isProtected():
            return ["Restricted", _("Restricted")]
        domain_list = target.getAccessController().getAnyDomainProtection()
        if domain_list:
            return ["DomainProtected", _("%s domain only")%(", ".join(map(lambda x: x.getName(), domain_list)))]
        return ["Public", _("Public")]

    def getVars( self ):
        vars = WTemplated.getVars( self )
        #urlHandlers.UHUserDetails.getURL(self._currentuser)
        # TODO: Remove this after CRBS headers are fixed!
        if self._currentuser:
            vars["userInfo"] = """<font size="-1"><a class="topbar" href="%s" target="_blank">%s</a> - <a href="%s">logout</a></font>"""%(urlHandlers.UHUserDetails.getURL(self._currentuser), self._currentuser.getFullName(), vars["logoutURL"])
            vars["userDetails"] = 'class="topbar" href="%s" target="_blank"'%urlHandlers.UHUserDetails.getURL(self._currentuser)

        else:
            vars["userInfo"] = """<a href="%s">login</a>"""%(vars["loginURL"])
            vars["userDetails"] = ""
        # *****************

        vars["currentUser"] = self._currentuser

        imgLogo=Configuration.Config.getInstance().getSystemIconURL( "logoIndico" )
        imgLogin=Configuration.Config.getInstance().getSystemIconURL( "login" )

        vars["imgLogo"] = imgLogo
        vars["imgLogin"] = imgLogin
        vars["isFrontPage"] = self._isFrontPage
        vars["target"] = vars["currentCategory"] = self.__currentCategory

        selLang = session.lang
        vars["ActiveTimezone"] = session.timezone
        """
            Get the timezone for displaying on top of the page.
            1. If the user has "LOCAL" timezone then show the timezone
            of the event/category. If that's not possible just show the
            standard timezone.
            2. If the user has a custom timezone display that one.
        """
        vars["ActiveTimezoneDisplay"] = self._getTimezoneDisplay(vars["ActiveTimezone"])

        vars["SelectedLanguage"] = selLang
        locale = parseLocale(selLang)
        vars["SelectedLanguageName"] = locale.languages[locale.language].encode('utf-8')
        vars["Languages"] = getLocaleDisplayNames()

        if DBMgr.getInstance().isConnected():
            vars["title"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTitle()
            vars["organization"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getOrganisation()
        else:
            vars["title"] = "Indico"
            vars["organization"] = ""

        vars['searchBox']= ""
        vars["categId"] = self.__currentCategory.getId() if self.__currentCategory else 0
        extension_point("fillCategoryHeader", vars)

        # Check if room booking module is active
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars['roomBooking'] = minfo.getRoomBookingModuleActive()
        vars['protectionDisclaimerProtected'] = minfo.getProtectionDisclaimerProtected()
        vars['protectionDisclaimerRestricted'] = minfo.getProtectionDisclaimerRestricted()
        #Build a list of items for the administration menu
        adminList = AdminList.getInstance()
        adminItemList = []
        if self._currentuser:
            if self._currentuser.isAdmin() or not adminList.getList():
                adminItemList.append({'id': 'serverAdmin', 'url': urlHandlers.UHAdminArea.getURL(), 'text': _("Server admin")})
            self._notify("addParamsToHeaderItem",{"user": self._currentuser}, adminItemList)
            if webcast.HelperWebcastManager.getWebcastManagerInstance().isManager(self._currentuser):
                adminItemList.append({'id': 'webcastAdmin', 'url': urlHandlers.UHWebcast.getURL(), 'text': _("Webcast Admin")})

        vars["adminItemList"] = adminItemList
        vars["getProtection"] = lambda x: self._getProtection(x)

        announcement_header = getAnnoucementMgrInstance().getText()
        vars["announcement_header"] = announcement_header
        vars["announcement_header_hash"] = binascii.crc32(announcement_header)

        return vars


class WStaticWebHeader(WTemplated):
    """Templating web component for generating the HTML header for
        the static web interface when generating a DVD.
    """
    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars

class WManagementHeader( WHeader ):
    """Templating web component for generating the HTML header for
        the management web interface.
    """
    pass

class WHelpHeader( WHeader ):
    """Templating web component for generating the HTML header for
        the help web interface.
    """
    pass

class WRoomBookingHeader( WHeader ):
    """Templating web component for generating the HTML header for
        the (standalone) room booking web interface.
    """
    pass

class WConferenceHeader(WHeader):
    """Templating web component for generating the HTML header for
        the conferences' web interface.
    """

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw
        WHeader.__init__(self, self._aw, tpl_name='EventHeader')
        tzUtil = DisplayTZ(self._aw,self._conf)
        self._locTZ = tzUtil.getDisplayTZ()

    def getVars( self ):
        vars = WHeader.getVars( self )
        vars["categurl"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])

        vars["conf"] = vars["target"] = self._conf;
        vars["urlICSFile"] = urlHandlers.UHConferenceToiCal.getURL(self._conf, detail = "events")

        vars["imgLogo"] = Configuration.Config.getInstance().getSystemIconURL( "miniLogo" )
        vars["MaKaCHomeURL"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])

        # Default values to avoid NameError while executing the template
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        styles = styleMgr.getExistingStylesForEventType("conference")

        vars["viewoptions"] = list({"id": sid, "name": styleMgr.getStyleName(sid)} \
                                       for sid in sorted(styles, key=styleMgr.getStyleName))
        vars["SelectedStyle"] = ""
        vars["pdfURL"] = ""
        vars["displayURL"] = str(urlHandlers.UHConferenceOtherViews.getURL(self._conf))

        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = False
        vars["showMoreButton"] = True
        vars["showExportToICal"] = True
        vars["showExportToPDF"] = False
        vars["showDLMaterial"] = True
        vars["showLayout"] = True

        vars["usingModifKey"]=False
        if self._conf.canKeyModify(self._aw):
            vars["usingModifKey"]=True
        vars["displayNavigationBar"] = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf, False).getDisplayNavigationBar()

        # This is basically the same WICalExportBase, but we need some extra
        # logic in order to have the detailed URLs
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        apiMode = minfo.getAPIMode()

        vars["icsIconURL"] = str(Config.getInstance().getSystemIconURL("ical_grey"))
        vars["apiMode"] = apiMode
        vars["signingEnabled"] = apiMode in (API_MODE_SIGNED, API_MODE_ONLYKEY_SIGNED, API_MODE_ALL_SIGNED)
        vars["persistentAllowed"] = minfo.isAPIPersistentAllowed()
        user  = self._aw.getUser()
        apiKey = user.getAPIKey() if user else None

        topURLs = generate_public_auth_request(apiMode, apiKey, '/export/event/%s.ics' % \
            self._conf.getId(), {}, minfo.isAPIPersistentAllowed() and \
            (apiKey.isPersistentAllowed() if apiKey else False), minfo.isAPIHTTPSRequired())
        urls = generate_public_auth_request(apiMode, apiKey, '/export/event/%s.ics' % \
            self._conf.getId(), {'detail': 'contributions'}, minfo.isAPIPersistentAllowed() and \
            (apiKey.isPersistentAllowed() if apiKey else False), minfo.isAPIHTTPSRequired())

        vars["requestURLs"] = {
            'publicRequestURL': topURLs["publicRequestURL"],
            'authRequestURL':  topURLs["authRequestURL"],
            'publicRequestDetailedURL': urls["publicRequestURL"],
            'authRequestDetailedURL':  urls["authRequestURL"]
        }

        vars["persistentUserEnabled"] = apiKey.isPersistentAllowed() if apiKey else False
        vars["apiActive"] = apiKey != None
        vars["userLogged"] = user != None
        vars['apiKeyUserAgreement'] = minfo.getAPIKeyUserAgreement()
        vars['apiPersistentUserAgreement'] = minfo.getAPIPersistentUserAgreement()

        return vars


class WMenuConferenceHeader( WConferenceHeader ):
    """Templating web component for generating the HTML header for
        the conferences' web interface with a menu
    """
    def __init__(self, aw, conf, modifKey=False):
        self._conf = conf
        self._modifKey=modifKey
        self._aw=aw
        WConferenceHeader.__init__(self, self._aw, conf)

    def getVars( self ):
        vars = WConferenceHeader.getVars( self )
        vars["categurl"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        url = urlHandlers.UHConfEnterModifKey.getURL(self._conf)
        url.addParam("redirectURL",urlHandlers.UHConferenceOtherViews.getURL(self._conf))
        vars["confModif"] =  i18nformat("""<a href=%s> _("manage")</a>""")%quoteattr(str(url))
        if self._conf.canKeyModify(self._aw):
            url = urlHandlers.UHConfCloseModifKey.getURL(self._conf)
            url.addParam("redirectURL",urlHandlers.UHConferenceOtherViews.getURL(self._conf))
            vars["confModif"] = i18nformat("""<a href=%s>_("exit manage")</a>""")%quoteattr(str(url))

        # Dates Menu
        tz = DisplayTZ(self._aw,self._conf,useServerTZ=1).getDisplayTZ()
        sdate = self._conf.getStartDate().astimezone(timezone(tz))
        edate = self._conf.getEndDate().astimezone(timezone(tz))
        dates = []
        if sdate.strftime("%Y-%m-%d") != edate.strftime("%Y-%m-%d"):
            selected = ""
            if vars.has_key("selectedDate"):
                selectedDate = vars["selectedDate"]
                if selectedDate == "all" or selectedDate == "":
                    selected = "selected"
            else:
                selectedDate = "all"
            dates = [ i18nformat(""" <select name="showDate" onChange="document.forms[0].submit();" style="font-size:8pt;"><option value="all" %s>- -  _("all days") - -</option> """)%selected]
            while sdate.strftime("%Y-%m-%d") <= edate.strftime("%Y-%m-%d"):
                selected = ""
                if selectedDate == sdate.strftime("%d-%B-%Y"):
                    selected = "selected"
                d = sdate.strftime("%d-%B-%Y")
                dates.append(""" <option value="%s" %s>%s</option> """%(d, selected, d))
                sdate = sdate + timedelta(days=1)
            dates.append("</select>")
        else:
            dates.append("""<input type="hidden" name="showDate" value="all">""")
        # Sessions Menu
        sessions = []
        if len(self._conf.getSessionList()) != 0:
            selected = ""
            if vars.has_key("selectedSession"):
                selectedSession = vars["selectedSession"]
                if selectedSession == "all" or selectedSession == "":
                    selected = "selected"
            else:
                selectedSession = "all"
            sessions = [ i18nformat(""" <select name="showSession" onChange="document.forms[0].submit();" style="font-size:8pt;"><option value="all" %s>- -  _("all sessions") - -</option> """)%selected]
            for session in self._conf.getSessionList():
                selected = ""
                id = session.getId()
                if id == selectedSession:
                    selected = "selected"
                sessions.append(""" <option value="%s" %s>%s</option> """%(id, selected, session.getTitle()))
            sessions.append("</select>")
        else:
            sessions.append("""<input type="hidden" name="showSession" value="all">""")
        # Handle hide/show contributions option
        hideContributions = None;
        if len(self._conf.getSessionList()) != 0:
            if vars.has_key("detailLevel"):
                if vars["detailLevel"] == "session":
                    hideContributions = "checked"
                else:
                    hideContributions = ""
        # Save to session
        vars["hideContributions"] = hideContributions;

        evaluation = self._conf.getEvaluation()
        if self._conf.hasEnabledSection("evaluation") and evaluation.isVisible() and evaluation.inEvaluationPeriod() and evaluation.getNbOfQuestions()>0 :
            vars["evaluation"] =  i18nformat("""<a href="%s"> _("Evaluation")</a>""")%urlHandlers.UHConfEvaluationDisplay.getURL(self._conf)
        else :
            vars["evaluation"] = ""

        urlCustPrint = urlHandlers.UHConferenceOtherViews.getURL(self._conf)
        urlCustPrint.addParam("showDate", vars.get("selectedDate", "all"))
        urlCustPrint.addParam("showSession", vars.get("selectedSession", "all"))
        urlCustPrint.addParam("fr", "no")
        urlCustPrint.addParam("view", vars["currentView"])
        vars["printURL"]=str(urlCustPrint)

        vars["printIMG"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "printer" )))
        urlCustPDF=urlHandlers.UHConfTimeTableCustomizePDF.getURL(self._conf)
        urlCustPDF.addParam("showDays", vars.get("selectedDate", "all"))
        urlCustPDF.addParam("showSessions", vars.get("selectedSession", "all"))
        vars["pdfURL"]=quoteattr(str(urlCustPDF))
        vars["pdfIMG"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "pdf" )))
        urlMatPack=urlHandlers.UHConferenceDisplayMaterialPackage.getURL(self._conf)
        vars["matPackURL"]=quoteattr(str(urlMatPack))
        vars["zipIMG"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "smallzip" )))

        return vars

class WMenuMeetingHeader( WConferenceHeader ):
    """Templating web component for generating the HTML header for
        the meetings web interface with a menu
    """
    def __init__(self, aw, conf, modifKey=False):
        self._conf = conf
        self._modifKey=modifKey
        self._aw=aw
        WHeader.__init__(self, self._aw, tpl_name='EventHeader')
        tzUtil = DisplayTZ(self._aw,self._conf)
        self._locTZ = tzUtil.getDisplayTZ()


    def getVars( self ):
        vars = WConferenceHeader.getVars( self )

        vars["categurl"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        styles = styleMgr.getExistingStylesForEventType(vars["type"])

        viewoptions = []
        if len(styles) != 0:
            styles.sort(key=styleMgr.getStyleName)
            for styleId in styles:
                viewoptions.append({"id": styleId, "name": styleMgr.getStyleName(styleId) })
        vars["viewoptions"] = viewoptions
        vars["SelectedStyle"] = styleMgr.getStyleName(vars["currentView"])
        vars["displayURL"] = urlHandlers.UHConferenceDisplay.getURL(self._rh._conf)

        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = True
        vars["showExportToPDF"] = True
        vars["showDLMaterial"] = True
        vars["showLayout"] = True


        # Dates Menu
        tz = DisplayTZ(self._aw,self._conf,useServerTZ=1).getDisplayTZ()
        sdate = self._conf.getStartDate().astimezone(timezone(tz))
        edate = self._conf.getEndDate().astimezone(timezone(tz))
        dates = []
        selected = ""
        if vars.has_key("selectedDate"):
            selectedDate = vars["selectedDate"]
            if selectedDate == "all" or selectedDate == "":
                selected = "selected"
        else:
            selectedDate = "all"
        dates = [ i18nformat(""" <option value="all" %s>- -  _("all days") - -</option> """)%selected]
        while sdate.strftime("%Y-%m-%d") <= edate.strftime("%Y-%m-%d"):
            selected = ""
            if selectedDate == sdate.strftime("%d-%B-%Y"):
                selected = "selected"
            d = sdate.strftime("%d-%B-%Y")
            dates.append(""" <option value="%s" %s>%s</option> """%(d, selected, d))
            sdate = sdate + timedelta(days=1)
        vars["datesMenu"] = "".join(dates);

        # Sessions Menu
        sessions = []
        selected = ""
        if vars.has_key("selectedSession"):
            selectedSession = vars["selectedSession"]
            if selectedSession == "all" or selectedSession == "":
                selected = "selected"
        else:
            selectedSession = "all"
        sessions = [ i18nformat(""" <option value="all" %s>- -  _("all sessions") - -</option> """)%selected]
        for session in self._conf.getSessionList():
            selected = ""
            id = session.getId()
            if id == selectedSession:
                selected = "selected"
            title = session.getTitle()
            if len(title) > 60:
                title = title[0:40] + "..."
            sessions.append(""" <option value="%s" %s>%s</option> """%(id, selected, title))
        vars["sessionsMenu"] = "".join(sessions);

        # Handle hide/show contributions option
        hideContributions = None;
        if len(self._conf.getSessionList()) != 0:
            if vars.has_key("detailLevel"):
                if vars["detailLevel"] == "session":
                    hideContributions = "checked"
                else:
                    hideContributions = ""
        vars["hideContributions"] = hideContributions;

        urlCustPrint = urlHandlers.UHConferenceOtherViews.getURL(self._conf)
        urlCustPrint.addParam("showDate", vars.get("selectedDate", "all"))
        urlCustPrint.addParam("showSession", vars.get("selectedSession", "all"))
        urlCustPrint.addParam("detailLevel", vars.get("detailLevel", "all"))
        urlCustPrint.addParam("fr", "no")
        urlCustPrint.addParam("view", vars["currentView"])
        vars["printURL"]=str(urlCustPrint)


        urlCustPDF=urlHandlers.UHConfTimeTableCustomizePDF.getURL(self._conf)
        urlCustPDF.addParam("showDays", vars.get("selectedDate", "all"))
        urlCustPDF.addParam("showSessions", vars.get("selectedSession", "all"))
        # Add the view as a parameter to keep track of the current layout
        # when exporting a pdf
        urlCustPDF.addParam("view", vars["currentView"])
        vars["pdfURL"]=str(urlCustPDF)


        return vars

class WMenuSimpleEventHeader( WMenuMeetingHeader ):
    """Templating web component for generating the HTML header for
        the simple event' web interface with a menu
    """

    def getVars( self ):
        vars = WMenuMeetingHeader.getVars( self )
        vars["confModif"] = """<a href=%s>manage</a>"""%quoteattr(str(urlHandlers.UHConfEnterModifKey.getURL(self._conf)))
        if self._conf.canKeyModify(self._aw):
            vars["confModif"] = """<a href=%s>exit manage</a>"""%quoteattr(str(urlHandlers.UHConfCloseModifKey.getURL(self._conf)))

        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = False
        vars["showExportToPDF"] = False

        vars["accessWrapper"] = self._aw
        return vars



class WFooter(WTemplated):
    """Templating web component for generating a common HTML footer for the
        web interface.
    """

    def __init__(self, tpl_name = None, isFrontPage = False):
        WTemplated.__init__(self, tpl_name)
        self._isFrontPage = isFrontPage

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["isFrontPage"] = self._isFrontPage;

        if not vars.has_key("modificationDate"):
            vars["modificationDate"] = ""

        if not vars.has_key("shortURL"):
            vars["shortURL"] = ""

        vars['debugActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()

        return vars


class WEventFooter(WFooter):
    """
    Specialization of WFooter that provides extra info for events
    """
    def __init__(self, conf, tpl_name = None, isFrontPage = False):
        WFooter.__init__(self, tpl_name, isFrontPage)
        self._conf = conf

    def _gCalDateFormat(self, dtime):
        return dtime.strftime("%Y%m%dT%H%M%SZ")

    def getVars(self):
        v = WFooter.getVars(self)

        cid = self._conf.getUrlTag().strip() or self._conf.getId()
        location = self._conf.getLocation().getName() if self._conf.getLocation() else ''

        if self._conf.getRoom() and self._conf.getRoom().getName():
            location = "%s (%s)" % (self._conf.getRoom().getName(), location)

        description = self._conf.getDescription()

        if len(description) > 1000:
            description = description[:997] + "..."

        if description:
            description += '\n\n'

        description += Config.getInstance().getShortEventURL() + cid

        v['gc_params'] = urllib.urlencode({
            'action': 'TEMPLATE',
            'text': self._conf.getTitle(),
            'dates': "%s/%s" % (self._gCalDateFormat(self._conf.getStartDate()),
                                self._gCalDateFormat(self._conf.getEndDate())),
            'details': description,
            'location': location,
            'trp': False,
            'sprop': [str(urlHandlers.UHConferenceDisplay.getURL(self._conf)),
                      'name:indico']
            })

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        app_data = minfo.getSocialAppConfig()

        v['icalURL'] = urlHandlers.UHConferenceToiCal.getURL(self._conf)
        v["shortURL"] = Config.getInstance().getShortEventURL() + cid
        v["app_data"] = app_data
        v["showSocial"] = app_data.get('active', False) and self._conf.getDisplayMgr().getShowSocialApps()
        v['conf'] = self._conf
        self._notify('eventDetailFooter', v)

        return v


class WNavigationDrawer(WTemplated):

    def __init__( self, pars, bgColor = None, type = None):
        self._target = pars["target"]
        self._isModif = pars.get("isModif", False)
        self._track = pars.get("track", None) #for abstracts viewed inside a track
        self._bgColor = bgColor
        self._actionType = type #type of action

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["target"] = self._target
        vars["isModif"]= self._isModif
        vars["track"]= self._track
        vars["bgColor"] = self._bgColor
        vars["actionType"] = self._actionType
        return vars

    def getHTML(self, params=None):
        return WTemplated.getHTML(self, params)

class WSimpleNavigationDrawer(WTemplated):

    def __init__( self, title, handler = None, bgColor = None, **pars  ):
        self._urlHandler = handler
        self._pars = pars
        self._title = title
        self._bgColor = bgColor

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["urlHandler"] = self._urlHandler
        vars["title"] = self._title
        vars["pars"] = self._pars
        vars["bgColor"] = self._bgColor
        return vars

    def getHTML(self, params=None):
        return WTemplated.getHTML(self, params)

class WBannerModif(WTemplated):

    def __init__(self, path = [], itemType = "", title = ""):
        WTemplated.__init__( self, "BannerModif" )
        self._path = path
        self._title = title
        self._type = itemType

    def getHTML(self):
        """ Retrieves the HTML of the banner of the modification interface
            of the given target event / category / contribution / abstract / etc.
            'track' argument should be provided for abstracts viewed inside a track.
            If originUrl and originPageTitle is set then this link his added to the end
            of the breadcrumb showed in the banner.
        """

        return WTemplated.getHTML(self, {"type" : self._type, "path": self._path, "title": self._title})

class WTimetableBannerModif(WBannerModif):

    def __init__(self, aw, target):
        ## PATH
        # Iterate till conference is reached
        conf = target.getConference()
        path = self._getOwnerBasePath(target)
        # TITLE AND TYPE
        itemType = type(target).__name__
        title = target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)

    def _getOwnerBasePath(self, target):
        path = []
        obj = target
        while obj:
            obj = obj.getOwner()
            if type(obj) != Conference and type(obj) != conference.Category:
                path.append({"url": urlHandlers.UHHelper.getModifUH(type(obj)).getURL(obj),
                             "title": truncateTitle(obj.getTitle(), 30),
                             "type": type(obj).__name__})
                if type(obj) == conference.Session:
                    path[-1]["sessionTimetableURL"] =  urlHandlers.UHSessionModifSchedule.getURL(obj)
                    path[-1]["sessionContributionsURL"] =  urlHandlers.UHSessionModContribList.getURL(obj)
            else:
                break
        return path

class WListOfPapersToReview(WBannerModif):

    def __init__(self, target, user ):
        ## PATH
        # Iterate till conference is reached
        conf = target.getConference()
        if user == "referee":
            path = [{"url": urlHandlers.UHConfModifListContribToJudge.getURL(conf), "title":_("Contributions list")}]
        if user == "reviewer":
            path = [{"url": urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL(conf), "title":_("Contributions list")}]
        if user == "editor":
            path = [{"url": urlHandlers.UHConfModifListContribToJudgeAsEditor.getURL(conf), "title":_("Contributions list")}]
        # TITLE AND TYPE
        itemType = type(target).__name__
        title = target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)


class WNotifTplBannerModif(WBannerModif):

    def __init__( self, target ):
        path = [{"url": urlHandlers.UHAbstractReviewingNotifTpl.getURL(target), "title":_("Notification template list")}]
        itemType="Notification Template"
        title=target.getName()
        WBannerModif.__init__(self, path, itemType, title)

class WAbstractBannerModif(WBannerModif):

    def __init__( self, target ):
        path = [{"url": urlHandlers.UHConfAbstractManagment.getURL(target), "title":_("Abstracts list")}]
        itemType="Abstract"
        title=target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)

class WTrackBannerModif(WBannerModif):

    def __init__( self, track, abstract=None, isManager = False ):
        path = []
        target = track
        if abstract:
            path.append({"url": urlHandlers.UHTrackModifAbstracts.getURL(track), "title":_("Abstract list")})
        if isManager:
            path.append({"url": urlHandlers.UHConfModifProgram.getURL(track.getConference()), "title":_("Track list")})
        itemType=type(target).__name__
        title=target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)

class WCategoryBannerModif(WBannerModif):

    def __init__( self, target ):
        itemType="Category"
        title=target.getTitle()
        WBannerModif.__init__(self, [], itemType, title)

class WRegFormBannerModif(WBannerModif):

    def __init__( self, registrant ):
        path=[{"url": urlHandlers.UHConfModifRegistrantList.getURL(registrant.getConference()), "title":_("Registrants list")}]

        itemType="Registrant"
        title=registrant.getFullName()
        WBannerModif.__init__(self, path, itemType, title)

class WRegFormSectionBannerModif(WBannerModif):

    def __init__( self, target, conf ):
        path=[{"url": urlHandlers.UHConfModifRegForm.getURL(conf), "title":_("Registration form setup")}]

        itemType="Registration form Section"
        title=target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)

class WEpaymentBannerModif(WBannerModif):

    def __init__( self, target, conf ):
        path=[{"url": urlHandlers.UHConfModifEPayment.getURL(conf), "title":_("Epayment setup")}]

        itemType="Epayment plugin"
        title=target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)

class WParticipantsBannerModif(WBannerModif):

    def __init__( self, conf ):
        path=[{"url": urlHandlers.UHConfModifParticipants.getURL(conf), "title":_("Participants list")}]

        itemType="Pending participants"
        title=""
        WBannerModif.__init__(self, path, itemType, title)

class WCategModifHeader(WTemplated):

    def __init__(self, targetConf ):
        self._conf = targetConf

    def _getSingleCategHTML( self, categ, URLGen ):

        return """<a href="%s">%s</a>"""%(URLGen( categ ), categ.getName())

    def _getMultipleCategHTML( self, categList, URLGen ):
        l = []
        for categ in self._conf.getOwnerList():
            l.append("""<option value="%s">%s</option>"""%(categ.getId(),\
                                                          categ.getName()))
        return  i18nformat("""<form action="%s" method="GET">
                        <select name="categId">%s</select>
                        <input type="submit" class="btn" value="_("go")">
                    </form>""")%(URLGen(), "".join(l))

    def getVars( self ):

        vars = WTemplated.getVars( self )
        #raise "%s"%(type(self._conf))
        try:
            ol = self._conf.getOwnerList()
        except:
            ol=self._conf
        #raise "%s"%ol
        URLGen = vars.get("categDisplayURLGen", urlHandlers.UHCategoryDisplay.getURL )

        try:
            if len(ol)>1:
                vars["categ"] = self._getMultipleCategHTML(ol, URLGen)
            else:
                vars["categ"] = self._getSingleCategHTML( ol[0], URLGen)
            vars["viewImageURL"] = Configuration.Config.getInstance().getSystemIconURL( "view" )
        except:
            vars["categ"] = self._getSingleCategHTML( ol, URLGen)
            vars["viewImageURL"] = Configuration.Config.getInstance().getSystemIconURL( "view" )

        return vars


class WCategoryModificationHeader(WTemplated):


    def __init__( self, category ):
        self._categ = category

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["confTitle"] = self._categ.getName()
        vars["title"] = self._categ.getName()
        vars["catDisplayURL"] = urlHandlers.UHCategoryDisplay.getURL(self._categ)
        vars["catModifURL"]= urlHandlers.UHCategoryModification.getURL(self._categ)
        vars["titleTabPixels"] = self.getTitleTabPixels()
        #vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        vars["eventCaption"]= "Category"
        return vars

    def getIntermediateVTabPixels( self ):
        return 0

    def getTitleTabPixels( self ):
        return 260

class WConfModifHeader(WTemplated):

    def __init__( self, conf, aw ):
        self._conf = conf
        self._aw = aw

    def getVars( self ):
        vars = WTemplated.getVars( self )
        #raise "%s"%vars
        try:
            vars["creator"] = self._conf.getCreator().getFullName()
        except:
            vars["creator"] = ""
        vars["imgGestionGrey"] = Configuration.Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["confTitle"] = escape(self._conf.getTitle())
        if self._conf.canModify( self._aw ):
            URLGen = vars.get("confModifURLGen", \
                                urlHandlers.UHConferenceModification.getURL )
            vars["confTitle"] = """<a href=%s>%s</a>"""%(quoteattr( str( URLGen( self._conf ) ) ), escape(self._conf.getTitle()) )
        URLGen = vars.get( "confDisplayURLGen", urlHandlers.UHConferenceDisplay.getURL )
        vars["confDisplayURL"] = URLGen( self._conf )
        vars["titleTabPixels"] = WConferenceModifFrame(self._conf, self._aw).getTitleTabPixels()
        try:
            type = self._conf.getType()
        except:
            type = ""
        if type == "simple_event":
            type = "lecture"
        vars["eventCaption"]=type.capitalize()#"Event"


        return vars


class WSessionModifHeader(WTemplated):

    def __init__( self, session, aw ):
        self._session = session
        self._aw = aw

    def getHTML( self, params ):
        conf = self._session.getConference()
        confHTML = WConfModifHeader( conf, self._aw ).getHTML( params )
        return "%s%s"%(confHTML, WTemplated.getHTML( self, params ) )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["imgGestionGrey"] = Configuration.Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["sessionTitle"] = escape(self._session.getTitle())
        vars["sessionDisplayURL"] = vars["sessionDisplayURLGen"](self._session)
        vars["sessionModificationURL"] = vars["sessionModifURLGen"](self._session)
        return vars

class WBreakModifHeader(WTemplated):

    def __init__( self, breakSlot, aw ):
        self._break = breakSlot
        self._aw = aw

    def getHTML( self, params ):
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["imgGestionGrey"] = Configuration.Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["breakTitle"] = escape(self._break.getTitle())
        return vars


class WContribModifHeader(WTemplated):

    def __init__( self, contrib, aw):
        self._contrib = contrib
        self._aw = aw

    def getHTML( self, params ):
        conf = self._contrib.getConference()
        session = self._contrib.getSession()
        if session is not None:
            HTML = WSessionModifHeader( session, self._aw ).getHTML( params )
        else:
            HTML = WConfModifHeader( conf, self._aw ).getHTML( params )
        return "%s%s"%(HTML, WTemplated.getHTML( self, params ) )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["imgGestionGrey"] = Configuration.Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["title"] = escape(self._contrib.getTitle())
        urlGen = vars.get( "contribDisplayURLGen", urlHandlers.UHContributionDisplay.getURL )
        vars["contribDisplayURL"] = urlGen(self._contrib)
        urlGen = vars.get( "contribModifURLGen", urlHandlers.UHContributionModification.getURL )
        vars["contribModificationURL"] = urlGen(self._contrib)
        return vars


class WContribModifTool(WTemplated):
    pass


class WContributionDeletion(WTemplated):
    pass


class WContribModifSC(WTemplated):

    def __init__(self, contrib):
        self._contrib = contrib
        self._conf = self._contrib.getConference()

    def getSubContItems(self, SCModifURL):
        temp = []
        scList = self._contrib.getSubContributionList()
        for sc in scList:
            id = sc.getId()
            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (scList.index(sc), scList.index(sc))
            for i in range(1, len(scList) + 1):
                if i == scList.index(sc) + 1:
                    selbox += "<option selected value='%s'>%s" % (i - 1, i)
                else:
                    selbox += "<option value='%s'>%s" % (i - 1, i)
            selbox += """
                </select>"""
            temp.append("""
                <tr>
                    <td>
                        <input type="checkbox" name="selSubContribs" value="%s">
                        %s
                        &nbsp;<a href="%s">%s</a>
                    </td>
                </tr>""" % (id, selbox,SCModifURL(sc), escape(sc.getTitle())))
        html = """
                <input type="hidden" name="oldpos">
                <table align="center">%s
                </table>""" % "".join(temp)
        return html

    def getVars(self):
        vars = WTemplated.getVars(self)
        cfg = Configuration.Config.getInstance()
        vars["subContList"] = self.getSubContItems(vars["subContModifURL"])
        vars["confId"] = self._contrib.getConference().getId()
        vars["contribId"] = self._contrib.getId()
        vars["deleteItemsURL"] = vars["moveSubContribURL"]

        return vars
###ness##################################################################################
#     def __getSubCategoryItems( self, sl, modifURLGen ):
#        temp = []
#        for categ in sl:
#            id = categ.getId()
#            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (sl.index(categ),sl.index(categ))
#            for i in range (1,len(sl)+1):
#                if i==sl.index(categ)+1:
#                    selbox += "<option selected value='%s'>%s" % (i-1,i)
#                else:
#                    selbox += "<option value='%s'>%s" % (i-1,i)
#            selbox += """
#                </select>"""
#            temp.append("""
#                <tr>
#                    <td>
#                        <input type="checkbox" name="selectedCateg" value="%s">
#                        %s
#                        &nbsp;<a href="%s">%s</a>
#                    </td>
#                </tr>"""%(id, selbox,modifURLGen( categ ), categ.getName()))
#        html = """
#                <input type="hidden" name="oldpos">
#                <table align="center">%s
#                </table>"""%"".join( temp )
#        return html
##ness##############################################################################


class WMaterialModifHeader(WTemplated):

    def __init__( self, material, aw ):
        self._mat = material
        self._aw = aw

    def getHTML( self, params ):
        owner = self._mat.getOwner()
        if isinstance( owner, conference.Contribution ):
            HTML = WContribModifHeader( owner, self._aw ).getHTML( params )
        elif isinstance( owner, conference.SubContribution ):
            HTML = WSubContribModifHeader( owner, self._aw ).getHTML( params )
        elif isinstance( owner, conference.Session ):
            HTML = WSessionModifHeader( owner, self._aw ).getHTML( params )
        elif isinstance( owner, conference.Conference ):
            HTML = WConfModifHeader( owner, self._aw ).getHTML( params )
        elif isinstance( owner, conference.Category):
            HTML = WCategoryModificationHeader( owner ).getHTML( params )
        return "%s%s"%(HTML, WTemplated.getHTML( self, params ))

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["imgGestionGrey"] = Configuration.Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["title"] = escape(self._mat.getTitle())
        vars["materialDisplayURL"] = vars["materialDisplayURLGen"](self._mat)
        vars["materialModificationURL"] = vars["materialModifURLGen"](self._mat)
        vars["titleTabPixels"] = WMaterialModifFrame(self._mat, self._aw).getTitleTabPixels()
        return vars


class WConferenceModifFrame(WTemplated):

    def __init__( self, conference, aw,):
        self.__conf = conference
        self._aw = aw

    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["conf"] = self.__conf
        vars["startDate"] = utils.formatDateTime(self.__conf.getAdjustedStartDate(), format="d MMM")
        vars["endDate"] = utils.formatDateTime(self.__conf.getAdjustedEndDate(), format="d MMM")

        return vars

class WCategoryModifFrame(WTemplated):

    def __init__( self, conference):
        self.__conf = conference


    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        #p = {"categDisplayURLGen": vars["categDisplayURLGen"] }
        #vars["context"] = WCategModifHeader(self.__conf).getHTML(p)
        vars["creator"] = ""#self.__conf.getCreator().getFullName()
        vars["context"] = ""
        vars["imgGestionGrey"] = Configuration.Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["categDisplayURL"] = vars["categDisplayURLGen"]( self.__conf )
        vars["title"] = escape(self.__conf.getTitle())
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        return vars


    def getIntermediateVTabPixels( self ):
        return 0

    def getTitleTabPixels( self ):
        return 260

    def getCloseHeaderTags( self ):
        return ""

class WNotifTPLModifFrame(WTemplated):

    def __init__(self, notifTpl, aw):
        self._notifTpl = notifTpl
        self._aw = aw

    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        conf = self._notifTpl.getConference()
        vars["context"] = WConfModifHeader( conf, self._aw ).getHTML(vars)
        vars["title"] = self._notifTpl.getName()
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        vars["closeHeaderTags"] = self.getCloseHeaderTags()
        return vars

    def getOwnerComponent( self ):
        owner = self._notifTpl.getOwner()
        wc = WConferenceModifFrame(owner, self._aw)
        return wc

    def getIntermediateVTabPixels( self ):
        wc = self.getOwnerComponent()
        return 7 + wc.getIntermediateVTabPixels()

    def getTitleTabPixels( self ):
        wc = self.getOwnerComponent()
        return wc.getTitleTabPixels() - 7

    def getCloseHeaderTags( self ):
        wc = self.getOwnerComponent()
        return "</table></td></tr>" + wc.getCloseHeaderTags()


class WScheduleContributionModifFrame(WTemplated):

    def __init__( self, contribution, aw, days, handler=urlHandlers.UHContributionModification):
        self._contrib = contribution
        self._conf = self._contrib.getConference()
        self._aw = aw
        self._days = days
        self._handler = handler

    def getHTML( self, body, **params ):

        params["body"] = body

        dateList = [d.getDate() for d in self._days]

        # Keep contributions that happen in the selected day(s)

        # DEBUG

        for c in self._conf.getContributionList():
            assert(type(c.getStartDate()) == datetime),"Not all dates are present for the contributions!"

        ###

        l = []
        for contrib in self._conf.getContributionList():
            if contrib.getStartDate().date() in dateList:
                l.append(contrib)
        params["contribList"] = l
        params["handler"] = self._handler

        return WTemplated.getHTML( self, params )

class WContributionModifFrame(WTemplated):

    def __init__( self, contribution, aw):
        self._contrib = contribution
        self._aw = aw

    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["target"] = self._contrib
        return vars


class WMaterialModifFrame(WTemplated):

    def __init__( self, material, aw):
        self._material = material
        self._aw = aw

    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        closeHeaderTags = "</table></td></tr>"
        vars = WTemplated.getVars( self )
        vars["imgGestionGrey"] = Config.getInstance().getSystemIconURL( "gestionGrey" )
        owner = self._material.getOwner()
        if isinstance(owner, conference.Contribution):
            wc = WContribModifHeader( owner, self._aw )
        elif isinstance(owner, conference.Session):
            wc = WSessionModifHeader( owner, self._aw )
        elif isinstance(owner, conference.SubContribution):
            wc = WSubContribModifHeader( owner, self._aw )
        elif isinstance(owner, conference.Category) :
            wc = WCategoryModificationHeader(owner)
        else:
            wc = WConfModifHeader( owner, self._aw )
        vars["context"] = wc.getHTML( vars )
        vars["closeHeaderTags"] = self.getCloseHeaderTags()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["title"] = escape(self._material.getTitle())
        vars["materialDisplayURL"] = vars["materialDisplayURLGen"]( self._material )
        return vars

    def getOwnerComponent( self ):
        owner = self._material.getOwner()
        if isinstance(owner, conference.Contribution):
            wc = WContributionModifFrame(owner, self._aw)
        elif isinstance(owner, conference.Session):
            wc = WSessionModifFrame(owner, self._aw)
        elif isinstance(owner, conference.SubContribution):
            wc = WSubContributionModifFrame(owner, self._aw)

        else:
            wc = WConferenceModifFrame(owner, self._aw)
        return wc

    def getIntermediateVTabPixels( self ):
        wc = self.getOwnerComponent()
        return 7 + wc.getIntermediateVTabPixels()

    def getTitleTabPixels( self ):
        wc = self.getOwnerComponent()
        return wc.getTitleTabPixels() - 7

    def getCloseHeaderTags( self ):
        wc = self.getOwnerComponent()
        return "</table></td></tr>" + wc.getCloseHeaderTags()


class WResourceModifFrame(WTemplated):

    def __init__( self, resource, aw):
        self._resource = resource
        self._aw = aw

    def getHTML( self, body, **params ):
        params["body"] = body
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        wc = WMaterialModifHeader( self._resource.getOwner(), self._aw )
        vars["context"] = wc.getHTML( vars )
        vars["name"] = self._resource.getName()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["closeHeaderTags"] = self.getCloseHeaderTags()
        return vars

    def getOwnerComponent( self ):
        owner = self._resource.getOwner()
        wc = WMaterialModifFrame(owner, self._aw)
        return wc

    def getIntermediateVTabPixels( self ):
        wc = self.getOwnerComponent()
        return 7 + wc.getIntermediateVTabPixels()

    def getTitleTabPixels( self ):
        wc = self.getOwnerComponent()
        return wc.getTitleTabPixels() - 7

    def getCloseHeaderTags( self ):
        wc = self.getOwnerComponent()
        return "</table></td></tr>" + wc.getCloseHeaderTags()


class WFileModifFrame( WResourceModifFrame ):
    pass


class WLinkModifFrame( WResourceModifFrame ):
    pass



class ModifFrameFactory:

    def getFrameClass( cls, target ):
        if isinstance(target, conference.Conference):
            return WConferenceModifFrame
        if isinstance( target, conference.Session ):
            return WSessionModifFrame
        if isinstance( target, conference.Contribution ):
            return WContributionModifFrame
        if isinstance( target, conference.SubContribution ):
            return WSubContributionModifFrame
        if isinstance(target, conference.Material):
            return WMaterialModifFrame
        if isinstance(target, conference.LocalFile):
            return WFileModifFrame
        if isinstance( target, conference.Link ):
            return WLinkModifFrame
        return None
    getFrameClass = classmethod( getFrameClass )

    def getModifFrame( target ):
        f = ModifFrameFactory.getFrameClass( target )
        if f:
            return f( target )
        return None
    getModifFrame = staticmethod( getModifFrame )


class WSubContributionDisplay:

    def __init__(self, aw, subContrib):
        self._aw = aw
        self._subContrib = subContrib

    def getHTML( self, params ):
        if self._subContrib.canAccess( self._aw ):
            c = WSubContributionDisplayFull( self._aw, self._subContrib)
            return c.getHTML( params )
        if self._subContrib.canView( self._aw ):
            c = WSubContributionDisplayMin( self._aw, self._subContrib)
            return c.getHTML( params )
        return ""

class WSubContributionDisplayBase(WTemplated):

    def __init__(self, aw, subContrib):
        self._aw = aw
        self._subContrib = subContrib

    def __getHTMLRow( self, title, body):
        if body.strip() == "":
            return ""
        str = """
                <tr>
                    <td valign="top" align="right">
                        <font size="-1" color="#000060">%s:</font>
                    </td>
                    <td width="100%%">%s</td>
                </tr>"""%(title, body)
        return str

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["title"] = self._subContrib.getTitle()
        vars["description"] = self._subContrib.getDescription()
        vars["modifyItem"] = ""
        if self._subContrib.canModify( self._aw ):
            vars["modifyItem"] = """<a href="%s"><img src="%s" alt="Jump to the modification interface"></a> """%(vars["modifyURL"], Configuration.Config.getInstance().getSystemIconURL( "modify" ) )
        l=[]
        for speaker in self._subContrib.getSpeakerList():
            l.append( """<a href="mailto:%s">%s</a>"""%(speaker.getEmail(), \
                                                        speaker.getFullName()))
        l.append(self._subContrib.getSpeakerText())
        vars["speakers"] = self.__getHTMLRow(  _("Presenters"), "<br>".join( l ) )
        lm = []
        for material in self._subContrib.getAllMaterialList():
            lm.append( WMaterialDisplayItem().getHTML( self._aw, material, \
                                            vars["materialURLGen"]( material) ))
        vars["material"] = self.__getHTMLRow( "Material", "<br>".join( lm ) )
        vars["duration"] = (datetime(1900,1,1)+self._subContrib.getDuration()).strftime("%M'")
        if int(self._subContrib.getDuration().seconds/3600)>0:
            vars["duration"] = (datetime(1900,1,1)+self._subContrib.getDuration()).strftime("%Hh%M'")
        return vars


class WSubContributionDisplayFull(WSubContributionDisplayBase):
    pass


class WSubContributionDisplayMin(WSubContributionDisplayBase):
    pass


class WMaterialDisplayItem(WTemplated):

    def getHTML( self, aw, material, URL="", icon=Configuration.Config.getInstance().getSystemIconURL( "material" ) ):
        if material.canView( aw ):

            return """<a href=%s>%s</a>"""%(quoteattr( str( URL ) ), WTemplated.htmlText( material.getTitle() ) )
        return ""

class WMaterialTable( WTemplated ):
    # Deprecated - used in old file management scheme

    def __init__(self, matOwner, registry = None ):
        self._owner = matOwner
        self._fr = registry

    def _getAdditionalMaterialItems( self ):
        l = []
        for mat in self._owner.getMaterialList():
            l.append("""
                <tr>
                    <td>
                        <table cellpadding="1" cellspacing="1">
                            <tr>
                                <td align="left">
                                    <input type="checkbox" name="deleteMaterial" value="%s">
                                </td>
                                <td align="left">
                                    <img src="%s" style="vertical-align:middle" alt="">
                                </td>
                                <td align="left">&nbsp;</td>
                                <td align="left" width="100%%">
                                    <a href="%s">%s</a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                     """%(mat.getId(), Config.getInstance().getSystemIconURL("material"), self._modifyURLGen( mat ), mat.getTitle() ) )
        return "".join(l)

    def _getSpecialMaterialItems( self ):
        if not self._fr:
            return ""
        l = []
        for factory in self._fr.getList():
            if factory.canDelete( self._owner ):
                icon = ""
                if factory.getIconURL():
                    icon = """<img src="%s" style="vertical-align:middle" alt="">"""%factory.getIconURL()
                mat = factory.get( self._owner )
                l.append("""    <tr>
                                    <td valing="bottom">
                                        <table cellpadding="1" cellspacing="1">
                                            <tr>
                                                <td align="left">
                                                    <input type="checkbox" name="deleteMaterial" value="%s">
                                                </td>
                                                <td align="left">
                                                    %s
                                                </td>
                                                <td align="left">&nbsp;</td>
                                                <td align="left" width="100%%">
                                                    <a href="%s">%s</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                         """%(factory.getId(), icon, factory.getModificationURL( mat ), mat.getTitle()))
        return "".join(l)

    def getHTML( self, addURL, removeURL, modifyURLGen ):
        self._modifyURLGen = modifyURLGen
        params={"addURL": addURL, "deleteURL": removeURL}

        hiddenParams = self._owner.getLocator().getWebForm()

        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["items"] = "%s%s"%(self._getSpecialMaterialItems(), \
                                self._getAdditionalMaterialItems())
        vars["locator"] = self._owner.getLocator().getWebForm()
        l = []
        if self._fr:
            for factory in self._fr.getList():
                if factory.canAdd( self._owner ):
                    l.append("""<option value="%s">%s</option>"""%(\
                                          factory.getId(), factory.getTitle()))
        vars["matTypesSelectItems"] = "".join(l)
        return vars

class WAccessControlFrameBase(WTemplated):

    def _getAccessControlFrametParams( self ):
        vars = {}
        if self._target.getAccessProtectionLevel() == -1:
            vars["privacy"] = "PUBLIC"
            vars["statusColor"] = "#128F33"
        elif self._target.isItselfProtected():
            vars["privacy"] = "RESTRICTED"
            vars["statusColor"] = "#B02B2C"
        else :
            vars["privacy"] = "INHERITING"
            vars["statusColor"] = "#444444"

        if isinstance(self._target, Category) and self._target.isRoot():
            vars["parentName"] = vars["parentPrivacy"] = vars["parentStatusColor"] = ''
        else:
            if isinstance(self._target, Conference):
                vars["parentName"] = self._target.getOwner().getName()
            else:
                vars["parentName"] = self._target.getOwner().getTitle()
            if self._target.hasProtectedOwner():
                    vars["parentPrivacy"] = "RESTRICTED"
                    vars["parentStatusColor"] = "#B02B2C"
            else :
                    vars["parentPrivacy"] = "PUBLIC"
                    vars["parentStatusColor"] = "#128F33"

        vars["locator"] = self._target.getLocator().getWebForm()
        return vars

class WAccessControlFrame(WAccessControlFrameBase):

    def getHTML( self, target, setVisibilityURL, type ):
        self._target = target

        params = { "setPrivacyURL": setVisibilityURL,\
                   "target": target,\
                   "type": type }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars.update(self._getAccessControlFrametParams())
        return vars


class WConfAccessControlFrame(WAccessControlFrameBase):

    def getHTML( self, target, setVisibilityURL):
        self._target = target
        params = { "target": target,\
                   "setPrivacyURL": setVisibilityURL,\
                   "type": "Event" }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["accessKey"] = self._target.getAccessKey()
        vars.update(self._getAccessControlFrametParams())
        return vars

class WModificationControlFrame(WTemplated):

    def getHTML( self, target ):
        self.__target = target
        return  WTemplated.getHTML( self )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self.__target.getLocator().getWebForm()
        return vars


class WConfModificationControlFrame(WTemplated):

    def _getManagersList(self):
        result = fossilize(self.__target.getManagerList())
        # get pending users
        for email in self.__target.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def getHTML(self, target):
        self.__target = target
        params = { "target": target }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self.__target.getLocator().getWebForm()
        vars["confId"] = self.__target.getId()
        vars["modifKey"] = self.__target.getModifKey()
        vars["managers"] = self._getManagersList()
        return vars

class WConfRegistrarsControlFrame(WTemplated):

    def getHTML(self, target):
        self.__target = target
        params = {}
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["confId"] = self.__target.getId()
        vars["registrars"] = fossilize(self.__target.getRegistrarList())
        return vars


class WConfProtectionToolsFrame(WTemplated):

    def __init__( self, target ):
        self._target = target

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["grantSubmissionToAllSpeakersURL"] = str(urlHandlers.UHConfGrantSubmissionToAllSpeakers.getURL(self._target))
        vars["removeAllSubmissionRightsURL"] = str(urlHandlers.UHConfRemoveAllSubmissionRights.getURL(self._target))
        vars["grantModificationToAllConvenersURL"] = str(urlHandlers.UHConfGrantModificationToAllConveners.getURL(self._target))
        return vars

class WDomainControlFrame(WTemplated):

    def __init__(self, target):
        self._target = target

    def getVars(self):
        tpl_vars = WTemplated.getVars(self)

        if isinstance(self._target, conference.Conference):
            tpl_vars['method'] = 'event.protection.toggleDomains'
            event = self._target
        elif isinstance(self._target, conference.Contribution):
            tpl_vars['method'] = 'contribution.protection.toggleDomains'
            event = self._target.getConference()
        elif isinstance(self._target, conference.Session):
            tpl_vars['method'] = 'session.protection.toggleDomains'
            event = self._target.getConference()
        else:
            tpl_vars['method'] = 'category.protection.toggleDomains'
            event = None

        ac = self._target.getAccessController()
        inheriting = ac.getAccessProtectionLevel() == 0
        domain_list = ac.getAnyDomainProtection() if inheriting else self._target.getDomainList()

        tpl_vars["inheriting"] = inheriting
        tpl_vars["domains"] = dict((dom, dom in domain_list)
                                   for dom in domain.DomainHolder().getList())
        tpl_vars["locator"] = self._target.getLocator().getWebForm()
        tpl_vars["target"] = self._target
        tpl_vars["event"] = event

        return tpl_vars


class WInlineContextHelp(WTemplated):

    def __init__(self, content):
        self._content = content

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["helpContent"] = self._content
        vars["imgSrc"] = Config.getInstance().getSystemIconURL( "help" )
        return vars

class WResourceModification(WTemplated):

    def __init__( self, resource ):
        self._resource = resource
        self._conf = resource.getConference()
        self._session = resource.getSession()
        self._contrib = resource.getContribution()
        self._material = resource.getOwner()

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["confTitle"] = self._conf.getTitle()
        vars["sessionTitle"] = ""
        if self._session != None:
            vars["sessionTitle"] = self._session.getTitle()
        vars["contributionTitle"] = ""
        if self._contrib != None:
            vars["contributionTitle"] = self._contrib.getTitle()
        vars["materialTitle"] = self._material.getTitle()
        vars["title"] = self._resource.getName()
        vars["description"] = self._resource.getDescription()
        vars["accessControlFrame"] = WAccessControlFrame().getHTML(\
                                                    self._resource,\
                                                    vars["setVisibilityURL"],\
                                                    vars["addAllowedURL"],\
                                                    vars["removeAllowedURL"],\
                                                    vars["setAccessKeyURL"], \
                                                    vars["setModifKeyURL"] )
        return vars


class WResourceDataModification(WResourceModification):

    def getHTML(self, params):
        str = """
            <form action="%s" method="POST" enctype="multipart/form-data">
                %s
                %s
            </form>
              """%(params["postURL"],\
                   self._resource.getLocator().getWebForm(),\
                   WTemplated.getHTML( self, params ) )
        return str

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["title"] = self._resource.getName()
        vars["description"] = self._resource.getDescription()
        return vars


class WUserRegistration(WTemplated):

    def __init__( self, av = None ):
        self._avatar = av

    def __defineNewUserVars( self, vars={} ):
        vars["Wtitle"] = _("Creating a new Indico user")
        vars["name"] = quoteattr( vars.get("name","") )
        vars["surName"] = quoteattr( vars.get("surName","") )
        vars["organisation"] = quoteattr( vars.get("organisation","") )
        vars["address"] = vars.get("address","")
        vars["email"] = quoteattr( vars.get("email","") )
        vars["telephone"] = quoteattr( vars.get("telephone","") )
        vars["fax"] = quoteattr( vars.get("fax","") )
        vars["login"] = quoteattr( vars.get("login","") )
        return vars

    def __defineExistingUserVars( self, vars={} ):
        u = self._avatar
        vars["Wtitle"] = _("Modifying an Indico user")
        vars["name"] = quoteattr( u.getName() )
        vars["surName"] =  quoteattr( u.getSurName() )
        vars["title"] = quoteattr( u.getTitle() )
        vars["organisation"] = quoteattr( u.getOrganisations()[0] )
        vars["address"] = u.getAddresses()[0]
        vars["email"] = quoteattr( u.getEmails()[0] )
        vars["telephone"] = quoteattr( u.getTelephones()[0] )
        vars["fax"] =  quoteattr( u.getFaxes()[0] )
        return vars

    def getVars( self ):
        vars = WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["after"] =  _("After the submission of your personal data, an email will be sent to you")+".<br>"+ _("You will able to use your account only after you activate it by clicking on the link inside the email.")
        if minfo.getModerateAccountCreation():
            vars["after"] =  _("The site manager has to accept your account creation request. You will be informed of the decision by email.")+"<br>"
        vars["postURL"] = quoteattr( str( vars["postURL"] ) )
        if not self._avatar:
            vars = self.__defineNewUserVars( vars )
            vars["locator"] = ""
        else:
            vars = self.__defineExistingUserVars( vars )
            vars["locator"] = self._avatar.getLocator().getWebForm()

        #note: there's a reason this line is TitlesRegistry() and not just TitlesRegistry
        #methods in TitlesRegistry cannot be classmethods because _items cannot be a class
        #attribute because the i18n '_' function doesn't work for class attributes
        vars["titleOptions"]=TitlesRegistry().getSelectItemsHTML(vars.get("title",""))
        tz = minfo.getTimezone()
        if vars.get("defaultTZ","") != "":
            tz = vars.get("defaultTZ")
        tzmode = "Event Timezone"
        if vars.get("displayTZMode","") != "":
            tzmode = vars.get("displayTZMode")
        vars["timezoneOptions"]=TimezoneRegistry.getShortSelectItemsHTML(tz)
        vars["displayTZModeOptions"]=DisplayTimezoneRegistry.getSelectItemsHTML(tzmode)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if vars.get("defaultLang","") == "":
            vars["defaultLang"] = minfo.getLang()
        return vars


class WUserCreated(WTemplated):

    def __init__( self, av = None ):
        self._avatar = av

    def getVars( self ):
        vars = WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["however"] =  _("However, you will not be able to log into the system until you have activated your new account. To do this please follow the instructions in the mail that we have already sent you")+".<br>"
        if minfo.getModerateAccountCreation():
            vars["however"] =  _("However, you will not be able to log into the system until the site administrator has accepted your account creation request. You will be notified of the decision by email")+".<br>"
        vars["signInURL"] = quoteattr( str( vars["signInURL"] ) )
        vars["supportAddr"] = Config.getInstance().getSupportEmail()
        return vars


class WUserSendIdentity(WTemplated):

    def __init__( self, av = None ):
        self._avatar = av

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self._avatar.getLocator().getWebForm()
        vars["name"] = self._avatar.getName()
        vars["surName"] = self._avatar.getSurName()
        vars["email"] = self._avatar.getEmail()
        vars["org"] = self._avatar.getOrganisation()
        vars["title"] = self._avatar.getTitle()
        vars["address"] = self._avatar.getAddresses()[0]
        vars["contactEmail"]  = Config.getInstance().getSupportEmail()
        return vars

class WSignIn(WTemplated):

    def getVars( self ):
        vars = WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        authManager = AuthenticatorMgr()
        vars["postURL"] = quoteattr( str( vars.get( "postURL", "" ) ) )
        vars["returnURL"] = quoteattr( str( vars.get( "returnURL", "" ) ) )
        vars["forgotPasswordURL"] = quoteattr( str( vars.get( "forgotPassordURL", "" ) ) )
        vars["login"] = quoteattr( vars.get( "login", "" ) )
        vars["msg"] = self.htmlText( vars.get( "msg" ) )
        vars["ssoURL"] = urlHandlers.UHSignInSSO.getURL()
        imgIcon=Configuration.Config.getInstance().getSystemIconURL("currentMenuItem")
        if Configuration.Config.getInstance().getAuthenticatedEnforceSecure():
            imgIcon=imgIcon.replace("http://", "https://")
            imgIcon = urlHandlers.setSSLPort( imgIcon )
        vars["itemIcon"] = imgIcon
        vars["isAuthorisedAccountCreation"] = minfo.getAuthorisedAccountCreation()
        vars["hasExternalAuthentication"] = authManager.hasExternalAuthenticators()
        vars["externalAuthenticators"]= [auth for auth in authManager.getAuthenticatorIdList() if auth != 'Local']
        vars["isSSOLoginActive"] = authManager.isSSOLoginActive()
        vars["authenticators"] = authManager.getList()
        return vars


class WResetPassword(WTemplated):
    pass


class WConfirmation(WTemplated):

    def getHTML(self, message, postURL, passingArgs, loading=False, severity="warning", **opts):
        params = {}
        params["message"] = message
        params["postURL"] = postURL

        params["severity"] = severity
        params["passingArgs"] = passingArgs
        params["loading"] = loading
        params["confirmButtonCaption"] = opts.get("confirmButtonCaption", _("Yes"))
        params["cancelButtonCaption"] = opts.get("cancelButtonCaption", _("Cancel"))
        params["systemIconWarning"] = Configuration.Config.getInstance().getSystemIconURL("warning")
        return WTemplated.getHTML(self, params)


class WDisplayConfirmation(WTemplated):

    def getHTML(self, message, postURL, passingArgs, **opts):
        params = {}
        params["message"] = message
        params["postURL"] = postURL
        pa = []

        for arg in passingArgs.keys():
            if not type(passingArgs[arg]) == types.ListType:
                passingArgs[arg] = [passingArgs[arg]]

            for value in passingArgs[arg]:
                pa.append("""<input type="hidden" name="%s" value="%s">""" % (arg, value))

        params["passingArgs"] = "".join(pa)
        params["confirmButtonCaption"] = opts.get("confirmButtonCaption", _("OK"))
        params["cancelButtonCaption"] = opts.get("cancelButtonCaption", _("Cancel"))
        params["systemIconWarning"] = Configuration.Config.getInstance().getSystemIconURL("warning")
        return WTemplated.getHTML(self, params)

class WClosed(WTemplated):
    pass


class SideMenu(object):
    def __init__(self, userStatus=False):
        """ Constructor
            userStatus: a boolean that is True if the user is logged in, False otherwise
        """
        self._sections = []
        self._userStatus = userStatus

    def addSection(self, section, top=False):
        if top:
            self._sections.insert(0, section)
        else:
            self._sections.append(section)

    def getSections(self):
        return self._sections


class ManagementSideMenu(SideMenu):

    def getHTML(self):
        return WSideMenu(self, self._userStatus, type="management").getHTML()


class BasicSideMenu(SideMenu):

    def getHTML(self):
        return WSideMenu(self, self._userStatus, type="basic").getHTML()


class SideMenuSection:
    """ class coment
    """

    def __init__(self, title=None, active=False, currentPage = None, visible=True):
        """ -title is the words that will be displayed int he side menu.
            -active is True if ...
            -currentPage stores information about in which page we are seeing the Side Menu. For example,
            its values can be "category" or "admin".
        """
        self._title = title
        self._active = active
        self._currentPage = currentPage
        self._items = []
        self._visible = visible

    def getTitle(self):
        return self._title

    def getItems(self):
        return self._items

    def addItem(self, item):
        self._items.append(item)
        item.setSection(self)

    def isActive(self):
        return self._active

    def setActive(self, val):
        self._active = val

    def checkActive(self):

        self._active = False

        for item in self._items:
            if item.isActive():
                self._active = True
                break

    def getCurrentPage(self):
        return self._currentPage

    def setCurrentPage(self, currentPage):
        self._currentPage = currentPage

    def isVisible(self):
        return self._visible

    def setVisible(self, visible):
        self._visible = visible

    def hasVisibleItems(self):
        for item in self._items:
            if item.isVisible():
                return True
        return False

class SideMenuItem:

    def __init__(self, title, url, active=False, enabled=True, errorMessage = "msgNoPermissions", visible=True):
        """ errorMessage: one of the error messages in SideMenu.wohl
        """
        self._title = title
        self._url = url
        self._active = active
        self._enabled = enabled
        self._errorMessage = errorMessage
        self._visible = visible

    def getTitle(self):
        return self._title;

    def setSection(self, section):
        self._section = section

    def getURL(self):
        return self._url

    def setURL(self, url):
        self._url = url

    def isActive(self):
        return self._active

    def isEnabled(self):
        return self._enabled

    def getErrorMessage(self):
        return self._errorMessage

    def setActive(self, val=True):
        self._active = val
        self._section.checkActive()

    def setEnabled(self, val):
        self._enabled = val

    def setErrorMessage(self, val):
        self._errorMessage = val

    def isVisible(self):
        return self._visible

    def setVisible(self, visible):
        self._visible = visible

class WSideMenu(WTemplated):

    def __init__(self, menu, loggedIn, type="basic"):
        """
            type can be: basic (display interface) or management (management interface).
        """
        self._menu = menu
        self._type = type

        # is the user logged in? used for changing some tooltips
        self._loggedIn = loggedIn

    def getVars(self):
        vars = WTemplated.getVars(self)

        vars['menu'] = self._menu
        vars['loggedIn'] = self._loggedIn
        vars['sideMenuType'] = self._type
        return vars

class WebToolBar(object):

    def __init__( self, caption="" ):
        self.caption = caption
        self.items = []
        self.currentItem = None

    def getCaption( self ):
        return self.caption

    def addItem( self, newItem ):
        if newItem not in self.items:
            self.items.append( newItem )
            newItem.setOwner( self )

    def removeItem( self, item ):
        if item in self.items:
            if self.isCurrent( item ):
                self.setCurrentItem( None )
            self.items.remove( item )

    def getItemList( self ):
        return self.items

    def isCurrent( self, item ):
        return self.currentItem == item

    def setCurrentItem( self, item ):
        self.currentItem = item

    def isFirstItem( self, item):
        return self.items[0] == item

    def isLastItem( self, item ):
        return self.items[len(self.items)-1] == item

    def getHTML( self ):
        return WTBDrawer(self).getHTML()


class WTBItem:

    def __init__( self, caption, **args):
        self.owner = None
        self.caption = caption
        self.icon = args.get("icon", "")
        self.actionURL = args.get("actionURL", "")
        self.enabled = args.get("enabled", 1)
        self.subItems = []
        self.id = args.get("id", "")
        self.elementId = args.get("elementId", "")
        self.className = args.get("className", "")

    def getCaption(self):
        return self.caption

    def getIcon( self ):
        return self.icon

    def getActionURL( self ):
        return self.actionURL

    def setActionURL( self, URL ):
        self.actionURL = URL
        #self.actionURL = URL.strip()

    def setCurrent( self ):
        self.owner.setCurrentItem( self )

    def isCurrent( self ):
        return self.owner.isCurrent( self )

    def enable( self ):
        self.enabled = 1

    def disable( self ):
        self.enabled = 0

    def isEnabled( self ):
        return self.enabled

    def hasIcon( self ):
        return self.icon != ""

    def addItem( self, newItem ):
        if newItem not in self.subItems:
            self.subItems.append( newItem )
            newItem.setOwner( self.owner )

    def removeItem( self, item ):
        if item in self.subItems:
            self.subItems.remove( item )

    def getItemList( self ):
        return self.subItems

    def isFirstItem( self, item):
        return self.subItems[0] == item

    def isLastItem( self, item ):
        i = len(self.subItems)-1
        while not self.subItems[i].isEnabled():
            i -= 1
        return self.subItems[i] == item

    def setOwner( self, owner ):
        self.owner = owner
        for item in self.getItemList():
            item.setOwner( self.owner )

    def getId(self):
        return self.id

    def getElementId(self):
        return self.elementId

    def getClassName(self):
        return self.className


class WTBSeparator(WTBItem):

    def __init__( self ):
        WTBItem.__init__(self, "")

    def setCurrent( self ):
        return

class WTBGroup( WTBItem ):

    def __init__( self, caption, **args ):
        WTBItem.__init__( self, caption, **args )
        self.items= []

    def addItem( self, newItem ):
        if newItem not in self.items:
            self.items.append( newItem )
            newItem.setOwner( self.owner )

    def removeItem( self, item ):
        if item in self.items:
            self.items.remove( item )

    def getItemList( self ):
        return self.items

    def isFirstItem( self, item):
        return self.items[0] == item

    def isLastItem( self, item ):
        i = len(self.items)-1
        while not self.items[i].isEnabled():
            i -= 1
        return self.items[i] == item

    def setOwner( self, owner ):
        self.owner = owner
        for item in self.getItemList():
            item.setOwner( self.owner )

class WTBSection( WTBItem ):

    def __init__( self, caption, **args ):
        WTBItem.__init__( self, caption, **args )
        self.items= []
        self.drawer = None

    def addItem( self, newItem ):
        if newItem not in self.items:
            self.items.append( newItem )
            newItem.setOwner( self.owner )

    def removeItem( self, item ):
        if item in self.items:
            self.items.remove( item )

    def getItemList( self ):
        return self.items

    def isFirstItem( self, item):
        return self.items[0] == item

    def isLastItem( self, item ):
        i = len(self.items)-1
        while not self.items[i].isEnabled():
            i -= 1
        return self.items[i] == item

    def setOwner( self, owner ):
        self.owner = owner
        for item in self.getItemList():
            item.setOwner( self.owner )

    def setDrawer( self, d ):
        self.drawer = d(self)

    def getDrawer( self ):
        return self.drawer

    def hasDrawer( self ):
        return self.drawer != None

class WTBDrawer:
    def __init__( self, toolbar ):
        self.toolbar = toolbar

    def getHTML( self ):
        l = []
        for item in self.toolbar.getItemList():
            if not item.isEnabled():
                continue
            if isinstance(item, WTBSection) and item.hasDrawer():
                drawer = item.getDrawer()
            elif isinstance(item, WTBSection) and not item.hasDrawer():
                drawer = WStdSectionDrawer(item)
            else:
                drawer = WStdTBDrawer(item)
            l.append(drawer.getHTML())
        return "".join(l)

class WStdTBDrawer(WTemplated):

    def __init__( self, item ):
        self.item = item

    def _getTBItemCaption( self, item):
        return """<tr>
      <td colspan="2" class="menutitle">%s</td>
    </tr>"""%item.getCaption()

    def _getTBItemHTML( self, item ):
        str = """%s"""%(item.getCaption() )
        if item.getActionURL() != "":
            str = """<a href="%s">%s</a>"""%(item.getActionURL(), \
                                            item.getCaption())
        return str

    def _getCurrentIconHTML( self, style ):
        return """<td class="%s">&nbsp;<img src="%s"\
         style="vertical-align:middle" alt=""></td>"""%(style,\
                         Configuration.Config.getInstance().getSystemIconURL("arrowLeft"))

    def _getIconHTML( self, item, style ):
        return """<td class="%s">&nbsp;<img src="%s" alt="" hspace="3" vspace="2">
                </td>"""%(style, item.getIcon())

    def _getSectionItemsHTML( self, group ):
        lg = []
        for gItem in section.getItemList():
            if not gItem.isEnabled():
                continue
            style = self._getStyleForItem(gItem, section)
            lg.append("""<tr>
                          <td><table cellspacing="0" cellpadding="0" width="100%%">
                          <tr>%s<td class="%s" width="100%%">%s</td>
                          </tr></table></td>
                        </tr>"""%(self._getCurrentIconForItem(gItem, style),\
                                style,\
                                self._getTBItemHTML(gItem)))
        return """<table cellspacing="0" cellpadding="0" width="100%%">
                    %s
                  </table>"""%("".join(lg))

    def _getCurrentIconForItem( self, item, style ):
        if item.isCurrent():
            return self._getCurrentIconHTML(style)
        elif item.hasIcon():
            return self._getIconHTML(item, style)
        return ""

    def _getStyleForItem( self, item, list ):
        if item.isCurrent():
            return "menuselectedcell"
        elif list.isFirstItem(item):
            return "menutopcell"
        elif item.getItemList():
            return "menumiddlecell"
        elif list.isLastItem(item):
            return "menubottomcell"
        else:
            return "menumiddlecell"
        return ""

    def getVars( self ):
        vars = WTemplated.getVars( self )
        l = []

        if self.item != None:
            for tbItem in self.item.getItemList():
                if not tbItem.isEnabled():
                    continue
                groupItemsHTML = ""
                itemHTML = ""
                if tbItem.__class__ == WTBSeparator:
                    itemHTML = ""
                elif tbItem.__class__ == WTBSection:
                    sectionItemsHTML = self._getSectionItemsHTML( tbItem )
                    l.append(self._getTBItemCaption())
                    l.append("""<tr><td colspan="2">%s</td>
                                    </tr>"""%(sectionItemsHTML) )
                else:
                    itemHTML = self._getTBItemHTML( tbItem )
                    style = self._getStyleForItem(tbItem, self.item)
                    l.append( """<tr><td colspan="2">
                        <table cellspacing="0" cellpadding="0" width="100%%">
                        <tr>%s<td class="%s" width="100%%">%s</td></tr></table>
                        </td></tr>"""%(self._getCurrentIconForItem(tbItem,style),\
                        style, itemHTML))
        vars["items"] = "".join(l)
        return vars


class WStdSectionDrawer(WStdTBDrawer):

    def __init__( self, item ):
        self.section = item

    def getVars( self ):
        vars = WTemplated.getVars( self )
        l = []
        l.append(self._getTBItemCaption(self.section))
        if self.section != None:
            for tbItem in self.section.getItemList():
                if not tbItem.isEnabled():
                    continue
                itemHTML = ""
                if tbItem.__class__ == WTBSeparator:
                    itemHTML = ""
                else:
                    itemHTML = self._getTBItemHTML( tbItem )
                    style = self._getStyleForItem(tbItem, self.section)
                    l.append( """<tr><td colspan="2">
                        <table cellspacing="0" cellpadding="0" width="100%%">
                        <tr>%s<td class="%s" width="100%%">%s</td></tr></table>
                        </td></tr>"""%(self._getCurrentIconForItem(tbItem,style),\
                        style, itemHTML))
                    for subitem in tbItem.getItemList():
                        if not subitem.isEnabled():
                            continue
                        styleSubitem = self._getStyleForItem(subitem, self.section)
                        if subitem.isCurrent():
                            subitemHTML = self._getTBItemHTML( subitem )
                            l.append("""<tr><td colspan="2">
                                    <table cellspacing="0" cellpadding="0" width="100%%">
                                    <tr><td class="%s">&nbsp;&nbsp;&nbsp;&nbsp;</td>%s<td class="%s" width="100%%">\
                                    <span style="font-size:11px">%s</span></td></tr></table></td></tr>"""%(styleSubitem,\
                                    self._getCurrentIconForItem(subitem,styleSubitem),styleSubitem, subitemHTML))
                        else:
                            styleSubitem = "menuConfMiddleCell"
                            if self.section.isLastItem(tbItem) and tbItem.isLastItem(subitem):
                                styleSubitem = "menuConfBottomCell"
                            l.append( """<tr><td class="%s" nowrap>&nbsp;&nbsp;&nbsp;<a class="confSubSection" href="%s">\
                                    <img src="%s" alt="">&nbsp;%s</a></td></tr>\
                                    """%(styleSubitem, subitem.getActionURL(), subitem.getIcon(), subitem.getCaption()))
        vars["items"] = "".join(l)
        return vars


class WAddEventSectionDrawer(WStdSectionDrawer):

    def __init__( self, item ):
        self.section = item

    def _getTBItemHTML( self, item ):
        str = """<span class="menuadd">%s</span>"""%(item.getCaption() )
        if item.getActionURL() != "":
            str = """<a class="menuaddlink" href="%s">%s
                    </a>"""%(item.getActionURL(), \
                                            item.getCaption())
        return str

    def _getCurrentIconForItem( self, item, style ):
        if item.hasIcon():
            return self._getIconHTML(item, style)
        return ""

    def _getStyleForItem( self):
        return "menuadd"

    def getVars( self ):
        vars = WTemplated.getVars( self )
        l = []
        l.append(self._getTBItemCaption(self.section))
        if self.section != None:
            for tbItem in self.section.getItemList():
                if not tbItem.isEnabled():
                    continue
                itemHTML = ""
                if tbItem.__class__ == WTBSeparator:
                    itemHTML = ""
                else:
                    itemHTML = self._getTBItemHTML( tbItem )
                    style = self._getStyleForItem()
                    l.append( """<tr><td class="%s" colspan="2">
                        <table cellspacing="0" cellpadding="0" width="100%%">
                        <tr>%s<td class="%s" width="100%%">%s</td></tr></table>
                        </td></tr>"""%(WStdSectionDrawer._getStyleForItem(self,tbItem, self.section),self._getCurrentIconForItem(tbItem,style), style, itemHTML))
        vars["items"] = "".join(l)
        return vars


class WConferenceListEvents(WTemplated):

    def __init__( self, items, aw):
        self._items = items
        self._aw = aw

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["items"] = self._items
        vars["conferenceDisplayURLGen"] = urlHandlers.UHConferenceDisplay.getURL
        vars["aw"] = self._aw
        return vars

class WConferenceListItem(WTemplated):
    def __init__(self, event, aw):
        self._event = event
        self._aw = aw

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["lItem"] = self._event
        vars["conferenceDisplayURLGen"] = urlHandlers.UHConferenceDisplay.getURL
        vars["aw"] = self._aw
        vars["getProtection"] = lambda x: utils.getProtectionText(x)

        return vars


class WEmptyCategory(WTemplated):
    def getVars(self):
        return {}


class WConferenceList(WTemplated):

    def __init__( self, category, wfRegm, showPastEvents ):
        self._categ = category
        self._showPastEvents = showPastEvents

    def getHTML( self, aw, params ):
        self._aw = aw
        return WTemplated.getHTML( self, params )

    def getEventTimeline(self, tz):
        # Getting current and previous at the beggining
        index = Catalog.getIdx('categ_conf_sd').getCategory(self._categ.getId())
        today = nowutc().astimezone(timezone(tz)).replace(hour=0, minute=0, second=0)
        thisMonth = nowutc().astimezone(timezone(tz)).replace(hour=0, minute=0, second=0, day=1)
        nextMonthTS = utc_timestamp(thisMonth + relativedelta(months=1))
        previousMonthTS = utc_timestamp(thisMonth - relativedelta(months=1))
        twoMonthTS = utc_timestamp((today - timedelta(days=60)).replace(day=1))
        future = []
        present = []


        # currentMonth will be used to ensure that when the OPTIMAL_PRESENT_EVENTS is reached
        # the events of that month are still displayed in the present list
        currentMonth = utctimestamp2date(previousMonthTS)
        for ts, conf in index.iteritems(previousMonthTS):
            if ts < nextMonthTS or len(present) < OPTIMAL_PRESENT_EVENTS or is_same_month(currentMonth, utctimestamp2date(ts)):
                present.append(conf)
                currentMonth = utctimestamp2date(ts)
            else:
                future.append(conf)

        if len(present) < MIN_PRESENT_EVENTS:
            present = index.values(twoMonthTS, previousMonthTS) + present

        if not present:
            maxDT = timezone('UTC').localize(datetime.utcfromtimestamp(index.maxKey())).astimezone(timezone(tz))
            prevMonthTS = utc_timestamp(maxDT.replace(day=1))
            present = index.values(prevMonthTS)
        numPast = self._categ.getNumConferences() - len(present) - len(future)
        return present, future, len(future), numPast

    def getVars( self ):
        vars = WTemplated.getVars( self )
        displayTZ = DisplayTZ(self._aw, self._categ, useServerTZ=1).getDisplayTZ()
        vars["ActiveTimezone"] = displayTZ
        vars["presentItems"], vars["futureItems"], vars["numOfEventsInTheFuture"], vars["numOfEventsInThePast"] =  self.getEventTimeline(displayTZ)
        vars["categ"] = self._categ

        vars["showPastEvents"] = self._showPastEvents
        vars["getProtection"] = lambda x: utils.getProtectionText(x)

        return vars


class WCategoryList(WTemplated):

    def __init__( self, categ ):
        self._categ = categ
        self._list = categ.getSubCategoryList()

    def getHTML( self, aw, params ):
        self._aw = aw
        return WTemplated.getHTML( self, params )

    def getVars( self ):

        vars = WTemplated.getVars( self )
        vars["items"] = self._list
        vars["categ"] = self._categ;
        vars["getProtection"] = lambda x: utils.getProtectionText(x)

        return vars

class WCategoryStatisticsListRow(WTemplated):

    def __init__( self, year, percent, number ):
        self._year = year
        self._percent = percent
        self._number = number

    def getHTML( self, aw ):
        self._aw = aw
        return WTemplated.getHTML( self )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["year"] = self._year
        vars["percent"] = self._percent
        vars["percentCompl"] = 100-self._percent
        vars["number"] = self._number
        return vars


class WCategoryStatisticsListRowEmpty(WTemplated):
    def __init__(self, year, end_year):
        self._year = year
        self._end_year = end_year

    def getVars(self):
        v = WTemplated.getVars(self)
        v['year'] = self._year
        v['end_year'] = self._end_year
        return v


class WCategoryStatisticsList(WTemplated):
    def __init__(self, statsName, stats):
        self._stats = stats
        self._statsName = statsName

    def getHTML(self, aw):
        self._aw = aw
        return WTemplated.getHTML(self)

    def getVars(self):
        v = WTemplated.getVars(self)
        # Construction of the tables from the dictionary (stats).
        tmp = []
        stats = {}
        years = self._stats.keys()
        years.sort()
        for y in range(years[0], min(datetime.now().year + 4, years[-1] + 1)):
            stats[y] = self._stats.get(y, 0)
        maximum = max(stats.values())
        years = stats.keys()
        years.sort()
        year, last_year = years[0], years[-1]
        while year < last_year:
            nb = stats[year]
            # We hide holes >=10 years
            if not nb and not any(stats[y] for y in xrange(year, year + 10)):
                end = next((y - 1 for y in xrange(year, last_year) if stats[y]), sys.maxint)
                tmp.append(WCategoryStatisticsListRowEmpty(year, end).getHTML())
                year = end + 1
                continue
            percent = (nb * 100) / maximum
            if nb > 0 and percent == 0:
                percent = 1
            wcslr = WCategoryStatisticsListRow(year, percent, stats[year])
            tmp.append(wcslr.getHTML(self._aw))
            year += 1
        v['statsName'] = self._statsName
        v['statsRows'] = ''.join(tmp)
        v['total'] = sum(stats.values())
        return v


class WConfCreationControlFrame(WTemplated):

    def __init__( self, categ ):
        self._categ = categ

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self._categ.getLocator().getWebForm()
        vars["status"] =  _("OPENED")
        vars["changeStatus"] =  i18nformat("""( <input type="submit" class="btn" name="RESTRICT" value="_("RESTRICT it")"> )""")
        if self._categ.isConferenceCreationRestricted():
            vars["status"] =  _("RESTRICTED")
            vars["changeStatus"] = i18nformat("""( <input type="submit" class="btn" name="OPEN" value="_("OPEN it")"> )""")
        vars["notifyCreationList"] = quoteattr(self._categ.getNotifyCreationList())
        vars["setNotifyCreationURL"] = urlHandlers.UHCategorySetNotifyCreation.getURL(self._categ)
        vars["categoryId"] = self._categ.getId()
        vars["confCreators"] = fossilize(self._categ.getConferenceCreatorList())
        return vars

class WMinutesDisplay(WTemplated):

    def __init__( self, target ):
        self._target = target

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["text"] = self.textToHTML(self._target.readBin())
        return vars

class TabControl:

    def __init__( self, parent=None, child=None ):
        self._tabs = []
        self._active = None
        self._default = None
        # Parent element (another tabcontrol),
        # in case there is nesting
        self._parent = parent

        if parent != None:
            parent.setChild(self);
        self._child = child

    def _addTab( self, tab ):
        self._tabs.append( tab )
        if len( self._tabs ) == 1:
            self._default = tab
            self._active = tab

    def newTab( self, id, caption, url, hidden=False, className="" ):
        tab = Tab( self, id, caption, url, hidden=hidden, className=className )
        self._addTab( tab )
        return tab

    def setDefaultTab( self, tab ):
        if tab in self._tabs:
            self._default = tab

    def getDefaultTab( self ):
        return self._default

    def setActiveTab( self, tab ):
        if tab in self._tabs:
            self._active = tab

    def getActiveTab( self ):
        return self._active

    def getTabList( self ):
        return self._tabs

    def getTabById( self, id ):
        for tab in self.getTabList():
            if tab.getId() == id:
                return tab
        return None

    def getParent( self ):
        # retrieve parent TabControl
        return self._parent

    def setChild( self, child ):
        self._child = child

    def getChild( self ):
        # retrieve child TabControl
        return self._child

    def getLevel( self ):
        tmp = self.getParent()
        level = 0
        while tmp:
            level += 1
            tmp = tmp.getParent()
        return level

class Tab:

    def __init__( self, owner, id, caption, URL, hidden = False, className="" ):
        self._owner = owner
        self._id = id.strip()
        self._caption = caption.strip()
        self._url = URL
        self._enabled = True
        self._subtabControl=None
        self._hidden = hidden
        self._className = className

    def __repr__(self):
        return '<Tab(%s, %s, %s, %s)>' % (self._id, self._caption, self._url, int(self.isActive()))

    def getId( self ):
        return self._id

    def getCaption( self ):
        return self._caption

    def setCaption( self, cp):
        self._caption = cp

    def getURL( self ):
        return self._url

    def setDefault( self ):
        self._owner.setDefaultTab( self )

    def isDefault( self ):
        return self._owner.getDefaultTab() == self

    def isActive( self ):
        return self._owner.getActiveTab() == self

    def setActive( self ):
        self._owner.setActiveTab( self )

    def enable( self ):
        self._enabled = True

    def disable( self ):
        self._enabled = False

    def setEnabled(self,value):
        self._enabled=value

    def isEnabled( self ):
        return self._enabled

    def setHidden(self, value):
        self._hidden = value

    def isHidden( self ):
        return self._hidden

    def getSubTabControl(self):
        return self._subtabControl

    def newSubTab( self, id, caption, url ):
        # guarantee that a subtabControl exists
        if not self._subtabControl:
            self._subtabControl = TabControl(parent=self._owner)

        tab=self._subtabControl.newTab( id, caption, url )
        return tab

    def hasChildren(self):
        return self._subtabControl is not None

    def getClassName(self):
        return self._className


class WTabControl(WTemplated):
    def __init__(self, ctrl, accessWrapper, **params):
        self._tabCtrl = ctrl
        self._aw = accessWrapper

    def _getTabs(self):
        tabs = []
        for tab in self._tabCtrl.getTabList():
            if (not tab.isEnabled() or tab.isHidden()) and not tab.isActive():
                # The active tab may never be skipped. If we skipped it jQuery would consider the first tab active and
                # send an AJAX request to load its contents, which would break the whole page.
                continue
            tabs.append((tab.getCaption(), tab.getURL(), tab.isActive(), tab.getClassName()))
        return tabs

    def _getActiveTabId(self):
        skipped = 0
        for i, tab in enumerate(self._tabCtrl.getTabList()):
            if tab.isActive():
                return i - skipped
            if not tab.isEnabled() or tab.isHidden():
                skipped += 1
        return 0

    def _getActiveTab(self):
        for tab in self._tabCtrl.getTabList():
            if tab.isActive():
                return tab

    def _getBody(self):
        tab = self._getActiveTab()
        if not tab:
            return self._body
        sub = tab.getSubTabControl()
        if not sub:
            return self._body
        return WTabControl(sub, self._aw).getHTML(self._body)

    def getHTML(self, body):
        self._body = body
        return WTemplated.getHTML(self)

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars['body'] = self._getBody()
        vars['tabs'] = self._getTabs()
        vars['activeTab'] = self._getActiveTabId()
        vars['tabControlId'] = id(self)

        return vars


class WSelectionBox(WTemplated):

    def getVars(self):
        vars=WTemplated.getVars(self)
        if not vars.has_key("description"):
            vars["description"]=""
        if not vars.has_key("options"):
            vars["options"]=""
        if not vars.has_key("table_width"):
            vars["table_width"]=""
        return vars

class WSelectionBoxAuthors:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  _("Please make your selection if you want to add the submitter/s directly to any of the following roles:"),\
            "options":  i18nformat("""<input type="radio" name="submitterRole" value="primaryAuthor"> _("Primary author")<br>
                        <input type="radio" name="submitterRole" value="coAuthor"> _("Co-author")<br><hr>
                        <input type="checkbox" name="submitterRole" value="speaker"> _("Speaker")
                            """)
          }
        return wc.getHTML(p)

class WMSelectionBoxAuthors:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  _("Please make your selection if you want to add the submitter/s directly to:"),\
            "options":  i18nformat("""<input type="checkbox" name="submitterRole" value="speaker"> _("Speaker")
                            """), \
            "table_width": "180px" \
          }
        return wc.getHTML(p)

class WSelectionBoxSubmitter:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  i18nformat(""" _("Please check the box if you want to add them as submitters"):<br><br><i><font color=\"black\"><b> _("Note"): </b></font> _("If this person is not already a user they will be sent an email asking them to create an account. After their registration the user will automatically be given submission rights").</i><br>"""),\
            "options":  i18nformat("""<input type="checkbox" name="submissionControl" value="speaker" checked> _("Add as submitter")
                        """)
          }
        return wc.getHTML(p)

class WSelectionBoxConveners:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description": _("Please make your selection if you want to add the result/s directly to the role of session Convener:"),\
            "options":  i18nformat("""<input type="checkbox" name="userRole" value="convener"> _("Add as convener")
                        """)
          }
        return wc.getHTML(p)

class WSelectionBoxConvToManagerCoordinator:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  i18nformat(""" _("Please check the box if you want to add them as managers/coordinators"):"""),\
            "options":  i18nformat("""<input type="checkbox" name="managerControl"> _("Add as session manager")<br>
                             <input type="checkbox" name="coordinatorControl"> _("Add as session coordinator")
                        """)
          }
        return wc.getHTML(p)


class WSelectionBoxCloneLecture :

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  _("Please check the boxes indicating which elements of the lecture you want to clone"),\
            "options":  i18nformat("""<input type="checkbox" name="cloneDetails" id="cloneDetails" checked="1" disabled="1" value="1">  _("Event details")
                          <input type="checkbox" name="cloneMaterials" id="cloneMaterials" value="1" >  _("Attached materials")
                          <input type="checkbox" name="cloneAccess" id="cloneAccess" value="1" >  _("Access and management privileges")
                        """)
          }
        return wc.getHTML(p)


class WAccountAlreadyActivated(WTemplated):

    def __init__(self, av):
        self._av = av

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars


class WAccountActivated(WTemplated):

    def __init__(self, av):
        self._av = av

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars


class WAccountDisabled(WTemplated):

    def __init__(self, av):
        self._av = av

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars


class WUnactivatedAccount(WTemplated):

    def __init__(self, av):
        self._av = av

    def getVars( self ):
        vars = WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["moderated"]=minfo.getModerateAccountCreation()
        return vars


class WAbstractModIntCommentEdit(WTemplated):

    def __init__(self,comment):
        self._comment=comment

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["content"]=self.htmlText(self._comment.getContent())
        return vars


class WAbstractModNewIntComment(WTemplated):

    def __init__(self,aw,abstract):
        self._aw=aw
        self._abstract=abstract

    def getVars(self):
        vars=WTemplated.getVars(self)
        return vars


class WSessionModifComm(WTemplated):
    def __init__(self, aw,session):
        self._aw = aw
        self._session = session
        self._conf = session.getConference()

    def _getHTML(self,editCommentsURLGen):
        try:
            comment =self._session.getComments()
            if comment=="":
               comment= _("No Session Comment Entered")
        except:
            comment = _("No Session Comment Entered")
            self._session.setComments("")

        modifButton=""
        if self._conf.canModify(self._aw):

            modifButton =  i18nformat("""<form action=%s method="POST">
                    <td align="center">
                        <input type="submit" class="btn" value="_("modify")">
                    </td>
                    </form>
                        """)%quoteattr(str(editCommentsURLGen(self._session)))
        return ( i18nformat("""
        <table width="50%%" align="center" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"> _("Session comment")</td>
        </tr>
        <tr>
            <td>
                %s
            </td>
        </tr>
        <tr>
            %s
        </tr>
        </table> """)%(comment,modifButton))

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["comment"]=self._getHTML(vars["editCommentsURLGen"])
        return vars



class WSessionModifCommEdit(WTemplated):

    def __init__(self,comment):
        self._comment=comment

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["comment"]=self.htmlText(self._comment)
        return vars

class WAbstractModIntComments(WTemplated):

    def __init__(self,aw,abstract):
        self._aw=aw
        self._abstract=abstract

    def _getCommentsHTML(self,commentEditURLGen,commentRemURLGen):
        res=[]
        commentList = self._abstract.getIntCommentList()
        for c in commentList:
            mailtoSubject="[Indico] Abstract %s: %s"%(self._abstract.getId(), self._abstract.getTitle())
            mailtoURL=URL("mailto:%s"%c.getResponsible().getEmail())
            mailtoURL.addParam("subject", mailtoSubject)
            responsible="""<a href=%s>%s</a>"""%(quoteattr(str(mailtoURL)),self.htmlText(c.getResponsible().getFullName()))
            date=self.htmlText(c.getCreationDate().strftime("%Y-%m-%d %H:%M"))
            buttonMod,buttonRem="",""
            if self._aw.getUser()==c.getResponsible():
                buttonMod= i18nformat("""
                    <form action=%s method="POST">
                    <td valign="bottom">
                        <input type="submit" class="btn" value="_("modify")">
                    </td>
                    </form>
                        """)%quoteattr(str(commentEditURLGen(c)))
                buttonRem= i18nformat("""
                    <form action=%s method="POST">
                    <td valign="bottom">
                        <input type="submit" class="btn" value="_("remove")">
                    </td>
                    </form>
                        """)%quoteattr(str(commentRemURLGen(c)))
            res.append("""
                <tr>
                    <td bgcolor="white" style="border-top:1px solid #777777;border-bottom:1px solid #777777;">
                        <table>
                            <tr>
                                <td width="100%%">%s on %s</td>
                            </tr>
                            <tr>
                                <td>%s</td>
                                %s
                                %s
                            </tr>
                        </table>
                    </td>
                </tr>"""%(responsible,date,c.getContent(),buttonMod,buttonRem))
        if res == []:
            res.append( i18nformat("""<tr><td align=\"center\" style=\"color:black\"><br>--_("no internal comments")--<br><br></td></tr>"""))
        return "".join(res)

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["comments"]=self._getCommentsHTML(vars["commentEditURLGen"],vars["commentRemURLGen"])
        vars["newCommentURL"]=quoteattr(str(vars["newCommentURL"]))
        return vars


class WAbstractModMarkAsDup(WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["duplicateURL"]=quoteattr(str(vars["duplicateURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        return vars


class WAbstractModUnMarkAsDup(WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract


    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["unduplicateURL"]=quoteattr(str(vars["unduplicateURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        return vars


class WScheduleAddContributions(WTemplated):

    def __init__(self,selectList,targetDay=None):
        self._contribList=selectList
        self._targetDay=targetDay

    def _getContribListHTML(self):
        res=[]
        contribList=filters.SimpleFilter(None,contribFilters.SortingCriteria(["number"])).apply(self._contribList)
        for contrib in self._contribList:
            typeCaption=""
            if contrib.getType() is not None:
                typeCaption=contrib.getType().getName()
            l=[]
            for spk in contrib.getSpeakerList():
                l.append("""%s"""%(self.htmlText(spk.getFullName())))
            spksCaption="<br>".join(l)
            res.append("""
                <tr>
                    <td valign="top">
                        <input type="checkbox" name="manSelContribs" value=%s>
                    </td>
                    <td valign="top">%s</td>
                    <td valign="top">[%s]</td>
                    <td valign="top"><i>%s</i></td>
                    <td valign="top">%s</td>
                </tr>
                        """%(quoteattr(str(contrib.getId())),
                            self.htmlText(contrib.getId()),
                            self.htmlText(typeCaption),
                            self.htmlText(contrib.getTitle()),
                            spksCaption))
        return "".join(res)


    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["contribs"]="".join(self._getContribListHTML())
        vars["targetDay"]=""
        if self._targetDay is not None:
            vars["targetDay"]="""<input type="hidden" name="targetDay" value=%s>"""%(quoteattr(str(self._targetDay.strftime("%Y-%m-%d"))))
        return vars


class WSchEditContrib(WTemplated):

    def __init__(self,contrib):
        self._contrib=contrib

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["title"]=self.htmlText(self._contrib.getTitle())
        confTZ = self._contrib.getConference().getTimezone()
        sDate=self._contrib.getStartDate().astimezone(timezone(confTZ))
        vars["sYear"]=quoteattr(str(sDate.year))
        vars["sMonth"]=quoteattr(str(sDate.month))
        vars["sDay"]=quoteattr(str(sDate.day))
        vars["sHour"]=quoteattr(str(sDate.hour))
        vars["sMinute"]=quoteattr(str(sDate.minute))
        vars["durHours"]=quoteattr(str(int(self._contrib.getDuration().seconds/3600)))
        vars["durMins"]=quoteattr(str(int((self._contrib.getDuration().seconds%3600)/60)))
        defaultDefinePlace=defaultDefineRoom=""
        defaultInheritPlace=defaultInheritRoom="checked"
        locationName,locationAddress,roomName="","",""
        if self._contrib.getOwnLocation():
            defaultDefinePlace,defaultInheritPlace="checked",""
            locationName=self._contrib.getLocation().getName()
            locationAddress=self._contrib.getLocation().getAddress()
        if self._contrib.getOwnRoom():
            defaultDefineRoom,defaultInheritRoom="checked",""
            roomName=self._contrib.getRoom().getName()
        vars["defaultInheritPlace"]=defaultInheritPlace
        vars["defaultDefinePlace"]=defaultDefinePlace
        vars["confPlace"]=""
        confLocation=self._contrib.getOwner().getLocation()
        if self._contrib.isScheduled():
            confLocation=self._contrib.getSchEntry().getSchedule().getOwner().getLocation()
        if confLocation:
            vars["confPlace"]=confLocation.getName()
        vars["locationName"]=locationName
        vars["locationAddress"]=locationAddress
        vars["defaultInheritRoom"]=defaultInheritRoom
        vars["defaultDefineRoom"]=defaultDefineRoom
        vars["confRoom"]=""
        confRoom=self._contrib.getOwner().getRoom()
        if self._contrib.isScheduled():
            confRoom=self._contrib.getSchEntry().getSchedule().getOwner().getRoom()
        if confRoom:
            vars["confRoom"]=confRoom.getName()
        vars["roomName"]=quoteattr(roomName)
        vars["parentType"]="conference"
        if self._contrib.getSession() is not None:
            vars["parentType"]="session"
            if self._contrib.isScheduled():
                vars["parentType"]="session slot"
        vars["boardNumber"]=quoteattr(str(self._contrib.getBoardNumber()))
        vars["autoUpdate"] = ""
        return vars


class WSessionModEditDataCode(WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=WTemplated.getVars(self)
        vars["code"]=quoteattr(str(vars.get("code","")))
        return vars

class WSessionModEditDataType(WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=WTemplated.getVars(self)
        l=[]
        currentTTType=vars.get("tt_type",conference.SlotSchTypeFactory.getDefaultId())
        for i in conference.SlotSchTypeFactory.getIdList():
            sel=""
            if i==currentTTType:
                sel=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(str(i)),
                        sel,self.htmlText(i)))
        vars["tt_types"]="".join(l)
        return vars

class WSessionModEditDataColors(WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=WTemplated.getVars(self)
        return vars

class WSessionModEditData(WTemplated):

    def __init__(self, targetConf, aw, pageTitle="", targetDay=None):
        self._conf = targetConf
        self._title = pageTitle
        self._targetDay = targetDay
        self._aw = aw

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["conference"] = self._conf
        vars["eventId"] = "s" + vars["sessionId"]
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()
        vars["pageTitle"] = self.htmlText(self._title)
        vars["postURL"] = quoteattr(str(vars["postURL"]))
        vars["title"] = quoteattr(str(vars.get("title", "")))
        vars["description"] = self.htmlText(vars.get("description", ""))
        vars["durHour"] = quoteattr(str(vars.get("durHour", 0)))
        vars["durMin"] = quoteattr(str(vars.get("durMin", 20)))
        vars["defaultInheritPlace"] = "checked"
        vars["defaultDefinePlace"] = ""

        if vars.get("convenerDefined", None) is None:
            sessionId = vars["sessionId"]
            session = self._conf.getSessionById(sessionId)
            html = []
            for convener in session.getConvenerList():
                text = """
                 <tr>
                     <td width="5%%"><input type="checkbox" name="%ss" value="%s"></td>
                     <td>&nbsp;%s</td>
                 </tr>""" % ("convener", convener.getId(), convener.getFullName())
                html.append(text)
            vars["definedConveners"] = """
                                         """.join(html)
        if vars.get("locationAction", "") == "define":
            vars["defaultInheritPlace"] = ""
            vars["defaultDefinePlace"] = "checked"
        vars["confPlace"] = ""
        confLocation = self._conf.getConference().getLocation()
        if confLocation:
            vars["confPlace"] = self.htmlText(confLocation.getName())
        vars["locationName"] = quoteattr(str(vars.get("locationName", "")))
        vars["locationAddress"] = self.htmlText(
            vars.get("locationAddress", ""))
        vars["defaultInheritRoom"] = ""
        vars["defaultDefineRoom"] = ""
        vars["defaultExistRoom"] = ""
        if vars.get("roomAction", "") == "inherit":
            vars["defaultInheritRoom"] = "checked"
            roomName = ""
        elif vars.get("roomAction", "") == "define":
            vars["defaultDefineRoom"] = "checked"
            roomName = vars.get(
                "bookedRoomName") or vars.get("roomName", "")
        elif vars.get("roomAction", "") == "exist":
            vars["defaultExistRoom"] = "checked"
            roomName = vars.get("exists", "") or vars.get("roomName", "")
        else:
            vars["defaultInheritRoom"] = "checked"
            roomName = ""

        vars["confRoom"] = ""
        rx = []
        roomsexist = self._conf.getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            sel = ""
            if room == roomName:
                sel = "selected=\"selected\""
            rx.append(
                """<option value=%s %s>%s</option>""" % (quoteattr(str(room)),
                                                         sel, self.htmlText(room)))
        vars["roomsexist"] = "".join(rx)
        confRoom = self._conf.getConference().getRoom()
        if confRoom:
            vars["confRoom"] = self.htmlText(confRoom.getName())
        vars["roomName"] = quoteattr(str(roomName))

        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(self._conf)
        if wf is not None:
            type = wf.getId()
        else:
            type = "conference"
        if type == "conference":
            vars["Type"] = WSessionModEditDataType().getHTML(vars)
            vars["Colors"] = WSessionModEditDataColors().getHTML(vars)
            vars["code"] = WSessionModEditDataCode().getHTML(vars)
        else:
            vars["Type"] = ""
            vars["Colors"] = ""
            vars["code"] = ""
        return vars


#--------------------------------------------------------------------------------------

class WConfModMoveContribsToSessionConfirmation(WTemplated):

    def __init__(self,conf,contribIdList=[],targetSession=None):
        self._conf=conf
        self._contribIdList=contribIdList
        self._targetSession=targetSession

    def _getWarningsHTML(self):
        wl=[]
        for id in self._contribIdList:
            contrib=self._conf.getContributionById(id)
            if contrib is None:
                continue
            spkList=[]
            for spk in contrib.getSpeakerList():
                spkList.append(self.htmlText(spk.getFullName()))
            spkCaption=""
            if len(spkList)>0:
                spkCaption=" by %s"%"; ".join(spkList)
            if (contrib.getSession() is not None and \
                            contrib.getSession()!=self._targetSession):
                scheduled=""
                if contrib.isScheduled():
                    scheduled= i18nformat("""  _("and scheduled") (%s)""")%self.htmlText(contrib.getStartDate().strftime("%Y-%b-%d %H:%M"))
                wl.append( i18nformat("""
                        <li>%s-<i>%s</i>%s: is <font color="red"> _("already in session") <b>%s</b>%s</font></li>
                """)%(self.htmlText(contrib.getId()),
                        self.htmlText(contrib.getTitle()),
                        spkCaption,
                        self.htmlText(contrib.getSession().getTitle()),
                        scheduled))
            if (contrib.getSession() is None and \
                            self._targetSession is not None and \
                            contrib.isScheduled()):
                wl.append( i18nformat("""
                        <li>%s-<i>%s</i>%s: is <font color="red"> _("scheduled") (%s)</font></li>
                """)%(self.htmlText(contrib.getId()),
                        self.htmlText(contrib.getTitle()),
                        spkCaption,
                        self.htmlText(contrib.getStartDate().strftime("%Y-%b-%d %H:%M"))))
        return "<ul>%s</ul>"%"".join(wl)

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["systemIconWarning"]=Config.getInstance().getSystemIconURL("warning")
        vars["contribIdList"]=", ".join(self._contribIdList)
        vars["targetSession"]="--none--"
        if self._targetSession is not None:
            vars["targetSession"]=self.htmlText("%s"%self._targetSession.getTitle())
        vars["warnings"]=self._getWarningsHTML()
        vars["targetSessionId"]=quoteattr("--none--")
        if self._targetSession is not None:
            vars["targetSessionId"]=quoteattr(str(self._targetSession.getId()))
        l=[]
        for id in self._contribIdList:
            l.append("""<input type="hidden" name="contributions" value=%s">"""%quoteattr(str(id)))
        vars["contributions"]="\n".join(l)
        return vars


class WConfTBDrawer(WTemplated):

    def __init__(self,tb):
        self._tb=tb

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["items"] = [item for item in self._tb.getItemList() if item.isEnabled()]
        return vars

class WConfTickerTapeDrawer(WTemplated):

    def __init__(self,conf, tz=None):
        self._conf=conf
        self._tz = tz
        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf, False)
        self._tickerTape = dm.getTickerTape()

    def getNowHappeningHTML( self, params=None ):
        if not self._tickerTape.isActive():
            return None

        html = WTemplated.getHTML( self, params )

        if html == "":
            return None

        return html

    def getSimpleText( self ):
        if not self._tickerTape.isSimpleTextEnabled() or \
           self._tickerTape.getText().strip() == "":
            return None

        return self._tickerTape.getText()

    def getVars(self):
        vars = WTemplated.getVars( self )

        vars["nowHappeningArray"] = None
        if self._tickerTape.isNowHappeningEnabled():
            vars["nowHappeningArray"] = self._getNowHappening()

        return vars

    def _getNowHappening( self ):
        # This will contain a string formated for use in the template
        # javascripts
        nowHappeningArray = None

        # currently happening:
        n = nowutc()
        entries = self._conf.getSchedule().getEntriesOnDate(n)
        entryCaptions = []
        for entry in entries:
            if isinstance(entry, schedule.LinkedTimeSchEntry) and \
                                  isinstance(entry.getOwner(), conference.SessionSlot):
                ss=entry.getOwner()
                ssEntries=ss.getSchedule().getEntriesOnDate(n)
                if isinstance(ss.getSchedule(), conference.PosterSlotSchedule):
                    ssEntries=ss.getSchedule().getEntries()
                for ssEntry in ssEntries:
                    title=ssEntry.getTitle()
                    if isinstance(ssEntry.getOwner(), conference.Contribution):
                        title="""<a href=%s>%s</a>"""%( \
                                quoteattr(str(urlHandlers.UHContributionDisplay.getURL(ssEntry.getOwner()))), title)
                    else:
                        title="""<a href=%s>%s</a>"""%( \
                                quoteattr(str(urlHandlers.UHSessionDisplay.getURL(ssEntry.getOwner()))), title)
                    if ssEntry.getOwnRoom() is not None:
                        if self._conf.getRoom() is None or \
                            ssEntry.getOwnRoom().getName().strip().lower() != self._conf.getRoom().getName().strip().lower():
                                title="%s (%s)"%(title, ssEntry.getOwnRoom().getName().strip())
                    entryCaptions.append("%s <em>%s-%s</em>" %(title,
                        entry.getAdjustedStartDate(self._tz).strftime("%H:%M"), \
                        entry.getAdjustedEndDate(self._tz).strftime("%H:%M")))
            else:
                title=entry.getTitle()
                if isinstance(entry.getOwner(), conference.Contribution):
                    title="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHContributionDisplay.getURL(entry.getOwner()))), title)
                else:
                    url=urlHandlers.UHConferenceTimeTable.getURL(self._conf)
                    url.addParam("showDate",entry.getStartDate().strftime("%d-%B-%Y"))
                    title="""<a href=%s>%s</a>"""%(quoteattr(str(url)), title)
                    if entry.getOwnRoom() is not None:
                        if self._conf.getRoom() is None or \
                            entry.getOwnRoom().getName().strip().lower() != self._conf.getRoom().getName().strip().lower():
                                title="%s (%s)"%(title, entry.getOwnRoom().getName().strip())
                entryCaptions.append("%s <em>%s-%s</em>" %(title,
                    entry.getAdjustedStartDate(self._tz).strftime("%H:%M"), \
                    entry.getAdjustedEndDate(self._tz).strftime("%H:%M")))
        if entryCaptions!=[]:
            nowHappeningArray = """['%s']""" %("', '".join(entryCaptions))

        return nowHappeningArray


class WShowExistingMaterial(WTemplated):

    def __init__(self,target, mode='display', showTitle=True):
        """
        mode should be 'display' or 'management'
        """
        self._target=target
        self._mode = mode
        self._showTitle = showTitle


    def getVars(self):
        vars=WTemplated.getVars(self)

        # yes, this may look a bit redundant, but materialRegistry isn't
        # bound to a particular target
        materialRegistry = self._target.getMaterialRegistry()
        vars["materialList"] = materialRegistry.getMaterialList(self._target)


        if self._showTitle:
            vars["existingMaterialsTitle"] = """ <div class="groupTitle" id="title">%s</div>""" % _("Existing material")
        else:
            vars["existingMaterialsTitle"] = " "
        vars["materialModifHandler"] = vars.get("materialModifHandler", None)
        vars["materialProtectHandler"] = vars.get("materialProtectHandler", None)
        vars["resourcesFileModifHandler"] = vars.get("resourcesFileModifHandler", None)
        vars["resourcesFileProtectHandler"] = vars.get("resourcesFileProtectHandler", None)
        vars["resourcesLinkModifHandler"] = vars.get("resourcesLinkModifHandler", None)
        vars["resourcesLinkProtectHandler"] = vars.get("resourcesLinkProtectHandler", None)
        vars['mode'] = self._mode

        return vars

class WShowExistingReviewingMaterial(WTemplated):

    def __init__(self, target):
        self._target = target


    def getVars(self):
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager

        vars = WTemplated.getVars(self)
        reviewManager = self._target.getReviewManager()
        vars["Contribution"] = self._target
        vars["CanModify"] = (self._target.getReviewing().getReviewingState() in [2, 3] if self._target.getReviewing() else True) and \
                            (self._target.canModify(self._rh._aw) or RCPaperReviewManager.hasRights(self._rh) \
                            or reviewManager.isReferee(self._rh._getUser()) or reviewManager.isEditor(self._rh._getUser()))
        vars["ShowWarning"] = (self._target.getReviewing().getReviewingState() == 2 if self._target.getReviewing() else False) and \
                            (self._target.canModify(self._rh._aw) or RCPaperReviewManager.hasRights(self._rh) \
                            or reviewManager.isReferee(self._rh._getUser()) or reviewManager.isEditor(self._rh._getUser()))

        return vars


class WSchRelocateTime(WTemplated):

    def getVars(self):
        vars = WTemplated.getVars(self)
        return vars


class WSchRelocate(WTemplated):

    def __init__(self, entry):
        self._entry=entry
        if isinstance(self._entry, conference.Contribution):
            self._conf = self._entry.getConference()
        else:
            # entry is a break
            self._conf = self._entry.getSchedule().getOwner().getConference()

    def _getTargetPlaceHTML(self):
        html=[]
        html.append( i18nformat("""
                        <tr><td><input type="radio" name="targetId" value="conf"></td><td colspan="3" width="100%%"><b> _("Top timetable (within no session)")</b></td></tr>
                        <tr><td colspan="4"><hr></td></tr>
                    """))
        sessionList=self._conf.getSessionList()
        sessionList.sort(conference.Session._cmpTitle)
        for session in sessionList:
            if len(session.getSlotList())==1:
                html.append("""
                        <tr><td><input type="radio" name="targetId" value="%s:%s"></td><td colspan="3" style="background-color:%s;color:%s" width="100%%">&nbsp;%s&nbsp;<b>%s</b></td></tr>
                    """%(session.getId(), session.getSlotList()[0].getId(), session.getColor(), session.getTextColor(), session.getStartDate().strftime("%d-%m-%Y"),session.getTitle()) )
            else:
                html.append("""
                        <tr><td></td><td colspan="3" style="background-color:%s;" width="100%%">
                            <table>
                                <tr><td colspan="2" width="100%%" style="color:%s"><b>%s:</b></td></tr>
                    """%(session.getColor(), session.getTextColor(), session.getTitle()) )
                for slotEntry in session.getSchedule().getEntries():
                    slot=slotEntry.getOwner()
                    html.append("""
                        <tr><td><input type="radio" name="targetId" value="%s:%s"></td><td width="100%%" style="color:%s">%s <small>(%s %s-%s)</small></td></tr>
                    """%(session.getId(), slot.getId(), session.getTextColor(), slot.getTitle() or "[slot %s]"%slot.getId(),  slot.getAdjustedStartDate().strftime("%d-%m-%Y"),\
                            slot.getAdjustedStartDate().strftime("%H:%M"), slot.getAdjustedEndDate().strftime("%H:%M")) )
                html.append("</table></td></tr>")
        return "".join(html)


    def getVars(self):
        vars = WTemplated.getVars(self)
        if isinstance(self._entry, conference.Contribution):
            vars["entryType"]="Contribution"
        else:
            vars["entryType"]=""
        vars["entryTitle"]=self._entry.getTitle()
        vars["targetPlace"]=self._getTargetPlaceHTML()
        vars["autoUpdate"]=""
        return vars

class WReportNumbersTable(WTemplated):

    def __init__(self, target, type="event"):
        self._target=target
        self._type=type

    def _getCurrentItems(self):
        rns = self._target.getReportNumberHolder().listReportNumbers()
        reportCodes = []

        for rn in rns:
            key = rn[0]
            if key in Configuration.Config.getInstance().getReportNumberSystems().keys():
                number = rn[1]
                reportNumberId="s%sr%s"%(key, number)
                name=Configuration.Config.getInstance().getReportNumberSystems()[key]["name"]
                reportCodes.append({"id" : reportNumberId, "number": number, "system": key, "name": name})
        return reportCodes

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["params"] = {"confId": self._target.getConference().getId()}

        if self._type == "event":
            vars["addAction"] = "reportNumbers.conference.addReportNumber"
            vars["deleteAction"] = "reportNumbers.conference.removeReportNumber"
        elif self._type == "contribution":
            vars["params"]["contribId"] = self._target.getId()
            vars["addAction"] = "reportNumbers.contribution.addReportNumber"
            vars["deleteAction"] = "reportNumbers.contribution.removeReportNumber"
        else:
            vars["params"]["contribId"] = self._target.getContribution().getId()
            vars["params"]["subcontribId"] = self._target.getId()
            vars["addAction"] = "reportNumbers.subcontribution.addReportNumber"
            vars["deleteAction"] = "reportNumbers.subcontribution.removeReportNumber"
        vars["items"]=self._getCurrentItems()
        systems = Configuration.Config.getInstance().getReportNumberSystems()
        vars["reportNumberSystems"]= dict([(system, systems[system]["name"]) for system in systems])
        return vars

# ============================================================================
# === ROOM BOOKING RELATED ===================================================
# ============================================================================
# 1. Freestanding
# 2. In the context of an event

from MaKaC.rb_reservation import ReservationBase, Collision, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.plugins.RoomBooking.default.room import Room
from MaKaC.rb_tools import iterdays
from calendar import day_name
from MaKaC.rb_location import Location, CrossLocationFactory
from indico.util.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.roomBooking import IRoomBarFossil, IBarFossil

class Bar( Fossilizable ):
    """
    Keeps data necessary for graphical bar on calendar.
    """
    fossilizes(IBarFossil)
    BLOCKED, PREBOOKED, PRECONCURRENT, UNAVAILABLE, CANDIDATE, PRECONFLICT, CONFLICT = xrange(0, 7)
    # I know this names are not wisely choosed; it's due to unexpected additions
    # without refactoring
    # BLOCKED:        room is blocked (dark-gray)
    # CANDIDATE:      represents new reservation (green)
    # CONFLICT:       overlap between candidate and confirmed resv. (dark red)
    # PREBOOKED:      represents pre-reservation (yellow)
    # PRECONFLICT:    represents conflict with pre-reservation (orange)
    # PRECONCURRENT:  conflicting pre-reservations
    # UNAVAILABLE :   represents confirmed reservation (bright-red)

    def __init__( self, c, barType ):
        self.startDT = c.startDT
        self.endDT = c.endDT
        self.forReservation = c.withReservation
        self.type = barType

    def __cmp__( self, obj ):
        return cmp( self.type, obj.type )

class RoomBars( Fossilizable ):

    fossilizes(IRoomBarFossil)

    room = None
    bars = []

    def __init__( self, room, bars ):
        self.room = room
        self.bars = bars
    def __cmp__( self, obj ):
        return cmp( self.room, obj.room )

# ============================================================================
# == FREESTANDING ==== (Room Booking Related) ================================
# ============================================================================

class WRoomBookingWelcome( WTemplated ):

    def __init__(self):
        self.__adminList = AdminList.getInstance()

    def getVars( self ):
        vars = WTemplated.getVars( self )
        return vars

# ============================================================================
# == EVENT CONTEXT ==== (Room Booking Related) ===============================
# ============================================================================


# 0. Choosing an "event" (conference / session / contribution)...

class WRoomBookingChooseEvent( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["conference"] = self._rh._conf
        vars["contributions"] = list( [ c for c in self._rh._conf.getContributionList() if c.getStartDate() ] )

        return vars

# 1. Searching

class WRoomBookingSearch4Rooms( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._standalone = standalone
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["standalone"] = self._standalone

        vars["Location"] = Location
        vars["rooms"] = self._rh._rooms
        vars["possibleEquipment"] = self._rh._equipment
        vars["forNewBooking"] = self._rh._forNewBooking
        vars["eventRoomName"] = self._rh._eventRoomName
        vars["isResponsibleForRooms"] = Room.isAvatarResponsibleForRooms(self._rh.getAW().getUser())

        vars["preview"] = False

        vars["startDT"] = session.get("rbDefaultStartDT")
        vars["endDT"] = session.get("rbDefaultEndDT")
        vars["startT"] = session.get("rbDefaultStartDT").time().strftime("%H:%M")
        vars["endT"] = session.get("rbDefaultEndDT").time().strftime("%H:%M")
        vars["repeatability"] = session.get("rbDefaultRepeatability")

        if self._standalone:
            # URLs for standalone room booking
            vars["roomBookingRoomListURL"] = urlHandlers.UHRoomBookingRoomList.getURL( None )
            vars["detailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            vars["bookingFormUH"] =  urlHandlers.UHRoomBookingBookingForm
        else:
            # URLs for room booking in the event context
            vars["roomBookingRoomListURL"] = urlHandlers.UHConfModifRoomBookingRoomList.getURL( self._rh._conf )
            vars["detailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            vars["bookingFormUH"] =  urlHandlers.UHConfModifRoomBookingBookingForm

        return vars

class WRoomBookingSearch4Bookings( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["today"] = datetime.now()
        vars["weekLater"] = datetime.now() + timedelta( 7 )
        vars["Location"] = Location
        vars["rooms"] = self._rh._rooms
        vars["repeatability"] = None
        vars["isResponsibleForRooms"] = Room.isAvatarResponsibleForRooms(self._rh.getAW().getUser())
        vars["roomBookingBookingListURL"] = urlHandlers.UHRoomBookingBookingList.getURL( None )

        return vars

class WRoomBookingBookRoom( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )
        rooms = self._rh._rooms

        vars["today"] = datetime.now()
        vars["rooms"] = fossilize(rooms)
        vars["maxRoomCapacity"] = max(room.capacity for room in rooms) if rooms else 0
        vars["roomBookingBookingListURL"] = urlHandlers.UHRoomBookingBookingListForBooking.getURL(newBooking = 'True')

        return vars

class WRoomBookingMapOfRooms(WTemplated):

    def __init__(self, **params):
        if params is not None:
            self._params = params
        else:
            self._params = {}
        WTemplated.__init__(self)

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["mapOfRoomsWidgetURL"] = urlHandlers.UHRoomBookingMapOfRoomsWidget.getURL(None, **self._params)

        return vars

class WRoomBookingMapOfRoomsWidget(WTemplated):

    def __init__(self, aspects, buildings, defaultLocation, forVideoConference, roomID):
        self._aspects = aspects
        self._buildings = buildings
        self._defaultLocation = defaultLocation
        self._forVideoConference = forVideoConference
        self._roomID = roomID

    def getVars(self):
        vars = WTemplated.getVars(self)

        vars["aspects"] = self._aspects
        vars["buildings"] = self._buildings
        vars["defaultLocation"] = self._defaultLocation
        vars["forVideoConference"] = self._forVideoConference
        vars["roomID"] = self._roomID

        vars["roomBookingRoomListURL"] = urlHandlers.UHRoomBookingRoomList.getURL(None)
        vars["startDT"] = session.get("rbDefaultStartDT")
        vars["endDT"] = session.get("rbDefaultEndDT")
        vars["startT"] = session.get("rbDefaultStartDT").time().strftime("%H:%M")
        vars["endT"] = session.get("rbDefaultEndDT").time().strftime("%H:%M")
        vars["repeatability"] = session.get("rbDefaultRepeatability")

        return vars

# 2. List of...

class WRoomBookingRoomList( WTemplated ):

    def __init__( self, rh, standalone = False, onlyMy = False ):
        self._rh = rh
        self._standalone = standalone
        self._title = None
        self._onlyMy = onlyMy
        try: self._title = self._rh._title;
        except: pass

    def getVars( self ):
        vars=WTemplated.getVars( self )

        vars["rooms"] = self._rh._rooms
        vars["mapAvailable"] = self._rh._mapAvailable
        vars["standalone"] = self._standalone
        vars["title"] = self._title
        if self._onlyMy:
            vars["noResultsMsg"] = _("You are not the owner of any room")
        else :
            vars["noResultsMsg"] = _("There are no rooms with this search criteria")

        if self._standalone:
            vars["detailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            vars["bookingFormUH"] = urlHandlers.UHRoomBookingBookingForm
        else:
            vars["conference"] = self._rh._conf
            vars["detailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            vars["bookingFormUH"] = urlHandlers.UHConfModifRoomBookingBookingForm

        return vars

class WRoomBookingList( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._standalone = standalone
        self._rh = rh
        if not standalone:
            self._conf = rh._conf

    def getVars( self ):
        vars=WTemplated.getVars( self )

        vars["reservations"] = self._rh._resvs
        vars["standalone"] = self._standalone
        dm = datetime.now() - timedelta( 1 )
        vars["yesterday"] = dm #datetime( dm.year, dm.month, dm.day, 0, 0, 1 )

        if self._standalone:
            vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            vars["conference"] = self._conf
            vars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails

        return vars


class WRoomBookingBookingList(WTemplated):  # Standalone version

    def __init__(self, rh):
        self._rh = rh
        self._candResvs = rh._candResvs
        self._title = None
        try:
            self._title = self._rh._title
        except:
            pass

    def _isOn(self, boolVal):
        if boolVal:
            return "on"
        else:
            return ""

    def getVars(self):
        vars = WTemplated.getVars(self)
        rh = self._rh
        candResvs = self._candResvs

        vars["finishDate"] = rh._finishDate
        vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        vars["withPhoto"] = False
        vars["title"] = self._title
        vars["search"] = rh._search
        vars["showRejectAllButton"] = rh._showRejectAllButton
        vars["prebookingsRejected"] = rh._prebookingsRejected
        vars["subtitle"] = rh._subtitle
        vars["description"] = rh._description
        yesterday = datetime.now() - timedelta(1)
        vars["yesterday"] = yesterday  # datetime( dm.year, dm.month, dm.day, 0, 0, 1 )
        ed = None
        sd = rh._resvEx.startDT.date()
        if rh._resvEx.endDT:
            ed = rh._resvEx.endDT.date()
        else:
            ed = sd + timedelta(7)

        if rh._ofMyRooms and not rh._rooms:
            rh._resvs = []
        # autoCriteria - dates are calculated based on the next reservation
        elif rh._autoCriteria and not rh._resvs:
            # reservation not found for the next 7 days, change search period to 30 days
            ed = sd + timedelta(30)
            rh._resvEx.startDT = datetime(sd.year, sd.month, sd.day, 0, 0)
            rh._resvEx.endDT = datetime(ed.year, ed.month, ed.day, 23, 59)
            rh._resvs = ReservationBase.getReservations(resvExample=rh._resvEx, rooms=rh._rooms)
            firstResv = ReservationBase.findSoonest(rh._resvs, afterDT=yesterday)
            if firstResv:
                # extend period to latest reservation date if necessarily
                sd = firstResv.startDT
                ed = sd + timedelta(7)

        # set the calendar dates as calculated
        calendarStartDT = datetime(sd.year, sd.month, sd.day, 0, 0)
        calendarEndDT = datetime(ed.year, ed.month, ed.day, 23, 59)

        from MaKaC.common.utils import formatDate

        if calendarStartDT.date() == calendarEndDT.date():
            vars["periodName"] = "day"
        else:
            vars["periodName"] = "period"
        vars["startD"] = formatDate(calendarStartDT)
        vars["endD"] = formatDate(calendarEndDT)

        # Data for previous/next URLs (it's about periods, not paging)
        newParams4Previous = rh._reqParams.copy()
        newParams4Next = rh._reqParams.copy()
        if rh._reqParams.has_key('autoCriteria'):
            del newParams4Previous['autoCriteria']
            del newParams4Next['autoCriteria']
        if rh._reqParams.has_key('day'):
            del newParams4Previous['day']
            del newParams4Next['day']

        startD = calendarStartDT.date()
        endD = calendarEndDT.date()

        if endD != startD:
            period = endD - startD

            prevStartD = startD - period - timedelta(1)
            prevEndD = startD - timedelta(1)

            nextStartD = endD + timedelta(1)
            nextEndD = endD + period + timedelta(1)
        else:
            prevStartD = prevEndD = startD - timedelta(1)
            nextStartD = nextEndD = endD + timedelta(1)

        newParams4Previous['sDay'] = prevStartD.day
        newParams4Previous['sMonth'] = prevStartD.month
        newParams4Previous['sYear'] = prevStartD.year
        newParams4Previous['eDay'] = prevEndD.day
        newParams4Previous['eMonth'] = prevEndD.month
        newParams4Previous['eYear'] = prevEndD.year

        newParams4Next['sDay'] = nextStartD.day
        newParams4Next['sMonth'] = nextStartD.month
        newParams4Next['sYear'] = nextStartD.year
        newParams4Next['eDay'] = nextEndD.day
        newParams4Next['eMonth'] = nextEndD.month
        newParams4Next['eYear'] = nextEndD.year

        vars["attributes"] = {}
        vars["withPrevNext"] = True
        vars["prevURL"] = urlHandlers.UHRoomBookingBookingList.getURL(newParams=newParams4Previous)
        vars["nextURL"] = urlHandlers.UHRoomBookingBookingList.getURL(newParams=newParams4Next)

        vars['overload'] = self._rh._overload
        vars['dayLimit'] = self._rh._dayLimit
        vars['newBooking'] = self._rh._newBooking

        # empty days are shown for "User bookings" and "User pre-bookings"
        # and for the calendar as well
        # but not for the booking search
        # showEmptyDays = ( self._rh._ofMyRooms or \
        #                  (not self._rh._ofMyRooms and not self._rh._onlyMy) ) and \
        #                  not self._rh._search

        showEmptyDays = showEmptyRooms = not self._rh._newBooking

        # Calendar related stuff ==========

        bars = []
        collisionsOfResvs = []

        # Bars: Candidate reservation
        collisions = []  # only with confirmed resvs
        for candResv in candResvs:
            periodsOfCandResv = candResv.splitToPeriods()
            for b in candResv.getBlockedDates():
                bStartDT = datetime.combine(b, datetime.min.time())
                bEndDT = datetime.combine(b, datetime.max.time())
                bars.append(Bar(Collision((bStartDT, bEndDT), candResv), Bar.BLOCKED))
            for p in periodsOfCandResv:
                bars.append(Bar(Collision((p.startDT, p.endDT), candResv), Bar.CANDIDATE))

            # Bars: Conflicts all vs candidate
            candResvIsConfirmed = candResv.isConfirmed
            candResv.isConfirmed = None

            candResv.startDT, calendarStartDT = calendarStartDT, candResv.startDT
            candResv.endDT, calendarEndDT = calendarEndDT, candResv.endDT

            allCollisions = candResv.getCollisions()

            candResv.startDT, calendarStartDT = calendarStartDT, candResv.startDT
            candResv.endDT, calendarEndDT = calendarEndDT, candResv.endDT

            candResv.isConfirmed = candResvIsConfirmed
            if candResv.id:
                # Exclude candidate vs self pseudo-conflicts (Booking modification)
                allCollisions = filter(lambda c: c.withReservation.id != candResv.id, allCollisions)
            for c in allCollisions:
                if c.withReservation.isConfirmed:
                    bars.append(Bar(c, Bar.UNAVAILABLE))
                else:
                    bars.append(Bar(c, Bar.PREBOOKED))

            allCollisions = candResv.getCollisions()

            for c in allCollisions:
                if c.withReservation.isConfirmed:
                    bars.append(Bar(c, Bar.CONFLICT))
                    collisions.append(c)
                else:
                    bars.append(Bar(c, Bar.PRECONFLICT))

            if not candResv.isRejected and not candResv.isCancelled:
                vars["thereAreConflicts"] = len(collisions) > 0
            else:
                vars["thereAreConflicts"] = False
            vars["conflictsNumber"] = len(collisions)

        # there's at least one reservation
        if len(rh._resvs) > 0:

            # Prepare the list of Collisions
            # (collision is just a helper object, it's not the best notion here)

            for r in rh._resvs:
                for p in r.splitToPeriods(endDT=calendarEndDT, startDT=calendarStartDT):
                    if p.startDT >= calendarStartDT and p.endDT <= calendarEndDT:
                        collisionsOfResvs.append(Collision((p.startDT, p.endDT), r))

            # Translate collisions to Bars
            for c in collisionsOfResvs:
                if c.withReservation.isConfirmed:
                    bars.append(Bar(c, Bar.UNAVAILABLE))
                else:
                    bars.append(Bar(c, Bar.PREBOOKED))

            bars = barsList2Dictionary(bars)
            bars = addOverlappingPrebookings(bars)
            bars = sortBarsByImportance(bars, calendarStartDT, calendarEndDT)

            rooms = set(r.room for r in rh._resvs)

            #CrossLocationQueries.getRooms( location = self.location )
            if not self._rh._onlyMy:
                rooms = self._rh._rooms

            bars = introduceRooms(rooms, bars, calendarStartDT, calendarEndDT, showEmptyDays=showEmptyDays, showEmptyRooms=showEmptyRooms, user=rh._aw.getUser())

            vars["Bar"] = Bar

            self.__sortUsingCriterion(rh._order, collisionsOfResvs)

        # we want to display every room, with or without reservation
        else:
            # initialize collision bars
            bars = barsList2Dictionary(bars)
            bars = sortBarsByImportance(bars, calendarStartDT, calendarEndDT)

            # insert rooms
            if not self._rh._onlyMy:
                    rooms = self._rh._rooms
            else:
                    rooms = []

            bars = introduceRooms(rooms, bars, calendarStartDT, calendarEndDT, showEmptyDays=showEmptyDays, showEmptyRooms=showEmptyRooms, user=rh._aw.getUser())

        fossilizedBars = {}
        for key in bars:
            cachedDayBars = self._rh._dayBars.get(str(key))
            if not cachedDayBars:
                fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
            else:
                fossilizedBars[str(key)] = cachedDayBars
        if self._rh._updateCache:
            self._rh._cache.set_multi(fossilizedBars, 7200)
        resvIds = set()
        for dayBars in fossilizedBars.itervalues():
            for roomBars in dayBars:
                for bar in roomBars['bars']:
                    resvIds.add(bar['forReservation']['id'])
        numResvs = len(resvIds)
        vars["barsFossil"] = fossilizedBars
        vars["numResvs"] = numResvs
        vars["dayAttrs"] = fossilize({})
        vars["showEmptyRooms"] = showEmptyRooms
        vars["manyRooms"] = not self._rh._rooms or len(self._rh._rooms) > 1
        vars["calendarParams"] = {}
        if self._title and rh._ofMyRooms:
            vars["calendarParams"]["ofMyRooms"] = "on"
        elif rh._onlyMy:
            vars["calendarParams"]["onlyMy"] = "on"
        elif rh._allRooms:
            vars["calendarParams"]["roomGUID"] = "allRooms"
        else:
            for room in rh._roomGUIDs:
                vars["calendarParams"]["roomGUID"] = room
        if rh._onlyPrebookings:
            vars["calendarParams"]["onlyPrebookings"] = "on"
        if rh._onlyBookings:
            vars["calendarParams"]["onlyBookings"] = "on"
        vars["repeatability"] = rh._repeatability
        vars["flexibleDatesRange"] = rh._flexibleDatesRange
        vars["calendarFormUrl"] = urlHandlers.UHRoomBookingBookingList.getURL()
        vars["numRooms"] = len(rh._rooms) if rh._rooms else 0
        vars["ofMyRooms"] = rh._ofMyRooms

        return vars

    def __sortUsingCriterion(self, order, uresvs):

        if order == "" or order == "room":
            # standard sorting order (by room, and then date)
            uresvs.sort(lambda r1, r2: cmp(r1.withReservation.room.name, r2.withReservation.room.name))
        else:
            if order == 'date':
                uresvs.sort(lambda r1, r2: cmp(r1.startDT, r2.startDT))
            elif order == 'reason':
                uresvs.sort(lambda r1, r2: cmp(r1.withReservation.reason.lower(), r2.withReservation.reason.lower()))
            elif order == 'for':
                uresvs.sort(lambda r1, r2: cmp(r1.withReservation.bookedForName.lower(), r2.withReservation.bookedForName.lower()))
            elif order == 'hours':
                uresvs.sort(lambda r1, r2: cmp(r1.startDT.time(), r2.startDT.time()))


# 3. Details of...

def barsList2Dictionary(bars):
    """
    Converts:
    list of bars => dictionary of bars, key = datetime, value = list of bars
    """
    h = {}
    for bar in bars:
        d = bar.startDT.date()
        if h.has_key(d):
            h[d].append(bar)
        else:
            h[d] = [bar]
    return h


def addOverlappingPrebookings(bars):
    """
    Adds bars representing overlapping pre-bookings.
    Returns new bars dictionary.
    """

    # For each day
    for dt in bars.keys():
        dayBars = bars[dt]

        # For each (prebooked) bar i
        for i in xrange(0, len(dayBars)):
            bar = dayBars[i]
            if bar.type == Bar.PREBOOKED:

                # For each (prebooked) bar j
                for j in xrange(i+1, len(dayBars)):
                    collCand = dayBars[j]
                    if collCand.type == Bar.PREBOOKED:

                        # If there is an overlap, add PRECONCURRENT bar
                        over = overlap(bar.startDT, bar.endDT, collCand.startDT, collCand.endDT)
                        if over and bar.forReservation.room == collCand.forReservation.room and collCand.forReservation != bar.forReservation:
                            collision = Collision(over, collCand.forReservation)
                            dayBars.append(Bar(collision, Bar.PRECONCURRENT))

        bars[dt] = dayBars # With added concurrent prebooking bars

    return bars


def sortBarsByImportance(bars, calendarStartDT, calendarEndDT):
    """
    Moves conflict bars to the end of the list,
    so they will be drawn last and therefore be visible.

    Returns sorted bars.
    """
    for dt in bars.keys():
        dayBars = bars[dt]
        dayBars.sort()
        bars[dt] = dayBars

    for day in iterdays(calendarStartDT, calendarEndDT):
        if not bars.has_key( day.date() ):
           bars[day.date()] = []

    return bars

def getRoomBarsList( rooms ):
    roomBarsList = []
    if rooms is None:
        rooms=[]
    for room in rooms:
        roomBarsList.append( RoomBars( room, [] ) )
    roomBarsList.sort()
    return roomBarsList

def introduceRooms( rooms, dayBarsDic, calendarStartDT, calendarEndDT, showEmptyDays=True, showEmptyRooms=True, user = None ):
    # Input:
    # dayBarsDic is a dictionary date => [bar1, bar2, bar3, ...]
    #
    # Output:
    # newDayBarsDic is a dictionary date => [roomBars1, roomBars2, roomBars3, ...],
    # where roomBars is object JSON:{ room: RoomBase, bars: [bar1, bar2, bar3, ...] }
    #import copy
    #cleanRoomBarsList = getRoomBarsList( rooms )
    newDayBarsDic = {}
    from MaKaC.common.utils import formatDate
    for day in iterdays( calendarStartDT, calendarEndDT ):
        dayBars = dayBarsDic[day.date()]
        roomBarsDic = {}
        for bar in dayBars:
#            bar.canReject = False
#            bar.canReject = bar.forReservation.id is not None and bar.forReservation.canReject(user)
#            if bar.forReservation.repeatability != None:
#                bar.rejectURL = str(urlHandlers.UHRoomBookingRejectBookingOccurrence.getURL( bar.forReservation, formatDate(bar.startDT.date()) ))
#            else:
#                bar.rejectURL = str(urlHandlers.UHRoomBookingRejectBooking.getURL( bar.forReservation ))
            room = bar.forReservation.room
            if not roomBarsDic.has_key( room ):
                roomBarsDic[room] = []
            # Bars order should be preserved
            roomBarsDic[room].append( bar )

        if showEmptyRooms:
            dayRoomBarsList = getRoomBarsList( rooms ) #copy.copy( cleanRoomBarsList )

            for roomBar in dayRoomBarsList:
                roomBar.bars = roomBarsDic.get( roomBar.room, [] )
        else:
            dayRoomBarsList = []
            for room in roomBarsDic.keys():
                dayRoomBarsList.append(RoomBars(room,roomBarsDic[room]))

        if showEmptyDays or len(dayBars) > 0:
            newDayBarsDic[day.date()] = dayRoomBarsList

    return newDayBarsDic

def getDayAttrsForRoom(dayDT, room):
    attrs = {'tooltip': '', 'className': ''}
    roomBlocked = room.getBlockedDay(dayDT)
    if roomBlocked:
        block = roomBlocked.block
    if roomBlocked and block.canOverride(ContextManager.get('currentUser'), explicitOnly=True):
        attrs['className'] = "blocked_permitted"
        attrs['tooltip'] = _('Blocked by %s:\n%s\n\n<b>You are permitted to override the blocking.</b>') % (block.createdByUser.getFullName(), block.message)
    elif roomBlocked and roomBlocked.active is True:
        if block.canOverride(ContextManager.get('currentUser'), room):
            attrs['className'] = "blocked_override"
            attrs['tooltip'] = _('Blocked by %s:\n%s\n\n<b>You own this room or are an administrator and are thus permitted to override the blocking. Please use this privilege with care!</b>') % (block.createdByUser.getFullName(), block.message)
        else:
            attrs['className'] = "blocked"
            attrs['tooltip'] = _('Blocked by %s:\n%s') % (block.createdByUser.getFullName(), block.message)
    elif roomBlocked and roomBlocked.active is None:
        attrs['className'] = "preblocked"
        attrs['tooltip'] = _('Blocking requested by %s:\n%s\n\n<b>If this blocking is approved, any colliding bookings will be rejected!</b>') % (block.createdByUser.getFullName(), block.message)
    return attrs

class WRoomBookingRoomStats( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._standalone = standalone

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["room"] = self._rh._room
        vars["standalone"] = self._standalone
        vars["period"] = self._rh._period
        vars["kpiAverageOccupation"] = '{0:.02f}%'.format(self._rh._kpiAverageOccupation * 100)
        # Bookings
        vars["kbiTotalBookings"] = self._rh._totalBookings
        # Next 9 KPIs
        vars["stats"] = self._rh._booking_stats
        vars["statsURL"] = urlHandlers.UHRoomBookingRoomStats.getURL(self._rh._room)
        return vars


class WRoomBookingRoomDetails( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._standalone = standalone

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars["room"] = self._rh._room
        goodFactory = Location.parse(self._rh._room.locationName).factory
        attributes = goodFactory.getCustomAttributesManager().getAttributes(location=self._rh._room.locationName)
        wvars["attrs"] = {}
        for attribute in attributes:
            if not attribute.get("hidden", False) or self._rh._getUser().isAdmin():
                wvars["attrs"][attribute['name']] = self._rh._room.customAtts.get(attribute['name'], "")
                if attribute['name'] == 'notification email':
                    wvars["attrs"][attribute['name']] = wvars["attrs"][attribute['name']].replace(',', ', ')
        wvars["config"] = Config.getInstance()
        wvars["standalone"] = self._standalone
        wvars["actionSucceeded"] = self._rh._afterActionSucceeded
        wvars["deletionFailed"] = self._rh._afterDeletionFailed

        wvars["roomStatsUH"] = urlHandlers.UHRoomBookingRoomStats

        if self._standalone:
            wvars["bookingFormUH"] = urlHandlers.UHRoomBookingBookingForm
            wvars["modifyRoomUH"] = urlHandlers.UHRoomBookingRoomForm
            wvars["deleteRoomUH"] = urlHandlers.UHRoomBookingDeleteRoom
            wvars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            wvars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails
            wvars["conference"] = self._rh._conf
            wvars["bookingFormUH"] = urlHandlers.UHConfModifRoomBookingBookingForm
            wvars["modifyRoomUH"] = urlHandlers.UHRoomBookingRoomForm
            wvars["deleteRoomUH"] = urlHandlers.UHRoomBookingDeleteRoom

        # Calendar range: 3 months
        if self._rh._searchingStartDT and self._rh._searchingEndDT:
            sd = self._rh._searchingStartDT
            calendarStartDT = datetime( sd.year, sd.month, sd.day, 0, 0, 1 )
            ed = self._rh._searchingEndDT
            calendarEndDT = datetime( ed.year, ed.month, ed.day, 23, 59 )
        else:
            now = datetime.now()
            calendarStartDT = datetime( now.year, now.month, now.day, 0, 0, 1 )
            calendarEndDT = calendarStartDT + timedelta( 3 * 31, 50, 0, 0, 59, 23 )

        # Example resv. to ask for other reservations
        resvEx = CrossLocationFactory.newReservation( location = self._rh._room.locationName )
        resvEx.startDT = calendarStartDT
        resvEx.endDT = calendarEndDT
        resvEx.repeatability = RepeatabilityEnum.daily
        resvEx.room = self._rh._room
        resvEx.isConfirmed = None # to include not also confirmed

        # Bars: Existing reservations
        collisionsOfResvs = resvEx.getCollisions()

        bars = []
        for c in collisionsOfResvs:
            if c.withReservation.isConfirmed:
                bars.append( Bar( c, Bar.UNAVAILABLE ) )
            else:
                bars.append( Bar( c, Bar.PREBOOKED ) )

        bars = barsList2Dictionary( bars )
        bars = addOverlappingPrebookings( bars )
        bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )

        # Set owner for all
        if not self._standalone:
            for dt in bars.iterkeys():
                for bar in bars[dt]:
                    bar.forReservation.setOwner(self._rh._conf)

        wvars["calendarStartDT"] = calendarStartDT
        wvars["calendarEndDT"] = calendarEndDT
        bars = introduceRooms([self._rh._room], bars, calendarStartDT, calendarEndDT, user=self._rh._aw.getUser())
        fossilizedBars = {}
        for key in bars:
            fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
        wvars["barsFossil"] = fossilizedBars
        wvars["dayAttrs"] = fossilize(dict((day.strftime("%Y-%m-%d"), getDayAttrsForRoom(day, self._rh._room))
                                           for day in bars.iterkeys()))
        wvars["bars"] = bars
        wvars["iterdays"] = iterdays
        wvars["day_name"] = day_name
        wvars["Bar"] = Bar
        wvars["withConflicts"] = False
        wvars["currentUser"] = self._rh._aw.getUser()
        room_mapper = RoomMapperHolder().match({"placeName": self._rh._room.locationName}, exact=True)
        if room_mapper:
            wvars["show_on_map"] = room_mapper[0].getMapURL(self._rh._room.name)
        else:
            wvars["show_on_map"] = urlHandlers.UHRoomBookingMapOfRooms.getURL(roomID=self._rh._room.id)
        return wvars


class WRoomBookingDetails(WTemplated):

    def __init__(self, rh, conference=None):
        self._rh = rh
        self._resv = rh._resv
        self._conf = conference
        self._standalone = (conference is None)

    def getVars(self):
        wvars = WTemplated.getVars( self )
        wvars["standalone"] = self._standalone
        wvars["reservation"] = self._resv
        wvars["collisions"] = self._rh._collisions
        wvars["config"] = Config.getInstance()
        wvars["actionSucceeded"] = self._rh._afterActionSucceeded
        if self._rh._afterActionSucceeded:
            wvars["title"] = self._rh._title
            wvars["description"] = self._rh._description

        if self._standalone:
            wvars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            wvars["modifyBookingUH"] = urlHandlers.UHRoomBookingModifyBookingForm
            wvars["cloneURL"] = urlHandlers.UHRoomBookingCloneBooking.getURL(self._resv)
        else:
            wvars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            wvars["modifyBookingUH"] = urlHandlers.UHConfModifRoomBookingModifyBookingForm
            wvars["cloneURL"] = urlHandlers.UHConfModifRoomBookingCloneBooking.getURL(self._resv)

        wvars["isPreBooking"] = not self._resv.isConfirmed
        wvars["bookMessage"] = _("PRE-Booking") if wvars["isPreBooking"] else _("Booking")

        return wvars

# 4. Booking Form

class WRoomBookingBookingForm( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._candResv = rh._candResv
        self._standalone = standalone

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["standalone"] = self._standalone
        vars["config"] = Config.getInstance()

        if self._standalone:
            vars["conf"] = None
            vars["saveBookingUH"] = urlHandlers.UHRoomBookingSaveBooking
            vars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            vars["calendarPreviewUH"] = urlHandlers.UHRoomBookingBookingForm
            vars["bookingFormURL"] = urlHandlers.UHRoomBookingBookingForm
        else:
            vars["conf"] = self._rh._conf
            vars["saveBookingUH"] = urlHandlers.UHConfModifRoomBookingSaveBooking
            vars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            vars["calendarPreviewUH"] = urlHandlers.UHConfModifRoomBookingBookingForm
            vars["bookingFormURL"] = urlHandlers.UHConfModifRoomBookingBookingForm

        vars["candResv"] = self._candResv
        vars["startDT"] = self._candResv.startDT
        vars["endDT"] = self._candResv.endDT
        vars["startT"] = ''
        vars["endT"] = ''
        if any((self._candResv.startDT.hour, self._candResv.startDT.minute, self._candResv.endDT.hour,  self._candResv.endDT.minute)):
            vars["startT"] = '%02d:%02d' % (self._candResv.startDT.hour, self._candResv.startDT.minute )
            vars["endT"] = '%02d:%02d' % (self._candResv.endDT.hour, self._candResv.endDT.minute )

        vars["showErrors"] = self._rh._showErrors
        vars["errors"] = self._rh._errors
        vars["thereAreConflicts"] = self._rh._thereAreConflicts
        vars["skipConflicting"] = self._rh._skipConflicting

        if self._rh._formMode == FormMode.MODIF:
            vars["allowPast"] = "true"
        else:
            vars["allowPast"] = "false"
        vars["formMode"] = self._rh._formMode
        vars["FormMode"] = FormMode

        # [Book] or [PRE-Book] ?
        bookingMessage = "Book"
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook( user ) and not room.canBook( user ):
            bookingMessage = "PRE-Book"
        vars["bookingMessage"] = bookingMessage
        vars["user"] = user

        if self._rh._formMode != FormMode.MODIF:
            bText = bookingMessage
        else:
            bText = "Save"

        vars["roomBookingRoomCalendar"] = WRoomBookingRoomCalendar( self._rh, self._standalone, buttonText=bText).getHTML( {} )
        vars["rooms"] = self._rh._rooms
        vars["infoBookingMode"] = self._rh._infoBookingMode

        return vars

class WRoomBookingConfirmBooking( WRoomBookingBookingForm ):

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["candResv"] = self._candResv

        vars["standalone"] = self._standalone
        vars["formMode"] = self._rh._formMode
        vars["FormMode"] = FormMode
        vars["collisions"] = self._rh._collisions

        # If we are here, we are either in booking mode and trying to overwrite PRE-Bookings...
        bookingMessage = "Book"
        bookingMessageOther = "PRE-Book"
        vars["rejectOthers"] = True
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook( user ) and not room.canBook( user ):
            # ...or we are in PRE-booking mode and conflicting with another PRE-Booking
            bookingMessage = "PRE-Book"
            bookingMessageOther = "PRE-Book"
            vars["rejectOthers"] = False
        vars["bookingMessage"] = bookingMessage
        vars["bookingMessageOther"] = bookingMessageOther

        if self._standalone:
             vars["conf"] = None
             vars["saveBookingUH"] = urlHandlers.UHRoomBookingSaveBooking
             vars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
        else:
             vars["conf"] = self._rh._conf
             vars["saveBookingUH"] = urlHandlers.UHConfModifRoomBookingSaveBooking
             vars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
        return vars

class WRoomBookingRoomForm( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        candRoom = self._rh._candRoom
        goodFactory = Location.parse( candRoom.locationName ).factory

        vars["Location"] = Location
        vars["room"] = candRoom
        vars["largePhotoPath"] = None
        vars["smallPhotoPath"] = None
        vars["config"] = Config.getInstance()
        vars["possibleEquipment"] = goodFactory.getEquipmentManager().getPossibleEquipment( location = candRoom.locationName )

        vars["showErrors"] = self._rh._showErrors
        vars["errors"] = self._rh._errors

        vars["insert"] = ( candRoom.id == None )
        vars["attrs"] = goodFactory.getCustomAttributesManager().getAttributes( location = candRoom.locationName )
        resp = candRoom.getResponsible()
        if resp:
            vars["responsibleName"] = resp.getFullName()
        else:
            vars["responsibleName"] = ""

        nbd = candRoom.getNonBookableDates()
        if len(nbd) == 0:
            from MaKaC.plugins.RoomBooking.default.room import NonBookableDate
            nbd = [NonBookableDate(None, None)]
        vars["nonBookableDates"] = nbd

        nbp = candRoom.getDailyBookablePeriods()
        if len(nbp) == 0:
            from MaKaC.plugins.RoomBooking.default.room import DailyBookablePeriod
            nbp = [DailyBookablePeriod(None, None)]
        vars["dailyBookablePeriods"] = nbp

        return vars


class WRoomBookingRoomCalendar( WTemplated ):

    def __init__( self, rh, standalone = False, buttonText ='' ):
        self._rh = rh
        self._candResv = rh._candResv
        self._standalone = standalone
        self._buttonText = buttonText

    def getVars( self ):
        vars = WTemplated.getVars( self )

        candResv = self._candResv
        room = candResv.room

        if self._standalone:
            vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            vars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails

        # Calendar range
        now = datetime.now()
        if candResv != None: #.startDT != None and candResv.endDT != None:
            calendarStartDT = datetime( candResv.startDT.year, candResv.startDT.month, candResv.startDT.day, 0, 0, 1 )  # Potential performance problem
            calendarEndDT =  datetime( candResv.endDT.year, candResv.endDT.month, candResv.endDT.day, 23, 59 )     # with very long reservation periods
        else:
            calendarStartDT = datetime( now.year, now.month, now.day, 0, 0, 1 )
            calendarEndDT = calendarStartDT + timedelta( 3 * 31, 50, 0, 0, 59, 23 )

        # example resv. to ask for other reservations
        resvEx = CrossLocationFactory.newReservation( location = room.locationName )
        resvEx.startDT = calendarStartDT
        resvEx.endDT = calendarEndDT
        resvEx.repeatability = RepeatabilityEnum.daily
        resvEx.room = room
        resvEx.isConfirmed = None # To include both confirmed and not confirmed

        # Bars: Existing reservations
        collisionsOfResvs = resvEx.getCollisions()
        bars = []
        for c in collisionsOfResvs:
            if c.withReservation.isConfirmed:
                bars.append( Bar( c, Bar.UNAVAILABLE ) )
            else:
                bars.append( Bar( c, Bar.PREBOOKED ) )

        # Bars: Candidate reservation
        periodsOfCandResv = candResv.splitToPeriods()
        for p in periodsOfCandResv:
            bars.append( Bar( Collision( (p.startDT, p.endDT), candResv ), Bar.CANDIDATE  ) )

        # Bars: Conflicts all vs candidate
        candResvIsConfirmed = candResv.isConfirmed;
        candResv.isConfirmed = None
        allCollisions = candResv.getCollisions()
        candResv.isConfirmed = candResvIsConfirmed
        if candResv.id:
            # Exclude candidate vs self pseudo-conflicts (Booking modification)
            allCollisions = filter( lambda c: c.withReservation.id != candResv.id, allCollisions )
        collisions = [] # only with confirmed resvs
        for c in allCollisions:
            if c.withReservation.isConfirmed:
                bars.append( Bar( c, Bar.CONFLICT ) )
                collisions.append( c )
            else:
                bars.append( Bar( c, Bar.PRECONFLICT ) )

        if not candResv.isRejected and not candResv.isCancelled:
            vars["thereAreConflicts"] = len( collisions ) > 0
        else:
            vars["thereAreConflicts"] = False
        vars["conflictsNumber"] = len( collisions )

        bars = barsList2Dictionary( bars )
        bars = addOverlappingPrebookings( bars )
        bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )

        if not self._standalone:
            for dt in bars.iterkeys():
                for bar in bars[dt]:
                    bar.forReservation.setOwner( self._rh._conf )

        vars["blockConflicts"] = candResv.getBlockingConflictState(self._rh._aw.getUser())

        vars["calendarStartDT"] = calendarStartDT
        vars["calendarEndDT"] = calendarEndDT
        bars = introduceRooms( [room], bars, calendarStartDT, calendarEndDT, user = self._rh._aw.getUser() )
        fossilizedBars = {}
        for key in bars:
            fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
        vars["barsFossil"] = fossilizedBars
        vars["dayAttrs"] = fossilize(dict((day.strftime("%Y-%m-%d"), getDayAttrsForRoom(day, room)) for day in bars.iterkeys()))
        vars["bars"] = bars
        vars["iterdays"] = iterdays
        vars["day_name"] = day_name
        vars["Bar"] = Bar
        vars["room"] = room
        vars["buttonText"] = self._buttonText
        vars["currentUser"] = self._rh._aw.getUser()
        vars["withConflicts"] = True

        return vars


class WRoomBookingStatement( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars['title'] = self._rh._title
        vars['description'] = self._rh._description
        return vars

class WRoomBookingAdmin( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["Location"] = Location
        return vars


class WRoomBookingAdminLocation( WTemplated ):

    def __init__( self, rh, location ):
        self._rh = rh
        self._location = location

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["location"] = self._location
        vars["possibleEquipment"] = self._location.factory.getEquipmentManager().getPossibleEquipment(location = self._location.friendlyName)
        vars["AttsManager"] = self._location.factory.getCustomAttributesManager()

        # Rooms
        rooms = self._location.factory.newRoom().getRooms(location = self._location.friendlyName)
        rooms.sort()

        vars["Rooms"] = rooms

        rh = self._rh

        vars["withKPI"] = rh._withKPI

        if rh._withKPI:
            vars["kpiAverageOccupation"] = str( int( round( rh._kpiAverageOccupation * 100 ) ) ) + "%"

            vars["kpiTotalRooms"] = rh._kpiTotalRooms
            vars["kpiActiveRooms"] = rh._kpiActiveRooms
            vars["kpiReservableRooms"] = rh._kpiReservableRooms

            vars["kpiReservableCapacity"] = rh._kpiReservableCapacity
            vars["kpiReservableSurface"] = rh._kpiReservableSurface

            # Bookings

            vars["kbiTotalBookings"] = rh._totalBookings

            # Next 9 KPIs
            vars["stats"] = rh._booking_stats

        return vars

class WRoomBookingBlockingsForMyRooms(WTemplated):

    def __init__(self, roomBlocks):
        self._roomBlocks = roomBlocks

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars['roomBlocks'] = self._roomBlocks
        return vars

class WRoomBookingBlockingDetails(WTemplated):

    def __init__(self, block):
        self._block = block

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars['block'] = self._block
        return vars

class WRoomBookingBlockingList(WTemplated):

    def __init__(self, blocks):
        self._blocks = blocks

    def getVars(self):
        vars = WTemplated.getVars(self)

        self._blocks.sort(key=attrgetter('startDate'), reverse=True)
        vars['blocks'] = self._blocks
        return vars


class WRoomBookingBlockingForm(WTemplated):

    def __init__(self, block, errorMessage):
        self._block = block
        self._errorMessage = errorMessage

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['block'] = self._block
        wvars['errorMessage'] = self._errorMessage
        return wvars


class WUtils:
    """A interface for creating easily some HTML elements..."""

    def createImg(cls, imgId, imgInfo="", imgText="", **attributes):
        """ returns an HTML image with optional text on the right.
            Params:
                imgId -- ID of the picture (see /code/MaKaC/common/MaCaKConfig.py ->SystemIcons).
                ImgInfo -- optional information text about the link.
                imgText -- optional text which will be displayed on the right of the pic.
                attributes -- [dictionary] attributes for <img> (e.g. border="" name="" ...).
        """
        attr = utils.dictionaryToString(attributes)
        return """<img src="%s" alt="%s" %s /> %s"""%(Config.getInstance().getSystemIconURL(imgId),imgInfo,attr,imgText)
    createImg = classmethod(createImg)

    def createImgButton(cls, url, imgId, imgInfo="", imgText="", **attributes):
        """ returns an HTML image link with optional text on the right.
            Params:
                url -- link of target.
                imgId -- ID of the picture (see /code/MaKaC/common/MaCaKConfig.py ->SystemIcons).
                ImgInfo -- optional information text about the link.
                imgText -- optional text which will be displayed on the right of the pic.
                attributes -- [dictionary] attributes for <a> (e.g. onclick="" onchange="" ...).
        """
        attr = utils.dictionaryToString(attributes)
        return """<a href="%s" %s>
              <img src="%s" alt="%s" /> %s
          </a>"""%(url, attr, Config.getInstance().getSystemIconURL(imgId), imgInfo, imgText)
    createImgButton = classmethod(createImgButton)

    def createChangingImgButton(cls, url, imgID, imgOverId, imgInfo="", imgText="", **attributes):
        """ returns a changing HTML image link
            (i.e. the image changes depending on mouseOver/mouseOut)
            with optional text on the right.

            Params:
                url -- link of target.
                imgID -- ID of the basic picture (see /code/MaKaC/common/MaCaKConfig.py ->SystemIcons).
                imgOverId -- ID of the picture appearing with onMouseOver.
                ImgInfo -- optional information text about the link.
                imgText -- optional text which will be displayed on the right of the pic.
                attributes -- [dictionary] attributes for <a> (e.g. onclick="" onchange="" ...).
        """
        attr = utils.dictionaryToString(attributes)
        iconUrl = Config.getInstance().getSystemIconURL(imgID)
        iconOverUrl = Config.getInstance().getSystemIconURL(imgOverId)
        return """<a href="%s" %s>
              <img src="%s" alt="%s" onmouseover="javascript:this.src='%s'" onMouseOut="javascript:this.src='%s'"/> %s
          </a>"""%(url, attr, iconUrl, imgInfo, iconOverUrl, iconUrl, imgText)
    createChangingImgButton = classmethod(createChangingImgButton)

    def createTextarea(cls, content="", **attributes):
        """ returns an HTML textarea with optional text.
            Params:
                content -- optional text which will be displayed in the textarea.
                attributes -- [dictionary] attributes for <input> (e.g. name="" type="" ...).
        """
        #check
        if content==None: content=""
        #attributes to string...
        attr = utils.dictionaryToString(attributes)
        #return HTML string
        return """<textarea rows="5" cols="15" %s>%s</textarea>"""%(attr,content)
    createTextarea = classmethod(createTextarea)

    def createInput(cls, text="", **attributes):
        """ returns an HTML input with optional text.
            Params:
                text -- optional text which will be displayed on the right of the input.
                attributes -- [dictionary] attributes for <input> (e.g. name="" type="" ...).
        """
        #check
        if text==None: text=""
        #attributes to string...
        attr = utils.dictionaryToString(attributes)
        #return HTML string
        return """<input %s/>%s"""%(attr,text)
    createInput = classmethod(createInput)

    def createSelect(cls, emptyOption, options, selected="", **attributes):
        """ returns an HTML select field.
            Params:
                emptyOption -- [bool] if True, add a selectionable empty option in the select.
                options -- list of the options.
                selected -- (optional) the selected option.
                attributes -- [dictionary] attributes for <select> (e.g. name="" onchange="" ...).
        """
        #attributes to string...
        attr = utils.dictionaryToString(attributes)
        #with empty option?
        if emptyOption==True:
            optionsHTML="<option></option>"
        else:
            optionsHTML=""
        #treating options...
        for option in options:
            if option!=None and option!="":
                if str(option)==str(selected):
                    optionsHTML += """<option selected>%s</option>"""%(option)
                else:
                    optionsHTML += "<option>%s</option>"%(option)
        return """<select %s>%s</select>"""%(attr,optionsHTML)
    createSelect = classmethod(createSelect)

    def appendNewLine(cls, htmlContent):
        """ appends a new line <br/> to the given html element.
            Params:
                htmlContent -- [str] html element
        """
        return str(htmlContent) + "<br/>"
    appendNewLine = classmethod(appendNewLine)

class WBeautifulHTMLList(WTemplated):

    def __init__(self, listObject, classNames, level):
        """ classNames: a dictionary such as {'UlClassName' : 'optionList'}. See the getVars for more class names.
        """
        WTemplated.__init__(self)
        self.__listObject = listObject
        self.__classNames = classNames
        self.__level = level

    def getVars(self):
        vars = WTemplated.getVars( self )
        vars["ListObject"] = self.__listObject
        vars["UlClassName"] = self.__classNames.get("UlClassName", "")
        vars["LiClassName"] = self.__classNames.get("LiClassName", "")
        vars["DivClassName"] = self.__classNames.get("DivClassName", "")
        vars["Level"] = self.__level
        return vars

class WBeautifulHTMLDict(WTemplated):

    def __init__(self, dictObject, classNames, level):
        """ classNames: a dictionary such as {'UlClassName' : 'optionList'}. See the getVars for more class names.
        """
        WTemplated.__init__(self)
        self.__dictObject = dictObject
        self.__classNames = classNames
        self.__level = level

    def getVars(self):
        vars = WTemplated.getVars( self )
        vars["DictObject"] = self.__dictObject
        vars["UlClassName"] = self.__classNames.get("UlClassName", "")
        vars["LiClassName"] = self.__classNames.get("LiClassName", "")
        vars["DivClassName"] = self.__classNames.get("DivClassName", "")
        vars["KeyClassName"] = self.__classNames.get("KeyClassName", "")
        vars["Level"] = self.__level
        return vars


class WFilterCriteria(WTemplated):
    """
    Draws the options for a filter criteria object
    This means rendering the actual table that contains
    all the HTML for the several criteria
    """

    def __init__(self, options, filterCrit, extraInfo=""):
        WTemplated.__init__(self, tpl_name = "FilterCriteria")
        self._filterCrit = filterCrit
        self._options = options
        self._extraInfo = extraInfo

    def _drawFieldOptions(self, formName, form):
        raise Exception("Method WFilterCriteria._drawFieldOptions must be overwritten")

    def getVars(self):

        vars = WTemplated.getVars( self )

        vars["extra"] = self._extraInfo

        vars["content"] =  list((name, self._drawFieldOptions(name, form))
                                for (name, form) in self._options)
        return vars

class WDateField(WTemplated):

    def __init__(self, name, date, format, isDisabled=False, isMandatory=False):
        self._withTime = format.find('%H') >= 0
        self._name = name
        self._format = format
        self._isMandatory = isMandatory
        self._date = date
        self._isDisabled = isDisabled

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars['name'] = self._name
        vars['date'] = self._date
        if self._date:
            vars['dateDisplay'] = datetime.strftime(self._date, self._format)
        else:
            vars['dateDisplay'] = ''
        vars['isDisabled'] = self._isDisabled
        vars['withTime'] = self._withTime
        vars['isMandatory'] = self._isMandatory
        vars['format'] = self._format
        return vars
