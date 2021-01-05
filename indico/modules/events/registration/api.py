# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core import signals
from indico.modules.events.controllers.base import RHProtectedEventBase
from indico.modules.events.models.events import Event
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.util import build_registration_api_data, build_registrations_api_data
from indico.modules.oauth import oauth
from indico.web.rh import RH


class RHAPIRegistrant(RH):
    """RESTful registrant API."""

    CSRF_ENABLED = False

    @oauth.require_oauth('registrants')
    def _check_access(self):
        if not self.event.can_manage(request.oauth.user, permission='registration'):
            raise Forbidden()

    def _process_args(self):
        self.event = Event.find(id=request.view_args['event_id'], is_deleted=False).first_or_404()
        self._registration = (self.event.registrations
                              .filter_by(id=request.view_args['registrant_id'],
                                         is_deleted=False)
                              .options(joinedload('data').joinedload('field_data'))
                              .first_or_404())

    def _process_GET(self):
        return jsonify(build_registration_api_data(self._registration))

    def _process_PATCH(self):
        if request.json is None:
            raise BadRequest('Expected JSON payload')

        invalid_fields = request.json.viewkeys() - {'checked_in'}
        if invalid_fields:
            raise BadRequest("Invalid fields: {}".format(', '.join(invalid_fields)))

        if 'checked_in' in request.json:
            if self._registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
                raise BadRequest('This registration cannot be marked as checked-in')
            self._registration.checked_in = bool(request.json['checked_in'])
            signals.event.registration_checkin_updated.send(self._registration)

        return jsonify(build_registration_api_data(self._registration))


class RHAPIRegistrants(RH):
    """RESTful registrants API."""

    @oauth.require_oauth('registrants')
    def _check_access(self):
        if not self.event.can_manage(request.oauth.user, permission='registration'):
            raise Forbidden()

    def _process_args(self):
        self.event = Event.find(id=request.view_args['event_id'], is_deleted=False).first_or_404()

    def _process_GET(self):
        return jsonify(registrants=build_registrations_api_data(self.event))


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)
