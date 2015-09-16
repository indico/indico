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

from wtforms import StringField, HiddenField, FileField, IntegerField
from wtforms.validators import NumberRange

from indico.modules.events.registration.fields.base import RegistrationFormFieldBase


class FreeTextField(RegistrationFormFieldBase):
    name = 'label'
    wtf_field_class = HiddenField

    def save_data(self, registration, value):
        return


class TextField(RegistrationFormFieldBase):
    name = 'text'
    wtf_field_class = StringField


class NumberField(RegistrationFormFieldBase):
    name = 'number'
    wtf_field_class = IntegerField

    @property
    def validators(self):
        min_value = self.form_item.current_data.data.get('minValue', None)
        return [NumberRange(min=min_value)] if min_value else None


class TextAreaField(RegistrationFormFieldBase):
    name = 'textarea'
    wtf_field_class = StringField


class SelectField(RegistrationFormFieldBase):
    name = 'radio'
    wtf_field_class = StringField


class CheckboxField(RegistrationFormFieldBase):
    name = 'checkbox'
    wtf_field_class = StringField

    def save_data(self, registration, value):
        if not value:
            value = 'off'
        registration.data.append(RegistrationData(field_data_id=self.form_item.current_data_id, data=value))


class DateField(RegistrationFormFieldBase):
    name = 'date'
    wtf_field_class = StringField


class BooleanField(RegistrationFormFieldBase):
    name = 'yes/no'
    wtf_field_class = StringField


class PhoneField(RegistrationFormFieldBase):
    name = 'telephone'
    wtf_field_class = StringField


class CountryField(RegistrationFormFieldBase):
    name = 'country'
    wtf_field_class = StringField


class FileField(RegistrationFormFieldBase):
    name = 'file'
    wtf_field_class = FileField

    def save_data(self, registration, value):
        pass
