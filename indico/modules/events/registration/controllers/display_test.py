# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import request, session
from marshmallow import fields
from werkzeug.exceptions import Forbidden, UnprocessableEntity

from indico.modules.events.registration.controllers.display import (RHRegistrationDisplayEdit, RHRegistrationForm,
                                                                    RHRegistrationWithdraw)
from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import ModificationMode
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.util import create_registration
from indico.testing.util import extract_emails
from indico.util.date_time import now_utc
from indico.util.marshmallow import UUIDString
from indico.util.string import snakify_keys


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('request_context')
def test_RHRegistrationForm_can_register(db, dummy_regform, dummy_reg, dummy_user, create_user):
    invitation = RegistrationInvitation(registration_form=dummy_regform, email='foo@bar.com', first_name='foo',
                                        last_name='bar', affiliation='test')
    db.session.flush()
    request.view_args = {'reg_form_id': dummy_regform.id, 'event_id': dummy_regform.event_id}
    request.args = {'invitation': invitation.uuid}
    rh = RHRegistrationForm()
    rh._process_args()
    assert rh._can_register()  # invited
    rh.invitation = None
    assert not rh._can_register()  # not open
    dummy_regform.start_dt = now_utc(False)
    assert rh._can_register()
    session.set_session_user(dummy_user)  # registered in dummy_reg
    assert not rh._can_register()
    dummy_reg.state = RegistrationState.rejected
    assert not rh._can_register()  # being rejected does not allow registering again
    dummy_reg.state = RegistrationState.withdrawn
    assert not rh._can_register()  # being withdrawn does not allow registering again
    session.set_session_user(create_user(123, email='user@example.com'))
    assert rh._can_register()
    dummy_regform.registration_limit = 1
    assert rh._can_register()  # withdrawn/rejected do not count against limit
    dummy_reg.state = RegistrationState.complete
    db.session.expire(dummy_regform)
    assert not rh._can_register()  # exceeding limit


@pytest.mark.usefixtures('request_context')
def test_withdraw_registration_rh(smtp, dummy_regform, dummy_reg, dummy_user):
    # Register the user and enable manager notifications
    dummy_regform.start_dt = now_utc(False)
    dummy_regform.organizer_notifications_enabled = True
    dummy_regform.organizer_notification_recipients = ['mgr@example.test']
    session.set_session_user(dummy_user)

    # Set up request
    request.view_args = {
        'reg_form_id': dummy_regform.id,
        'event_id': dummy_regform.event_id,
    }
    rh = RHRegistrationWithdraw()
    rh._process_args()

    # Throw forbidden if no modification allowed
    dummy_regform.modification_mode = ModificationMode.not_allowed
    assert not dummy_reg.can_be_withdrawn
    with pytest.raises(Forbidden):
        rh._check_access()
    dummy_regform.modification_mode = ModificationMode.allowed_always

    # Check if an email is sent, one to the user, one to the manager
    assert not smtp.outbox
    rh._process()
    extract_emails(
        smtp,
        required=True,
        count=1,
        subject=f'[Indico] Registration withdrawn for {dummy_regform.event.title}',
        to=dummy_user.email,
    )
    extract_emails(
        smtp,
        required=True,
        count=1,
        subject='[Indico] Registration withdrawn for {}: {} {}'.format(  # noqa: UP032
            dummy_regform.event.title, dummy_user.first_name, dummy_user.last_name
        ),
        to='mgr@example.test',
    )
    assert not smtp.outbox


