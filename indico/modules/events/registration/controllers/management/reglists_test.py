# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from decimal import Decimal

import pytest
from flask import request, session
from werkzeug.exceptions import Forbidden, UnprocessableEntity

from indico.core import signals
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.controllers.management.reglists import (RHRegistrationCreate,
                                                                                RHRegistrationDetails,
                                                                                RHRegistrationEdit,
                                                                                RHRegistrationsApprove,
                                                                                RHRegistrationsBasePrice,
                                                                                RHRegistrationsConfigBadges,
                                                                                RHRegistrationsExportCSV)
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import Registration, RegistrationState
from indico.modules.events.registration.util import create_registration


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_registration_edit_override_required(db, dummy_regform, app_context, create_user):
    # Add a section and a required field
    section = RegistrationFormSection(
        registration_form=dummy_regform, title='dummy_section', is_manager_only=False
    )
    db.session.flush()

    boolean_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
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


def test_registration_create_override_required(dummy_regform, app_context):
    # Add a section and a required field
    section = RegistrationFormSection(
        registration_form=dummy_regform, title='dummy_section', is_manager_only=False
    )

    assert dummy_regform.active_registration_count == 0

    boolean_field = RegistrationFormField(parent=section, registration_form=dummy_regform)
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


@pytest.mark.parametrize(('rh_class', 'method'), (
    (RHRegistrationsApprove, 'POST'),
    (RHRegistrationsExportCSV, 'GET'),
))
def test_bulk_action_filtered_by_registration_list_criteria(db, dummy_regform, dummy_user, app_context, rh_class,
                                                            method):
    dummy_regform.event.update_principal(dummy_user, full_access=True)
    mine, theirs = (create_registration(dummy_regform, {'email': email, 'first_name': 'A', 'last_name': last_name},
                                        invitation=None, management=True, notify_user=False)
                    for email, last_name in (('mine@example.test', 'Mine'), ('theirs@example.test', 'Theirs')))
    db.session.flush()

    def _only_mine(sender, user, **kwargs):
        return Registration.id == mine.id

    data = {'registration_id': [mine.id, theirs.id]} if method == 'POST' else None
    with app_context.test_request_context(method=method, data=data):
        request.view_args = {'reg_form_id': dummy_regform.id, 'event_id': dummy_regform.event_id}
        session.set_session_user(dummy_user)

        rh = rh_class()
        with signals.event.filter_registration_list.connected_to(_only_mine):
            rh._process_args()
            rh._check_access()
        assert rh.registrations == [mine]


@pytest.mark.parametrize('select_theirs', (False, True))
def test_badge_config_filtered_by_registration_list_criteria(db, dummy_regform, dummy_user, app_context,
                                                             select_theirs):
    dummy_regform.event.update_principal(dummy_user, full_access=True)
    mine, theirs = (create_registration(dummy_regform, {'email': email, 'first_name': 'A', 'last_name': last_name},
                                        invitation=None, management=True, notify_user=False)
                    for email, last_name in (('mine@example.test', 'Mine'), ('theirs@example.test', 'Theirs')))
    db.session.flush()

    def _only_mine(sender, user, **kwargs):
        return Registration.id == mine.id

    data = {'registration_id': [theirs.id]} if select_theirs else {}
    with app_context.test_request_context(method='POST', data=data):
        request.view_args = {'reg_form_id': dummy_regform.id, 'event_id': dummy_regform.event_id}
        session.set_session_user(dummy_user)

        rh = RHRegistrationsConfigBadges()
        with signals.event.filter_registration_list.connected_to(_only_mine):
            rh._process_args()
        assert rh.registrations == ([] if select_theirs else [mine])


@pytest.mark.parametrize(('scoped_in', 'allowed'), (
    (True, True),
    (False, False),
))
def test_registration_management_requires_manageable_registration(db, dummy_regform, dummy_user, app_context,
                                                                   scoped_in, allowed):
    dummy_regform.event.update_principal(dummy_user, full_access=True)
    registration = create_registration(dummy_regform, {'email': 'a@example.test', 'first_name': 'A', 'last_name': 'B'},
                                       invitation=None, management=True, notify_user=False)
    db.session.flush()

    def _scope(sender, user, **kwargs):
        return Registration.id == (registration.id if scoped_in else -1)

    with app_context.test_request_context():
        request.view_args = {'reg_form_id': dummy_regform.id, 'event_id': dummy_regform.event_id,
                             'registration_id': registration.id}
        session.set_session_user(dummy_user)

        rh = RHRegistrationDetails()
        rh._process_args()
        with signals.event.filter_registration_list.connected_to(_scope):
            if allowed:
                rh._check_access()
            else:
                with pytest.raises(Forbidden, match='this registration'):
                    rh._check_access()


