# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from marshmallow.fields import Raw, String
from marshmallow_sqlalchemy import column2field

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionFieldValue
from indico.modules.events.contributions.models.types import ContributionType


class ContributionSchema(mm.ModelSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'friendly_id', 'code')


class ContributionTypeSchema(mm.ModelSchema):
    class Meta:
        model = ContributionType
        fields = ('id', 'name', 'description')


class ContributionFieldValueSchema(mm.Schema):
    id = column2field(ContributionFieldValue.contribution_field_id, attribute='contribution_field_id')
    name = String(attribute='contribution_field.title')
    value = Raw(attribute='friendly_data')

    class Meta:
        model = ContributionFieldValue
        fields = ('id', 'name', 'value')


contribution_type_schema = ContributionTypeSchema()
contribution_type_schema_basic = ContributionTypeSchema(only=('id', 'name'))
