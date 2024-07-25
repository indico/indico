# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib
from operator import attrgetter

from marshmallow import fields, post_dump
from marshmallow_enum import EnumField
from marshmallow_sqlalchemy import column2field

from indico.core.marshmallow import mm
from indico.modules.events.abstracts.util import filter_field_values
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import (ContributionField, ContributionFieldValue,
                                                               ContributionFieldVisibility)
from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.sessions.schemas import BasicSessionSchema, SessionBlockSchema
from indico.modules.events.tracks.schemas import TrackSchema
from indico.modules.users.schemas import AffiliationSchema
from indico.util.marshmallow import SortedList


class BasicContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'friendly_id', 'code')


class ContributionTypeSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ContributionType
        fields = ('id', 'name', 'description')


class ContributionFieldSchema(mm.Schema):
    visibility = EnumField(ContributionFieldVisibility)

    class Meta:
        model = ContributionField
        fields = ('id', 'position', 'title', 'description', 'is_required', 'is_active', 'is_user_editable',
                  'visibility', 'field_type', 'field_data')


class ContributionFieldValueSchema(mm.Schema):
    id = column2field(ContributionFieldValue.contribution_field_id, attribute='contribution_field_id')
    name = fields.String(attribute='contribution_field.title')
    value = fields.Raw(attribute='friendly_data')

    class Meta:
        model = ContributionFieldValue
        fields = ('id', 'name', 'value')


class ContributionPersonLinkSchema(mm.SQLAlchemyAutoSchema):
    affiliation_link = fields.Nested(AffiliationSchema)
    email_hash = fields.Function(lambda x: hashlib.md5(x.email.encode()).hexdigest() if x.email else None)

    class Meta:
        model = ContributionPersonLink
        fields = ('id', 'person_id', 'email', 'email_hash', 'first_name', 'last_name', 'full_name', 'title',
                  'affiliation', 'affiliation_link', 'address', 'phone', 'is_speaker', 'author_type')

    @post_dump
    def _hide_sensitive_data(self, data, **kwargs):
        if self.context.get('hide_restricted_data'):
            del data['email']
            del data['address']
            del data['phone']
        return data


class FullContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'friendly_id', 'code', 'abstract_id', 'board_number', 'keywords',
                  'venue_name', 'room_name', 'address', 'inherit_location',
                  'start_dt', 'end_dt', 'duration',
                  'session', 'session_block', 'track', 'type', 'custom_fields', 'persons')

    session = fields.Nested(BasicSessionSchema, only=('id', 'title', 'friendly_id', 'code'))
    session_block = fields.Nested(SessionBlockSchema, only=('id', 'title', 'code'))
    track = fields.Nested(TrackSchema, only=('id', 'title', 'code'))
    type = fields.Nested(ContributionTypeSchema, only=('id', 'name'))
    custom_fields = fields.List(fields.Nested(ContributionFieldValueSchema), attribute='field_values')
    persons = SortedList(fields.Nested(ContributionPersonLinkSchema), attribute='person_links',
                         sort_key=attrgetter('display_order_key'))

    @post_dump(pass_original=True)
    def _hide_restricted_fields(self, data, orig, **kwargs):
        if self.context.get('hide_restricted_data'):
            can_manage = self.context['user_can_manage']
            owns_abstract = self.context['user_owns_abstract']
            allowed_field_values = {fv.contribution_field_id
                                    for fv in filter_field_values(orig.field_values, can_manage, owns_abstract)}
            data['custom_fields'] = [x for x in data['custom_fields'] if x['id'] in allowed_field_values]
        return data


contribution_type_schema = ContributionTypeSchema()
contribution_type_schema_basic = ContributionTypeSchema(only=('id', 'name'))
