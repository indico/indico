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

from flask import flash, redirect, request, session
from sqlalchemy.orm import defaultload

from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.util import get_event_section_data, make_registration_form, modify_registration
from indico.util.string import camelize_keys


class RegistrationFormMixin:
    """Mixin for single registration form RH"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _process_args(self):
        self.regform = (RegistrationForm.query
                        .filter_by(id=request.view_args['reg_form_id'], is_deleted=False)
                        .options(defaultload('form_items').joinedload('children').joinedload('current_data'))
                        .one())


class RegistrationEditMixin:
    def _process(self):
        form = make_registration_form(self.regform, management=self.management, registration=self.registration)()

        if form.validate_on_submit():
            data = form.data
            notify_user = not self.management or data.pop('notify_user', False)
            if self.management:
                session['registration_notify_user_default'] = notify_user
            modify_registration(self.registration, data, management=self.management, notify_user=notify_user)
            return redirect(self.success_url)
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')

        registration_data = {r.field_data.field.html_field_name: camelize_keys(r.user_data)
                             for r in self.registration.data}
        section_data = camelize_keys(get_event_section_data(self.regform, management=self.management,
                                                            registration=self.registration))

        registration_metadata = {
            'paid': self.registration.is_paid,
            'manager': self.management
        }

        return self.view_class.render_template(self.template_file, self.event,
                                               sections=section_data, regform=self.regform,
                                               registration_data=registration_data,
                                               registration_metadata=registration_metadata,
                                               registration=self.registration)
