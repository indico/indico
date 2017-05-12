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
from indico.legacy.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WPConferenceModifBase
from indico.legacy.webinterface.pages.main import WPMainBase
from indico.legacy.webinterface.wcomponents import WSimpleNavigationDrawer


class WPVCJinjaMixin(WPJinjaMixin):
    template_prefix = 'vc/'


class WPVCManageEvent(WPVCJinjaMixin, WPConferenceModifBase):
    sidemenu_option = 'videoconference'

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['selectize_css'].urls()

    def getJSFiles(self):
        return (WPConferenceModifBase.getJSFiles(self) +
                self._asset_env['modules_vc_js'].urls() +
                self._asset_env['selectize_js'].urls())

    def _getPageContent(self, params):
        return WPVCJinjaMixin._getPageContent(self, params)


class WPVCEventPage(WPVCJinjaMixin, WPConferenceDefaultDisplayBase):
    menu_entry_name = 'videoconference_rooms'

    def __init__(self, rh, conf, **kwargs):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf, **kwargs)
        self._conf = conf

    def getJSFiles(self):
        return (WPConferenceDefaultDisplayBase.getJSFiles(self) +
                self._asset_env['modules_vc_js'].urls())

    def _getBody(self, params):
        return self._getPageContent(params)


class WPVCService(WPVCJinjaMixin, WPMainBase):
    def _getNavigationDrawer(self):
        return WSimpleNavigationDrawer('Videoconference')

    def _getBody(self, params):
        return self._getPageContent(params)
