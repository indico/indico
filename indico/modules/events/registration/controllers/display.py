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

from flask import request

from indico.modules.events.registration.models.registration_forms import RegistrationForm
from indico.modules.events.registration.util import get_event_section_data
from indico.modules.events.registration.views import (WPDisplayRegistrationFormConference,
                                                      WPDisplayRegistrationFormMeeting,
                                                      WPDisplayRegistrationFormLecture)
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHRegistrationFormDisplayBase(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.event = self._conf

    @property
    def view_class(self):
        mapping = {
            'conference': WPDisplayRegistrationFormConference,
            'meeting': WPDisplayRegistrationFormMeeting,
            'simple_event': WPDisplayRegistrationFormLecture
        }
        return mapping[self.event.getType()]


class RHRegistrationFormList(RHRegistrationFormDisplayBase):
    """List of all registration forms in the event"""

    def _process(self):
        regforms = RegistrationForm.find_all(is_active=True, event_id=int(self.event.id))
        return self.view_class.render_template('display/regforms_list.html', self.event, regforms=regforms,
                                               event=self.event)

