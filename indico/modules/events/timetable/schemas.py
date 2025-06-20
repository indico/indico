# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, fields, pre_load

from indico.core.marshmallow import mm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.schemas import ContributionReferenceSchema
from indico.modules.events.person_link_schemas import ContributionPersonLinkSchema as _ContributionPersonLinkSchema
from indico.modules.events.person_link_schemas import SessionBlockPersonLinkSchema as _SessionBlockPersonLinkSchema
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.schemas import LocationDataSchema, SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType


class SimplePersonLinkSchema(_ContributionPersonLinkSchema):
    class Meta:
        model = _ContributionPersonLinkSchema
        fields = ('id', 'roles')


class SessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'start_dt', 'duration', 'code', 'conveners', 'location_data', 'session_id')

    start_dt = fields.DateTime(required=True)
    location_data = fields.Nested(LocationDataSchema)
    # TODO: Make it so that passing explicit `many=True` is not required
    conveners = fields.List(fields.Nested(
        _SessionBlockPersonLinkSchema(partial=False, unknown=EXCLUDE),
        partial=False,
        unknown=EXCLUDE
    ), attribute='person_links')
    duration = fields.TimeDelta(required=True)


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
                  'event_id', 'references', 'person_links', 'session_block', 'duration', 'start_dt',
                  'avatar_url', 'name')

    start_dt = fields.DateTime(required=True)
    duration = fields.TimeDelta(precision=fields.TimeDelta.SECONDS)
    person_links = fields.Nested(_ContributionPersonLinkSchema(many=True, partial=False), partial=False)
    references = fields.List(fields.Nested(ContributionReferenceSchema))
    location_data = fields.Nested(LocationDataSchema)


class TimetableEntrySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = TimetableEntry
        fields = ('id', 'event_id', 'parent_id', 'session_block_id',
                  'contribution_id', 'break_id', 'type', 'start_dt',
                  'end_dt', 'duration', 'object', 'contribution', 'break_',
                  'session_block')

    type = fields.Method('get_type', 'load_type')
    object = fields.Method('get_object', 'load_object')
    session_block_id = fields.Nested(SessionBlockSchema, only=('id',), dump_only=True)
    contribution_id = fields.Nested(ContributionSchema, only=('id',), dump_only=True)
    break_id = fields.Nested(BreakSchema, only=('id',), dump_only=True)

    @pre_load
    def _get_type(self, data, **kwargs):
        if 'type' in data:
            self.context['type'] = data['type']
        return data

    def load_type(self, value):
        try:
            return TimetableEntryType[value]
        except KeyError:
            raise ValueError(f'Unsupported entry type: {value}')

    def get_type(self, obj):
        return obj.type.name

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

    def load_object(self, data, **kwargs):
        entry_type = TimetableEntryType[self.context['type']]
        if entry_type == TimetableEntryType.SESSION_BLOCK:
            return SessionBlockSchema(context=self.context).load(data, **kwargs)
        elif entry_type == TimetableEntryType.CONTRIBUTION:
            return ContributionSchema(context=self.context).load(data, **kwargs)
        elif entry_type == TimetableEntryType.BREAK:
            return BreakSchema(context=self.context).load(data, **kwargs)
        else:
            raise ValueError(f'Unsupported entry type: {entry_type}')

