# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from operator import itemgetter

import wtforms
from marshmallow import ValidationError as MMValidationError
from marshmallow import fields, pre_load, validate, validates_schema
from wtforms.validators import InputRequired, ValidationError

from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import (BillableFieldDataSchema,
                                                            LimitedPlacesBillableFieldDataSchema,
                                                            RegistrationFormBillableField, RegistrationFormFieldBase)
from indico.modules.files.models.files import File
from indico.util.countries import get_countries, get_country
from indico.util.date_time import strftime_all_years
from indico.util.i18n import L_, _
from indico.util.marshmallow import UUIDString
from indico.util.string import normalize_phone_number, validate_email
from indico.web.forms.fields import IndicoRadioField


class TextField(RegistrationFormFieldBase):
    name = 'text'
    wtf_field_class = wtforms.StringField
    mm_field_class = fields.String
    setup_schema_fields = {
        'min_length': fields.Integer(load_default=None, validate=validate.Range(1)),
        'max_length': fields.Integer(load_default=None, validate=validate.Range(1)),
    }


class NumberFieldDataSchema(BillableFieldDataSchema):
    min_value = fields.Integer(load_default=0, validate=validate.Range(0), allow_none=True)
    max_value = fields.Integer(validate=validate.Range(0), allow_none=True)

    @validates_schema(skip_on_field_errors=True)
    def validate_min_max(self, data, **kwargs):
        if data['min_value'] and data['max_value'] and data['min_value'] > data['max_value']:
            raise MMValidationError('Maximum value must be less than minimum value', 'max_value')


class NumberField(RegistrationFormBillableField):
    name = 'number'
    wtf_field_class = wtforms.IntegerField
    required_validator = InputRequired
    mm_field_class = fields.Integer
    setup_schema_base_cls = NumberFieldDataSchema

    def get_validators(self, existing_registration):
        return validate.Range(min=self.form_item.data.get('min_value', None) or 0,
                              max=self.form_item.data.get('max_value', None))

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0) * int(reg_data or 0)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if registration_data.data is None:
            return ''
        return str(registration_data.data) if for_humans else registration_data.data


class TextAreaField(RegistrationFormFieldBase):
    name = 'textarea'
    wtf_field_class = wtforms.StringField
    mm_field_class = fields.String
    setup_schema_fields = {
        'number_of_rows': fields.Integer(load_default=None, validate=validate.Range(1, 20)),
    }


class CheckboxField(RegistrationFormBillableField):
    name = 'checkbox'
    wtf_field_class = wtforms.BooleanField
    mm_field_class = fields.Boolean
    setup_schema_base_cls = LimitedPlacesBillableFieldDataSchema
    friendly_data_mapping = {None: '',
                             True: L_('Yes'),
                             False: L_('No')}

    def calculate_price(self, reg_data, versioned_data):
        if not reg_data:
            return 0
        return versioned_data.get('price', 0)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        return self.friendly_data_mapping[registration_data.data]

    def get_places_used(self):
        places_used = 0
        if self.form_item.data.get('places_limit'):
            for registration in self.form_item.registration_form.active_registrations:
                if self.form_item.id not in registration.data_by_field:
                    continue
                if registration.data_by_field[self.form_item.id].data:
                    places_used += 1
        return places_used

    @property
    def view_data(self):
        return dict(super().view_data, places_used=self.get_places_used())

    @property
    def filter_choices(self):
        return {str(val).lower(): caption for val, caption in self.friendly_data_mapping.items()
                if val is not None}

    def get_validators(self, existing_registration):
        def _check_number_of_places(new_data):
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if not old_data or not self.has_data_changed(new_data, old_data):
                    return True
            if new_data and self.form_item.data.get('places_limit'):
                places_left = self.form_item.data.get('places_limit') - self.get_places_used()
                if not places_left:
                    raise MMValidationError(_('There are no places left for this option.'))
        return _check_number_of_places

    @property
    def default_value(self):
        return None


class DateFieldDataSchema(mm.Schema):
    date_format = fields.String(required=True, validate=validate.OneOf([
        '%d/%m/%Y %I:%M %p',
        '%d.%m.%Y %I:%M %p',
        '%m/%d/%Y %I:%M %p',
        '%m.%d.%Y %I:%M %p',
        '%Y/%m/%d %I:%M %p',
        '%Y.%m.%d %I:%M %p',
        '%d/%m/%Y %H:%M',
        '%d.%m.%Y %H:%M',
        '%m/%d/%Y %H:%M',
        '%m.%d.%Y %H:%M',
        '%Y/%m/%d %H:%M',
        '%Y.%m.%d %H:%M',
        '%d/%m/%Y',
        '%d.%m.%Y',
        '%m/%d/%Y',
        '%m.%d.%Y',
        '%Y/%m/%d',
        '%Y.%m.%d',
        '%m/%Y',
        '%m.%Y',
        '%Y'
    ]))

    @pre_load
    def _merge_date_time_formats(self, data, **kwargs):
        data = data.copy()
        time_format = data.pop('time_format', None)
        if time_format == '12h':
            data['date_format'] += ' %I:%M %p'
        elif time_format == '24h':
            data['date_format'] += ' %H:%M'
        return data


