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

from indico.legacy.webinterface.pages.base import WPJinjaMixin
from indico.modules.events.management.views import WPEventManagementLegacy
from indico.modules.events.views import WPConferenceDisplayLegacyBase


class WPLayoutEdit(WPJinjaMixin, WPEventManagementLegacy):
    template_prefix = 'events/layout/'
    sidemenu_option = 'layout'


class WPMenuEdit(WPJinjaMixin, WPEventManagementLegacy):
    template_prefix = 'events/layout/'
    sidemenu_option = 'menu'

    def getJSFiles(self):
        return WPEventManagementLegacy.getJSFiles(self) + self._asset_env['modules_event_layout_js'].urls()


class WPPage(WPJinjaMixin, WPConferenceDisplayLegacyBase):
    template_prefix = 'events/layout/'

    def __init__(self, rh, conference, **kwargs):
        self.page = kwargs['page']
        WPConferenceDisplayLegacyBase.__init__(self, rh, conference, **kwargs)

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    @property
    def sidemenu_option(self):
        return self.page.menu_entry.id


class WPImages(WPJinjaMixin, WPEventManagementLegacy):
    template_prefix = 'events/layout/'
    sidemenu_option = 'images'
