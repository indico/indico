# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import print_function, unicode_literals

import posixpath

from flask import render_template, request
from sqlalchemy.orm import load_only
from werkzeug.utils import cached_property

from indico.modules.admin.views import WPAdmin
from indico.modules.core.settings import core_settings, social_settings
from indico.modules.events import Event
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.events.models.events import EventType
from indico.modules.events.util import serialize_event_for_json_ld
from indico.util.date_time import format_date
from indico.util.mathjax import MathjaxMixin
from indico.util.string import strip_tags, to_unicode, truncate
from indico.web.flask.util import url_for
from indico.web.views import WPDecorated, WPJinjaMixin


def _get_print_url(event, theme=None, theme_override=False):
    view = theme if theme_override else None

    if event.type_ == EventType.conference:
        return url_for('timetable.timetable', event, print='1', view=view)
    elif event.type_ == EventType.meeting:
        show_date = request.args.get('showDate')
        show_session = request.args.get('showSession')
        detail_level = request.args.get('detailLevel')
        if show_date == 'all':
            show_date = None
        if show_session == 'all':
            show_session = None
        if detail_level in ('all', 'contrinbution'):
            detail_level = None
        return url_for('events.display', event, showDate=show_date, showSession=show_session, detailLevel=detail_level,
                       print='1', view=view)
    elif event.type_ == EventType.lecture:
        return url_for('events.display', event, print='1', view=view)


def render_event_header(event, conference_layout=False, theme=None, theme_override=False):
    print_url = _get_print_url(event, theme, theme_override) if not conference_layout else None
    show_nav_bar = event.type_ != EventType.conference or layout_settings.get(event, 'show_nav_bar')
    themes = {tid: {'name': data['title'], 'user_visible': data.get('user_visible')}
              for tid, data in theme_settings.get_themes_for(event.type_.name).viewitems()}
    return render_template('events/header.html',
                           event=event, print_url=print_url, show_nav_bar=show_nav_bar, themes=themes, theme=theme)


def render_event_footer(event, dark=False):
    location = event.venue_name
    if event.room_name:
        location = '{} ({})'.format(event.room_name, location)
    description = '{}\n\n{}'.format(truncate(event.description, 1000), event.short_external_url).strip()
    google_calendar_params = {
        'action': 'TEMPLATE',
        'text': event.title,
        'dates': '{}/{}'.format(event.start_dt.strftime('%Y%m%dT%H%M%SZ'),
                                event.end_dt.strftime('%Y%m%dT%H%M%SZ')),
        'details': description,
        'location': location,
        'trp': False,
        'sprop': [event.external_url, 'name:indico']
    }

    social_settings_data = social_settings.get_all()
    show_social = social_settings_data['enabled'] and layout_settings.get(event, 'show_social_badges')
    return render_template('events/footer.html',
                           event=event,
                           dark=dark,
                           social_settings=social_settings_data,
                           show_social=show_social,
                           google_calendar_params=google_calendar_params)


class WPReferenceTypes(WPAdmin):
    template_prefix = 'events/'


