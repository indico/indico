# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.schemas import ContributionReferenceSchema, TimezoneAwareSessionBlockSchema
from indico.modules.events.person_link_schemas import EventPersonLinkSchema
from indico.modules.events.sessions.schemas import LocationDataSchema, SessionBlockSchema, SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType


class BreakSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Break
        fields = ('id', 'title', 'description', 'start_dt', 'duration', 'location_data', 'colors', 'type')

    title = fields.String(required=True)
    description = fields.String()
    start_dt = fields.DateTime(required=True)
    duration = fields.TimeDelta(required=True)
    location_data = fields.Nested(LocationDataSchema)
    colors = fields.Nested(SessionColorSchema)


class ContributionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'code', 'board_number', 'keywords', 'location_data',
                  'event_id', 'references', 'person_links', 'session_block')

    person_links = fields.Nested(EventPersonLinkSchema, many=True, dump_only=True)
    references = fields.List(fields.Nested(ContributionReferenceSchema))
    location_data = fields.Nested(LocationDataSchema)
    session_block = fields.Nested(TimezoneAwareSessionBlockSchema)


class TimetableEntrySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = TimetableEntry
        fields = ('id', 'event_id', 'parent_id', 'session_block_id',
                  'contribution_id', 'break_id', 'type', 'start_dt',
                  'end_dt', 'duration', 'object')

    type = fields.Method('get_type')
    object = fields.Method('get_object')
    duration = fields.TimeDelta(precision=fields.TimeDelta.SECONDS)
    session_block_id = fields.Nested(SessionBlockSchema, only=('id',), dump_only=True)
    contribution_id = fields.Nested(ContributionSchema, only=('id',), dump_only=True)
    break_id = fields.Nested(BreakSchema, only=('id',), dump_only=True)

    def get_type(self, obj):
        return obj.type.name

    # def load_type(self, value):
    #     try:
    #         return TimetableEntryType[value]
    #     except KeyError:
    #         raise ValueError(f'Unsupported entry type: {value}')

    def get_object(self, obj):
        match obj.type:
            case TimetableEntryType.SESSION_BLOCK:
                return SessionBlockSchema(context=self.context).dump(obj.session_block)
            case TimetableEntryType.CONTRIBUTION:
                return ContributionSchema(context=self.context).dump(obj.contribution)
            case TimetableEntryType.BREAK:
                return BreakSchema(context=self.context).dump(obj.break_)
            case _:
                return None

    # def load_object(self, data, **kwargs):
    #     entry_type = self.entry_type
    #     if entry_type == TimetableEntryType.SESSION_BLOCK:
    #         return SessionBlockSchema(context=self.context).load(data, **kwargs)
    #     elif entry_type == TimetableEntryType.CONTRIBUTION:
    #         return ContributionSchema(context=self.context).load(data, **kwargs)
    #     elif entry_type == TimetableEntryType.BREAK:
    #         return BreakSchema(context=self.context).load(data, **kwargs)
    #     else:
    #         raise ValueError(f'Unsupported entry type: {entry_type}')

