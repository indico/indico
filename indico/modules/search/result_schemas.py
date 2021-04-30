# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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
    name = fields.String(required=True)
    affiliation = fields.String(missing='')


class HighlightSchema(_ResultSchemaBase):
    content = fields.List(fields.String())


class ResultSchemaBase(_ResultSchemaBase):
    category_path = fields.List(fields.Nested(CategoryPathSchema), required=True)


def require_search_target(target):
    def validate(value):
        if value != target:
            raise ValidationError(f'type must be {target}, got {value}')

    return validate


class EventResultSchema(ResultSchemaBase):
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.event))
    event_id = fields.Int(required=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    event_type = EnumField(EventType, required=True)
    start_dt = fields.DateTime(required=True)
    end_dt = fields.DateTime(required=True)
    persons = fields.List(fields.Nested(PersonSchema), required=True)
    # extra fields that are not taken from the data returned by the search engine
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('events.display', event_id=data['event_id'])


class ContributionResultSchema(ResultSchemaBase):
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.contribution))
    event_id = fields.Int(required=True)
    contribution_id = fields.Int(required=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    start_dt = fields.DateTime(missing=None)
    end_dt = fields.DateTime(required=True)
    persons = fields.List(fields.Nested(PersonSchema), required=True)
    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)
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
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.subcontribution))
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
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.attachment))
    attachment_id = fields.Int(required=True)
    folder_id = fields.Int(required=True)
    event_id = fields.Int(required=True)
    contribution_id = fields.Int(missing=None)
    subcontribution_id = fields.Int(missing=None)
    title = fields.String(required=True)
    filename = fields.String(missing=None)
    user = fields.Nested(PersonSchema, missing=None)
    attachment_type = EnumField(AttachmentType, required=True)
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
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.event_note))
    note_id = fields.Int(required=True)
    event_id = fields.Int(required=True)
    contribution_id = fields.Int(missing=None)
    subcontribution_id = fields.Int(missing=None)
    title = fields.String(required=True)
    user = fields.Nested(PersonSchema, missing=None)
    modified_dt = fields.DateTime(required=True)
    content = fields.String(required=True)
    highlight = fields.Nested(HighlightSchema, missing=None)
    # extra fields that are not taken from the data returned by the search engine
    url = fields.Method('_get_url')
    event_path = fields.Method('_get_event_path', dump_only=True)

    def _get_url(self, data):
        return url_for('event_notes.view', event_id=data['event_id'],
                       contrib_id=data['contribution_id'], subcontrib_id=data['subcontribution_id'])

    def _get_event_path(self, data):
        if not (note := EventNote.get(data['note_id'])):
            return []
        return _get_event_path(note)


class BucketSchema(_ResultSchemaBase):
    key = fields.String(required=True)
    doc_count = fields.Int(required=True)
    filter = fields.String(required=True)


class AggregationSchema(_ResultSchemaBase):
    label = fields.String(required=True)
    buckets = fields.List(fields.Nested(BucketSchema), required=True)


class ResultItemSchema(OneOfSchema):
    type_field = 'type'
    type_field_remove = False
    type_schemas = {
        SearchTarget.event.name: EventResultSchema,
        SearchTarget.contribution.name: ContributionResultSchema,
        SearchTarget.subcontribution.name: SubContributionResultSchema,
        SearchTarget.attachment.name: AttachmentResultSchema,
        SearchTarget.event_note.name: EventNoteResultSchema,
    }

    class Meta:
        # OneOfEschema passes the own schema's `unknown` value to the target schemas
        unknown = EXCLUDE

    def get_obj_type(self, obj):
        return obj['type'].name

    def _dump(self, obj, *, update_fields=True, **kwargs):
        rv = super()._dump(obj, update_fields=update_fields, **kwargs)
        if isinstance(rv, tuple):
            # https://github.com/marshmallow-code/marshmallow-oneofschema/issues/48
            raise ValidationError(rv[1]['_schema'])
        return rv


class ResultSchema(_ResultSchemaBase):
    total = fields.Int(required=True)
    pages = fields.Int(required=True)
    results = fields.List(fields.Nested(ResultItemSchema), required=True)
    aggregations = fields.Dict(fields.String(), fields.Nested(AggregationSchema), missing={})
