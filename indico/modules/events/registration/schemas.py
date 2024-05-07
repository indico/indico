# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import itemgetter

from marshmallow.decorators import post_dump
from marshmallow.fields import String
from webargs import fields

from indico.core.marshmallow import mm
from indico.modules.events import Event
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.events.registration.util import get_flat_section_submission_data, get_form_registration_data
from indico.util.string import natural_sort_key


class RegistrationFormPrincipalSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'name', 'identifier')

    name = String(attribute='title')
    identifier = String()


class RegistrationTagSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationTag
        fields = ('id', 'title', 'color')

    @post_dump(pass_many=True)
    def sort_list(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda tag: natural_sort_key(tag['title']))
        return data


class CheckinEventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start_dt', 'end_dt')


class CheckinRegFormSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'event_id', 'title', 'introduction', 'start_dt', 'end_dt',
                  'is_open', 'registration_count', 'checked_in_count')

    is_open = fields.Bool()
    registration_count = fields.Int(attribute='existing_registrations_count')
    checked_in_count = fields.Int(attribute='checked_in_registrations_count')


class CheckinRegistrationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Registration
        fields = ('id', 'regform_id', 'event_id', 'full_name', 'email', 'state', 'checked_in', 'checked_in_dt',
                  'checkin_secret', 'is_paid', 'price', 'payment_date', 'currency', 'formatted_price', 'tags',
                  'occupied_slots', 'registration_date', 'registration_data')

    regform_id = fields.Int(attribute='registration_form_id')
    full_name = fields.Str(attribute='display_full_name')
    state = fields.Enum(RegistrationState)
    checkin_secret = fields.UUID(attribute='ticket_uuid')
    payment_date = fields.Method('_get_payment_date')
    formatted_price = fields.Function(lambda reg: reg.render_price())
    tags = fields.Function(lambda reg: sorted(t.title for t in reg.tags))
    registration_date = fields.DateTime(attribute='submitted_dt')
    registration_data = fields.Method('_get_registration_data')

    def _get_payment_date(self, registration):
        if registration.is_paid and (transaction := registration.transaction):
            return fields.DateTime().serialize('timestamp', transaction)
        return None

    def _get_filenames(self, registration):
        """Extract filenames from file fields."""
        return {r.field_data.field.id: r.filename
                for r in registration.data
                if r.field_data.field.field_impl.is_file_field and r.storage_file_id is not None}

    def _get_registration_data(self, registration):
        regform = registration.registration_form
        form_data = get_flat_section_submission_data(regform, registration=registration, management=True)
        reg_data = get_form_registration_data(regform, registration, management=True)
        filenames = self._get_filenames(registration)
        sections = sorted(form_data['sections'].values(), key=itemgetter('position'))
        fields = sorted(form_data['items'].values(), key=itemgetter('position'))
        data = {}

        for section in sections:
            data[section['id']] = {
                'id': section['id'],
                'position': section['position'],
                'title': section['title'],
                'description': section['description'],
                'fields': []
            }

        for field in fields:
            if field['inputType'] == 'label':
                # Do not include labels in the response
                continue

            section = data[field['sectionId']]
            field_data = {
                'id': field['id'],
                'position': field['position'],
                'title': field['title'],
                'description': field['description'],
                'input_type': field['inputType'],
                'data': reg_data[field['htmlName']],
                'default_value': field['defaultValue'],
            }
            if 'price' in field:
                field_data['price'] = field['price']
            if 'choices' in field:
                field_data['choices'] = field['choices']
            # File field stores the uuid as data which is not helpful.
            # We want to show the filename instead.
            if field['id'] in filenames:
                field_data['data'] = filenames[field['id']]
            section['fields'].append(field_data)

        return list(data.values())
