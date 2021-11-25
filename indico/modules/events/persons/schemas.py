# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, fields, post_dump, pre_load
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.models.persons import EventPerson
from indico.modules.users.models.users import UserTitle


class PersonLinkSchema(mm.Schema):
    class Meta:
        unknown = EXCLUDE

    type = fields.Constant('PersonLink')
    person_id = fields.Int()
    user_id = fields.Int(attribute='person.user_id')
    user_identifier = fields.String(attribute='person.user.identifier')
    first_name = fields.String(load_default='')
    last_name = fields.String(required=True)
    _title = EnumField(UserTitle, data_key='title')
    affiliation = fields.String(load_default='')
    phone = fields.String(load_default='')
    address = fields.String(load_default='')
    email = fields.String(required=True)
    display_order = fields.Int(load_default=0)
    avatar_url = fields.Function(lambda o: o.person.user.avatar_url if o.person.user else None)

    @pre_load
    def load_title(self, data, **kwargs):
        if not data.get('title'):
            data['title'] = UserTitle.none.name
        return data

    @post_dump
    def dump_type(self, data, **kwargs):
        if not data['person_id']:
            del data['type']
        return data


class EventPersonSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventPerson
        public_fields = ('id', 'identifier', '_title', 'email', 'affiliation', 'name',
                         'first_name', 'last_name', 'user_identifier')
        fields = public_fields + ('phone', 'address')

    type = fields.Constant('EventPerson')
    _title = EnumField(UserTitle, data_key='title')
    name = fields.String(attribute='full_name')
    user_identifier = fields.String(attribute='user.identifier')
    last_name = fields.String(required=True)
    email = fields.String(load_default='')

    @pre_load
    def load_title(self, data, **kwargs):
        if not data.get('title'):
            data['title'] = UserTitle.none.name
        return data
