# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.marshmallow import fields, mm
from indico.modules.categories.models.event_move_request import EventMoveRequest
from indico.modules.events import Event
from indico.modules.users import User


class CategoryEventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('title', 'id')


class CategoryUserSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'title', 'affiliation', 'avatar_url')


class EventMoveRequestSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventMoveRequest
        fields = ('id', 'event', 'category_id', 'submitter', 'state', 'submitted_dt')

    event = fields.Nested(CategoryEventSchema)
    submitter = fields.Nested(CategoryUserSchema)
