# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase


class WPLayoutEdit(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/layout/'

    def _setActiveSideMenuItem(self):
        self.extra_menu_items_advanced['layout'].setActive()


class WPMenuEdit(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/layout/'

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['event_management_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._asset_env['modules_event_layout_js'].urls()

    def _setActiveSideMenuItem(self):
        self.extra_menu_items_advanced['menu'].setActive()
