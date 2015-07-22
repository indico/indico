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

from indico.web.flask.util import url_for
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WPConferenceModifBase
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import WSimpleNavigationDrawer


class WPVCJinjaMixin(WPJinjaMixin):
    template_prefix = 'vc/'


class WPVCManageEvent(WPVCJinjaMixin, WPConferenceModifBase):

    def getCSSFiles(self):
        return (WPConferenceModifBase.getCSSFiles(self) +
                self._asset_env['vc_sass'].urls())

    def getJSFiles(self):
        return (WPConferenceModifBase.getJSFiles(self) +
                self._asset_env['modules_vc_js'].urls() +
                self._asset_env['zero_clipboard_js'].urls())

    def _setActiveSideMenuItem(self):
        self.extra_menu_items['vc'].setActive()

    def _getPageContent(self, params):
        return WPVCJinjaMixin._getPageContent(self, params)


class WPVCEventPage(WPVCJinjaMixin, WPConferenceDefaultDisplayBase):

    def __init__(self, rh, conf, **kwargs):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf, **kwargs)
        self._conf = conf
        self._aw = rh.getAW()

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + self._asset_env['eventservices_sass'].urls()

    def getJSFiles(self):
        return (WPConferenceDefaultDisplayBase.getJSFiles(self) +
                self._asset_env['zero_clipboard_js'].urls() +
                self._asset_env['modules_event_display_js'].urls() +
                self._asset_env['modules_vc_js'].urls())

    def _getBody(self, params):
        return self._getPageContent(params)

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._sectionMenu.getLinkByName('vc-event-page'))


class WPVCService(WPVCJinjaMixin, WPMainBase):
    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + self._asset_env['overviews_sass'].urls()

    def _getNavigationDrawer(self):
        return WSimpleNavigationDrawer('Videoconference', lambda: url_for('.vc_room_list'))

    def _getBody(self, params):
        return self._getPageContent(params)
