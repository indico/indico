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

from flask import session, render_template, request
from pytz import timezone
from sqlalchemy.orm import load_only

from indico.core.config import Config
from indico.modules.auth.util import url_for_logout
from indico.modules.core.settings import social_settings, core_settings
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.events.models.events import Event
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.util.mathjax import MathjaxMixin
from indico.util.string import encode_if_unicode, to_unicode
from indico.web.flask.util import url_for

from indico.legacy.common.output import outputGenerator
from indico.legacy.common.timezoneUtils import DisplayTZ
from indico.legacy.common.utils import isStringHTML
from indico.legacy.webinterface import wcomponents
from indico.legacy.webinterface.common.tools import strip_ml_tags, escape_html
from indico.legacy.webinterface.pages import main, base
from indico.legacy.webinterface.pages.base import WPDecorated


class WPConferenceBase(base.WPDecorated):

    def __init__(self, rh, conference, **kwargs):
        event = conference.as_event
        WPDecorated.__init__(self, rh, _protected_object=event, _current_category=event.category, **kwargs)
        self._navigationTarget = self._conf = conference
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


class WPConferenceDefaultDisplayBase(MathjaxMixin, WPConferenceBase):
    menu_entry_plugin = None
    menu_entry_name = None

    def get_extra_css_files(self):
        theme_url = get_css_url(self._conf.as_event)
        return [theme_url] if theme_url else []

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
        frame = WConfDisplayFrame( self._getAW(), self._conf )

        announcement = ''
        if layout_settings.get(self._conf, 'show_announcement'):
            announcement = layout_settings.get(self._conf, 'announcement')

        frameParams = {
            "confModifURL": url_for('event_management.settings', self._conf.as_event),
            "logoURL": self.logo_url,
            "currentURL": request.url,
            "announcement": announcement,
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
        css = '<link rel="stylesheet" type="text/css" href="{}/css/Conf_Basic.css?{}">'.format(path, timestamp)

        return '\n'.join([
            css,
            WConfMetadata(self._conf).getHTML(),
            MathjaxMixin._getHeadContent(self)
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


class WPConferenceDisplay(WPConferenceDefaultDisplayBase):
    menu_entry_name = 'overview'

    def _getBody(self, params):
        return WConfDetailsFull(self._getAW(), self._conf).getHTML()

    def _getFooter(self):
        return wcomponents.WEventFooter(self._conf).getHTML()


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

    def _applyDecoration(self, body):
        return to_unicode(body)

    def _getBodyVariables(self):
        return {'firstDay': self._firstDay, 'lastDay': self._lastDay, 'daysPerRow': self._daysPerRow}

    def _getBody(self, params):
        body_vars = self._getBodyVariables()
        outGen = outputGenerator(self._getAW())
        if self._view in theme_settings.xml_themes:
            if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                includeContribution = 1
            else:
                includeContribution = 0
            theme = theme_settings.themes[self._view]
            stylesheet = None
            if theme['template']:
                assert theme.get('plugin')  # we don't have XSL-based themes in the core anymore
                stylesheet = os.path.join(theme['plugin'].root_path, 'themes', theme['template'])
            body = outGen.getFormattedOutput(self._rh, self._conf, stylesheet,
                                             body_vars, 1, includeContribution, 1, 1,
                                             self._params.get("showSession", ""), self._params.get("showDate", ""))
            return body
        else:
            return _("Cannot find the %s stylesheet") % self._view


class WPTPLConferenceDisplay(MathjaxMixin, WPXSLConferenceDisplay, object):
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

    def _getHeadContent( self ):
        theme_css_tag = ''
        theme_url = get_css_url(self._conf.as_event)
        if theme_url:
            theme_css_tag = '<link rel="stylesheet" type="text/css" href="{url}">'.format(url=theme_url)
        confMetadata = WConfMetadata(self._conf).getHTML()
        return theme_css_tag + confMetadata + MathjaxMixin._getHeadContent(self)

    def _getFooter(self):
        wc = wcomponents.WEventFooter(self._conf)
        p = {
            "subArea": self._getSiteArea(),
            "dark": True,
            "shortURL": self._conf.as_event.short_external_url
        }
        return wc.getHTML(p)

    def _getHeader(self):
        if self._type == 'lecture':
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
        theme_print_sass = (self.theme['asset_env']['print_sass'].urls()
                            if 'print_sass' in self.theme.get('asset_env', [])
                            else [])
        return WPConferenceBase.getPrintCSSFiles(self) + theme_print_sass

    def getCSSFiles(self):
        theme_sass = self.theme['asset_env']['display_sass'].urls() if self.theme.get('asset_env') else []
        return WPConferenceBase.getCSSFiles(self) + theme_sass

    def getJSFiles(self):
        modules = WPConferenceBase.getJSFiles(self)

        # TODO: find way to check if the user is able to manage
        # anything inside the conference (sessions, ...)
        modules += (self._includeJSPackage('Management') +
                    self._asset_env['modules_event_cloning_js'].urls() +
                    self._asset_env['modules_vc_js'].urls() +
                    self._asset_env['modules_event_display_js'].urls() +
                    self._asset_env['clipboard_js'].urls())
        return modules

    def _applyDecoration(self, body):
        if self._params.get('frame', '') == 'no' or self._params.get('fr', '') == 'no':
            return to_unicode(WPrintPageFrame().getHTML({'content': body}))
        return WPConferenceBase._applyDecoration(self, body)

    def _getBody(self, params):
        """Return main information about the event."""

        if self._view != 'xml':
            kwargs = self._getVariables(self._conf)
            kwargs['isStringHTML'] = isStringHTML
        else:
            outGen = outputGenerator(self._rh._aw)
            varsForGenerator = self._getBodyVariables()
            kwargs = {'xml': outGen._getBasicXML(self._conf, varsForGenerator, 1, 1, 1, 1)}

        kwargs['theme_settings'] = self.theme.get('settings', {})
        plugin = self.theme.get('plugin')
        tpl_name = self.theme['template']
        tpl = ((plugin.name + tpl_name)
               if (plugin and tpl_name[0] == ':')
               else posixpath.join('events/display', tpl_name))
        return (render_template(tpl, event=self._conf.as_event, conf=self._conf, **kwargs)
                .encode('utf-8'))


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
                self._asset_env['modules_event_cloning_js'].urls() +
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
        css = '<link rel="stylesheet" type="text/css" href="{}/Conf_Basic.css?{}">\n'.format(path, timestamp)
        if self._kwargs['css_url']:
            css += '<link rel="stylesheet" type="text/css" href="{url}">\n'.format(url=self._kwargs['css_url'])
        return css

    def get_extra_css_files(self):
        return []


class WPreviewPage( wcomponents.WTemplated ):
    pass