def test_display_edit_override_required_rh(dummy_regform, dummy_user, app_context, smtp):
    # Add a section and a required field
    section = RegistrationFormSection(
        registration_form=dummy_regform, title='dummy_section', is_manager_only=False
    )

    assert dummy_regform.active_registration_count == 0
    boolean_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(
        boolean_field, {'input_type': 'bool', 'is_required': True, 'title': 'Yes/No'}
    )

    # Register the user
    dummy_regform.modification_mode = ModificationMode.allowed_always
    data = {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name,
    }
    reg = create_registration(
        dummy_regform, data, invitation=None, management=False, notify_user=False
    )
    assert dummy_regform.active_registration_count == 1

    # We are not a manager, but are attempting to avoid setting the required field. We should get a 422
    jsondata = {'first_name': 'hax0r'}
    url = f'/event/{dummy_regform.event_id}/registrations/{dummy_regform.id}/edit?token={reg.uuid}'
    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationDisplayEdit()
        rh._process_args()
        rh._check_access()

        with pytest.raises(UnprocessableEntity) as excinfo:
            rh._process_POST()

        messages = excinfo.value.data['messages']
        assert messages == {boolean_field.html_field_name: ['Missing data for required field.']}

    # Attempting to set override_required must also fail
    jsondata = {'first_name': 'hax0r', 'override_required': True}
    url = f'/event/{dummy_regform.event_id}/registrations/{dummy_regform.id}/edit?token={reg.uuid}'
    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationDisplayEdit()
        rh._process_args()
        rh._check_access()

        with pytest.raises(UnprocessableEntity) as excinfo:
            rh._process_POST()

        messages = excinfo.value.data['messages']
        assert messages['override_required'] == ['Unknown field.']

    # Try again with the correct fields
    assert not smtp.outbox
    del jsondata['override_required']
    jsondata[boolean_field.html_field_name] = True
    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationDisplayEdit()
        rh._process_args()
        rh._check_access()
        rh._process_POST()

        assert reg.first_name == 'hax0r'
        assert reg.data_by_field[boolean_field.id].data is True

        extract_emails(
            smtp,
            required=True,
            count=1,
            subject=f'[Indico] Registration modified for {dummy_regform.event.title}',
            to=dummy_user.email,
        )


condition_field_params = pytest.mark.parametrize(
    ('input_type', 'input_data', 'false_values', 'true_value', 'condition'), (
    ('bool', {}, [False], True, True),
    ('checkbox', {}, [False], True, True),
    ('single_choice', {'with_extra_slots': False, 'item_type': 'dropdown', 'choices': [
        {'caption': 'Yes', 'id': 'yes', 'is_enabled': True},
        {'caption': 'No', 'id': 'no', 'is_enabled': True},
    ]}, [{}, {'no': 1}, {'yes': 0}], {'yes': 1}, 'yes'),
    ('multi_choice', {'with_extra_slots': False, 'choices': [
        {'caption': 'Yes', 'id': 'yes', 'is_enabled': True},
        {'caption': 'No', 'id': 'no', 'is_enabled': True},
    ]}, [{}, {'no': 1}, {'yes': 0}], {'yes': 1}, 'yes'),
    (
        'accommodation',
        {
            'arrival': {'start_date': '2025-05-01', 'end_date': '2025-05-03'},
            'departure': {'start_date': '2025-05-02', 'end_date': '2025-05-05'},
            'choices': [
                {
                    'caption': 'Nothing',
                    'id': 'noacc',
                    'is_enabled': True,
                    'is_no_accommodation': True,
                },
                {'caption': 'Yes', 'id': 'yes', 'is_enabled': True},
                {'caption': 'No', 'id': 'no', 'is_enabled': True},
            ],
        },
        [
            {'choice': 'noacc', 'isNoAccommodation': True},
            {'choice': 'no', 'isNoAccommodation': False, 'arrivalDate': '2025-05-01', 'departureDate': '2025-05-02'},
        ],
        {'choice': 'yes', 'isNoAccommodation': False, 'arrivalDate': '2025-05-01', 'departureDate': '2025-05-02'},
        'yes',
    ),
))


