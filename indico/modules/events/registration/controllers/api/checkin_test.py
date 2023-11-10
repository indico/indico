# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.features.util import set_feature_enabled


pytest_plugins = ('indico.modules.events.registration.testing.fixtures', 'indico.core.oauth.testing.fixtures')


@pytest.fixture(autouse=True)
def enable_registration_feature(dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)


@pytest.mark.parametrize('auth', ('guest', 'noscope', 'scope'))
@pytest.mark.parametrize('url', (
    '/api/checkin/event/{event_id}/',
    '/api/checkin/event/{event_id}/forms/',
    '/api/checkin/event/{event_id}/forms/{regform_id}/',
    '/api/checkin/event/{event_id}/forms/{regform_id}/registrations/',
    '/api/checkin/event/{event_id}/forms/{regform_id}/registrations/{reg_id}',
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

    url = url.format(event_id=dummy_event.id, regform_id=dummy_regform.id, reg_id=dummy_reg.id)
    resp = test_client.get(url, headers=headers)
    assert 'error' in resp.json
    assert resp.status_code == 403
