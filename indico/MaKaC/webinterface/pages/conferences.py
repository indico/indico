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
from datetime import datetime

from flask import session, render_template, request
from pytz import timezone
from sqlalchemy.orm import load_only

from indico.core.config import Config
from indico.modules.auth.util import url_for_logout
from indico.modules.core.settings import social_settings, core_settings
from indico.modules.events.cloning import EventCloner
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.events.models.events import Event
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.util.string import encode_if_unicode, to_unicode
from indico.web.flask.util import url_for

from MaKaC.common.TemplateExec import render
from MaKaC.common.output import outputGenerator
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.common.utils import isStringHTML
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.common.tools import strip_ml_tags, escape_html
from MaKaC.webinterface.pages import main, base
from MaKaC.webinterface.pages.base import WPDecorated


class WPConferenceBase(base.WPDecorated):

    def __init__(self, rh, conference, **kwargs):
        WPDecorated.__init__(self, rh, _protected_object=conference, _current_category=conference.as_event.category,
                             **kwargs)
        self._navigationTarget = self._conf = conference
        event = self._conf.as_event
        self._tz = event.display_tzinfo.zone
        start_dt_local = event.start_dt_display.astimezone(event.display_tzinfo)
        end_dt_local = event.end_dt_display.astimezone(event.display_tzinfo)
        dates = " (%s)" % format_date(start_dt_local, format='long')
        if start_dt_local.strftime("%d%B%Y") != end_dt_local.strftime("%d%B%Y"):
            if start_dt_local.strftime("%B%Y") == end_dt_local.strftime("%B%Y"):
                dates = " (%s-%s)" % (start_dt_local.strftime("%d"), format_date(end_dt_local, format='long'))
            else:
                dates = " (%s - %s)" % (format_date(start_dt_local, format='long'),
                                        format_date(end_dt_local, format='long'))
        self._setTitle("%s %s" % (strip_ml_tags(self._conf.as_event.title.encode('utf-8')), dates))

    def _getFooter(self):
        wc = wcomponents.WFooter()
        p = {"subArea": self._getSiteArea()}
        return wc.getHTML(p)

    def getLogoutURL(self):
        return url_for_logout(self._conf.as_event.external_url)


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
        p = {"subArea": self._getSiteArea(),
             "shortURL": self._conf.as_event.short_external_url}
        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WConferenceHeader(self._getAW(), self._conf)
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.id,
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
            "confModifURL": url_for('event_management.settings', self._conf.as_event),
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
        v['site_name'] = core_settings.get('site_title')
        v['social'] = social_settings.get_all()

        event = self._conf.as_event
        v['image'] = event.logo_url if event.has_logo else Config.getInstance().getSystemIconURL("logo_indico")
        v['description'] = strip_ml_tags(self._conf.as_event.description[:500].encode('utf-8'))
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
            vars["logo"] = '<img src="{}" alt="{}" border="0" class="confLogo">'.format(
                vars["logoURL"], escape_html(self.event.title.encode('utf-8'), escape_quotes=True))
        vars["confTitle"] = self.event.title.encode('utf-8')
        vars["displayURL"] = self.event.url
        start_dt_local = self.event.start_dt_display.astimezone(self.event.display_tzinfo)
        end_dt_local = self.event.end_dt_display.astimezone(self.event.display_tzinfo)
        vars["timezone"] = self.event.display_tzinfo.zone
        vars["confDateInterval"] = _("from {start} to {end}").format(start=format_date(start_dt_local, format='long'),
                                                                     end=format_date(end_dt_local, format='long'))
        if start_dt_local.strftime("%d%B%Y") == end_dt_local.strftime("%d%B%Y"):
            vars["confDateInterval"] = format_date(start_dt_local, format='long')
        elif start_dt_local.strftime("%B%Y") == end_dt_local.strftime("%B%Y"):
            vars["confDateInterval"] = "%s-%s %s" % (start_dt_local.day, end_dt_local.day,
                                                     format_date(start_dt_local, format='MMMM yyyy'))
        vars["confLocation"] = self.event.venue_name
        vars["body"] = self._body
        vars['menu'] = menu_entries_for_event(self.event)

        vars["bgColorCode"] = layout_settings.get(self._conf, 'header_background_color').replace("#", "")
        vars["textColorCode"] = layout_settings.get(self._conf, 'header_text_color').replace("#", "")

        vars["confId"] = self._conf.id
        vars["conf"] = self._conf
        return vars


