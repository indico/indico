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
from indico.util.mathjax import MathjaxMixin


class WPManageContributions(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/contributions/'
    sidemenu_option = 'contributions'

    def getJSFiles(self):
        return (WPEventManagement.getJSFiles(self) +
                self._asset_env['modules_contributions_js'].urls() +
                self._asset_env['markdown_js'].urls())

    def _getHeadContent(self):
        return WPEventManagement._getHeadContent(self) + MathjaxMixin._getHeadContent(self)


class WPContributionsDisplayBase(WPConferenceDisplayBase):
    template_prefix = 'events/contributions/'

    def getJSFiles(self):
        return (WPConferenceDisplayBase.getJSFiles(self) +
                self._asset_env['modules_contributions_js'].urls() +
                self._asset_env['modules_event_display_js'].urls())


class WPMyContributions(WPContributionsDisplayBase):
    menu_entry_name = 'my_contributions'


class WPContributions(WPContributionsDisplayBase):
    menu_entry_name = 'contributions'

    def getJSFiles(self):
        return WPContributionsDisplayBase.getJSFiles(self) + self._asset_env['dropzone_js'].urls()

    def getCSSFiles(self):
        return WPContributionsDisplayBase.getCSSFiles(self) + self._asset_env['dropzone_css'].urls()


class WPAuthorList(WPContributionsDisplayBase):
    menu_entry_name = 'author_index'


class WPSpeakerList(WPContributionsDisplayBase):
    menu_entry_name = 'speaker_index'