class DateField(RegistrationFormFieldBase):
    name = 'date'
    wtf_field_class = wtforms.StringField
    mm_field_class = fields.String
    setup_schema_base_cls = DateFieldDataSchema

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        data = {}
        time_date_formats = unversioned_data['date_format'].split(' ', 1)
        data['date_format'] = time_date_formats[0]
        if len(time_date_formats) > 1:
            if time_date_formats[1] == '%I:%M %p':
                data['time_format'] = '12h'
            elif time_date_formats[1] == '%H:%M':
                data['time_format'] = '24h'
        return data

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        date_string = registration_data.data
        if not date_string:
            return ''
        elif for_search:
            return date_string  # already in isoformat
        dt = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
        return strftime_all_years(dt, self.form_item.data['date_format'])

    @property
    def view_data(self):
        has_time = ' ' in self.form_item.data['date_format']
        return dict(super().view_data, has_time=has_time)


class BooleanField(RegistrationFormBillableField):
    name = 'bool'
    wtf_field_class = IndicoRadioField
    required_validator = InputRequired
    mm_field_class = fields.Boolean
    mm_field_kwargs = {'allow_none': True}
    setup_schema_base_cls = LimitedPlacesBillableFieldDataSchema
    setup_schema_fields = {
        'default_value': fields.String(load_default='', validate=validate.OneOf(['', 'yes', 'no'])),
    }
    friendly_data_mapping = {None: '',
                             True: L_('Yes'),
                             False: L_('No')}

    @property
    def wtf_field_kwargs(self):
        return {'choices': [('yes', _('Yes')), ('no', _('No'))],
                'coerce': lambda x: {'yes': True, 'no': False}.get(x, None)}

    @property
    def filter_choices(self):
        return {str(val).lower(): caption for val, caption in self.friendly_data_mapping.items()
                if val is not None}

    @property
    def view_data(self):
        return dict(super().view_data, places_used=self.get_places_used())

    def get_validators(self, existing_registration):
        def _check_number_of_places(new_data):
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if not old_data or not self.has_data_changed(new_data, old_data):
                    return True
            if new_data and self.form_item.data.get('places_limit'):
                places_left = self.form_item.data.get('places_limit') - self.get_places_used()
                if new_data and not places_left:
                    raise MMValidationError(_('There are no places left for this option.'))
        return _check_number_of_places

    @property
    def default_value(self):
        return None

    def get_places_used(self):
        places_used = 0
        if self.form_item.data.get('places_limit'):
            for registration in self.form_item.registration_form.active_registrations:
                if self.form_item.id not in registration.data_by_field:
                    continue
                if registration.data_by_field[self.form_item.id].data:
                    places_used += 1
        return places_used

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0) if reg_data else 0

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        return self.friendly_data_mapping[registration_data.data]


class PhoneField(RegistrationFormFieldBase):
    name = 'phone'
    wtf_field_class = wtforms.StringField
    wtf_field_kwargs = {'filters': [lambda x: normalize_phone_number(x) if x else '']}
    mm_field_class = fields.String


class CountryField(RegistrationFormFieldBase):
    name = 'country'
    wtf_field_class = wtforms.SelectField
    mm_field_class = fields.String

    @property
    def wtf_field_kwargs(self):
        return {'choices': sorted(get_countries().items(), key=itemgetter(1))}

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        choices = sorted(({'caption': v, 'countryKey': k} for k, v in get_countries().items()),
                         key=itemgetter('caption'))
        return {'choices': choices}

    @property
    def filter_choices(self):
        return dict(self.wtf_field_kwargs['choices'])

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if registration_data.data == 'None':
            # XXX: Not sure where this garbage data is coming from, but it resulted in
            # this method returning `None` and thus breaking the participant list..
            return ''
        return get_country(registration_data.data) if registration_data.data else ''


class FileField(RegistrationFormFieldBase):
    name = 'file'
    wtf_field_class = wtforms.StringField
    mm_field_class = UUIDString

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False):
        data = {'field_data': self.form_item.current_data}
        if not value:
            data['file'] = None
            return data

        if file := File.query.filter(File.uuid == value, ~File.claimed).first():
            # we have a file -> always save it
            data['file'] = file
            data['data'] = str(file.uuid)
        else:
            # TODO: Handle this case when we remove wtforms from regform submission
            raise ValidationError(_('Invalid file UUID'))
        return data

    @property
    def default_value(self):
        return None

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if not registration_data:
            return ''
        return registration_data.filename


class EmailField(RegistrationFormFieldBase):
    name = 'email'
    wtf_field_class = wtforms.StringField
    wtf_field_kwargs = {'filters': [lambda x: x.lower() if x else x]}
    mm_field_class = fields.Email

    def get_validators(self, existing_registration):
        def _indico_email(value):
            if value and not validate_email(value):
                raise MMValidationError(_('Invalid email address'))

        return _indico_email
