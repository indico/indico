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
from indico.modules.events.views import WPSimpleEventDisplayBase


class WPManageSurvey(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/surveys/'
    sidemenu_option = 'surveys'

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._asset_env['modules_surveys_js'].urls()


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


class WPDisplaySurveyConference(DisplaySurveyMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/surveys/'
    base_class = WPConferenceDefaultDisplayBase
    menu_entry_name = 'surveys'


class WPDisplaySurveySimpleEvent(DisplaySurveyMixin, WPSimpleEventDisplayBase):
    template_prefix = 'events/surveys/'
    base_class = WPSimpleEventDisplayBase
