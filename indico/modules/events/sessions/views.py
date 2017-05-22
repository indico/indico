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
from indico.legacy.webinterface.pages.conferences import WPConferenceDefaultDisplayBase
from indico.modules.events.management.views import WPEventManagement


class WPManageSessions(WPEventManagement):
    template_prefix = 'events/sessions/'
    sidemenu_option = 'sessions'

    def getJSFiles(self):
        return WPEventManagement.getJSFiles(self) + self._asset_env['modules_sessions_js'].urls()


class WPDisplaySession(WPJinjaMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/sessions/'
    menu_entry_name = 'timetable'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + self._asset_env['modules_timetable_js'].urls()


class WPDisplayMySessionsConference(WPDisplaySession):
    menu_entry_name = 'my_sessions'
