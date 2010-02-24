# -*- coding: utf-8 -*-
##
## $Id: wcomponents.py,v 1.340 2009/06/17 13:52:52 eragners Exp $
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

from MaKaC.plugins.base import PluginsHolder
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

import os,types,string
from xml.sax.saxutils import escape, quoteattr
from copy import copy
from datetime import timedelta,datetime, date
import exceptions
from MaKaC.common.db import DBMgr
import MaKaC.conference as conference
import MaKaC.user as user
import MaKaC.schedule as schedule
import MaKaC.common.info as info
import MaKaC.domain as domain
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.common.Configuration as Configuration
from MaKaC import webcast

from MaKaC.accessControl import AdminList
from MaKaC.errors import UserError
from MaKaC.common.url import URL
from MaKaC.common import Config
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.conference import Conference

from MaKaC.webinterface.common.timezones import TimezoneRegistry, DisplayTimezoneRegistry
import MaKaC.webinterface.common.timezones as convertTime
from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc
from MaKaC.webinterface.common import contribFilters as contribFilters
from MaKaC.common import filters, utils
from MaKaC.errors import MaKaCError
import MaKaC.webinterface.displayMgr as displayMgr
from MaKaC.common.TemplateExec import TemplateExec
from MaKaC.common.ContextHelp import ContextHelp
from MaKaC.rb_tools import FormMode, overlap

from libxml2 import parserError

from MaKaC.i18n import _
from MaKaC.i18n import langList

from MaKaC.common.TemplateExec import truncateTitle


class WTemplated:
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

    def __init__( self, tpl_name = None):
        if tpl_name != None:
            self.tplId = tpl_name

        #if ( '_rh' in ','.join( dir( self ) ) ):
        from MaKaC.webinterface.rh.base import RH
        self._rh = RH._currentRH

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
        dir = cfg.getTPLDir()
        file = cfg.getTPLFile( self.tplId )

        if file == "":
            file = self._getSpecificTPL(dir,self.tplId)
        self.tplFile = os.path.join(dir, file)

        hfile = self._getSpecificTPL(os.path.join(dir,'chelp'),
                                              self.tplId,
                                              extension='wohl')

        self.helpFile = os.path.join(dir,'chelp',hfile)


    def getVars( self ):
        """Returns a dictionary containing the TPL variables that will
            be passed at the TPL formating time. For this class, it will
            return the configuration user defined variables.
           Classes inheriting from this one will have to take care of adding
            their variables to the ones returned by this method.
        """
        from MaKaC.webinterface.rh.base import RH
        self._rh = RH._currentRH

        cfg = Configuration.Config.getInstance()
        vars = cfg.getTPLVars()

        for paramName in self.__params:
            vars[ paramName ] = self.__params[ paramName ]
        if len(vars.get("errorMsg", [])) > 0 :
            vars["errorMsg"] = WErrorMessage().getHTML(vars)
        else:
            vars["errorMsg"] = ""

        if len(vars.get("infoMsg", [])) > 0 :
            vars["infoMsg"] = WInfoMessage().getHTML(vars)
        else :
            vars["infoMsg"] = ""

        return vars

    def getHTML( self, params=None ):
        """Returns the HTML resulting of formating the text contained in
            the corresponding TPL file with the variables returned by the
            getVars method.
            Params:
                params -- additional paramters received from the caller
        """
        from MaKaC.webinterface.rh.base import RH
        self._rh = RH._currentRH
        if self.tplId == None:
            self.tplId = self.__class__.__name__[1:]
        self._setTPLFile()
        self.__params = {}
        if params != None:
            self.__params = params
        try:
            fh = open( self.tplFile, "r")
            text = fh.read()
            fh.close()
        except Exception, e:
            raise MaKaCError( _("Could not open template: %s")%self.tplFile, _("Template"))

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
        vars['self'] = self

        tempHTML = TemplateExec.executeTemplate( text, vars, self.tplId )

        if helpText == None:
            return tempHTML
        else:
            try:
                return ContextHelp().merge(self.tplId, tempHTML, helpText)
            except parserError, e:
                if tempHTML.strip() == '':
                    raise MaKaCError(_("Template " + str(self.tplId) + " produced empty output, and it has a .wohl file. Error: " + str(e)))
                else:
                    raise e


    def htmlText(param):
        if param:
            return escape(param)
        #return "&nbsp;"
        return ""
    htmlText = staticmethod( htmlText )

    def textToHTML(param):
        if param != "":
            if param.lower().find("<br>") == -1 and param.lower().find("<p>") == -1 and param.lower().find("<li>") == -1 and param.lower().find("<table") == -1:
                param=param.replace("\r\n", "<br>")
                param=param.replace("\n","<br>")
            return param
        return "&nbsp;"
    textToHTML = staticmethod( textToHTML )

    def _escapeChars(self, text):
        return text.replace('%','%%')

class WHTMLHeader(WTemplated):



    def __init__(self, tpl_name = None):
        WTemplated.__init__(self)

    def getVars( self ):
        vars = WTemplated.getVars( self )

        if DBMgr.getInstance().isConnected():
            vars['stylesheet'] = Config.getInstance().getCssStylesheetName()
        else:
            vars['stylesheet'] = 'Default.css'
        return vars


class WHeader(WTemplated):
    """Templating web component for generating a common HTML header for
        the web interface.
    """
    def __init__(self, aw, locTZ="", isFrontPage=False, currentCategory=None, tpl_name=None):
        WTemplated.__init__(self, tpl_name=tpl_name)
        self._currentuser = aw.getUser()
        self._locTZ = locTZ
        self._aw = aw
        self.__isFrontPage = isFrontPage
        self.__currentCategory = currentCategory

    """
        Returns the current active timezone.
    """
    def _getActiveTimezone(self):
        if self._aw.getSession():
            tz = self._aw.getSession().getVar("ActiveTimezone")
        else:
            tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()

        return tz

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

    def getVars( self ):
        vars = WTemplated.getVars( self )
        #urlHandlers.UHUserDetails.getURL(self._currentuser)
        vars["logMeAs"] = ""
        # TODO: Remove this after CRBS headers are fixed!
        if self._currentuser:
            vars["userInfo"] = """<font size="-1"><a class="topbar" href="%s" target="_blank">%s</a> - <a href="%s">logout</a></font>"""%(urlHandlers.UHUserDetails.getURL(self._currentuser), self._currentuser.getFullName(), vars["logoutURL"])
            vars["userDetails"] = """class="topbar" href="%s" target="_blank\""""%urlHandlers.UHUserDetails.getURL(self._currentuser)

            if self._currentuser.isAdmin():
                vars["logMeAs"] = vars["loginAsURL"]
        else:
            vars["userInfo"] = """<a href="%s">login</a>"""%(vars["loginURL"])
            vars["userDetails"] = ""
        # *****************

        vars["currentUser"] = self._currentuser

        imgLogo=Configuration.Config.getInstance().getSystemIconURL( "logoIndico" )
        imgLogin=Configuration.Config.getInstance().getSystemIconURL( "login" )
##
## TOCHECK: We do not need this anymore since we use the flaog _ishttps in the clase RHSignIn
##
#        if Configuration.Config.getInstance().getLoginURL().startswith("https"):
#
#            # Set proper PROTOCOL for images requested via SSL
#            imgLogo=imgLogo.replace("http://", "https://")
#            imgLogin=imgLogin.replace("http://", "https://")
#
#            # Set proper PORT for images requested via SSL
#            imgLogo = urlHandlers.setSSLPort( imgLogo )
#            imgLogin = urlHandlers.setSSLPort( imgLogin )
#
        vars["imgLogo"] = imgLogo
        vars["imgLogin"] = imgLogin
        vars["isFrontPage"] = self.__isFrontPage
        vars["currentCategory"] = self.__currentCategory

        if self._aw.getSession():
            selLang = self._aw.getSession().getLang()
        else:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            selLang = minfo.getLang()

        #language list related
        languages = {}
        vars["SelectedLanguageName"] = "Unknown Language";
        for lang in langList():
            if selLang.lower() == lang[0].lower():
                vars["SelectedLanguageName"] = lang[1];
            languages[lang[0]] = lang[1]
        vars["Languages"] = languages

        vars["SelectedLanguage"] = selLang;

        vars["ActiveTimezone"] = self._getActiveTimezone();
        """
            Get the timezone for displaying on top of the page.
            1. If the user has "LOCAL" timezone then show the timezone
            of the event/category. If that's not possible just show the
            standard timezone.
            2. If the user has a custom timezone display that one.
        """
        vars["ActiveTimezoneDisplay"] = self._getTimezoneDisplay(vars["ActiveTimezone"])

        if DBMgr.getInstance().isConnected():
            vars["title"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTitle()
            vars["organization"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getOrganisation()
        else:
            vars["title"] = "Indico"
            vars["organization"] = ""


        # Search box, in case search is active
        if Config.getInstance().getIndicoSearchServer() != '' :
            categId = 0
            if self.__currentCategory:
                categId = self.__currentCategory.getId()
            vars['searchBox'] = WCategorySearchBox(categId=categId).getHTML()
        else:
            vars['searchBox'] = ""

        # Check if room booking module is active
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars['roomBooking'] = minfo.getRoomBookingModuleActive()

        #Build a list of items for the administration menu
        adminList = AdminList.getInstance()
        adminItemList = []
        if self._currentuser:
            if self._currentuser.isAdmin() or not adminList.getList():
                adminItemList.append({'url': urlHandlers.UHAdminArea.getURL(), 'text': _("Server admin")})
            if PluginsHolder().hasPluginType("Collaboration"):
                from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin, RCCollaborationPluginAdmin
                if (self._currentuser.isAdmin() or RCCollaborationAdmin.hasRights(user = self._currentuser) or RCCollaborationPluginAdmin.hasRights(user = self._currentuser, plugins = "any")) and CollaborationTools.anyPluginsAreActive():
                    adminItemList.append({'url': urlHandlers.UHAdminCollaboration.getURL(), 'text': _("Video Services Overview")})
            if webcast.HelperWebcastManager.getWebcastManagerInstance().isManager(self._currentuser):
                adminItemList.append({'url': urlHandlers.UHWebcast.getURL(), 'text': _("Webcast Admin")})


        vars["adminItemList"] = adminItemList

        return vars


class WStaticWebHeader( WTemplated ):
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

class WConferenceHeader( WHeader ):
    """Templating web component for generating the HTML header for
        the conferences' web interface.
    """

    def __init__(self, aw, navDrawer, conf):
        self._conf = conf
        self._aw = aw
        WHeader.__init__(self, self._aw, navDrawer, tpl_name='EventHeader')
        tzUtil = DisplayTZ(self._aw,self._conf)
        self._locTZ = tzUtil.getDisplayTZ()

    def getVars( self ):
        vars = WHeader.getVars( self )
        vars["categurl"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])

        vars["conf"] = self._conf;

        vars["imgLogo"] = Configuration.Config.getInstance().getSystemIconURL( "miniLogo" )
        vars["MaKaCHomeURL"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])

        #moved here from WHeader in order to be able to use DisplayTZ with self._conf (in some pages WHeader has no self._conf).
        #TODO: Is this needed?
        #vars["Timezones"] = Config.getInstance().getTimezoneList()


#        if self._conf.getModifKey() != '':
#            url = urlHandlers.UHConfEnterModifKey.getURL(self._conf)
#            url.addParam("redirectURL",urlHandlers.UHConferenceDisplay.getURL(self._conf))
#            vars["confModif"] = """<a href=%s><img src=%s valign="middle"></a>"""%(quoteattr(str(url)), quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "modify" ))))
#        else:
#            vars["confModif"] = ""

        # Default values to avoid NameError while executing the template
        vars["viewoptions"] = []
        vars["SelectedStyle"] = ""
        vars["pdfURL"] = ""
        vars["displayURL"] = ""

        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = False
        vars["showMoreButton"] = True
        vars["showExportToICal"] = True
        vars["showExportToPDF"] = False
        vars["showDLMaterial"] = False
        vars["showLayout"] = False

        vars["usingModifKey"]=False
        if self._conf.canKeyModify(self._aw):
            vars["usingModifKey"]=True
        return vars

class WMenuConferenceHeader( WConferenceHeader ):
    """Templating web component for generating the HTML header for
        the conferences' web interface with a menu
    """
    def __init__(self, aw, navDrawer, conf, modifKey=False):
        self._conf = conf
        self._modifKey=modifKey
        self._aw=aw
        WConferenceHeader.__init__(self, self._aw, navDrawer, conf)

    def getVars( self ):
        vars = WConferenceHeader.getVars( self )
        vars["categurl"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        url = urlHandlers.UHConfEnterModifKey.getURL(self._conf)
        url.addParam("redirectURL",urlHandlers.UHConferenceOtherViews.getURL(self._conf))
        vars["confModif"] =  _("""<a href=%s> _("manage")</a>""")%quoteattr(str(url))
        if self._conf.canKeyModify(self._aw):
            url = urlHandlers.UHConfCloseModifKey.getURL(self._conf)
            url.addParam("redirectURL",urlHandlers.UHConferenceOtherViews.getURL(self._conf))
            vars["confModif"] = _("""<a href=%s>_("exit manage")</a>""")%quoteattr(str(url))
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        stylesheets = styleMgr.getStylesheetListForEventType(vars["type"])

        # View Menu
        viewoptions = []
        if len(stylesheets) != 0:
            stylesheets.sort()
            for stylesheet in stylesheets:
                viewoptions.append({"id": styleMgr.getStylesheetName(stylesheet), "name": stylesheet})

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
            dates = [ _(""" <select name="showDate" onChange="document.forms[0].submit();" style="font-size:8pt;"><option value="all" %s>- -  _("all days") - -</option> """)%selected]
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
            sessions = [ _(""" <select name="showSession" onChange="document.forms[0].submit();" style="font-size:8pt;"><option value="all" %s>- -  _("all sessions") - -</option> """)%selected]
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

        if self._conf.getType() == "meeting" and self._conf.getParticipation().isAllowedForApplying() and self._conf.getStartDate() > nowutc():
            vars["applyForParticipation"] = _("""<a href="%s">_("Apply for participation")</a>""")%urlHandlers.UHConfParticipantsNewPending.getURL(self._conf)
        else :
            vars["applyForParticipation"] = ""
        evaluation = self._conf.getEvaluation()
        if self._conf.hasEnabledSection("evaluation") and evaluation.isVisible() and evaluation.inEvaluationPeriod() and evaluation.getNbOfQuestions()>0 :
            vars["evaluation"] =  _("""<a href="%s"> _("Evaluation")</a>""")%urlHandlers.UHConfEvaluationDisplay.getURL(self._conf)
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

        if Config.getInstance().getIndicoSearchServer() != '' :
            vars["searchBox"] = WMicroSearchBox(self._conf.getId()).getHTML()
            vars["searchURL"] = quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "search" )))
        else:
            vars["searchBox"] = ""

        return vars

class WMenuMeetingHeader( WConferenceHeader ):
    """Templating web component for generating the HTML header for
        the meetings web interface with a menu
    """
    def __init__(self, aw, navDrawer, conf, modifKey=False):
        self._conf = conf
        self._modifKey=modifKey
        self._aw=aw
        WHeader.__init__(self, self._aw, navDrawer, tpl_name='EventHeader')
        tzUtil = DisplayTZ(self._aw,self._conf)
        self._locTZ = tzUtil.getDisplayTZ()


    def getVars( self ):
        vars = WConferenceHeader.getVars( self )

        vars["categurl"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])
        #vars["confModif"] =  _("""<a href=%s> _("manage")</a>""")%quoteattr(str(urlHandlers.UHConfEnterModifKey.getURL(self._conf)))
        #if self._conf.canKeyModify(self._aw):
        #    vars["confModif"] =  _("""<a href=%s> _("exit manage")</a>""")%quoteattr(str(urlHandlers.UHConfCloseModifKey.getURL(self._conf)))
        #vars["confModif"] += "&nbsp;|&nbsp;"
        #if not self._conf.canAccess(self._aw) and self._conf.getAccessKey() != "":
        #    vars["confModif"] += _("""<a href=%s>_("full agenda")</a>&nbsp;|&nbsp;""")%(quoteattr(str(urlHandlers.UHConfForceEnterAccessKey.getURL(self._conf))))
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        stylesheets = styleMgr.getStylesheetListForEventType(vars["type"])

        viewoptions = []
        if len(stylesheets) != 0:
            stylesheets.sort(key=styleMgr.getStylesheetName)
            for stylesheet in stylesheets:
                viewoptions.append({"id": stylesheet, "name": styleMgr.getStylesheetName(stylesheet) })
        vars["viewoptions"] = viewoptions
        vars["SelectedStyle"] = styleMgr.getStylesheetName(vars["currentView"])
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
        dates = [ _(""" <option value="all" %s>- -  _("all days") - -</option> """)%selected]
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
        sessions = [ _(""" <option value="all" %s>- -  _("all sessions") - -</option> """)%selected]
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

        if Config.getInstance().getIndicoSearchServer() != '' :
            vars["searchBox"] = WCategorySearchBox(optionsClass='meetingHeaderSearchBox').getHTML()
        else:
            vars["searchBox"] = ""

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
        self.__isFrontPage = isFrontPage

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["isFrontPage"] = self.__isFrontPage;

        if not vars.has_key("modificationDate"):
            vars["modificationDate"] = ""

        if not vars.has_key("shortURL"):
            vars["shortURL"] = ""

        return vars

class WNavigationDrawer(WTemplated):

    def __init__( self, pars, bgColor = None, appendPath = [] ):
        self._target = pars["target"]
        self._isModif = pars.get("isModif", False)
        self._track = pars.get("track", None) #for abstracts viewed inside a track
        self._bgColor = bgColor

        """
            The appendPath is an array with dictionaries: {"url": x, "title": x}.
            Each of these links are added in the end of the breadcrumb
        """
        self._appendPath = appendPath

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["target"] = self._target
        vars["isModif"]= self._isModif
        vars["track"]= self._track
        vars["bgColor"] = self._bgColor
        vars["appendPath"] = self._appendPath
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

    def __init__( self, path = [], itemType = "", title = "" ):
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

    def __init__(self, target ):
        ## PATH
        # Iterate till conference is reached
        conf = target.getConference()
        path = self._getOwnerBasePath(target)
        path.append({"url": urlHandlers.UHConfModifSchedule.getURL( conf ), "title": _("Timetable")})
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
            else:
                break
        return path

