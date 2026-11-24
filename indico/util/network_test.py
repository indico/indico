# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
import requests

from indico.util.network import (InsecureRequestError, is_private_url, make_validate_request_url_hook,
                                 validate_request_url)


@pytest.mark.parametrize(('url', 'expected'), (
    ('https://127.0.0.1', True),
    ('http://127.0.0.1', True),
    ('http://127.0.0.1\\@1.1.1.1', True),
    ('http://[::1]', True),
    ('https://localhost', True),
    ('http://192.168.0.12', True),
    ('http://indico.cern.ch', False),
    ('http://[2001:1458:201:87::100:c]', False),
    ('http://indico.local', True),
    ('http://local', True),
    ('http://testing-instance', True),
    ('http://indico', True),
    ('http//nonsense', True),
))
def test_is_private_url(url, expected):
    assert is_private_url(url) == expected


@pytest.mark.parametrize(('url', 'valid'), (
    ('https://public.test', True),
    ('http://public.test', True),
    ('http://PUBLIC.test', True),
    ('http://publi%63.test', False),
    ('http://a{b}.test', False),
    ('http://a%7Bb%7D.test', False),
    ('http://\N{FULLWIDTH DIGIT ONE}.test', False),
))
def test_validate_request_url_weird(monkeypatch, url, valid):
    monkeypatch.setattr('indico.util.network.is_private_url', lambda u: False)
    if valid:
        validate_request_url(url)
    else:
        with pytest.raises(InsecureRequestError) as exc_info:
            validate_request_url(url)
        assert str(exc_info.value) == 'Cannot make request to ambiguously parsed URL'


def test_validate_request_url(monkeypatch):
    monkeypatch.setattr('indico.util.network.is_private_url', lambda u: u == 'https://private.test')
    validate_request_url('https://public.test')
    with pytest.raises(InsecureRequestError) as exc_info:
        validate_request_url('https://private.test')
    assert str(exc_info.value) == 'Cannot make request to disallowed URL'


def test_validate_redirect_target_hook(mocked_responses, monkeypatch):
    monkeypatch.setattr('indico.util.network.is_private_url', lambda u: u == 'http://127.0.0.1')
    mocked_responses.get('http://no.redirect.test')
    mocked_responses.get('http://unsafe.redirect.test', status=302, headers={'Location': 'http://127.0.0.1'})
    mocked_responses.get('http://safe.redirect.test', status=302, headers={'Location': 'http://safe2.redirect.test/'})
    mocked_responses.get('http://safe2.redirect.test/')
    requests.get('http://no.redirect.test', **make_validate_request_url_hook())
    requests.get('http://safe.redirect.test', **make_validate_request_url_hook())
    with pytest.raises(InsecureRequestError) as exc_info:
        requests.get('http://unsafe.redirect.test', **make_validate_request_url_hook())
    assert str(exc_info.value) == 'Request redirected to disallowed URL'
