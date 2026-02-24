# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.core.errors import NoReportError
from indico.modules.events.models.events import Event
from indico.modules.events.models.series import EventSeries
from indico.modules.events.series.schemas import EventSeriesSchema, EventSeriesUpdateSchema
from indico.util.i18n import _
from indico.util.marshmallow import ModelField
from indico.web.args import use_kwargs, use_rh_args
from indico.web.rh import RHProtected


class RHEventSeries(RHProtected):
    @use_kwargs({
        'series': ModelField(EventSeries, load_default=None, data_key='series_id')
    }, location='view_args')
    def _process_args(self, series):
        self.series = series

    def _check_access(self):
        RHProtected._check_access(self)
        if self.series and not self.series.can_manage(session.user):
            raise NoReportError.wrap_exc(Forbidden(_('You can only manage a series if you can manage all its events.')))
        # XXX for POST the check for event management access is done in EventSeriesUpdateSchema

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
        Event.query.filter_by(series_id=self.series.id, is_deleted=True).update({Event.series_id: None})
        db.session.delete(self.series)
        return '', 204
