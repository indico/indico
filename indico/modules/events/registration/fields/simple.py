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
from copy import deepcopy
from datetime import datetime
from uuid import uuid4

import wtforms
from wtforms.validators import NumberRange, ValidationError

from indico.modules.events.registration.fields.base import (RegistrationFormFieldBase, RegistrationFormBillableField,
                                                            RegistrationFormBillableItemsField)
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.util.date_time import iterdays, format_date
from indico.util.fs import secure_filename
from indico.util.i18n import _, L_
from indico.util.string import crc32, normalize_phone_number, snakify_keys
from indico.web.forms.fields import IndicoRadioField, JSONField
from indico.web.forms.validators import IndicoEmail
from MaKaC.webinterface.common.countries import CountryHolder


class TextField(RegistrationFormFieldBase):
    name = 'text'
    wtf_field_class = wtforms.StringField


class NumberField(RegistrationFormBillableField):
    name = 'number'
    wtf_field_class = wtforms.IntegerField

    @property
    def validators(self):
        min_value = self.form_item.data.get('min_value', None)
        return [NumberRange(min=min_value)] if min_value else None

    def calculate_price(self, registration_data):
        data = registration_data.field_data.versioned_data
        if not data.get('is_billable'):
            return 0
        return data.get('price', 0) * int(registration_data.data or 0)

    def get_friendly_data(self, registration_data):
        if registration_data.data is None:
            return ''
        return registration_data.data


class TextAreaField(RegistrationFormFieldBase):
    name = 'textarea'
    wtf_field_class = wtforms.StringField


class ChoiceBaseField(RegistrationFormBillableItemsField):
    versioned_data_fields = RegistrationFormBillableItemsField.versioned_data_fields | {'choices'}
    has_default_item = False

    @property
    def wtf_field_kwargs(self):
        return {'choices': self.form_item.data['captions'].items()}

    @property
    def view_data(self):
        items = deepcopy(self.form_item.versioned_data['choices'])
        for item in items:
            item['caption'] = self.form_item.data['captions'][item['id']]
        return {'choices': items}

    @property
    def filter_choices(self):
        return self.form_item.data['captions']

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super(ChoiceBaseField, cls).process_field_data(data, old_data,
                                                                                          old_versioned_data)
        items = [x for x in versioned_data['choices'] if not x.get('remove')]
        captions = dict(old_data['captions']) if old_data is not None else {}
        if cls.has_default_item:
            unversioned_data.setdefault('default_item', None)
        for item in items:
            if 'id' not in item:
                item['id'] = unicode(uuid4())
            item.setdefault('is_billable', False)
            item['price'] = float(item['price']) if item.get('price') else 0
            item['places_limit'] = int(item['places_limit']) if item.get('places_limit') else 0
            item['max_extra_slots'] = int(item['max_extra_slots']) if item.get('max_extra_slots') else 0
            if cls.has_default_item and unversioned_data['default_item'] in {item['caption'], item['id']}:
                unversioned_data['default_item'] = item['id']
            captions[item['id']] = item.pop('caption')
        versioned_data['choices'] = items
        unversioned_data['captions'] = captions
        return unversioned_data, versioned_data


class SingleChoiceField(ChoiceBaseField):
    name = 'single_choice'
    wtf_field_class = wtforms.SelectField
    has_default_item = True

    @property
    def wtf_field_kwargs(self):
        return dict(super(SingleChoiceField, self).wtf_field_kwargs,
                    coerce=lambda x: x if x != 'None' else None)

    @property
    def default_value(self):
        data = self.form_item.data
        versioned_data = self.form_item.versioned_data
        try:
            default_item = data['default_item']
        except KeyError:
            return None
        # only use the default item if it exists in the current version
        return default_item if any(x['id'] == default_item for x in versioned_data['choices']) else None

    def calculate_price(self, registration_data):
        data = registration_data.field_data.versioned_data
        item = next((x for x in data['choices'] if registration_data.data == x['id'] and x['is_billable']), None)
        return item['price'] if item else 0

    def get_friendly_data(self, registration_data):
        if not registration_data.data:
            return ''
        return registration_data.field_data.field.data['captions'][registration_data.data]


