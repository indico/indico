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

from flask import flash, redirect, request
from sqlalchemy.orm import defaultload

from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.util import modify_registration, get_event_section_data, make_registration_form
from indico.modules.payment import event_settings as payment_event_settings
from indico.util.string import camelize_keys


class RegistrationFormMixin:
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


class RegistrationEditMixin:
    def _process(self):
        form = make_registration_form(self.regform, management=self.management, registration=self.registration)()

        if form.validate_on_submit():
            modify_registration(self.registration, form.data, management=self.management)
            return redirect(self.success_url)
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')

        registration_data = {r.field_data.field.html_field_name: camelize_keys(r.rdata) for r in self.registration.data}
        section_data = camelize_keys(get_event_section_data(self.regform, management=self.management,
                                                            registration=self.registration))

        registration_data.update({
            'paid': self.registration.is_paid,
            'manager': self.management
        })

        return self.view_class.render_template(self.template_file, self.event, event=self.event,
                                               sections=section_data, regform=self.regform,
                                               currency=payment_event_settings.get(self.event, 'currency'),
                                               registration_data=registration_data,
                                               registration=self.registration)
