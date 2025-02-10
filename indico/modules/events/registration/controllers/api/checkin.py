# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request
from sqlalchemy.orm import joinedload, selectinload, undefer
from webargs import fields
from werkzeug.exceptions import NotFound, UnprocessableEntity

from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.payment.util import toggle_registration_payment
from indico.modules.events.registration.models.checks import RegistrationCheckType
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.schemas import (CheckinEventSchema, CheckinRegFormSchema,
                                                        CheckinRegistrationSchema)
from indico.modules.events.registration.util import create_registration_check
from indico.web.args import use_kwargs
from indico.web.rh import cors, json_errors, oauth_scope


@json_errors
@cors
@oauth_scope('registrants')
class RHCheckinAPIBase(RHManageEventBase):
    """Base class for the Check-in API."""

    PERMISSION = 'registration'


class RHCheckinAPIEventDetails(RHCheckinAPIBase):
    """Get details about an event."""

    def _process(self):
        return CheckinEventSchema().jsonify(self.event)


class RHCheckinAPIRegForms(RHCheckinAPIBase):
    """Get details about the registrations forms in an event."""

    @use_kwargs({
        'check_type_id': fields.Integer(),
    }, location='query')
    def _process(self, check_type_id=None):
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .filter(~RegistrationForm.is_deleted)
                    .options(undefer('existing_registrations_count'), undefer('checked_in_registrations_count'))
                    .all())
        return CheckinRegFormSchema(many=True, context={'check_type_id': check_type_id}).jsonify(regforms)


class RHCheckinAPIRegFormBase(RHCheckinAPIBase):
    """Base class for Check-in API endpoints for a specific regform."""

    @use_kwargs({
        'check_type_id': fields.Integer(),
    }, location='query')
    def _process_args(self, check_type_id=None):
        RHCheckinAPIBase._process_args(self)
        self.check_type_id = check_type_id
        self.regform = (RegistrationForm.query
                        .with_parent(self.event)
                        .filter_by(id=request.view_args['reg_form_id'], is_deleted=False)
                        .first_or_404())


class RHCheckinAPIRegFormDetails(RHCheckinAPIRegFormBase):
    """Get details about a specific registration form."""

    def _process(self):
        return CheckinRegFormSchema(context={'check_type_id': self.check_type_id}).jsonify(self.regform)


class RHCheckinAPIRegistrations(RHCheckinAPIRegFormBase):
    """Get details about all the registrations in a registration form."""

    def _process(self):
        registrations = (Registration.query.with_parent(self.regform)
                         .filter(~Registration.is_deleted)
                         .options(selectinload('data').joinedload('field_data'),
                                  selectinload('tags'),
                                  joinedload('transaction'),
                                  undefer('occupied_slots'))
                         .all())
        return CheckinRegistrationSchema(many=True, exclude=('registration_data',),
                                         context={'check_type_id': self.check_type_id}).jsonify(registrations)


class RHCheckinAPIRegistration(RHCheckinAPIRegFormBase):
    """Get full details for a specific registration or update it."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    def _process_args(self):
        RHCheckinAPIRegFormBase._process_args(self)
        registration_id = request.view_args['registration_id']
        self.registration = (Registration.query
                             .with_parent(self.regform)
                             .options(selectinload('data').joinedload('field_data'),
                                      selectinload('tags'),
                                      joinedload('transaction'),
                                      undefer('occupied_slots'))
                             .filter_by(id=registration_id, is_deleted=False)
                             .first_or_404())

    def _process_GET(self):
        return CheckinRegistrationSchema(context={'check_type_id': self.check_type_id}).jsonify(self.registration)

    @use_kwargs({
        'checked_in': fields.Bool(),
        'checked_out': fields.Bool(),
        'check_type_id': fields.Integer(),
        'paid': fields.Bool()
    })
    def _process_PATCH(self, checked_in=None, checked_out=None, check_type_id=None, paid=None):
        if check_type_id is not None and (checked_in is not None or checked_out is not None):
            check_type = RegistrationCheckType.get_or_404(check_type_id)
            is_check_out = checked_out is not None
            action = bool(checked_out) if is_check_out else bool(checked_in)
            try:
                if action:
                    create_registration_check(self.registration, check_type=check_type, is_check_out=is_check_out)
                else:
                    self.registration.checks.remove(self.registration.get_last_check_for_type(check_type.id))
            except ValueError as e:
                raise UnprocessableEntity(str(e))
        if paid is not None and paid != self.registration.is_paid and self.registration.price:
            toggle_registration_payment(self.registration, paid=paid)
        return CheckinRegistrationSchema().jsonify(self.registration)


class RHCheckinAPIRegistrationUUID(RHCheckinAPIBase):
    """Get full details for a specific registration from the ticket UUID (checkin secret)."""

    def _process_args(self):
        ticket_uuid = str(request.view_args['ticket_uuid'])
        self.registration = (Registration.query
                             .filter_by(ticket_uuid=ticket_uuid, is_deleted=False)
                             .first_or_404())
        self.regform = self.registration.registration_form
        self.event = self.registration.event
        if self.regform.is_deleted:
            raise NotFound

    @use_kwargs({
        'check_type_id': fields.Integer(),
    }, location='query')
    def _process_GET(self, check_type_id=None):
        return CheckinRegistrationSchema(context={'check_type_id': check_type_id}).jsonify(self.registration)
