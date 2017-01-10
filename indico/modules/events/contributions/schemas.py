# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from marshmallow.fields import Raw, String
from marshmallow_sqlalchemy import column2field

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.fields import ContributionFieldValue
from indico.modules.events.contributions.models.types import ContributionType


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
