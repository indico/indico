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

from __future__ import unicode_literals

from flask import render_template_string

from indico.legacy.webinterface.wcomponents import render_header
from indico.modules.events.models.events import EventType
from indico.util.string import strip_tags, to_unicode
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.flask.templating import get_template_module
from indico.web.views import WPDecorated, WPJinjaMixin


class WPEventManagement(WPJinjaMixin, WPDecorated):
    """Base class for event management pages.

    When using this class the template will always have `event`
    available; it is not necessary to pass it as a kwarg when calling
    the `render_template` classmethod.

    When using the class directly, pass the menu item as a posarg::

        return WPEventManagement.render_template('foobar.html', self.event, 'foobar',
                                                 foo='bar')

    When subclassing you can set `sidemenu_option` on the class,
    allowing you to omit it.  This is recommended if you have many
    pages using the same menu item or if you already need to subclass
    for some other reason (e.g. to set a `template_prefix` or include
    additional JS/CSS bundles)::

        return WPSomething.render_template('foobar.html', self.event,
                                           foo='bar')
    """

    MANAGEMENT = True
    ALLOW_JSON = False

    def __init__(self, rh, event_, active_menu_item=None, **kwargs):
        assert event_ == kwargs.setdefault('event', event_)
        self.event = event_
        self.title = strip_tags(self.event.title)
        kwargs['base_layout_params'] = {
            'active_menu_item': active_menu_item or self.sidemenu_option,
            'event_types': [(et.name, et.title) for et in EventType]
        }
        WPDecorated.__init__(self, rh, **kwargs)

    def getJSFiles(self):
        return (WPDecorated.getJSFiles(self) +
                self._includeJSPackage('Management') +
                self._asset_env['modules_event_cloning_js'].urls() +
                self._asset_env['modules_event_management_js'].urls())

    def _getHeader(self):
        return render_header(category=self.event.category, local_tz=self.event.timezone, force_local_tz=True)

    def _getBody(self, params):
        return self._getPageContent(params)

    def _get_breadcrumbs(self):
        return render_breadcrumbs(event=self.event, management=True)


class WPEventManagementLegacy(WPEventManagement):
    """Base class for event management pages without Jinja inheritance.

    Do not use this for anything new.  Instead, use `WPEventManagement`
    directly (or inherit from it) and inherit the associated Jinja template
    from ``events/management/base.html``.
    """

    def _getBody(self, params):
        # Legacy handling for pages that do not use Jinja inheritance.
        tpl = u"{% extends 'events/management/base.html' %}{% block content %}{{ _body | safe }}{% endblock %}"
        body = to_unicode(self._getPageContent(params))
        return render_template_string(tpl, _body=body, **self._kwargs)

    def _getTabContent(self, params):
        raise NotImplementedError

    def _getPageContent(self, params):
        raise NotImplementedError


class WPEventSettings(WPEventManagement):
    template_prefix = 'events/management/'


class WPEventProtection(WPEventManagement):
    template_prefix = 'events/management/'


def render_event_management_header_right(event):
    tpl = get_template_module('events/management/_management_frame.html')
    return tpl.render_event_management_header_right(event=event, event_types=[(et.name, et.title) for et in EventType])
