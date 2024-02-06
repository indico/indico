# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from decimal import Decimal

import pytest
from flask import request
from werkzeug.exceptions import UnprocessableEntity

from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.controllers.management.reglists import (RHRegistrationCreate,
                                                                                RHRegistrationEdit,
                                                                                RHRegistrationsBasePrice)
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.util import create_registration


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_registration_edit_override_required(
    db, dummy_regform, app_context, create_user
):
    # Add a section and a required field
    section = RegistrationFormSection(
        registration_form=dummy_regform, title='dummy_section', is_manager_only=False
    )
    db.session.flush()

    boolean_field = RegistrationFormField(parent_id=section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(
        boolean_field, {'input_type': 'bool', 'is_required': True, 'title': 'Yes/No'}
    )

    # Register a new user
    other_user = create_user(1, first_name='first', last_name='last', email='email@example.com')
    data = {
        'email': other_user.email,
        'first_name': other_user.first_name,
        'last_name': other_user.last_name,
    }
    reg = create_registration(dummy_regform, data, invitation=None, management=True, notify_user=False)

    # Attempting to edit the registration without setting the required field works in edit mode
    with app_context.test_request_context(json={}):
        request.view_args = {
            'registration_id': reg.id,
            'reg_form_id': dummy_regform.id,
            'event_id': dummy_regform.event_id,
        }

        rh = RHRegistrationEdit()
        rh._process_args()
        rh._process_POST()


def test_registration_create_override_required(db, dummy_regform, app_context):
    # Add a section and a required field
    section = RegistrationFormSection(
        registration_form=dummy_regform, title='dummy_section', is_manager_only=False
    )

    assert dummy_regform.active_registration_count == 0

    boolean_field = RegistrationFormField(parent_id=section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(
        boolean_field, {'input_type': 'bool', 'is_required': True, 'title': 'Yes/No'}
    )

    # Attempting to create a registration without required fields fails
    jsondata = {'first_name': 'Greater', 'last_name': 'Capybara', 'email': 'indico@getindico.io'}
    url = f'/event/{dummy_regform.event_id}/manage/registration/{dummy_regform.id}/registrations/create'

    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationCreate()
        rh._process_args()

        with pytest.raises(UnprocessableEntity) as excinfo:
            rh._process_POST()

        messages = excinfo.value.data['messages']
        assert len(messages) == 1
        assert messages[boolean_field.html_field_name][0] == 'Missing data for required field.'
        assert dummy_regform.active_registration_count == 0

    # Trying again with override works
    jsondata['override_required'] = True
    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationCreate()
        rh._process_args()
        rh._process_POST()
        assert dummy_regform.active_registration_count == 1


@pytest.mark.parametrize(
    ('base_price_1', 'base_price_2', 'initial_state', 'action', 'new_price', 'apply_complete',
     'expected_price', 'expected_state'),
    (
        (5, 10, RegistrationState.complete, 'remove', None, None, 5, RegistrationState.complete),
        (5, 10, RegistrationState.unpaid, 'remove', None, None, 0, RegistrationState.complete),
        (5, 10, RegistrationState.complete, 'default', None, False, 5, RegistrationState.complete),
        (5, 10, RegistrationState.complete, 'default', None, True, 5, RegistrationState.complete),
        (0, 10, RegistrationState.complete, 'default', None, False, 0, RegistrationState.complete),
        (0, 10, RegistrationState.complete, 'default', None, True, 10, RegistrationState.unpaid),
        (5, 10, RegistrationState.unpaid, 'default', None, False, 10, RegistrationState.unpaid),
        (5, 10, RegistrationState.unpaid, 'default', None, True, 10, RegistrationState.unpaid),
        (0, 10, RegistrationState.unpaid, 'default', None, False, 10, RegistrationState.unpaid),
        (0, 10, RegistrationState.unpaid, 'default', None, True, 10, RegistrationState.unpaid),
        (5, 10, RegistrationState.complete, 'custom', 15, False, 5, RegistrationState.complete),
        (5, 10, RegistrationState.complete, 'custom', 15, True, 5, RegistrationState.complete),
        (0, 10, RegistrationState.complete, 'custom', 15, False, 0, RegistrationState.complete),
        (0, 10, RegistrationState.complete, 'custom', 15, True, 15, RegistrationState.unpaid),
        (5, 10, RegistrationState.unpaid, 'custom', 15, False, 15, RegistrationState.unpaid),
        (5, 10, RegistrationState.unpaid, 'custom', 15, True, 15, RegistrationState.unpaid),
    ),
)
@pytest.mark.usefixtures('smtp')
def test_registration_update_base_price(dummy_regform, dummy_user, app_context, base_price_1, base_price_2,
                                        initial_state, action, new_price, apply_complete, expected_price,
                                        expected_state):
    # Set the base price to the first registration
    dummy_regform.base_price = Decimal(base_price_1)

    # Register a new user
    data = {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name,
    }
    reg = create_registration(dummy_regform, data, invitation=None, management=True, notify_user=False)
    dummy_regform.base_price = Decimal(base_price_2)
    reg.state = initial_state

    # Generate the request data
    form_data = {
        'action': action,
        'registration_id': reg.id,
        'submitted': '',
        'csrf_token': '00000000-0000-0000-0000-000000000000'
    }
    if new_price is not None:
        form_data['base_price'] = new_price
    if apply_complete:
        form_data['apply_complete'] = 'y'
    with app_context.test_request_context(method='POST', data=form_data):
        request.view_args = {
            'reg_form_id': dummy_regform.id,
            'event_id': dummy_regform.event_id,
        }

        rh = RHRegistrationsBasePrice()
        rh._process_args()
        response = rh._process()
        assert response.status_code == 200

    assert reg.base_price == Decimal(expected_price)
    assert reg.state == expected_state
