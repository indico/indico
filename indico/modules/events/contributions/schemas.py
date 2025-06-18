# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib
from operator import attrgetter

from marshmallow import EXCLUDE, ValidationError, fields, post_dump, post_load, validates
from marshmallow_sqlalchemy import column2field

from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.marshmallow import mm
from indico.modules.events.abstracts.util import filter_field_values
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import (ContributionField, ContributionFieldValue,
                                                               ContributionFieldVisibility)
from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.contributions.models.references import ContributionReference
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.person_link_schemas import ContributionPersonLinkSchema as _ContributionPersonLinkSchema
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.schemas import BasicSessionBlockSchema, BasicSessionSchema, LocationDataSchema
from indico.modules.events.tracks.schemas import TrackSchema
from indico.modules.users.schemas import AffiliationSchema
from indico.util.marshmallow import EventTimezoneDateTimeField, SortedList


class BasicContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'friendly_id', 'code')


class ContributionTypeSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ContributionType
        fields = ('id', 'name', 'description')


class ContributionFieldSchema(mm.Schema):
    visibility = fields.Enum(ContributionFieldVisibility)

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


def _get_principal_roles(principal):
    roles = [principal.author_type.name]
    if principal.is_speaker:
        roles.append('speaker')
    if principal.contribution and principal.is_submitter:
        roles.append('submitter')
    return roles


class ContributionPersonLinkSchema(mm.SQLAlchemyAutoSchema):
    affiliation_link = fields.Nested(AffiliationSchema)
    email_hash = fields.Function(lambda x: hashlib.md5(x.email.encode()).hexdigest() if x.email else None)
    roles = fields.Function(_get_principal_roles, load_only=True)

    class Meta:
        model = ContributionPersonLink
        fields = ('id', 'person_id', 'email', 'email_hash', 'first_name', 'last_name', 'full_name', 'title',
                  'affiliation', 'affiliation_link', 'address', 'phone', 'is_speaker', 'author_type', 'roles')

    @post_dump
    def _hide_sensitive_data(self, data, **kwargs):
        if self.context.get('hide_restricted_data'):
            del data['email']
            del data['address']
            del data['phone']
        return data


class ContributionReferenceSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ContributionReference
        fields = ('id', 'type', 'value')

    type = fields.Integer(attribute='reference_type_id')


class FullContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'friendly_id', 'code', 'abstract_id', 'board_number', 'keywords',
                  'venue_name', 'room_name', 'address', 'inherit_location',
                  'start_dt', 'end_dt', 'duration',
                  'session', 'session_block', 'track', 'type', 'custom_fields', 'persons')

    session = fields.Nested(BasicSessionSchema, only=('id', 'title', 'friendly_id', 'code'))
    session_block = fields.Nested(BasicSessionBlockSchema, only=('id', 'title', 'code'))
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


class ContribFieldSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ContributionField
        fields = ('title', 'description', 'is_required', 'field_data')


class ContribFieldValueSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ContributionFieldValue
        fields = ('id', 'data')

    id = fields.Integer(attribute='contribution_field_id', required=True)
    data = fields.Raw(load_default=None)

    @validates('id')
    def _check_contribution_field(self, id, **kwargs):
        if not ContributionField.get(id):
            raise ValidationError('Invalid contribution field')

    @post_load()
    @no_autoflush
    def make_instance(self, data, **kwargs):
        return ContributionFieldValue(contribution_field_id=data['contribution_field_id'], data=data['data'])


class TimezoneAwareSessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('start_dt', 'end_dt')

    start_dt = EventTimezoneDateTimeField()
    end_dt = EventTimezoneDateTimeField()


# TODO: (Ajob) Evaluate this schema vs timetable one
class ContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'code', 'board_number', 'keywords', 'location_data',
                  'start_dt', 'duration', 'event_id', 'references', 'custom_fields', 'person_links', 'session_block',
                  'timetable_entry')

    start_dt = EventTimezoneDateTimeField()
    # TODO: filter inactive and resitricted contrib fields
    custom_fields = fields.List(fields.Nested(ContribFieldValueSchema), attribute='field_values')
    person_links = fields.Nested(_ContributionPersonLinkSchema(many=True, partial=False), partial=False, unknown=EXCLUDE)
    references = fields.List(fields.Nested(ContributionReferenceSchema))
    location_data = fields.Nested(LocationDataSchema)
    session_block = fields.Nested(TimezoneAwareSessionBlockSchema)
    duration = fields.TimeDelta(required=True)