class WContribListBannerModif(WTimetableBannerModif):

    def __init__(self, target ):
        ## PATH
        # Iterate till conference is reached
        conf = target.getConference()
        path = self._getOwnerBasePath(target)
        path.append({"url": urlHandlers.UHConfModifContribList.getURL( conf ), "title": _("Contributions list")})
        # TITLE AND TYPE
        itemType = type(target).__name__
        title = target.getTitle()
        WBannerModif.__init__(self, path, itemType, title)


class WNotifTplBannerModif(WBannerModif):

    def __init__( self, target ):
        path = [{"url": urlHandlers.UHConfModifCFA.getURL(target), "title":_("Call for abstracts setup")}]
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

    def __init__( self, track, abstract=None ):
        path = []
        target = track
        if abstract:
            target = abstract
            path = [{"url": urlHandlers.UHHelper.getModifUH(type(track)).getURL(track),
                             "title": truncateTitle(track.getTitle(), 30),
                             "type": type(track).__name__}]
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

class WListingsBannerModif(WBannerModif):

    def __init__( self, conf ):
        path=[{"url": urlHandlers.UHConfModifListings.getURL(conf), "title":_("All listings")}]

        itemType="Pending queues"
        title=""
        WBannerModif.__init__(self, path, itemType, title)

class WParticipantsBannerModif(WBannerModif):

    def __init__( self, conf ):
        path=[{"url": urlHandlers.UHConfModifParticipants.getURL(conf), "title":_("Participants list")}]

        itemType="Pending participants"
        title=""
        WBannerModif.__init__(self, path, itemType, title)


class WConfLogsBannerModif(WBannerModif):

    def __init__( self, conf ):
        path=[{"url": urlHandlers.UHConfModifLog.getURL(conf), "title":_("Logs")}]

        itemType="Log item"
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
        return  _("""<form action="%s" method="GET">
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

    def __init__( self, contrib ):
        self._contrib = contrib

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["deleteIconURL"] = Configuration.Config.getInstance().getSystemIconURL("delete")
        vars["moveIconURL"] = Configuration.Config.getInstance().getSystemIconURL("move")
        vars["writeIconURL"] = Configuration.Config.getInstance().getSystemIconURL("write_minutes")
        return vars



class WContributionDeletion(object):

    def __init__( self, contribList ):
        self._contribList = contribList

    def getHTML( self, actionURL ):
        l = []
        for contrib in self._contribList:
            l.append("""<li><i>%s</i></li>"""%contrib.getTitle())
        msg =  _("""
        <font size="+2"> _("Are you sure that you want to DELETE the following contributions"):<ul>%s</ul>?</font><br>
            <table>
                <tr><td>
                <font color="red"> _("Note that the following changes will result from this deletion"):</font>
                <ul>
                    <li> _("If the contribution is linked to an abstract"):</li>
                        <ul>
                            <li> _("The link between the abstract and the contribution will be deleted")</li>
                            <li> _("The status of the abstract will change to 'submitted'")</li>
                            <li> _("You'll lose the information about when and who accepted the abstract")</li>
                        </ul>
                    <li> _("ALL the existing sub-contributions within the above contribution(s) will also be deleted")</li>
                </ul>
                </td></tr>
            </table>
              """)%("".join(l))
        wc = WConfirmation()
        contribIdList = []
        for contrib in self._contribList:
            contribIdList.append( contrib.getId() )
        return wc.getHTML( msg, actionURL, {"selectedCateg": contribIdList}, \
                                            confirmButtonCaption="Yes", \
                                            cancelButtonCaption="No" )

    def delete( self ):
        for contrib in self._contribList:
            contrib.delete()
        return "done"


class WContribModifSC(WTemplated):

    def __init__( self, contrib ):
        self._contrib = contrib
        self._conf = self._contrib.getConference()


    def getSubContItems(self,SCModifURL):
        temp = []
        scList = self._contrib.getSubContributionList()
        for sc in scList:
            id = sc.getId()
            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (scList.index(sc),scList.index(sc))
            for i in range(1,len(scList)+1):
                if i== scList.index(sc)+1:
                    selbox += "<option selected value='%s'>%s" % (i-1,i)
                else:
                    selbox += "<option value='%s'>%s" % (i-1,i)
            selbox += """
                </select>"""
            temp.append("""
                <tr>
                    <td>
                        <input type="checkbox" name="selSubContribs" value="%s">
                        %s
                        &nbsp;<a href="%s">%s</a>
                    </td>
                </tr>"""%(id, selbox,SCModifURL(sc), escape(sc.getTitle())))
        html = """
                <input type="hidden" name="oldpos">
                <table align="center">%s
                </table>"""%"".join( temp )
        return html

    def getVars( self ):
        vars = WTemplated.getVars( self )
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
        vars["date"] = utils.formatDateTime(self.__conf.getAdjustedStartDate(), format="%d %B")

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


class WBreakDataModification(WTemplated):

    def __init__(self,sch,breakEntry=None,targetDay=None,conf=None):
        self._break=breakEntry
        if self._break!=None:
            self._sch=self._break.getSchedule()
        else:
            self._sch=sch
        self._targetDay=targetDay
        self._conf=conf

    def getVars( self ):
        vars = WTemplated.getVars( self )
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName = "", "", ""
        if self._break is not None:
            wpTitle =  _("Break entry data modification")
            title=self._break.getTitle()
            description=self._break.getDescription()
            tz = self._conf.getTimezone()
            sDate=convertTime.convertTime(self._break.getStartDate(),self._conf.getTimezone())
            day=sDate.day
            month=sDate.month
            year=sDate.year
            sHour=sDate.hour
            sMinute=sDate.minute
            durHours=int(self._break.getDuration().seconds/3600)
            durMinutes=int((self._break.getDuration().seconds%3600)/60)
            if self._break.getOwnLocation() is not None:
                defaultDefinePlace = "checked"
                defaultInheritPlace = ""
                locationName = self._break.getLocation().getName()
                locationAddress = self._break.getLocation().getAddress()
            if self._break.getOwnRoom() is not None:
                defaultDefineRoom= "checked"
                defaultInheritRoom = ""
                roomName = self._break.getRoom().getName()
            bgcolor=self._break.getColor()
            textcolor=self._break.getTextColor()
            textcolortolinks=""
            if self._break.isTextColorToLinks():
                textcolortolinks="checked=\"checked\""
            schOptions= _("""&nbsp;<input type="checkbox" name="moveEntries" value="1">  _("reschedule entries after this time")""")
        else:
            wpTitle = "Create new break"
            title, description = "break", ""
            refDate=self._sch.getFirstFreeSlotOnDay(self._targetDay)
            day = refDate.day
            month = refDate.month
            year = refDate.year
            sHour = refDate.hour
            sMinute = refDate.minute
            durHours, durMinutes = 0, 15
            bgcolor="#90C0F0"
            textcolor="#777777"
            schOptions=""
            textcolortolinks=False
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["ownerPlace"] = ""
        owner = self._sch.getOwner()
        vars["ownerType"]="conference"
        if isinstance(owner, conference.SessionSlot):
            vars["ownerType"]="session"
        ownerLocation = owner.getLocation()
        if ownerLocation:
            vars["ownerPlace"] = ownerLocation.getName()
        vars["locationName"] = quoteattr(str(locationName))
        vars["locationAddress"] = locationAddress
        vars["defaultInheritRoom"] = defaultInheritRoom
        vars["defaultDefineRoom"] = defaultDefineRoom
        vars["ownerRoom"] = ""
        ownerRoom =owner.getRoom()
        if ownerRoom:
            vars["ownerRoom"] = ownerRoom.getName()
        vars["roomName"] = quoteattr(str(roomName))

        vars["WPtitle"]=wpTitle
        vars["title"]=quoteattr(str(title))
        vars["description"]=self.htmlText(description)
        vars["sDay"]=str(day)
        vars["sMonth"]=str(month)
        vars["sYear"]=str(year)
        vars["sHour"]=str(sHour)
        vars["sMinute"]=str(sMinute)
        vars["durationHours"]=quoteattr(str(durHours))
        vars["durationMinutes"]=quoteattr(str(durMinutes))
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["colorChartIcon"]=Config.getInstance().getSystemIconURL("colorchart")
        urlbg=urlHandlers.UHSimpleColorChart.getURL()
        urlbg.addParam("colorCodeTarget", "backgroundColor")
        urlbg.addParam("colorPreviewTarget", "backgroundColorpreview")
        vars["bgcolorChartURL"]=urlbg
        vars["bgcolor"] = bgcolor
        urltext=urlHandlers.UHSimpleColorChart.getURL()
        urltext.addParam("colorCodeTarget", "textColor")
        urltext.addParam("colorPreviewTarget", "textColorpreview")
        vars["textcolorChartURL"]=urltext
        vars["textcolor"] = textcolor
        vars["textColorToLinks"] = textcolortolinks
        vars["calendarIconURL"]=Config.getInstance().getSystemIconURL( "calendar" )
        vars["calendarSelectURL"]=urlHandlers.UHSimpleCalendar.getURL()
        vars["schOptions"]=schOptions
        vars["autoUpdate"]=""
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(self._conf)
        if wf != None:
            type = wf.getId()
        else:
            type = "conference"
        if type == "conference":
            vars["Colors"]=WSessionModEditDataColors().getHTML(vars)
        else:
            vars["Colors"]=""
        vars["conference"] = self._conf
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()

        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
        return vars


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


class WAccessControlFrame(WTemplated):

    def getHTML( self, target, setVisibilityURL, addAllowedURL, removeAllowedURL):
        self.__target = target
        params = { "setVisibilityURL": setVisibilityURL,\
                   "addAllowedURL": addAllowedURL, \
                   "removeAllowedURL": removeAllowedURL }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        if self.__target.getAccessProtectionLevel() == -1:
            vars["privacy"] = "ABSOLUTELY PUBLIC%s" % WInlineContextHelp('The object will stay public regardless of the protection of its parent (no more inheritance)').getHTML()
            vars["changePrivacy"] = """make it simply <input type="submit" class="btn" name="visibility" value="PUBLIC">%s<br/>""" % WInlineContextHelp('It will then be public by default but will inherit from the potential protection of its parent').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself%s<br/>""" % WInlineContextHelp('It will then be private').getHTML()
        elif self.__target.isItselfProtected():
            vars["privacy"] = "PRIVATE%s" % WInlineContextHelp('The object is private by itself').getHTML()
            vars["changePrivacy"] = """make it simply <input type="submit" class="btn" name="visibility" value="PUBLIC">%s<br/>""" % WInlineContextHelp('It will then be public by default but will inherit from the potential protection of its parent').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        elif self.__target.hasProtectedOwner():
            vars["privacy"] = "PRIVATE by inheritance%s" % WInlineContextHelp('Private because a parent object is private').getHTML()
            vars["changePrivacy"] = """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself%s<br/>""" % WInlineContextHelp('It will then remain private even if the parent object goes public').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        else:
            vars["privacy"] = "PUBLIC%s" % WInlineContextHelp('the object is currently public because its parent is public but might inherit from the potential protection of its parent if it changes one day').getHTML()
            vars["changePrivacy"] = """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself<br/>"""
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        vars["locator"] = self.__target.getLocator().getWebForm()
        vars["userTable"] = WPrincipalTable().getHTML( self.__target.getAllowedToAccessList(), self.__target, vars["addAllowedURL"], vars["removeAllowedURL"],selectable=False )

        return vars


class WConfAccessControlFrame(WTemplated):

    def getHTML( self, target, setVisibilityURL, addAllowedURL, removeAllowedURL,  setAccessKeyURL):
        self.__target = target
        params = { "setPrivacyURL": setVisibilityURL,\
                   "addAllowedURL": addAllowedURL, \
                   "removeAllowedURL": removeAllowedURL, \
                    "setAccessKeyURL": setAccessKeyURL }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        if self.__target.getAccessProtectionLevel() == -1:
            vars["privacy"] = "ABSOLUTELY PUBLIC%s" % WInlineContextHelp('The object will stay public regardless of the protection of its parent (no more inheritance)').getHTML()
            vars["changePrivacy"] = """make it simply <input type="submit" class="btn" name="visibility" value="PUBLIC">%s<br/>""" % WInlineContextHelp('It will then be public by default but will inherit from the potential protection of its parent').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself%s<br/>""" % WInlineContextHelp('It will then be private').getHTML()
        elif self.__target.isItselfProtected():
            vars["privacy"] = "PRIVATE%s" % WInlineContextHelp('The object is private by itself').getHTML()
            vars["changePrivacy"] = """make it simply <input type="submit" class="btn" name="visibility" value="PUBLIC">%s<br/>""" % WInlineContextHelp('It will then be public by default but will inherit from the potential protection of its parent').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        elif self.__target.hasProtectedOwner():
            vars["privacy"] = "PRIVATE by inheritance%s" % WInlineContextHelp('Private because a parent object is private').getHTML()
            vars["changePrivacy"] = """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself%s<br/>""" % WInlineContextHelp('It will then remain private even if the parent object goes public').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        else:
            if not self.__target.isFullyPublic():
                fullyPublic = " - part of this event is protected"
            else:
                fullyPublic = ""
            vars["privacy"] = "PUBLIC%s%s" % (WInlineContextHelp('the object is currently public because its parent is public but might inherit from the potential protection of its parent if it changes one day').getHTML(), fullyPublic)
            vars["changePrivacy"] = """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself<br/>"""
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()

        vars["locator"] = self.__target.getLocator().getWebForm()
        vars["userTable"] = WPrincipalTable().getHTML( self.__target.getAllowedToAccessList(),
                                                       self.__target,
                                                       vars["addAllowedURL"],
                                                       vars["removeAllowedURL"],
                                                       selectable=False )
        vars["accessKey"] = self.__target.getAccessKey()
        return vars


class WUserTableItem(WTemplated):

    def __init__(self, multi=True):
        self._multi = multi

    def getHTML( self, user, selected=False, selectable=True ):
        self.__user = user
        self._selected = selected
        self._selectable = selectable
        return WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["id"] = self.__user.getId()
        vars["email"] = self.__user.getEmail()
        vars["fullName"] = self.__user.getFullName()
        vars["type"] = "checkbox"
        selectionText = "checked"
        if not self._multi:
            vars["type"] = "radio"
            selectionText = "selected"
        vars["selected"] = ""
        if self._selected:
            vars["selected"] = selectionText

        if self._rh._getUser():
            vars["currentUserBasket"] = self._rh._getUser().getPersonalInfo().getBasket()
        else:
            vars["currentUserBasket"] = None

        vars["selectable"] = self._selectable

        return vars

class WPendingUserTableItem(WTemplated):

    def getHTML( self, email, selectable=True ):
        self.email = email
        self._selectable = selectable
        return WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["email"] = self.email
        vars["selectable"] = self._selectable

        return vars

class WGroupTableItem(WTemplated):

    def __init__(self, multi=True):
        self._multi = multi

    def getHTML( self, group, selected=False, selectable=True ):
        self.__group = group
        self._selected = selected
        self._selectable = selectable
        return WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["groupImg"] = Configuration.Config.getInstance().getSystemIconURL("group")
        vars["id"] = self.__group.getId()
        vars["fullName"] = self.__group.getName()
        vars["type"] = "checkbox"
        selectionText = "checked"
        if not self._multi:
            vars["type"] = "radio"
            selectionText = "selected"
        vars["selected"] = ""
        if self._selected:
            vars["selected"] = selectionText
        vars["selectable"] = self._selectable
        return vars

class WGroupNICETableItem(WTemplated):

    def __init__(self, multi=True):
        self._multi = multi

    def getHTML( self, group, selected=False, selectable=True ):
        self.__group = group
        self._selected = selected
        self._selectable = selectable
        return WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["id"] = self.__group.getId()
        vars["fullName"] = self.__group.getName()
        vars["type"] = "checkbox"
        selectionText = "checked"
        if not self._multi:
            vars["type"] = "radio"
            selectionText = "selected"
        vars["selected"] = ""
        if self._selected:
            vars["selected"] = selectionText
        vars["selectable"] = self._selectable
        return vars

class WAuthorTableItem(WTemplated):

    def __init__(self, multi=False):
        self._multi = multi

    def getHTML( self, author, selected=False ):
        self.__author = author
        self._selected = selected
        return WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["id"] = "*author*:%s"%conference.AuthorIndex()._getKey(self.__author)
        vars["fullName"] = self.__author.getFullName()
        vars["type"] = "checkbox"
        selectionText = "checked"
        if not self._multi:
            vars["type"] = "radio"
            selectionText = "selected"
        vars["selected"] = ""
        if self._selected:
            vars["selected"] = selectionText
        return vars


class WPrincipalTable(WTemplated):

    def getHTML( self, principalList, target, addPrincipalsURL, removePrincipalsURL, pendings=[], selectable=True ):
        self.__principalList = principalList
        self.__principalList.sort(utils.sortPrincipalsByName)
        self.__pendings = pendings
        self.__target = target
        self.__selectable = selectable;
        return WTemplated.getHTML( self, {"addPrincipalsURL": addPrincipalsURL,\
                                  "removePrincipalsURL": removePrincipalsURL } )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = ""
        if self.__target:
            vars["locator"] = self.__target.getLocator().getWebForm()
        ul = []
        selected = False
        if len(self.__principalList) == 1:
            selected = True
        for principal in self.__principalList:
            if isinstance(principal, user.Avatar):
                ul.append( WUserTableItem().getHTML( principal, selected, self.__selectable ) )
            elif isinstance(principal, user.CERNGroup):
                ul.append( WGroupNICETableItem().getHTML( principal, selected, self.__selectable ) )
            elif isinstance(principal, user.Group):
                ul.append( WGroupTableItem().getHTML( principal, selected, self.__selectable ) )
        for email in self.__pendings:
            ul.append(WPendingUserTableItem().getHTML(email, self.__selectable))
        vars["userItems"] = "".join( ul )
        return vars


class WModificationControlFrame(WTemplated):

    def getHTML( self, target, addManagersURL, removeManagersURL ):
        self.__target = target
        params = { "addManagersURL": addManagersURL, \
                   "removeManagersURL": removeManagersURL }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self.__target.getLocator().getWebForm()
        vars["principalTable"] = WPrincipalTable().getHTML( self.__target.getManagerList(),
                                                            self.__target,vars["addManagersURL"],
                                                            vars["removeManagersURL"],
                                                            pendings=self.__target.getAccessController().getModificationEmail(),
                                                            selectable=False)

        return vars


class WConfModificationControlFrame(WTemplated):

    def getHTML( self, target, addManagersURL, removeManagersURL, setModifKeyURL ):
        self.__target = target
        params = { "addManagersURL": addManagersURL, \
                   "removeManagersURL": removeManagersURL, \
                    "setModifKeyURL": setModifKeyURL }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self.__target.getLocator().getWebForm()
        vars["principalTable"] = WPrincipalTable().getHTML( self.__target.getManagerList(),
                                                            self.__target, vars["addManagersURL"],
                                                            vars["removeManagersURL"],
                                                            pendings=self.__target.getAccessController().getModificationEmail(),
                                                            selectable=False)
        vars["modifKey"] = self.__target.getModifKey()
        return vars

class WConfRegistrarsControlFrame(WTemplated):

    def getHTML(self, target, addRegistrarURL, removeRegistrarURL):
        self.__target = target
        params = {
            "addRegistrarURL": addRegistrarURL,
            "removeRegistrarURL": removeRegistrarURL
        }
        return WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["principalTable"] = WPrincipalTable().getHTML( self.__target.getRegistrarList(), self.__target, vars["addRegistrarURL"], vars["removeRegistrarURL"], selectable=False)
        return vars


class WAlarmFrame(WTemplated):

    def getHTML( self, target, addAlarmURL, deleteAlarmURL, modifyAlarmURL ):
        self.__target = target
        self._deleteAlarmURL = deleteAlarmURL
        self._modifyAlarmURL = modifyAlarmURL
        params = { "addAlarmURL": addAlarmURL, \
                   "deleteAlarmURL": deleteAlarmURL, \
                   "modifyAlarmURL": modifyAlarmURL
                   }
        return  WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self.__target.getLocator().getWebForm()
        stri = ""
        for al in self.__target.getAlarmList():
            addr = ""
            if len(al.getToAddrList()) > 0 :
                addr = " <br> ".join(al.getToAddrList()) + " <br> "
            for user in al.getToUserList():
                addr = addr + user.getEmail() + " <br> "

            if al.getToAllParticipants() :
                addr = "to all participants"
            if al.getAdjustedLastDate() != None:
                sent = " (Sent the %s)"%al.getAdjustedLastDate().strftime("%Y-%m-%d %HH")
            else:
                sent = ""
            sd = ""
            if al.getTimeBefore() is not None:
                tb = al.getTimeBefore()
                d = tb.days
                if d != 0:
                    sd = "D-%s (%s)" % (d,al.getAdjustedStartDate().strftime("%Y-%m-%d %HH"))
                else:
                    sd = "H-%s (%s)" % (tb.seconds/3600,al.getAdjustedStartDate().strftime("%Y-%m-%d %HH"))
            elif al.getAdjustedStartDate() is not None:
                sd = al.getAdjustedStartDate().strftime("%Y-%m-%d %HH")
            else:
                sd = "not set"
            stri = stri +  _("""<tr> <td nowrap>%s</td> <td width=\"60%%\"><a href=\"%s\">%s</a>%s</td> <td nowrap>%s</td>  <td align=\"center\"><a href=\"%s\"> _("Delete")</a></td>   </tr>""")%(\
                                    sd, \
                                    str(self._modifyAlarmURL) + "?" + al.getLocator().getURLForm(), \
                                    al.getSubject(), \
                                    sent, \
                                    addr, \
                                    str(self._deleteAlarmURL) + "?" + al.getLocator().getURLForm())
        vars["alarms"] = stri
        #vars["timezone"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        vars["timezone"] = self.__target.getTimezone()
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

    def __init__( self, target ):
        self._target = target

    def getHTML(self, addURL, removeURL):
        self._addURL = addURL
        self._removeURL = removeURL
        return WTemplated.getHTML( self )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        l = []
        for dom in self._target.getDomainList():
            l.append("""<input type="checkbox" name="selectedDomain" value="%s"> %s"""%(dom.getId(), dom.getName()))
        vars["domains"] = "<br>".join(l)
        l = []
        for dom in domain.DomainHolder().getList():
            if dom not in self._target.getDomainList():
                l.append("""<option value="%s">%s</option>"""%(dom.getId(), dom.getName()))
        vars["domainsToAdd"] = "".join(l)
        vars["removeURL"] = self._removeURL
        vars["addURL"] = self._addURL
        vars["locator"] = self._target.getLocator().getWebForm()
        return vars


