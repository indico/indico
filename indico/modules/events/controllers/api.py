# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session

from indico.modules.events import Event
from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.persons.util import check_person_link_email
from indico.util.marshmallow import LowercaseString, ModelField
from indico.web.args import use_kwargs
from indico.web.rh import RH


class RHSingleEventAPI(RH):
    """Return info about a single event."""

    @use_kwargs({'event': ModelField(Event, none_if_missing=True, required=True, data_key='event_id')},
                location='view_args')
    def _process(self, event):
        from indico.modules.events.series.schemas import EventDetailsForSeriesManagementSchema
        if event is None:
            return jsonify(None)
        elif not event.can_access(session.user):
            return jsonify(can_access=False)
        return EventDetailsForSeriesManagementSchema().jsonify(event)


class RHEventCheckEmail(RHEventBase):
    """Check a person's email when editing a person link."""

    @use_kwargs({
        'email': LowercaseString(required=True),
    }, location='query')
    def _process(self, email):
        return jsonify(check_person_link_email(self.event, email))
