# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from decimal import Decimal
from uuid import uuid4

from marshmallow import ValidationError, fields, post_load, pre_load, validate, validates_schema

from indico.core import signals
from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import BillableFieldDataSchema, RegistrationFormBillableField
from indico.modules.users.models.users import PersonMixin
from indico.util.i18n import _, ngettext
from indico.util.marshmallow import not_empty


class AccompanyingPerson(PersonMixin):
    def __init__(self, entry):
        self.first_name = entry['firstName']
        self.last_name = entry['lastName']


class AccompanyingPersonSchema(mm.Schema):
    id = fields.UUID()
    firstName = fields.String(required=True, validate=not_empty)  # noqa: N815
    lastName = fields.String(required=True, validate=not_empty)  # noqa: N815

    @pre_load
    def _generate_new_uuid(self, data, **kwargs):
        old_id = data.get('id', '')
        if old_id.startswith('new:'):
            data['id'] = str(uuid4())
            signals.event.registration.generate_accompanying_person_id.send(self, temporary_id=old_id,
                                                                            permanent_id=data['id'])
        return data

    @post_load
    def _stringify_uuid(self, data, **kwargs):
        if 'id' in data:
            data['id'] = str(data['id'])
        return data


class AccompanyingPersonsFieldDataSchema(BillableFieldDataSchema):
    max_persons = fields.Integer(load_default=0, validate=validate.Range(0))
    persons_count_against_limit = fields.Bool(load_default=False)
    is_anonymous = fields.Bool(load_default=False)

    @validates_schema(skip_on_field_errors=True)
    def _validate_anonymous_mode(self, data, **kwargs):
        field = self.context['field']
        field_impl = field.field_impl
        current_is_anonymous = field_impl.is_anonymous
        has_active_registration_data = field_impl.has_active_registration_data
        is_anonymous = data['is_anonymous']

        if not is_anonymous:
            if current_is_anonymous and has_active_registration_data:
                raise ValidationError(
                    _('Cannot be switched back to named mode when anonymous accompanying persons are registered.'),
                    'is_anonymous',
                )
            return
        if field.registration_form.tickets_for_accompanying_persons:
            raise ValidationError(
                _(
                    'Anonymous accompanying persons cannot be enabled while tickets for '
                    'accompanying persons are enabled.'
                ),
                'is_anonymous',
            )
        if not current_is_anonymous and has_active_registration_data:
            raise ValidationError(
                _('Cannot be enabled when accompanying persons are registered.'),
                'is_anonymous',
            )


class AccompanyingPersonsField(RegistrationFormBillableField):
    name = 'accompanying_persons'
    mm_field_class = fields.List
    mm_field_args = (fields.Nested(AccompanyingPersonSchema),)
    setup_schema_base_cls = AccompanyingPersonsFieldDataSchema

    @property
    def is_anonymous(self):
        return (self.form_item.data or {}).get('is_anonymous', False)

    @property
    def has_active_registration_data(self):
        from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
        from indico.modules.events.registration.models.registrations import Registration, RegistrationData

        if self.form_item.id is None:
            return False
        return (
            db.session.query(RegistrationData)
            .join(RegistrationData.registration)
            .join(RegistrationData.field_data)
            .filter(
                RegistrationFormFieldData.field_id == self.form_item.id,
                Registration.is_active,
            )
            .has_rows()
        )

    @property
    def is_anonymous_locked(self):
        return self.has_active_registration_data

    @property
    def anonymous_lock_reason(self):
        if self.is_anonymous and self.has_active_registration_data:
            return _('Cannot be switched back to named mode when anonymous accompanying persons are registered.')
        if self.has_active_registration_data:
            return _('Cannot be enabled when accompanying persons are registered.')
        return None

    def _get_person_count(self, data):
        if isinstance(data, list):
            return len(data)
        return int(data or 0)

    @staticmethod
    def _format_person_count(count, *, for_humans=False):
        if not for_humans:
            return str(count)
        if not count:
            return ''
        return ngettext('{count} person', '{count} persons', count).format(count=count)

    @property
    def default_value(self):
        return 0 if self.is_anonymous else []

    @property
    def ui_default_value(self):
        return self.default_value

    @property
    def empty_value(self):
        return self.default_value

    @property
    def view_data(self):
        return dict(
            super().view_data,
            available_places=self.get_available_places(None),
            is_anonymous=self.is_anonymous,
            is_anonymous_locked=self.is_anonymous_locked,
            anonymous_lock_reason=self.anonymous_lock_reason,
        )

    def create_mm_field(self, registration=None, override_required=False, management=False):
        if not self.is_anonymous:
            return super().create_mm_field(registration=registration, override_required=override_required,
                                           management=management)

        validators = self.get_validators(registration) or []
        if not isinstance(validators, list):
            validators = [validators]
        validators.append(validate.Range(min=0))
        if self.form_item.is_required and self.not_empty_if_required and not override_required:
            validators.append(not_empty)
        return fields.Integer(
            required=(self.form_item.is_required and not override_required),
            allow_none=override_required,
            validate=validators,
        )

    def get_validators(self, existing_registration):
        def _check_number_of_places(new_data):
            new_count = self._get_person_count(new_data)
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if old_data and new_count <= self._get_person_count(old_data.data):
                    return
            if (
                new_count
                and (available_places := self._get_field_available_places(existing_registration)) is not None
                and new_count > available_places
            ):
                raise ValidationError(_('There are no places left for this option.'))

        return _check_number_of_places

    def get_available_places(self, registration):
        field_data = self.form_item.data or {}
        count = self.form_item.registration_form.registration_limit
        if not count or not field_data.get('persons_count_against_limit'):
            return None
        count -= self.form_item.registration_form.active_registration_count + 1
        if registration:
            count += registration.occupied_slots
        return max(count, 0)

    def calculate_price(self, reg_data, versioned_data):
        if not reg_data:
            # this gets called when getting the old price during an update, but when the field was
            # added after the registration was created, there is no reg data yet.
            return 0
        return Decimal(str(versioned_data.get('price', 0))) * self._get_person_count(reg_data)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        reg_data = registration_data.data
        if self.is_anonymous:
            return self._format_person_count(self._get_person_count(reg_data), for_humans=for_humans and not for_search)
        if not reg_data:
            return ''
        return '; '.join(AccompanyingPerson(entry).display_full_name for entry in reg_data)

    def render_summary_data(self, data):
        return self.get_friendly_data(data, for_humans=True)

    def render_invoice_data(self, data):
        return self.get_friendly_data(data, for_humans=True)

    def render_email_data(self, data):
        return self.get_friendly_data(data, for_humans=True)

    def _get_field_available_places(self, registration):
        max_persons = (self.form_item.data or {}).get('max_persons') or None
        regform_available_places = self.get_available_places(registration)
        if regform_available_places is None:
            return max_persons
        if max_persons is None:
            return regform_available_places
        return min(max_persons, regform_available_places)
