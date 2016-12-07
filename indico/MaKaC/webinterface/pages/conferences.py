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
import posixpath
import re
from collections import OrderedDict
from datetime import datetime
from xml.sax.saxutils import quoteattr

from flask import session, render_template, request
from markupsafe import escape
from pytz import timezone
from sqlalchemy.orm import load_only

from indico.core.config import Config
from indico.modules import ModuleHolder
from indico.modules.auth.util import url_for_logout
from indico.modules.categories.util import get_visibility_options
from indico.modules.events.cloning import EventCloner
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.events.models.events import EventType, Event
from indico.util.date_time import format_date, format_datetime
from indico.util.i18n import i18nformat, _
from indico.util.string import encode_if_unicode, to_unicode
from indico.web.flask.util import url_for
from indico.web.menu import render_sidemenu

from MaKaC.common import info
from MaKaC.PDFinterface.base import PDFSizes
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.common.TemplateExec import render
from MaKaC.common.output import outputGenerator
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.common.utils import isStringHTML, formatDateTime
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface import wcomponents, urlHandlers
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.webinterface.common.tools import strip_ml_tags, escape_html
from MaKaC.webinterface.pages import main, base
from MaKaC.webinterface.pages.base import WPDecorated

LECTURE_SERIES_RE = re.compile(r'^part\d+$')


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

    def __init__(self, rh, conference, **kwargs):
        WPDecorated.__init__(self, rh, _protected_object=conference, _current_category=conference.as_event.category,
                             **kwargs)
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

    def getLogoutURL(self):
        return url_for_logout(str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))


class WPConferenceDisplayBase(WPConferenceBase):
    pass


class WPConferenceDefaultDisplayBase( WPConferenceBase):
    menu_entry_plugin = None
    menu_entry_name = None

    def get_extra_css_files(self):
        theme_url = get_css_url(self._conf.as_event)
        return [theme_url] if theme_url else []

    def getJSFiles(self):
        return (WPConferenceBase.getJSFiles(self) + self._includeJSPackage('MaterialEditor'))

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"modificationDate": format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),
                "subArea": self._getSiteArea()}

        cid = self._conf.getUrlTag().strip() or self._conf.getId()
        p["shortURL"] =  Config.getInstance().getShortEventURL() + cid

        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WConferenceHeader(self._getAW(), self._conf)
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(), \
                             "dark": True} )

    @property
    def sidemenu_option(self):
        if not self.menu_entry_name:
            return None
        name = build_menu_entry_name(self.menu_entry_name, self.menu_entry_plugin)
        entry = get_menu_entry_by_name(name, self.event)
        if entry:
            return entry.id

    def _applyConfDisplayDecoration( self, body ):
        drawer = wcomponents.WConfTickerTapeDrawer(self._conf, self._tz)
        frame = WConfDisplayFrame( self._getAW(), self._conf )

        frameParams = {
            "confModifURL": urlHandlers.UHConferenceModification.getURL(self._conf),
            "logoURL": self.logo_url,
            "currentURL": request.url,
            "simpleTextAnnouncement": drawer.getSimpleText(),
            'active_menu_entry_id': self.sidemenu_option
        }
        if self.event.has_logo:
            frameParams["logoURL"] = self.logo_url
        body = '''
            <div class="confBodyBox clearfix">
                <div class="mainContent">
                    <div class="col2">
                        {}
                    </div>
                </div>
            </div>
        '''.format(encode_if_unicode(body))
        return frame.getHTML(body, frameParams)

    def _getHeadContent(self):
        path = self._getBaseURL()
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        printCSS = '<link rel="stylesheet" type="text/css" href="{}/css/Conf_Basic.css?{}">'.format(path, timestamp)

        # Include MathJax

        return '\n'.join([
            printCSS,
            WConfMetadata(self._conf).getHTML(),                   # confMetadata
            render('js/mathjax.config.js.tpl'),                    # mathJax
            '\n'.join('<script src="{0}" type="text/javascript"></script>'.format(url)
                      for url in self._asset_env['mathjax_js'].urls())
        ])

    def _applyDecoration( self, body ):
        self.event = self._conf.as_event
        self.logo_url = self.event.logo_url if self.event.has_logo else None
        body = self._applyConfDisplayDecoration( body )
        return WPConferenceBase._applyDecoration(self, to_unicode(body))


