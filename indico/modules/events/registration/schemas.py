# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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


# Schemas for the Check-in app API

class CheckinEventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start_dt', 'end_dt')


class CheckinRegFormSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'event_id', 'title', 'introduction', 'start_dt', 'end_dt',
                  'is_open', 'registration_count', 'checked_in_count')

    is_open = fields.Bool(attribute='is_open')
    registration_count = fields.Function(lambda regform: len(regform.registrations))
    checked_in_count = fields.Function(lambda regform: len(regform.checked_in_registrations))


class CheckinRegistrationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Registration
        fields = ('id', 'regform_id', 'event_id', 'full_name', 'email', 'state', 'checked_in', 'checked_in_dt',
                  'checkin_secret', 'tags', 'registration_date', 'registration_data')

    regform_id = fields.Int(attribute='registration_form_id')
    full_name = fields.Str(attribute='display_full_name')
    state = fields.Enum(RegistrationState)
    checkin_secret = fields.UUID(attribute='ticket_uuid')
    tags = fields.Function(lambda reg: sorted(t.title for t in reg.tags))
    registration_date = fields.DateTime(attribute='submitted_dt')
    registration_data = fields.Method('_get_registration_data')

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
        data = {}

        for section_id, section in form_data['sections'].items():
            data[section_id] = {
                'id': section_id,
                'position': section['position'],
                'title': section['title'],
                'description': section['description'],
                'fields': []
            }

        for field_id, field in form_data['items'].items():
            section = data[field['sectionId']]
            field_data = {
                'id': field_id,
                'position': field['position'],
                'title': field['title'],
                'description': field['description'],
                'inputType': field['inputType'],
                'data': reg_data[field['htmlName']],
                'defaultValue': field['defaultValue'],
            }
            if 'price' in field:
                field_data['price'] = field['price']
            if 'choices' in field:
                field_data['choices'] = field['choices']
            # File field stores the uuid as data which is not helpful.
            # We want to show the filename instead.
            if field_id in filenames:
                field_data['data'] = filenames[field_id]
            section['fields'].append(field_data)

        # Sort sections and fields based on 'position'
        data = list(data.values())
        data.sort(key=lambda s: s['position'])
        for sections in data:
            sections['fields'].sort(key=lambda f: f['position'])

        # Remove the 'position' key
        for section in data:
            del section['position']
            for field in section['fields']:
                del field['position']
        return data
