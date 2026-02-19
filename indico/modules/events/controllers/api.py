# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.config import config
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import AbstractState
from indico.modules.events.persons.util import check_person_link_email
from indico.modules.events.util import get_object_from_args
from indico.util.marshmallow import LowercaseString, ModelField, UUIDString
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

    @use_kwargs({
        'invited_abstract_uuid': UUIDString(load_default=None),
    }, location='query')
    def _check_access(self, invited_abstract_uuid):
        obj = self.object.session if self.object_type == 'session_block' else self.object
        # For invited abstracts we only care about the UUID instead of regular edit permissions, because
        # the person submitting it may be logged in as a user who does not have edit permissions on the invited
        # abstract, but can nonetheless submit it due to the UUID
        if (
            self.object_type != 'abstract'
            or self.object.state != AbstractState.invited
            or self.object.uuid != invited_abstract_uuid
        ):
            # Depending on the settings, contribution submitters may be able to edit
            # speakers/authors without having management rights
            method = (obj.can_edit if self.object_type in ('contribution', 'subcontribution', 'abstract')
                      else obj.can_manage)
            if not method(session.user):
                raise Forbidden
        # Abstract submission is usually open to unknown people, so in case of search restrictions we require
        # at least abstract management access
        if (
            not config.ALLOW_PUBLIC_USER_SEARCH
            and self.object_type == 'abstract'
            and not self.event.can_manage(session.user, permission='abstracts')
        ):
            raise Forbidden('You are not allowed to search users')

    @use_kwargs({
        'email': LowercaseString(required=True),
    }, location='query')
    def _process(self, email):
        return jsonify(check_person_link_email(self.event, email))