class WConfMetadata(wcomponents.WTemplated):
    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        v = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        v['site_name'] = minfo.getTitle()
        v['fb_config'] = minfo.getSocialAppConfig().get('facebook', {})

        event = self._conf.as_event
        v['image'] = event.logo_url if event.has_logo else Config.getInstance().getSystemIconURL("logo_indico")
        v['description'] = strip_ml_tags(to_unicode(self._conf.getDescription())[:500].encode('utf-8'))
        return v


class WConfDisplayFrame(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf
        self.event = self._conf.as_event

    def getHTML(self, body, params):
        self._body = body
        return wcomponents.WTemplated.getHTML( self, params )

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["logo"] = ""
        if self.event.has_logo:
            vars["logoURL"] = self.event.logo_url
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
        vars["confLocation"] = self.event.venue_name
        vars["body"] = self._body
        vars["supportEmail"] = ""
        vars["supportTelephone"] = ""
        vars['menu'] = menu_entries_for_event(self.event)
        vars['support_info'] = self._conf.getSupportInfo()

        vars["bgColorCode"] = layout_settings.get(self._conf, 'header_background_color').replace("#", "")
        vars["textColorCode"] = layout_settings.get(self._conf, 'header_text_color').replace("#", "")

        vars["confId"] = self._conf.getId()
        vars["conf"] = self._conf
        return vars


class WConfDisplayMenu(wcomponents.WTemplated):

    def __init__(self, menu):
        wcomponents.WTemplated.__init__(self)
        self._menu = menu


class WConfDetailsBase( wcomponents.WTemplated ):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

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

        vars["address"] = None
        vars["room"] = None

        vars["attachments"] = self._conf.attached_items
        vars["conf"] = self._conf
        vars["event"] = self._conf.as_event

        info = self._conf.getContactInfo()
        vars["moreInfo_html"] = isStringHTML(info)
        vars["moreInfo"] = info
        vars["actions"] = ''
        vars["isSubmitter"] = self._conf.as_event.can_manage(session.user, 'submit')
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
    menu_entry_name = 'overview'

    def _getBody(self, params):

        wc = WConfDetails(self._getAW(), self._conf)
        pars = {"modifyURL": urlHandlers.UHConferenceModification.getURL(self._conf)}
        return wc.getHTML(pars)

    def _getFooter(self):
        wc = wcomponents.WEventFooter(self._conf)
        return wc.getHTML()


class WPXSLConferenceDisplay(WPConferenceBase):
    """
    Use this class just to transform to XML
    """
    menu_entry_name = 'overview'

    def __init__(self, rh, conference, view, type, params):
        WPConferenceBase.__init__(self, rh, conference)
        self._params = params
        self._view = view
        self._conf = conference
        self._type = type
        self._firstDay = params.get("firstDay")
        self._lastDay = params.get("lastDay")
        self._daysPerRow = params.get("daysPerRow")

    def _getFooter(self):
        """
        """
        return ""

    def _getHTMLHeader(self):
        return ""

    def _applyDecoration(self, body):
        """
        """
        return to_unicode(body)

    def _getHTMLFooter(self):
        return ""

    def _getBodyVariables(self):
        pars = {"modifyURL": urlHandlers.UHConferenceModification.getURL(self._conf),
                "cloneURL": urlHandlers.UHConfClone.getURL(self._conf)}

        pars.update({ 'firstDay' : self._firstDay, 'lastDay' : self._lastDay, 'daysPerRow' : self._daysPerRow })
        return pars

    def _getBody(self, params):
        body_vars = self._getBodyVariables()
        outGen = outputGenerator(self._getAW())
        if self._view in theme_settings.xml_themes:
            if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                includeContribution = 1
            else:
                includeContribution = 0
            template_path = os.path.join(Config.getInstance().getStylesheetsDir(), 'events',
                                         theme_settings.themes[self._view]['template'])
            body = outGen.getFormattedOutput(self._rh, self._conf, template_path,
                                             body_vars, 1, includeContribution, 1, 1,
                                             self._params.get("showSession", ""), self._params.get("showDate", ""))
            return body
        else:
            return _("Cannot find the %s stylesheet") % self._view


class WPTPLConferenceDisplay(WPXSLConferenceDisplay, object):
    """
    Overrides XSL related functions in WPXSLConferenceDisplay
    class and re-implements them using normal Indico templates.
    """

    def __init__(self, rh, conference, view, type, params):
        WPXSLConferenceDisplay.__init__(self, rh, conference, view, type, params)
        theme_id = self._view if self._view and self._view in theme_settings.themes else self._conf.as_event.theme
        self.theme_id = theme_id
        self.theme = theme_settings.themes[theme_id]

    def _getVariables(self, conf):
        event = conf.as_event
        wvars = {}
        wvars['INCLUDE'] = '../include'

        wvars['accessWrapper'] = accessWrapper = self._rh._aw
        wvars['category'] = event.category.title

        timezoneUtil = DisplayTZ(accessWrapper, conf)
        tz = timezoneUtil.getDisplayTZ()
        wvars['timezone'] = timezone(tz)

        attached_items = conf.attached_items
        folders = [folder for folder in attached_items.get('folders', []) if folder.title != "Internal Page Files"]

        lectures = []
        if event.series is not None and event.series.show_links:
            lectures = (Event.query.with_parent(event.series)
                        .filter(Event.id != event.id)
                        .options(load_only('series_pos', 'id'))
                        .order_by(Event.series_pos)
                        .all())

        wvars.update({
            'files': attached_items.get('files', []),
            'folders': folders,
            'lectures': lectures
        })

        return wvars

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

    def _getHTMLHeader( self ):
        return WPConferenceBase._getHTMLHeader(self)

    def _getHeadContent( self ):
        baseurl = self._getBaseURL()
        # First include the default Indico stylesheet
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        styleText = """<link rel="stylesheet" href="%s/css/%s?%d">\n""" % \
            (baseurl, Config.getInstance().getCssStylesheetName(), timestamp)

        theme_url = get_css_url(self._conf.as_event)
        if theme_url:
            link = '<link rel="stylesheet" type="text/css" href="{url}">'.format(url=theme_url)
            styleText += link

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

    def getPrintCSSFiles(self):
        theme_print_sass = (self._asset_env['themes_{}_print_sass'.format(self.theme_id)].urls()
                            if self.theme.get('print_stylesheet') else [])
        return WPConferenceBase.getPrintCSSFiles(self) + theme_print_sass

    def getCSSFiles(self):
        theme_sass = self._asset_env['themes_{}_sass'.format(self.theme_id)].urls() if self.theme['stylesheet'] else []
        return WPConferenceBase.getCSSFiles(self) + theme_sass

    def getJSFiles(self):
        modules = WPConferenceBase.getJSFiles(self)

        # TODO: find way to check if the user is able to manage
        # anything inside the conference (sessions, ...)
        modules += (self._includeJSPackage('Management') +
                    self._includeJSPackage('MaterialEditor') +
                    self._asset_env['modules_vc_js'].urls() +
                    self._asset_env['modules_event_display_js'].urls() +
                    self._asset_env['clipboard_js'].urls())
        return modules

    def _applyDecoration( self, body ):
        """
        """
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
                return to_unicode(WPrintPageFrame().getHTML({"content":body}))
        return WPConferenceBase._applyDecoration(self, body)

    def _getHTMLFooter( self ):
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
            return ""
        return WPConferenceBase._getHTMLFooter(self)


    def _getBody(self, params):
        """Return main information about the event."""

        if self._view != 'xml':
            kwargs = self._getVariables(self._conf)
            kwargs['isStringHTML'] = isStringHTML
        else:
            outGen = outputGenerator(self._rh._aw)
            varsForGenerator = self._getBodyVariables()
            kwargs = {}
            kwargs['xml'] = outGen._getBasicXML(self._conf, varsForGenerator, 1, 1, 1, 1)

        kwargs['theme_settings'] = self.theme.get('settings', {})
        return render_template(posixpath.join('events/display', self.theme['template']), event=self._conf.as_event,
                               conf=self._conf, **kwargs).encode('utf-8')


class WPrintPageFrame (wcomponents.WTemplated):
    pass


class WConfDisplayBodyBase(wcomponents.WTemplated):
    def _getTitle(self):
        entry = get_menu_entry_by_name(self._linkname, self._conf.as_event)
        return entry.localized_title


class WPConferenceModifBase(main.WPMainBase):

    _userData = ['favorite-user-ids']

    def __init__(self, rh, conference, **kwargs):
        conference = getattr(conference, 'as_legacy', conference)
        main.WPMainBase.__init__(self, rh, _current_category=conference.as_event.category, **kwargs)
        self._navigationTarget = self._conf = conference

    def getJSFiles(self):
        return (main.WPMainBase.getJSFiles(self) +
                self._includeJSPackage('Management') +
                self._includeJSPackage('MaterialEditor') +
                self._asset_env['modules_event_management_js'].urls())

    def _getSiteArea(self):
        return "ModificationArea"

    def _getHeader( self ):
        wc = wcomponents.WHeader(self._getAW(), currentCategory=self._current_category, prot_obj=self._protected_object)
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())) } )

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": True }
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _applyFrame(self, body):
        frame = wcomponents.WConferenceModifFrame(self._conf, self._getAW())

        params = {
            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL,
            "event": "Conference",
            "sideMenu": render_sidemenu('event-management-sidemenu', active_item=self.sidemenu_option,
                                        event=self._conf.as_event)
        }

        wf = self._rh.getWebFactory()
        if wf:
            params["event"] = wf.getName()
        return frame.getHTML(body, **params)

    def _getBody( self, params ):
        return self._applyFrame( self._getPageContent( params ) )

    def _getTabContent( self, params ):
        return "nothing"

    def _getPageContent( self, params ):
        return "nothing"


