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

from flask import request
from sqlalchemy.orm import contains_eager, defaultload

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.registration.controllers import RegistrationFormMixin
from indico.modules.events.registration.lists import RegistrationListGenerator
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration


class RHManageRegFormsBase(RHManageEventBase):
    """Base class for all registration management RHs"""

    ROLE = 'registration'


class RHManageRegFormBase(RegistrationFormMixin, RHManageRegFormsBase):
    """Base class for a specific registration form"""

    def _checkParams(self, params):
        RHManageRegFormsBase._checkParams(self, params)
        RegistrationFormMixin._checkParams(self)
        self.list_generator = RegistrationListGenerator(regform=self.regform)


class RHManageRegistrationBase(RHManageRegFormBase):
    """Base class for a specific registration"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    def _checkParams(self, params):
        RHManageRegFormBase._checkParams(self, params)
        self.registration = (Registration
                             .find(Registration.id == request.view_args['registration_id'],
                                   ~Registration.is_deleted,
                                   ~RegistrationForm.is_deleted)
                             .join(Registration.registration_form)
                             .options(contains_eager(Registration.registration_form)
                                      .defaultload('form_items')
                                      .joinedload('children'))
                             .options(defaultload(Registration.data)
                                      .joinedload('field_data'))
                             .one())
