# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import typing as t
from copy import deepcopy
from operator import attrgetter

from marshmallow import ValidationError, fields, post_load, pre_load, validate, validates_schema
from marshmallow_oneofschema import OneOfSchema
from speaklater import is_lazy_string

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event
from indico.modules.events.payment.models.transactions import PaymentTransaction
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.util.marshmallow import YAML, not_empty
from indico.util.string import slugify


class OwnerDataSchema(mm.Schema):
    title = fields.String()
    id = fields.Int()
    locator = fields.Dict()


class _AttributesSchemaBase(mm.Schema):
    label = fields.String(required=True)
    description = fields.String(load_default='')


class _CheckboxAttributesSchema(_AttributesSchemaBase):
    value = fields.Bool()


class _DropdownAttributesSchema(_AttributesSchemaBase):
    options = fields.List(fields.String())
    default = fields.Int(validate=validate.Range(0), strict=True)

    @validates_schema(skip_on_field_errors=True)
    def _validate_default(self, data, **kwargs):
        if 'default' in data and data['default'] >= len(data['options']):
            raise ValidationError('The provided value is out of range')


class _InputAttributesSchema(_AttributesSchemaBase):
    value = fields.String()


class _TextareaAttributesSchema(_AttributesSchemaBase):
    value = fields.String()


class _ImageAttributesSchema(_AttributesSchemaBase):
    pass


class CustomFieldAttributesSchema(OneOfSchema):
    type_schemas = {
        'checkbox': _CheckboxAttributesSchema,
        'dropdown': _DropdownAttributesSchema,
        'input': _InputAttributesSchema,
        'textarea': _TextareaAttributesSchema,
        'image': _ImageAttributesSchema,
    }


class CustomFieldValidationsSchema(mm.Schema):
    required = fields.Bool()


class CustomFieldSchema(mm.Schema):
    name = fields.String(required=True, validate=not_empty)
    type = fields.String(required=True)
    attributes = fields.Nested(CustomFieldAttributesSchema, required=True)
    validations = fields.Nested(CustomFieldValidationsSchema)

    @pre_load
    def _add_attributes_type(self, data, **kwargs):
        # OneOfSchema requires the type to be in the attributes
        data = deepcopy(data)
        if 'attributes' in data and isinstance(data['attributes'], dict) and 'type' in data:
            data['attributes']['type'] = data['type']
        return data


class ReceiptTplMetadataSchema(mm.Schema):
    custom_fields = fields.List(fields.Nested(CustomFieldSchema), load_default=lambda: [])


class ReceiptTemplateTypeSchema(mm.Schema):
    title = fields.String()
    name = fields.String()
    file_prefix = fields.String()


class ReceiptTemplateDBSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ReceiptTemplate
        fields = ('id', 'title', 'html', 'css', 'custom_fields', 'default_filename', 'yaml', 'owner')

    owner = fields.Nested(OwnerDataSchema)
    custom_fields = fields.List(fields.Dict())


class ReceiptTemplateAPISchema(mm.Schema):
    title = fields.String(required=True, validate=validate.Length(3))
    default_filename = fields.String(load_default='')
    html = fields.String(required=True, validate=validate.Length(3))
    css = fields.String(required=True)
    yaml = YAML(ReceiptTplMetadataSchema, keep_text=True, required=True, allow_none=True)

    @post_load
    def ensure_filename_is_slug(self, data, **kwargs):
        data['default_filename'] = slugify(data['default_filename'])
        return data


class PersonalDataSchema(mm.Schema):
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    email = fields.Email(required=True)
    title = fields.String(load_default='')
    affiliation = fields.String(load_default='')
    position = fields.String(load_default='')
    address = fields.String(load_default='')
    country = fields.String(load_default='')
    phone = fields.String(load_default='')


class EventDataSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', '_category_chain', 'title', 'start_dt', 'end_dt', 'timezone', 'venue_name', 'room_name',
                  'address', '_type', 'category_chain', 'type', '_url', 'url')

    # dump from nested data
    _category_chain = fields.List(fields.String(), attribute='category.chain_titles', data_key='category_chain',
                                  dump_only=True)
    _type = fields.String(attribute='_type.name', data_key='type', dump_only=True)
    _url = fields.String(attribute='short_external_url', data_key='url', dump_only=True)
    # load into flat data
    category_chain = fields.List(fields.String(), load_only=True, load_default=lambda: [])
    type = fields.String(load_only=True, required=True)
    url = fields.String(load_only=True, required=True)


class TransactionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = PaymentTransaction
        fields = ('status', '_status', 'amount', 'currency', 'provider', 'timestamp', 'data')

    amount = fields.Number(required=True)
    _status = fields.String(attribute='status.name', data_key='status', dump_only=True)
    status = fields.String(load_only=True)


class RegistrationDataSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Registration
        fields = ('id', 'friendly_id', 'submitted_dt', 'base_price', 'total_price', 'currency', 'formatted_price',
                  'state', 'field_data', 'personal_data', 'transaction')

    base_price = fields.Number(required=True)
    total_price = fields.Number(required=True)
    currency = fields.String(required=True)
    formatted_price = fields.String(required=True)
    state = fields.String(required=True)
    field_data = fields.Method('_dump_field_data', '_load_field_data', required=True)
    personal_data = fields.Nested(PersonalDataSchema, required=True)
    transaction = fields.Nested(TransactionSchema, required=True, allow_none=True)

    def get_attribute(self, obj: Registration | dict, attr: str, default: t.Any):
        # Unfortunately marshmallow has no nice way to specify that a value is coming from a method
        # on the object, so we have to hack into the attribute lookup logic for this purpose...
        if isinstance(obj, dict):
            # Dummy preview data loaded from YAML - no magic needed
            return super().get_attribute(obj, attr, default)

        if attr == 'personal_data':
            return obj.get_personal_data()
        elif attr == 'total_price':
            return obj.price
        elif attr == 'formatted_price':
            return obj.render_price()
        elif attr == 'state':
            return obj.state.name

        return super().get_attribute(obj, attr, default)

    def _dump_field_data(self, registration: Registration | dict):
        if isinstance(registration, dict):
            # Dummy preview data loaded from YAML
            return registration['field_data']
        regform = registration.registration_form
        data_by_field = registration.data_by_field
        fields = []
        for field in sorted(regform.active_fields, key=attrgetter('parent.position', 'position')):
            try:
                data = data_by_field[field.id]
            except KeyError:
                continue
            friendly_value = data.get_friendly_data(for_humans=True)
            if is_lazy_string(friendly_value):
                friendly_value = str(friendly_value)
            fields.append({
                'title': field.title,
                'section_title': field.parent.title,
                'input_type': field.input_type,
                'raw_value': data.data,
                'friendly_value': friendly_value,
                'config': field.versioned_data | field.data,
                'actual_price': data.price
            })
        return fields

    def _load_field_data(self, value):
        return value


class TemplateDataSchema(mm.Schema):
    custom_fields = fields.Dict(keys=fields.String, required=True)
    event = fields.Nested(EventDataSchema, required=True)
    registration = fields.Nested(RegistrationDataSchema, required=True)
