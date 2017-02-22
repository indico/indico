# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import os
import urllib
import pkg_resources
from flask import session
from speaklater import _LazyString
from datetime import timedelta
from xml.sax.saxutils import escape, quoteattr

from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.common.contextManager import ContextManager
import MaKaC.common.TemplateExec as templateEngine

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.api import APIMode
from indico.modules.api import settings as api_settings
from indico.modules.core.settings import social_settings, core_settings
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.legacy import LegacyConference
from indico.modules.legal import legal_settings
from indico.util.i18n import i18nformat, get_current_locale, get_all_locales, _
from indico.util.date_time import format_date
from indico.util.signals import values_from_signal
from indico.util.string import truncate
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.menu import HeaderMenuEntry


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
        custom = core_settings.get('custom_template_set')
        if custom is not None:
            custom_tpl = '{}.{}.{}'.format(tplId, custom, extension)
            if os.path.exists(os.path.join(dir, custom_tpl)):
                return custom_tpl
        return '{}.{}'.format(tplId, extension)

    def _setTPLFile(self):
        """Sets the TPL (template) file for the object. It will try to get
            from the configuration if there's a special TPL file for it and
            if not it will look for a file called as the class name+".tpl"
            in the configured TPL directory.
        """
        cfg = Config.getInstance()

        # because MANY classes skip the constructor...
        tplDir = cfg.getTPLDir()
        if hasattr(self, '_for_module') and self._for_module:
            self.tplFile = pkg_resources.resource_filename(self._for_module.__name__,
                                                          'tpls/{0}.tpl'.format(self.tplId))
        else:
            self.tplFile = self._getSpecificTPL(tplDir, self.tplId)

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

        vars = self.getVars()
        vars['__rh__'] = self._rh
        vars['self_'] = self
        return templateEngine.render(self.tplFile, vars, self)

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
    def __init__(self, aw, locTZ="", isFrontPage=False, currentCategory=None, tpl_name=None, prot_obj=None):
        WTemplated.__init__(self, tpl_name=tpl_name)
        self._currentuser = aw.getUser()
        self._locTZ = locTZ
        self._aw = aw
        self._isFrontPage = isFrontPage
        self.__currentCategory = currentCategory
        # The object for which to show the protection indicator
        self._prot_obj = prot_obj

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

    def _get_protection_new(self, obj):
        if not obj.is_protected:
            return ['Public', _('Public')]
        else:
            networks = [x.name for x in obj.get_access_list() if x.is_network]
            if networks:
                return ['DomainProtected', _('{} network only').format('/'.join(networks))]
            else:
                return ["Restricted", _("Restricted")]

    def _getProtection(self, target):
        """
        Return a list with the status (Public, Protected, Restricted)
        and extra info (domain list).
        """
        if isinstance(target, LegacyConference):
            return self._get_protection_new(target.as_event)
        elif isinstance(target, db.m.Category):
            return self._get_protection_new(target)
        else:
            raise TypeError('Unexpected object: {}'.format(target))

    def getVars( self ):
        vars = WTemplated.getVars(self)

        vars["currentUser"] = self._currentuser

        config =  Config.getInstance()
        imgLogin = config.getSystemIconURL("login")

        vars["imgLogin"] = imgLogin
        vars["isFrontPage"] = self._isFrontPage
        vars["currentCategory"] = self.__currentCategory
        vars['prot_obj'] = self._prot_obj

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

        vars["title"] = core_settings.get('site_title')
        vars["organization"] = core_settings.get('site_organization')
        vars['roomBooking'] = Config.getInstance().getIsRoomBookingActive()
        vars['protectionDisclaimerProtected'] = legal_settings.get('network_protected_disclaimer')
        vars['protectionDisclaimerRestricted'] = legal_settings.get('restricted_disclaimer')

        # Build a list of items for the administration menu
        adminItemList = []
        if session.user and session.user.is_admin:
            adminItemList.append({'id': 'serverAdmin', 'url': url_for('core.dashboard'),
                                  'text': _("Server admin")})

        vars["adminItemList"] = adminItemList
        vars['extra_items'] = HeaderMenuEntry.group(values_from_signal(signals.indico_menu.send()))
        vars["getProtection"] = self._getProtection

        vars["show_contact"] = config.getPublicSupportEmail() is not None

        return vars


