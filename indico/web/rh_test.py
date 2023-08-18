# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from contextlib import nullcontext as does_not_raise
from unittest.mock import MagicMock

import pytest
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
        resp = client.get('/test/cors/error')
        # Ensure the CORS headers are set even if an error was raised
        assert resp.headers['Access-Control-Allow-Origin'] == 'localhost'
