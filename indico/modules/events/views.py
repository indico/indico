# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function, unicode_literals

import posixpath

from flask import current_app, render_template, request
from sqlalchemy.orm import load_only
from werkzeug.utils import cached_property

from indico.modules.admin.views import WPAdmin
from indico.modules.core.settings import social_settings
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


class WPEventAdmin(WPAdmin):
    template_prefix = 'events/'


class WPEventBase(WPDecorated):
    ALLOW_JSON = False
    bundles = ('module_events.display.js', 'module_events.contributions.js')

    @property
    def page_metadata(self):
        metadata = super(WPEventBase, self).page_metadata
        return {
            'og': dict(metadata['og'], **{
                'title': self.event.title,
                'type': 'event',
                'image': (self.event.logo_url if self.event.has_logo else
                          url_for('assets.image', filename='indico_square.png', _external=True)),
                'description': self.event.description
            }),
            'json_ld': serialize_event_for_json_ld(self.event, full=True),
            'keywords': self.event.keywords
        }

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
        page_title = kwargs.get('page_title')
        if page_title:
            self.title += ': {}'.format(strip_tags(page_title))

    def _get_header(self):
        raise NotImplementedError  # must be overridden by meeting/lecture and conference WPs


class WPSimpleEventDisplayBase(MathjaxMixin, WPEventBase):
    """Base class for displaying something on a lecture/meeting page."""

    def __init__(self, rh, event_, **kwargs):
        self.event = event_
        WPEventBase.__init__(self, rh, event_, **kwargs)

    def _get_header(self):
        return render_event_header(self.event)

    def _get_footer(self):
        return render_event_footer(self.event)


class WPSimpleEventDisplay(WPSimpleEventDisplayBase):
    bundles = ('module_vc.js', 'module_vc.css', 'module_events.cloning.js', 'module_events.importing.js')

    def __init__(self, rh, conf, theme_id, theme_override=False):
        WPSimpleEventDisplayBase.__init__(self, rh, conf)
        self.theme_id = theme_id
        self.theme_file_name = theme_id.replace('-', '_')
        self.theme = theme_settings.themes[theme_id]
        self.theme_override = theme_override

    @property
    def additional_bundles(self):
        plugin = self.theme.get('plugin')
        print_stylesheet = self.theme.get('print_stylesheet')
        if plugin:
            manifest = plugin.manifest
        else:
            manifest = current_app.manifest
        return {
            'screen': (manifest['themes_{}.css'.format(self.theme_file_name)],),
            'print': ((manifest['themes_{}.print.css'.format(self.theme_file_name)],)
                      if print_stylesheet else ())
        }

    def _get_head_content(self):
        return MathjaxMixin._get_head_content(self) + WPEventBase._get_head_content(self)

    def get_extra_css_files(self):
        custom_url = get_css_url(self.event)
        return [custom_url] if custom_url else []

    def _apply_decoration(self, body):
        if request.args.get('frame') == 'no' or request.args.get('fr') == 'no' or request.args.get('print') == '1':
            return render_template('events/display/print.html', content=body)
        else:
            return WPEventBase._apply_decoration(self, body)

    def _get_header(self):
        return render_event_header(self.event, theme=self.theme_id, theme_override=self.theme_override)

    def _get_footer(self):
        return render_event_footer(self.event, dark=True)

    def _get_body(self, params):
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
    bundles = ('conferences.css',)

    def __init__(self, rh, event_, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        kwargs['conf_layout_params'] = self._get_layout_params()
        kwargs.setdefault('page_title', self.sidemenu_title)
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

    def _get_header(self):
        return render_event_header(self.event, conference_layout=True)

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

    def _get_head_content(self):
        return '\n'.join([
            MathjaxMixin._get_head_content(self),
            WPEventBase._get_head_content(self)
        ])

    def _get_body(self, params):
        return WPJinjaMixin._get_page_content(self, params)

    def _apply_decoration(self, body):
        self.logo_url = self.event.logo_url if self.event.has_logo else None
        css_override_form = self._kwargs.get('css_override_form')
        if css_override_form:
            override_html = render_template('events/layout/css_preview_header.html',
                                            event=self.event, form=css_override_form,
                                            download_url=self._kwargs['css_url_override'])
            body = override_html + body
        return WPEventBase._apply_decoration(self, to_unicode(body))


class WPConferenceDisplay(WPConferenceDisplayBase):
    menu_entry_name = 'overview'

    def _get_body(self, params):
        return render_template('events/display/conference.html', **self._kwargs)

    def _get_footer(self):
        return render_event_footer(self.event)


class WPAccessKey(WPJinjaMixin, WPDecorated):
    template_prefix = 'events/'

    def _get_body(self, params):
        return self._get_page_content(params)
