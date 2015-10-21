# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import csv
import re
from io import BytesIO

from flask import current_app, session
from wtforms import ValidationError

from indico.modules.events.registration import logger
from indico.modules.events.registration.models.form_fields import (RegistrationFormPersonalDataField,
                                                                   RegistrationFormFieldData)
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import RegistrationInvitation, InvitationState
from indico.modules.events.registration.models.items import (RegistrationFormPersonalDataSection,
                                                             RegistrationFormItemType, PersonalDataType)
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.modules.events.registration.notifications import notify_registration_creation
from indico.modules.users.util import get_user_by_email
from indico.web.forms.base import IndicoForm
from indico.core.db import db
from indico.util.date_time import format_datetime


def user_registered_in_event(user, event):
    """
    Check whether there is a `Registration` entry for a user in any
    form tied to a particular event.

    :param user: the `User` object
    :param event: the event in question
    """
    return bool(Registration
                .find(Registration.user == user,
                      RegistrationForm.event_id == int(event.id),
                      ~Registration.is_cancelled)
                .join(Registration.registration_form)
                .count())


def get_event_section_data(regform, management=False):
    return [s.view_data for s in regform.sections if not s.is_deleted and (management or not s.is_manager_only)]


def make_registration_form(regform, management=False):
    """Creates a WTForm based on registration form fields"""

    class RegistrationFormWTF(IndicoForm):
        def validate_email(self, field):
            if regform.get_registration(email=field.data):
                raise ValidationError('Email already in use')

    for form_item in regform.active_fields:
        if not management and form_item.parent.is_manager_only:
            continue
        field_impl = form_item.field_impl
        setattr(RegistrationFormWTF, form_item.html_field_name, field_impl.create_wtf_field())
    return RegistrationFormWTF


def create_personal_data_fields(regform):
    """Creates the special section/fields for personal data."""
    section = next((s for s in regform.sections if s.type == RegistrationFormItemType.section_pd), None)
    if section is None:
        section = RegistrationFormPersonalDataSection(registration_form=regform, title='Personal Data')
        missing = set(PersonalDataType)
    else:
        existing = {x.personal_data_type for x in section.children if x.type == RegistrationFormItemType.field_pd}
        missing = set(PersonalDataType) - existing
    for pd_type, data in PersonalDataType.FIELD_DATA:
        if pd_type not in missing:
            continue
        field = RegistrationFormPersonalDataField(registration_form=regform, personal_data_type=pd_type,
                                                  is_required=pd_type.is_required)
        for key, value in data.iteritems():
            setattr(field, key, value)
        field.data, versioned_data = field.field_impl.process_field_data(data.pop('data', {}))
        field.current_data = RegistrationFormFieldData(versioned_data=versioned_data)
        section.children.append(field)


def url_rule_to_angular(endpoint):
    """Converts a flask-style rule to angular style"""
    mapping = {
        'reg_form_id': 'confFormId',
        'section_id': 'sectionId',
        'field_id': 'fieldId',
    }
    rules = list(current_app.url_map.iter_rules(endpoint))
    assert len(rules) == 1
    rule = rules[0]
    assert not rule.defaults
    segments = [':' + mapping.get(data, data) if is_dynamic else data
                for is_dynamic, data in rule._trace]
    return ''.join(segments).split('|', 1)[-1]


def create_registration(regform, data, invitation=None):
    registration = Registration(registration_form=regform, user=get_user_by_email(data['email']),
                                base_price=regform.base_price)
    for form_item in regform.active_fields:
        if form_item.parent.is_manager_only:
            with db.session.no_autoflush:
                value = form_item.field_impl.default_value
        else:
            value = data.get(form_item.html_field_name)
        with db.session.no_autoflush:
            form_item.field_impl.save_data(registration, value)
        if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
            setattr(registration, form_item.personal_data_type.column, value)
    if invitation is None:
        # Associate invitation based on email in case the user did not use the link
        with db.session.no_autoflush:
            invitation = (RegistrationInvitation
                          .find(email=data['email'], registration_id=None)
                          .with_parent(regform)
                          .first())
    if invitation:
        invitation.state = InvitationState.accepted
        invitation.registration = registration
    registration.update_state()
    notify_registration_creation(registration)
    db.session.flush()
    logger.info('New registration %s by %s', registration, session.user)
    return registration


def _prepare_data(data):
    if isinstance(data, list):
        data = ','.join(data)
    elif data is None:
        data = ''
    return re.sub(r'(\r?\n)+', '    ', unicode(data)).encode('utf-8')


def generate_csv_from_registrations(registrations, regform_items, special_items):
    """Generates a CSV file from a given registration list.

    :param registrations: The list of registrations to include in the file
    :param regform_items: The registration form items to be used as columns
    :param special_items: Registration form information as extra columns
    """

    field_names = {'name'}
    field_names |= {'{}_{}'.format(item.title, item.id) for item in regform_items}
    if 'reg_date' in special_items:
        field_names.add('Registration date')
    if 'state' in special_items:
        field_names.add('Registration state')
    if 'price' in special_items:
        field_names.add('Price')
    buf = BytesIO()
    writer = csv.DictWriter(buf, fieldnames=field_names)
    writer.writeheader()
    for registration in registrations:
        data = registration.data_by_field
        registration_dict = {
            'name': "{} {}".format(registration.first_name, registration.last_name).encode('utf-8')
        }
        for item in regform_items:
            key = '{}_{}'.format(item.title, item.id)
            registration_dict[key] = _prepare_data(data[item.id].friendly_data if item.id in data else '')
        if 'reg_date' in special_items:
            registration_dict['Registration date'] = format_datetime(registration.submitted_dt)
        if 'state' in special_items:
            registration_dict['Registration state'] = registration.state.title.encode('utf-8')
        if 'price' in special_items:
            registration_dict['Price'] = registration.price
        writer.writerow(registration_dict)
    buf.seek(0)
    return buf


def get_registrations_with_tickets(user, event):
    return Registration.find(Registration.user == user,
                             Registration.state == RegistrationState.complete,
                             RegistrationForm.event_id == event.id,
                             RegistrationForm.tickets_enabled,
                             RegistrationForm.ticket_on_event_page,
                             ~RegistrationForm.is_deleted,
                             ~Registration.is_deleted,
                             _join=Registration.registration_form).all()
