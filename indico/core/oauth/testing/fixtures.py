# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

import pytest
from authlib.common.security import generate_token

from indico.core.oauth.models.applications import OAuthApplication, OAuthApplicationUserLink
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.core.oauth.models.tokens import OAuthToken
from indico.core.oauth.util import TOKEN_PREFIX_OAUTH


@pytest.fixture
def create_application(db):
    """Return a callable which lets you create applications."""

    def _create_application(name, **params):
        params.setdefault('client_id', str(uuid4()))
        params.setdefault('allowed_scopes', ['read:legacy_api', 'write:legacy_api', 'read:user'])
        params.setdefault('redirect_uris', ['http://localhost:10500/'])
        params.setdefault('allow_pkce_flow', True)
        application = OAuthApplication(name=name, **params)
        db.session.add(application)
        db.session.flush()
        return application

    return _create_application


@pytest.fixture
def dummy_application(create_application):
    """Return a dummy application."""
    return create_application(name='dummy')


@pytest.fixture
def dummy_app_link(db, dummy_application, dummy_user):
    """Return an app link for the dummy user."""
    link = OAuthApplicationUserLink(application=dummy_application, user=dummy_user,
                                    scopes=['read:legacy_api', 'read:user'])
    db.session.add(link)
    db.session.flush()
    return link


@pytest.fixture
def dummy_token(db, dummy_app_link):
    """Return a token for the dummy app/user."""
    token_string = TOKEN_PREFIX_OAUTH + generate_token()
    token = OAuthToken(access_token=token_string, app_user_link=dummy_app_link, scopes=['read:legacy_api', 'read:user'])
    token._plaintext_token = token_string
    db.session.add(token)
    db.session.flush()
    return token


@pytest.fixture
def dummy_personal_token(db, dummy_user):
    """Return a personal token for the dummy user."""
    token = PersonalToken(name='dummy', user=dummy_user, scopes=['read:legacy_api', 'read:user'])
    token._plaintext_token = token.generate_token()
    db.session.add(token)
    db.session.flush()
    return token