@condition_field_params
def test_display_register_conditional(db, dummy_regform, dummy_user, app_context, mocker, monkeypatch,
                                      input_type, input_data, false_values, true_value, condition):
    mocker.patch('indico.modules.events.registration.util.notify_registration_creation')
    mocker.patch('indico.modules.events.registration.util.notify_registration_modification')
    monkeypatch.setattr(UUIDString, '_deserialize', fields.String._deserialize)  # for accommodation field
    monkeypatch.setattr(fields.UUID, '_deserialize', fields.String._deserialize)  # for choice fields

    # Extend the dummy_regform with more sections and fields
    section = RegistrationFormSection(registration_form=dummy_regform, title='dummy_section', is_manager_only=False)

    condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(condition_field, {
        'input_type': input_type, 'title': 'Condition trigger',
        **input_data
    })

    db.session.flush()
    text_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(text_field, {
        'input_type': 'text', 'title': 'Cond Text',
        'show_if_field_id': condition_field.id,
        'show_if_field_values': [condition],
    })
    text_field_req = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(text_field_req, {
        'input_type': 'text', 'title': 'Cond Text Required',
        'is_required': True,
        'show_if_field_id': condition_field.id,
        'show_if_field_values': [condition],
    })

    dummy_regform.start_dt = now_utc(False)
    dummy_regform.modification_mode = ModificationMode.allowed_always
    dummy_regform.require_captcha = False
    db.session.flush()
    assert dummy_regform.active_registration_count == 0
    personal_data = {'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}

    def _test_register(data, *, raises):
        url = f'/event/{dummy_regform.event_id}/registrations/{dummy_regform.id}/'
        with app_context.test_request_context(url, json={**personal_data, **data}):
            rh = RHRegistrationForm()
            rh._process_args()
            rh._check_access()
            if raises:
                with pytest.raises(UnprocessableEntity) as excinfo:
                    rh._process_POST()
                return excinfo.value.data['messages']
            else:
                rh._process_POST()
                assert dummy_regform.active_registration_count == 1
                return dummy_regform.registrations[0]

    # Registering fails because the required field is active but has no data
    data = {condition_field.html_field_name: true_value}
    messages = _test_register(data, raises=True)
    assert messages == {text_field_req.html_field_name: ['Missing data for required field.']}

    # Registering fails because the conditional fields are hidden (no value for condition) but have data
    data = {
        text_field.html_field_name: 'foo',
        text_field_req.html_field_name: 'bar',
    }
    messages = _test_register(data, raises=True)
    assert messages == {
        text_field.html_field_name: ['Unknown field.'],
        text_field_req.html_field_name: ['Unknown field.'],
    }

    # Registering fails because the conditional fields are hidden (explicit "wrong" value for condition) but have data
    for val in false_values:
        data = {
            condition_field.html_field_name: val,
            text_field.html_field_name: 'foo',
            text_field_req.html_field_name: 'bar',
        }
        messages = _test_register(data, raises=True)
        assert messages == {
            text_field.html_field_name: ['Unknown field.'],
            text_field_req.html_field_name: ['Unknown field.'],
        }

    # Registering succeeds, conditional field disabled (no value)
    reg = _test_register({}, raises=False)
    default_value = (
        # This is kind of ugly, but less obscure than going through `process_form_data` just for the accommodation field
        {'choice': 'noacc', 'is_no_accommodation': True}
        if input_type == 'accommodation'
        else condition_field.field_impl.ui_default_value
    )
    assert reg.data_by_field[condition_field.id].data == default_value
    assert text_field.id not in reg.data_by_field
    assert text_field_req.id not in reg.data_by_field

    db.session.delete(reg)
    db.session.flush()
    db.session.expire(dummy_regform)
    assert dummy_regform.active_registration_count == 0

    # Registering succeeds, conditional field + required field have values
    data = {
        condition_field.html_field_name: true_value,
        text_field_req.html_field_name: 'foo',
    }
    reg = _test_register(data, raises=False)
    assert reg.data_by_field[condition_field.id].data
    assert reg.data_by_field[text_field.id].data == ''
    assert reg.data_by_field[text_field_req.id].data == 'foo'


@condition_field_params
def test_display_modify_conditional(db, dummy_regform, dummy_user, app_context, mocker, monkeypatch,
                                    input_type, input_data, false_values, true_value, condition):
    mocker.patch('indico.modules.events.registration.util.notify_registration_creation')
    mocker.patch('indico.modules.events.registration.util.notify_registration_modification')
    monkeypatch.setattr(UUIDString, '_deserialize', fields.String._deserialize)  # for accommodation field
    monkeypatch.setattr(fields.UUID, '_deserialize', fields.String._deserialize)  # for choice fields

    # Extend the dummy_regform with more sections and fields
    section = RegistrationFormSection(registration_form=dummy_regform, title='dummy_section', is_manager_only=False)

    condition_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(condition_field, {
        'input_type': input_type, 'title': 'Condition trigger',
        **input_data
    })

    db.session.flush()
    text_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(text_field, {
        'input_type': 'text', 'title': 'Cond Text',
        'show_if_field_id': condition_field.id,
        'show_if_field_values': [condition],
    })
    text_field_req = RegistrationFormField(parent=section, registration_form=dummy_regform)
    _fill_form_field_with_data(text_field_req, {
        'input_type': 'text', 'title': 'Cond Text Required',
        'is_required': True,
        'show_if_field_id': condition_field.id,
        'show_if_field_values': [condition],
    })

    dummy_regform.start_dt = now_utc(False)
    dummy_regform.modification_mode = ModificationMode.allowed_always
    dummy_regform.require_captcha = False
    db.session.flush()
    assert dummy_regform.active_registration_count == 0
    personal_data = {'email': dummy_user.email, 'first_name': dummy_user.first_name, 'last_name': dummy_user.last_name}

    def _test_register(data, *, raises):
        url = f'/event/{dummy_regform.event_id}/registrations/{dummy_regform.id}/'
        with app_context.test_request_context(url, json={**personal_data, **data}):
            rh = RHRegistrationForm()
            rh._process_args()
            rh._check_access()
            if raises:
                with pytest.raises(UnprocessableEntity) as excinfo:
                    rh._process_POST()
                return excinfo.value.data['messages']
            else:
                rh._process_POST()
                assert dummy_regform.active_registration_count == 1
                return dummy_regform.registrations[0]

    def _test_modify(reg, data, *, raises):
        url = f'/event/{dummy_regform.event_id}/registrations/{dummy_regform.id}/edit?token={reg.uuid}'
        with app_context.test_request_context(url, json={**personal_data, **data}):
            rh = RHRegistrationDisplayEdit()
            rh._process_args()
            rh._check_access()
            if raises:
                with pytest.raises(UnprocessableEntity) as excinfo:
                    rh._process_POST()
                return excinfo.value.data['messages']
            else:
                rh._process_POST()

    # Register with value in conditional field
    data = {
        condition_field.html_field_name: true_value,
        text_field_req.html_field_name: 'foo',
    }
    reg = _test_register(data, raises=False)
    assert reg.data_by_field[condition_field.id].data
    assert reg.data_by_field[text_field.id].data == ''
    assert reg.data_by_field[text_field_req.id].data == 'foo'

    # No-op should be fine, existing data kept
    _test_modify(reg, {}, raises=False)
    assert reg.data_by_field[condition_field.id].data
    assert reg.data_by_field[text_field.id].data == ''
    assert reg.data_by_field[text_field_req.id].data == 'foo'

    # Cannot clear required field
    messages = _test_modify(reg, {text_field_req.html_field_name: ''}, raises=True)
    assert messages == {text_field_req.html_field_name: ['This field cannot be empty.']}

    # Condition no longer met -> cannot set data for them
    for val in false_values:
        messages = _test_modify(reg, {condition_field.html_field_name: val, text_field.html_field_name: ''},
                                raises=True)
        assert messages == {text_field.html_field_name: ['Unknown field.']}

    # Condition no longer met -> data for fields removed
    _test_modify(reg, {condition_field.html_field_name: false_values[0]}, raises=False)
    assert reg.data_by_field[condition_field.id].data == snakify_keys(false_values[0])
    assert text_field.id not in reg.data_by_field
    assert text_field_req.id not in reg.data_by_field

    # Cannot enable field w/o providing new value for required one
    messages = _test_modify(reg, {condition_field.html_field_name: true_value}, raises=True)
    assert messages == {text_field_req.html_field_name: ['Missing data for required field.']}

    # Cannot enable field with an empty new new value for required one
    messages = _test_modify(reg, {condition_field.html_field_name: true_value, text_field_req.html_field_name: ''},
                            raises=True)
    assert messages == {text_field_req.html_field_name: ['This field cannot be empty.']}

    # Success when providing required data
    _test_modify(reg, {condition_field.html_field_name: true_value, text_field_req.html_field_name: 'bar'},
                 raises=False)
    assert reg.data_by_field[condition_field.id].data
    assert reg.data_by_field[text_field.id].data == ''
    assert reg.data_by_field[text_field_req.id].data == 'bar'
