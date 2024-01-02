# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.models.series import EventSeries
from indico.modules.events.series.schemas import EventSeriesSchema, EventSeriesUpdateSchema
from indico.util.i18n import _
from indico.web.args import use_rh_args
from indico.web.rh import RH


class RHEventSeries(RH):
    def _process_args(self):
        self.series = None
        if 'series_id' in request.view_args:
            self.series = EventSeries.get(request.view_args['series_id'])
            if self.series is None:
                raise NotFound(_('A series with this ID does not exist.'))

    def _process_GET(self):
        return EventSeriesSchema().dump(self.series)

    @use_rh_args(EventSeriesUpdateSchema, partial=True)
    def _process_PATCH(self, changes):
        self.series.populate_from_dict(changes)
        return '', 204

    @use_rh_args(EventSeriesUpdateSchema)
    def _process_POST(self, data):
        series = EventSeries()
        series.populate_from_dict(data)
        return '', 204

    def _process_DELETE(self):
        db.session.delete(self.series)
        return '', 204
