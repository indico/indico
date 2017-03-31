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

from __future__ import print_function

import os

from flask import session, render_template, request

from indico.core.config import Config
from indico.legacy.common.utils import isStringHTML
from indico.legacy.webinterface import wcomponents
from indico.legacy.webinterface.common.tools import strip_ml_tags, escape_html
from indico.legacy.webinterface.pages import main, base
from indico.legacy.webinterface.pages.base import WPDecorated
from indico.legacy.webinterface.wcomponents import render_header
from indico.modules.auth.util import url_for_logout
from indico.modules.core.settings import social_settings, core_settings
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.events.models.events import EventType
from indico.util.date_time import format_date
from indico.util.i18n import _
from indico.util.mathjax import MathjaxMixin
from indico.util.string import encode_if_unicode, to_unicode, truncate
from indico.web.flask.util import url_for


def _get_print_url(event, theme=None, theme_override=False):
    view = theme if theme_override else None

    if event.type_ == EventType.conference:
        return url_for(u'timetable.timetable', event, print=u'1', view=view)
    elif event.type_ == EventType.meeting:
        show_date = request.args.get(u'showDate')
        show_session = request.args.get(u'showSession')
        detail_level = request.args.get(u'detailLevel')
        if show_date == u'all':
            show_date = None
        if show_session == u'all':
            show_session = None
        if detail_level in (u'all', u'contrinbution'):
            detail_level = None
        return url_for(u'events.display', event, showDate=show_date, showSession=show_session, detailLevel=detail_level,
                       print=u'1', view=view)
    elif event.type_ == EventType.lecture:
        return url_for(u'events.display', event, print=u'1', view=view)


def render_event_header(event, conference_layout=False, theme=None, theme_override=False):
    print_url = _get_print_url(event, theme, theme_override) if not conference_layout else None
    show_nav_bar = event.type_ != EventType.conference or layout_settings.get(event, u'show_nav_bar')
    themes = {tid: data[u'title'] for tid, data in theme_settings.get_themes_for(event.type_.name).viewitems()}
    return render_template(u'events/header.html',
                           event=event, print_url=print_url, show_nav_bar=show_nav_bar, themes=themes, theme=theme)


def render_event_footer(event, dark=False):
    location = event.venue_name
    if event.room_name:
        location = u'{} ({})'.format(event.room_name, location)
    description = u'{}\n\n{}'.format(truncate(event.description, 1000), event.short_external_url).strip()
    google_calendar_params = {
        u'action': u'TEMPLATE',
        u'text': event.title,
        u'dates': u'{}/{}'.format(event.start_dt.strftime(u'%Y%m%dT%H%M%SZ'),
                                  event.end_dt.strftime(u'%Y%m%dT%H%M%SZ')),
        u'details': description,
        u'location': location,
        u'trp': False,
        u'sprop': [event.external_url, u'name:indico']
    }

    social_settings_data = social_settings.get_all()
    show_social = social_settings_data[u'enabled'] and layout_settings.get(event, u'show_social_badges')
    return render_template(u'events/footer.html',
                           event=event,
                           dark=dark,
                           social_settings=social_settings_data,
                           show_social=show_social,
                           google_calendar_params=google_calendar_params)


class WPConferenceBase(base.WPDecorated):
    def __init__(self, rh, conference, **kwargs):
        event = conference.as_event
        WPDecorated.__init__(self, rh, **kwargs)
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

    def _getHeader(self):
        raise NotImplementedError  # must be overridden by meeting/lecture and conference WPs

    def getJSFiles(self):
        return base.WPDecorated.getJSFiles(self) + self._asset_env['modules_event_display_js'].urls()

    def getLogoutURL(self):
        return url_for_logout(self._conf.as_event.external_url)


class WPConferenceDefaultDisplayBase(MathjaxMixin, WPConferenceBase):
    menu_entry_plugin = None
    menu_entry_name = None

    def get_extra_css_files(self):
        theme_url = get_css_url(self._conf.as_event)
        return [theme_url] if theme_url else []

    def _getHeader(self):
        return render_event_header(self.event, conference_layout=True).encode('utf-8')

    @property
    def sidemenu_option(self):
        if not self.menu_entry_name:
            return None
        name = build_menu_entry_name(self.menu_entry_name, self.menu_entry_plugin)
        entry = get_menu_entry_by_name(name, self.event)
        if entry:
            return entry.id

    def _applyConfDisplayDecoration( self, body ):
        frame = WConfDisplayFrame(self._conf)

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
        path = Config.getInstance().getBaseURL()
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

    def __init__(self, conf):
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

    def __init__(self, conf):
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars['timezone'] = self._conf.as_event.display_tzinfo.zone

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
        return WConfDetailsFull(self._conf).getHTML()

    def _getFooter(self):
        return render_event_footer(self.event).encode('utf-8')


class WPrintPageFrame(wcomponents.WTemplated):
    pass


class WConfDisplayBodyBase(wcomponents.WTemplated):
    def _getTitle(self):
        entry = get_menu_entry_by_name(self._linkname, self._conf.as_event)
        return entry.localized_title


class WPConferenceModifBase(main.WPMainBase):
    def __init__(self, rh, conference, **kwargs):
        conference = getattr(conference, 'as_legacy', conference)
        main.WPMainBase.__init__(self, rh, **kwargs)
        self._navigationTarget = self._conf = conference

    def getJSFiles(self):
        return (main.WPMainBase.getJSFiles(self) +
                self._includeJSPackage('Management') +
                self._asset_env['modules_event_cloning_js'].urls() +
                self._asset_env['modules_event_management_js'].urls())

    def _getHeader(self):
        return render_header(category=self._conf.as_event.category, local_tz=self._conf.as_event.timezone,
                             force_local_tz=True)

    def _getNavigationDrawer(self):
        pars = {"target": self._conf.as_event, "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _applyFrame(self, body):
        from indico.modules.events.management.views import render_event_management_frame
        return render_event_management_frame(self._conf.as_event, body, self.sidemenu_option)

    def _getBody( self, params ):
        return self._applyFrame( self._getPageContent( params ) )

    def _getTabContent(self, params):
        raise NotImplementedError

    def _getPageContent(self, params):
        raise NotImplementedError


class WPConferenceModificationClosed( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

    def _getPageContent( self, params ):
        # XXX: We show a message in the management frame but this class is used
        # in too many places so we keep it around for now.
        return ''


class WConfMyStuff(WConfDisplayBodyBase):
    _linkname = 'my_conference'

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


class WPMyStuff(WPConferenceDefaultDisplayBase):
    menu_entry_name = 'my_conference'

    def _getBody(self,params):
        return WConfMyStuff(self._conf).getHTML()


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
