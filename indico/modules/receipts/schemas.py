# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import yaml
from marshmallow import fields, validate

from indico.core.marshmallow import mm
from indico.modules.receipts.models.templates import ReceiptTemplate
from indico.util.marshmallow import YAML, not_empty


class OwnerDataSchema(mm.Schema):
    title = fields.String()
    id = fields.Integer()
    locator = fields.Dict()


class CustomFieldSchema(mm.Schema):
    name = fields.String(required=True, validate=not_empty)
    type = fields.String(required=True, validate=validate.OneOf(['str', 'bool', 'choice']))
    options = fields.List(fields.String())

    class Meta:
        additional = ('default',)


class ReceiptTplMetadataSchema(mm.Schema):
    custom_fields = fields.Nested(CustomFieldSchema(many=True))


class ReceiptTemplateDBSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ReceiptTemplate
        fields = ('id', 'title', 'html', 'css', 'custom_fields', 'yaml', 'owner')

    yaml = fields.Function(lambda tpl: (yaml.safe_dump({'custom_fields': tpl.custom_fields})
                                        if tpl.custom_fields else None))
    owner = fields.Nested(OwnerDataSchema)


class ReceiptTemplateAPISchema(mm.Schema):
    title = fields.String(required=True, validate=validate.Length(3))
    html = fields.String(required=True, validate=validate.Length(3))
    css = fields.String(load_default='')
    yaml = YAML(ReceiptTplMetadataSchema, load_default=None, allow_none=True)


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
    _fields = fields.List(fields.Nested(FormFieldsSchema), data_key='fields')
    base_price = fields.Number()
    total_price = fields.Number()
    currency = fields.String()
    formatted_price = fields.String()
