# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.
import itertools
import os
import types
import exceptions
import urllib
import pkg_resources
import binascii
import uuid
from collections import OrderedDict
from flask import session, g
from lxml import etree
from pytz import timezone
from speaklater import _LazyString
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from xml.sax.saxutils import escape, quoteattr

from MaKaC.i18n import _
from MaKaC import conference
from MaKaC import schedule
from MaKaC.common import info
from MaKaC import domain
from MaKaC.webinterface import urlHandlers
from MaKaC.common.url import URL
from indico.core.config import Config
from MaKaC.conference import Conference, Category
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc, utctimestamp2date
from MaKaC.common import utils
from MaKaC.errors import MaKaCError
from MaKaC.common.ContextHelp import ContextHelp
from MaKaC.common.TemplateExec import truncateTitle
from MaKaC.common.fossilize import fossilize
from MaKaC.common.contextManager import ContextManager
from MaKaC.common.Announcement import getAnnoucementMgrInstance
import MaKaC.common.TemplateExec as templateEngine

from indico.core import signals
from indico.core.db import DBMgr
from indico.modules.api import APIMode
from indico.modules.api import settings as api_settings
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.util import preload_events
from indico.util.i18n import i18nformat, get_current_locale, get_all_locales
from indico.util.date_time import utc_timestamp, is_same_month, format_date
from indico.util.signals import values_from_signal
from indico.core.index import Catalog
from indico.web.flask.templating import get_template_module
from indico.web.menu import HeaderMenuEntry

MIN_PRESENT_EVENTS = 6
OPTIMAL_PRESENT_EVENTS = 10


