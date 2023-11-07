# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request, session
from sqlalchemy.orm import joinedload, undefer
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core import signals
from indico.modules.events import Event
from indico.modules.events.controllers.base import RHProtectedEventBase
from indico.modules.events.payment.util import toggle_registration_payment
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.modules.events.registration.util import build_registration_api_data, build_registrations_api_data
from indico.web.args import use_kwargs
from indico.web.rh import RH, cors, json_errors, oauth_scope


@json_errors
@cors
@oauth_scope('registrants')
class RHAPICheckinBase(RHProtectedEventBase):
    """Base class for the Check-in API."""


class RHAPIEvent(RHAPICheckinBase):
    """Manage a single event."""

    def _check_access(self):
        RHAPICheckinBase._check_access(self)
        if not self.event.can_manage(session.user, permission='registration'):
            raise Forbidden()

    def _process(self):
        from indico.modules.events.registration.schemas import CheckinEventSchema
        return CheckinEventSchema().jsonify(self.event)


class RHAPIRegForms(RHAPIEvent):
    """Manage registration forms."""

    def _process(self):
        from indico.modules.events.registration.schemas import CheckinRegFormSchema
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .options(undefer('existing_registrations_count'), undefer('checked_in_registrations_count'))
                    .all())
        return CheckinRegFormSchema(many=True).jsonify(regforms)


class RHAPIRegFormBase(RHAPICheckinBase):
    """Base class for registration forms management."""

    def _process_args(self):
        RHAPICheckinBase._process_args(self)
        self.regform = (RegistrationForm.query
                        .with_parent(self.event)
                        .filter_by(id=request.view_args['reg_form_id'])
                        .first_or_404())


class RHAPIRegForm(RHAPIRegFormBase):
    """Manage a single registration form."""

    def _process(self):
        from indico.modules.events.registration.schemas import CheckinRegFormSchema
        return CheckinRegFormSchema().jsonify(self.regform)


class RHAPIRegistrations(RHAPIRegFormBase):
    """Manage registrations."""

    def _process(self):
        from indico.modules.events.registration.schemas import CheckinRegistrationSchema
        registrations = (Registration.query.with_parent(self.regform)
                         .filter(~Registration.is_deleted)
                         .all())
        return CheckinRegistrationSchema(many=True).jsonify(registrations)


class RHAPIRegistration(RHAPIRegFormBase):
    """Manage a single registration."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    def _process_args(self):
        RHAPIRegFormBase._process_args(self)
        registration_id = request.view_args['registration_id']
        self.registration = (Registration.query
                             .with_parent(self.regform)
                             .filter_by(id=registration_id, is_deleted=False)
                             .first_or_404())

    def _process_GET(self):
        from indico.modules.events.registration.schemas import CheckinRegistrationSchema
        return CheckinRegistrationSchema().jsonify(self.registration)

    @use_kwargs({'checked_in': fields.Bool(), 'paid': fields.Bool()})
    def _process_PATCH(self, checked_in=None, paid=None):
        from indico.modules.events.registration.schemas import CheckinRegistrationSchema

        if checked_in is not None:
            self.registration.checked_in = checked_in
            signals.event.registration_checkin_updated.send(self.registration)
        if paid is not None and paid != self.registration.is_paid and self.registration.price:
            toggle_registration_payment(self.registration, paid=paid)
        return CheckinRegistrationSchema().jsonify(self.registration)


@oauth_scope('registrants')
class RHAPIRegistrant(RH):
    """RESTful registrant API.

    This API is deprecated.
    """

    def _check_access(self):
        if not self.event.can_manage(session.user, permission='registration'):
            raise Forbidden()

    def _process_args(self):
        self.event = Event.query.filter_by(id=request.view_args['event_id'], is_deleted=False).first_or_404()
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

        invalid_fields = request.json.keys() - {'checked_in'}
        if invalid_fields:
            raise BadRequest('Invalid fields: {}'.format(', '.join(invalid_fields)))

        if 'checked_in' in request.json:
            if self._registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
                raise BadRequest('This registration cannot be marked as checked-in')
            self._registration.checked_in = bool(request.json['checked_in'])
            signals.event.registration_checkin_updated.send(self._registration)

        return jsonify(build_registration_api_data(self._registration))


@oauth_scope('registrants')
class RHAPIRegistrants(RH):
    """RESTful registrants API.

    This API is deprecated.
    """

    def _check_access(self):
        if not self.event.can_manage(session.user, permission='registration'):
            raise Forbidden()

    def _process_args(self):
        self.event = Event.query.filter_by(id=request.view_args['event_id'], is_deleted=False).first_or_404()

    def _process_GET(self):
        return jsonify(registrants=build_registrations_api_data(self.event))


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)
