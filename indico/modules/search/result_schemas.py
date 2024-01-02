# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, ValidationError, fields
from marshmallow_enum import EnumField
from marshmallow_oneofschema import OneOfSchema

from indico.core.db.sqlalchemy.links import LinkType
from indico.core.marshmallow import mm
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.models.events import Event, EventType
from indico.modules.events.notes.models.notes import EventNote
from indico.modules.search.base import SearchTarget
from indico.web.flask.util import url_for


class _ResultSchemaBase(mm.Schema):
    class Meta:
        unknown = EXCLUDE


class CategoryPathSchema(_ResultSchemaBase):
    id = fields.Int(required=True)
    title = fields.String(required=True)
    url = fields.Method('_get_url')
    type = fields.Constant('category')

    def _get_url(self, data):
        return url_for('categories.display', category_id=data['id'])


class PersonSchema(_ResultSchemaBase):
    #: The person's name
    name = fields.String(required=True)
    #: The person's affiliation
    affiliation = fields.String(load_default=None)


class HighlightSchema(_ResultSchemaBase):
    #: The field's content to highlight
    content = fields.List(fields.String())
    #: The field's description to highlight
    description = fields.List(fields.String())


class ResultSchemaBase(_ResultSchemaBase):
    #: The parent category chain
    category_path: CategoryPathSchema = fields.List(fields.Nested(CategoryPathSchema), required=True)


def require_search_target(target):
    def validate(value):
        if value != target:
            raise ValidationError(f'type must be {target}, got {value}')

    return validate


class CategoryResultSchema(ResultSchemaBase):
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.category))
    category_id = fields.Int(required=True)
    title = fields.String(required=True)
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('categories.display', category_id=data['category_id'])


class LocationResultSchema(mm.Schema):
    #: The venue name
    venue_name = fields.String(required=True)
    #: The room name
    room_name = fields.String(required=True)
    #: The address
    address = fields.String(required=True)


class EventResultSchema(ResultSchemaBase):
    #: The record type
    type: SearchTarget = EnumField(SearchTarget, validate=require_search_target(SearchTarget.event))
    #: The event id
    event_id = fields.Int(required=True)
    #: The event title
    title = fields.String(required=True)
    #: The event description
    description = fields.String(required=True)
    #: The event type
    event_type = EnumField(EventType, required=True)
    #: The event start date time
    start_dt = fields.DateTime(required=True)
    #: The event end date time
    end_dt = fields.DateTime(required=True)
    #: The event associated persons
    persons: PersonSchema = fields.List(fields.Nested(PersonSchema), required=True)
    #: The event location
    location: LocationResultSchema = fields.Nested(LocationResultSchema, required=True)
    #: The event content to highlight
    highlight = fields.Nested(HighlightSchema, load_default=lambda: {})
    # extra fields that are not taken from the data returned by the search engine
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('events.display', event_id=data['event_id'])


class ContributionResultSchema(ResultSchemaBase):
    #: The record type
    type: SearchTarget = EnumField(SearchTarget, validate=require_search_target(SearchTarget.contribution))
    #: The contribution id
    contribution_id = fields.Int(required=True)
    #: The contribution event id
    event_id = fields.Int(required=True)
    #: The contribution title
    title = fields.String(required=True)
    #: The contribution description
    description = fields.String(required=True)
    #: The contribution start date time
    start_dt = fields.DateTime(load_default=None)
    #: The contribution end date time
    end_dt = fields.DateTime(load_default=None)
    #: The contribution associated persons
    persons: PersonSchema = fields.List(fields.Nested(PersonSchema), required=True)
    #: The contribution location
    location: LocationResultSchema = fields.Nested(LocationResultSchema, required=True)
    #: The contribution duration
    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)
    #: The contribution content to highlight
    highlight = fields.Nested(HighlightSchema, load_default=lambda: {})
    # extra fields that are not taken from the data returned by the search engine
    url = fields.Method('_get_url')
    event_path = fields.Method('_get_event_path', dump_only=True)

    def _get_url(self, data):
        return url_for('contributions.display_contribution', event_id=data['event_id'],
                       contrib_id=data['contribution_id'])

    def _get_event_path(self, data):
        if not (event := Event.get(data['event_id'])):
            return []
        return [
            {'type': 'event', 'id': event.id, 'title': event.title, 'url': event.url}
        ]


class SubContributionResultSchema(ContributionResultSchema):
    #: The record type
    type: SearchTarget = EnumField(SearchTarget, validate=require_search_target(SearchTarget.subcontribution))
    #: The sub-contribution id
    subcontribution_id = fields.Int(required=True)

    def _get_url(self, data):
        return url_for('contributions.display_subcontribution', event_id=data['event_id'],
                       contrib_id=data['contribution_id'], subcontrib_id=data['subcontribution_id'])

    def _get_event_path(self, data):
        if not (contrib := Contribution.get(data['contribution_id'])):
            return []
        contrib_url = url_for('contributions.display_contribution', contrib)
        return [
            {'type': 'event', 'id': contrib.event.id, 'title': contrib.event.title, 'url': contrib.event.url},
            {'type': 'contribution', 'id': contrib.id, 'title': contrib.title, 'url': contrib_url},
        ]


