# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump

from indico.core.marshmallow import mm
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.search.base import SearchTarget
from indico.modules.users.models.users import User
from indico.util.marshmallow import NoneRemovingList
from indico.util.string import strip_tags
from indico.web.flask.util import url_for


class CategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url')

    url = fields.Function(lambda c: url_for('categories.display', category_id=c['id']))


class DetailedCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        fields = ('type', 'category_id', 'title', 'category_path')

    category_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.category.name)
    category_path = fields.List(fields.Nested(CategorySchema), attribute='chain')

    @post_dump
    def update_path(self, c, **kwargs):
        c['category_path'] = c['category_path'][:-1]
        return c


class PersonSchema(mm.Schema):
    name = fields.Function(lambda p: p.get_full_name(last_name_first=False, last_name_upper=False,
                                                     abbrev_first_name=False, show_title=False))
    affiliation = fields.Function(lambda p: p.affiliation or None)

    @post_dump(pass_original=True)
    def skip_system_user(self, data, orig, **kwargs):
        # obj can be a User or a PersonLinkBase subclass
        user = orig if isinstance(orig, User) else orig.person.user
        if user and user.is_system:
            return None
        return data


class LocationSchema(mm.Schema):
    venue_name = fields.String()
    room_name = fields.String()
    address = fields.String()


class EventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('event_id', 'type', 'event_type', 'title', 'description', 'url', 'keywords', 'location', 'persons',
                  'category_id', 'category_path', 'start_dt', 'end_dt')

    event_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.event.name)
    event_type = fields.String(attribute='_type.name')
    location = fields.Function(lambda event: LocationSchema().dump(event))
    persons = NoneRemovingList(fields.Nested(PersonSchema), attribute='person_links')
    category_id = fields.Int()
    category_path = fields.List(fields.Nested(CategorySchema), attribute='detailed_category_chain')


class HTMLStrippingEventSchema(EventSchema):
    @post_dump
    def _strip_html(self, data, **kwargs):
        data['description'] = strip_tags(data['description'])
        return data