class WPEventBase(WPDecorated):
    ALLOW_JSON = False

    def __init__(self, rh, event_, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        WPDecorated.__init__(self, rh, **kwargs)
        start_dt_local = event_.start_dt_display.astimezone(event_.display_tzinfo)
        end_dt_local = event_.end_dt_display.astimezone(event_.display_tzinfo)
        dates = ' ({})'.format(to_unicode(format_date(start_dt_local, format='long')))
        if start_dt_local.date() != end_dt_local.date():
            if start_dt_local.year == end_dt_local.year and start_dt_local.month == end_dt_local.month:
                dates = ' ({}-{})'.format(start_dt_local.day, to_unicode(format_date(end_dt_local, format='long')))
            else:
                dates = ' ({} - {})'.format(to_unicode(format_date(start_dt_local, format='long')),
                                            to_unicode(format_date(end_dt_local, format='long')))
        self.title = '{} {}'.format(strip_tags(self.event.title), dates)

    def _getHeader(self):
        raise NotImplementedError  # must be overridden by meeting/lecture and conference WPs

    def getJSFiles(self):
        return WPDecorated.getJSFiles(self) + self._asset_env['modules_event_display_js'].urls()

    def _getHeadContent(self):
        site_name = core_settings.get('site_title')
        meta = render_template('events/meta.html', event=self.event, site_name=site_name,
                               json_ld=serialize_event_for_json_ld(self.event, full=True))
        return WPDecorated._getHeadContent(self) + meta


class WPSimpleEventDisplayBase(MathjaxMixin, WPEventBase):
    """Base class for displaying something on a lecture/meeting page"""

    def __init__(self, rh, event_, **kwargs):
        self.event = event_
        WPEventBase.__init__(self, rh, event_, **kwargs)

    def _getHeader(self):
        return render_event_header(self.event).encode('utf-8')

    def _getFooter(self):
        return render_event_footer(self.event).encode('utf-8')


class WPSimpleEventDisplay(WPSimpleEventDisplayBase):
    def __init__(self, rh, conf, theme_id, theme_override=False):
        WPSimpleEventDisplayBase.__init__(self, rh, conf)
        self.theme_id = theme_id
        self.theme = theme_settings.themes[theme_id]
        self.theme_override = theme_override

    def _getHeadContent(self):
        return MathjaxMixin._getHeadContent(self) + WPEventBase._getHeadContent(self)

    def get_extra_css_files(self):
        theme_urls = self.theme['asset_env']['display_sass'].urls() if self.theme.get('asset_env') else []
        custom_url = get_css_url(self.event)
        return theme_urls + ([custom_url] if custom_url else [])

    def getPrintCSSFiles(self):
        theme_print_sass = (self.theme['asset_env']['print_sass'].urls()
                            if 'print_sass' in self.theme.get('asset_env', [])
                            else [])
        return WPEventBase.getPrintCSSFiles(self) + theme_print_sass

    def getJSFiles(self):
        return (WPSimpleEventDisplayBase.getJSFiles(self) +
                self._asset_env['modules_event_cloning_js'].urls() +
                self._asset_env['modules_vc_js'].urls())

    def _applyDecoration(self, body):
        if request.args.get('frame') == 'no' or request.args.get('fr') == 'no' or request.args.get('print') == '1':
            return render_template('events/display/print.html', content=body)
        else:
            return WPEventBase._applyDecoration(self, body)

    def _getHeader(self):
        return render_event_header(self.event, theme=self.theme_id, theme_override=self.theme_override).encode('utf-8')

    def _getFooter(self):
        return render_event_footer(self.event, dark=True).encode('utf-8')

    def _getBody(self, params):
        attached_items = self.event.attached_items
        folders = [folder for folder in attached_items.get('folders', []) if folder.title != 'Internal Page Files']
        files = attached_items.get('files', [])

        lectures = []
        if self.event.series is not None and self.event.series.show_links:
            lectures = (Event.query.with_parent(self.event.series)
                        .filter(Event.id != self.event.id)
                        .options(load_only('series_pos', 'id'))
                        .order_by(Event.series_pos)
                        .all())

        plugin = self.theme.get('plugin')
        tpl_name = self.theme['template']
        tpl = ((plugin.name + tpl_name)
               if (plugin and tpl_name[0] == ':')
               else posixpath.join('events/display', tpl_name))

        rv = render_template(tpl,
                             event=self.event,
                             category=self.event.category.title,
                             timezone=self.event.display_tzinfo,
                             theme_settings=self.theme.get('settings', {}),
                             theme_user_settings=layout_settings.get(self.event, 'timetable_theme_settings'),
                             files=files,
                             folders=folders,
                             lectures=lectures)
        return rv.encode('utf-8')


class WPConferenceDisplayBase(WPJinjaMixin, MathjaxMixin, WPEventBase):
    menu_entry_plugin = None
    menu_entry_name = None

    def __init__(self, rh, event_, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        kwargs['conf_layout_params'] = self._get_layout_params()
        kwargs['page_title'] = self.sidemenu_title
        WPEventBase.__init__(self, rh, event_, **kwargs)

    def _get_layout_params(self):
        bg_color = layout_settings.get(self.event, 'header_background_color').replace('#', '').lower()
        text_color = layout_settings.get(self.event, 'header_text_color').replace('#', '').lower()
        announcement = ''
        if layout_settings.get(self.event, 'show_announcement'):
            announcement = layout_settings.get(self.event, 'announcement')
        return {
            'menu': menu_entries_for_event(self.event),
            'active_menu_item': self.sidemenu_option,
            'bg_color_css': 'background: #{0}; border-color: #{0};'.format(bg_color) if bg_color else '',
            'text_color_css': 'color: #{};'.format(text_color) if text_color else '',
            'announcement': announcement
        }

    def get_extra_css_files(self):
        theme_url = self._kwargs.get('css_url_override', get_css_url(self.event))
        return [theme_url] if theme_url else []

    def _getHeader(self):
        return render_event_header(self.event, conference_layout=True).encode('utf-8')

    @cached_property
    def sidemenu_entry(self):
        if not self.menu_entry_name:
            return None
        name = build_menu_entry_name(self.menu_entry_name, self.menu_entry_plugin)
        return get_menu_entry_by_name(name, self.event)

    @cached_property
    def sidemenu_option(self):
        entry = self.sidemenu_entry
        return entry.id if entry else None

    @cached_property
    def sidemenu_title(self):
        entry = self.sidemenu_entry
        return entry.localized_title if entry else ''

    def _getHeadContent(self):
        return '\n'.join([
            MathjaxMixin._getHeadContent(self),
            WPEventBase._getHeadContent(self)
        ])

    def getCSSFiles(self):
        return self._asset_env['conference_css'].urls() + WPEventBase.getCSSFiles(self)

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def _applyDecoration(self, body):
        self.logo_url = self.event.logo_url if self.event.has_logo else None
        css_override_form = self._kwargs.get('css_override_form')
        if css_override_form:
            override_html = render_template('events/layout/css_preview_header.html',
                                            event=self.event, form=css_override_form,
                                            download_url=self._kwargs['css_url_override'])
            body = override_html + body
        return WPEventBase._applyDecoration(self, to_unicode(body))


class WPConferenceDisplay(WPConferenceDisplayBase):
    menu_entry_name = 'overview'

    def _getBody(self, params):
        return render_template('events/display/conference.html', **self._kwargs)

    def _getFooter(self):
        return render_event_footer(self.event).encode('utf-8')


class WPAccessKey(WPJinjaMixin, WPDecorated):
    template_prefix = 'events/'

    def _getBody(self, params):
        return self._getPageContent(params)
