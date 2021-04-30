# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, ValidationError, fields
from marshmallow_enum import EnumField
from marshmallow_oneofschema import OneOfSchema

from indico.core.marshmallow import mm
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.events.models.events import EventType
from indico.modules.search.base import SearchTarget
from indico.web.flask.util import url_for


class _ResultSchemaBase(mm.Schema):
    class Meta:
        unknown = EXCLUDE


class CategoryPathSchema(_ResultSchemaBase):
    id = fields.Int(required=True)
    title = fields.String(required=True)


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
    event_type = EnumField(EventType, required=True)
    start_dt = fields.DateTime(required=True)
    end_dt = fields.DateTime(required=True)
    persons = fields.List(fields.Nested(PersonSchema), required=True)
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('events.display', event_id=data['event_id'])


class ContributionResultSchema(ResultSchemaBase):
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.contribution))
    event_id = fields.Int(required=True)
    contribution_id = fields.Int(required=True)
    title = fields.String(required=True)
    start_dt = fields.DateTime(missing=None)
    end_dt = fields.DateTime(required=True)
    persons = fields.List(fields.Nested(PersonSchema), required=True)
    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('contributions.display_contribution', event_id=data['event_id'],
                       contrib_id=data['contribution_id'])


class SubContributionResultSchema(ContributionResultSchema):
    type = EnumField(SearchTarget, validate=require_search_target(SearchTarget.subcontribution))
    subcontribution_id = fields.Int(required=True)

    def _get_url(self, data):
        return url_for('contributions.display_subcontribution', event_id=data['event_id'],
                       contrib_id=data['contribution_id'], subcontrib_id=data['subcontribution_id'])


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
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('attachments.download', event_id=data['event_id'],
                       contrib_id=data['contribution_id'], subcontrib_id=data['subcontribution_id'],
                       folder_id=data['folder_id'], attachment_id=data['attachment_id'],
                       filename=(data['filename'] or 'go'))


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
    url = fields.Method('_get_url')

    def _get_url(self, data):
        return url_for('event_notes.view', event_id=data['event_id'],
                       contrib_id=data['contribution_id'], subcontrib_id=data['subcontribution_id'])


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
