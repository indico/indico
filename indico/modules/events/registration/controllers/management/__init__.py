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

from indico.modules.events.registration.models.forms import RegistrationForm
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageRegFormsBase(RHConferenceModifBase):
    """Base class for all registration management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf
        self.event_new = self.event.as_event


class RHManageRegFormBase(RHManageRegFormsBase):
    """Base class for a specific registration form"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _checkParams(self, params):
        RHManageRegFormsBase._checkParams(self, params)
        self.regform = RegistrationForm.find_one(id=request.view_args['reg_form_id'], is_deleted=False)