class WMaterialDataModificationBase(WTemplated):

    def __init__( self, material ):
        self._material = material
        self._owner = material.getOwner()

    def _setMaterialValues( self, material, materialData ):
        material.setTitle( materialData["title"] )
        material.setDescription( materialData["description"] )
        if "type" in materialData:
            material.setType( materialData["type"] )

    def _getTypesSelectItems( self, default = "misc" ):
        definedTypes = ["misc"]
        l = []
        for type in definedTypes:
            default = ""
            if type == default:
                default = "default"
            l.append("""<option value="%s" %s>%s</option>"""%( type, default, type ))
        return "".join( l )



class WMaterialCreation(WMaterialDataModificationBase):

    def __init__( self, owner):
        self._owner = owner


    def getVars( self ):
        vars = WMaterialDataModificationBase.getVars( self )
        vars["title"] = ""
        vars["description"] = ""
        vars["types"] = self._getTypesSelectItems()
        vars["locator"] = self._owner.getLocator().getWebForm()
        return vars

    def create( self, materialData ):
        m = conference.Material()
        self._setMaterialValues( m, materialData )
        self._owner.addMaterial( m )
        return m

class WInlineContextHelp(WTemplated):

    def __init__(self, content):
        self._content = content

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["helpContent"] = self._content
        vars["imgSrc"] = Config.getInstance().getSystemIconURL( "help" )
        return vars

#class WPaperDataModification( WMaterialDataModification ):
#    pass

#class WMaterialModification( WTemplated ):
#
#    def __init__( self, material ):
#        self._material = material
#        self.__conf = material.getConference()
#        self.__session = material.getSession()
#        self.__contrib = material.getContribution()
#
#    def getVars( self ):
#        vars = WTemplated.getVars( self )
#        vars["locator"] = self._material.getLocator().getWebForm()
#        vars["confTitle"] = self.__conf.getTitle()
#        vars["sessionTitle"] = ""
#        if self.__session != None:
#            vars["sessionTitle"] = self.__session.getTitle()
#        vars["contributionTitle"] = ""
#        if self.__contrib != None:
#             vars["contributionTitle"] = self.__contrib.getTitle()
#        vars["title"] = self._material.getTitle()
#        vars["description"] = self._material.getDescription()
#        vars["type"] = self._material.getType()
#        l = []
#        for res in self._material.getResourceList():
#            if res.__class__ is conference.LocalFile:
#                l.append( """<li><input type="checkbox" name="removeResources" value="%s"><small>[%s]</small> <b><a href="%s">%s</a></b> (%s) - <small>%s bytes</small></li>"""%(res.getId(), res.getFileType(), vars["modifyFileURLGen"](res), res.getName(), res.getFileName(), strfFileSize( res.getSize() )))
#            elif res.__class__ is conference.Link:
#                l.append( """<li><input type="checkbox" name="removeResources" value="%s"><b><a href="%s">%s</a></b> (%s)</li>"""%(res.getId(), vars["modifyLinkURLGen"](res), res.getName(), res.getURL()))
#        vars["resources"] = "<ol>%s</ol>"%"".join( l )
#        vars["accessControlFrame"] = WAccessControlFrame().getHTML(\
#                                                    self._material,\
#                                                    vars["setVisibilityURL"],\
#                                                    vars["addAllowedURL"],\
#                                                    vars["removeAllowedURL"] )
#        if not self._material.isProtected():
#            df =  WDomainControlFrame( self._material )
#            vars["accessControlFrame"] += "<br>%s"%df.getHTML( \
#                                                    vars["addDomainURL"], \
#                                                    vars["removeDomainURL"] )
#        return vars


#class WResourceSubmission(WTemplated):
#
#    def _setObjects( self, confId, sessionId, contribId, materialId ):
#        ch = conference.ConferenceHolder()
#        self._conf = ch.getById( confId )
#        self._session =  self._contrib  = self._material = None
#        self._matParent = self._conf
#        if sessionId != None and sessionId != "":
#            self._session = self._conf.getSessionById( sessionId )
#            self._matParent =  self._session
#            if contribId != None and contribId != "":
#                self._contrib = self._session.getContributionById( contribId )
#                self._matParent = self._contrib
#        elif  contribId != None and contribId != "":
#            self._contrib = self._conf.getContributionById( contribId )
#            self._matParent = self._contrib
#        if materialId != None and materialId != "":
#            self._material = self._matParent.getMaterialById( materialId )
#
#    def getHTML( self, confId, sessionId, contribId, materialId, params ):
#        self._setObjects( confId, sessionId, contribId, materialId )
#        str = """
#            <form action="%s" method="POST" enctype="multipart/form-data">
#                <input type="hidden" name="confId" value="%s">
#                <input type="hidden" name="sessionId" value="%s">
#                <input type="hidden" name="contribId" value="%s">
#                <input type="hidden" name="materialId" value="%s">
#                %s
#            </form>
#              """%(params["postURL"], confId, sessionId, contribId, \
#                    materialId,  WTemplated.getHTML( self, params ) )
#        return str


#class WFileSubmission(WTemplated):
#
#    def __init__(self, material):
#        self.__material = material
#
#    def getHTML( self, params ):
#        str = """
#            <form action="%s" method="POST" enctype="multipart/form-data">
#                %s
#                %s
#            </form>
#              """%(params["postURL"], \
#                   self.__material.getLocator().getWebForm(),\
#                   WTemplated.getHTML( self, params ) )
#        return str
#
#    def submit( self, params ):
#        f = conference.LocalFile()
#        f.setName( params["title"] )
#        f.setDescription( params["description"] )
#        f.setFileName( params["fileName"] )
#        f.setFilePath( params["filePath"] )
#        self.__material.addResource( f )
#        return "[done]"


