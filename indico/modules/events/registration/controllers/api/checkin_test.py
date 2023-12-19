# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

import pytest
import yaml

from indico.modules.events.features.util import set_feature_enabled
from indico.testing.util import remove_dynamic_data


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.fixture(autouse=True)
def _configure_dummy_event(dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)


@pytest.fixture
def auth_headers(dummy_personal_token, dummy_user, dummy_event):
    dummy_personal_token.scopes = ['registrants']
    dummy_event.update_principal(dummy_user, add_permissions={'registration'})
    return {'Authorization': f'Bearer {dummy_personal_token._plaintext_token}'}


def _assert_successful_request(snapshot, resp, name):
    snapshot.snapshot_dir = Path(__file__).parent / 'test_snapshots'
    assert resp.status_code == 200
    dumped = yaml.dump(resp.json)
    dumped = remove_dynamic_data(dumped)
    __tracebackhide__ = True
    snapshot.assert_match(dumped, f'{name}.yml')


@pytest.mark.parametrize('auth', ('guest', 'noscope', 'scope'))
@pytest.mark.parametrize('url', (
    '/api/checkin/event/{event_id}/',
    '/api/checkin/event/{event_id}/forms/',
    '/api/checkin/event/{event_id}/forms/{regform_id}/',
    '/api/checkin/event/{event_id}/forms/{regform_id}/registrations/',
    '/api/checkin/event/{event_id}/forms/{regform_id}/registrations/{reg_id}',
    '/api/checkin/ticket/{ticket_uuid}',
))
def test_unauthorized(dummy_event, dummy_regform, dummy_reg, dummy_user, dummy_personal_token, test_client, auth, url):
    if auth == 'guest':
        headers = None
    else:
        headers = {'Authorization': f'Bearer {dummy_personal_token._plaintext_token}'}
        if auth == 'scope':
            dummy_personal_token.scopes = ['registrants']
        else:
            # missing scope on the token, so being a manager should not grant access
            dummy_event.update_principal(dummy_user, full_access=True)

    url = url.format(event_id=dummy_event.id, regform_id=dummy_regform.id,
                     reg_id=dummy_reg.id, ticket_uuid=dummy_reg.ticket_uuid)
    resp = test_client.get(url, headers=headers)
    assert 'error' in resp.json
    assert resp.status_code == 403


def test_event_details(snapshot, dummy_event, auth_headers, test_client):
    resp = test_client.get(f'/api/checkin/event/{dummy_event.id}/', headers=auth_headers)
    _assert_successful_request(snapshot, resp, 'checkin_event_details')


@pytest.mark.usefixtures('dummy_regform', 'dummy_reg')
def test_event_regforms(snapshot, dummy_event, auth_headers, test_client):
    resp = test_client.get(f'/api/checkin/event/{dummy_event.id}/forms/', headers=auth_headers)
    _assert_successful_request(snapshot, resp, 'checkin_regforms')


@pytest.mark.usefixtures('dummy_reg')
def test_event_regform_details(snapshot, dummy_event, dummy_regform, auth_headers, test_client):
    resp = test_client.get(f'/api/checkin/event/{dummy_event.id}/forms/{dummy_regform.id}/', headers=auth_headers)
    _assert_successful_request(snapshot, resp, 'checkin_regform_details')


@pytest.mark.usefixtures('dummy_reg')
def test_event_registrations(snapshot, dummy_event, dummy_regform, auth_headers, test_client):
    resp = test_client.get(f'/api/checkin/event/{dummy_event.id}/forms/{dummy_regform.id}/registrations/',
                           headers=auth_headers)
    _assert_successful_request(snapshot, resp, 'checkin_registrations')


def test_event_registration_details(snapshot, dummy_event, dummy_regform, dummy_reg, auth_headers, test_client):
    resp = test_client.get(f'/api/checkin/event/{dummy_event.id}/forms/{dummy_regform.id}/registrations/{dummy_reg.id}',
                           headers=auth_headers)
    _assert_successful_request(snapshot, resp, 'checkin_registration_details')

    resp = test_client.get(f'/api/checkin/ticket/{dummy_reg.ticket_uuid}', headers=auth_headers)
    _assert_successful_request(snapshot, resp, 'checkin_registration_details')


@pytest.mark.usefixtures('smtp')  # marking as paid sends an email
def test_update_registration(dummy_event, dummy_regform, dummy_reg, auth_headers, test_client):
    assert dummy_reg.checked_in  # dummy_reg is checked-in by default
    assert not dummy_reg.is_paid
    dummy_reg.base_price = 69
    url = f'/api/checkin/event/{dummy_event.id}/forms/{dummy_regform.id}/registrations/{dummy_reg.id}'

    resp = test_client.patch(url, json={'checked_in': False}, headers=auth_headers)
    assert not resp.json['checked_in']
    assert not dummy_reg.checked_in

    resp = test_client.patch(url, json={'checked_in': True}, headers=auth_headers)
    assert dummy_reg.checked_in
    assert resp.json['checked_in']

    resp = test_client.patch(url, json={'paid': True}, headers=auth_headers)
    assert dummy_reg.is_paid
    assert resp.json['is_paid']

    resp = test_client.patch(url, json={'paid': False}, headers=auth_headers)
    assert not dummy_reg.is_paid
    assert not resp.json['is_paid']
    assert resp.json['state'] != 'unpaid'
