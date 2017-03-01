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
from indico.legacy.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase


class WPLayoutEdit(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/layout/'
    sidemenu_option = 'layout'


class WPMenuEdit(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/layout/'
    sidemenu_option = 'menu'

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._asset_env['modules_event_layout_js'].urls()


class WPPage(WPJinjaMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/layout/'

    def __init__(self, rh, conference, **kwargs):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conference, **kwargs)
        self.page = kwargs['page']

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    @property
    def sidemenu_option(self):
        return self.page.menu_entry.id


class WPImages(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/layout/'
    sidemenu_option = 'images'
