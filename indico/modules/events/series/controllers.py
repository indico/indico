# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.models.series import EventSeries
from indico.modules.events.schemas import EventDetailsSchema
from indico.modules.events.series.schemas import EventSeriesUpdateSchema
from indico.util.i18n import _
from indico.web.args import use_rh_args
from indico.web.rh import RH


class RHEventSeries(RH):
    def _process_args(self):
        self.series = EventSeries.get(request.view_args['series_id']) if 'series_id' in request.view_args else None

    def _process_GET(self):
        if self.series is None:
            raise NotFound(_('A series with this ID does not exist.'))
        return jsonify({'events': [EventDetailsSchema().dump(e) for e in self.series.events],
                        'show_sequence_in_title': self.series.show_sequence_in_title,
                        'show_links': self.series.show_links})

    @use_rh_args(EventSeriesUpdateSchema)
    def _process_PATCH(self, changes):
        if self.series is None:
            raise NotFound(_('A series with this ID does not exist.'))
        self.series.populate_from_dict(changes)

        db.session.commit()
        return '', 204

    @use_rh_args(EventSeriesUpdateSchema, partial=True)
    def _process_POST(self, data):
        # TODO: show_sequence_in_title, show_links??
        series = EventSeries()
        series.populate_from_dict(data)
        db.session.commit()
        return '', 204

    def _process_DELETE(self):
        if self.series is None:
            raise NotFound(_('A series with this ID does not exist.'))
        for event in self.series.events:
            event.series_id = None
        db.session.commit()
        return '', 204
