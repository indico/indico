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

from flask import request, session
from sqlalchemy.orm import defaultload

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormItemType
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.users.util import get_user_by_email


class RegistrationFormMixin(object):
    """Mixin for single registration form RH"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _checkParams(self):
        self.regform = (RegistrationForm
                        .find(id=request.view_args['reg_form_id'], is_deleted=False)
                        .options(defaultload('form_items').joinedload('children').joinedload('current_data'))
                        .one())


class RegistrationCreationMixin(object):
    """Mixin for a single registration RH"""

    def _save_registration(self, data):
        registration = Registration(registration_form=self.regform, user=get_user_by_email(data['email']))
        for form_item in self.regform.active_fields:
            if form_item.parent.is_manager_only:
                value = form_item.field_impl.default_value
            else:
                value = data.get(form_item.html_field_name)
            form_item.field_impl.save_data(registration, value)
            if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
                setattr(registration, form_item.personal_data_type.column, value)
        registration.init_state(self.event)
        db.session.flush()
        logger.info('New registration %s by %s', registration, session.user)
        return registration
