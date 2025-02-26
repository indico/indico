# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields, post_dump

from indico.core.marshmallow import mm
from indico.modules.events.sessions.schemas import LocationDataSchema, SessionBlockSchema, SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.search.schemas import ContributionSchema


class TimetableEntrySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = TimetableEntry
        fields = ('id', 'event_id', 'parent_id', 'session_block_id',
                  'contribution_id', 'break_id', 'type', 'start_dt',
                  'end_dt', 'duration', 'object')

    type = fields.Method('get_type')
    object = fields.Method('get_object')

    def get_type(self, obj):
        return obj.type.name

    def get_object(self, obj):
        if obj.type == TimetableEntryType.SESSION_BLOCK:
            return SessionBlockSchema().dump(obj.session_block)
        elif obj.type == TimetableEntryType.CONTRIBUTION:
            return ContributionSchema().dump(obj.contribution)
        elif obj.type == TimetableEntryType.BREAK:
            return BreakSchema().dump(obj.break_)
        return None

    @post_dump
    def remove_nulls(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class BreakSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Break
        fields = ('id', 'title', 'description', 'start_dt', 'duration', 'location_data', 'colors')

    title = fields.String(required=True)
    description = fields.String()
    start_dt = fields.DateTime(required=True)
    duration = fields.TimeDelta(required=True)
    location_data = fields.Nested(LocationDataSchema)
    colors = fields.Nested(SessionColorSchema)
