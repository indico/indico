# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import ValidationError, fields, validate

from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import RegistrationFormBillableField
from indico.util.i18n import _
from indico.util.marshmallow import not_empty


class AccompanyingPersonSchema(mm.Schema):
    first_name = fields.String(required=True, validate=not_empty)
    last_name = fields.String(required=True, validate=not_empty)


class AccompanyingPersonsField(RegistrationFormBillableField):
    name = 'accompanying_persons'
    mm_field_class = fields.List
    mm_field_args = (fields.Nested(AccompanyingPersonSchema), )
    setup_schema_fields = {
        'max_persons': fields.Integer(load_default=0, validate=validate.Range(0)),
        'persons_count_against_limit': fields.Bool(load_default=False),
    }

    @property
    def default_value(self):
        return []

    @property
    def view_data(self):
        return dict(super().view_data, available_places=self.get_available_places(True))

    def get_validators(self, existing_registration):
        def _check_number_of_places(new_data):
            if existing_registration:
                old_data = existing_registration.data_by_field.get(self.form_item.id)
                if not old_data or not self.has_data_changed(new_data, old_data):
                    return True
            if (new_data
                    and (available_places := self.get_available_places(not existing_registration)) is not None
                    and len(new_data) > available_places):
                raise ValidationError(_('There are no places left for this option.'))
        return _check_number_of_places

    def get_available_places(self, is_new_registration):
        max_persons = self.form_item.data.get('max_persons') or None
        if (self.form_item.data.get('persons_count_against_limit')
                and (reg_limit := self.form_item.registration_form.registration_limit) is not None):
            reg_count = self.form_item.registration_form.active_registration_count
            if is_new_registration:
                reg_count += 1
            if max_persons is None:
                return max(0, reg_limit - reg_count)
            return min(max_persons, max(0, reg_limit - reg_count))
        return max_persons

    def calculate_price(self, reg_data, versioned_data):
        return versioned_data.get('price', 0) * len(reg_data)

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        def _format_person(entry):
            first_name = entry['first_name']
            last_name = entry['last_name']
            return f'{first_name} {last_name}'

        reg_data = registration_data.data
        if not reg_data:
            return ''
        persons = [_format_person(entry) for entry in reg_data]

        return ', '.join(persons) if for_humans or for_search else persons
