# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request, session
from sqlalchemy.orm import joinedload
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core import signals
from indico.modules.events.controllers.base import RHEventBase, RHProtectedEventBase
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.util import build_registration_api_data, build_registrations_api_data
from indico.web.args import use_kwargs
from indico.web.rh import json_errors, oauth_scope


@json_errors
@oauth_scope('registrants')
class RHAPICheckinAppBase(RHEventBase):
    """Base class for the Indico Check-in API."""

    CORS_ENABLED = True


class RHAPIRegistrant(RHAPICheckinAppBase):
    """RESTful registrant API."""

    def _check_access(self):
        if not self.event.can_manage(session.user, permission='registration'):
            raise Forbidden()

    def _process_args(self):
        RHEventBase._process_args(self)
        self._registration = (self.event.registrations
                              .filter_by(id=request.view_args['registrant_id'],
                                         is_deleted=False)
                              .options(joinedload('data').joinedload('field_data'))
                              .first_or_404())

    def _process_GET(self):
        return jsonify(build_registration_api_data(self._registration))

    @use_kwargs({'checked_in': fields.Bool(required=True)})
    def _process_PATCH(self, checked_in):
        if self._registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
            raise BadRequest('This registration cannot be marked as checked-in')
        self._registration.checked_in = checked_in
        signals.event.registration_checkin_updated.send(self._registration)
        return jsonify(build_registration_api_data(self._registration))


class RHAPIRegistrants(RHAPICheckinAppBase):
    """RESTful registrants API."""

    def _check_access(self):
        if not self.event.can_manage(session.user, permission='registration'):
            raise Forbidden()

    def _process_GET(self):
        return jsonify(registrants=build_registrations_api_data(self.event))


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)
