# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE, fields

from indico.core.marshmallow import mm
from indico.modules.events.contributions.schemas import ContributionRESTSchema, TimezoneAwareSessionBlockSchema
from indico.modules.events.person_link_schemas import ContributionPersonLinkSchema as _ContributionPersonLinkSchema
from indico.modules.events.person_link_schemas import SessionBlockPersonLinkSchema as _SessionBlockPersonLinkSchema
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.schemas import SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.modules.events.timetable.serializer import TimetableSerializer
from indico.util.locations import LocationDataSchema, LocationParentSchema
from indico.util.marshmallow import EventTimezoneDateTimeField, NonPartialNested


class SessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'start_dt', 'duration', 'code', 'person_links', 'location_data', 'location_parent',
                  'child_location_parent', 'session_id', 'session_title', 'attachments')
        rh_context = ('event', {'object': 'session_block'})

    start_dt = EventTimezoneDateTimeField()
    location_data = fields.Nested(LocationDataSchema)
    location_parent = fields.Nested(LocationParentSchema, attribute='resolved_location_parent')
    child_location_parent = fields.Nested(LocationParentSchema)
    person_links = NonPartialNested(_SessionBlockPersonLinkSchema(many=True, unknown=EXCLUDE))
    duration = fields.TimeDelta(required=True)
    session_title = fields.String(attribute='session.title', dump_only=True)
    attachments = fields.Function(lambda obj: TimetableSerializer.get_attachment_data(obj.session))


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
        )

    # TODO sync person_links code with parent schema and remove here
    person_links = NonPartialNested(_ContributionPersonLinkSchema(many=True, unknown=EXCLUDE))
    location_parent = NonPartialNested(LocationParentSchema, attribute='resolved_location_parent')
    session_block = NonPartialNested(TimezoneAwareSessionBlockSchema)
    session_block_id = fields.Integer(allow_none=True)
    session_id = fields.Integer(dump_only=True)
    event_id = fields.Integer(dump_only=True)  # XXX needed?
    parent_id = fields.Integer(allow_none=True, load_only=True)
    attachments = fields.Function(TimetableSerializer.get_attachment_data)
