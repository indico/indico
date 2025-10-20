# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, fields

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.schemas import (ContribFieldValueSchema, ContributionReferenceSchema,
                                                         TimezoneAwareSessionBlockSchema)
from indico.modules.events.person_link_schemas import ContributionPersonLinkSchema as _ContributionPersonLinkSchema
from indico.modules.events.person_link_schemas import SessionBlockPersonLinkSchema as _SessionBlockPersonLinkSchema
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.schemas import SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.util.locations import LocationDataSchema, LocationParentSchema
from indico.util.marshmallow import EventTimezoneDateTimeField


class SessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'start_dt', 'duration', 'code', 'conveners', 'location_data', 'location_parent',
                  'child_location_parent', 'session_id', 'session_title')
        rh_context = ('event',)

    start_dt = EventTimezoneDateTimeField()
    location_data = fields.Nested(LocationDataSchema)
    location_parent = fields.Nested(LocationParentSchema, attribute='resolved_location_parent')
    child_location_parent = fields.Nested(LocationParentSchema)
    conveners = fields.List(fields.Nested(_SessionBlockPersonLinkSchema(unknown=EXCLUDE)), attribute='person_links')
    duration = fields.TimeDelta(required=True)
    session_title = fields.String(attribute='session.title', dump_only=True)


def _get_break_session_id(entry):
    if entry.timetable_entry.parent:
        return entry.timetable_entry.parent.session_block.session_id


class BreakSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Break
        fields = ('id', 'title', 'description', 'start_dt', 'duration', 'location_data', 'location_parent', 'colors',
                  'type', 'parent_id', 'session_block_id', 'session_id')
        rh_context = ('event',)

    title = fields.String(required=True)
    description = fields.String()
    start_dt = EventTimezoneDateTimeField()
    duration = fields.TimeDelta(required=True)
    location_data = fields.Nested(LocationDataSchema)
    location_parent = fields.Nested(LocationParentSchema, attribute='resolved_location_parent')
    colors = fields.Nested(SessionColorSchema)
    parent_id = fields.Integer(allow_none=True, attribute='timetable_entry.parent_id')
    session_block_id = fields.Integer(attribute='timetable_entry.parent.session_block_id', allow_none=True)
    session_id = fields.Function(_get_break_session_id, dump_only=True)


class ContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'code', 'board_number', 'keywords', 'location_data', 'location_parent',
                  'start_dt', 'duration', 'event_id', 'references', 'custom_fields', 'person_links', 'session_block',
                  'session_block_id', 'session_id', 'parent_id')
        rh_context = ('event',)

    start_dt = EventTimezoneDateTimeField()
    _description = fields.String(attribute='description')
    # TODO: filter inactive and restricted contrib fields
    custom_fields = fields.List(fields.Nested(ContribFieldValueSchema), attribute='field_values')
    person_links = fields.Nested(_ContributionPersonLinkSchema(many=True, unknown=EXCLUDE))
    references = fields.List(fields.Nested(ContributionReferenceSchema))
    location_data = fields.Nested(LocationDataSchema)
    location_parent = fields.Nested(LocationParentSchema, attribute='resolved_location_parent')
    session_block = fields.Nested(TimezoneAwareSessionBlockSchema)
    session_id = fields.Integer(dump_only=True)
    duration = fields.TimeDelta(required=True)
    parent_id = fields.Integer(allow_none=True, load_only=True)
    session_block_id = fields.Integer(allow_none=True, load_only=True)
