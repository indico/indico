# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import base64
import csv
import dataclasses
import itertools
import uuid
from io import BytesIO
from operator import attrgetter

from flask import json, session
from marshmallow import RAISE, ValidationError, fields, validates
from marshmallow_enum import EnumField
from PIL import Image, ImageOps
from qrcode import QRCode, constants
from sqlalchemy import and_, or_
from sqlalchemy.orm import contains_eager, joinedload, load_only, undefer

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.errors import UserValueError
from indico.core.marshmallow import IndicoSchema
from indico.modules.core.captcha import CaptchaField
from indico.modules.events import EventLogRealm
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.payment.models.transactions import TransactionStatus
from indico.modules.events.registration import logger
from indico.modules.events.registration.constants import REGISTRATION_PICTURE_SIZE, REGISTRATION_PICTURE_THUMBNAIL_SIZE
from indico.modules.events.registration.fields.accompanying import AccompanyingPersonsField
from indico.modules.events.registration.fields.choices import (AccommodationField, ChoiceBaseField,
                                                               get_field_merged_options)
from indico.modules.events.registration.models.form_fields import (RegistrationFormFieldData,
                                                                   RegistrationFormPersonalDataField)
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.invitations import InvitationState, RegistrationInvitation
from indico.modules.events.registration.models.items import (PersonalDataType, RegistrationFormItemType,
                                                             RegistrationFormPersonalDataSection)
from indico.modules.events.registration.models.registrations import (Registration, RegistrationData, RegistrationState,
                                                                     RegistrationVisibility)
from indico.modules.events.registration.notifications import (notify_invitation, notify_registration_creation,
                                                              notify_registration_modification)
from indico.modules.logs import LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.users.util import get_user_by_email
from indico.util.countries import get_country_reverse
from indico.util.date_time import format_date, now_utc
from indico.util.i18n import _
from indico.util.signals import make_interceptable, values_from_signal
from indico.util.spreadsheets import csv_text_io_wrapper, unique_col
from indico.util.string import camelize_keys, validate_email, validate_email_verbose


@dataclasses.dataclass
class ActionMenuEntry:
    text: str
    icon_name: str
    # _: dataclasses.KW_ONLY  # TODO uncomment once we require python3.10+; until then consider everything below kw-only
    weight: int = 0
    dialog_title: str = None  # defaults to `text`
    type: str = 'ajax-dialog'  # use 'callback' to call a global JS function or 'href-custom' for a data-href
    params: dict = dataclasses.field(default_factory=dict)
    url: str = ''
    callback: str = ''
    requires_selected: bool = True
    reload_page: bool = False
    hide_if_locked: bool = False
    extra_classes: str = ''


def import_user_records_from_csv(fileobj, columns, delimiter=','):
    """Parse and do basic validation of user data from a CSV file.

    :param fileobj: the CSV file to be read
    :param columns: A list of column names, 'first_name', 'last_name', & 'email' are compulsory.
    :return: A list dictionaries each representing one row,
             the keys of which are given by the column names.
    """
    with csv_text_io_wrapper(fileobj) as ftxt:
        reader = csv.reader(ftxt.read().splitlines(), delimiter=delimiter)
    used_emails = set()
    email_row_map = {}
    user_records = []
    for row_num, row in enumerate(reader, 1):
        values = [value.strip() for value in row]
        if len(columns) != len(values):
            raise UserValueError(_('Row {}: malformed CSV data - please check that the number of columns is correct')
                                 .format(row_num))
        record = dict(zip(columns, values, strict=True))

        if not record['email']:
            raise UserValueError(_('Row {}: missing e-mail address').format(row_num))
        record['email'] = record['email'].lower()

        if not validate_email(record['email']):
            raise UserValueError(_('Row {}: invalid e-mail address').format(row_num))
        if not record['first_name'] or not record['last_name']:
            raise UserValueError(_('Row {}: missing first or last name').format(row_num))
        record['first_name'] = record['first_name'].title()
        record['last_name'] = record['last_name'].title()

        if record['email'] in used_emails:
            raise UserValueError(_('Row {}: email address is not unique').format(row_num))
        if conflict_row_num := email_row_map.get(record['email']):
            raise UserValueError(_('Row {}: email address belongs to the same user as in row {}')
                                 .format(row_num, conflict_row_num))

        used_emails.add(record['email'])
        if user := get_user_by_email(record['email']):
            email_row_map.update((e, row_num) for e in user.all_emails)

        user_records.append(record)
    return user_records


def get_title_uuid(regform, title):
    """Convert a string title to its UUID value.

    If the title does not exist in the title PD field, it will be
    ignored and returned as ``None``.
    """
    if not title:
        return None
    title_field = next((x
                        for x in regform.active_fields
                        if (x.type == RegistrationFormItemType.field_pd and
                            x.personal_data_type == PersonalDataType.title)), None)
    if title_field is None:  # should never happen
        return None
    valid_choices = {x['id'] for x in title_field.current_data.versioned_data['choices']}
    uuid = next((k for k, v in title_field.data['captions'].items() if v == title), None)
    return {uuid: 1} if uuid in valid_choices else None


