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

from flask import render_template, render_template_string, request

from indico.core.config import config
from indico.legacy.webinterface import wcomponents
from indico.legacy.webinterface.common.tools import escape_html, strip_ml_tags
from indico.legacy.webinterface.pages import base
from indico.legacy.webinterface.pages.base import WPDecorated
from indico.modules.core.settings import core_settings, social_settings
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.models.events import EventType
from indico.util.date_time import format_date
from indico.util.event import unify_event_args
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
    themes = {tid: {'name': data[u'title'], 'user_visible': data.get(u'user_visible')}
              for tid, data in theme_settings.get_themes_for(event.type_.name).viewitems()}
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
    @unify_event_args
    def __init__(self, rh, event_, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        WPDecorated.__init__(self, rh, **kwargs)
        self._navigationTarget = self._conf = event_.as_legacy
        self._tz = event_.display_tzinfo.zone
        start_dt_local = event_.start_dt_display.astimezone(event_.display_tzinfo)
        end_dt_local = event_.end_dt_display.astimezone(event_.display_tzinfo)
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


class WPConferenceDefaultDisplayBase(MathjaxMixin, WPConferenceBase):
    menu_entry_plugin = None
    menu_entry_name = None

    @unify_event_args
    def __init__(self, rh, event_, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        kwargs['conf_layout_params'] = self._get_layout_params()
        WPConferenceBase.__init__(self, rh, event_, **kwargs)

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
        theme_url = self._kwargs.get('css_url_override', get_css_url(self._conf.as_event))
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

    def _apply_conference_layout(self, body):
        tpl = u"{% extends 'events/display/conference/base.html' %}{% block content %}{{ _body | safe }}{% endblock %}"
        return render_template_string(tpl, _body=body, **self._kwargs)

    def _getHeadContent(self):
        path = config.BASE_URL
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

    def _applyDecoration(self, body):
        self.logo_url = self.event.logo_url if self.event.has_logo else None
        body = self._apply_conference_layout(body)
        css_override_form = self._kwargs.get('css_override_form')
        if css_override_form:
            override_html = render_template('events/layout/css_preview_header.html',
                                            event=self.event, form=css_override_form,
                                            download_url=self._kwargs['css_url_override'])
            body = override_html + body
        return WPConferenceBase._applyDecoration(self, to_unicode(body))


class WConfMetadata(wcomponents.WTemplated):
    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        v = wcomponents.WTemplated.getVars( self )
        v['site_name'] = core_settings.get('site_title')
        v['social'] = social_settings.get_all()

        event = self._conf.as_event
        v['image'] = event.logo_url if event.has_logo else (config.IMAGES_BASE_URL + '/logo_indico.png')
        v['description'] = strip_ml_tags(self._conf.as_event.description[:500].encode('utf-8'))
        return v


class WPConferenceModifBase(WPEventManagement):
    """Base class for event management pages without Jinja inheritance.

    Do not use this for anything new.  Instead, use `WPEventManagement`
    directly (or inherit from it) and inherit the associated Jinja template
    from ``events/management/base.html``.
    """

    @unify_event_args
    def __init__(self, rh, event_, **kwargs):
        WPEventManagement.__init__(self, rh, event_, **kwargs)
        self._conf = self.event.as_legacy

    def _getBody(self, params):
        # Legacy handling for pages that do not use Jinja inheritance.
        tpl = u"{% extends 'events/management/base.html' %}{% block content %}{{ _body | safe }}{% endblock %}"
        body = to_unicode(self._getPageContent(params))
        return render_template_string(tpl, _body=body, **self._kwargs)

    def _getTabContent(self, params):
        raise NotImplementedError

    def _getPageContent(self, params):
        raise NotImplementedError
