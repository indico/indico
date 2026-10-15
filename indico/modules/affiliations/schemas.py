# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.modules.users.schemas import AffiliationSchema
from indico.util.marshmallow import not_empty


class AffiliationArgs(AffiliationSchema):
    class Meta(AffiliationSchema.Meta):
        fields = ('name', 'alt_names', 'street', 'postcode', 'city', 'country_code', 'meta')

    name = fields.String(required=True, validate=[not_empty])
    alt_names = fields.List(fields.String(validate=not_empty))
    meta = fields.Dict(keys=fields.Str())