def get_country_field(regform):
    """Get the country personal-data field of a regform."""
    return next((x
                 for x in regform.active_fields
                 if (x.type == RegistrationFormItemType.field_pd and
                     x.personal_data_type == PersonalDataType.country)), None)


def get_flat_section_setup_data(regform):
    section_data = {s.id: camelize_keys(s.own_data) for s in regform.sections if not s.is_deleted}
    item_data = {f.id: f.view_data for f in regform.form_items
                 if not f.is_section and not f.is_deleted and not f.parent.is_deleted}
    return {'sections': section_data, 'items': item_data}


def get_flat_section_positions_setup_data(regform):
    section_data = {s.id: s.position for s in regform.sections if not s.is_deleted}
    item_data = {f.id: f.position for f in regform.form_items
                 if not f.is_section and not f.is_deleted and not f.parent.is_deleted}
    return {'sections': section_data, 'items': item_data}


@make_interceptable
def get_flat_section_submission_data(regform, *, management=False, registration=None):
    section_data = {s.id: camelize_keys(s.own_data) for s in regform.active_sections
                    if management or not s.is_manager_only}

    item_data = {}
    registration_data = {r.field_data.field.id: r for r in registration.data} if registration else None
    for item in regform.active_fields:
        can_modify = management or not item.parent.is_manager_only
        if not can_modify:
            continue
        if registration and isinstance(item.field_impl, (ChoiceBaseField, AccommodationField)):
            field_data = get_field_merged_options(item, registration_data)
        elif registration and isinstance(item.field_impl, AccompanyingPersonsField):
            field_data = item.view_data
            field_data['availablePlaces'] = item.field_impl.get_available_places(registration)
        else:
            field_data = item.view_data
        field_data['lockedReason'] = item.get_locked_reason(registration)
        item_data[item.id] = field_data
    for item in regform.active_labels:
        if management or not item.parent.is_manager_only:
            item_data[item.id] = item.view_data
    return {'sections': section_data, 'items': item_data}


def get_initial_form_values(regform, *, management=False):
    initial_values = {}
    for item in regform.active_fields:
        can_modify = management or not item.parent.is_manager_only
        if can_modify:
            impl = item.field_impl
            if not impl.is_invalid_field:
                initial_values[item.html_field_name] = camelize_keys(impl.default_value)
    return initial_values


@make_interceptable
def get_user_data(regform, user, invitation=None):
    if user is None:
        user_data = {}
    else:
        user_data = {t.name: getattr(user, t.name, None) for t in PersonalDataType
                     if t.name not in {'title', 'picture'} and getattr(user, t.name, None)}
        if (
            (country_field := get_country_field(regform)) and
            country_field.data.get('use_affiliation_country') and
            user.affiliation_link and
            user.affiliation_link.country_code
        ):
            user_data['country'] = user.affiliation_link.country_code
    if invitation:
        user_data.update((attr, getattr(invitation, attr)) for attr in ('first_name', 'last_name', 'email'))
        if invitation.affiliation:
            user_data['affiliation'] = invitation.affiliation
    title = getattr(user, 'title', None)
    if title_uuid := get_title_uuid(regform, title):
        user_data['title'] = title_uuid

    active_fields = {item.personal_data_type.name for item in regform.active_fields
                     if item.type == RegistrationFormItemType.field_pd}

    return {name: value for name, value in user_data.items() if name in active_fields}


def get_form_registration_data(regform, registration, *, management=False):
    """
    Return a mapping from 'html_field_name' to the registration data.
    This also includes default values for any newly added fields since
    the React frontend requires all initial values to be present.
    """
    data_by_field = registration.data_by_field
    registration_data = {}
    for item in regform.active_fields:
        can_modify = management or not item.parent.is_manager_only
        if not can_modify:
            continue
        elif item.id in data_by_field:
            registration_data[item.html_field_name] = camelize_keys(data_by_field[item.id].user_data)
        else:
            # we never use default values when editing a registration where data does not exist yet.
            # such a field has been added after the registration has been created, and it's rather
            # confusing when you see the default value when editing your own registration, even though
            # you never set that value. and it also breaks things because when you submit the form there
            # is no value sent (since nothing changed and we send partial updates when editing), but the
            # field is required and thus validation fails
            registration_data[item.html_field_name] = item.field_impl.empty_value
    if management:
        registration_data['notify_user'] = session.get('registration_notify_user_default', True)
    return registration_data


