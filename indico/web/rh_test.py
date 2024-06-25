# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from contextlib import nullcontext as does_not_raise
from unittest.mock import MagicMock

import pytest
from flask import request
from werkzeug.exceptions import Forbidden

from indico.core import signals
from indico.core.errors import IndicoError
from indico.web.flask.util import make_view_func
from indico.web.rh import RH, cors


@pytest.mark.usefixtures('request_context')
def test_before_check_access_signal(mocker):
    mocker.patch.object(RH, '_check_access')
    RH._process_GET = MagicMock()
    rh = RH()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: True):
        rh.process()
        rh._check_access.assert_not_called()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: None):
        rh.process()
        rh._check_access.assert_called_once()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: False):
        with pytest.raises(Forbidden):
            rh.process()


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('signal_rv_1', 'signal_rv_2', 'skipped'), (
    (None,  None,  False),
    (None,  True,  True),
    (True,  True,  True),
))
def test_before_check_access_signal_many_handlers_skipped(mocker, signal_rv_1, signal_rv_2, skipped):
    mocker.patch.object(RH, '_check_access')
    RH._process_GET = MagicMock()
    rh = RH()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_1):
        with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_2):
            rh.process()
            if skipped:
                rh._check_access.assert_not_called()
            else:
                rh._check_access.assert_called_once()


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('signal_rv_1', 'signal_rv_2', 'expectation'), (
    (False, False, pytest.raises(Forbidden)),
    (False, True,  pytest.raises(Forbidden)),
    (False, None,  pytest.raises(Forbidden)),
    (True,  True,  does_not_raise()),
    (None,  None,  does_not_raise()),
))
def test_before_check_access_signal_many_handlers_forbidden(mocker, signal_rv_1, signal_rv_2, expectation):
    RH._process_GET = MagicMock()
    rh = RH()

    with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_1):
        with signals.rh.before_check_access.connected_to(lambda *args, **kwargs: signal_rv_2):
            with expectation:
                rh.process()


def test_cors_usage(mocker):
    # Ensure `cors` can be used both as `@cors` and `@cors(...)`
    @cors
    class DummyRH(RH):
        def _process(self):
            pass

    assert DummyRH._CORS == {}

    @cors()
    class DummyRH(RH):
        def _process(self):
            pass

    assert DummyRH._CORS == {}

    @cors(origins='localhost')
    class DummyRH(RH):
        def _process(self):
            pass

    assert DummyRH._CORS == {'origins': 'localhost'}


def test_cors_headers(app):
    @cors(origins='localhost')
    class DummyRH(RH):
        def _process(self):
            pass

    app.add_url_rule('/test/cors/headers', 'test_cors_headers', make_view_func(DummyRH))

    with app.test_client() as client:
        resp = client.options('/test/cors/headers')
        # Ensure the CORS headers are set
        assert resp.headers['Access-Control-Allow-Origin'] == 'localhost'


def test_cors_headers_set_after_error(app):
    @cors(origins='localhost')
    class DummyRH(RH):
        def _process(self):
            raise IndicoError('something went wrong')

    app.add_url_rule('/test/cors/error', 'test_cors_error', make_view_func(DummyRH))

    with app.test_client() as client:
        # Force a json response in `render_error`.
        # Otherwise, Indico will try to render an HTML error which requires webpack
        # which we don't use in the python tests workflow.
        headers = {'Content-Type': 'application/json'}
        resp = client.get('/test/cors/error', headers=headers)
        # Ensure the CORS headers are set even if an error was raised
        assert resp.headers['Access-Control-Allow-Origin'] == 'localhost'


def test_normalize_simple(app, test_client):
    @make_view_func
    class DummyRH(RH):
        normalize_url_spec = {'locators': {lambda self: {'id': 42}}}

        def _process(self):
            assert request.view_args['id'] == 42
            return str(request.view_args['id'])

    app.add_url_rule('/test/normalize/simple/<int:id>', 'test_normalize_simple', DummyRH)

    resp = test_client.get('/test/normalize/simple/1', follow_redirects=True)
    assert resp.request.path == '/test/normalize/simple/42'


class _LateDummyRH(RH):
    normalize_url_spec = {'locators': {lambda self: {'id': 42}}, 'preserved_args': {'slug'}}
    normalize_url_spec_late = {'locators': {lambda self: {'id': 42, 'slug': 'meow'}}}

    def _check_access(self):
        if not self.authorized:
            raise Forbidden

    def _process(self):
        assert request.view_args['id'] == 42
        return str(request.view_args['id'])


@pytest.mark.parametrize('authorized', (False, True))
@pytest.mark.parametrize('suffix', ('', '-meow', '-foo'))
def test_normalize_late(app, test_client, dummy_user, authorized, suffix):
    _LateDummyRH.authorized = authorized
    app.add_url_rule('/test/normalize/late/<int:id>', 'test_normalize_late', make_view_func(_LateDummyRH))
    app.add_url_rule('/test/normalize/late/<int:id>-<slug>', 'test_normalize_late', make_view_func(_LateDummyRH))

    with test_client.session_transaction() as sess:
        sess.set_session_user(dummy_user)  # avoid redirect to login page
    resp = test_client.get(f'/test/normalize/late/1{suffix}', follow_redirects=True)
    history = [x.location for x in resp.history]

    if authorized:
        assert resp.request.path == '/test/normalize/late/42-meow'
        # Using a set here because the order is not really significant, and it's easiest way to deduplicate.
        assert set(history) == {f'/test/normalize/late/42{suffix}', '/test/normalize/late/42-meow'}
    else:
        assert resp.request.path == f'/test/normalize/late/42{suffix}'
        assert history == [f'/test/normalize/late/42{suffix}']

    # TODO: Add more tests for other URL normalization functionality
