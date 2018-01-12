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

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase


class WPLayoutEdit(WPEventManagement):
    template_prefix = 'events/layout/'
    sidemenu_option = 'layout'


class WPMenuEdit(WPEventManagement):
    template_prefix = 'events/layout/'
    sidemenu_option = 'menu'

    def getJSFiles(self):
        return WPEventManagement.getJSFiles(self) + self._asset_env['modules_event_layout_js'].urls()


class WPImages(WPEventManagement):
    template_prefix = 'events/layout/'
    sidemenu_option = 'images'


class WPPage(WPConferenceDisplayBase):
    template_prefix = 'events/layout/'

    def __init__(self, rh, conference, **kwargs):
        self.page = kwargs['page']
        WPConferenceDisplayBase.__init__(self, rh, conference, **kwargs)

    @property
    def sidemenu_option(self):
        return self.page.menu_entry.id