class WTemplated():
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
        cfg = Config.getInstance()

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

        cfg = Config.getInstance()
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
        if not isinstance(param, (basestring, _LazyString)):
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
                return Config.getInstance().getDefaultTimezone()
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
        vars = WTemplated.getVars(self)

        vars["currentUser"] = self._currentuser

        config =  Config.getInstance()
        imgLogin = config.getSystemIconURL("login")

        vars["imgLogin"] = imgLogin
        vars["isFrontPage"] = self._isFrontPage
        vars["target"] = vars["currentCategory"] = self.__currentCategory

        current_locale = get_current_locale()
        vars["ActiveTimezone"] = session.timezone
        """
            Get the timezone for displaying on top of the page.
            1. If the user has "LOCAL" timezone then show the timezone
            of the event/category. If that's not possible just show the
            standard timezone.
            2. If the user has a custom timezone display that one.
        """
        vars["ActiveTimezoneDisplay"] = self._getTimezoneDisplay(vars["ActiveTimezone"])

        vars["SelectedLanguage"] = str(current_locale)
        vars["SelectedLanguageName"] = current_locale.language_name
        vars["Languages"] = get_all_locales()

        if DBMgr.getInstance().isConnected():
            vars["title"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTitle()
            vars["organization"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getOrganisation()
        else:
            vars["title"] = "Indico"
            vars["organization"] = ""

        vars["categId"] = self.__currentCategory.getId() if self.__currentCategory else 0

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars['roomBooking'] = Config.getInstance().getIsRoomBookingActive()
        vars['protectionDisclaimerProtected'] = minfo.getProtectionDisclaimerProtected()
        vars['protectionDisclaimerRestricted'] = minfo.getProtectionDisclaimerRestricted()
        #Build a list of items for the administration menu
        adminItemList = []
        if session.user and session.user.is_admin:
            adminItemList.append({'id': 'serverAdmin', 'url': urlHandlers.UHAdminArea.getURL(),
                                  'text': _("Server admin")})

        vars["adminItemList"] = adminItemList
        vars['extra_items'] = HeaderMenuEntry.group(values_from_signal(signals.indico_menu.send()))
        vars["getProtection"] = lambda x: self._getProtection(x)

        announcement_header = getAnnoucementMgrInstance().getText()
        vars["announcement_header"] = announcement_header
        vars["announcement_header_hash"] = binascii.crc32(announcement_header)
        vars["show_contact"] = config.getPublicSupportEmail() is not None

        return vars


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
        from indico.web.http_api.util import generate_public_auth_request

        vars = WHeader.getVars( self )
        vars["categurl"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])

        vars["conf"] = vars["target"] = self._conf;
        vars["urlICSFile"] = urlHandlers.UHConferenceToiCal.getURL(self._conf, detail = "events")

        vars["imgLogo"] = Config.getInstance().getSystemIconURL("miniLogo")
        vars["MaKaCHomeURL"] = urlHandlers.UHCategoryDisplay.getURL(self._conf.getOwnerList()[0])

        # Default values to avoid NameError while executing the template
        styles = theme_settings.get_themes_for("conference")

        vars["viewoptions"] = [{'id': theme_id, 'name': data['title']}
                               for theme_id, data in sorted(styles.viewitems(), key=lambda x: x[1]['title'])]
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
        if self._conf.canKeyModify():
            vars["usingModifKey"]=True
        vars["displayNavigationBar"] = layout_settings.get(self._conf, 'show_nav_bar')

        # This is basically the same WICalExportBase, but we need some extra
        # logic in order to have the detailed URLs
        apiMode = api_settings.get('security_mode')

        vars["icsIconURL"] = str(Config.getInstance().getSystemIconURL("ical_grey"))
        vars["apiMode"] = apiMode
        vars["signingEnabled"] = apiMode in {APIMode.SIGNED, APIMode.ONLYKEY_SIGNED, APIMode.ALL_SIGNED}
        vars["persistentAllowed"] = api_settings.get('allow_persistent')
        user = self._aw.getUser()
        apiKey = user.api_key if user else None

        topURLs = generate_public_auth_request(apiKey, '/export/event/%s.ics' % self._conf.getId())
        urls = generate_public_auth_request(apiKey, '/export/event/%s.ics' % self._conf.getId(),
                                            {'detail': 'contributions'})

        vars["requestURLs"] = {
            'publicRequestURL': topURLs["publicRequestURL"],
            'authRequestURL':  topURLs["authRequestURL"],
            'publicRequestDetailedURL': urls["publicRequestURL"],
            'authRequestDetailedURL':  urls["authRequestURL"]
        }

        vars["persistentUserEnabled"] = apiKey.is_persistent_allowed if apiKey else False
        vars["apiActive"] = apiKey is not None
        vars["userLogged"] = user is not None
        tpl = get_template_module('api/_messages.html')
        vars['apiKeyUserAgreement'] = tpl.get_ical_api_key_msg()
        vars['apiPersistentUserAgreement'] = tpl.get_ical_persistent_msg()

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
        if self._conf.canKeyModify():
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
                sid = session.friendly_id
                if sid == selectedSession:
                    selected = "selected"
                sessions.append(""" <option value="%s" %s>%s</option> """ % (sid, selected, session.title))
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

        urlCustPrint = urlHandlers.UHConferenceOtherViews.getURL(self._conf)
        urlCustPrint.addParam("showDate", vars.get("selectedDate", "all"))
        urlCustPrint.addParam("showSession", vars.get("selectedSession", "all"))
        urlCustPrint.addParam("fr", "no")
        urlCustPrint.addParam("view", vars["currentView"])
        vars["printURL"]=str(urlCustPrint)

        vars["printIMG"] = quoteattr(str(Config.getInstance().getSystemIconURL("printer")))
        urlCustPDF = urlHandlers.UHConfTimeTableCustomizePDF.getURL(self._conf)
        urlCustPDF.addParam("showDays", vars.get("selectedDate", "all"))
        urlCustPDF.addParam("showSessions", vars.get("selectedSession", "all"))
        vars["pdfURL"] = quoteattr(str(urlCustPDF))
        vars["pdfIMG"] = quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["zipIMG"] = quoteattr(str(Config.getInstance().getSystemIconURL("smallzip")))

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
        view_options = [{'id': tid, 'name': data['title']} for tid, data in
                        sorted(theme_settings.get_themes_for(vars["type"]).viewitems(), key=lambda x: x[1]['title'])]

        vars["viewoptions"] = view_options
        vars["SelectedStyle"] = theme_settings.themes[vars['currentView']]['title']
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
        while sdate.date() <= edate.date():
            iso_date = sdate.date().isoformat()
            selected = 'selected' if selectedDate == iso_date else ''
            dates.append('<option value="{}" {}>{}</option>'.format(iso_date, selected, format_date(sdate)))
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
        for session_ in self._conf.as_event.sessions:
            selected = "selected" if str(session_.id) == selectedSession else ''
            title = session_.title
            if len(title) > 60:
                title = title[0:40] + "..."
            sessions.append(""" <option value="%s" %s>%s</option> """%(session_.id, selected, title))
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

        return vars

class WMenuSimpleEventHeader( WMenuMeetingHeader ):
    """Templating web component for generating the HTML header for
        the simple event' web interface with a menu
    """

    def getVars( self ):
        vars = WMenuMeetingHeader.getVars( self )
        vars["confModif"] = """<a href=%s>manage</a>"""%quoteattr(str(urlHandlers.UHConfEnterModifKey.getURL(self._conf)))
        if self._conf.canKeyModify():
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
        from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase

        vars = WTemplated.getVars(self)
        vars["isFrontPage"] = self._isFrontPage
        event = getattr(self._rh, '_conf', None)
        vars['is_meeting'] = event and event.getType() == 'meeting' and not isinstance(self._rh, RHConferenceModifBase)

        if not vars.has_key("modificationDate"):
            vars["modificationDate"] = ""

        if not vars.has_key("shortURL"):
            vars["shortURL"] = ""
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
        v["showSocial"] = app_data.get('active', False) and layout_settings.get(self._conf, 'show_social_badges')
        v['conf'] = self._conf

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
        conf = target.event_new.as_legacy
        if user == "referee":
            path = [{"url": urlHandlers.UHConfModifListContribToJudge.getURL(conf), "title":_("Contributions list")}]
        if user == "reviewer":
            path = [{"url": urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL(conf), "title":_("Contributions list")}]
        if user == "editor":
            path = [{"url": urlHandlers.UHConfModifListContribToJudgeAsEditor.getURL(conf), "title":_("Contributions list")}]
        # TITLE AND TYPE
        itemType = type(target).__name__
        title = target.title
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
        vars["creator"] = ""
        vars["context"] = ""
        vars["imgGestionGrey"] = Config.getInstance().getSystemIconURL("gestionGrey")
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
        return fossilize(self.__target.getManagerList())

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
        inheriting = (ac.getAccessProtectionLevel() == 0) and (self._target.getOwner() is not None)
        domain_list = ac.getAnyDomainProtection() if inheriting else self._target.getDomainList()

        tpl_vars["inheriting"] = inheriting
        tpl_vars["domains"] = dict((dom, dom in domain_list)
                                   for dom in domain.DomainHolder().getList())
        tpl_vars["locator"] = self._target.getLocator().getWebForm()
        tpl_vars["target"] = self._target
        tpl_vars["event"] = event

        return tpl_vars


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
        params["systemIconWarning"] = Config.getInstance().getSystemIconURL("warning")
        return WTemplated.getHTML(self, params)


class WClosed(WTemplated):
    pass


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
        preload_events(itertools.chain(present, future))
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


class WAdminCreated(WTemplated):

    def __init__(self, av):
        self._av = av


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
        vars["useRoomBookingModule"] = Config.getInstance().getIsRoomBookingActive()
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


class WConfTickerTapeDrawer(WTemplated):

    def __init__(self,conf, tz=None):
        self._conf = conf
        self._tz = tz

    def getNowHappeningHTML( self, params=None ):
        if not layout_settings.get(self._conf, 'show_banner'):
            return None

        html = WTemplated.getHTML( self, params )

        if html == "":
            return None

        return html

    def getSimpleText( self ):
        if layout_settings.get(self._conf, 'show_announcement'):
            return layout_settings.get(self._conf, 'announcement')

    def getVars(self):
        vars = WTemplated.getVars( self )

        vars["nowHappeningArray"] = None
        if layout_settings.get(self._conf, 'show_banner'):
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
                if isinstance(ss.getSchedule(), schedule.PosterSlotSchedule):
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


class WReportNumbersTable(WTemplated):

    def __init__(self, target, type="event"):
        self._target=target
        self._type=type

    def _getCurrentItems(self):
        rns = self._target.getReportNumberHolder().listReportNumbers()
        reportCodes = []

        for rn in rns:
            key = rn[0]
            if key in Config.getInstance().getReportNumberSystems().keys():
                number = rn[1]
                reportNumberId="s%sr%s"%(key, number)
                name=Config.getInstance().getReportNumberSystems()[key]["name"]
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
        systems = Config.getInstance().getReportNumberSystems()
        vars["reportNumberSystems"]= dict([(system, systems[system]["name"]) for system in systems])
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
        return '<img src="{}" alt="{}" {} /> {}'.format(
            Config.getInstance().getSystemIconURL(imgId), imgInfo, attr, imgText)
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
        return '<a href="{}" {}><img src="{}" alt="{}" /> {}</a>'.format(
            url, attr, Config.getInstance().getSystemIconURL(imgId), imgInfo, imgText)
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
