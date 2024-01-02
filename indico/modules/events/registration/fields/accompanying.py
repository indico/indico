# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

from marshmallow import ValidationError, fields, post_load, pre_load, validate

from indico.core import signals
from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import RegistrationFormBillableField
from indico.modules.users.models.users import PersonMixin
from indico.util.i18n import _
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


class AccompanyingPersonsField(RegistrationFormBillableField):
    name = 'accompanying_persons'
    mm_field_class = fields.List
    mm_field_args = (fields.Nested(AccompanyingPersonSchema),)
    setup_schema_fields = {
        'max_persons': fields.Integer(load_default=0, validate=validate.Range(0)),
        'persons_count_against_limit': fields.Bool(load_default=False),
    }

    @property
    def default_value(self):
        return []

    @property
    def view_data(self):
        return dict(super().view_data, available_places=self.get_available_places(None))

    def get_validators(self, existing_registration):
        def _check_number_of_places(new_data):
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if old_data and len(new_data) <= len(old_data.data):
                    return
            if (new_data
                    and (available_places := self._get_field_available_places(existing_registration)) is not None
                    and len(new_data) > available_places):
                raise ValidationError(_('There are no places left for this option.'))
        return _check_number_of_places

    def get_available_places(self, registration):
        count = self.form_item.registration_form.registration_limit
        if not count or not self.form_item.data.get('persons_count_against_limit'):
            return None
        count -= self.form_item.registration_form.active_registration_count + 1
        if registration:
            count += registration.occupied_slots
        return max(count, 0)

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0) * len(reg_data)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        reg_data = registration_data.data
        if not reg_data:
            return ''
        return '; '.join(AccompanyingPerson(entry).display_full_name for entry in reg_data)

    def _get_field_available_places(self, registration):
        max_persons = self.form_item.data.get('max_persons') or None
        regform_available_places = self.get_available_places(registration)
        if regform_available_places is None:
            return max_persons
        if max_persons is None:
            return regform_available_places
        return min(max_persons, regform_available_places)
