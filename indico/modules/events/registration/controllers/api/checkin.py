# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

from flask import jsonify, request
from sqlalchemy.orm import joinedload, selectinload, undefer
from webargs import fields
from werkzeug.exceptions import BadRequest, NotFound

from indico.core import signals
from indico.core.config import config
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.payment.util import toggle_registration_payment
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormItem
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.schemas import (CheckinEventSchema, CheckinRegFormSchema,
                                                        CheckinRegistrationSchema)
from indico.modules.events.registration.util import _base64_encode_uuid, get_custom_ticket_qr_code_handlers
from indico.util.marshmallow import not_empty
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file
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

    def _process(self):
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .filter(~RegistrationForm.is_deleted)
                    .options(undefer('existing_registrations_count'), undefer('checked_in_registrations_count'))
                    .all())
        return CheckinRegFormSchema(many=True).jsonify(regforms)


class RHCheckinAPIRegFormBase(RHCheckinAPIBase):
    """Base class for Check-in API endpoints for a specific regform."""

    def _process_args(self):
        RHCheckinAPIBase._process_args(self)
        self.regform = (RegistrationForm.query
                        .with_parent(self.event)
                        .filter_by(id=request.view_args['reg_form_id'], is_deleted=False)
                        .first_or_404())


class RHCheckinAPIRegFormDetails(RHCheckinAPIRegFormBase):
    """Get details about a specific registration form."""

    def _process(self):
        return CheckinRegFormSchema().jsonify(self.regform)


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
        return CheckinRegistrationSchema(many=True, exclude=('registration_data',)).jsonify(registrations)


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
        return CheckinRegistrationSchema().jsonify(self.registration)

    @use_kwargs({'checked_in': fields.Bool(), 'paid': fields.Bool()})
    def _process_PATCH(self, checked_in=None, paid=None):
        if checked_in is not None:
            self.registration.checked_in = checked_in
            signals.event.registration_checkin_updated.send(self.registration)
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

    def _process_GET(self):
        return CheckinRegistrationSchema().jsonify(self.registration)


class RHCheckinAPIRegistrationCustomQRCode(RHCheckinAPIBase):
    """Get Indico-style ticket details for a specific registration from a custom plugin QR code."""

    @use_kwargs({
        'data': fields.String(required=True, validate=not_empty),
        'qr_name': fields.String(required=True, validate=not_empty),
    }, location='json')
    def _process_args(self, data, qr_name):
        try:
            qr_handler = get_custom_ticket_qr_code_handlers()[qr_name]
        except KeyError:
            raise BadRequest('Unknown code')
        if not (reg := qr_handler.lookup_registration(data)):
            raise NotFound('No registration found')
        self.event = reg.event
        self.registration = reg

    def _process_POST(self):
        url = config.BASE_URL.removeprefix('https://')
        qr_code_version = 2
        result = {
            'i': [qr_code_version, url, _base64_encode_uuid(self.registration.ticket_uuid)]
        }
        return jsonify(result)


class RHCheckinAPIRegistrationPicture(RHCheckinAPIBase):
    """Return the picture from the picture field of the registration form."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.field_data.locator.file
        }
    }

    def _process_args(self):
        RHCheckinAPIBase._process_args(self)
        self.field_data = (RegistrationData.query
                           .filter(RegistrationFormItem.input_type == 'picture',
                                   RegistrationData.registration_id == request.view_args['registration_id'],
                                   RegistrationData.field_data_id == request.view_args['field_data_id'],
                                   RegistrationData.filename.isnot(None))
                           .join(RegistrationData.field_data)
                           .join(RegistrationFormFieldData.field)
                           .options(joinedload('registration').joinedload('registration_form'))
                           .one())

    def _process(self):
        # We cannot use `self.field_data.send()` here because depending on the storage backend
        # the CORS headers would be lost. In case of nginx+xaccelredirect this could be fixed
        # via the nginx config, but when redirecting to a signed S3 URL, this is not possible
        # since S3 only allows setting such headers on the bucket level, but not for individual
        # presigned urls
        with self.field_data.open() as fd:
            data = BytesIO(fd.read())
        return send_file(self.field_data.filename, data, self.field_data.content_type)
