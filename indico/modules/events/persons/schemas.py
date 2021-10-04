# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.models.persons import EventPerson
from indico.modules.users.models.users import UserTitle
from indico.util.i18n import orig_string


class PublicEventPersonSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventPerson
        fields = ('id', 'identifier', 'title', 'email', 'affiliation', 'full_name',
                  'first_name', 'last_name', 'user_identifier')

    title = fields.Method('get_title', deserialize='load_title')
    full_name = fields.Function(lambda ep: f'{ep.first_name} {ep.last_name}'.strip() or 'Unknown')
    user_identifier = fields.String(attribute='user.identifier')
    last_name = fields.String(required=True)
    email = fields.String(missing='')  # TODO: email

    def get_title(self, obj):
        return obj.title

    def load_title(self, title):
        return next((x.value for x in UserTitle if title == orig_string(x.title)), UserTitle.none)


class EventPersonSchema(PublicEventPersonSchema):
    class Meta:
        model = EventPerson
        fields = PublicEventPersonSchema.Meta.fields + ('phone', 'address')
