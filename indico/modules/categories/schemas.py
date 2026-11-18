# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
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


class CategoryManagerSchema(mm.Schema):
    id = fields.Integer()
    full_name = fields.String()
    avatar_url = fields.String()


class CategoryMaterialSchema(mm.Schema):
    id = fields.Integer()
    title = fields.String()
    url = fields.Method('_get_url')
    is_protected = fields.Boolean()
    attachments = fields.List(fields.Nested(lambda: CategoryMaterialSchema()))

    def _get_url(self, material):
        if not hasattr(material, 'type'):
            return None
        return material.link_url if material.type.name == 'link' else material.download_url


class CategoryMaterialsSchema(mm.Schema):
    files = fields.List(fields.Nested(CategoryMaterialSchema), dump_default=list)
    folders = fields.List(fields.Nested(CategoryMaterialSchema), dump_default=list)


class EventMoveRequestSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventMoveRequest
        fields = ('id', 'event', 'category', 'requestor', 'requestor_comment', 'state', 'requested_dt')

    event = fields.Nested(MoveRequestEventSchema)
    category = fields.Nested(MoveRequestCategorySchema, attribute='event.category')
    requestor = fields.Nested(CategoryUserSchema)
