# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest


@pytest.mark.parametrize('authenticated', (False, True))
def test_user_logs_unauthenticated(test_client, dummy_user, create_user, authenticated):
    if authenticated:
        with test_client.session_transaction() as sess:
            sess.set_session_user(dummy_user)
    other_user = create_user(123)
    # no access via self url
    resp = test_client.get('/user/logs/api/logs', json={})
    assert resp.status_code == 403
    # no access via id url
    resp = test_client.get(f'/user/{dummy_user.id}/logs/api/logs', json={})
    assert resp.status_code == 403
    # no access to another user
    resp = test_client.get(f'/user/{other_user.id}/logs/api/logs', json={})
    assert resp.status_code == 403
