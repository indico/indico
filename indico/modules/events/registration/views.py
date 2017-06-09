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
from indico.modules.events.models.events import EventType
from indico.modules.events.views import WPSimpleEventDisplayBase


class WPManageRegistration(WPEventManagement):
    template_prefix = 'events/registration/'

    def __init__(self, rh, event_, active_menu_item=None, **kwargs):
        self.regform = kwargs.get('regform')
        self.registration = kwargs.get('registration')
        WPEventManagement.__init__(self, rh, event_, active_menu_item, **kwargs)

    @property
    def sidemenu_option(self):
        if self.event.type_ != EventType.conference:
            regform = self.regform
            if not regform:
                if self.registration:
                    regform = self.registration.registration_form
            if regform and regform.is_participation:
                return 'participants'
        return 'registration'

    def getJSFiles(self):
        return WPEventManagement.getJSFiles(self) + self._asset_env['modules_registration_js'].urls()


class WPManageRegistrationStats(WPManageRegistration):
    def getJSFiles(self):
        return (WPManageRegistration.getJSFiles(self) +
                self._asset_env['statistics_js'].urls() +
                self._includeJSPackage('jqplot_js', prefix=''))


class WPManageParticipants(WPManageRegistration):
    sidemenu_option = 'participants'


class DisplayRegistrationFormMixin(WPJinjaMixin):
    template_prefix = 'events/registration/'
    base_class = None

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return self.base_class.getJSFiles(self) + self._asset_env['modules_registration_js'].urls()


class WPDisplayRegistrationFormConference(DisplayRegistrationFormMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/registration/'
    base_class = WPConferenceDefaultDisplayBase
    menu_entry_name = 'registration'


class WPDisplayRegistrationParticipantList(WPDisplayRegistrationFormConference):
    menu_entry_name = 'participants'


class WPDisplayRegistrationFormSimpleEvent(DisplayRegistrationFormMixin, WPSimpleEventDisplayBase):
    template_prefix = 'events/registration/'
    base_class = WPSimpleEventDisplayBase
