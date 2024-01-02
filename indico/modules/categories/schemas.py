# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.marshmallow import fields, mm
from indico.modules.categories import Category
from indico.modules.categories.models.event_move_request import EventMoveRequest
from indico.modules.events import Event
from indico.modules.users import User


class MoveRequestEventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'start_dt', 'end_dt')


class MoveRequestCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'chain_titles')


class CategoryUserSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'full_name', 'first_name', 'last_name', 'title', 'affiliation', 'avatar_url')


class EventMoveRequestSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventMoveRequest
        fields = ('id', 'event', 'category', 'requestor', 'requestor_comment', 'state', 'requested_dt')

    event = fields.Nested(MoveRequestEventSchema)
    category = fields.Nested(MoveRequestCategorySchema, attribute='event.category')
    requestor = fields.Nested(CategoryUserSchema)
