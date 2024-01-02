# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.events import Event
from indico.modules.events.persons.util import check_person_link_email
from indico.modules.events.util import get_object_from_args
from indico.util.marshmallow import LowercaseString, ModelField
from indico.web.args import use_kwargs
from indico.web.rh import RH, RHProtected


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


class RHEventCheckEmail(RHProtected):
    """Check a person's email when editing a person link.

    Access to this endpoint is restricted to those users who can manage the person link's
    parent object i.e. event, session block, abstract & {sub}contribution.
    """

    def _process_args(self):
        self.object_type, self.event, self.object = get_object_from_args()
        if self.object is None:
            raise NotFound

    def _check_access(self):
        obj = self.object.session if self.object_type == 'session_block' else self.object
        # Depending on the settings, contribution submitters may be able to edit
        # speakers/authors without having management rights
        method = obj.can_edit if self.object_type in ('contribution', 'subcontribution', 'abstract') else obj.can_manage
        if not method(session.user):
            raise Forbidden

    @use_kwargs({
        'email': LowercaseString(required=True),
    }, location='query')
    def _process(self, email):
        return jsonify(check_person_link_email(self.event, email))