class CheckboxField(RegistrationFormBillableField):
    name = 'checkbox'
    wtf_field_class = wtforms.BooleanField
    friendly_data_mapping = {None: '',
                             True: L_('Yes'),
                             False: L_('No')}

    def calculate_price(self, registration_data):
        data = registration_data.field_data.versioned_data
        if not data.get('is_billable') or not registration_data.data:
            return 0
        return data.get('price', 0)

    def get_friendly_data(self, registration_data):
        return self.friendly_data_mapping[registration_data.data]

    @property
    def filter_choices(self):
        return {unicode(val).lower(): caption for val, caption in self.friendly_data_mapping.iteritems()
                if val is not None}


class DateField(RegistrationFormFieldBase):
    name = 'date'
    wtf_field_class = wtforms.StringField

    def save_data(self, registration, value):
        # TODO: fix client side code to send us time information then adapt the next line
        date_format = self.form_item.data['date_format'].split(' ')[0]
        value = datetime.strptime(value, date_format).isoformat()
        return super(DateField, self).save_data(registration, value)

    def get_friendly_data(self, registration_data):
        date_string = registration_data.data
        if not date_string:
            return ''
        dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
        return dt.strftime(self.form_item.data['date_format'])


class BooleanField(RegistrationFormBillableField):
    name = 'bool'
    wtf_field_class = IndicoRadioField
    friendly_data_mapping = {None: '',
                             True: L_('Yes'),
                             False: L_('No')}

    @property
    def wtf_field_kwargs(self):
        return {'choices': [(True, _('Yes')), (False, _('No'))],
                'coerce': lambda x: {'yes': True, 'no': False}.get(x, None)}

    @property
    def filter_choices(self):
        return {unicode(val).lower(): caption for val, caption in self.friendly_data_mapping.iteritems()
                if val is not None}

    def calculate_price(self, registration_data):
        data = registration_data.field_data.versioned_data
        if not data.get('is_billable'):
            return 0
        return data.get('price', 0) if registration_data.data else 0

    def get_friendly_data(self, registration_data):
        return self.friendly_data_mapping[registration_data.data]


class PhoneField(RegistrationFormFieldBase):
    name = 'phone'
    wtf_field_class = wtforms.StringField
    wtf_field_kwargs = {'filters': [lambda x: normalize_phone_number(x) if x else '']}


class CountryField(RegistrationFormFieldBase):
    name = 'country'
    wtf_field_class = wtforms.SelectField

    @property
    def wtf_field_kwargs(self):
        return {'choices': CountryHolder.getCountries().items()}

    @property
    def view_data(self):
        return {'choices': [{'caption': v, 'countryKey': k} for k, v in CountryHolder.getCountries().iteritems()]}

    @property
    def filter_choices(self):
        return dict(self.wtf_field_kwargs['choices'])

    def get_friendly_data(self, registration_data):
        return CountryHolder.getCountries()[registration_data.data]


class FileField(RegistrationFormFieldBase):
    name = 'file'
    wtf_field_class = wtforms.FileField

    def save_data(self, registration, value):
        if value is None or not value.filename:
            return
        content = value.file.read()
        metadata = {
            'hash': crc32(content),
            'size': len(content),
            'filename': secure_filename(value.filename, 'registration_form_file'),
            'content_type': mimetypes.guess_type(value.filename)[0] or value.mimetype or 'application/octet-stream'
        }

        registration.data.append(RegistrationData(field_data=self.form_item.current_data, file=content,
                                                  file_metadata=metadata))

    @property
    def default_value(self):
        return None

    def get_friendly_data(self, registration_data):
        if not registration_data:
            return ''
        return registration_data.file_metadata['filename']


class EmailField(RegistrationFormFieldBase):
    name = 'email'
    wtf_field_class = wtforms.StringField
    wtf_field_kwargs = {'filters': [lambda x: x.lower() if x else x]}

    @property
    def validators(self):
        return [IndicoEmail()]