class WConferenceHeader(WHeader):
    """Templating web component for generating the HTML header for
        the conferences' web interface.
    """

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw
        WHeader.__init__(self, self._aw, prot_obj=self._conf, tpl_name='EventHeader')
        tzUtil = DisplayTZ(self._aw,self._conf)
        self._locTZ = tzUtil.getDisplayTZ()

    def getVars( self ):
        from indico.web.http_api.util import generate_public_auth_request

        vars = WHeader.getVars( self )
        vars["categurl"] = self._conf.as_event.category.url

        vars["conf"] = vars["target"] = self._conf

        vars["imgLogo"] = Config.getInstance().getSystemIconURL("miniLogo")
        vars["MaKaCHomeURL"] = self._conf.as_event.category.url

        # Default values to avoid NameError while executing the template
        styles = theme_settings.get_themes_for("conference")

        vars["viewoptions"] = [{'id': theme_id, 'name': data['title']}
                               for theme_id, data in sorted(styles.viewitems(), key=lambda x: x[1]['title'])]
        vars["SelectedStyle"] = ""
        vars["pdfURL"] = ""
        vars["displayURL"] = url_for('event.conferenceOtherViews', self._conf.as_event)

        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = False
        vars["showMoreButton"] = True
        vars["showExportToICal"] = True
        vars["showExportToPDF"] = False
        vars["showDLMaterial"] = True
        vars["showLayout"] = True

        vars["displayNavigationBar"] = layout_settings.get(self._conf, 'show_nav_bar')

        apiMode = api_settings.get('security_mode')

        vars["icsIconURL"] = str(Config.getInstance().getSystemIconURL("ical_grey"))
        vars["apiMode"] = apiMode
        vars["signingEnabled"] = apiMode in {APIMode.SIGNED, APIMode.ONLYKEY_SIGNED, APIMode.ALL_SIGNED}
        vars["persistentAllowed"] = api_settings.get('allow_persistent')
        user = self._aw.getUser()
        apiKey = user.api_key if user else None

        topURLs = generate_public_auth_request(apiKey, '/export/event/%s.ics' % self._conf.id)
        urls = generate_public_auth_request(apiKey, '/export/event/%s.ics' % self._conf.id,
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
    def __init__(self, aw, conf):
        self._conf = conf
        self._aw=aw
        WConferenceHeader.__init__(self, self._aw, conf)

    def getVars( self ):
        vars = WConferenceHeader.getVars( self )
        vars["categurl"] = self._conf.as_event.category.url

        # Dates Menu
        event = self._conf.as_event
        sdate = event.start_dt.astimezone(event.display_tzinfo)
        edate = event.end_dt.astimezone(event.display_tzinfo)
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
        if self._conf.as_event.sessions:
            selected = ""
            if vars.has_key("selectedSession"):
                selectedSession = vars["selectedSession"]
                if selectedSession == "all" or selectedSession == "":
                    selected = "selected"
            else:
                selectedSession = "all"
            sessions = [ i18nformat(""" <select name="showSession" onChange="document.forms[0].submit();" style="font-size:8pt;"><option value="all" %s>- -  _("all sessions") - -</option> """)%selected]
            for session in self._conf.as_event.sessions:
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
        if self._conf.as_event.sessions:
            if vars.has_key("detailLevel"):
                if vars["detailLevel"] == "session":
                    hideContributions = "checked"
                else:
                    hideContributions = ""
        # Save to session
        vars["hideContributions"] = hideContributions

        vars['printURL'] = url_for('event.conferenceOtherViews', event,
                                   showDate=vars.get('selectedDate') or 'all',
                                   showSession=vars.get('selectedSession') or 'all',
                                   fr='no',
                                   view=vars['currentView'])

        vars["printIMG"] = quoteattr(str(Config.getInstance().getSystemIconURL("printer")))
        vars["pdfURL"] = quoteattr(url_for('timetable.export_pdf', self._conf.as_event))
        vars["pdfIMG"] = quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["zipIMG"] = quoteattr(str(Config.getInstance().getSystemIconURL("smallzip")))

        return vars

class WMenuMeetingHeader( WConferenceHeader ):
    """Templating web component for generating the HTML header for
        the meetings web interface with a menu
    """
    def __init__(self, aw, conf):
        self._conf = conf
        self._aw=aw
        WHeader.__init__(self, self._aw, prot_obj=self._conf, tpl_name='EventHeader')
        tzUtil = DisplayTZ(self._aw,self._conf)
        self._locTZ = tzUtil.getDisplayTZ()

    def getVars( self ):
        vars = WConferenceHeader.getVars( self )

        vars["categurl"] = self._conf.as_event.category.url
        view_options = [{'id': tid, 'name': data['title']} for tid, data in
                        sorted(theme_settings.get_themes_for(vars["type"]).viewitems(), key=lambda x: x[1]['title'])]

        vars["viewoptions"] = view_options
        vars["SelectedStyle"] = theme_settings.themes[vars['currentView']]['title']
        vars["displayURL"] = self._rh._conf.as_event.url

        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = True
        vars["showExportToPDF"] = True
        vars["showDLMaterial"] = True
        vars["showLayout"] = True

        # Dates Menu
        event = self._conf.as_event
        sdate = event.start_dt.astimezone(event.display_tzinfo)
        edate = event.end_dt.astimezone(event.display_tzinfo)
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
        selected = ""
        if vars.has_key("selectedSession"):
            selectedSession = vars["selectedSession"]
            if selectedSession == "all" or selectedSession == "":
                selected = "selected"
        else:
            selectedSession = "all"
        sessions = [ i18nformat(""" <option value="all" %s>- -  _("all sessions") - -</option> """)%selected]
        for session_ in self._conf.as_event.sessions:
            selected = "selected" if unicode(session_.friendly_id) == selectedSession else ''
            title = session_.title
            if len(title) > 60:
                title = title[0:40] + u"..."
            sessions.append(""" <option value="%s" %s>%s</option> """ % (session_.friendly_id, selected,
                                                                         title.encode('utf-8')))
        vars["sessionsMenu"] = "".join(sessions)

        # Handle hide/show contributions option
        hideContributions = None;
        if self._conf.as_event.sessions:
            if vars.has_key("detailLevel"):
                if vars["detailLevel"] == "session":
                    hideContributions = "checked"
                else:
                    hideContributions = ""
        vars["hideContributions"] = hideContributions

        vars['printURL'] = url_for('event.conferenceOtherViews', event,
                                   showDate=vars.get('selectedDate') or 'all',
                                   showSession=vars.get('selectedSession') or 'all',
                                   detailLevel=vars.get('detailLevel') or 'all',
                                   fr='no',
                                   view=vars['currentView'])
        vars["pdfURL"] = url_for('timetable.export_pdf', self._conf.as_event)
        return vars


class WMenuSimpleEventHeader( WMenuMeetingHeader ):
    """Templating web component for generating the HTML header for
        the simple event' web interface with a menu
    """

    def getVars( self ):
        vars = WMenuMeetingHeader.getVars( self )
        # Setting the buttons that will be displayed in the header menu
        vars["showFilterButton"] = False
        vars["showExportToPDF"] = False

        vars["accessWrapper"] = self._aw
        return vars



class WFooter(WTemplated):
    """Templating web component for generating a common HTML footer for the
        web interface.
    """

    def __init__(self, tpl_name=None, isFrontPage=False):
        WTemplated.__init__(self, tpl_name)
        self._isFrontPage = isFrontPage

    def getVars( self ):
        from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase

        vars = WTemplated.getVars(self)
        vars["isFrontPage"] = self._isFrontPage
        event = getattr(self._rh, '_conf', None)
        vars['is_meeting'] = (event and event.as_event.type == 'meeting' and
                              not isinstance(self._rh, RHConferenceModifBase))

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
        self._event = conf.as_event

    def _gCalDateFormat(self, dtime):
        return dtime.strftime("%Y%m%dT%H%M%SZ")

    def getVars(self):
        v = WFooter.getVars(self)

        location = self._event.venue_name
        if self._event.room_name:
            location = u'{} ({})'.format(self._event.room_name, location)

        description = truncate(self._event.description, 1000).encode('utf-8')
        if description:
            description += '\n\n'

        description += self._event.short_external_url

        v['gc_params'] = urllib.urlencode({
            'action': 'TEMPLATE',
            'text': self._event.title.encode('utf-8'),
            'dates': "%s/%s" % (self._gCalDateFormat(self._event.start_dt),
                                self._gCalDateFormat(self._event.end_dt)),
            'details': description,
            'location': location.encode('utf-8'),
            'trp': False,
            'sprop': [self._event.external_url, 'name:indico']
        })

        social_settings_data = social_settings.get_all()
        v["shortURL"] = self._event.short_external_url
        v["showSocial"] = social_settings_data['enabled'] and layout_settings.get(self._conf, 'show_social_badges')
        v["social_settings"] = social_settings_data
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


class WConfTickerTapeDrawer(WTemplated):

    def __init__(self,conf, tz=None):
        self._conf = conf
        self._tz = tz

    def getSimpleText( self ):
        if layout_settings.get(self._conf, 'show_announcement'):
            return layout_settings.get(self._conf, 'announcement')


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
