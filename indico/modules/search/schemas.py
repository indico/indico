# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.
from marshmallow import post_dump

from indico.core.db.sqlalchemy.links import LinkType
from indico.core.marshmallow import mm
from indico.modules.attachments import Attachment
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.web.flask.util import url_for


class CategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url')

    url = mm.Function(lambda c: url_for('categories.display', category_id=c['id']))


class DetailedCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        fields = ('id', 'title', 'url', 'path')

    path = mm.List(mm.Nested(CategorySchema), attribute='chain')

    @post_dump()
    def update_path(self, c, **kwargs):
        c['path'] = c['path'][:-1]
        return c


class PersonSchema(mm.Schema):
    id = mm.Int()
    name = mm.Function(lambda e: e.title and f'{e.title} {e.name}' or e.name)
    affiliation = mm.String()


class LocationSchema(mm.Schema):
    venue_name = mm.String()
    room_name = mm.String()
    address = mm.String()


# TODO: Date formats
class EventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'url', 'type', 'keywords', 'category_path', 'chair_persons',
                  'location', 'start_dt', 'end_dt')

    location = mm.Function(lambda event: LocationSchema().dump(event))
    chair_persons = mm.List(mm.Nested(PersonSchema), attribute='person_links')
    category_path = mm.List(mm.Nested(CategorySchema), attribute='detailed_category_chain')


class AttachmentSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Attachment
        fields = ('type', 'title', 'url', 'filename', 'event_id', 'contribution_id', 'user', 'content', 'modified_dt')

    filename = mm.String(attribute='file.filename')
    event_id = mm.Int(attribute='folder.event.id')
    contribution_id = mm.Method('_contribution_id')
    subcontribution_id = mm.Method('_subcontribution_id')
    user = mm.Nested(PersonSchema)
    url = mm.String(attribute='download_url')
    content = mm.String()

    def _contribution_id(self, attachment):
        return attachment.folder.contribution_id if attachment.folder.link_type == LinkType.contribution else None

    def _subcontribution_id(self, attachment):
        return attachment.folder.subcontribution_id \
            if attachment.folder.link_type == LinkType.subcontribution else None


class ContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'type', 'event_id', 'title', 'description', 'location', 'persons', 'url', 'start_dt', 'end_dt')

    type = mm.String(attribute='type.name')
    location = mm.Function(lambda contrib: LocationSchema().dump(contrib))
    persons = mm.List(mm.Nested(PersonSchema), attribute='person_links')
    url = mm.Function(lambda contrib: url_for('contributions.display_contribution', contrib, _external=False))


class ResultSchema(mm.Schema):
    page = mm.Int(required=True)
    pages = mm.Int(required=True)
    total = mm.Int(required=True)


class CategoryResultSchema(ResultSchema):
    results = mm.Nested(DetailedCategorySchema, required=True, many=True, attribute='items')


class EventResultSchema(ResultSchema):
    results = mm.Nested(EventSchema, required=True, many=True, attribute='items')