_CSRF_TOKEN = '00000000-0000-0000-0000-000000000001'


@pytest.fixture
def moderation_manager(dummy_regform, create_user, test_client):
    """Log in a manager of a moderated regform with the given permissions."""
    set_feature_enabled(dummy_regform.event, 'registration', True)
    dummy_regform.moderation_enabled = True

    def _login(permissions):
        user = create_user(123, email='manager@example.test')
        if permissions == 'full':
            dummy_regform.event.update_principal(user, full_access=True)
        else:
            dummy_regform.event.update_principal(user, add_permissions=permissions)
        with test_client.session_transaction() as sess:
            sess.set_session_user(user)
            sess['_csrf_token'] = _CSRF_TOKEN
        return user

    return _login


_moderation_matrix = pytest.mark.parametrize(('permissions', 'expected_state'), (
    ({'registration_edit'}, RegistrationState.pending),
    ({'registration_edit', 'registration_moderation'}, RegistrationState.complete),
    ({'registration'}, RegistrationState.complete),
    ('full', RegistrationState.complete),
))


@_moderation_matrix
@pytest.mark.usefixtures('smtp', 'no_csrf_check')
def test_registration_create_moderation(dummy_regform, test_client, moderation_manager, permissions, expected_state):
    moderation_manager(permissions)
    url = f'/event/{dummy_regform.event_id}/manage/registration/{dummy_regform.id}/registrations/create'
    resp = test_client.post(url, json={'first_name': 'Greater', 'last_name': 'Capybara',
                                       'email': 'capybara@example.test'})
    assert resp.status_code == 200
    registration = dummy_regform.get_registration(email='capybara@example.test')
    assert registration.state == expected_state
    with test_client.session_transaction() as sess:
        expected_message = ('The registration was created and is awaiting approval.'
                            if expected_state == RegistrationState.pending else 'The registration was created.')
        assert sess['_flashes'] == [('success', expected_message)]


@pytest.mark.usefixtures('smtp', 'no_csrf_check')
def test_registration_create_unmoderated(dummy_regform, test_client, moderation_manager):
    moderation_manager({'registration_edit'})
    dummy_regform.moderation_enabled = False
    url = f'/event/{dummy_regform.event_id}/manage/registration/{dummy_regform.id}/registrations/create'
    resp = test_client.post(url, json={'first_name': 'Greater', 'last_name': 'Capybara',
                                       'email': 'capybara@example.test'})
    assert resp.status_code == 200
    registration = dummy_regform.get_registration(email='capybara@example.test')
    assert registration.state == RegistrationState.complete


@_moderation_matrix
@pytest.mark.usefixtures('smtp')
def test_registration_create_multiple_moderation(dummy_regform, dummy_user, test_client, moderation_manager,
                                                 permissions, expected_state):
    moderation_manager(permissions)
    url = f'/event/{dummy_regform.event_id}/manage/registration/{dummy_regform.id}/registrations/create-multiple'
    resp = test_client.post(url, data={'csrf_token': _CSRF_TOKEN, 'user_principals': f'["{dummy_user.identifier}"]'})
    assert resp.status_code == 200
    registration = dummy_regform.get_registration(user=dummy_user)
    assert registration.state == expected_state


@pytest.mark.parametrize(('permissions', 'reset_approval', 'expected_state'), (
    ({'registration_edit'}, True, RegistrationState.pending),
    ({'registration_edit'}, False, RegistrationState.complete),
    ({'registration_edit', 'registration_moderation'}, True, RegistrationState.complete),
    ({'registration'}, True, RegistrationState.complete),
    ('full', True, RegistrationState.complete),
))
@pytest.mark.usefixtures('smtp', 'no_csrf_check')
def test_registration_edit_moderation(dummy_regform, test_client, moderation_manager, permissions, reset_approval,
                                      expected_state):
    dummy_regform.reset_approval_on_modification = reset_approval
    registration = create_registration(dummy_regform, {'email': 'capybara@example.test', 'first_name': 'Greater',
                                                       'last_name': 'Capybara'},
                                       management=True, notify_user=False)
    assert registration.state == RegistrationState.complete
    moderation_manager(permissions)
    url = (f'/event/{dummy_regform.event_id}/manage/registration/{dummy_regform.id}/registrations/'
           f'{registration.id}/edit')
    resp = test_client.post(url, json={'last_name': 'Lesser'})
    assert resp.status_code == 200
    assert registration.last_name == 'Lesser'
    assert registration.state == expected_state
