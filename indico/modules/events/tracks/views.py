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

from indico.util.mathjax import MathjaxMixin
from indico.legacy.webinterface.pages.base import WPJinjaMixin
from indico.legacy.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase


class WPManageTracks(MathjaxMixin, WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/tracks/'
    sidemenu_option = 'program'

    def getJSFiles(self):
        return (WPConferenceModifBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['modules_tracks_js'].urls())

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + MathjaxMixin._getHeadContent(self)


class WPDisplayTracks(MathjaxMixin, WPJinjaMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/tracks/'
    menu_entry_name = 'program'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return (WPConferenceDefaultDisplayBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['modules_tracks_js'].urls())

    def _getHeadContent(self):
        return WPConferenceDefaultDisplayBase._getHeadContent(self) + MathjaxMixin._getHeadContent(self)
