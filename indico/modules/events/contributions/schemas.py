# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib
from operator import attrgetter

from marshmallow import EXCLUDE, ValidationError, fields, post_dump, post_load, validates
from marshmallow_sqlalchemy import column2field

from indico.core.marshmallow import mm
from indico.modules.events.abstracts.util import filter_field_values
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import (ContributionField, ContributionFieldValue,
                                                               ContributionFieldVisibility)
from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.contributions.models.references import ContributionReference
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.management.settings import global_event_settings
from indico.modules.events.models.events import Event
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.person_link_schemas import ContributionPersonLinkSchema as _ContributionPersonLinkSchema
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.schemas import BasicSessionBlockSchema, BasicSessionSchema
from indico.modules.events.tracks.schemas import TrackSchema
from indico.modules.users.schemas import AffiliationSchema
from indico.util.i18n import _
from indico.util.locations import LocationDataSchema
from indico.util.marshmallow import EventTimezoneDateTimeField, ModelField, NonPartialNested, SortedList, not_empty
from indico.util.user import make_user_search_token
from indico.web.flask.util import url_for


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
    roles = []
    if principal.author_type:
        roles.append(principal.author_type.name)
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


class UserContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'friendly_id', 'code',
                  'start_dt', 'end_dt', 'url', 'edit_url', 'edit_search_token')

    def _get_edit_url(self, contribution):
        user = self.context['user']
        if not contribution.can_edit(user):
            return None
        return url_for('contributions.manage_update_contrib', contribution, standalone=True)

    def _get_edit_search_token(self, contribution):
        user = self.context['user']
        if not contribution.can_edit(user):
            return None
        return make_user_search_token()

    edit_url = fields.Method('_get_edit_url')
    edit_search_token = fields.Method('_get_edit_search_token')


class ContributionReferenceSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ContributionReference
        fields = ('reference_type', 'value')

    reference_type = ModelField(ReferenceType, data_key='type', required=True)
    value = fields.String(required=True, validate=not_empty)


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


class TimezoneAwareSessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('start_dt', 'end_dt')

    start_dt = EventTimezoneDateTimeField()
    end_dt = EventTimezoneDateTimeField()


class CustomFieldsMixin:
    custom_fields = fields.Method('_dump_custom_fields', '_load_custom_fields')

    def _make_custom_fields_schema(self):
        schema = {}
        if not (ctx := self.context['custom_fields_context']):
            raise RuntimeError('ContributionRESTSchema missing custom fields context')
        management = ctx['management']
        allowed_fields = ctx['allowed_fields'] if not management else None
        for field in self.context['event'].contribution_fields:
            if not field.is_active:
                continue
            if allowed_fields is not None and field not in allowed_fields:
                continue
            impl = field.mgmt_field if management else field.field
            schema[f'custom_{field.id}'] = impl.create_mm_field()
        return mm.Schema.from_dict(schema, name='CustomFieldsSchema')

    def _load_custom_fields(self, value):
        schema_cls = self._make_custom_fields_schema()
        schema = schema_cls(partial=bool(self.partial))
        return schema.load(value)

    def _dump_custom_fields(self, contrib):
        schema_cls = self._make_custom_fields_schema()
        schema = schema_cls()
        return schema.dump({f'custom_{k}': v.data for k, v in contrib.data_by_field.items()})

    @staticmethod
    def get_custom_fields_context(event: Event, management: bool = False):
        """Get the necessary context for building the custom fields schema.

        Outside management (submitters editing their contribution) this includes a list
        of fields that are visible (and editable).
        For managers no filtering is needed, so no field list is generated at all.
        """
        if management:
            return {'management': True}
        fields = {
            f
            for f in event.contribution_fields
            # we hide both non-user-editable and manager-only fields outside management, which is stronger than
            # the check in the old form (which only removed non-user-editable), because while it makes no sense
            # to have user-editable manager-only fields, there was no server-side validation for it and when editing
            # a manager-only field the user-editable toggle did not get disabled
            if f.visibility != ContributionFieldVisibility.managers_only and f.is_user_editable
        }
        return {
            'management': False,
            'allowed_fields': fields,
        }


class ContributionRESTSchema(CustomFieldsMixin, mm.SQLAlchemyAutoSchema):
    """Schema for RESTful operations on contributions."""

    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'code', 'board_number', 'keywords', 'location_data',
                  'start_dt', 'duration', 'references', 'custom_fields', 'person_links', 'type')
        rh_context = ('event', 'custom_fields_context', {'object': 'contrib'})

    id = fields.Int(dump_only=True)
    start_dt = EventTimezoneDateTimeField()
    person_links = fields.List(NonPartialNested(_ContributionPersonLinkSchema, unknown=EXCLUDE))
    references = fields.List(NonPartialNested(ContributionReferenceSchema))
    location_data = NonPartialNested(LocationDataSchema)
    session_block = NonPartialNested(TimezoneAwareSessionBlockSchema)
    duration = fields.TimeDelta(required=True)
    _description = fields.String(attribute='description')
    type = ModelField(ContributionType, with_parent='event', data_key='type_id', allow_none=True)

    @validates('keywords')
    def _validate_keywords(self, value):
        if not (allowed_keywords := set(global_event_settings.get('allowed_contribution_keywords'))):
            return
        contrib = self.context.get('object')
        existing_keywords = set(contrib.keywords) if contrib else set()
        keywords = set(value)
        if not (keywords <= (allowed_keywords | existing_keywords)):
            raise ValidationError(_('Invalid keyword found'))

    @post_load
    def _sort_keywords(self, data, **kwargs):
        if 'keywords' in data:
            data['keywords'] = sorted(set(data['keywords']))
        return data

    @staticmethod
    def get_editable_fields(contrib: Contribution, management: bool = False):
        """Get the list of contrib fields a user can edit.

        This is ``None`` if there is no restriction (usually a manager).
        The return value of this is meant to be passed to the ``only`` kwarg of
        this schema.
        """
        if management:
            # all fields
            return None
        if not contribution_settings.get(contrib.event, 'submitters_can_edit'):
            # no edit permission, shouldn't even get this far, but just in case
            return ()
        custom = ()
        if contribution_settings.get(contrib.event, 'submitters_can_edit_custom'):
            # we don't use a Nested schema for it since it's generated on the fly,
            # so we have to grant full access to custom fields here.
            # restrictions on which fields can actually be edited are determined inside
            # the schema via context (see `get_custom_fields_context`)
            custom = ('custom_fields',)
        return ('title', 'description', 'person_links', *custom)
