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

from __future__ import unicode_literals

import posixpath

from flask import render_template, request
from sqlalchemy.orm import load_only

from indico.legacy.webinterface.pages.conferences import (render_event_header, render_event_footer,
                                                          WPConferenceBase, WConfMetadata, WPrintPageFrame)
from indico.modules.admin.views import WPAdmin
from indico.modules.events import Event
from indico.modules.events.layout import theme_settings
from indico.modules.events.layout.util import get_css_url
from indico.util.mathjax import MathjaxMixin
from indico.util.string import to_unicode


class WPReferenceTypes(WPAdmin):
    template_prefix = 'events/'


class WPSimpleEventDisplayBase(MathjaxMixin, WPConferenceBase):
    """Base class for displaying something on a lecture/meeting page"""

    def __init__(self, rh, conf, **kwargs):
        WPConferenceBase.__init__(self, rh, conf, **kwargs)
        self.event = conf.as_event

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
        return WConfMetadata(self._conf).getHTML() + MathjaxMixin._getHeadContent(self)

    def get_extra_css_files(self):
        theme_urls = self.theme['asset_env']['display_sass'].urls() if self.theme.get('asset_env') else []
        custom_url = get_css_url(self.event)
        return theme_urls + ([custom_url] if custom_url else [])

    def getPrintCSSFiles(self):
        theme_print_sass = (self.theme['asset_env']['print_sass'].urls()
                            if 'print_sass' in self.theme.get('asset_env', [])
                            else [])
        return WPConferenceBase.getPrintCSSFiles(self) + theme_print_sass

    def getJSFiles(self):
        return (WPSimpleEventDisplayBase.getJSFiles(self) +
                self._asset_env['modules_event_cloning_js'].urls() +
                self._asset_env['modules_vc_js'].urls())

    def _applyDecoration(self, body):
        if request.args.get('frame') == 'no' or request.args.get('fr') == 'no' or request.args.get('print') == '1':
            return to_unicode(WPrintPageFrame().getHTML({'content': body}))
        else:
            return WPConferenceBase._applyDecoration(self, body)

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
                             event=self.event, conf=self._conf,
                             category=self.event.category.title,
                             timezone=self.event.display_tzinfo,
                             theme_settings=self.theme.get('settings', {}),
                             files=files,
                             folders=folders,
                             lectures=lectures)
        return rv.encode('utf-8')