class WConfDetailsFull(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        vars["timezone"] = tz

        description = self._conf.as_event.description.encode('utf-8')
        vars["description_html"] = isStringHTML(description)
        vars["description"] = description

        event = self._conf.as_event
        start_dt_local = event.start_dt_display.astimezone(event.display_tzinfo)
        end_dt_local = event.end_dt_display.astimezone(event.display_tzinfo)

        fsdate, fedate = format_date(start_dt_local, format='medium'), format_date(end_dt_local, format='medium')
        fstime, fetime = start_dt_local.strftime("%H:%M"), end_dt_local.strftime("%H:%M")

        vars["dateInterval"] = (fsdate, fstime, fedate, fetime)

        vars["address"] = None
        vars["room"] = None

        vars["attachments"] = self._conf.as_event.attached_items
        vars["conf"] = self._conf
        vars["event"] = self._conf.as_event

        info = self._conf.as_event.additional_info
        vars["moreInfo_html"] = isStringHTML(info)
        vars["moreInfo"] = info
        vars["actions"] = ''
        vars["isSubmitter"] = self._conf.as_event.can_manage(session.user, 'submit')
        return vars


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
        pars = {"modifyURL": url_for('event_management.settings', self._conf.as_event)}
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
        pars = {"modifyURL": url_for('event_management.settings', self._conf.as_event),
                "cloneURL": url_for('event_mgmt.confModifTools-clone', self._conf.as_event)}

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

        attached_items = event.attached_items
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

    def _getFooter(self):
        wc = wcomponents.WEventFooter(self._conf)
        p = {
            "subArea": self._getSiteArea(),
            "dark": True,
            "shortURL": self._conf.as_event.short_external_url
        }
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
                             "confId": str(self._conf.id),
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
        pars = {"target": self._conf.as_event, "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _applyFrame(self, body):
        from indico.modules.events.management.views import render_event_management_frame
        return render_event_management_frame(self._conf.as_event, body, self.sidemenu_option)

    def _getBody( self, params ):
        return self._applyFrame( self._getPageContent( params ) )

    def _getTabContent( self, params ):
        return "nothing"

    def _getPageContent( self, params ):
        return "nothing"


class WPConferenceModificationClosed( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

    def _getPageContent( self, params ):
        # XXX: We show a message in the management frame but this class is used
        # in too many places so we keep it around for now.
        return ''


class WPConfCloneConfirm(WPConferenceModifBase):

    def __init__(self, rh, conf, nbClones):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._nbClones = nbClones

    def _getPageContent(self, params):

        msg = _("This action will create {0} new events. Are you sure you want to proceed").format(self._nbClones)

        wc = wcomponents.WConfirmation()
        params = dict(self._rh._getRequestParams())
        del params['confId']
        url = url_for('event_mgmt.confModifTools-performCloning', self._conf.as_event, **params)
        return wc.getHTML(msg, url, {}, True, confirmButtonCaption=_("Yes"), cancelButtonCaption=_("No"))


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
        vars["confTitle"] = self.__conf.as_event.title.encode('utf-8')
        vars["confId"] = self.__conf.id
        vars["selectDay"] = self._getSelectDay()
        vars["selectMonth"] = self._getSelectMonth()
        vars["selectYear"] = self._getSelectYear()
        return vars


class WPConfClone(WPConferenceModifBase):
    def _getPageContent(self, params):
        p = WConferenceClone(self._conf)
        pars = {"cloning": url_for('event_mgmt.confModifTools-performCloning', self._conf.as_event),
                "startTime": self._conf.as_event.start_dt_local.isoformat(),
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


class WPConfModifPreviewCSS( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, **kwargs):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf, **kwargs)

        self._conf = conf

    def _applyDecoration( self, body ):
        """
        """
        return "%s%s%s"%( self._getHeader(), body, self._getFooter() )

    def _getBody( self, params ):
        params['confId'] = self._conf.id
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
