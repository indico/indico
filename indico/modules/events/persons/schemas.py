# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import ValidationError, fields, post_dump, post_load, pre_load, validates_schema

from indico.core.marshmallow import mm
from indico.modules.events.models.persons import EventPerson
from indico.modules.users import user_management_settings
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.users import UserTitle
from indico.modules.users.schemas import AffiliationSchema
from indico.util.marshmallow import ModelField, NoneValueEnumField


class PersonLinkSchema(mm.Schema):
    type = fields.String(dump_default='person_link')
    person_id = fields.Int()
    user_id = fields.Int(attribute='person.user_id', dump_only=True)
    user_identifier = fields.String(attribute='person.user.identifier', dump_only=True)
    name = fields.String(attribute='display_full_name', dump_only=True)
    first_name = fields.String(load_default='')
    last_name = fields.String(required=True)
    _title = fields.Enum(UserTitle, data_key='title')
    affiliation = fields.String(load_default='')
    affiliation_link = ModelField(Affiliation, data_key='affiliation_id', load_default=None, load_only=True)
    affiliation_id = fields.Integer(load_default=None, dump_only=True)
    affiliation_meta = fields.Nested(AffiliationSchema, attribute='affiliation_link', dump_only=True)
    phone = fields.String(load_default='')
    address = fields.String(load_default='')
    email = fields.String(load_default='')
    display_order = fields.Int(load_default=0, dump_default=0)
    avatar_url = fields.Function(lambda o: o.person.user.avatar_url if o.person.user else None, dump_only=True)
    roles = fields.List(fields.String(), load_only=True)

    @pre_load
    def load_nones(self, data, **kwargs):
        if not data.get('title'):
            data['title'] = UserTitle.none.name
        if not data.get('affiliation'):
            data['affiliation'] = ''
        if data.get('affiliation_id') == -1:
            # external search results with a predefined affiliation
            del data['affiliation_id']
        return data

    @post_load
    def ensure_affiliation_text(self, data, **kwargs):
        if data['affiliation_link']:
            data['affiliation'] = data['affiliation_link'].name
        return data

    @post_dump
    def dump_type(self, data, **kwargs):
        if data['person_id'] is None:
            del data['type']
            del data['person_id']
        if data['title'] == UserTitle.none.name:
            data['title'] = None
        return data

    @validates_schema(skip_on_field_errors=True)
    def check_restricted_affiliation(self, data, **kwargs):
        if self.context.get('affiliations_disabled'):
            # XXX This is a horrible hack to fix the jacow plugin which implements multiple affiliations.
            # Ideally, we would completely ignore affiliation data in this schema when a plugin disables
            # affiliations, and then let the plugin's server-side code deal with assigning everything it
            # wants stored in the core (such as a semicolon-separated list of the affiliations in the
            # normal affiliation string).
            # Anyway, for now we accept the fact that the affiliation string is not really "protected"
            # by the check here when such a plugin is used.
            return
        restricted = user_management_settings.get('only_predefined_affiliations')
        if restricted and data['affiliation'] and not data['affiliation_link']:
            raise ValidationError('Custom affiliations are not allowed')


class EventPersonSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventPerson
        public_fields = ('id', 'identifier', 'title', 'email', 'affiliation', 'affiliation_link', 'affiliation_id',
                         'affiliation_meta', 'name', 'first_name', 'last_name', 'user_identifier')
        fields = (*public_fields, 'phone', 'address')

    type = fields.Constant('EventPerson')
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    name = fields.String(attribute='full_name')
    user_identifier = fields.String(attribute='user.identifier')
    last_name = fields.String(required=True)
    email = fields.String(load_default='')
    affiliation_link = ModelField(Affiliation, data_key='affiliation_id', load_default=None, load_only=True)
    affiliation_id = fields.Integer(load_default=None, dump_only=True)
    affiliation_meta = fields.Nested(AffiliationSchema, attribute='affiliation_link', dump_only=True)

    @pre_load
    def handle_affiliation_link(self, data, **kwargs):
        # in some cases we get data that's already been loaded by PersonLinkSchema and thus no longer
        # has an affiliation_id but only an affiliation_link...
        data = data.copy()
        if affiliation_link := data.pop('affiliation_link', None):
            data['affiliation_id'] = affiliation_link.id
        return data

    @post_load
    def ensure_affiliation_text(self, data, **kwargs):
        if affiliation_link := data.get('affiliation_link'):
            data['affiliation'] = affiliation_link.name
        return data


class EventPersonUpdateSchema(EventPersonSchema):
    class Meta(EventPersonSchema.Meta):
        fields = ('title', 'first_name', 'last_name', 'address', 'phone', 'affiliation', 'affiliation_link')

    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none)

    @validates_schema(skip_on_field_errors=True)
    def check_restricted_affiliation(self, data, **kwargs):
        restricted = user_management_settings.get('only_predefined_affiliations')
        if restricted and data.get('affiliation') and not data.get('affiliation_link'):
            raise ValidationError('Custom affiliations are not allowed', field_name='affiliation_data')
