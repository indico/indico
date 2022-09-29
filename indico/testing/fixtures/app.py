# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

import pytest
from flask_webpackext.ext import _FlaskWebpackExtState

from indico.web.flask.app import make_app
from indico.web.flask.wrappers import IndicoFlask


@pytest.fixture(scope='session')
def app(request, redis_proc):
    """Create the flask app."""
    config_override = {
        'BASE_URL': 'http://localhost',
        'SMTP_SERVER': ('localhost', 0),  # invalid port - just in case so we NEVER send emails!
        'TEMP_DIR': request.config.indico_temp_dir.strpath,
        'CACHE_DIR': request.config.indico_temp_dir.strpath,
        'REDIS_CACHE_URL': f'redis://{redis_proc.host}:{redis_proc.port}/0',
        'STORAGE_BACKENDS': {'default': 'mem:'},
        'PLUGINS': request.config.indico_plugins,
        'ENABLE_ROOMBOOKING': True,
        'SECRET_KEY': os.urandom(16),
        'SMTP_USE_CELERY': False,
    }
    return make_app(testing=True, config_override=config_override)


@pytest.fixture(autouse=True)
def app_context(app):
    """Create a flask app context."""
    with app.app_context():
        yield app
        # flask 2.2 applies setupmethod checks even outside debug mode, so we can no longer
        # add new endpoints (specific to some test) whenever we want. by resetting it we
        # avoid the error. of course any of those endpoints added during test leak to other
        # tests but that can't be avoided without adding the overhead of creating a new app
        # for every single test.
        app._got_first_request = False


@pytest.fixture
def request_context(app_context):
    """Create a flask request context."""
    with app_context.test_request_context():
        yield


@pytest.fixture
def make_test_client(app, mocker):
    """Return a factory for test clients."""
    mocker.patch.object(_FlaskWebpackExtState, 'manifest')
    mocker.patch.object(IndicoFlask, 'manifest')

    return app.test_client


@pytest.fixture
def test_client(make_test_client):
    """Create a flask test client."""
    with make_test_client() as c:
        yield c
