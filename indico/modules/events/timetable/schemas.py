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
from indico.modules.events.sessions.schemas import LocationDataSchema, SessionColorSchema
from indico.modules.events.timetable.models.breaks import Break
from indico.util.marshmallow import EventTimezoneDateTimeField


class SessionBlockSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SessionBlock
        fields = ('id', 'title', 'start_dt', 'duration', 'code', 'conveners', 'location_data', 'session_id')
        rh_context = ('event',)

    start_dt = fields.DateTime(required=True)
    location_data = fields.Nested(LocationDataSchema)
    conveners = fields.List(fields.Nested(
        _SessionBlockPersonLinkSchema(unknown=EXCLUDE),
    ), attribute='person_links')
    duration = fields.TimeDelta(required=True)


class BreakSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Break
        fields = ('id', 'title', 'description', 'start_dt', 'duration', 'location_data', 'colors', 'type')
        rh_context = ('event',)

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
                  'start_dt', 'duration', 'event_id', 'references', 'custom_fields', 'person_links', 'session_block')
        rh_context = ('event',)

    start_dt = EventTimezoneDateTimeField()
    # TODO: filter inactive and resitricted contrib fields
    custom_fields = fields.List(fields.Nested(ContribFieldValueSchema), attribute='field_values')
    person_links = fields.Nested(_ContributionPersonLinkSchema(many=True, unknown=EXCLUDE))
    references = fields.List(fields.Nested(ContributionReferenceSchema))
    location_data = fields.Nested(LocationDataSchema)
    session_block = fields.Nested(TimezoneAwareSessionBlockSchema)
    duration = fields.TimeDelta(required=True)
