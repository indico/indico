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
from indico.util.mathjax import MathjaxMixin


class WPManageTracks(MathjaxMixin, WPJinjaMixin, WPEventManagementLegacy):
    template_prefix = 'events/tracks/'
    sidemenu_option = 'program'

    def getJSFiles(self):
        return (WPEventManagementLegacy.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['modules_tracks_js'].urls())

    def _getHeadContent(self):
        return WPEventManagementLegacy._getHeadContent(self) + MathjaxMixin._getHeadContent(self)


class WPDisplayTracks(MathjaxMixin, WPJinjaMixin, WPConferenceDisplayLegacyBase):
    template_prefix = 'events/tracks/'
    menu_entry_name = 'program'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return (WPConferenceDisplayLegacyBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['modules_tracks_js'].urls())

    def _getHeadContent(self):
        return WPConferenceDisplayLegacyBase._getHeadContent(self) + MathjaxMixin._getHeadContent(self)
