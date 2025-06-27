# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from flask import json, request
from sqlalchemy.orm import contains_eager, defaultload

from indico.core import signals
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.registration.controllers import RegistrationFormMixin
from indico.modules.events.registration.lists import RegistrationListGenerator
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration


class RHManageRegFormsBase(RHManageEventBase):
    """Base class for all registration management RHs."""

    PERMISSION = 'registration'


class RHManageRegFormBase(RegistrationFormMixin, RHManageRegFormsBase):
    """Base class for a specific registration form."""

    def _process_args(self):
        RHManageRegFormsBase._process_args(self)
        RegistrationFormMixin._process_args(self)
        self.list_generator = RegistrationListGenerator(regform=self.regform)


class RHManageRegistrationBase(RHManageRegFormBase):
    """Base class for a specific registration."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.registration = (Registration.query
                             .filter(Registration.id == request.view_args['registration_id'],
                                     ~Registration.is_deleted,
                                     ~RegistrationForm.is_deleted)
                             .join(Registration.registration_form)
                             .options(contains_eager(Registration.registration_form)
                                      .defaultload('form_items')
                                      .joinedload('children'))
                             .options(defaultload(Registration.data)
                                      .joinedload('field_data'))
                             .one())


class RHManageRegistrationFieldActionBase(RHManageRegFormBase):
    """Base class for a specific registration field."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.field
        },
        'skipped_args': {'section_id'}
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.field = (RegistrationFormField.query
                      .filter(RegistrationFormField.id == request.view_args['field_id'],
                              RegistrationFormField.registration_form == self.regform,
                              RegistrationFormField.is_enabled,
                              ~RegistrationFormField.is_deleted)
                      .one())


# TODO The signals added here are for testing purposes and will be removed
@signals.event.registration.generate_ticket_qr_code.connect
def _inject_custom_qr_code_data(registration, person, ticket_data):
    ticket_data.clear()
    return {
        'r': str(registration.id),
        'f': str(registration.registration_form_id),
    }


QR_CODE_NAME = 'Example'


@signals.event.registration.generate_regform_ticket_config_qr_code.connect
def _inject_pattern_for_ticket_qr_code_config(regform, **kwargs):
    qr_data = kwargs.get('qr_data', {})
    qr_data.update({
        'regex': {
            'pattern': '^\\{("r":"\\d+","f":"\\d+"|"f":"\\d+","r":"\\d+")\\}$',
            'name': QR_CODE_NAME
        }
    })


@signals.event.registration.handle_custom_ticket_qr_code.connect
def _handle_custom_ticket_qr_code_data(qr_code_data, qr_code_name):
    if qr_code_name != QR_CODE_NAME:
        return None
    json_qr_code_pattern = re.compile(r'^\{("r":"\d+","f":"\d+"|"f":"\d+","r":"\d+")\}$')
    if json_qr_code_pattern.match(qr_code_data):
        try:
            qr_code_data = json.loads(qr_code_data)
            if reg := Registration.query.filter_by(id=qr_code_data['r'], registration_form_id=qr_code_data['f'],
                                                   is_deleted=False).first():
                return reg
        except ValueError:
            return None
    return None
