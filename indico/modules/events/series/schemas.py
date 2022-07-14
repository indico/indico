# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from marshmallow import ValidationError, fields, validates

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event
from indico.modules.events.models.series import EventSeries
from indico.util.i18n import _
from indico.util.marshmallow import ModelList, not_empty


class EventSeriesSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventSeries
        fields = ('id', 'events', 'show_sequence_in_title', 'show_links')

    id = fields.Int(data_key='series_id')


class EventSeriesUpdateSchema(EventSeriesSchema):
    class Meta(EventSeriesSchema.Meta):
        fields = ('events', 'show_sequence_in_title', 'show_links')
        rh_context = ('series',)

    events = ModelList(Event, filter_deleted=True, data_key='event_ids', required=True, validate=not_empty)

    @validates('events')
    def _check_event_ids(self, events, **kwargs):
        series_id = (
            self.context['series'].id if 'series' in self.context and self.context['series'] is not None else None
        )
        if events is None:
            raise ValidationError(_('No event IDs provided.'))
        event_ids = [e.id for e in events]

        if set(event_ids) - {e.id for e in events}:
            raise ValidationError(_('Invalid event IDs provided.'))
        elif series_id is None and [e for e in events if e.series]:
            raise ValidationError(_('At least one event is already in a series.'))
        elif [e for e in events if e.series and e.series_id is not series_id]:
            raise ValidationError(_('At least one event is already in a different series.'))

        for event in events:
            if not event.can_manage(session.user):
                raise ValidationError(_('You are not allowed to manage all of these events.'))


class EventDetailsForSeriesManagementSchema(mm.SQLAlchemyAutoSchema):
    """Please someone just choose a better name for this oh my god."""
    class Meta:
        model = Event
        fields = ('id', 'category_chain', 'title', 'start_dt', 'end_dt', 'can_manage', 'series_id', 'can_access')

    category_chain = fields.List(fields.String(), attribute='category.chain_titles')
    can_manage = fields.Function(lambda event: event.can_manage(session.user))
    can_access = fields.Function(lambda event: event.can_access(session.user))
