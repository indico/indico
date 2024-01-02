# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump, post_load, pre_load
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.models.persons import EventPerson
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
    _title = EnumField(UserTitle, data_key='title')
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

    title = EnumField(UserTitle)
