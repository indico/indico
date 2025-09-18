# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import hashlib

from marshmallow import ValidationError, fields, post_dump, post_load

from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.core.marshmallow import mm
from indico.modules.events.person_link_schemas import SessionBlockPersonLinkSchema as _SessionBlockPersonLinkSchema
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.models.types import SessionType
from indico.modules.users.schemas import AffiliationSchema
from indico.util.locations import LocationDataSchema
from indico.util.marshmallow import ModelField
from indico.web.forms.colors import get_colors


class BasicSessionBlockSchema(mm.SQLAlchemyAutoSchema):
    room_name_verbose = fields.Function(lambda obj: obj.get_room_name(full=False, verbose=True))

    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'code', 'start_dt', 'end_dt', 'duration', 'room_name', 'room_name_verbose')


class BasicSessionSchema(mm.SQLAlchemyAutoSchema):
    blocks = fields.List(fields.Nested(BasicSessionBlockSchema))

    class Meta:
        model = Session
        fields = ('id', 'title', 'friendly_id', 'code', 'blocks')


class SessionColorSchema(mm.Schema):
    text = fields.String(required=True)
    background = fields.String(required=True)

    def validate_colors(self, data, **kwargs):
        colors = ColorTuple(**data)
        if colors not in get_colors():
            raise ValidationError('Invalid colors')

    @post_load
    def create_color_tuple(self, data, **kwargs):
        return ColorTuple(**data)

    @post_dump
    def make_valid_hex_color(self, data, **kwargs):
        return {k: f'#{v}' for k, v in data.items()}


class SessionTypeSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionType
        fields = ('id', 'name', 'code', 'is_poster')


class SessionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Session
        fields = ('id', 'title', 'code', 'description', 'default_contribution_duration',
                  'type', 'location_data', 'colors')

    colors = fields.Nested(SessionColorSchema)
    type = ModelField(SessionType, allow_none=True)
    location_data = fields.Nested(LocationDataSchema)


class SessionBlockPersonLinkSchema(mm.SQLAlchemyAutoSchema):
    affiliation_link = fields.Nested(AffiliationSchema)
    email_hash = fields.Function(lambda x: hashlib.md5(x.email.encode()).hexdigest() if x.email else None)

    class Meta:
        model = SessionBlockPersonLink
        fields = ('id', 'person_id', 'email', 'email_hash', 'first_name', 'last_name', 'title', 'affiliation',
                  'affiliation_link', 'address', 'phone', 'roles')

    @post_dump
    def _hide_sensitive_data(self, data, **kwargs):
        if self.context.get('hide_restricted_data'):
            del data['email']
            del data['address']
            del data['phone']
        return data


class SessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'start_dt', 'duration', 'code', 'conveners', 'location_data', 'session_id')

    start_dt = fields.DateTime()
    location_data = fields.Nested(LocationDataSchema)
    # TODO: Make it so that passing explicit `many=True` is not required
    conveners = fields.Nested(_SessionBlockPersonLinkSchema(many=True), attribute='person_links')
