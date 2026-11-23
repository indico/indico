# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import render_template


SUPPORT_EMAIL = 'support@example.test'
SUPPORT_URL = 'https://example.test/support'


@pytest.mark.parametrize(('email', 'url', 'status_code'), (
    (None, None, 404),
    (SUPPORT_EMAIL, None, 200),
    (None, SUPPORT_URL, 302),
    (SUPPORT_EMAIL, SUPPORT_URL, 302),
))
@pytest.mark.usefixtures('db')
def test_contact_page(patch_indico_config, test_client, email, url, status_code):
    patch_indico_config('PUBLIC_SUPPORT_EMAIL', email)
    patch_indico_config('PUBLIC_SUPPORT_URL', url)
    resp = test_client.get('/contact')
    assert resp.status_code == status_code
    if url:
        assert resp.location == SUPPORT_URL
    elif email:
        assert f'href="mailto:{SUPPORT_EMAIL}"' in resp.text


@pytest.mark.parametrize(('email', 'url', 'contact_link'), (
    (None, None, None),
    (SUPPORT_EMAIL, None, '/contact'),
    (None, SUPPORT_URL, SUPPORT_URL),
    (SUPPORT_EMAIL, SUPPORT_URL, SUPPORT_URL),
))
@pytest.mark.usefixtures('db', 'request_context')
def test_footer_contact_link(patch_indico_config, email, url, contact_link):
    patch_indico_config('PUBLIC_SUPPORT_EMAIL', email)
    patch_indico_config('PUBLIC_SUPPORT_URL', url)
    html = render_template('footer.html')
    assert ('Contact' in html) == bool(contact_link)
    if contact_link:
        assert f'href="{contact_link}"' in html


@pytest.mark.parametrize('endpoint', ('/api/config', '/rooms/api/config'))
@pytest.mark.parametrize(('email', 'url', 'expected_email', 'expected_url'), (
    (None, None, None, None),
    (SUPPORT_EMAIL, None, SUPPORT_EMAIL, None),
    (None, SUPPORT_URL, None, SUPPORT_URL),
    (SUPPORT_EMAIL, SUPPORT_URL, None, SUPPORT_URL),
))
def test_config_api_contact(patch_indico_config, test_client, dummy_user, endpoint, email, url, expected_email,
                            expected_url):
    patch_indico_config('PUBLIC_SUPPORT_EMAIL', email)
    patch_indico_config('PUBLIC_SUPPORT_URL', url)
    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)
    data = test_client.get(endpoint).json
    assert data['contact_email'] == expected_email
    assert data['contact_url'] == expected_url