class WConfModifMainData(wcomponents.WTemplated):

    def __init__(self, conference, ct, rh):
        self._conf = conference
        self._ct = ct
        self._rh = rh

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["defaultStyle"] = self._conf.as_event.theme
        vars["visibility"] = self._conf.getVisibility()
        vars["dataModificationURL"]=quoteattr(str(urlHandlers.UHConfDataModif.getURL(self._conf)))
        vars["title"]=self._conf.getTitle()
        if isStringHTML(self._conf.getDescription()):
            vars["description"] = self._conf.getDescription()
        elif self._conf.getDescription():
            vars["description"] = self._conf.getDescription()
        else:
            vars["description"] = ""

        tz = self._conf.getTimezone()
        vars["timezone"] = tz
        vars["startDate"]=formatDateTime(self._conf.getAdjustedStartDate())
        vars["endDate"]=formatDateTime(self._conf.getAdjustedEndDate())
        vars["chairText"] = self.htmlText(self._conf.getChairmanText())
        if isStringHTML(self._conf.getContactInfo()):
            vars["contactInfo"]=self._conf.getContactInfo()
        else:
            vars["contactInfo"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._conf.getContactInfo()
        vars["supportEmailCaption"] = self._conf.getSupportInfo().getCaption()
        vars["supportEmail"] = i18nformat("""--_("not set")--""")
        if self._conf.getSupportInfo().hasEmail():
            vars["supportEmail"] = self.htmlText(self._conf.getSupportInfo().getEmail())
        #------------------------------------------------------
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
        vars['rbActive'] = Config.getInstance().getIsRoomBookingActive()
        vars["screenDates"] = "%s -> %s" % (ssdate, sedate)
        vars["timezoneList"] = TimezoneRegistry.getList()

        vars['styleOptions'] = {tid: data['title'] for tid, data in
                                theme_settings.get_themes_for(self._conf.getType()).viewitems()}
        return vars

class WPConferenceModificationClosed( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

    def _getPageContent( self, params ):
        from indico.modules.events.management import can_lock
        can_unlock = can_lock(self._conf, session.user)
        message = _("The event is currently locked so it cannot be modified.")
        if can_unlock:
            message += ' ' + _("If you unlock the event, you will be able to modify it again.")
        return wcomponents.WClosed().getHTML({"message": message,
                                              "postURL": url_for('event_management.unlock', self._conf),
                                              "showUnlockButton": can_unlock,
                                              "unlockButtonCaption": _("Unlock event")})


class WPConferenceModification( WPConferenceModifBase ):

    sidemenu_option = 'general'

    def __init__(self, rh, target, ct=None):
        WPConferenceModifBase.__init__(self, rh, target)
        self._ct = ct

    def _getPageContent( self, params ):
        wc = WConfModifMainData(self._conf, self._ct, self._rh)
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
        options = [(val or 999,
                    label,
                    'selected' if self._conf.getVisibility() == (val or 999) else '')
                   for val, label in get_visibility_options(self._conf.as_event)]
        return u'\n'.join(u'<option value="{}" {}>{}</option>'.format(val, selected, escape(label))
                          for val, label, selected in options)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        navigator = ""
        evt_type = self._conf.getType()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(self._conf.getTimezone())
        styleoptions = ""
        defStyle = self._conf.as_event.theme
        if defStyle not in theme_settings.themes:
            defStyle = ""
        for theme_id, theme_data in theme_settings.get_themes_for(evt_type).viewitems():
            if theme_id == defStyle or (defStyle == "" and theme_id == "static"):
                selected = "selected"
            else:
                selected = ""
            styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected, theme_data['title'])
        vars["conference"] = self._conf
        vars["useRoomBookingModule"] = Config.getInstance().getIsRoomBookingActive()
        vars["styleOptions"] = styleoptions
        vars['types'] = OrderedDict((t.legacy_name, t.title) for t in EventType)
        vars["title"] = quoteattr( self._conf.getTitle() )
        vars["description"] = self._conf.getDescription()
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
        vars["orgText"] = self._conf.getOrgText()
        vars["visibility"] = self._getVisibilityHTML()
        vars["shortURLTag"] = quoteattr( self._conf.getUrlTag() )
        vars["locator"] = self._conf.getLocator().getWebForm()
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


class WPConfModifToolsBase(WPConferenceModifBase):

    sidemenu_option = 'utilities'

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabPosters = self._tabCtrl.newTab("posters", _("Posters"), \
                urlHandlers.UHConfModifPosterPrinting.getURL(self._conf))
        self._tabBadges = self._tabCtrl.newTab("badges", _("Badges/Tablesigns"), \
                urlHandlers.UHConfModifBadgePrinting.getURL(self._conf))

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


class WPConfCloneConfirm(WPConferenceModifBase):

    def __init__(self, rh, conf, nbClones):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._nbClones = nbClones

    def _getPageContent(self, params):

        msg = _("This action will create {0} new events. Are you sure you want to proceed").format(self._nbClones)

        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfPerformCloning.getURL(self._conf)
        params = self._rh._getRequestParams()
        for key in params.keys():
            url.addParam(key, params[key])
        return wc.getHTML( msg, \
                        url, {}, True, \
                        confirmButtonCaption=_("Yes"), cancelButtonCaption=_("No"))


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


class WPConfClone(WPConferenceModifBase):

    def _getPageContent(self, params):
        p = WConferenceClone(self._conf)
        pars = {"cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
                "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
                "startTime": self._conf.getUnixStartDate(),
                "cloneOptions": EventCloner.get_form_items(self._conf.as_event).encode('utf-8')}
        return p.getHTML(pars)


class WConfMyStuff(WConfDisplayBodyBase):

    _linkname = 'my_conference'

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


class WPMyStuff(WPConferenceDefaultDisplayBase):
    menu_entry_name = 'my_conference'

    def _getBody(self,params):
        wc=WConfMyStuff(self._getAW(),self._conf)
        return wc.getHTML()


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
        dconf = info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
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
            dconf = info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
            templMan = conf.getBadgeTemplateManager()
            newId = templateId
            default_template = dconf.getBadgeTemplateManager().getTemplateById(baseTemplateId)
            default_template.clone(templMan, newId)
            # now, let's pretend nothing happened, and let the code
            # handle the template as if it existed before
            self.__new = False

    def _setActiveTab(self):
        self._tabBadges.setActive()

    def _getTabContent(self, params):
        wc = WConfModifBadgeDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()


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
        templates['global'] = (info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
                               .getPosterTemplateManager().getTemplates())
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
        templates = (info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
                     .getPosterTemplateManager().getTemplates())
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

    def __init__(self, rh, conf, **kwargs):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf, **kwargs)

        self._conf = conf
        self._cssTplsModule = ModuleHolder().getById("cssTpls")

    def _applyDecoration( self, body ):
        """
        """
        return "%s%s%s"%( self._getHeader(), body, self._getFooter() )

    def _getBody( self, params ):
        params['confId'] = self._conf.getId()
        params['conf'] = self._conf

        ###############################
        # injecting ConferenceDisplay #
        ###############################
        p = WPConferenceDisplay( self._rh, self._conf )
        p.event = self._conf.as_event
        p.logo_url = p.event.logo_url if p.event.has_logo else None
        params["bodyConf"] = p._applyConfDisplayDecoration(p._getBody(params))
        ###############################
        ###############################

        wc = WPreviewPage()
        return wc.getHTML(params)

    def _getHeadContent(self):
        path = Config.getInstance().getCssBaseURL()
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        printCSS = '<link rel="stylesheet" type="text/css" href="{}/Conf_Basic.css?{}">\n'.format(path, timestamp)

        if self._kwargs['css_url']:
            printCSS += '<link rel="stylesheet" type="text/css" href="{url}">'.format(url=self._kwargs['css_url'])
        return printCSS

    def get_extra_css_files(self):
        return []


class WPreviewPage( wcomponents.WTemplated ):
    pass
