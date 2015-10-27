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
from sqlalchemy.orm import load_only, joinedload
from wtforms import ValidationError

from indico.modules.events.models.events import Event
from indico.modules.events.registration import logger
from indico.modules.events.registration.fields.simple import (ChoiceBaseField, AccommodationField,
                                                              get_field_merged_options)
from indico.modules.events.registration.models.form_fields import (RegistrationFormPersonalDataField,
                                                                   RegistrationFormFieldData)
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import RegistrationInvitation, InvitationState
from indico.modules.events.registration.models.items import (RegistrationFormPersonalDataSection,
                                                             RegistrationFormItemType, PersonalDataType)
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState
from indico.modules.events.registration.notifications import (notify_registration_creation,
                                                              notify_registration_modification)
from indico.modules.fulltextindexes.models.events import IndexedEvent
from indico.modules.users.util import get_user_by_email
from indico.web.forms.base import IndicoForm
from indico.core.db import db
from indico.util.date_time import format_datetime, format_date


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
                      ~RegistrationForm.is_deleted,
                      Registration.is_active)
                .join(Registration.registration_form)
                .count())


def get_event_section_data(regform, management=False, registration=None):
    data = []
    if not registration:
        return [s.view_data for s in regform.sections if not s.is_deleted and (management or not s.is_manager_only)]

    registration_data = {r.field_data.field.id: r for r in registration.data}
    for section in regform.sections:
        if section.is_deleted or (not management and section.is_manager_only):
            continue

        section_data = section.own_data
        section_data['items'] = []

        for child in section.fields:
            if child.is_deleted:
                continue
            if isinstance(child.field_impl, ChoiceBaseField) or isinstance(child.field_impl, AccommodationField):
                field_data = get_field_merged_options(child, registration_data)
            else:
                field_data = child.view_data
            section_data['items'].append(field_data)
        data.append(section_data)
    return data


def check_registration_email(regform, email, registration=None, management=False):
    """Checks whether an email address is suitable for registration.

    :param regform: The registration form
    :param email: The email address
    :param registration: The existing registration (in case of
                         modification)
    :param management: If it's a manager adding a new registration
    """
    email = email.lower().strip()
    user = get_user_by_email(email)
    email_registration = regform.get_registration(email=email)
    user_registration = regform.get_registration(user=user) if user else None
    if registration is not None:
        if email_registration and email_registration != registration:
            return dict(status='error', conflict='email-already-registered')
        elif user_registration and user_registration != registration:
            return dict(status='error', conflict='user-already-registered')
        elif user and registration.user and registration.user != user:
            return dict(status='warning' if management else 'error', conflict='email-other-user', user=user.full_name)
        elif not user and registration.user:
            return dict(status='warning' if management else 'error', conflict='email-no-user',
                        user=registration.user.full_name)
        elif user:
            return dict(status='ok', user=user.full_name, self=(not management and user == session.user),
                        same=(user == registration.user))
        elif regform.require_user and (management or email != registration.email):
            return dict(status='warning' if management else 'error', conflict='no-user')
        else:
            return dict(status='ok', user=None)
    else:
        if email_registration:
            return dict(status='error', conflict='email-already-registered')
        elif user_registration:
            return dict(status='error', conflict='user-already-registered')
        elif user:
            return dict(status='ok', user=user.full_name, self=(not management and user == session.user), same=False)
        elif regform.require_user:
            return dict(status='warning' if management else 'error', conflict='no-user')
        else:
            return dict(status='ok', user=None)


def make_registration_form(regform, management=False, registration=None):
    """Creates a WTForm based on registration form fields"""

    class RegistrationFormWTF(IndicoForm):
        def validate_email(self, field):
            status = check_registration_email(regform, field.data, registration, management=management)
            if status['status'] == 'error':
                raise ValidationError('Email validation failed: ' + status['conflict'])

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
            data_entry = RegistrationData()
            registration.data.append(data_entry)
            for attr, value in form_item.field_impl.process_form_data(registration, value).iteritems():
                setattr(data_entry, attr, value)
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
    db.session.flush()
    notify_registration_creation(registration)
    logger.info('New registration %s by %s', registration, session.user)
    return registration


def modify_registration(registration, data, management=False):
    with db.session.no_autoflush:
        regform = registration.registration_form
        data_by_field = registration.data_by_field
        if management or not registration.user:
            registration.user = get_user_by_email(data['email'])

        for form_item in regform.active_fields:
            if form_item.parent.is_manager_only and not management:
                with db.session.no_autoflush:
                    value = form_item.field_impl.default_value
            else:
                value = data.get(form_item.html_field_name)

            if form_item.id not in data_by_field:
                data_by_field[form_item.id] = RegistrationData(registration=registration,
                                                               field_data=form_item.current_data)

            attrs = form_item.field_impl.process_form_data(registration, value, data_by_field[form_item.id])

            for key, val in attrs.iteritems():
                setattr(data_by_field[form_item.id], key, val)
            if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
                setattr(registration, form_item.personal_data_type.column, value)
        registration.update_state()
    db.session.flush()
    notify_registration_modification(registration)
    logger.info('Registration {} modified by {}', registration, session.user)


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
    for item in regform_items:
        field_names.add('{}_{}'.format(item.title.encode('utf-8'), item.id))
        if item.input_type == 'accommodation':
            field_names.add('{}_{}_{}'.format(item.title.encode('utf-8'), 'Arrival', item.id))
            field_names.add('{}_{}_{}'.format(item.title.encode('utf-8'), 'Departure', item.id))
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
            if item.input_type == 'accommodation':
                key = '{}_{}'.format(item.title.encode('utf-8'), item.id)
                registration_dict[key] = _prepare_data(data[item.id].friendly_data['choice'] if item.id in data else '')
                key = '{}_{}_{}'.format(item.title.encode('utf-8'), 'Arrival', item.id)
                registration_dict[key] = _prepare_data(format_date(data[item.id].friendly_data['arrival_date'])
                                                       if item.id in data else '')
                key = '{}_{}_{}'.format(item.title.encode('utf-8'), 'Departure', item.id)
                registration_dict[key] = _prepare_data(format_date(data[item.id].friendly_data['departure_date'])
                                                       if item.id in data else '')
            else:
                key = '{}_{}'.format(item.title.encode('utf-8'), item.id)
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


def get_events_registered(user, from_dt=None, to_dt=None):
    """Gets the IDs of events where the user is registered.

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    :return: A set of event ids
    """
    event_date_filter = True
    if from_dt and to_dt:
        event_date_filter = IndexedEvent.start_date.between(from_dt, to_dt)
    elif from_dt:
        event_date_filter = IndexedEvent.start_date >= from_dt
    elif to_dt:
        event_date_filter = IndexedEvent.start_date <= to_dt
    query = (user.registrations
             .options(load_only('event_id'))
             .options(joinedload(Registration.registration_form).load_only('event_id'))
             .join(Registration.registration_form)
             .join(RegistrationForm.event_new)
             .join(IndexedEvent, IndexedEvent.id == Registration.event_id)
             .filter(Registration.is_active, ~RegistrationForm.is_deleted, ~Event.is_deleted)
             .filter(event_date_filter))
    return {registration.event_id for registration in query}