def _get_event_path(obj):
    path = [{'type': 'event', 'id': obj.event.id, 'title': obj.event.title, 'url': obj.event.url}]
    if obj.link_type == LinkType.contribution:
        contrib = obj.contribution
        contrib_url = url_for('contributions.display_contribution', contrib)
        path.append({'type': 'contribution', 'id': contrib.id, 'title': contrib.title, 'url': contrib_url})
    elif obj.link_type == LinkType.subcontribution:
        subcontrib = obj.subcontribution
        subcontrib_url = url_for('contributions.display_subcontribution', subcontrib)
        contrib = subcontrib.contribution
        contrib_url = url_for('contributions.display_contribution', contrib)
        path += [
            {'type': 'contribution', 'id': contrib.id, 'title': contrib.title, 'url': contrib_url},
            {'type': 'subcontribution', 'id': subcontrib.id, 'title': subcontrib.title, 'url': subcontrib_url},
        ]
    return path


class AttachmentResultSchema(ResultSchemaBase):
    #: The record type
    type: SearchTarget = EnumField(SearchTarget, validate=require_search_target(SearchTarget.attachment))
    #: The attachment id
    attachment_id = fields.Int(required=True)
    #: The attachment folder id
    folder_id = fields.Int(required=True)
    #: The attachment event id
    event_id = fields.Int(required=True)
    #: The attachment contribution id
    contribution_id = fields.Int(load_default=None)
    #: The attachment sub-contribution id
    subcontribution_id = fields.Int(load_default=None)
    #: The attachment title
    title = fields.String(required=True)
    #: The attachment filename
    filename = fields.String(load_default=None)
    #: The attachment author
    user: PersonSchema = fields.Nested(PersonSchema, load_default=None)
    #: The attachment type
    attachment_type: AttachmentType = EnumField(AttachmentType, required=True)
    #: The attachment last modified date time
    modified_dt = fields.DateTime(required=True)
    # extra fields that are not taken from the data returned by the search engine
    url = fields.Method('_get_url')
    event_path = fields.Method('_get_event_path', dump_only=True)

    def _get_url(self, data):
        return url_for('attachments.download', event_id=data['event_id'],
                       contrib_id=data['contribution_id'], subcontrib_id=data['subcontribution_id'],
                       folder_id=data['folder_id'], attachment_id=data['attachment_id'],
                       filename=(data['filename'] or 'go'))

    def _get_event_path(self, data):
        if not (folder := AttachmentFolder.get(data['folder_id'])):
            return []
        return _get_event_path(folder)


class EventNoteResultSchema(ResultSchemaBase):
    #: The record type
    type: SearchTarget = EnumField(SearchTarget, validate=require_search_target(SearchTarget.event_note))
    #: The note id
    note_id = fields.Int(required=True)
    #: The note event id
    event_id = fields.Int(required=True)
    #: The note contribution id
    contribution_id = fields.Int(load_default=None)
    #: The note sub-contribution id
    subcontribution_id = fields.Int(load_default=None)
    #: The note title
    title = fields.String(required=True)
    #: The note author
    user: PersonSchema = fields.Nested(PersonSchema, load_default=None)
    #: The note last modification date time
    modified_dt = fields.DateTime(required=True)
    #: The note content
    content = fields.String(required=True)
    #: The note content to highlight
    highlight: HighlightSchema = fields.Nested(HighlightSchema, load_default=lambda: {})
    # extra fields that are not taken from the data returned by the search engine
    url = fields.Method('_get_url')
    event_path = fields.Method('_get_event_path', dump_only=True)

    def _get_url(self, data):
        return url_for('event_notes.goto', event_id=data['event_id'], note_id=data['note_id'])

    def _get_event_path(self, data):
        if not (note := EventNote.get(data['note_id'])):
            return []
        return _get_event_path(note)


class BucketSchema(_ResultSchemaBase):
    """Represents an individual aggregation bucket element."""

    #: The aggregation key.
    key: str = fields.String(required=True)
    #: The number of elements.
    count: int = fields.Int(required=True)
    #: The key that identifies the element's filter.
    filter: str = fields.String(required=True)


class AggregationSchema(_ResultSchemaBase):
    """Represents an aggregation list."""

    #: The name of the aggregation.
    label: str = fields.String(required=True)
    #: A bucket list representing each group.
    buckets: list[BucketSchema] = fields.List(fields.Nested(BucketSchema), required=True)


class ResultItemSchema(OneOfSchema):
    type_field = 'type'
    type_field_remove = False
    type_schemas = {
        SearchTarget.category.name: CategoryResultSchema,
        SearchTarget.event.name: EventResultSchema,
        SearchTarget.contribution.name: ContributionResultSchema,
        SearchTarget.subcontribution.name: SubContributionResultSchema,
        SearchTarget.attachment.name: AttachmentResultSchema,
        SearchTarget.event_note.name: EventNoteResultSchema,
    }

    class Meta:
        # OneOfSchema passes the own schema's `unknown` value to the target schemas
        unknown = EXCLUDE

    def get_obj_type(self, obj):
        return obj['type'].name

    def _dump(self, obj, *, update_fields=True, **kwargs):
        rv = super()._dump(obj, update_fields=update_fields, **kwargs)
        if isinstance(rv, tuple):
            # https://github.com/marshmallow-code/marshmallow-oneofschema/issues/48
            raise ValidationError(rv[1]['_schema'])
        return rv


class PageNavSchema(_ResultSchemaBase):
    prev = fields.Int(required=True, allow_none=True)
    next = fields.Int(required=True, allow_none=True)


class ResultSchema(_ResultSchemaBase):
    total = fields.Int(required=True)
    pages = fields.Int(load_default=None)
    pagenav = fields.Nested(PageNavSchema, load_default=None)
    results = fields.List(fields.Nested(ResultItemSchema), required=True)
    aggregations = fields.Dict(fields.String(), fields.Nested(AggregationSchema), load_default=lambda: {})