#class WLinkSubmission(WResourceSubmission):
#
#    def __init__(self, material):
#        self.__material = material
#
#    def getHTML( self, params ):
#        str = """
#            <form action="%s" method="POST" enctype="multipart/form-data">
#                %s
#                %s
#            </form>
#              """%(params["postURL"], \
#                   self.__material.getLocator().getWebForm(),\
#                   WTemplated.getHTML( self, params ) )
#        return str
#
#    def submit( self, params ):
#        l = conference.Link()
#        l.setName( params["title"] )
#        l.setDescription( params["description"] )
#        l.setURL( params["url"] )
#        self.__material.addResource( l )
#        return "[done]"


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
            vars["however"] =  _("However, you will not be able to log into the system until the site administrator has accepted your account creation request. You will be warned of the decision by email")+".<br>"
        vars["signInURL"] = quoteattr( str( vars["signInURL"] ) )
        vars["supportAddr"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
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
        vars["contactEmail"]  = info.HelperMaKaCInfo.getMaKaCInfoInstance().getSupportEmail()
        return vars


class WUserSearchResultsTable( WTemplated ):

    def __init__(self, multi=True):
        self._multi = multi

    def __getItemClass( self, principal ):
        if principal.__class__.__name__ == "Avatar":
            return WUserTableItem
        elif isinstance(principal, user.CERNGroup):
            return WGroupNICETableItem
        elif isinstance(principal, user.Group):
            return WGroupTableItem
        elif isinstance(principal,conference.ContributionParticipation):
            return WAuthorTableItem
        return None

    def getHTML( self, resultList ):
        self.__resultList = resultList
        self.__resultList.sort(utils.sortPrincipalsByName)
        return WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        l = []
        selected = False
        if len(self.__resultList) == 1:
            selected = True
        for principal in self.__resultList:
            l.append( self.__getItemClass(principal)(self._multi).getHTML( principal, selected ) )
        if l:
            vars["usersFound"] = "".join( l )
        else:
            vars["usersFound"] =  _(""""<br><span class=\"blacktext\">&nbsp;&nbsp;&nbsp; _("No results for this search")</span>""")
        vars["nbResults"] = len(self.__resultList)
        return vars


class WSignIn(WTemplated):

    def getVars( self ):
        vars = WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["postURL"] = quoteattr( str( vars.get( "postURL", "" ) ) )
        vars["returnURL"] = quoteattr( str( vars.get( "returnURL", "" ) ) )
        vars["forgotPasswordURL"] = quoteattr( str( vars.get( "forgotPassordURL", "" ) ) )
        vars["login"] = quoteattr( vars.get( "login", "" ) )
        vars["msg"] = self.htmlText( vars.get( "msg" ) )
        imgIcon=Configuration.Config.getInstance().getSystemIconURL("currentMenuItem")
        if Configuration.Config.getInstance().getLoginURL().startswith("https"):
           imgIcon=imgIcon.replace("http://", "https://")
           imgIcon = urlHandlers.setSSLPort( imgIcon )
        vars["itemIcon"] = imgIcon
        vars["createAccount"] = ""
        if minfo.getAuthorisedAccountCreation():
            vars["createAccount"] =  _("""_("If you don't have an account, you can create one")<a href="%s"> _("here")</a>
        """) % (vars["createAccountURL"])
        vars["NiceMsg"]=""
        if "Nice" in Configuration.Config.getInstance().getAuthenticatorList():
            vars["NiceMsg"]= _("Please note you can use your NICE (CERN) account")
        return vars

class WConfirmation(WTemplated):

    def getHTML( self, message, postURL, passingArgs, **opts):
        params = {}
        params["message"] = message
        params["postURL"] = postURL
        pa = []
        for arg in passingArgs.keys():
            if not type( passingArgs[arg] ) == types.ListType:
                passingArgs[arg] = [passingArgs[arg]]
            for value in passingArgs[arg]:
                pa.append("""<input type="hidden" name="%s" value="%s">"""%( arg, value ))
        params["passingArgs"] = "".join(pa)
        params["confirmButtonCaption"]=opts.get("confirmButtonCaption",  _("OK"))
        params["cancelButtonCaption"]=opts.get("cancelButtonCaption",  _("Cancel"))
        params["systemIconWarning"] = Configuration.Config.getInstance().getSystemIconURL( "warning" )
        return WTemplated.getHTML( self, params )

class WDisplayConfirmation(WTemplated):

    def getHTML( self, message, postURL, passingArgs, **opts):
        params = {}
        params["message"] = message
        params["postURL"] = postURL
        pa = []
        for arg in passingArgs.keys():
            if not type( passingArgs[arg] ) == types.ListType:
                passingArgs[arg] = [passingArgs[arg]]
            for value in passingArgs[arg]:
                pa.append("""<input type="hidden" name="%s" value="%s">"""%( arg, value ))
        params["passingArgs"] = "".join(pa)
        params["confirmButtonCaption"]=opts.get("confirmButtonCaption",  _("OK"))
        params["cancelButtonCaption"]=opts.get("cancelButtonCaption",  _("Cancel"))
        params["systemIconWarning"] = Configuration.Config.getInstance().getSystemIconURL( "warning" )
        return WTemplated.getHTML( self, params )

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


class WConferenceList(WTemplated):

    def __init__( self, category, wfReg ):
        self._categ = category
        self._list = category.getConferenceList()

    def getHTML( self, aw, params ):
        self._aw = aw
        return WTemplated.getHTML( self, params )

    @staticmethod
    def sortEvents(list):

        # populate a year -> month -> day -> event (4 level) tree in O(N) time
        # each node is a dictionary, so that O(1) is reached for lookup of leaves

        def __addLeaf(map, path, leaf):

            # stop condition
            if path == []:
                map[leaf.getId()] = leaf
                return;

            if not map.has_key(path[0]):
                map[path[0]] = {} # virgin node

            # this reminds me of Prolog... beautiful...
            __addLeaf(map[path[0]], path[1:], leaf)

        fList = {}
        listByMonth = {}
        for conf in list:
            startDate = conf.getStartDate()
            path = [startDate.year, startDate.month, startDate.day]
            __addLeaf(fList, path, conf)
            listByMonth.setdefault(startDate.year,{}).setdefault(startDate.month,[]).append(conf)
        return fList, listByMonth

    def getPresentPastFutureEvents(self, allEvents, eventsByMonth, numEvents):
        """
        @param allEvents: is a dictionary with the format expected by the template ConferenceListItem
        @param eventsByMonth: is a dictionary with all the events by year and month. E.g. eventsByMonth[2009][1] == [conf1, conf2,...]
        @return:
            - a dictionary with the same format as allEvents but just with the events to display
            - a dictionary with the same format as allEvents but just with the future events
            - a counter with the number of future events
            - a counter with the number of past events
            - the oldest date of the events that are shown by default
        """

        def getPrevMonth(d):
            year = d.year
            prevMonth = (d.month - 1)%12
            if prevMonth == 0:
                prevMonth = 12
                year -= 1
            return date(year, prevMonth, 1)


        def getNextMonth(d):
            year = d.year
            nextMonth = (d.month + 1)%12
            if d.month + 1 == 12:
                nextMonth = 12
            elif d.month + 1 > 12:
                year += 1
            return date(year, nextMonth, 1)

        MAX_NUMBER_OF_EVENTS_SHOWN = 10
        if numEvents < MAX_NUMBER_OF_EVENTS_SHOWN:
            MAX_NUMBER_OF_EVENTS_SHOWN = numEvents
        todayDate = nowutc().date()
        previousMonthDate, nextMonthDate, newerDateUsed, olderDateUsed = todayDate, todayDate, todayDate, todayDate
        nextMonthDate = todayDate

        ## CREATE Present Events dict
        presentEvents = {}
        presentCounter = 0
        if allEvents.has_key(todayDate.year) and allEvents[todayDate.year].has_key(todayDate.month):
            presentEvents.setdefault(todayDate.year,{}).setdefault(todayDate.month, allEvents[todayDate.year][todayDate.month])
            del allEvents[todayDate.year][todayDate.month]
            presentCounter = len(eventsByMonth[todayDate.year][todayDate.month])
        while presentCounter < MAX_NUMBER_OF_EVENTS_SHOWN:
            previousMonthDate = getPrevMonth(previousMonthDate)
            nextMonthDate = getNextMonth(nextMonthDate)
            # add nextMonth
            if allEvents.has_key(nextMonthDate.year) and allEvents[nextMonthDate.year].has_key(nextMonthDate.month):
                presentEvents.setdefault(nextMonthDate.year,{}).setdefault(nextMonthDate.month, allEvents[nextMonthDate.year][nextMonthDate.month])
                del allEvents[nextMonthDate.year][nextMonthDate.month] # the events are removed for the later gathering of future events
                presentCounter += len(eventsByMonth[nextMonthDate.year][nextMonthDate.month])
                newerDateUsed = nextMonthDate
            # add prevMonth
            if allEvents.has_key(previousMonthDate.year) and allEvents[previousMonthDate.year].has_key(previousMonthDate.month):
                presentEvents.setdefault(previousMonthDate.year,{}).setdefault(previousMonthDate.month, allEvents[previousMonthDate.year][previousMonthDate.month])
                del allEvents[previousMonthDate.year][previousMonthDate.month]
                presentCounter += len(eventsByMonth[previousMonthDate.year][previousMonthDate.month])
                olderDateUsed = previousMonthDate

        ## CREATE future events dict and future/past counter
        futureEvents = {}
        futureCounter = 0
        pastCounter = 0
        for year in allEvents.keys():
            if year > newerDateUsed.year:
                futureEvents[year] = allEvents[year]
                for m in eventsByMonth[year].keys():
                    futureCounter += len(eventsByMonth[year][m])
            elif year < olderDateUsed.year:
                for m in eventsByMonth[year].keys():
                    pastCounter += len(eventsByMonth[year][m])
            else:
                for month in allEvents[year].keys():
                    if newerDateUsed.year == year and month > newerDateUsed.month:
                        futureEvents.setdefault(year,{})[month] = allEvents[year][month]
                        futureCounter += len(eventsByMonth[year][month])
                    elif olderDateUsed.year == year and month < olderDateUsed.month:
                        pastCounter += len(eventsByMonth[year][month])

        return presentEvents, futureEvents, futureCounter, pastCounter, olderDateUsed

    def getVars( self ):
        vars = WTemplated.getVars( self )
        allEvents, eventsByMonth = WConferenceList.sortEvents(self._list)
        #vars["items"], vars["futureItems"], vars["numOfEventsInTheFuture"], vars["numOfEventsInThePast"] = allEvents, allEvents, 0, 0
        vars["presentItems"], vars["futureItems"], vars["numOfEventsInTheFuture"], vars["numOfEventsInThePast"], vars["oldestMonthDate"] =  self.getPresentPastFutureEvents(allEvents, eventsByMonth, len(self._list))
        vars["categ"] = self._categ
        vars["ActiveTimezone"] = DisplayTZ(self._aw,self._categ,useServerTZ=1).getDisplayTZ()

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


class WCategoryStatisticsList(WTemplated):

    def __init__( self, statsName, stats ):
        self._stats = stats
        self._statsName = statsName

    def getHTML( self, aw ):
        self._aw = aw
        return WTemplated.getHTML( self )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        # Construction of the tables from the dictionary (stats).
        # Initialization:
        tmp = []
        maximum = 0
        stats = {}
        years = self._stats.keys()
        years.sort()
        for y in range(years[0], min(datetime.now().year+4,years[-1:][0]+1)):
            stats[y] = self._stats.get(y,0)
        maximum = max(stats.values())
        years = stats.keys()
        years.sort()
        for y in years:
            nb = stats[y]
            percent = (nb*100)/maximum
            if nb > 0 and percent == 0:
                percent = 1
            wcslr = WCategoryStatisticsListRow( y, percent, stats[y] )
            tmp.append(wcslr.getHTML( self._aw ))
        vars["statsName"] = self._statsName
        vars["statsRows"] = "".join( tmp )
        vars["total"] = sum(stats.values())
        return vars

class WConfCreationControlFrame(WTemplated):

    def __init__( self, categ ):
        self._categ = categ

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["locator"] = self._categ.getLocator().getWebForm()
        vars["status"] =  _("OPENED")
        vars["changeStatus"] =  _("""( <input type="submit" class="btn" name="RESTRICT" value="_("RESTRICT it")"> )""")
        if self._categ.isConferenceCreationRestricted():
            vars["status"] =  _("RESTRICTED")
            vars["changeStatus"] = _("""( <input type="submit" class="btn" name="OPEN" value="_("OPEN it")"> )""")
        vars["principalTable"] = WPrincipalTable().getHTML( self._categ.getConferenceCreatorList(), self._categ , vars["addCreatorsURL"], vars["removeCreatorsURL"], selectable=False )
        vars["notifyCreationList"] = quoteattr(self._categ.getNotifyCreationList())
        vars["setNotifyCreationURL"] = urlHandlers.UHCategorySetNotifyCreation.getURL(self._categ)
        return vars


class WWriteMinutes(WTemplated):

    def __init__( self, target ):
        self._target = target

    def getVars( self ):
        vars = WTemplated.getVars( self )
        minutes = self._target.getMinutes()
        vars["text"] = ""
        if minutes:
            vars["text"] = minutes.getText()
        vars["baseURL"]=Config.getInstance().getBaseURL()
        vars["imageUploadURL"]=urlHandlers.UHConfModifDisplayAddPageFile.getURL(self._target)
        vars["imageBrowserURL"]=urlHandlers.UHConfModifDisplayAddPageFileBrowser.getURL(self._target)
        vars["compileButton"] = ""
        if isinstance(self._target, conference.Conference):
            vars["compileButton"] =  """
                <input type="submit" class="btn"  name="compile" value="compile minutes" onClick= "return confirm('Are you sure you want to compile minutes from all talks in the agenda? This will replace any existing text here.');">"""
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

    def newTab( self, id, caption, url, hidden=False ):
        tab = Tab( self, id, caption, url, hidden=hidden )
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

    def __init__( self, owner, id, caption, URL, hidden = False ):
        self._owner = owner
        self._id = id.strip()
        self._caption = caption.strip()
        self._url = URL
        self._enabled = True
        self._subtabControl=None
        self._hidden = hidden

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

class WConfModifAC:

    def __init__( self, conference ):
        self.__conf = conference

    def getHTML( self, params ):
        ac = WAccessControlFrame().getHTML( self.__conf,\
                                            params["setVisibilityURL"],\
                                            params["addAllowedURL"],\
                                            params["removeAllowedURL"] )
        dc = ""
        if not self.__conf.isProtected():
            dc =  "<br>%s"%WDomainControlFrame( self.__conf ).getHTML( \
                                                    params["addDomainURL"], \
                                                    params["removeDomainURL"] )
        mc = WModificationControlFrame().getHTML( self.__conf,\
                                                  params["addManagersURL"],\
                                                  params["removeManagersURL"] )
        return """%s%s<br>%s"""%( ac, dc, mc )

#class WTrackModifSubTrack( WTemplated ):
#
#    def __init__( self, track ):
#        self.__track = track
#        self.__conf = track.getConference()
#
#    def getVars( self ):
#        vars = WTemplated.getVars(self)
#        if len(self.__track.getSubTrackList()) == 0:
#            ht = "No sub track defined"
#        else:
#            ht = "<table width=\"100%%\">\n"
#            for subTrack in self.__track.getSubTrackList():
#                ht += "<tr bgcolor=\"#AAFFAA\"><td><input type=\"checkbox\" name=\"selSubTracks\" value=\"%s\"></td><td><a href=\"%s\">%s</a></td><td>%s</td></tr>\n"%(subTrack.getId(), vars["dataModificationURLGen"](subTrack) , subTrack.getTitle(), subTrack.getDescription())
#            ht += "</table>\n"
#        vars["listSubTrack"] = ht
#        return vars


#class WSubTrackDataModification(WTemplated):
#
#    def __init__( self, subTrack ):
#        self.__subTrack = subTrack
#        self.__track = subTrack.getTrack()
#
#    def getVars( self ):
#        vars = WTemplated.getVars(self)
#
#        vars["title"] = self.__subTrack.getTitle()
#        vars["description"] = self.__subTrack.getDescription()
#
#        vars["locator"] = self.__subTrack.getLocator().getWebForm()
#
#        return vars

#class WCFAModifFrame(WTemplated):
#
#    def __init__( self, conf, aw):
#        self.__conf = conf
#        self._aw = aw
#
#    def getHTML( self, body, **params):
#        params["body"] = body
#        return WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = WTemplated.getVars( self )
#
#        vars["context"] = WConfModifHeader( self.__conf, self._aw ).getHTML(vars)
#
#
#        return vars

#class WCFAModifMain(WTemplated):
#
#    def __init__( self, conf ):
#        self.__conf = conf
#
#    def getVars( self ):
#        vars = WTemplated.getVars( self )
#        abMgr = self.__conf.getAbstractMgr()
#
#        vars["startDate"] = abMgr.getStartSubmissionDate().strftime("%A %d %B %Y")
#        vars["endDate"] = abMgr.getEndSubmissionDate().strftime("%A %d %B %Y")
#
#        typeList = ""
#        for type in self._conf.getContribTypeList():
#            typeList += "<input type=\"checkbox\" name=\"types\" value=\"%s\">%s<br>\n"%(type.getId(), type.getName())
#        vars["typeList"] = typeList
#
#        return vars

#class WCFARefereeList(WTemplated):
#
#    def __init__( self, conf ):
#        self.__conf = conf
#
#    def getVars( self ):
#        vars = WTemplated.getVars(self)
#        vars["refereeTable"] = "%s"%WPrincipalTable().getHTML( self.__conf.getAbstractMgr().getRefereeList(), self.__conf, vars["addRefereeURL"], vars["removeRefereeURL"] )
#        return vars

class WTabControl( WTemplated ):
    _unSelTabCls="Unselected"
    _selTabCls="Selected"

    def __init__( self, ctrl, accessWrapper, **params ):
        self._tabCtrl = ctrl
        self._aw = accessWrapper

    def _getTabsHTML(self, tabCtrl=None,maxtabs=1):
        # TODO: Transport this to the template

        hasHiddenOptions = False
        optionsAreShown = self._aw.getUser() is not None and self._aw.getUser().getPersonalInfo().getTabAdvancedMode()

        if tabCtrl==None:
            tabCtrl = self._tabCtrl

        html = []

        # Which css class prefix to use
        tabClassPrefix = ""
        isSubTab = False

        addGradientDiv = True

        if tabCtrl.getLevel() % 2 == 0:
            tabClassPrefix = "tab"
            # If no sub tabs then add gradient
            if tabCtrl.getChild():
                addGradientDiv = False
        else:
            tabClassPrefix = "subTab"
            isSubTab = True

        ## Looking for the previous "not hidden and enabled" tab, before the active one.
        beforeActive = None
        for tab in tabCtrl.getTabList():
            if tab.isActive():
                break
            elif tab.isEnabled() and (not tab.isHidden() or optionsAreShown):
                beforeActive = tab
        ########
        for i in range(0, len(tabCtrl.getTabList())):
            tab = tabCtrl.getTabList()[i]

            if not tab.isEnabled():
                continue
            cls=self.__class__._unSelTabCls

            # Don't add the right border if in sub level and if last elemnt
            borderRight = ""
            if i == len(tabCtrl.getTabList()) -1 and isSubTab:
                borderRight = """ style="border-right: 0;" """

            caption = """<a href="%s"%s>%s</a>"""%(tab.getURL(), borderRight, \
                                                tab.getCaption().replace(" ","&nbsp;") )

            if tab.isActive():
                self._activeTab = tab
                cls=self.__class__._selTabCls

                if tab.getSubTabControl():
                    self._getTabsHTML(tab.getSubTabControl(), maxtabs)

            if (tab.isHidden()):
                hasHiddenOptions = True

                hiddenClass = ' hiddenTab'
            else:
                hiddenClass = ''

            html.append("""<li class="%s%s %s" onclick="window.location = '%s'" onmouseout="this.style.backgroundPosition = '0 -30px';" onmouseover="this.style.backgroundPosition = '0 0';">%s</li>"""%(tabClassPrefix, cls, hiddenClass, tab.getURL(), caption))
        if html!=[]:
            gradientDiv = ""
            if addGradientDiv:
                gradientDiv = """<div class="tabGradient"><div class="tabBorderGradient" style="float: left;"></div><div class="tabBorderGradient" style="float: right;"></div></div>"""

            cssClass = ""
            if tabCtrl.getLevel() == 0:
                cssClass = """ class="tabListContainer" """
            html.insert(0, """<div %s><ul id="tabList" class="%sList">""" %(cssClass, tabClassPrefix))
            html.append("""</ul>%s</div>""" % gradientDiv)

            self._tabsBars.append("".join(html))

            return True

        return False

    def _getTabs( self):
        self._tabsBars=[]

        self._getTabsHTML(tabCtrl=self._tabCtrl, maxtabs=len(self._tabCtrl.getTabList())+1)
        self._tabsBars.reverse()
        return "".join(self._tabsBars)

    def getHTML( self, body ):
        self._body = body
        return WTemplated.getHTML( self )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["cs"] = len(self._tabCtrl.getTabList())+1
        vars["body"] = self._body
        vars["tabItems"] = self._getTabs()

        return vars

#class WAbstractFilterCtrl( WTemplated ):
#
#    def __init__(self, conf, filter, sorter):
#        self._filter = filter
#        self._conf = conf
#        self._sorter = sorter
#
#    def getVars( self ):
#        vars = WTemplated.getVars(self)
#        abMgr = self._conf.getAbstractMgr()
#
#        trackFilter = "<option value=\"\">No filter</option>\n"
#        for track in self._conf.getTrackList():
#            selected = ""
#            if track.getId() == self._filter["track"]:
#                selected = "selected"
#            trackFilter += "<option value=\"%s\" %s>%s</option>\n"%(track.getId(), selected, track.getTitle())
#        vars["trackFilter"] = trackFilter
#
#        typeFilter = "<option value=\"\">No filter</option>\n"
#        for type in self._conf.getContribTypeList():
#            selected = ""
#            if type.getId() == self._filter["type"]:
#                selected = "selected"
#            typeFilter += "<option value=\"%s\" %s>%s</option>\n"%(type.getId(), selected, type)
#        vars["typeFilter"] = typeFilter
#
#        statusFilter = "<option value=\"\">No filter</option>\n"
#        for name in StatusName().getNameList():
#            selected = ""
#            if name == self._filter["status"]:
#                selected = "selected"
#            statusFilter += "<option value=\"%s\" %s>%s</option>\n"%(name, selected, name)
#        vars["statusFilter"] = statusFilter
#
#        fDay = "<option value=\"\"> </option>\n"
#        for i in range(1,32):
#            selected = ""
#            if self._filter["fromDate"] != None:
#                if i == self._filter["fromDate"].day:
#                    selected = "selected"
#            fDay += "<option value=\"%s\" %s>%s</option>\n"%(i, selected, i)
#        vars["fDay"] = fDay
#
#        fMonth = "<option value=\"\"> </option>\n"
#        month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
#        for i in range(1,13):
#            selected = ""
#            if self._filter["fromDate"] != None:
#                if i == self._filter["fromDate"].month:
#                    selected = "selected"
#            fMonth += "<option value=\"%s\" %s>%s</option>\n"%(i, selected, month[i-1])
#        vars["fMonth"] = fMonth
#
#        fYear = "<option value=\"\"> </option>\n"
#        for i in range(2000,2011):
#            selected = ""
#            if self._filter["fromDate"] != None:
#                if i == self._filter["fromDate"].year:
#                    selected = "selected"
#            fYear += "<option value=\"%s\" %s>%s</option>\n"%(i, selected, i)
#        vars["fYear"] = fYear
#
#
#
#        tDay = "<option value=\"\"> </option>\n"
#        for i in range(1,32):
#            selected = ""
#            if self._filter["toDate"] != None:
#                if i == self._filter["toDate"].day:
#                    selected = "selected"
#            tDay += "<option value=\"%s\" %s>%s</option>\n"%(i, selected, i)
#        vars["tDay"] = tDay
#
#        tMonth = "<option value=\"\"> </option>\n"
#        for i in range(1,13):
#            selected = ""
#            if self._filter["toDate"] != None:
#                if i == self._filter["toDate"].month:
#                    selected = "selected"
#            tMonth += "<option value=\"%s\" %s>%s</option>\n"%(i, selected, month[i-1])
#        vars["tMonth"] = tMonth
#
#        tYear = "<option value=\"\"> </option>\n"
#        for i in range(2000,2011):
#            selected = ""
#            if self._filter["toDate"] != None:
#                if i == self._filter["toDate"].year:
#                    selected = "selected"
#            tYear += "<option value=\"%s\" %s>%s</option>\n"%(i, selected, i)
#        vars["tYear"] = tYear
#
#
#
#        #sortList = ["title", "type", "modification date"]
#        selected = ""
#        if self._sorter["field"] == "title":
#            selected = "selected"
#        sortBy = "<option value=\"title\" %s>Title</option>\n"%selected
#        selected = ""
#        if self._sorter["field"] == "type":
#            selected = "selected"
#        sortBy += "<option value=\"type\" %s>Type</option>\n"%selected
#        selected = ""
#        if self._sorter["field"] == "modification date":
#            selected = "selected"
#        sortBy += "<option value=\"modification date\" %s>Modification date</option>\n"%selected
#        selected = ""
#        if self._sorter["field"] == "status":
#            selected = "selected"
#        sortBy += "<option value=\"status\" %s>Status</option>\n"%selected
#        selected = ""
#
#        if self._sorter["direction"] == "desc":
#            vars["ascChecked"] = ""
#            vars["descChecked"] = "checked"
#        else:
#            vars["ascChecked"] = "checked"
#            vars["descChecked"] = ""
#
#        vars["sortBy"] = sortBy
#
#
#        return vars
#
#class WSubTrackCreation( WTemplated ):
#
#    def __init__( self, track ):
#        self.__track = track
#
#    def getVars( self ):
#        vars = WTemplated.getVars(self)
#        vars["title"], vars["description"] = "", ""
#        vars["locator"] = self.__track.getLocator().getWebForm()
#        return vars

#class WSetLogo( WTemplated ):
#
#    def __init__( self, conference ):
#        self.__conf = conference
#
#    def getVars( self ):
#        vars = WTemplated.getVars( self )
#        vars["confTitle"] = self.__conf.getTitle()
#
#        return vars

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
            "options":  _("""<input type="radio" name="submitterRole" value="primaryAuthor"> _("Primary author")<br>
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
            "options":  _("""<input type="checkbox" name="submitterRole" value="speaker"> _("Speaker")
                            """), \
            "table_width": "180px" \
          }
        return wc.getHTML(p)

class WSelectionBoxSubmitter:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  _(""" _("Please check the box if you want to add them as submitters"):<br><br><i><font color=\"black\"><b> _("Note"): </b></font> _("If this person is not already a user they will be sent an email asking them to create an account. After their registration the user will automatically be given submission rights").</i><br>"""),\
            "options":  _("""<input type="checkbox" name="submissionControl" value="speaker"> _("Add as submitter")
                        """)
          }
        return wc.getHTML(p)

