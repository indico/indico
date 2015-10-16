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

from MaKaC.webinterface.meeting import WPMeetingDisplay
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.webinterface.simple_event import WPSimpleEventDisplay


class WPManageRegistration(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/registration/'
    sidemenu_option = 'registration'

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._asset_env['modules_registration_js'].urls()

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['registration_sass'].urls()


class DisplayRegistrationFormMixin(WPJinjaMixin):
    template_prefix = 'events/registration/'
    base_class = None

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return self.base_class.getJSFiles(self) + self._asset_env['modules_registration_js'].urls()

    def getCSSFiles(self):
        return (self.base_class.getCSSFiles(self) + self._asset_env['registration_sass'].urls()
                                                  + self._asset_env['payment_sass'].urls())


class WPDisplayRegistrationFormConference(DisplayRegistrationFormMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/registration/'
    base_class = WPConferenceDefaultDisplayBase
    menu_entry_name = 'registration'


class WPDisplayRegistrationFormMeeting(DisplayRegistrationFormMixin, WPMeetingDisplay):
    template_prefix = 'events/registration/'
    base_class = WPMeetingDisplay


class WPDisplayRegistrationFormLecture(DisplayRegistrationFormMixin, WPSimpleEventDisplay):
    template_prefix = 'events/registration/'
    base_class = WPSimpleEventDisplay
