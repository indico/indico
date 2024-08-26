# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

from marshmallow import ValidationError, fields, pre_load, validate, validates_schema
from PIL import Image

from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import (BillableFieldDataSchema,
                                                            LimitedPlacesBillableFieldDataSchema,
                                                            RegistrationFormBillableField, RegistrationFormFieldBase)
from indico.modules.files.models.files import File
from indico.util.countries import get_countries, get_country
from indico.util.date_time import strftime_all_years
from indico.util.i18n import L_, _
from indico.util.marshmallow import LowercaseString, UUIDString
from indico.util.signals import make_interceptable
from indico.util.string import remove_accents, str_to_ascii, validate_email


# we use a special UUID that's never generated as a valid uuid4 to indicate that the
# user did not change the file in a file upload field but wants to keep the existing
# one instead
KEEP_EXISTING_FILE_UUID = '00000000-0000-0000-0000-000000000001'


class TextFieldDataSchema(mm.Schema):
    min_length = fields.Integer(load_default=0, validate=validate.And(validate.Range(0), validate.NoneOf((1,))))
    max_length = fields.Integer(load_default=0, validate=validate.Range(0))

    @validates_schema(skip_on_field_errors=True)
    def validate_min_max(self, data, **kwargs):
        if data['min_length'] and data['max_length'] and data['min_length'] > data['max_length']:
            raise ValidationError('Maximum value must be less than minimum value.', 'max_length')


class TextFieldLengthValidator(validate.Length):
    def __call__(self, value):
        if not value:
            return value
        return super().__call__(value)


class TextField(RegistrationFormFieldBase):
    name = 'text'
    mm_field_class = fields.String
    setup_schema_base_cls = TextFieldDataSchema

    def get_validators(self, existing_registration):
        return TextFieldLengthValidator(min=self.form_item.data.get('min_length') or None,
                                        max=self.form_item.data.get('max_length') or None)


class NumberFieldDataSchema(BillableFieldDataSchema):
    min_value = fields.Integer(load_default=0, validate=validate.Range(0))
    max_value = fields.Integer(load_default=0, validate=validate.Range(0))

    @validates_schema(skip_on_field_errors=True)
    def validate_min_max(self, data, **kwargs):
        if data['min_value'] and data['max_value'] and data['min_value'] > data['max_value']:
            raise ValidationError('Maximum value must be less than minimum value.', 'max_value')


class NumberField(RegistrationFormBillableField):
    name = 'number'
    mm_field_class = fields.Integer
    setup_schema_base_cls = NumberFieldDataSchema
    not_empty_if_required = False

    @property
    def mm_field_kwargs(self):
        return {'allow_none': not self.form_item.is_required}

    def get_validators(self, existing_registration):
        return validate.Range(min=self.form_item.data.get('min_value') or 0,
                              max=self.form_item.data.get('max_value') or None)

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0) * int(reg_data or 0)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if registration_data.data is None:
            return ''
        return str(registration_data.data) if for_humans else registration_data.data

    @property
    def default_value(self):
        return None


class TextAreaField(RegistrationFormFieldBase):
    name = 'textarea'
    mm_field_class = fields.String
    setup_schema_fields = {
        'number_of_rows': fields.Integer(load_default=None, validate=validate.Range(1, 20)),
    }


class CheckboxField(RegistrationFormBillableField):
    name = 'checkbox'
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
                if old_data and not self.has_data_changed(new_data, old_data):
                    return
            if new_data and self.form_item.data.get('places_limit'):
                places_left = self.form_item.data.get('places_limit') - self.get_places_used()
                if not places_left:
                    raise ValidationError(_('There are no places left for this option.'))
        return _check_number_of_places

    @property
    def default_value(self):
        return False


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
    mm_field_class = fields.String
    setup_schema_base_cls = DateFieldDataSchema

    def validators(self, **kwargs):
        def _validate_date(date_string):
            try:
                datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                raise ValidationError(_('Invalid date'))
            return True
        return _validate_date

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


class BooleanFieldSetupSchema(LimitedPlacesBillableFieldDataSchema):
    default_value = fields.String(load_default='', validate=validate.OneOf(['', 'yes', 'no']))

    @pre_load
    def _convert_to_yes_no(self, data, **kwargs):
        """
        For historical reasons, the boolean default value is
        saved as 'yes'/'no'/'' instead of True/False/None where the latter
        is used for the actual value of the field.
        """
        data['default_value'] = {True: 'yes', False: 'no'}.get(data.get('default_value'), '')
        return data


