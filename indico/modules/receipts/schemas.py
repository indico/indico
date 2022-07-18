# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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
