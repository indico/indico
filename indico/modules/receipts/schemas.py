# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import yaml
from marshmallow import ValidationError, fields, post_load, pre_load, validate, validates_schema
from marshmallow_oneofschema import OneOfSchema

from indico.core.marshmallow import mm
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.util.marshmallow import YAML, not_empty
from indico.util.string import slugify


class OwnerDataSchema(mm.Schema):
    title = fields.String()
    id = fields.Integer()
    locator = fields.Dict()


class _CheckboxAttributesSchema(mm.Schema):
    value = fields.Bool()
    label = fields.String(required=True)


class _DropdownAttributesSchema(mm.Schema):
    label = fields.String(required=True)
    options = fields.List(fields.String())
    default = fields.Int(validate=validate.Range(0))

    @validates_schema(skip_on_field_errors=True)
    def _validate_default(self, data, **kwargs):
        if 'default' in data and data['default'] >= len(data['options']):
            raise ValidationError('The provided value is out of range')


class _InputAttributesSchema(mm.Schema):
    value = fields.String()
    label = fields.String(required=True)


class CustomFieldAttributesSchema(OneOfSchema):
    type_schemas = {
        'checkbox': _CheckboxAttributesSchema,
        'dropdown': _DropdownAttributesSchema,
        'input': _InputAttributesSchema
    }


class CustomFieldSchema(mm.Schema):
    name = fields.String(required=True, validate=not_empty)
    type = fields.String(required=True)
    attributes = fields.Nested(CustomFieldAttributesSchema, required=True)

    @pre_load
    def _add_attributes_type(self, data, **kwargs):
        data = data.copy()
        data['attributes']['type'] = data['type']
        return data


class ReceiptTplMetadataSchema(mm.Schema):
    custom_fields = fields.Nested(CustomFieldSchema(many=True))


class ReceiptTemplateTypeSchema(mm.Schema):
    title = fields.String()
    name = fields.String()
    file_prefix = fields.String()


class ReceiptTemplateDBSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ReceiptTemplate
        fields = ('id', 'title', 'html', 'css', 'custom_fields', 'default_filename', 'yaml', 'owner')

    yaml = fields.Function(lambda tpl: (yaml.safe_dump({'custom_fields': tpl.custom_fields})
                                        if tpl.custom_fields else None))
    owner = fields.Nested(OwnerDataSchema)


class ReceiptTemplateAPISchema(mm.Schema):
    title = fields.String(required=True, validate=validate.Length(3))
    default_filename = fields.String(load_default='')
    html = fields.String(required=True, validate=validate.Length(3))
    css = fields.String(load_default='')
    yaml = YAML(ReceiptTplMetadataSchema, load_default=None, allow_none=True)

    @post_load
    def ensure_filename_is_slug(self, data, **kwargs):
        data['default_filename'] = slugify(data['default_filename'])
        return data


class PersonalDataFieldSchema(mm.Schema):
    title = fields.String()
    first_name = fields.String()
    last_name = fields.String()
    email = fields.Email()
    affiliation = fields.String()
    position = fields.String()
    address = fields.String()
    country = fields.String()
    phone = fields.String()
    price = fields.Number()


class FormFieldsSchema(mm.Schema):
    title = fields.String()
    value = fields.Boolean()
    field_data = fields.Dict()
    actual_price = fields.Number()


class TemplateDataSchema(mm.Schema):
    custom_fields = fields.Dict(keys=fields.String, values=fields.String)
    personal_data = fields.Nested(PersonalDataFieldSchema)
    _fields = fields.List(fields.Nested(FormFieldsSchema), attribute='fields', data_key='fields')
    base_price = fields.Number()
    total_price = fields.Number()
    currency = fields.String()
    formatted_price = fields.String()
