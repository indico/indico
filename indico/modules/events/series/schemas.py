# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from marshmallow import ValidationError, fields, validates

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event
from indico.modules.events.models.series import EventSeries
from indico.modules.events.schemas import EventDetailsSchema
from indico.util.i18n import _
from indico.util.marshmallow import ModelList, not_empty


class EventSeriesSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventSeries
        fields = ('id', 'events', 'show_sequence_in_title', 'show_links', 'event_title_pattern')

    id = fields.Int()
    events = fields.List(fields.Nested(EventDetailsSchema))


class EventSeriesUpdateSchema(EventSeriesSchema):
    class Meta(EventSeriesSchema.Meta):
        fields = ('events', 'show_sequence_in_title', 'show_links', 'event_title_pattern')
        rh_context = ('series',)

    events = ModelList(Event, filter_deleted=True, data_key='event_ids', required=True, validate=not_empty)

    @validates('events')
    def _check_event_ids(self, events, **kwargs):
        series_id = series.id if (series := self.context.get('series')) is not None else None

        if series_id is None and any(e.series for e in events):
            raise ValidationError(_('At least one event is already in a series.'))
        elif any(e.series and e.series_id != series_id for e in events):
            raise ValidationError(_('At least one event is already in a different series.'))

        if not all(e.can_manage(session.user) for e in events):
            raise ValidationError(_('You must be a manager of all chosen events.'))
        if any(e.is_unlisted for e in events):
            raise ValidationError(_('At least one event is unlisted.'))

    @validates('event_title_pattern')
    def _check_title_pattern(self, event_title_pattern, **kwargs):
        if not event_title_pattern:
            return
        # XXX: we do not use validate_placeholders here since it's just this one and in
        # addition we do not want to prohibit using `{` literally (in case someone wants
        # to use it in the event title for whatever reason)
        if '{n}' not in event_title_pattern:
            raise ValidationError('Title pattern must contain the {n} placeholder')


class EventDetailsForSeriesManagementSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'category_chain', 'title', 'start_dt', 'end_dt', 'can_manage', 'series_id', 'can_access')

    category_chain = fields.List(fields.String(), attribute='category.chain_titles')
    can_manage = fields.Function(lambda event: event.can_manage(session.user))
    can_access = fields.Function(lambda event: event.can_access(session.user))


class SeriesManagementSearchResultsSchema(mm.Schema):
    events = fields.List(fields.Nested(EventDetailsForSeriesManagementSchema))
    has_more = fields.Bool()