class WSelectionBoxConveners:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description": _("Please make your selection if you want to add the result/s directly to the role of session Convener:"),\
            "options":  _("""<input type="checkbox" name="userRole" value="convener"> _("Add as convener")
                        """)
          }
        return wc.getHTML(p)

class WSelectionBoxConvToManager:

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  _(""" _("Please check the box if you want to add them as manager/s"):<br><br><i><font color=\"black\"><b> _("Note"): </b></font>_("If this person is not already an Indico user they will be sent an email asking them to create an account. After their registration the user will automatically be given session manager rights").</i><br>"""),\
            "options":  _("""<input type="checkbox" name="userRole" value="convener"> _("Add as session manager")
                        """)
          }
        return wc.getHTML(p)


class WSelectionBoxCloneLecture :

    def getHTML(self):
        wc=WSelectionBox()
        p={
            "description":  _("Please check the boxes indicating which elements of the lecture you want to clone"),\
            "options":  _("""<input type="checkbox" name="cloneDetails" id="cloneDetails" checked="1" disabled="1" value="1">  _("Event details")
                          <input type="checkbox" name="cloneMaterials" id="cloneMaterials" value="1" >  _("Attached materials")
                          <input type="checkbox" name="cloneAccess" id="cloneAccess" value="1" >  _("Access and management privileges")
                        """)
          }
        return wc.getHTML(p)


class WUserSelection(WTemplated):


    def __init__( self, searchURL, multi=True, addTo=0, forceWithoutExtAuth=False):
        self._title =  _("Search for users")
        self._searchURL = searchURL
        self._forceWithoutExtAuth = forceWithoutExtAuth
        self._multi = multi # for multiple selection
        #addTo=0: do not show any selection box.
        #addTo=1: show selection box to add submitter as primary author, coauthor or speaker.
        #addTo=2: show selection box to add primary author, coauthor or speaker as submitter.
        #addTo=3: show selection box to add session managers as session conveners
        #addTo=4: show selection box to add submitter as speaker. This is just for meetings
        self._addTo=addTo

    def _performSearch( self, criteria, exact=0 ):
        ah = user.AvatarHolder()
        res = ah.match(criteria, exact=exact, forceWithoutExtAuth=self._forceWithoutExtAuth)
        return res

    def setTitle( self, newTitle ):
        self._title = newTitle.strip()

    def _getPassingParams( self, params ):
        l = []
        for p in params.keys():
            if p in ["firstname", "surname", "organisation", "email", "groupname","exact","searchExt", 'selectedPrincipals']:
                continue
            l.append( """<input type="hidden" name="%s" value="%s">\n"""%(p, \
                                                                params[p] ) )
        return "\n".join( l )

    def _filterParams( self, params ):
        pars = copy( params )
        self._action = "show"
        if pars.has_key("action"):
            self._action = pars["action"].strip()
            del pars["action"]
        return pars

    def _create( self, params ):
        pass
        #a = user.Avatar()
        #a.setName( params["firstname"] )
        #a.setSurName( params["surname"] )
        #a.setEmail( params["email"] )
        #a.setOrganisation( params["organisation"] )
        #user.AvatarHolder().add( a )

    def _normaliseListParam( self, param ):
        if not isinstance(param, list):
                return [ param ]
        return param

    def getHTML( self, params ):
        self._cancelURL = params.get("addURL","")
        pars = self._filterParams( params )
        self._passingParams = self._getPassingParams( pars )
        self._msg = ""
        if self._action == _("create"):
            try:
                self._create( pars )
            except UserError,e:
                self._msg = str(e)#"User not created. The email address is already used."
            self._action = _("search")
        return WTemplated.getHTML( self, pars )

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["usericon"]=quoteattr(str(Config.getInstance().getSystemIconURL("user" )))
        vars["firstName"] = vars.get("firstname", "")
        vars["surName"] = vars.get("surname", "")
        vars["email"] = vars.get("email", "")
        vars["organisation"] = vars.get("organisation", "")
        if "WPtitle" not in vars or vars["WPtitle"].strip() == "":
            vars["WPtitle"] = self._title
        vars["params"] = self._passingParams
        vars["addURL"] = urlHandlers.UHUserSearchCreateExternalUser.getURL()
        #vars["createURL"] = urlHandlers.UHUserSearchCreateExternalUser.getURL()
        vars["postURL"] = self._searchURL
        vars["cancelURL"] = self._cancelURL
        vars["searchResultsTable"] = ""
        res=[]

        if self._action == _("search").strip():
            criteria = { "name": vars["firstName"], \
                         "surName": vars["surName"], \
                         "email" : vars["email"], \
                         "organisation": vars["organisation"] \
                       }
            if vars.has_key("groupname"):
                criteria["groupname"] = vars["groupname"]
            exact = 0
            if vars.get("exact",0) != 0:
                exact = 1
            res = self._performSearch( criteria, exact=exact )
            vars["searchResultsTable"] = WUserSearchResultsTable(self._multi).getHTML( res )
        vars["msg"] = ""
        if self._msg:
            vars["msg"] = """<tr>
        <td bgcolor="white" colspan="3" align="center">
            <font color="red">%s</font>
        </td>
    </tr>"""%self._msg
        sb=""
        if res!=[]:
            if self._addTo==1:
                sb=WSelectionBoxAuthors().getHTML()
            elif self._addTo==2:
                sb=WSelectionBoxSubmitter().getHTML()
            elif self._addTo==3:
                sb=WSelectionBoxConveners().getHTML()
            elif self._addTo==4:
                sb=WMSelectionBoxAuthors().getHTML()
        vars["selectionBox"]=sb
        vars["searchOptions"]=""
        authenticators = Config.getInstance().getAuthenticatorList()
        searchList = self._normaliseListParam(vars.get("searchExt",""))
        for auth in authenticators:
            if auth.lower() != "local":
                selected = ""
                if auth in searchList:
                    selected = "checked"
                vars["searchOptions"]+= _("""<input type="checkbox" name="searchExt" value="%s" %s> _("search %s database")<br>""") % (auth, selected, auth.upper())
        selected = ""
        if vars.get("exact","") != "":
            selected = "checked"
        vars["searchOptions"]+= _("""<input type="checkbox" name="exact" value="1" %s>  _("exact match")<br>""") % selected
        return vars

class WAuthorSearch(WUserSelection):

    def __init__(self, conf, searchURL, multi=True, addTo=0, forceWithoutExtAuth=False):
        _title =  _("Search Users and Authors")
        WUserSelection.__init__(self, searchURL, multi, addTo, forceWithoutExtAuth=forceWithoutExtAuth)
        self._conf = conf


    def _performSearch( self, criteria, exact=0  ):
        #this should go in the PrincipalHolder match method
        ah = user.AvatarHolder()
        resUsers = ah.match(criteria, exact=exact, forceWithoutExtAuth=self._forceWithoutExtAuth)
        auths = self._conf.getAuthorIndex()
        resAuths = auths.match(criteria, exact=exact)
        #crear una lista y devolver el resultado
        l = []
        emails = []
        for usr in resUsers:
            l.append(usr)
            emails.append(usr.getEmail())
        for author in resAuths :
            if author.getEmail() not in emails:
                l.append(author)
        return l

class WPrincipalSelection(WUserSelection):


    def _performSearch( self, criteria, exact=0 ):
        #this should go in the PrincipalHolder match method
        _title =  _("Search for users and groups")
        ah = user.AvatarHolder()
        resUsers = ah.match(criteria,exact=exact,forceWithoutExtAuth=self._forceWithoutExtAuth)
        gh = user.GroupHolder()
        resGroups = gh.match(criteria,forceWithoutExtAuth=self._forceWithoutExtAuth)
        l = []
        for item in resUsers:
            l.append(item)
        for item in resGroups:
            l.append(item)
        return l

    def getVars( self ):
        vars=WUserSelection.getVars(self)
        vars["usericon"]=quoteattr(str(Config.getInstance().getSystemIconURL("user" )))
        vars["groupicon"]=quoteattr(str(Config.getInstance().getSystemIconURL("group" )))
        vars["groupNICEicon"]=quoteattr(str(Config.getInstance().getSystemIconURL("groupNICE" )))
        vars["groupname"] = vars.get("groupname", "")
        return vars


class WComplexSelection(WUserSelection):


    def __init__(self, target, searchAction, forceWithoutExtAuth=False):
        _title = _("Search for users")
        WUserSelection.__init__(self, searchAction, forceWithoutExtAuth=forceWithoutExtAuth)
        try:
            self._conf = target.getConference()
        except:
            self._conf = None
        self._target = target

    def _performSearch( self, criteria, exact=0 ):
        #this should go in the PrincipalHolder match method
        ah = user.AvatarHolder()
        resUsers = ah.match(criteria, exact=exact, forceWithoutExtAuth=self._forceWithoutExtAuth)
        try:
            auths = self._conf.getAuthorIndex()
            resAuths = auths.match(criteria, exact=exact)
        except:
            resAuths = []
        l = []
        emails = []
        for usr in resUsers:
            l.append(usr)
            emails.append(usr.getEmail())
        for author in resAuths :
            if author.getEmail() not in emails:
                l.append(author)
        return l

    def getVars(self):
        vars = WUserSelection.getVars( self )
        vars["usericon"]=quoteattr(str(Config.getInstance().getSystemIconURL("user" )))
        return vars

class WCategoryComplexSelection(WComplexSelection):


    def __init__(self, category, searchAction, forceWithoutExtAuth=False):
        WComplexSelection.__init__(self, None, searchAction,forceWithoutExtAuth=forceWithoutExtAuth)
        self._category = category

    def _performSearch( self, criteria, exact=0 ):
        #this should go in the PrincipalHolder match method
        ah = user.AvatarHolder()
        resUsers = ah.match(criteria, exact=exact, forceWithoutExtAuth=self._forceWithoutExtAuth)
        return resUsers


class WNewPerson(WTemplated):

    def getVars( self ):
        vars = WTemplated.getVars( self )
        options = [" ",  _("Mr."),  _("Ms."),  _("Dr."),  _("Prof.")]
        titles = []
        titleValue = vars.get("titleValue", " ")

        for o in options :
            selected = ""
            if titleValue == o :
                selected = "selected"
            text = """<option value="%s" %s>%s</option>"""%(o, selected, o)
            titles.append(text)
        vars["titles"] = """
                        """.join(titles)

        if vars.get("disabledTitle", False) :
            vars["titles"] = """<input type="hidden" name="title" value="%s"></input>%s"""%(titleValue,titleValue)
        else :
            vars["titles"] = """
            <select name="title">
            %s
            </select>
            """%vars["titles"]

        if vars.get("disabledSurName", False) :
            vars["surName"] = """<input type="hidden" name="surName" value="%s"></input>%s"""%(vars["surNameValue"],vars["surNameValue"])
        else :
            vars["surName"] = """<input type="text" size="50" name="surName" value="%s" >"""%vars["surNameValue"]

        if vars.get("disabledName", False) :
            vars["name"] = """<input type="hidden" name="name" value="%s"></input>%s"""%(vars["nameValue"],vars["nameValue"])
        else :
            vars["name"] = """<input type="text" size="50" name="name" value="%s" >"""%vars["nameValue"]

        if vars.get("disabledAffiliation", False) :
            vars["affiliation"] = """<input type="hidden" name="affiliation" value="%s"></input>%s"""%(vars["affiliationValue"],vars["affiliationValue"])
        else :
            vars["affiliation"] = """<input type="text" size="50" name="affiliation" value="%s" >"""%vars["affiliationValue"]

        if vars.get("disabledEmail", False) :
            vars["email"] = """<input type="hidden" name="email" value="%s"></input>%s"""%(vars["emailValue"],vars["emailValue"])
        else :
            js=""
            if not vars.get("disabledRole", True) and vars["roleDescription"] == "Submitter":
                js="""onkeyup="if (!this.form.submissionControl.checked || this.value.length != 0) {this.form.warning_email.type='hidden';}else{this.form.warning_email.type='text';}">
                <input type="text"  size="50" value="Warning: if email is empty, submission rights will not be given" style="border: 0px none ; color: red;" id="warning_email"/"""
            vars["email"] = """<input type="text" size="50" name="email" value="%s" %s>"""%(vars["emailValue"],js)
        if vars.get("disabledAddress", False) :
            vars["address"] = """<input type="hidden" name="address" value="%s"></input>%s"""%(vars["addressValue"],vars["addressValue"])
        else :
            vars["address"] = """<textarea name="address" rows="5" cols="38" value="%s"></textarea>"""%vars["emailValue"]

        if vars.get("disabledPhone", False) :
            vars["phone"] = """<input type="hidden" name="phone" value="%s"></input>%s"""%(vars["phoneValue"],vars["phoneValue"])
        else :
            vars["phone"] = """<input type="text" size="50" name="phone" value="%s" >"""%vars["phoneValue"]

        if vars.get("disabledPhone", False) :
            vars["phone"] = """<input type="hidden" name="phone" value="%s"></input>%s"""%(vars["phoneValue"],vars["phoneValue"])
        else :
            vars["phone"] = """<input type="text" size="50" name="phone" value="%s" >"""%vars["phoneValue"]

        if vars.get("disabledFax", False) :
            vars["fax"] = """<input type="hidden" name="fax" value="%s"></input>%s"""%(vars["faxValue"],vars["faxValue"])
        else :
            vars["fax"] = """<input type="text" size="50" name="fax" value="%s" >"""%vars["faxValue"]
        if vars.get("disabledRole", True) :
            vars["role"] = ""
        else :
            vars["role"] = """
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">%s</span></td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">%s</td>
        </tr>"""%(vars["roleDescription"], vars["roleValue"])

        if vars.get("disabledNotice", True) :
            vars["notice"] = ""
        else :
            vars["notice"] = """
        <tr>
            <td nowrap class="titleCellTD"></td>
            <td bgcolor="white" width="100%%" valign="top" class="blacktext">%s</td>
        </tr>"""%vars["noticeValue"]

        if vars.get("msg","")!="":
            vars["msg"]=  _("""<table bgcolor="gray"><tr><td bgcolor="white">
                      <font size="+1" color="red"><b> _("You must enter a valid email address.")</b></font>

                       </td></tr></table>""")
            #raise vars["msg"]
        else: vars["msg"]=""
        return vars