def check_registration_email(regform, email, registration=None, management=False):
    """Check whether an email address is suitable for registration.

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
    extra_checks = values_from_signal(
        signals.event.before_check_registration_email.send(
            regform,
            email=email, registration=registration, management=management, user=user,
            user_registration=user_registration, email_registration=email_registration),
        as_list=True)
    if extra_checks:
        return min(extra_checks, key=lambda x: ['error', 'warning', 'ok'].index(x['status']))
    if registration is not None:
        if email_registration and email_registration != registration:
            return {'status': 'error', 'conflict': 'email-already-registered'}
        elif user_registration and user_registration != registration:
            return {'status': 'error', 'conflict': 'user-already-registered'}
        elif user and registration.user and registration.user != user:
            return {'status': 'warning' if management else 'error', 'conflict': 'email-other-user',
                    'user': user.full_name}
        elif not user and registration.user:
            return {'status': 'warning' if management else 'error', 'conflict': 'email-no-user',
                    'user': registration.user.full_name}
        elif user:
            return {'status': 'ok', 'user': user.full_name, 'self': (not management and user == session.user),
                    'same': user == registration.user}
        email_err = validate_email_verbose(email)
        if email_err:
            return {'status': 'error', 'conflict': 'email-invalid', 'email_error': email_err}
        if regform.require_user and (management or email != registration.email):
            return {'status': 'warning' if management else 'error', 'conflict': 'no-user'}
        else:
            return {'status': 'ok', 'user': None}
    else:
        if email_registration:
            return {'status': 'error', 'conflict': 'email-already-registered'}
        elif user_registration:
            return {'status': 'error', 'conflict': 'user-already-registered'}
        elif user:
            return {'status': 'ok', 'user': user.full_name, 'self': not management and user == session.user,
                    'same': False}
        email_err = validate_email_verbose(email)
        if email_err:
            return {'status': 'error', 'conflict': 'email-invalid', 'email_error': email_err}
        if regform.require_user:
            return {'status': 'warning' if management else 'error', 'conflict': 'no-user'}
        else:
            return {'status': 'ok', 'user': None}


class RegistrationSchemaBase(IndicoSchema):
    # note: this schema is kept outside `make_registration_schema` so plugins can use it in
    # subclass checks when using signals such as `schema_post_load`
    class Meta:
        unknown = RAISE


def make_registration_schema(
    regform,
    *,
    management=False,
    override_required=False,
    registration=None,
    captcha_required=False,
):
    """Dynamically create a Marshmallow schema based on the registration form fields.

    :param regform: The registration form
    :param management: True if this registration is with manager privileges
    :param override_required: True if the registration manager requested to override required fields
    :param registration: The existing registration, if it exists
    :param captcha_required: True if a captcha is present on the registration form
    """
    class RegistrationSchema(RegistrationSchemaBase):
        @validates('email')
        def validate_email(self, email, **kwargs):
            status = check_registration_email(regform, email, registration, management=management)
            if status['status'] == 'error':
                raise ValidationError('Email validation failed: ' + status['conflict'])

    schema = {}

    if management:
        schema['notify_user'] = fields.Boolean()
        schema['override_required'] = fields.Boolean()
    elif regform.needs_publish_consent:
        schema['consent_to_publish'] = EnumField(RegistrationVisibility)

    if captcha_required:
        schema['captcha'] = CaptchaField()

    for form_item in regform.active_fields:
        if not management and form_item.parent.is_manager_only:
            continue

        if mm_field := form_item.field_impl.create_mm_field(
            registration=registration,
            override_required=(management and override_required)
        ):
            schema[form_item.html_field_name] = mm_field

    return RegistrationSchema.from_dict(schema, name='RegistrationSchema')


def create_personal_data_fields(regform):
    """Create the special section/fields for personal data."""
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
        for key, value in data.items():
            setattr(field, key, value)
        field.data, versioned_data = field.field_impl.process_field_data(data.pop('data', {}))
        field.current_data = RegistrationFormFieldData(versioned_data=versioned_data)
        section.children.append(field)


@no_autoflush
def create_registration(regform, data, invitation=None, management=False, notify_user=True, skip_moderation=None):
    user = session.user if session else None
    registration = Registration(registration_form=regform, user=get_user_by_email(data['email']),
                                base_price=regform.base_price, currency=regform.currency, created_by_manager=management)
    if skip_moderation is None:
        skip_moderation = management
    for form_item in regform.active_fields:
        if form_item.is_purged or form_item.get_locked_reason(None):
            # Leave the registration data empty
            continue
        default = form_item.field_impl.default_value
        can_modify = management or not form_item.parent.is_manager_only
        value = data.get(form_item.html_field_name, default) if can_modify else default
        data_entry = RegistrationData()
        registration.data.append(data_entry)
        for attr, field_value in form_item.field_impl.process_form_data(registration, value).items():
            setattr(data_entry, attr, field_value)
        if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
            setattr(registration, form_item.personal_data_type.column, value)
    if invitation is None:
        # Associate invitation based on email in case the user did not use the link
        invitation = (RegistrationInvitation.query
                      .filter_by(email=data['email'], registration_id=None)
                      .with_parent(regform)
                      .first())
    if invitation:
        invitation.state = InvitationState.accepted
        invitation.registration = registration
    if not management and regform.needs_publish_consent:
        registration.consent_to_publish = data.get('consent_to_publish', RegistrationVisibility.nobody)
    registration.sync_state(_skip_moderation=skip_moderation)
    db.session.flush()
    signals.event.registration_created.send(registration, management=management, data=data)
    notify_registration_creation(registration, notify_user=notify_user, from_management=management)
    logger.info('New registration %s by %s', registration, user)
    registration.log(EventLogRealm.management if management else EventLogRealm.participants,
                     LogKind.positive, 'Registration',
                     f'New registration: {registration.full_name}', user, data={'Email': registration.email})
    return registration


@no_autoflush
def modify_registration(registration, data, management=False, notify_user=True):
    from indico.modules.events.registration.tasks import delete_previous_registration_file

    old_data = snapshot_registration_data(registration)
    old_price = registration.price
    personal_data_changes = {}
    regform = registration.registration_form
    data_by_field = registration.data_by_field
    if 'email' in data and (management or not registration.user):
        registration.user = get_user_by_email(data['email'])

    billable_items_locked = not management and registration.is_paid
    for form_item in regform.active_fields:
        if form_item.is_purged or form_item.get_locked_reason(registration):
            continue

        field_impl = form_item.field_impl
        has_data = form_item.html_field_name in data
        can_modify = management or not form_item.parent.is_manager_only

        if has_data and can_modify:
            value = data.get(form_item.html_field_name)
        elif not has_data and form_item.id not in data_by_field and not management:
            # set default value for a field if it didn't have one before (including manager-only fields).
            # but we do so only if it's the user editing their registration - if a manager edits
            # the registration, we keep those fields empty so it's clear they have never been
            # filled in.
            value = field_impl.default_value
        else:
            # keep current value
            continue

        if (field_impl.is_file_field and (file_data := data_by_field.get(form_item.id))
                and file_data.storage_file_id is not None):
            delete_previous_registration_file.apply_async([file_data, file_data.storage_backend,
                                                           file_data.storage_file_id], countdown=600)
        if form_item.id not in data_by_field:
            data_by_field[form_item.id] = RegistrationData(registration=registration,
                                                           field_data=form_item.current_data)

        attrs = field_impl.process_form_data(registration, value, data_by_field[form_item.id],
                                             billable_items_locked=billable_items_locked)
        for key, val in attrs.items():
            setattr(data_by_field[form_item.id], key, val)
        if form_item.type == RegistrationFormItemType.field_pd and form_item.personal_data_type.column:
            key = form_item.personal_data_type.column
            if getattr(registration, key) != value:
                personal_data_changes[key] = value
            setattr(registration, key, value)

    if not management and regform.needs_publish_consent:
        consent_to_publish = data.get('consent_to_publish', RegistrationVisibility.nobody)
        update_registration_consent_to_publish(registration, consent_to_publish)

    registration.sync_state()
    db.session.flush()
    # sanity check
    if billable_items_locked and old_price != registration.price:
        raise Exception('There was an error while modifying your registration (price mismatch: %s / %s)',
                        old_price, registration.price)
    if personal_data_changes:
        signals.event.registration_personal_data_modified.send(registration, change=personal_data_changes)
    signals.event.registration_updated.send(registration, management=management, data=data)

    new_data = snapshot_registration_data(registration)
    diff = diff_registration_data(old_data, new_data)
    notify_registration_modification(registration, notify_user=notify_user, diff=diff, old_price=old_price,
                                     from_management=management)
    logger.info('Registration %s modified by %s', registration, session.user)
    registration.log(EventLogRealm.management if management else EventLogRealm.participants,
                     LogKind.change, 'Registration',
                     f'Registration modified: {registration.full_name}',
                     session.user, data={'Email': registration.email})


def update_registration_consent_to_publish(registration, consent_to_publish):
    if registration.consent_to_publish == consent_to_publish:
        return
    changes = make_diff_log({'consent_to_publish': (registration.consent_to_publish, consent_to_publish)},
                            {'consent_to_publish': 'Consent to publish'})
    registration.log(EventLogRealm.participants, LogKind.change, 'Registration',
                     f'Consent to publish modified: {registration.full_name}',
                     session.user, data={'Email': registration.email, 'Changes': changes})
    registration.consent_to_publish = consent_to_publish


def generate_spreadsheet_from_registrations(registrations, regform_items, static_items):
    """Generate a spreadsheet data from a given registration list.

    :param registrations: The list of registrations to include in the file
    :param regform_items: The registration form items to be used as columns
    :param static_items: Registration form information as extra columns
    """
    field_names = ['ID', 'Name']
    special_item_mapping = {
        'reg_date': ('Registration date', lambda x: x.submitted_dt),
        'state': ('Registration state', lambda x: x.state.title),
        'price': ('Price', lambda x: x.render_price()),
        'checked_in': ('Checked in', lambda x: x.checked_in),
        'checked_in_date': ('Check-in date', lambda x: x.checked_in_dt if x.checked_in else ''),
        'payment_date': ('Payment date', lambda x: (x.transaction.timestamp
                                                    if (x.transaction is not None and
                                                        x.transaction.status == TransactionStatus.successful)
                                                    else '')),
        'tags_present': ('Tags', lambda x: [t.title for t in x.tags] if x.tags else ''),
    }
    for item in regform_items:
        field_names.append(unique_col(item.title, item.id))
        if item.input_type == 'accommodation':
            field_names.append(unique_col('{} ({})'.format(item.title, 'Arrival'), item.id))
            field_names.append(unique_col('{} ({})'.format(item.title, 'Departure'), item.id))
    field_names.extend(title for name, (title, fn) in special_item_mapping.items() if name in static_items)
    rows = []
    for registration in registrations:
        data = registration.data_by_field
        registration_dict = {
            'ID': registration.friendly_id,
            'Name': f'{registration.first_name} {registration.last_name}'
        }
        for item in regform_items:
            key = unique_col(item.title, item.id)
            if item.input_type == 'accommodation':
                registration_dict[key] = data[item.id].friendly_data.get('choice') if item.id in data else ''
                key = unique_col('{} ({})'.format(item.title, 'Arrival'), item.id)
                arrival_date = data[item.id].friendly_data.get('arrival_date') if item.id in data else None
                registration_dict[key] = format_date(arrival_date) if arrival_date else ''
                key = unique_col('{} ({})'.format(item.title, 'Departure'), item.id)
                departure_date = data[item.id].friendly_data.get('departure_date') if item.id in data else None
                registration_dict[key] = format_date(departure_date) if departure_date else ''
            else:
                registration_dict[key] = data[item.id].friendly_data if item.id in data else ''
        for name, (title, fn) in special_item_mapping.items():
            if name not in static_items:
                continue
            value = fn(registration)
            registration_dict[title] = value
        rows.append(registration_dict)
    return field_names, rows


def get_registrations_with_tickets(user, event):
    query = (Registration.query.with_parent(event)
             .filter(Registration.user == user,
                     Registration.state == RegistrationState.complete,
                     RegistrationForm.tickets_enabled,
                     RegistrationForm.ticket_on_event_page,
                     ~RegistrationForm.is_deleted,
                     ~Registration.is_deleted)
             .join(Registration.registration_form))

    cached_templates = {}

    def _is_ticket_blocked(registration):
        regform = registration.registration_form
        if regform not in cached_templates:
            cached_templates[regform] = regform.get_ticket_template()
        return cached_templates[regform].is_ticket and registration.is_ticket_blocked

    return [r for r in query if not _is_ticket_blocked(r)]


def get_published_registrations(event, is_participant):
    """Get a list of published registrations for an event.

    :param event: the `Event` to get registrations for
    :param is_participant: whether the user accessing the registrations is a participant of the event
    :return: list of `Registration` objects
    """
    query = (Registration.query.with_parent(event)
             .filter(Registration.is_publishable(is_participant),
                     ~RegistrationForm.is_deleted,
                     ~Registration.is_deleted)
             .join(Registration.registration_form)
             .options(contains_eager(Registration.registration_form))
             .order_by(db.func.lower(Registration.first_name),
                       db.func.lower(Registration.last_name),
                       Registration.friendly_id))

    return query.all()


def count_hidden_registrations(event, is_participant):
    """Get the number of hidden registrations for an event.

    :param event: the `Event` to get registrations for
    :param is_participant: whether the user accessing the registrations is a participant of the event
    :return: number of registrations
    """
    query = (Registration.query.with_parent(event)
             .filter(Registration.is_state_publishable,
                     ~Registration.is_publishable(is_participant),
                     RegistrationForm.is_participant_list_visible(is_participant))
             .join(Registration.registration_form))

    return query.count()


def get_events_registered(user, dt=None):
    """Get the IDs of events where the user is registered.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    :return: A set of event ids
    """
    query = (user.registrations
             .options(load_only('event_id'))
             .options(joinedload(Registration.registration_form).load_only('event_id'))
             .join(Registration.registration_form)
             .join(RegistrationForm.event)
             .filter(Registration.is_active, ~RegistrationForm.is_deleted, ~Event.is_deleted,
                     Event.ends_after(dt)))
    return {registration.event_id for registration in query}


def build_registrations_api_data(event):
    api_data = []
    query = (RegistrationForm.query.with_parent(event)
             .options(joinedload('registrations').joinedload('data').joinedload('field_data')))
    for regform in query:
        for registration in regform.active_registrations:
            registration_info = _build_base_registration_info(registration)
            registration_info['checkin_secret'] = registration.ticket_uuid
            api_data.append(registration_info)
    return api_data


def _build_base_registration_info(registration):
    personal_data = _build_personal_data(registration)
    return {
        'registrant_id': str(registration.id),
        'checked_in': registration.checked_in,
        'checkin_secret': registration.ticket_uuid,
        'full_name': '{} {}'.format(personal_data.get('title', ''), registration.full_name).strip(),
        'personal_data': personal_data,
        'tags': sorted(t.title for t in registration.tags),
    }


def _build_personal_data(registration):
    personal_data = registration.get_personal_data()
    personal_data['firstName'] = personal_data.pop('first_name')
    personal_data['surname'] = personal_data.pop('last_name')
    personal_data['country'] = personal_data.pop('country', '')
    personal_data['country_code'] = get_country_reverse(personal_data['country']) or ''
    personal_data['phone'] = personal_data.pop('phone', '')
    return personal_data


def build_registration_api_data(registration):
    registration_info = _build_base_registration_info(registration)
    registration_info['amount_paid'] = registration.price if registration.is_paid else 0
    registration_info['ticket_price'] = registration.price
    registration_info['registration_date'] = registration.submitted_dt.isoformat()
    registration_info['paid'] = registration.is_paid
    registration_info['checkin_date'] = registration.checked_in_dt.isoformat() if registration.checked_in_dt else ''
    registration_info['event_id'] = registration.event_id
    return registration_info


def get_ticket_qr_code_data(person):
    """Get the data which will be saved in a ticket QR code.

    QR code format:

    {
        'i': [qr_code_version, indico_url, b64(checkin_secret), b64(person_id)],
        # extra keys may be added by plugins (e.g. site access)
    }

    This format tries to be as compact as possible so that the resulting QR codes
    are small and easy to scan. However, we need to stick with a JSON dictionary in
    order to be compatible with the site access plugin which inserts an extra key
    with the ADaMS URL.

    Note that `person_id` is only included if this is a ticket for an accompanying person.

    The checkin secret and person id (if present) is base64-encoded to save space
    (see https://stackoverflow.com/a/53136913/3911147).

    If Indico is running on HTTPS, the scheme ('https://') is stripped from the
    URL to save a few extra bytes.
    """
    registration = person['registration']
    is_accompanying = person['is_accompanying']
    person_id = person['id']
    checkin_secret = person['registration'].ticket_uuid

    qr_code_version = 2  # Increment this if the QR code format changes
    url = config.BASE_URL.removeprefix('https://')

    data = {
        'i': [qr_code_version, url, _base64_encode_uuid(checkin_secret)]
    }
    if is_accompanying:
        data['i'].append(_base64_encode_uuid(person_id))

    sig_rvs = values_from_signal(signals.event.registration.generate_ticket_qr_code.send(registration, person=person,
                                                                                         ticket_data=data),
                                 as_list=True)
    if not sig_rvs:
        return data
    elif len(sig_rvs) == 1:
        return sig_rvs[0]
    else:
        raise RuntimeError('Multiple values returned by `generate_ticket_qr_code` signal')


def _base64_encode_uuid(uid):
    return base64.b64encode(uuid.UUID(uid).bytes).decode('ascii')


def generate_ticket_qr_code(person):
    """Generate an image with a QR code encoding a check-in ticket.

    :param registration: corresponding `Registration` object
    :return: A `BytesIO` containing the image data
    """
    qr = QRCode(
        version=None,
        error_correction=constants.ERROR_CORRECT_M,
        box_size=3,
        border=1
    )
    data = get_ticket_qr_code_data(person)
    qr_data = json.dumps(data, separators=(',', ':')) if not isinstance(data, str) else data
    qr.add_data(qr_data)
    qr.make(fit=True)
    buf = BytesIO()
    qr.make_image().save(buf)
    buf.seek(0)
    return buf


def get_event_regforms(event, user, with_registrations=False, only_in_acl=False):
    """Get registration forms with information about user registrations.

    :param event: the `Event` to get registration forms for
    :param user: A `User`
    :param with_registrations: Whether to return the user's
                               registration instead of just
                               whether they have one
    :param only_in_acl: Whether to include only registration forms
                        that are in the event's ACL
    """
    if not user:
        registered_user = db.literal(None if with_registrations else False)
    elif with_registrations:
        registered_user = Registration
    else:
        registered_user = RegistrationForm.registrations.any((Registration.user == user) & ~Registration.is_deleted)
    query = (RegistrationForm.query.with_parent(event)
             .with_entities(RegistrationForm, registered_user)
             .options(undefer('active_registration_count'))
             .order_by(db.func.lower(RegistrationForm.title)))
    if only_in_acl:
        query = query.filter(RegistrationForm.in_event_acls.any(event=event))
    if with_registrations:
        user_criterion = (Registration.user == user) if user else False
        query = query.outerjoin(Registration, db.and_(Registration.registration_form_id == RegistrationForm.id,
                                                      user_criterion,
                                                      ~Registration.is_deleted))
    return query.all()


def get_event_regforms_registrations(event, user, include_scheduled=True, only_in_acl=False):
    """Get regforms and the associated registrations for an event+user.

    :param event: the `Event` to get registration forms for
    :param user: A `User`
    :param include_scheduled: Whether to include scheduled
                              but not open registration forms
    :param only_in_acl: Whether to include only registration forms
                        that are in the event's ACL
    :return: A tuple, which includes:
            - All registration forms which are scheduled, open or registered.
            - A dict mapping all registration forms to the user's registration if they have one.
    """
    all_regforms = get_event_regforms(event, user, with_registrations=True, only_in_acl=only_in_acl)
    if include_scheduled:
        displayed_regforms = [regform for regform, registration in all_regforms
                              if (regform.is_scheduled and not regform.private) or registration]
    else:
        displayed_regforms = [regform for regform, registration in all_regforms
                              if (regform.is_open and not regform.private) or registration]
    return displayed_regforms, dict(all_regforms)


def generate_ticket(registration):
    from indico.modules.events.registration.badges import RegistrantsListToBadgesPDF, RegistrantsListToBadgesPDFFoldable
    from indico.modules.events.registration.controllers.management.tickets import DEFAULT_TICKET_PRINTING_SETTINGS
    template = registration.registration_form.get_ticket_template()
    registrations = [registration]
    signals.event.designer.print_badge_template.send(template, regform=registration.registration_form,
                                                     registrations=registrations)
    pdf_class = RegistrantsListToBadgesPDFFoldable if template.backside_template else RegistrantsListToBadgesPDF
    pdf = pdf_class(template, DEFAULT_TICKET_PRINTING_SETTINGS, registration.event, registrations,
                    registration.registration_form.tickets_for_accompanying_persons)
    return pdf.get_pdf()


def get_ticket_attachments(registration):
    return [('Ticket.pdf', generate_ticket(registration).getvalue())]


def update_regform_item_positions(regform):
    """Update positions when deleting/disabling an item in order to prevent gaps."""
    section_positions = itertools.count(1)
    disabled_section_positions = itertools.count(1000)
    for section in sorted(regform.sections, key=attrgetter('position')):
        section_active = section.is_enabled and not section.is_deleted
        section.position = next(section_positions if section_active else disabled_section_positions)
        # ensure consistent field ordering
        positions = itertools.count(1)
        disabled_positions = itertools.count(1000)
        for child in section.children:
            child_active = child.is_enabled and not child.is_deleted
            child.position = next(positions if child_active else disabled_positions)


def create_invitation(regform, user, email_from, email_subject, email_body, *, skip_moderation, skip_access_check):
    invitation = RegistrationInvitation(
        email=user['email'],
        first_name=user['first_name'],
        last_name=user['last_name'],
        affiliation=user['affiliation'],
        skip_moderation=skip_moderation,
        skip_access_check=skip_access_check,
    )
    regform.invitations.append(invitation)
    db.session.flush()
    notify_invitation(invitation, email_subject, email_body, email_from)
    return invitation


def import_registrations_from_csv(regform, fileobj, skip_moderation=True, notify_users=False):
    """Import event registrants from a CSV file into a form."""
    columns = ['first_name', 'last_name', 'affiliation', 'position', 'phone', 'email']
    user_records = import_user_records_from_csv(fileobj, columns=columns)

    reg_data = (db.session.query(Registration.user_id, Registration.email)
                .with_parent(regform)
                .filter(Registration.is_active)
                .all())
    registered_user_ids = {rd.user_id for rd in reg_data if rd.user_id is not None}
    registered_emails = {rd.email for rd in reg_data}

    for row_num, record in enumerate(user_records, 1):
        if record['email'] in registered_emails:
            raise UserValueError(_('Row {}: a registration with this email already exists').format(row_num))

        user = get_user_by_email(record['email'])
        if user and user.id in registered_user_ids:
            raise UserValueError(_('Row {}: a registration for this user already exists').format(row_num))

    return [
        create_registration(regform, data, management=True, notify_user=notify_users, skip_moderation=skip_moderation)
        for data in user_records
    ]


def import_invitations_from_csv(regform, fileobj, email_from, email_subject, email_body, *,
                                skip_moderation=True, skip_access_check=True, skip_existing=False, delimiter=','):
    """Import invitations from a CSV file.

    :return: A list of invitations and the number of skipped records which
             is zero if skip_existing=False
    """
    columns = ['first_name', 'last_name', 'affiliation', 'email']
    user_records = import_user_records_from_csv(fileobj, columns=columns, delimiter=delimiter)

    reg_data = (db.session.query(Registration.user_id, Registration.email)
                .with_parent(regform)
                .filter(Registration.is_active)
                .all())
    registered_user_ids = {rd.user_id for rd in reg_data if rd.user_id is not None}
    registered_emails = {rd.email for rd in reg_data}
    invited_emails = {inv.email for inv in regform.invitations}

    filtered_records = []
    for row_num, user in enumerate(user_records, 1):
        if user['email'] in registered_emails:
            if skip_existing:
                continue
            raise UserValueError(_('Row {}: a registration with this email already exists').format(row_num))

        indico_user = get_user_by_email(user['email'])
        if indico_user and indico_user.id in registered_user_ids:
            if skip_existing:
                continue
            raise UserValueError(_('Row {}: a registration for this user already exists').format(row_num))

        if user['email'] in invited_emails:
            if skip_existing:
                continue
            raise UserValueError(_('Row {}: an invitation for this user already exists').format(row_num))

        filtered_records.append(user)

    invitations = [create_invitation(regform, user, email_from, email_subject, email_body,
                                     skip_moderation=skip_moderation, skip_access_check=skip_access_check)
                   for user in filtered_records]
    skipped_records = len(user_records) - len(filtered_records)
    return invitations, skipped_records


def get_registered_event_persons(event):
    """Get all registered EventPersons of an event."""
    query = (event.persons
             .join(Registration, and_(Registration.event_id == EventPerson.event_id,
                                      Registration.is_active,
                                      or_(Registration.user_id == EventPerson.user_id,
                                          Registration.email == EventPerson.email)))
             .join(RegistrationForm, and_(RegistrationForm.id == Registration.registration_form_id,
                                          ~RegistrationForm.is_deleted)))
    return set(query)


def serialize_registration_form(regform):
    """Serialize registration form to JSON-like object."""
    return {
        'id': regform.id,
        'name': regform.title,
        'identifier': f'RegistrationForm:{regform.id}',
        '_type': 'RegistrationForm'
    }


def snapshot_registration_data(registration):
    data = {}
    for regfields in registration.summary_data.values():
        for field, regdata in regfields.items():
            data[field.html_field_name] = {'price': regdata.price, 'data': regdata.data,
                                           'storage_file_id': regdata.storage_file_id,
                                           'is_file_field': field.field_impl.is_file_field,
                                           'friendly_data': regdata.friendly_data}
    return data


def diff_registration_data(old_data, new_data):
    """Compare two sets of registration data.

    :return: A dictionary where the key is the html name of the field and the value is
             the old and new friendly data and the field price
    """
    diff = {}
    for html_field_name in old_data:
        old = old_data[html_field_name]
        new = new_data[html_field_name]
        if old['data'] != new['data'] or (old['is_file_field'] and old['storage_file_id'] != new['storage_file_id']):
            diff[html_field_name] = {
                'old': {'price': old['price'], 'friendly_data': old['friendly_data']},
                'new': {'price': new['price'], 'friendly_data': new['friendly_data']}
            }
    return diff


def close_registration(regform):
    regform.end_dt = now_utc()
    if not regform.has_started:
        regform.start_dt = regform.end_dt


def get_persons(registrations, include_accompanying_persons=False):
    persons = []
    for registration in registrations:
        persons.append({
            'id': registration.id,
            'first_name': registration.first_name,
            'last_name': registration.last_name,
            'registration': registration,
            'is_accompanying': False,
        })
        if include_accompanying_persons:
            persons.extend({'id': person['id'],
                            'first_name': person['firstName'],
                            'last_name': person['lastName'],
                            'registration': registration,
                            'is_accompanying': True} for person in registration.accompanying_persons)
    return persons


def process_registration_picture(source, *, thumbnail=False):
    """Resize the picture to a maximum size and save it as JPEG."""
    max_size = REGISTRATION_PICTURE_THUMBNAIL_SIZE if thumbnail else REGISTRATION_PICTURE_SIZE
    try:
        picture = Image.open(source)
    except (OSError, Image.DecompressionBombError):
        return None
    picture = ImageOps.exif_transpose(picture)
    if picture.mode != 'RGB':
        picture = picture.convert('RGB')
    size_x, size_y = picture.size
    if max(size_x, size_y) > max_size:
        ratio = max_size / max(size_x, size_y)
        picture = picture.resize((int(ratio * size_x), int(ratio * size_y)), Image.Resampling.BICUBIC)
    image_bytes = BytesIO()
    picture.save(image_bytes, 'JPEG')
    image_bytes.seek(0)
    return image_bytes
