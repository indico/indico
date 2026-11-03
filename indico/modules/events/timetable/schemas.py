# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.contributions.schemas import ContributionRESTSchema, TimezoneAwareSessionBlockSchema
from indico.modules.events.sessions.schemas import SessionBlockRESTSchema, SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.events.timetable.serializer import TimetableSerializer, get_entry_type
from indico.util.locations import LocationDataSchema, LocationParentSchema
from indico.util.marshmallow import EventTimezoneDateTimeField, NonPartialNested


class SessionBlockSchema(SessionBlockRESTSchema):
    class Meta(SessionBlockRESTSchema.Meta):
        fields = (
            *SessionBlockRESTSchema.Meta.fields,
            'session_id',
            'session_title',
            'location_parent',
            'child_location_parent',
            'attachments',
            'type',
        )

    session_title = fields.String(attribute='session.title', dump_only=True)
    location_parent = NonPartialNested(LocationParentSchema, attribute='resolved_location_parent')
    child_location_parent = fields.Nested(LocationParentSchema)
    attachments = fields.Function(lambda obj: TimetableSerializer.get_attachment_data(obj.session))
    type = fields.Function(lambda __: get_entry_type(TimetableEntryType.SESSION_BLOCK))


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
    type = fields.Function(lambda __: get_entry_type(TimetableEntryType.BREAK))
    parent_id = fields.Integer(allow_none=True, attribute='timetable_entry.parent_id')
    session_block_id = fields.Integer(allow_none=True, attribute='session_block.id')
    session_id = fields.Function(_get_break_session_id, dump_only=True)


class ContributionSchema(ContributionRESTSchema):
    class Meta(ContributionRESTSchema.Meta):
        fields = (
            *ContributionRESTSchema.Meta.fields,
            'location_parent',
            'session_block',
            'session_block_id',
            'session_id',
            'event_id',
            'parent_id',
            'attachments',
            'type',
        )

    location_parent = NonPartialNested(LocationParentSchema, attribute='resolved_location_parent')
    session_block = NonPartialNested(TimezoneAwareSessionBlockSchema)
    session_block_id = fields.Integer(allow_none=True)
    session_id = fields.Integer(dump_only=True)
    event_id = fields.Integer(dump_only=True)  # XXX needed?
    parent_id = fields.Integer(allow_none=True, load_only=True)
    attachments = fields.Function(TimetableSerializer.get_attachment_data)
    type = fields.Function(lambda __: get_entry_type(TimetableEntryType.CONTRIBUTION))
