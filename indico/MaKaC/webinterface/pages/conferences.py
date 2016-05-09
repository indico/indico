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

from flask import session, render_template, request
import os
import posixpath
import re

from datetime import datetime
from xml.sax.saxutils import quoteattr

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.conference as conference
import MaKaC.common.filters as filters
from MaKaC.common.utils import isStringHTML
import MaKaC.common.utils
import MaKaC.review as review
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.common.tools import strip_ml_tags, escape_html
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from MaKaC.common.output import outputGenerator
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.PDFinterface.base import PDFSizes
from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface.pages import main
from MaKaC.webinterface.pages import base
import MaKaC.common.info as info
from indico.util.i18n import i18nformat, _
from indico.util.date_time import format_date, format_datetime
from indico.util.string import safe_upper
from MaKaC.common.fossilize import fossilize
from indico.modules import ModuleHolder
from indico.modules.auth.util import url_for_logout
from indico.core.config import Config
from MaKaC.common.utils import formatDateTime
from MaKaC.common.TemplateExec import render, mako_call_template_hook

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.events.cloning import EventCloner
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.users.util import get_user_by_email
from indico.util.string import to_unicode
from indico.web.flask.util import url_for
from indico.web.menu import render_sidemenu

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
        WPDecorated.__init__(self, rh, **kwargs)
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
        wc = wcomponents.WConferenceHeader( self._getAW(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(), \
                             "dark": True} )

    @property
    def sidemenu_option(self):
        if not self.menu_entry_name:
            return None
        name = build_menu_entry_name(self.menu_entry_name, self.menu_entry_plugin)
        entry = get_menu_entry_by_name(name, self._conf)
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
        '''.format(body)
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
        minfo =  info.HelperMaKaCInfo.getMaKaCInfoInstance()

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
        vars['menu'] = menu_entries_for_event(self._conf)
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

    def getCSSFiles(self):
        return (WPConferenceDefaultDisplayBase.getCSSFiles(self)
                + self._asset_env['eventservices_sass'].urls()
                + self._asset_env['event_display_sass'].urls())

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
        wvars = {}
        wvars['INCLUDE'] = '../include'

        wvars['accessWrapper'] = accessWrapper = self._rh._aw
        if conf.getOwnerList():
            wvars['category'] = conf.getOwnerList()[0].getName()
        else:
            wvars['category'] = ''

        timezoneUtil = DisplayTZ(accessWrapper, conf)
        tz = timezoneUtil.getDisplayTZ()
        wvars['timezone'] = timezone(tz)

        attached_items = conf.attached_items
        lectures, folders = [], []

        for folder in attached_items.get('folders', []):
            if LECTURE_SERIES_RE.match(folder.title):
                lectures.append(folder)
            elif folder.title != "Internal Page Files":
                folders.append(folder)

        cmp_title_number = lambda x, y: int(x.title[4:]) - int(y.title[4:])

        wvars.update({
            'files': attached_items.get('files', []),
            'folders': folders,
            'lectures': sorted(lectures, cmp=cmp_title_number)
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

        return (WPConferenceBase.getCSSFiles(self) +
                self._asset_env['eventservices_sass'].urls() +
                self._asset_env['contributions_sass'].urls() +
                self._asset_env['event_display_sass'].urls() + theme_sass)

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
            kwargs['isStringHTML'] = MaKaC.common.utils.isStringHTML
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
        entry = get_menu_entry_by_name(self._linkname, self._conf)
        return entry.localized_title


class WConfProgram(WConfDisplayBodyBase):

    _linkname = 'program'

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
    menu_entry_name = 'program'

    def _getBody(self, params):
        wc = WConfProgram(self._getAW(), self._conf)
        return wc.getHTML()


class WPConferenceModifBase(main.WPMainBase):

    _userData = ['favorite-user-ids']

    def __init__(self, rh, conference, **kwargs):
        conference = getattr(conference, 'as_legacy', conference)
        main.WPMainBase.__init__(self, rh, **kwargs)
        self._navigationTarget = self._conf = conference

    def getJSFiles(self):
        return (main.WPMainBase.getJSFiles(self) +
                self._includeJSPackage('Management') +
                self._includeJSPackage('MaterialEditor') +
                self._asset_env['modules_event_management_js'].urls())

    def getCSSFiles(self):
        return main.WPMainBase.getCSSFiles(self) + self._asset_env['event_management_sass'].urls()

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

    def _applyFrame(self, body):
        frame = wcomponents.WConferenceModifFrame(self._conf, self._getAW())

        params = {
            "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL,
            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL,
            "event": "Conference",
            "sideMenu": render_sidemenu('event-management-sidemenu', active_item=self.sidemenu_option, old_style=True,
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


class WPConferenceModifAbstractBase( WPConferenceModifBase ):

    sidemenu_option = 'abstracts'

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

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveTab(self):
        pass


class WConfModifMainData(wcomponents.WTemplated):

    def __init__(self, conference, ct, rh):
        self._conf = conference
        self._ct = ct
        self._rh = rh

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        type = vars["type"]
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
        for ctype in self._conf.getContribTypeList():
             # TODO: This will all go away soon
            typeList.append("""<input type="checkbox" name="types" value="%s"><a href="%s">%s</a><br>
<table><tr><td width="30"></td><td><font><pre>%s</pre></font></td></tr></table>"""%( \
                ctype.id, \
                '', \
                ctype.name, \
                ctype.description))
        vars["typeList"] = "".join(typeList)
        #------------------------------------------------------
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
        vars['rbActive'] = Config.getInstance().getIsRoomBookingActive()
        vars["screenDates"] = "%s -> %s" % (ssdate, sedate)
        vars["timezoneList"] = TimezoneRegistry.getList()

        loc = self._conf.getLocation()
        room = self._conf.getRoom()
        vars['styleOptions'] = {tid: data['title'] for tid, data in
                                theme_settings.get_themes_for(self._conf.getType()).viewitems()}
        vars["currentLocation"] = { 'location': loc.getName() if loc else "",
                                    'room': room.name if room else "",
                                    'address': loc.getAddress() if loc else "" }
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
        vars["orgText"] = self._conf.getOrgText()
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
            cr = "<br>" + mako_call_template_hook('conference-protection', event=self.__conf.as_event)

        return """<br><table width="100%%" class="ACtab"><tr><td>%s%s%s%s%s%s<br></td></tr></table>""" % (mc, rc, ac, dc, tf, cr)


class WPConfModifAC(WPConferenceModifBase):

    sidemenu_option = 'protection'

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType = "conference"
        if self._rh.getWebFactory() is not None:
            self._eventType = self._rh.getWebFactory().getId()
        self._user = self._rh._getUser()

    def _getPageContent(self, params):
        wc = WConfModifAC(self._conf, self._eventType, self._user)
        p = {
            'setVisibilityURL': urlHandlers.UHConfSetVisibility.getURL(self._conf)
        }
        return wc.getHTML(p)


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
                "cloneOptions": i18nformat("""<li><input type="checkbox" name="cloneTracks" id="cloneTracks" value="1">_("Tracks")</li>""")}
        pars['cloneOptions'] += EventCloner.get_form_items(self._conf.as_event).encode('utf-8')
        return p.getHTML(pars)


class WConfModifCFA(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

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

    sidemenu_option = 'program'

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
        for contribType in self._conf.as_event.contribution_types:
            checked = ""
            if field is not None and str(contribType.id) in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="type" value="%s" %s> %s"""%(contribType.id, checked, self.htmlText(contribType.name)) )
        return l

    def _getAccTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="accTrackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and str(t.getId()) in field.getValues():
                checked=" checked"
            l.append("""<input type="checkbox" name="acc_track" value=%s%s> (%s) %s"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getAccContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="accTypeShowNoValue"%s> --_("not specified")--""")%checked]
        for contribType in self._conf.as_event.contribution_types:
            checked = ""
            if field is not None and str(contribType.id) in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="acc_type" value="%s" %s> %s""" % (contribType.id, checked, self.htmlText(contribType.name)))
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
            return self.htmlText(status.getType().name)
        return ""

    def _getAccTrack(self, abstract):
        acc_track = abstract.getAcceptedTrack()
        if not acc_track:
            return ""
        return self.htmlText(acc_track.getCode())

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


class WPConfParticipantList( WPConfAbstractList ):

    def __init__(self, rh, conf, emailList, displayedGroups, abstracts):
        WPConfAbstractList.__init__(self, rh, conf, None)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._abstracts = abstracts

    def _getTabContent( self, params ):
        wc = WAbstractsParticipantList(self._conf, self._emailList, self._displayedGroups, self._abstracts)
        return wc.getHTML()


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


class WConfMyStuffMyTracks(WConfDisplayBodyBase):

    _linkname = 'my_tracks'

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
        for t in lt:
            modURL = urlHandlers.UHTrackModifAbstracts.getURL(t)
            res.append("""
                <tr class="infoTR">
                    <td class="infoTD" width="100%%">%s</td>
                    <td nowrap class="infoTD"><a href=%s>%s</a></td>
                </tr>""" % (self.htmlText(t.getTitle()),
                            quoteattr(str(modURL)),
                            _("Edit")))
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
    menu_entry_name = 'my_tracks'

    def _getBody(self,params):
        wc=WConfMyStuffMyTracks(self._getAW(),self._conf)
        return wc.getHTML()


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
        vars["bookOfAbstractsMenuActive"] = get_menu_entry_by_name('abstracts_book', self._conf).is_enabled
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


class WPreviewPage( wcomponents.WTemplated ):
    pass
