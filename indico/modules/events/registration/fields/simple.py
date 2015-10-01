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

import mimetypes

import wtforms
from wtforms.validators import NumberRange

from indico.modules.events.registration.fields.base import RegistrationFormFieldBase
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.fs import secure_filename
from indico.util.string import crc32
from indico.web.forms.validators import IndicoEmail


class TextField(RegistrationFormFieldBase):
    name = 'text'
    wtf_field_class = wtforms.StringField


class NumberField(RegistrationFormFieldBase):
    name = 'number'
    wtf_field_class = wtforms.IntegerField

    @property
    def validators(self):
        min_value = self.form_item.current_data.versioned_data.get('minValue', None)
        return [NumberRange(min=min_value)] if min_value else None


class TextAreaField(RegistrationFormFieldBase):
    name = 'textarea'
    wtf_field_class = wtforms.StringField


class SelectField(RegistrationFormFieldBase):
    name = 'radio'
    wtf_field_class = wtforms.StringField

    @property
    def default_value(self):
        data = self.form_item.current_data.versioned_data
        try:
            default_item = data['defaultItem']
        except KeyError:
            return None
        return next((x['id'] for x in data['radioitems'] if x['caption'] == default_item), None)


class CheckboxField(RegistrationFormFieldBase):
    name = 'checkbox'
    wtf_field_class = wtforms.StringField

    def save_data(self, registration, value):
        if not value:
            value = 'off'
        registration.data.append(RegistrationData(field_data_id=self.form_item.current_data_id, data=value))


class DateField(RegistrationFormFieldBase):
    name = 'date'
    wtf_field_class = wtforms.StringField


class BooleanField(RegistrationFormFieldBase):
    name = 'yes/no'
    wtf_field_class = wtforms.StringField


class PhoneField(RegistrationFormFieldBase):
    name = 'telephone'
    wtf_field_class = wtforms.StringField


class CountryField(RegistrationFormFieldBase):
    name = 'country'
    wtf_field_class = wtforms.StringField


class FileField(RegistrationFormFieldBase):
    name = 'file'
    wtf_field_class = wtforms.FileField

    def save_data(self, registration, value):
        if value is None:
            return
        f = value.file
        content = f.read()
        metadata = {
            'hash': crc32(content),
            'size': len(content),
            'filename': secure_filename(value.filename, 'registration_form_file'),
            'content_type': mimetypes.guess_type(value.filename)[0] or value.mimetype or 'application/octet-stream'
        }

        registration.data.append(RegistrationData(field_data_id=self.form_item.current_data_id, file=content,
                                                  file_metadata=metadata))


class EmailField(RegistrationFormFieldBase):
    name = 'email'
    wtf_field_class = wtforms.StringField

    @property
    def validators(self):
        return [IndicoEmail()]