class AccommodationField(RegistrationFormBillableItemsField):
    name = 'accommodation'
    wtf_field_class = JSONField
    versioned_data_fields = RegistrationFormBillableField.versioned_data_fields | {'choices'}

    @classmethod
    def process_field_data(cls, data, old_data=None, old_versioned_data=None):
        unversioned_data, versioned_data = super(AccommodationField, cls).process_field_data(data, old_data,
                                                                                             old_versioned_data)
        items = [x for x in versioned_data['choices'] if not x.get('remove')]
        captions = dict(old_data['captions']) if old_data is not None else {}
        for item in items:
            if 'id' not in item:
                item['id'] = unicode(uuid4())
            item.setdefault('is_billable', False)
            item['price'] = float(item['price']) if item.get('price') else 0
            item['places_limit'] = int(item['places_limit']) if item.get('places_limit') else 0
            captions[item['id']] = item.pop('caption')
        for key in {'arrival_date_from', 'arrival_date_to', 'departure_date_from', 'departure_date_to'}:
            unversioned_data[key] = _to_machine_date(unversioned_data[key])
        versioned_data['choices'] = items
        unversioned_data['captions'] = captions
        return unversioned_data, versioned_data

    @property
    def view_data(self):
        data = {}
        arrival_date_from = _to_date(self.form_item.data['arrival_date_from'])
        arrival_date_to = _to_date(self.form_item.data['arrival_date_to'])
        departure_date_from = _to_date(self.form_item.data['departure_date_from'])
        departure_date_to = _to_date(self.form_item.data['departure_date_to'])
        data['arrival_dates'] = [format_date(date) for date in iterdays(arrival_date_from, arrival_date_to)]
        data['departure_dates'] = [format_date(date) for date in iterdays(departure_date_from, departure_date_to)]
        items = deepcopy(self.form_item.versioned_data['choices'])
        for item in items:
            item['caption'] = self.form_item.data['captions'][item['id']]
        data['choices'] = items
        return data

    @property
    def validators(self):
        def stay_dates_valid(form, field):
            data = snakify_keys(field.data)
            if _to_date(data['arrival_date']) > _to_date(data['departure_date']):
                raise ValidationError(_("Arrival date can't be set after the departure date."))
        return [stay_dates_valid]

    def get_friendly_data(self, registration_data):
        friendly_data = dict(registration_data.data)
        unversioned_data = registration_data.field_data.field.data
        friendly_data['choice'] = unversioned_data['captions'][friendly_data['choice']]
        friendly_data['arrival_date'] = _to_date(friendly_data['arrival_date'])
        friendly_data['departure_date'] = _to_date(friendly_data['departure_date'])
        friendly_data['nights'] = (friendly_data['departure_date'] - friendly_data['arrival_date']).days
        return friendly_data

    def calculate_price(self, registration_data):
        data = registration_data.field_data.versioned_data
        reg_data = registration_data.data
        item = next((x for x in data['choices']
                     if reg_data['choice'] == x['id'] and x.get('is_billable', False)), None)
        if not item or not item['price']:
            return 0
        nights = (_to_date(reg_data['departure_date']) - _to_date(reg_data['arrival_date'])).days
        return item['price'] * nights

    def save_data(self, registration, value):
        data = {'choice': value['choice'], 'arrival_date': value['arrivalDate'],
                'departure_date': value['departureDate']}
        return super(AccommodationField, self).save_data(registration, data)


def _to_machine_date(date):
    return datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')


def _to_date(date):
    return datetime.strptime(date, '%Y-%m-%d').date()


class MultiChoiceField(ChoiceBaseField):
    name = 'multi_choice'
    wtf_field_class = wtforms.SelectMultipleField

    def get_friendly_data(self, registration_data):
        reg_data = registration_data.data
        return [self.form_item.data['captions'][x] for x in reg_data]

    def calculate_price(self, registration_data):
        reg_data = [x for x in self.form_item.versioned_data['choices'] if x['id'] in registration_data.data]
        return sum(item['price'] for item in reg_data if item['is_billable'])
