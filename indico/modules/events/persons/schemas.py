# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, fields, post_dump

from indico.core.marshmallow import mm
from indico.modules.events.models.persons import EventPerson
from indico.modules.users.models.users import UserTitle
from indico.util.i18n import orig_string


class PersonLinkSchema(mm.Schema):
    class Meta:
        unknown = EXCLUDE

    _type = fields.Constant('PersonLink')
    person_id = fields.Int()
    user_id = fields.Function(lambda o: o.person.user_id)
    first_name = fields.String(missing='')
    last_name = fields.String(required=True)
    title = fields.Method('get_title', deserialize='load_title')
    affiliation = fields.String(missing='')
    phone = fields.String(missing='')
    address = fields.String(missing='')
    email = fields.String(required=True)
    display_order = fields.Int()
    avatar_url = fields.Function(lambda o: o.person.user.avatar_url if o.person.user else None)

    def get_title(self, obj):
        return obj.title

    def load_title(self, title):
        return next((x.value for x in UserTitle if title == orig_string(x.title)), UserTitle.none)

    @post_dump
    def dump_type(self, data, **kwargs):
        if not data['person_id']:
            del data['_type']
        return data


class EventPersonSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventPerson
        public_fields = ('id', 'identifier', 'title', 'email', 'affiliation', 'name',
                         'first_name', 'last_name', 'user_identifier')
        fields = public_fields + ('phone', 'address')

    title = fields.Method('get_title', deserialize='load_title')
    name = fields.String(attribute='full_name')  # TODO: Unknown name fallback
    user_identifier = fields.String(attribute='user.identifier')
    last_name = fields.String(required=True)
    email = fields.String(missing='')

    def get_title(self, obj):
        return obj.title

    def load_title(self, title):
        return next((x.value for x in UserTitle if title == orig_string(x.title)), UserTitle.none)