class WAddPersonModule(WTemplated):

    def __addBasketPeople(self, peopleList):

        user = self._rh._getUser()

        # add extra options if the user is logged in
        if user:
            basket = user.getPersonalInfo().getBasket().getUsers()

            peopleList += """<option value=""></option>"""

            for userId in basket:
                peopleList += """<option class="favoriteItem" value="%s">%s</option>"""%(userId,basket[userId].getStraightFullName())

            return peopleList
        # just add nothing if the user is not logged in
        else:
            return ""

    def __init__(self,personType, displayName=""):
        self._personType = personType
        self._displayName = displayName

    def getVars( self ):
        vars = WTemplated.getVars( self )
        if self._personType is None or self._personType == "" :
            raise MaKaCError( _("'personType' must be set to use the Add Person Module"))
            return

        if self._displayName != "":
            vars["personName"] = self._displayName
        else:
            vars["personName"] = string.capwords("%s"%self._personType)

        # Add people from the users basket
        vars["personOptions"] = self.__addBasketPeople("")

        vars["personOptions"] += vars["%sOptions"%self._personType]

        vars["personChosen"] = "%sChosen"%self._personType

        vars["personDefined"] = vars["%sDefined"%self._personType]

        if vars["personOptions"] == """<option value=""> </option>""":
            vars["disabledAdd"] = "disabled"
        else:
            vars["disabledAdd"] = ""

        vars["personType"] = self._personType

        if vars.get("submission",None) is not None :
            vars["submissionButtons"] =  _("""
            <tr>
                <td colspan="4"><input type="submit" class="btn" value="_("Grant submission")" onClick="setAction(this.form,'Grant submission');"></td>
            </tr>
            <tr>
                <td colspan="4"><input type="submit" class="btn" value="_("Withdraw submission")" onClick="setAction(this.form,'Withdraw submission');"></td>
            </tr>""")
        else :
            vars["submissionButtons"] = ""
        return vars


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

            modifButton =  _("""<form action=%s method="POST">
                    <td align="center">
                        <input type="submit" class="btn" value="_("modify")">
                    </td>
                    </form>
                        """)%quoteattr(str(editCommentsURLGen(self._session)))
        return ( _("""
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
                buttonMod= _("""
                    <form action=%s method="POST">
                    <td valign="bottom">
                        <input type="submit" class="btn" value="_("modify")">
                    </td>
                    </form>
                        """)%quoteattr(str(commentEditURLGen(c)))
                buttonRem= _("""
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
            res.append( _("""<tr><td align=\"center\" style=\"color:black\"><br>--_("no internal comments")--<br><br></td></tr>"""))
        return "".join(res)

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["comments"]=self._getCommentsHTML(vars["commentEditURLGen"],vars["commentRemURLGen"])
        vars["newCommentURL"]=quoteattr(str(vars["newCommentURL"]))
        return vars


class WAbstractModMarkAsDup(WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def _getErrorHTML(self,msg):
        if msg.strip()=="":
            return ""
        return """
            <tr>
                <td align="center" colspan="2">
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
                """%self.htmlText(msg)

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["duplicateURL"]=quoteattr(str(vars["duplicateURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        vars["error"]=self._getErrorHTML(vars.get("errorMsg",""))
        return vars


class WAbstractModUnMarkAsDup(WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract


    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["unduplicateURL"]=quoteattr(str(vars["unduplicateURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        return vars


class WConfModAbstractEditData(WTemplated):

    def __init__(self,conference,abstractData):
        self._ad=abstractData
        self._conf=conference

    #def _getTitleItemsHTML(self,selected=""):
    #    titles=["", "Mr.", "Mrs.", "Miss.", "Prof.", "Dr."]
    #    res=[]
    #    for t in titles:
    #        sel=""
    #        if t==selected:
    #            sel=" selected"
    #        res.append("""<option value=%s%s>%s</option>"""%(quoteattr(t),sel,self.htmlText(t)))
    #    return "".join(res)

    def _getContribTypeItemsHTML(self):
        res=[ _("""<option value="">--_("not specified")--</option>""")]
        for cType in self._conf.getContribTypeList():
            selected=""
            if cType.getId()==self._ad.getContribTypeId():
                selected=" selected"
            res.append("""<option value=%s%s>%s</option>"""%(quoteattr(cType.getId()),selected,self.htmlText(cType.getName())))
        return "".join(res)

    def _getPrimaryAuthorsHTML(self):
        res=[]
        for author in self._ad.getPrimaryAuthorList():
            spk_checked=""
            if author.isSpeaker():
                spk_checked=" checked"
            tmp= _("""
                    <tr>
                        <td style="border-top:1px solid #777777; border-left:1px solid #777777">
                            <table align="center">
                                <tr>
                                    <td>
                                        <input type="submit" class="btn" name="upPA_%s" style="cursor:pointer; background-image : url(%s);background-repeat : no-repeat;background-color : transparent;border:0px" value="">
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <input type="submit" class="btn" name="downPA_%s" style="cursor:pointer; background-image : url(%s);background-repeat : no-repeat;background-color : transparent;border:0px" value="">
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <td style="border-top:1px solid #777777;" width="100%%">
                            <input type="checkbox" name="sel_prim_author" value=%s>
                            <input type="hidden" name="auth_prim_id" value=%s>
                        </td>
                        <td style="border-top:1px solid #777777;" width="100%%">
                            <table width="95%%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td nowrap>
                                         _("Title") <select name="auth_prim_title">%s</select>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Family name") <input type="text" size="40" name="auth_prim_family_name" value=%s>
                                         _("First name") <input type="text" size="30" name="auth_prim_first_name" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Affiliation") <input type="text" size="40" name="auth_prim_affiliation" value=%s>
                                         _("Email") <input type="text" size="39" name="auth_prim_email" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Phone") <input type="text" size="14" name="auth_prim_phone" value=%s>
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <td style="border-top:1px solid #777777;" valign="middle">
                            <input type="checkbox" name="auth_prim_speaker" value=%s%s> _("presenter")
                        </td>
                    </tr>
                    <tr><td colspan="3">&nbsp;</td></tr>
                """)%(author.getId(),\
                    Config.getInstance().getSystemIconURL("upArrow" ), \
                    author.getId(), \
                    Config.getInstance().getSystemIconURL( "downArrow" ), \
                    quoteattr(str(author.getId())),\
                    quoteattr(str(author.getId())),\
                    TitlesRegistry().getSelectItemsHTML(author.getTitle()), \
                    quoteattr(author.getFamilyName()),\
                    quoteattr(author.getFirstName()), \
                    quoteattr(author.getAffiliation()), \
                    quoteattr(author.getEmail()), \
                    quoteattr(author.getPhone()),\
                    quoteattr(str(author.getId())), spk_checked)
            res.append(tmp)
        return "".join(res)

    def _getCoAuthorsHTML(self):
        res=[]
        for author in self._ad.getCoAuthorList():
            spk_checked=""
            if author.isSpeaker():
                spk_checked=" checked"
            tmp= _("""
                    <tr>
                        <td style="border-top:1px solid #777777; border-left:1px solid #777777">
                            <table align="center">
                                <tr>
                                    <td>
                                        <input type="submit" class="btn" name="upCA_%s" style="cursor:pointer; background-image : url(%s);background-repeat : no-repeat;background-color : transparent;border:0px" value="">
                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <input type="submit" class="btn" name="downCA_%s" style="cursor:pointer; background-image : url(%s);background-repeat : no-repeat;background-color : transparent;border:0px" value="">
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <td style="border-top:1px solid #777777">
                            <input type="checkbox" name="sel_co_author" value=%s>
                            <input type="hidden" name="auth_co_id" value=%s>
                        </td>
                         <td style="border-top:1px solid #777777;">
                            <table color="gray">
                                <tr>
                                    <td nowrap>
                                         _("Title") <select name="auth_co_title">%s</select>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Family name") <input type="text" size="40" name="auth_co_family_name" value=%s>
                                         _("First name") <input type="text" size="30" name="auth_co_first_name" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Affiliation") <input type="text" size="40" name="auth_co_affiliation" value=%s>
                                         _("Email") <input type="text" size="39" name="auth_co_email" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Phone") <input type="text" size="14" name="auth_co_phone" value=%s>
                                    </td>
                                </tr>
                            </table>
                        </td>
                        <td style="border-top:1px solid #777777;" valign="middle">
                            <input type="checkbox" name="auth_co_speaker" value=%s%s> _("presenter")
                        </td>
                    </tr>
                    <tr><td colspan="3">&nbsp;</td></tr>
                """)%(author.getId(),\
                    Config.getInstance().getSystemIconURL( "upArrow" ), \
                    author.getId(),\
                    Config.getInstance().getSystemIconURL( "downArrow" ), \
                    quoteattr(str(author.getId())),\
                    quoteattr(str(author.getId())),\
                    TitlesRegistry().getSelectItemsHTML(author.getTitle()), \
                    quoteattr(author.getFamilyName()),\
                    quoteattr(author.getFirstName()), \
                    quoteattr(author.getAffiliation()), \
                    quoteattr(author.getEmail()), \
                    quoteattr(author.getPhone()),\
                    quoteattr(str(author.getId())), spk_checked)
            res.append(tmp)
        return "".join(res)

    def _getAdditionalFieldsHTML(self, ad):
        html = ""
        abfm = self._conf.getAbstractMgr().getAbstractFieldsMgr()
        for f in abfm.getFields():
            id = f.getId()
            value = ad.getOtherFieldValue(id)
            if not f.isActive():
                html += """<input type="hidden" name="%s" value=%s>""" % (id,quoteattr(value))
            else:
                caption = f.getName()
                maxLength = f.getMaxLength()
                isMandatory = f.isMandatory()
                if isMandatory:
                    mandatoryText = """<font color="red">*</font>"""
                else:
                    mandatoryText = ""
                nbRows = 10
                if maxLength > 0:
                    nbRows = int(int(maxLength)/85) + 1
                    maxLengthJS = """<small><br><input name="maxchars%s" size="4" value="%s" disabled> char. remain</small>""" % (id.replace(" ", "_"),maxLength)
                    maxLengthText = """ onkeyup="if (this.value.length > %s) {this.value = this.value.slice(0, %s);}; this.form.maxchars%s.value = %s - this.value.length;" onchange="if (this.value.length > %s) {this.value = this.value.slice(0, %s);}" """ % (maxLength,maxLength,id.replace(" ", "_"),maxLength,maxLength,maxLength)
                else:
                    maxLengthJS = maxLengthText = ""
                html+= _("""
                    <tr>
                        <td align="right" valign="top" class="titleCellTD">
                            <span class="titleCellFormat">
                            %s%s%s
                            </span>
                        </td>
                        <td valign="top">
                            <textarea name="%s" cols="85" rows="%s" %s>%s</textarea>
                        </td>
                    </tr>
                """) % ( mandatoryText, caption, maxLengthJS, id, nbRows, maxLengthText, value )
        return html

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["title"]=quoteattr(str(self._ad.getTitle()))
        vars["additionalFields"]=self._getAdditionalFieldsHTML(self._ad)
        vars["contribTypeItems"]=self._getContribTypeItemsHTML()
        vars["primaryAuthors"]=self._getPrimaryAuthorsHTML()
        vars["coAuthors"]=self._getCoAuthorsHTML()
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


class WConfModParticipEdit(WTemplated):

    def __init__(self,title="",part=None):
        self._part=part
        self._ctitle=title

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["caption"]=self.htmlText(self._ctitle)
        title,firstName,familyName="","",""
        affiliation,email,address,phone,fax="","","","",""
        if self._part is not None:
            title=self._part.getTitle()
            firstName=self._part.getFirstName()
            familyName=self._part.getFamilyName()
            affiliation=self._part.getAffiliation()
            email=self._part.getEmail()
            address=self._part.getAddress()
            phone=self._part.getPhone()
            fax=self._part.getFax()
        vars["titles"]=TitlesRegistry().getSelectItemsHTML(title)
        vars["surName"]=quoteattr(familyName)
        vars["name"]=quoteattr(firstName)
        vars["affiliation"]=quoteattr(affiliation)
        vars["email"]=quoteattr(email)
        vars["address"]=address
        vars["phone"]=quoteattr(phone)
        vars["fax"]=quoteattr(fax)
        if not vars.has_key("addToManagersList"):
            vars["addToManagersList"]=""
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

    def __init__(self,targetConf,aw,pageTitle="",targetDay=None):
        self._conf=targetConf
        self._title=pageTitle
        self._targetDay=targetDay
        self._aw = aw

    def _getErrorHTML(self,l):
        if len(l)>0:
            return """
                <tr>
                    <td colspan="2" align="center">
                        <br>
                        <table bgcolor="red" cellpadding="6">
                            <tr>
                                <td bgcolor="white" style="color: red">%s</td>
                            </tr>
                        </table>
                        <br>
                    </td>
                </tr>
                    """%"<br>".join(l)
        else:
            return ""

    def getVars( self ):
        vars=WTemplated.getVars(self)
        vars["conference"] = self._conf
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()
        vars["calendarIconURL"]=Config.getInstance().getSystemIconURL( "calendar" )
        vars["calendarSelectURL"]=urlHandlers.UHSimpleCalendar.getURL()
        vars["pageTitle"]=self.htmlText(self._title)
        vars["errors"]=self._getErrorHTML(vars.get("errors",[]))
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["title"]=quoteattr(str(vars.get("title","")))
        vars["description"]=self.htmlText(vars.get("description",""))
        if self._targetDay == None:
            sessionId = vars["sessionId"]
            session = self._conf.getSessionById(sessionId)
            refDate = session.getAdjustedStartDate()
        else:
            refDate=self._conf.getSchedule().getFirstFreeSlotOnDay(self._targetDay)
        endDate = None
        if refDate.hour == 23:
            refDate = refDate - timedelta(minutes=refDate.minute)
            endDate = refDate + timedelta(minutes=59)
        vars["sDay"]=str(vars.get("sDay",refDate.day))
        vars["sMonth"]=str(vars.get("sMonth",refDate.month))
        vars["sYear"]=str(vars.get("sYear",refDate.year))
        vars["sHour"]=str(vars.get("sHour",refDate.hour))
        vars["sMinute"]=str(vars.get("sMinute",refDate.minute))
        if not endDate:
            endDate=refDate+timedelta(hours=1)
        vars["eDay"]=str(vars.get("eDay",endDate.day))
        vars["eMonth"]=str(vars.get("eMonth",endDate.month))
        vars["eYear"]=str(vars.get("eYear",endDate.year))
        vars["eHour"]=str(vars.get("eHour",endDate.hour))
        vars["eMinute"]=str(vars.get("eMinute",endDate.minute))
        vars["durHour"]=quoteattr(str(vars.get("durHour",0)))
        vars["durMin"]=quoteattr(str(vars.get("durMin",20)))
        vars["defaultInheritPlace"]="checked"
        vars["defaultDefinePlace"]=""

        if vars.get("convenerDefined",None) is None :
            sessionId = vars["sessionId"]
            session = self._conf.getSessionById(sessionId)
            html = []
            for convener in session.getConvenerList() :
                text = """
                 <tr>
                     <td width="5%%"><input type="checkbox" name="%ss" value="%s"></td>
                     <td>&nbsp;%s</td>
                 </tr>"""%("convener",convener.getId(),convener.getFullName())
                html.append(text)
            vars["definedConveners"] = """
                                         """.join(html)
        if vars.get("locationAction","")=="define":
            vars["defaultInheritPlace"]=""
            vars["defaultDefinePlace"]="checked"
        vars["confPlace"]=""
        confLocation=self._conf.getConference().getLocation()
        if confLocation:
            vars["confPlace"]=self.htmlText(confLocation.getName())
        vars["locationName"]=quoteattr(str(vars.get("locationName","")))
        vars["locationAddress"]=self.htmlText(vars.get("locationAddress",""))
        vars["defaultInheritRoom"]=""
        vars["defaultDefineRoom"]=""
        vars["defaultExistRoom"]=""
        if vars.get("roomAction","")=="inherit":
            vars["defaultInheritRoom"]="checked"
            roomName = ""
        elif vars.get("roomAction","")=="define":
            vars["defaultDefineRoom"]="checked"
            roomName = vars.get( "bookedRoomName" )  or  vars.get("roomName","")
        elif vars.get("roomAction","")=="exist":
            vars["defaultExistRoom"]="checked"
            roomName = vars.get("exists", "") or vars.get("roomName","")
        else:
            vars["defaultInheritRoom"]="checked"
            roomName = ""


        vars["confRoom"]=""
        rx=[]
        roomsexist = self._conf.getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            sel=""
            if room==roomName:
                sel="selected=\"selected\""
            rx.append("""<option value=%s %s>%s</option>"""%(quoteattr(str(room)),
                        sel,self.htmlText(room)))
        vars ["roomsexist"] = "".join(rx)
        confRoom=self._conf.getConference().getRoom()
        if confRoom:
            vars["confRoom"]=self.htmlText(confRoom.getName())
        vars["roomName"]=quoteattr(str(roomName))

        vars["autoUpdate"]=""
        if not self._conf.getEnableSessionSlots():
            vars["disabled"] = "disabled"
        else:
            vars["disabled"] = ""
        if self._title.find("Ed") != -1 and self._conf.getEnableSessionSlots():
            vars["adjustSlots"]= _("""<input type="checkbox" name="slmove" value="1">  _("Also move timetable entries")""")
        else:
            vars["adjustSlots"]="""<input type="hidden" name="slmove" value="1">"""
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(self._conf)
        if wf != None:
            type = wf.getId()
        else:
            type = "conference"
        if type == "conference":
            vars["Type"]=WSessionModEditDataType().getHTML(vars)
            vars["Colors"]=WSessionModEditDataColors().getHTML(vars)
            vars["code"]=WSessionModEditDataCode().getHTML(vars)
        else:
            vars["Type"]=""
            vars["Colors"]=""
            vars["code"]=""
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
                    scheduled= _("""  _("and scheduled") (%s)""")%self.htmlText(contrib.getStartDate().strftime("%Y-%b-%d %H:%M"))
                wl.append( _("""
                        <li>%s-<i>%s</i>%s: is <font color="red"> _("already in session") <b>%s</b>%s</font></li>
                """)%(self.htmlText(contrib.getId()),
                        self.htmlText(contrib.getTitle()),
                        spkCaption,
                        self.htmlText(contrib.getSession().getTitle()),
                        scheduled))
            if (contrib.getSession() is None and \
                            self._targetSession is not None and \
                            contrib.isScheduled()):
                wl.append( _("""
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


class WConfTBDrawer:

    def __init__(self,tb):
        self._tb=tb

    def getHTML(self):
        if self._tb is None:
            return ""
        res=[]
        for item in self._tb.getItemList():
            if not item.isEnabled():
                continue
            res.append("""
                    <td align="right" nowrap><a href=%s><img src=%s alt=%s></a></td>
                        """%(quoteattr(str(item.getActionURL())),
                            quoteattr(str(item.getIcon())),
                            quoteattr(item.getCaption())))
        if res != []:
            return """
                <table cellpadding="0" cellspacing="1">
                    <tr>
                        %s
                    </tr>
                </table>
                    """%("".join(res))
        return ""

class WErrorMessage :

    def getHTML( self, vars ):

        if vars.get("errorMsg", None) is None :
            return ""
        if type(vars["errorMsg"]) != list:
            vars["errorMsg"]=[vars["errorMsg"]]
        for i in range(0,len(vars["errorMsg"])) :
            vars["errorMsg"][i] = """<span style="color: red;">"""+vars["errorMsg"][i]+"""</span>"""

        errorMsg = """
        """.join(vars["errorMsg"])

        html = """
                <div class="errorMsgBox">
                    %s
                </div>
               """%errorMsg

        return html

class WInfoMessage :

    def getHTML( self, vars ):
        if vars.get("infoMsg", None) is None :
            return ""
        if type(vars["infoMsg"]) != list:
            vars["infoMsg"]=[vars["infoMsg"]]
        for i in range(0,len(vars["infoMsg"])) :
            vars["infoMsg"][i] = """<span style="color: green;">"""+vars["infoMsg"][i]+"""</span>"""

        infoMsg = """
        """.join(vars["infoMsg"])

        html = """
                <div class="errorMsgBox">
                    %s
                </div>
        """%infoMsg

        return html

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

class WSubmitMaterialLink(WTemplated):

    def __init__(self, filenb, availMF):
        self._filenb=filenb
        self._availMF=availMF

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["itemNumber"]=self._filenb
        vars["materialTypeSelectFieldName"]="LinkType%s"%self._filenb
        vars["materialTypeInputFieldName"]="LinkTypeFT%s"%self._filenb
        vars["urlFieldName"]="link%s"%self._filenb
        l=[ _("""<option value="notype">--_("Select a type")--</option>""")]
        selMatType=vars.get("LinkType%s" % self._filenb,"")
        for mf in self._availMF:
            try:
                id = mf.getId()
                title = mf.getTitle()
            except:
                id = mf
                title = mf.capitalize()
            selected=""
            if id==selMatType:
                selected=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(\
                quoteattr(str(id)),selected,
                self.htmlText(title)))
        vars["matTypeItems"]="".join(l)
        if vars.get("LinkTypeFT%s" % self._filenb, "") != "":
            vars["materialTypeInputFieldValue"] = vars.get("LinkTypeFT%s" % self._filenb, "")
        else:
            vars["materialTypeInputFieldValue"] = ""
        if vars.get("link%s" % self._filenb, "") != "":
            vars["linkValue"] = vars.get("link%s" % self._filenb, "")
        else:
            vars["linkValue"] = ""
        return vars

class WSubmitMaterialFile(WTemplated):

    def __init__(self, filenb, availMF):
        self._filenb=filenb
        self._availMF=availMF

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["itemNumber"]=self._filenb
        vars["materialTypeSelectFieldName"]="FileType%s"%self._filenb
        vars["materialTypeInputFieldName"]="FileTypeFT%s"%self._filenb
        vars["fileFieldName"]="file%s"%self._filenb
        l=[ _("""<option value="notype">--_("Select a type")--</option>""")]
        selMatType=vars.get("FileType%s" % self._filenb,"")
        for mf in self._availMF:
            try:
                id = mf.getId()
                title = mf.getTitle()
            except:
                id = mf
                title = mf.capitalize()
            selected=""
            if id==selMatType:
                selected=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(\
                quoteattr(str(id)),selected,
                self.htmlText(title)))
        vars["matTypeItems"]="".join(l)
        if vars.get("FileTypeFT%s" % self._filenb, "") != "":
            vars["materialTypeInputFieldValue"] = vars.get("FileTypeFT%s" % self._filenb, "")
        else:
            vars["materialTypeInputFieldValue"] = ""
        if vars.get("FileNewName%s" % self._filenb, "") != "":
            vars["fileName"] = vars.get("FileNewName%s" % self._filenb)
        else:
            vars["fileName"] = ""
        vars["fileNewName"] = "FileNewName%s" % self._filenb
        return vars

class WMaterialListFile(WTemplated):

    def __init__(self, target):
        self._target=target

    def getVars(self):
        vars=WTemplated.getVars(self)
        try:
            name=self._target.getFileName()
        except:
            name=self._target.getURL()
        vars["fileName"]=name
        if self._target.getName()!="" and name!=self._target.getName():
            vars["fileName"]+=" (%s)" % self._target.getName()
        vars["fileActions"] = ""
        if isinstance(self._target, conference.Link):
            if vars["resourcesLinkModifHandler"]:
                vars["fileActions"] += """<a href="%s"><img src="%s" alt="Edit" style="margin-left: 5px; vertical-align:middle" /></a>"""%(vars["resourcesLinkModifHandler"].getURL(self._target), Config.getInstance().getSystemIconURL("file_edit"))
            if vars["resourcesLinkProtectHandler"]:
                vars["fileActions"] += """<a href="%s"><img src="%s" alt="Protect" style="margin-left: 5px; vertical-align:middle" /></a>"""%(vars["resourcesLinkProtectHandler"].getURL(self._target), Config.getInstance().getSystemIconURL("file_protect"))
        elif isinstance(self._target, conference.LocalFile):
            if vars["resourcesFileModifHandler"]:
                vars["fileActions"] += """<a href="%s"><img src="%s" alt="Edit" style="margin-left: 5px; vertical-align:middle" /></a>"""%(vars["resourcesFileModifHandler"].getURL(self._target), Config.getInstance().getSystemIconURL("file_edit"))
            if vars["resourcesFileProtectHandler"]:
                vars["fileActions"] += """<a href="%s"><img  alt="Protected" src="%s" style="margin-left: 5px; vertical-align:middle"/></a>"""%(vars["resourcesFileProtectHandler"].getURL(self._target), Config.getInstance().getSystemIconURL("file_protect"))
        vars["deleteIconURL"]=Configuration.Config.getInstance().getSystemIconURL("smallDelete")
        vars["delName"]="delete-%s-%s"% (self._target.getOwner().getId(),self._target.getId())
        try:
            vars["fileInfo"]="[%s bytes - %s]" % (self._target.getSize(),self._target.getCreationDate().strftime("%d.%m.%Y %H:%M:%S"))
        except:
            vars["fileInfo"]="[link]"
        if self._target.isProtected():
            vars["fileActions"] += """<img src="%s" alt="Protected" style="vertical-align: middle; border: 0;">""" % Config.getInstance().getSystemIconURL("protected")
        if isinstance(self._target, conference.Link):
            vars["fileAccessURL"]=quoteattr(str(self._target.getURL()))
        else:
            vars["fileAccessURL"]=quoteattr(str(urlHandlers.UHFileAccess.getURL(self._target)))
        return vars

class WMaterialListItem(WTemplated):

    def __init__(self, target, returnURL=""):
        self._target=target
        self._returnURL = returnURL.strip('"')

    def getVars(self):
        vars=WTemplated.getVars(self)
        deleteURL = None
        mf = None
        from MaKaC.webinterface.materialFactories import ConfMFRegistry,SessionMFRegistry,ContribMFRegistry
        if isinstance(self._target.getOwner(),conference.Conference):
            mf=ConfMFRegistry().get(self._target)
            deleteURL = urlHandlers.UHConferenceRemoveMaterials.getURL(self._target)
        elif isinstance(self._target.getOwner(),conference.Session):
            mf=SessionMFRegistry().get(self._target)
            deleteURL = urlHandlers.UHSessionRemoveMaterials.getURL(self._target)
        elif isinstance(self._target.getOwner(),conference.Contribution):
            mf=ContribMFRegistry().get(self._target)
            contrib=self._target.getOwner()
            deleteURL = urlHandlers.UHContributionRemoveMaterials.getURL(self._target)
        elif isinstance(self._target.getOwner(),conference.SubContribution):
            mf=ContribMFRegistry().get(self._target)
            deleteURL = urlHandlers.UHSubContributionRemoveMaterials.getURL(self._target)
        elif isinstance(self._target.getOwner(),conference.Category):
            deleteURL = urlHandlers.UHCategoryRemoveMaterial.getURL(self._target)
        if deleteURL:
            deleteURL.addParam("returnURL",self._returnURL)
        vars["materialName"] = self._target.getTitle()
        vars["materialActions"] = ""
        vars["materialActions"] += """<a href="%s" onClick="return confirm('Are you sure you want to delete all files of this type?');"><img src="%s" alt="Delete" style="margin-left: 5px; vertical-align:middle;"></a>""" % (str(deleteURL),Config.getInstance().getSystemIconURL("smallDelete"))
        if vars["materialModifHandler"]:
            vars["materialActions"] += """<a href="%s"><img src="%s" alt="Edit" style="margin-left: 5px; vertical-align:middle;"></a>""" % (urlHandlers.UHMaterialModification.getURL(self._target),Config.getInstance().getSystemIconURL("file_edit"))
        if vars["materialProtectHandler"]:
            vars["materialActions"] += """<a href="%s"><img src="%s" alt="Protect" style="margin-left: 5px; vertical-align:middle;" /></a>""" % (vars["materialProtectHandler"].getURL(self._target),Config.getInstance().getSystemIconURL("file_protect"))
        if self._target.isProtected():
            vars["materialActions"] += """<img src="%s" alt="Protected" style="margin-left: 5px; vertical-align: middle; border: 0;" />""" % Config.getInstance().getSystemIconURL("protected")
        vars["fileList"]=""
        for resource in self._target.getResourceList():
            vars["fileList"] += WMaterialListFile(resource).getHTML(vars)
        if mf is None:
            vars["materialIcon"]=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        else:
            vars["materialIcon"]=quoteattr(str(mf.getIconURL()))
        return vars


class WShowExistingMaterial(WTemplated):

    def __init__(self,target):
        self._target=target


    def getVars(self):
        vars=WTemplated.getVars(self)

        vars["materialModifHandler"] = vars.get("materialModifHandler", None)
        vars["materialProtectHandler"] = vars.get("materialProtectHandler", None)
        vars["resourcesFileModifHandler"] = vars.get("resourcesFileModifHandler", None)
        vars["resourcesFileProtectHandler"] = vars.get("resourcesFileProtectHandler", None)
        vars["resourcesLinkModifHandler"] = vars.get("resourcesLinkModifHandler", None)
        vars["resourcesLinkProtectHandler"] = vars.get("resourcesLinkProtectHandler", None)

        return vars

class WAddNewMaterial(WTemplated):

    def __init__(self,target,availMF):
        self._target=target
        self._availMF=availMF

    def _getErrorHTML(self,errorList):
        if len(errorList)==0:
            return ""
        return """
            <tr>
                <td>&nbsp;</td>
            </tr>
            <tr>
                <td colspan="2" align="center">
                    <table bgcolor="red">
                        <tr>
                            <td bgcolor="white">
                                <font color="red">%s</font>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td>&nbsp;</td>
            </tr>
                """%("<br>".join(errorList))

    def _getTargetName(self):
        if isinstance(self._target, conference.Contribution):
            return "Contribution"
        elif isinstance(self._target, conference.SubContribution):
            return "Subcontribution"
        elif isinstance(self._target, conference.Conference):
            return "Event"
        return ""

    def getVars(self):
        vars=WTemplated.getVars(self)
        nbFiles=int(vars.get("nbFiles",1))
        nbLinks=int(vars.get("nbLinks",1))
        vars["targetName"]=self._getTargetName()
        vars["targetId"]=self.htmlText(self._target.getId())
        vars["targetTitle"]=self.htmlText(self._target.getTitle())

        vars["selectNumberOfFiles"] = ""
        for i in range(1,10):
            if i == nbFiles:
                vars["selectNumberOfFiles"] += "<option selected>%s" % i
            else:
                vars["selectNumberOfFiles"] += "<option>%s" % i
        vars["fileSubmitForms"] = ""
        for i in range(1,nbFiles+1):
            vars["fileSubmitForms"] += WSubmitMaterialFile(i,self._availMF).getHTML(vars)
        vars["selectNumberOfLinks"] = ""
        for i in range(1,10):
            if i == nbLinks:
                vars["selectNumberOfLinks"] += "<option selected>%s" % i
            else:
                vars["selectNumberOfLinks"] += "<option>%s" % i
        vars["linkSubmitForms"] = ""
        for i in range(1,nbLinks+1):
            vars["linkSubmitForms"] += WSubmitMaterialLink(i,self._availMF).getHTML(vars)
        vars["conversion"]=""
        if Configuration.Config.getInstance().hasFileConverter():
            vars["conversion"]="""
                                <tr>
                                    <td class="titleCellTD"><span class="titleCellFormat">To PDF</span></td>
                                    <td><input type="checkbox" name="topdf" checked="checked">Automatic conversion to pdf (when applicable)? (PPT, DOC)</td>
                                </tr>
                                """
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        if vars["cancel"]:
            vars["CancelButton"] = """<input type="submit" name="CANCEL" value="cancel" class="btn">"""
        else:
            vars["CancelButton"] = ""
        return vars

class WSubmitMaterial(WTemplated):

    def __init__(self,target,availMF):
        self._target=target
        self._availMF=availMF

    def _getErrorHTML(self,errorList):
        if len(errorList)==0:
            return ""
        return """
            <tr>
                <td>&nbsp;</td>
            </tr>
            <tr>
                <td colspan="2" align="center">
                    <table bgcolor="red">
                        <tr>
                            <td bgcolor="white">
                                <font color="red">%s</font>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td>&nbsp;</td>
            </tr>
                """%("<br>".join(errorList))

    def _getTargetName(self):
        if isinstance(self._target, conference.Contribution):
            return "Contribution"
        elif isinstance(self._target, conference.SubContribution):
            return "Subcontribution"
        elif isinstance(self._target, conference.Conference):
            return "Event"
        return ""

    def getVars(self):
        vars=WTemplated.getVars(self)
        nbFiles=int(vars.get("nbFiles",1))
        nbLinks=int(vars.get("nbLinks",1))
        vars["targetName"]=self._getTargetName()
        vars["targetId"]=self.htmlText(self._target.getId())
        vars["targetTitle"]=self.htmlText(self._target.getTitle())
        vars["materialModifHandler"] = vars.get("materialModifHandler", None)
        vars["materialProtectHandler"] = vars.get("materialProtectHandler", None)
        vars["resourcesFileModifHandler"] = vars.get("resourcesFileModifHandler", None)
        vars["resourcesFileProtectHandler"] = vars.get("resourcesFileProtectHandler", None)
        vars["resourcesLinkModifHandler"] = vars.get("resourcesLinkModifHandler", None)
        vars["resourcesLinkProtectHandler"] = vars.get("resourcesLinkProtectHandler", None)
        vars["iconProtected"] = Config.getInstance().getSystemIconURL("protected")
        vars["iconDelete"] = Config.getInstance().getSystemIconURL("smallDelete")
        vars["iconKey"] = ""
        if vars["materialModifHandler"] or vars["resourcesFileModifHandler"] or vars["resourcesLinkModifHandler"]:
            vars["iconKey"] += _("""&nbsp;<img src=%s style="vertical-align:middle; margin: 1px;"> _("edit")""") % Config.getInstance().getSystemIconURL("file_edit")
        if vars["materialProtectHandler"] or vars["resourcesFileProtectHandler"] or vars["resourcesLinkProtectHandler"]:
            vars["iconKey"] += _("""&nbsp;<img src=%s style="vertical-align:middle; margin: 1px;"> _("protect")""") % Config.getInstance().getSystemIconURL("file_protect")
        vars["materialList"] = "<table>"
        materialList = self._target.getAllMaterialList()
        for material in materialList:
            vars["materialList"] += WMaterialListItem(material,vars["postURL"]).getHTML(vars)
        vars["materialList"] += "</table>"
        vars["selectNumberOfFiles"] = ""
        for i in range(1,10):
            if i == nbFiles:
                vars["selectNumberOfFiles"] += "<option selected>%s" % i
            else:
                vars["selectNumberOfFiles"] += "<option>%s" % i
        vars["fileSubmitForms"] = ""
        for i in range(1,nbFiles+1):
            vars["fileSubmitForms"] += WSubmitMaterialFile(i,self._availMF).getHTML(vars)
        vars["selectNumberOfLinks"] = ""
        for i in range(1,10):
            if i == nbLinks:
                vars["selectNumberOfLinks"] += "<option selected>%s" % i
            else:
                vars["selectNumberOfLinks"] += "<option>%s" % i
        vars["linkSubmitForms"] = ""
        for i in range(1,nbLinks+1):
            vars["linkSubmitForms"] += WSubmitMaterialLink(i,self._availMF).getHTML(vars)
        vars["conversion"]=""
        if Configuration.Config.getInstance().hasFileConverter():
            vars["conversion"]= _("""
                                <tr>
                                    <td nowrap class="titleCellTD"><span class="titleCellFormat">To PDF</span></td>
                                    <td align="left"><input type="checkbox" name="topdf" checked="checked"> _("Automatic conversion to pdf (when applicable)? (PPT, DOC)")</td>
                                </tr>
                                """)
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        if vars["cancel"]:
            vars["CancelButton"] =  _("""<input type="submit" name="CANCEL" value="_("cancel")" class="btn">""")
        else:
            vars["CancelButton"] = ""
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
        html.append( _("""
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
        html=[]
        rns = self._target.getReportNumberHolder().listReportNumbers()
        id = 0

        reportCodes = []

        for rn in rns:
            key = rn[0]
            number = rn[1]
            name=key
            if key in Configuration.Config.getInstance().getReportNumberSystems().keys():
                name=Configuration.Config.getInstance().getReportNumberSystems()[key]["name"]
                reportCodes.append((id, number, name))
            id+=1
        return reportCodes

    def _getSystems(self):
        html=[]
        rnsystems=Configuration.Config.getInstance().getReportNumberSystems()
        keys=rnsystems.keys()
        keys.sort()
        for system in keys:
            html.append("""
                        <option value="%s">%s</option>
                        """%(system, rnsystems[system]["name"] ) )
        return "".join(html)

    def getVars(self):
        vars = WTemplated.getVars(self)
        if self._type == "event":
            vars["deleteURL"]=quoteattr(str(urlHandlers.UHConfModifReportNumberRemove.getURL(self._target)))
            vars["addURL"]=quoteattr(str(urlHandlers.UHConfModifReportNumberEdit.getURL(self._target)))
        elif self._type == "contribution":
            vars["deleteURL"]=quoteattr(str(urlHandlers.UHContributionReportNumberRemove.getURL(self._target)))
            vars["addURL"]=quoteattr(str(urlHandlers.UHContributionReportNumberEdit.getURL(self._target)))
        else:
            vars["deleteURL"]=quoteattr(str(urlHandlers.UHSubContributionReportNumberRemove.getURL(self._target)))
            vars["addURL"]=quoteattr(str(urlHandlers.UHSubContributionReportNumberEdit.getURL(self._target)))
        vars["items"]=self._getCurrentItems()
        vars["repTypesSelectItems"]=self._getSystems()
        return vars

class WModifReportNumberEdit(WTemplated):

    def __init__(self, target, rns, type="event"):
        self._target=target
        self._rnSystem=rns
        self._type=type

    def getVars(self):
        vars=WTemplated.getVars(self)
        vars["reportNumber"]=""
        vars["reportNumberSystem"]=self._rnSystem
        name=self._rnSystem
        if self._rnSystem in Config.getInstance().getReportNumberSystems().keys():
            name=Config.getInstance().getReportNumberSystems()[self._rnSystem]["name"]
        vars["system"]=name
        if self._type == "event":
            vars["postURL"]=quoteattr(str(urlHandlers.UHConfModifReportNumberPerformEdit.getURL(self._target)))
        elif self._type == "contribution":
            vars["postURL"]=quoteattr(str(urlHandlers.UHContributionReportNumberPerformEdit.getURL(self._target)))
        else:
            vars["postURL"]=quoteattr(str(urlHandlers.UHSubContributionReportNumberPerformEdit.getURL(self._target)))
        return vars


class WHTMLEditorWrapper(WTemplated):

    def __init__(self, html, conf):
        self._html=html
        self._conf=conf

    def getVars(self):
        vars = WTemplated.getVars(self)
        vars["baseURL"]=Config.getInstance().getBaseURL()
        vars["imageUploadURL"]=urlHandlers.UHConfModifDisplayAddPageFile.getURL(self._conf)
        vars["imageBrowserURL"]=urlHandlers.UHConfModifDisplayAddPageFileBrowser.getURL(self._conf)
        vars["body"]=self._html
        return vars

# ============================================================================
# === ROOM BOOKING RELATED ===================================================
# ============================================================================
# 1. Freestanding
# 2. In the context of an event

from MaKaC.rb_reservation import ReservationBase, Collision, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.rb_tools import iterdays
from calendar import day_name
from MaKaC.rb_location import Location, CrossLocationFactory

class Bar:
    """
    Keeps data necessary for graphical bar on calendar.
    """
    PREBOOKED, PRECONCURRENT, UNAVAILABLE, CANDIDATE, PRECONFLICT, CONFLICT = xrange( 0, 6 )
    # I know this names are not wisely choosed; it's due to unexpected additions
    # without refactoring
    # UNAVAILABLE :   represents confirmed reservation (bright-red)
    # CANDIDATE:      represents new reservation (green)
    # CONFLICT:       overlap between candidate and confirmed resv. (dark red)
    # PREBOOKED:      represents pre-reservation (yellow)
    # PRECONFLICT:    represents conflict with pre-reservation (orange)
    # PRECONCURRENT:  conflicting pre-reservations

    def __init__( self, c, barType ):
        self.startDT = c.startDT
        self.endDT = c.endDT
        self.forReservation = c.withReservation
        self.type = barType

    def __cmp__( self, obj ):
        return cmp( self.type, obj.type )

class RoomBars:
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

class WRoomBookingRoomSelectList( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars['roomList'] = self._rh._roomList
        vars['locationRoom'] = self._rh._locationRoom

        return vars

class WRoomBookingRoomSelectList4SubEvents( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars['roomList'] = self._rh._roomList
        vars['locationRoom'] = self._rh._locationRoom

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

        websession = self._rh._websession

        vars["standalone"] = self._standalone

        vars["Location"] = Location
        vars["rooms"] = self._rh._rooms
        vars["possibleEquipment"] = self._rh._equipment
        vars["forNewBooking"] = self._rh._forNewBooking
        vars["eventRoomName"] = self._rh._eventRoomName

        vars["preview"] = False

        vars["startDT"] = websession.getVar( "defaultStartDT" )
        vars["endDT"] = websession.getVar( "defaultEndDT" )
        vars["startT"] = websession.getVar( "defaultStartDT" ).time().strftime( "%H:%M" )
        vars["endT"] = websession.getVar( "defaultEndDT" ).time().strftime( "%H:%M" )
        vars["repeatability"] = websession.getVar( "defaultRepeatability" )

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

        vars['youCannot'] = "javascript:alert( 'You cannot book this room' );"

        return vars

class WRoomBookingSearch4Bookings( WTemplated ):

    def __init__( self, rh ):
        self._rh = rh

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["today"] = datetime.now()
        vars["monthLater"] = datetime.now() + timedelta( 30 )
        vars["Location"] = Location
        vars["rooms"] = self._rh._rooms
        vars["repeatability"] = None

        vars["roomBookingBookingListURL"] = urlHandlers.UHRoomBookingBookingList.getURL( None )

        return vars

# 2. List of...

class WRoomBookingRoomList( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._standalone = standalone
        self._title = None
        try: self._title = self._rh._title;
        except: pass

    def getVars( self ):
        vars=WTemplated.getVars( self )

        vars["rooms"] = self._rh._rooms
        #vars["roomPhotoUH"] = urlHandlers.UHSendRoomPhoto
        vars["standalone"] = self._standalone
        vars["title"] = self._title

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

class WRoomBookingBookingList( WTemplated ): # Standalone version

    def __init__( self, rh ):
        self._rh = rh
        self._title = None
        try: self._title = self._rh._title;
        except: pass

    def _isOn(self, boolVal):
        if boolVal:
            return "on"
        else:
            return ""

    def getVars( self ):
        vars = WTemplated.getVars( self )
        rh = self._rh

        vars["reservations"] = rh._resvs

        #vars["smallPhotoUH"] = urlHandlers.UHSendRoomPhoto
        vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        vars["withPhoto"] = False
        vars["title"] = self._title
        vars["showRejectAllButton"] = rh._showRejectAllButton

        vars["prebookingsRejected"] = rh._prebookingsRejected
        vars["subtitle"] = rh._subtitle
        vars["description"] = rh._description
        yesterday = datetime.now() - timedelta( 1 )
        vars["yesterday"] = yesterday #datetime( dm.year, dm.month, dm.day, 0, 0, 1 )

        overload = ( len( rh._resvs ) > 300 ) or self._rh._overload

        ed = None
        sd = rh._resvEx.startDT.date()
        if rh._resvEx.endDT:
            ed = rh._resvEx.endDT.date()

        # autoCriteria - dates are calculated based on the next reservation
        if rh._autoCriteria:
            tmp = ReservationBase.findSoonest( rh._resvs, afterDT = yesterday )
            if tmp:
                tmp = tmp.getNextRepeating( afterDT = yesterday )
                if tmp and tmp.startDT.date() > sd:
                    sd = tmp.startDT
            if not ed:
                # one month of time span
                ed = sd + timedelta( 30 )

        # set the calendar dates as calculated
        calendarStartDT = datetime( sd.year, sd.month, sd.day, 0, 0, 1 )
        calendarEndDT = datetime( ed.year, ed.month, ed.day, 23, 59 )

        from MaKaC.rb_tools import formatDate

        if  calendarStartDT.date() == calendarEndDT.date():
            vars["periodName"] = "day"
            vars["verbosePeriod"] = formatDate(calendarStartDT)
        else:
            vars["periodName"] = "period"
            vars["verbosePeriod"] = "%s -> %s" % ( formatDate(calendarStartDT), formatDate(calendarEndDT) )
        vars["startD"] = formatDate(calendarStartDT)
        vars["endD"] = formatDate(calendarEndDT)

        # Data for previous/next URLs (it's about periods, not paging)
        newParams4Previous = rh._reqParams.copy()
        newParams4Next = rh._reqParams.copy()
        if rh._reqParams.has_key( 'autoCriteria' ):
            del newParams4Previous['autoCriteria']
            del newParams4Next['autoCriteria']
        if rh._reqParams.has_key( 'day' ):
            del newParams4Previous['day']
            del newParams4Next['day']


        startD = calendarStartDT.date()
        endD = calendarEndDT.date()

        if endD != startD:
            period = endD - startD

            prevStartD = startD - period
            prevEndD = startD - timedelta(1)

            nextStartD = endD + timedelta(1)
            nextEndD = endD + period
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

        vars["withPrevNext"] = True
        vars["prevURL"] = urlHandlers.UHRoomBookingBookingList.getURL( newParams = newParams4Previous )
        vars["nextURL"] = urlHandlers.UHRoomBookingBookingList.getURL( newParams = newParams4Next )

        # empty days are shown for "User bookings" and "User pre-bookings"
        # and for the calendar as well
        # but not for the booking search
        showEmptyDays = ( self._rh._ofMyRooms or \
                          (not self._rh._ofMyRooms and not self._rh._onlyMy) ) and \
                          not self._rh._search
        showEmptyRooms = showEmptyDays


        # Calendar related stuff ==========

        bars = []
        collisionsOfResvs = []

        # there's at least one reservation
        if len( rh._resvs ) > 0 and not overload:


            # Prepare the list of Collisions
            # (collision is just a helper object, it's not the best notion here)

            for r in rh._resvs:
                for p in r.splitToPeriods(endDT=calendarEndDT):
                    if p.startDT >= calendarStartDT and p.endDT <= calendarEndDT:
                        collisionsOfResvs.append( Collision( ( p.startDT, p.endDT ), r ) )

            if len( collisionsOfResvs ) > 500:
                overload = True
            else:

                # Translate collisions to Bars
                for c in collisionsOfResvs:
                    if c.withReservation.isConfirmed:
                        bars.append( Bar( c, Bar.UNAVAILABLE ) )
                    else:
                        bars.append( Bar( c, Bar.PREBOOKED ) )

                bars = barsList2Dictionary( bars )
                bars = addOverlappingPrebookings( bars )
                bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )

                rooms = []
                for r in rh._resvs:
                    rooms.append(r.room)

                #rooms = {}
                #for r in rh._resvs:
                #    rooms[r.room] = None
                #rooms = rooms.keys()

                #CrossLocationQueries.getRooms( location = self.location )
                if not self._rh._onlyMy:
                    rooms = self._rh._rooms

                bars = introduceRooms( rooms, bars, calendarStartDT, calendarEndDT, showEmptyDays = showEmptyDays, showEmptyRooms = showEmptyRooms )

                vars["Bar"] = Bar

                self.__sortUsingCriterion(rh._order, collisionsOfResvs)

        # we want to display every room, with or without reservation
        elif not overload:
            # initialize collision bars
            bars = {}
            bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )

            # insert rooms
            if not self._rh._onlyMy:
                    rooms = self._rh._rooms
            else:
                    rooms = []

            bars = introduceRooms( rooms, bars, calendarStartDT, calendarEndDT, showEmptyDays = showEmptyDays, showEmptyRooms = showEmptyRooms )


        vars["unrolledReservations"] = collisionsOfResvs
        vars["bars"] = bars
        vars["calendarStartDT"] = calendarStartDT
        vars["calendarEndDT"] = calendarEndDT
        vars["iterdays"] = iterdays
        vars['overload'] = overload
        vars["manyRooms"] = not self._rh._rooms or len(self._rh._rooms) > 1
        if not vars["manyRooms"]:
            vars["room"] = self._rh._rooms[0]
            vars["withConflicts"] = False
            bars = []
            for c in collisionsOfResvs:
                if c.withReservation.isConfirmed:
                    bars.append( Bar( c, Bar.UNAVAILABLE ) )
                else:
                    bars.append( Bar( c, Bar.PREBOOKED ) )
            bars = barsList2Dictionary( bars )
            bars = addOverlappingPrebookings( bars )
            bars = sortBarsByImportance( bars, calendarStartDT, calendarEndDT )
            vars["bars"] = bars

        return vars


    def __sortUsingCriterion(self, order, uresvs):

        if order == "" or order =="room":
            # standard sorting order (by room, and then date)
            uresvs.sort(lambda r1,r2: cmp(r1.withReservation.room.name,r2.withReservation.room.name))
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

def barsList2Dictionary( bars ):
    """
    Converts:
    list of bars => dictionary of bars, key = datetime, value = list of bars
    """
    h = {}
    for bar in bars:
        d = bar.startDT.date()
        if h.has_key( d ):
            h[d].append( bar )
        else:
            h[d] = [bar]
    return h

def addOverlappingPrebookings( bars ):
    """
    Adds bars representing overlapping pre-bookings.
    Returns new bars dictionary.
    """

    # For each day
    for dt in bars.keys():
        dayBars = bars[dt]

        # For each (prebooked) bar i
        for i in xrange( 0, len( dayBars ) ):
            bar = dayBars[i]
            if bar.type == Bar.PREBOOKED:

                # For each (prebooked) bar j
                for j in xrange( i+1, len( dayBars ) ):
                    collCand = dayBars[j]
                    if collCand.type == Bar.PREBOOKED:

                        # If there is an overlap, add PRECONCURRENT bar
                        over = overlap( bar.startDT, bar.endDT, collCand.startDT, collCand.endDT )
                        if over and bar.forReservation.room == collCand.forReservation.room:
                            collision = Collision( over, collCand.forReservation )
                            dayBars.append( Bar( collision, Bar.PRECONCURRENT ) )

        bars[dt] = dayBars # With added concurrent prebooking bars

    return bars

def sortBarsByImportance( bars, calendarStartDT, calendarEndDT ):
    """
    Moves conflict bars to the end of the list,
    so they will be drawn last and therefore be visible.

    Returns sorted bars.
    """
    for dt in bars.keys():
        dayBars = bars[dt]
        dayBars.sort()
        bars[dt] = dayBars

    for day in iterdays( calendarStartDT, calendarEndDT ):
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

def introduceRooms( rooms, dayBarsDic, calendarStartDT, calendarEndDT, showEmptyDays=True, showEmptyRooms=True ):
    # Input:
    # dayBarsDic is a dictionary date => [bar1, bar2, bar3, ...]
    #
    # Output:
    # newDayBarsDic is a dictionary date => [roomBars1, roomBars2, roomBars3, ...],
    # where roomBars is object JSON:{ room: RoomBase, bars: [bar1, bar2, bar3, ...] }
    import copy
    cleanRoomBarsList = getRoomBarsList( rooms )
    newDayBarsDic = {}

    s = ""
    for day in iterdays( calendarStartDT, calendarEndDT ):
        dayBars = dayBarsDic[day.date()]
        roomBarsDic = {}
        for bar in dayBars:
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


class WRoomBookingRoomStats( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._standalone = standalone

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["room"] = self._rh._room
        vars["standalone"] = self._standalone
        vars["period"] = self._rh._period
        vars["kpiAverageOccupation"] = str( int( round( self._rh._kpiAverageOccupation * 100 ) ) ) + "%"
        # Bookings
        vars["kbiTotalBookings"] = self._rh._totalBookings
        # Next 9 KPIs
        vars["stats"] = self._rh._booking_stats
        vars["statsURL"] = urlHandlers.UHRoomBookingRoomStats.getURL()
        return vars


class WRoomBookingRoomDetails( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._standalone = standalone

    def getVars( self ):
        vars = WTemplated.getVars( self )
        vars["room"] = self._rh._room
        goodFactory = Location.parse( self._rh._room.locationName ).factory
        attributes = goodFactory.getCustomAttributesManager().getAttributes( location = self._rh._room.locationName )
        vars["attrs"] = {}
        for attribute in attributes:
            if not attribute.get("hidden",False) or self._rh._getUser().isAdmin():
                vars["attrs"][attribute['name']] = self._rh._room.customAtts.get(attribute['name'],"")
        vars["config"] = Config.getInstance()
        #vars["roomPhoto"] = urlHandlers.UHSendRoomPhoto.getURL( self._rh._room.photoId, small = False )
        vars["standalone"] = self._standalone
        vars["actionSucceeded"] = self._rh._afterActionSucceeded
        vars["deletionFailed"] = self._rh._afterDeletionFailed

        vars["roomStatsUH"] = urlHandlers.UHRoomBookingRoomStats

        if self._standalone:
            vars["bookingFormUH"] = urlHandlers.UHRoomBookingBookingForm
            vars["modifyRoomUH"] = urlHandlers.UHRoomBookingRoomForm
            vars["deleteRoomUH"] = urlHandlers.UHRoomBookingDeleteRoom
            vars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            vars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails
            vars["conference"] = self._rh._conf
            vars["bookingFormUH"] = urlHandlers.UHConfModifRoomBookingBookingForm
            vars["modifyRoomUH"] = urlHandlers.UHRoomBookingRoomForm
            vars["deleteRoomUH"] = urlHandlers.UHRoomBookingDeleteRoom

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
                    bar.forReservation.setOwner( self._rh._conf )

        vars["calendarStartDT"] = calendarStartDT
        vars["calendarEndDT"] = calendarEndDT
        vars["bars"] = bars
        vars["iterdays"] = iterdays
        vars["day_name"] = day_name
        vars["Bar"] = Bar
        vars["withConflicts"] = False

        return vars

class WRoomBookingDetails( WTemplated ):

    def __init__( self, rh, standalone = False ):
        self._rh = rh
        self._resv = rh._resv
        self._standalone = standalone

    def getVars( self ):
        vars=WTemplated.getVars( self )
        vars["standalone"] = self._standalone
        vars["reservation"] = self._resv
        vars["config"] = Config.getInstance()
        #vars["smallPhotoUH"] = urlHandlers.UHSendRoomPhoto
        #vars["roomPhotoUH"] = urlHandlers.UHSendRoomPhoto
        vars["actionSucceeded"] = self._rh._afterActionSucceeded
        if self._rh._afterActionSucceeded:
            vars["title"] = self._rh._title
            vars["description"] = self._rh._description

        if self._standalone:
            vars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
        else:
            vars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails

        vars["bookMessage"] = "Book"
        if not self._resv.isConfirmed:
            vars["bookMessage"] = "PRE-Book"

        return vars

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
        else:
            vars["conf"] = self._rh._conf
            vars["saveBookingUH"] = urlHandlers.UHConfModifRoomBookingSaveBooking
            vars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            vars["calendarPreviewUH"] = urlHandlers.UHConfModifRoomBookingBookingForm

        vars["candResv"] = self._candResv
        vars["startDT"] = self._candResv.startDT
        vars["endDT"] = self._candResv.endDT
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

        if self._rh._formMode != FormMode.MODIF:
            bText = bookingMessage
        else:
            bText = "Save"

        vars["roomBookingRoomCalendar"] = WRoomBookingRoomCalendar( self._rh, self._standalone, buttonText=bText).getHTML( {} )

        return vars

class WRoomBookingConfirmBooking( WRoomBookingBookingForm ):

    def getVars( self ):
        vars = WTemplated.getVars( self )

        vars["candResv"] = self._candResv

        vars["standalone"] = self._standalone
        vars["formMode"] = self._rh._formMode
        vars["FormMode"] = FormMode
        vars["collisions"] = self._rh._collisions

        bookingMessage = "Book"
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook( user ) and not room.canBook( user ):
            bookingMessage = "PRE-Book"
        vars["bookingMessage"] = bookingMessage

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

        vars["calendarStartDT"] = calendarStartDT
        vars["calendarEndDT"] = calendarEndDT
        vars["bars"] = bars
        vars["iterdays"] = iterdays
        vars["day_name"] = day_name
        vars["Bar"] = Bar
        vars["room"] = room
        vars["buttonText"] = self._buttonText

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
        rooms.sort(key = lambda r: r.getFullName())

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

class WBaseSearchBox(WTemplated):

    def __init__(self, template='SearchBox', targetId=0):
        # overload the template
        WTemplated.__init__(self,template)
        self._targetId = targetId

    def getVars(self):
        vars = WTemplated.getVars( self )
        vars["searchAction"] = urlHandlers.UHSearch.getURL();
        vars['targetId'] = self._targetId
        vars['searchImg'] =  imgLogo=Configuration.Config.getInstance().getSystemIconURL( "search" )
        vars['categId'] = 0
        return vars

class WMiniSearchBox(WBaseSearchBox):

    def __init__(self, confId):
        WBaseSearchBox.__init__(self, template='MiniSearchBox',targetId = confId)

    def getVars(self):
        vars = WBaseSearchBox.getVars( self )
        return vars

class WMicroSearchBox(WBaseSearchBox):

    def __init__(self, confId):
        WBaseSearchBox.__init__(self, template='MicroSearchBox',targetId = confId)
        self._confId = confId

    def getVars(self):
        vars = WBaseSearchBox.getVars( self )
        vars["innerBox"] = WMiniSearchBox(self._confId).getHTML().replace('"', '\\"').replace("'", "\\'").replace("\n"," ")
        vars["closeIcon"] = quoteattr(str(Configuration.Config.getInstance().getSystemIconURL("remove")));
        return vars

class WCategorySearchBox(WBaseSearchBox):

    def __init__(self, categId = 0, optionsClass='arrowExpandIcon'):
        WBaseSearchBox.__init__(self, targetId = categId)
        self._categId = categId
        self._moreOptionsClass = optionsClass

    def getVars(self):
        vars = WBaseSearchBox.getVars( self )
        vars["categId"] = self._categId
        vars['moreOptionsClass'] = self._moreOptionsClass
        return vars

class WRootSearchBox(WBaseSearchBox):

    def __init__(self):
        # overload the template
        WBaseSearchBox.__init__(self,'RootSearchBox')

    def getVars(self):
        vars = WBaseSearchBox.getVars( self )
        vars["innerBox"] = WBaseSearchBox().getHTML()
        return vars

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
