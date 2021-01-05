# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os

import pytest

from indico.web.flask.app import make_app


@pytest.fixture(scope='session')
def app(request):
    """Create the flask app."""
    config_override = {
        'BASE_URL': 'http://localhost',
        'SMTP_SERVER': ('localhost', 0),  # invalid port - just in case so we NEVER send emails!
        'CACHE_BACKEND': 'null',
        'TEMP_DIR': request.config.indico_temp_dir.strpath,
        'CACHE_DIR': request.config.indico_temp_dir.strpath,
        'STORAGE_BACKENDS': {'default': 'mem:'},
        'PLUGINS': request.config.indico_plugins,
        'ENABLE_ROOMBOOKING': True,
        'SECRET_KEY': os.urandom(16),
        'SMTP_USE_CELERY': False,
    }
    return make_app(set_path=True, testing=True, config_override=config_override)


@pytest.fixture(autouse=True)
def app_context(app):
    """Create a flask app context."""
    with app.app_context():
        yield app


@pytest.fixture
def request_context(app_context):
    """Create a flask request context."""
    with app_context.test_request_context():
        yield
