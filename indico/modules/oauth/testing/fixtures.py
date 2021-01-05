# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

import pytest

from indico.modules.oauth.models.applications import OAuthApplication
from indico.modules.oauth.models.tokens import OAuthToken


@pytest.fixture
def create_application(db):
    """Return a callable which lets you create applications."""

    def _create_application(name, **params):
        params.setdefault('client_id', unicode(uuid4()))
        params.setdefault('default_scopes', 'read:user')
        params.setdefault('redirect_uris', 'http://localhost:10500')
        params.setdefault('is_trusted', True)
        application = OAuthApplication(name=name, **params)
        db.session.add(application)
        db.session.flush()
        return application

    return _create_application


@pytest.fixture
def create_token(db, dummy_application, dummy_user):
    """Return a callable which lets you create tokens."""

    def _create_tokens(**params):
        params.setdefault('access_token', unicode(uuid4()))
        params.setdefault('user', dummy_user)
        params.setdefault('application', dummy_application)
        params.setdefault('scopes', ['read:api', 'write:api'])
        token = OAuthToken(**params)
        db.session.add(token)
        db.session.flush()
        return token

    return _create_tokens


@pytest.fixture
def dummy_application(create_application):
    """Return a dummy application."""
    return create_application(name='dummy')


@pytest.fixture
def dummy_token(create_token):
    """Return a dummy token."""
    return create_token()
