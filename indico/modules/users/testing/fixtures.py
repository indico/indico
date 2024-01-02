# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import patch

import pytest

from indico.modules.events.registration.models.form_fields import RegistrationFormField, RegistrationFormFieldData
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState


@pytest.fixture
def dummy_reg_with_file_field(db, dummy_event, dummy_regform, dummy_user, create_file):
    """Create a dummy registration which includes an uploaded file."""
    from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data

    def create_file_field():
        field_data = {'title': 'File field', 'input_type': 'file'}
        form_field = RegistrationFormField(parent_id=dummy_regform.sections[0].id, registration_form=dummy_regform)

        def field_data_with_reproducible_id(*args, **kwargs):
            return RegistrationFormFieldData(*args, **kwargs, id=730)

        with patch('indico.modules.events.registration.models.form_fields.RegistrationFormFieldData',
                   field_data_with_reproducible_id):
            _fill_form_field_with_data(form_field, field_data)

        db.session.add(form_field)
        db.session.flush()
        return form_field

    def fill_file_field(registration, field, file):
        form_data = field.field_impl.process_form_data(registration, file.uuid)
        file_data = RegistrationData()
        registration.data.append(file_data)
        for attr, value in form_data.items():
            setattr(file_data, attr, value)

    file_field = create_file_field()
    db.session.flush()

    registration = Registration(
        id=730,
        registration_form=dummy_regform,
        user=dummy_user,
        first_name=dummy_user.first_name,
        last_name=dummy_user.last_name,
        email=dummy_user.email,
        state=RegistrationState.complete,
        currency=dummy_regform.currency,
    )

    dummy_file = create_file('registration_upload.txt', 'text/plain', 'registration', 'A dummy file', id=730)
    fill_file_field(registration, file_field, dummy_file)
    dummy_event.registrations.append(registration)
    db.session.flush()
    return registration
