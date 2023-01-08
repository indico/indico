# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import g, request


@pytest.mark.parametrize(('raw_ip', 'ip'), (
    ('::ffff:127.0.0.1', '127.0.0.1'),
    ('127.0.0.1', '127.0.0.1'),
    ('2001:db8::d34d:b33f', '2001:db8::d34d:b33f'),
))
def test_request_remote_addr(app, raw_ip, ip):
    with app.test_request_context(environ_base={'REMOTE_ADDR': raw_ip}):
        assert request.remote_addr == ip


def test_single_test_client(app, test_client):
    @app.route('/test-tc-single')
    def test_tc_single():
        foo = g.get('foo', 'notset')
        g.foo = 'bar'
        return foo

    resp = test_client.get('/test-tc-single')
    assert resp.text == 'notset'


def test_multi_test_client_no_g_leak(app, test_client):
    @app.route('/test-tc-multi')
    def test_tc_multi():
        foo = g.get('foo', 'notset')
        g.foo = 'bar'
        return foo

    # make sure g is cleared between requests
    resp = test_client.get('test-tc-multi')
    assert resp.text == 'notset'
    resp = test_client.get('test-tc-multi')
    assert resp.text == 'notset'
