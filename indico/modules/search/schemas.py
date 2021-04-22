# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump

from indico.core.db.sqlalchemy.links import LinkType
from indico.core.marshmallow import mm
from indico.modules.attachments import Attachment
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.notes.models.notes import EventNote
from indico.modules.search.base import SearchTarget
from indico.web.flask.util import url_for


class CategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url')

    url = fields.Function(lambda c: url_for('categories.display', category_id=c['id']))


class DetailedCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        fields = ('id', 'title', 'url', 'path')

    path = fields.List(fields.Nested(CategorySchema), attribute='chain')

    @post_dump()
    def update_path(self, c, **kwargs):
        c['path'] = c['path'][:-1]
        return c


class PersonSchema(mm.Schema):
    name = fields.Function(lambda e: e.title and f'{e.title} {e.name}' or e.name)
    affiliation = fields.String()


class LocationSchema(mm.Schema):
    venue_name = fields.String()
    room_name = fields.String()
    address = fields.String()


class EventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('event_id', 'type', 'type_format', 'title', 'description', 'url', 'keywords', 'location', 'persons',
                  'category_path', 'start_dt', 'end_dt')

    event_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.event.name)
    type_format = fields.String(attribute='_type.name')
    location = fields.Function(lambda event: LocationSchema().dump(event))
    persons = fields.List(fields.Nested(PersonSchema), attribute='person_links')
    category_path = fields.List(fields.Nested(CategorySchema), attribute='detailed_category_chain')
    note = fields.String()


class AttachmentSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Attachment
        fields = ('attachment_id', 'type', 'type_format', 'title', 'filename', 'event_id', 'contribution_id',
                  'subcontribution_id', 'user', 'url', 'category_path', 'content', 'modified_dt')

    attachment_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.attachment.name)
    type_format = fields.String(attribute='type.name')
    filename = fields.String(attribute='file.filename')
    event_id = fields.Int(attribute='folder.event.id')
    contribution_id = fields.Method('_contribution_id')
    subcontribution_id = fields.Method('_subcontribution_id')
    user = fields.Nested(PersonSchema)
    category_path = fields.List(fields.Nested(CategorySchema), attribute='folder.event.detailed_category_chain')
    url = fields.String(attribute='download_url')
    content = fields.String()

    def _contribution_id(self, attachment):
        return attachment.folder.contribution_id if attachment.folder.link_type == LinkType.contribution else None

    def _subcontribution_id(self, attachment):
        return attachment.folder.subcontribution_id \
            if attachment.folder.link_type == LinkType.subcontribution else None


class ContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('contribution_id', 'type', 'type_format', 'event_id', 'title', 'description', 'location',
                  'persons', 'url', 'category_path', 'start_dt', 'end_dt')

    contribution_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.contribution.name)
    type_format = fields.String(attribute='type.name')
    location = fields.Function(lambda contrib: LocationSchema().dump(contrib))
    persons = fields.List(fields.Nested(PersonSchema), attribute='person_links')
    category_path = fields.List(fields.Nested(CategorySchema), attribute='event.detailed_category_chain')
    url = fields.Function(lambda contrib: url_for('contributions.display_contribution', contrib, _external=False))


class SubContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SubContribution
        fields = ('subcontribution_id', 'type', 'title', 'description', 'event_id', 'contribution_id', 'persons',
                  'location', 'url', 'category_path')

    subcontribution_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.subcontribution.name)
    event_id = fields.Int(attribute='contribution.event_id')
    persons = fields.List(fields.Nested(PersonSchema), attribute='person_links')
    location = fields.Function(lambda subc: LocationSchema().dump(subc.contribution))
    category_path = fields.List(fields.Nested(CategorySchema), attribute='event.detailed_category_chain')
    url = fields.Function(lambda subc: url_for('contributions.display_subcontribution', subc, _external=False))


class EventNoteSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNote
        fields = ('note_id', 'type', 'content', 'event_id', 'contribution_id', 'subcontribution_id', 'url',
                  'category_path', 'created_dt')

    note_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.event_note.name)
    content = fields.Str(attribute='html')
    contribution_id = fields.Int(attribute='object.id')
    subcontribution_id = fields.Int()
    category_path = fields.List(fields.Nested(CategorySchema), attribute='event.detailed_category_chain')
    url = fields.Function(lambda note: url_for('event_notes.view', note, _external=False))
    # session_id = fields.Function(lambda note: note.session.id if note.session else None)
    created_dt = fields.DateTime(attribute='current_revision.created_dt', format='%Y-%m-%dT%H:%M')