class BooleanField(RegistrationFormBillableField):
    name = 'bool'
    mm_field_class = fields.Boolean
    setup_schema_base_cls = BooleanFieldSetupSchema
    not_empty_if_required = False
    friendly_data_mapping = {None: '',
                             True: L_('Yes'),
                             False: L_('No')}

    @property
    def mm_field_kwargs(self):
        return {'allow_none': not self.form_item.is_required}

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
                if old_data and not self.has_data_changed(new_data, old_data):
                    return
            if new_data and self.form_item.data.get('places_limit'):
                places_left = self.form_item.data.get('places_limit') - self.get_places_used()
                if new_data and not places_left:
                    raise ValidationError(_('There are no places left for this option.'))
        return _check_number_of_places

    @property
    def default_value(self):
        data = self.form_item.data
        return {'yes': True, 'no': False}.get(data.get('default_value'))

    @property
    def empty_value(self):
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
    mm_field_class = fields.String


class CountryField(RegistrationFormFieldBase):
    name = 'country'
    mm_field_class = fields.String
    setup_schema_fields = {
        'use_affiliation_country': fields.Bool(),
    }

    @classmethod
    def unprocess_field_data(cls, versioned_data, unversioned_data):
        choices = sorted(({'caption': v, 'countryKey': k} for k, v in get_countries().items()),
                         key=lambda x: str_to_ascii(remove_accents(x['caption'])))
        return {'choices': choices}

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        if registration_data.data == 'None':
            # XXX: Not sure where this garbage data is coming from, but it resulted in
            # this method returning `None` and thus breaking the participant list..
            return ''
        return get_country(registration_data.data) if registration_data.data else ''


class FileField(RegistrationFormFieldBase):
    name = 'file'
    mm_field_class = UUIDString
    is_file_field = True

    @property
    def mm_field_kwargs(self):
        return {'allow_none': not self.form_item.is_required}

    def has_data_changed(self, value, old_data):
        if value == KEEP_EXISTING_FILE_UUID:
            return False
        return value != old_data.user_data

    def process_form_data(self, registration, value, old_data=None, billable_items_locked=False):
        # `value` is the UUID of the file (either a real one pointing to a newly uploaded File or
        # the special one in KEEP_VALUE_UUID) or None (no file specified / remove existing)
        data = super().process_form_data(registration, value, old_data, billable_items_locked)
        if not data:
            # we get an empty dict if `has_data_changed` returned False; in that case we do not
            # want to touch the file to avoid duplicating it on the server
            return data

        # if we're here we either got None or a real uuid
        file = File.query.filter(File.uuid == value, ~File.claimed).first() if value else None
        if value and not file:
            raise ValidationError(_('Invalid file UUID'))

        # we don't want to keep the uuid - while convenient, no registration created before v3.2 has
        # this data, and we don't want to break editing those registrations even if it's very unlikely
        # that someone needs to edit a registration that was created with an earlier version and has
        # a file field...
        data['data'] = None
        # pass a reference to the file; the RegistrationData model has a property setter for `file`
        # which will take care of copying the file into storage. once again, it would be cleaner if
        # we just used the new `File` model and referenced it, but changing that for all the existing
        # registrations would be a big mess...
        data['file'] = file
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
    mm_field_class = LowercaseString

    def get_validators(self, existing_registration):
        def _indico_email(value):
            if value and not validate_email(value):
                raise ValidationError(_('Invalid email address'))

        return _indico_email


class PictureField(FileField):
    name = 'picture'
    setup_schema_fields = {
        'min_picture_size': fields.Integer(load_default=None, validate=validate.Range(25, 1000)),
    }

    def get_validators(self, existing_registration):
        def _picture_size_and_type(value):
            if not value:
                return
            file = File.query.filter(File.uuid == value, ~File.claimed).first()
            if not file:
                raise ValidationError('Invalid file')
            if not file.meta.get('registration_picture_checked'):
                raise ValidationError('Picture has not been properly validated.')
            try:
                with file.open() as f:
                    pic = Image.open(f)
            except OSError:
                raise ValidationError(_('Invalid picture file.'))
            if pic.format.lower() != 'jpeg':
                raise ValidationError('This field only accepts jpeg pictures.')
            min_picture_size = self._get_min_size()
            if min_picture_size and min(pic.size) < min_picture_size:
                raise ValidationError(_('The uploaded picture pixels is smaller than the minimum size of {}.')
                                      .format(min_picture_size))
        return _picture_size_and_type

    @make_interceptable
    def _get_min_size(self):
        return self.form_item.data.get('min_picture_size')
