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

from indico.modules.events.models.events import EventType
from indico.web.flask.templating import get_template_module
from indico.legacy.webinterface.pages.base import WPJinjaMixin
from indico.legacy.webinterface.pages.conferences import WPConferenceModifBase


class WPEventManagement(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/management/'

    def _getPageContent(self, params):
        return WPJinjaMixin._getPageContent(self, params)


class WPEventSettings(WPEventManagement):
    sidemenu_option = 'settings'


class WPEventProtection(WPEventManagement):
    sidemenu_option = 'protection'


# TODO: once all legacy event management code is gone, use jinja inheritance like we do in category management
def render_event_management_frame(event, body, active_menu_item):
    tpl = get_template_module('events/management/_management_frame.html')
    return tpl.render_management_frame(event=event,
                                       body=body,
                                       active_menu_item=active_menu_item,
                                       event_types=[(et.name, et.title) for et in EventType])


def render_event_management_header_right(event):
    tpl = get_template_module('events/management/_management_frame.html')
    return tpl.render_event_management_header_right(event=event, event_types=[(et.name, et.title) for et in EventType])
