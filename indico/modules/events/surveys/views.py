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
from indico.modules.events.views import WPConferenceDisplayBase, WPSimpleEventDisplayBase
from indico.web.views import WPJinjaMixin


class WPManageSurvey(WPEventManagement):
    template_prefix = 'events/surveys/'
    sidemenu_option = 'surveys'

    def getJSFiles(self):
        return WPEventManagement.getJSFiles(self) + self._asset_env['modules_surveys_js'].urls()


class WPSurveyResults(WPManageSurvey):
    template_prefix = 'events/surveys/'

    def getCSSFiles(self):
        return (WPManageSurvey.getCSSFiles(self) +
                self._asset_env['chartist_css'].urls())

    def getJSFiles(self):
        return (WPManageSurvey.getJSFiles(self) +
                self._asset_env['chartist_js'].urls())


class DisplaySurveyMixin(WPJinjaMixin):
    template_prefix = 'events/surveys/'
    base_class = None

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return self.base_class.getJSFiles(self) + self._asset_env['modules_surveys_js'].urls()


class WPDisplaySurveyConference(DisplaySurveyMixin, WPConferenceDisplayBase):
    template_prefix = 'events/surveys/'
    base_class = WPConferenceDisplayBase
    menu_entry_name = 'surveys'


class WPDisplaySurveySimpleEvent(DisplaySurveyMixin, WPSimpleEventDisplayBase):
    template_prefix = 'events/surveys/'
    base_class = WPSimpleEventDisplayBase
