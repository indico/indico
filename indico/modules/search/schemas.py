# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump

from indico.core.db.sqlalchemy.links import LinkType
from indico.core.marshmallow import mm
from indico.modules.attachments.models.attachments import Attachment
from indico.modules.categories import Category
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.notes.models.notes import EventNote
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


class ContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('contribution_id', 'type', 'contribution_type', 'event_id', 'title', 'description', 'location',
                  'persons', 'url', 'category_id', 'category_path', 'start_dt', 'end_dt', 'duration')

    contribution_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.contribution.name)
    contribution_type = fields.String(attribute='type.name')
    location = fields.Function(lambda contrib: LocationSchema().dump(contrib))
    persons = NoneRemovingList(fields.Nested(PersonSchema), attribute='person_links')
    category_id = fields.Int(attribute='event.category_id')
    category_path = fields.List(fields.Nested(CategorySchema), attribute='event.detailed_category_chain')
    url = fields.Function(lambda contrib: url_for('contributions.display_contribution', contrib, _external=False))
    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)


class SubContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SubContribution
        fields = ('subcontribution_id', 'type', 'title', 'description', 'event_id', 'contribution_id', 'persons',
                  'location', 'url', 'category_id', 'category_path', 'start_dt', 'end_dt', 'duration')

    subcontribution_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.subcontribution.name)
    event_id = fields.Int(attribute='contribution.event_id')
    persons = NoneRemovingList(fields.Nested(PersonSchema), attribute='person_links')
    location = fields.Function(lambda subc: LocationSchema().dump(subc.contribution))
    category_id = fields.Int(attribute='event.category_id')
    category_path = fields.List(fields.Nested(CategorySchema), attribute='event.detailed_category_chain')
    url = fields.Function(lambda subc: url_for('contributions.display_subcontribution', subc, _external=False))
    start_dt = fields.DateTime(attribute='contribution.start_dt')
    end_dt = fields.DateTime(attribute='contribution.end_dt')
    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)


class AttachmentSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Attachment
        fields = ('attachment_id', 'folder_id', 'type', 'attachment_type', 'title', 'filename', 'event_id',
                  'contribution_id', 'subcontribution_id', 'user', 'url', 'category_id', 'category_path',
                  'modified_dt')

    attachment_id = fields.Int(attribute='id')
    folder_id = fields.Int(attribute='folder_id')
    type = fields.Constant(SearchTarget.attachment.name)
    attachment_type = fields.String(attribute='type.name')
    filename = fields.String(attribute='file.filename')
    event_id = fields.Int(attribute='folder.event.id')
    contribution_id = fields.Method('_contribution_id')
    subcontribution_id = fields.Int(attribute='folder.subcontribution_id')
    user = fields.Nested(PersonSchema)
    category_id = fields.Int(attribute='folder.event.category_id')
    category_path = fields.List(fields.Nested(CategorySchema), attribute='folder.event.detailed_category_chain')
    url = fields.String(attribute='download_url')

    def _contribution_id(self, attachment):
        if attachment.folder.link_type == LinkType.contribution:
            return attachment.folder.contribution_id
        elif attachment.folder.link_type == LinkType.subcontribution:
            return attachment.folder.subcontribution.contribution_id
        return None


class EventNoteSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNote
        fields = ('note_id', 'type', 'content', 'event_id', 'contribution_id', 'subcontribution_id', 'url',
                  'category_id', 'category_path', 'modified_dt', 'user', 'title')

    note_id = fields.Int(attribute='id')
    type = fields.Constant(SearchTarget.event_note.name)
    content = fields.Str(attribute='current_revision.source')
    title = fields.Str(attribute='object.title')
    contribution_id = fields.Method('_contribution_id')
    subcontribution_id = fields.Int()
    category_id = fields.Int(attribute='event.category_id')
    category_path = fields.List(fields.Nested(CategorySchema), attribute='event.detailed_category_chain')
    url = fields.Function(lambda note: url_for('event_notes.view', note, _external=False))
    modified_dt = fields.DateTime(attribute='current_revision.created_dt')
    user = fields.Nested(PersonSchema, attribute='current_revision.user')

    def _contribution_id(self, note):
        if note.link_type == LinkType.contribution:
            return note.contribution_id
        elif note.link_type == LinkType.subcontribution:
            return note.subcontribution.contribution_id


class HTMLStrippingEventSchema(EventSchema):
    @post_dump
    def _strip_html(self, data, **kwargs):
        data['description'] = strip_tags(data['description'])
        return data


class HTMLStrippingContributionSchema(ContributionSchema):
    @post_dump
    def _strip_html(self, data, **kwargs):
        data['description'] = strip_tags(data['description'])
        return data


class HTMLStrippingEventNoteSchema(EventNoteSchema):
    @post_dump
    def _strip_html(self, data, **kwargs):
        data['content'] = strip_tags(data['content'])
        return data
