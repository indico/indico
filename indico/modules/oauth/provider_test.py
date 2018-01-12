# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from flask import session
from mock import MagicMock
from oauthlib.oauth2 import InvalidClientIdError
from sqlalchemy.orm.exc import NoResultFound

from indico.modules.oauth.models.applications import OAuthApplication
from indico.modules.oauth.models.tokens import OAuthGrant
from indico.modules.oauth.provider import DisabledClientIdError, load_client, load_token, save_grant, save_token


pytest_plugins = 'indico.modules.oauth.testing.fixtures'


@pytest.fixture
def token_data():
    return {'access_token': unicode(uuid4()),
            'expires_in': 3600,
            'refresh_token': '',
            'scope': 'api'}


@pytest.fixture
def create_request(dummy_application, dummy_user):
    def _create_request(implicit=False):
        request = MagicMock()
        request.grant_type = 'authorization_code' if not implicit else None
        request.client.client_id = dummy_application.client_id
        request.user = dummy_user
        return request
    return _create_request


@pytest.fixture
def dummy_request(create_request):
    return create_request()


def test_load_client(dummy_application):
    assert load_client(dummy_application.client_id) == dummy_application


def test_load_client_malformed_id():
    with pytest.raises(InvalidClientIdError):
        load_client('foobar')


def test_load_client_disabled_app(dummy_application):
    dummy_application.is_enabled = False
    with pytest.raises(DisabledClientIdError):
        load_client(dummy_application.client_id)


@pytest.mark.usefixtures('request_context')
def test_save_grant(mocker, freeze_time):
    freeze_time(datetime.utcnow())
    mocker.patch.object(OAuthGrant, 'save')
    request = MagicMock()
    request.scopes = 'api'
    request.redirect_uri = 'http://localhost:5000'
    client_id = unicode(uuid4())
    code = {'code': 'foobar'}
    expires = datetime.utcnow() + timedelta(seconds=120)
    grant = save_grant(client_id, code, request)
    assert grant.client_id == client_id
    assert grant.code == code['code']
    assert grant.redirect_uri == request.redirect_uri
    assert grant.user == session.user
    assert grant.scopes == request.scopes
    assert grant.expires == expires
    assert grant.save.called


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('access_token', (True, False))
def test_load_token_no_access_token(dummy_application, dummy_token, token_data, access_token):
    access_token = dummy_token.access_token if access_token else None
    token = load_token(access_token)
    if access_token:
        assert token == dummy_token
    else:
        assert token is None


@pytest.mark.usefixtures('request_context')
def test_load_token_malformed_access_token(dummy_application, dummy_token, token_data):
    assert load_token('foobar') is None


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('app_is_enabled', (True, False))
def test_load_token_disabled_app(dummy_application, dummy_token, token_data, app_is_enabled):
    dummy_application.is_enabled = app_is_enabled
    token = load_token(dummy_token.access_token)
    if app_is_enabled:
        assert token == dummy_token
    else:
        assert token is None


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('implicit', (True, False))
def test_save_token(create_request, create_user, token_data, implicit):
    request = create_request(implicit=implicit)
    session.user = create_user(1)
    token = save_token(token_data, request)
    assert request.user != session.user
    assert token.user == session.user if implicit else request.user
    assert token.access_token == token_data['access_token']
    assert token.scopes == set(token_data['scope'].split())
    assert 'expires_in' not in token_data
    assert 'refresh_token' not in token_data


@pytest.mark.parametrize(('initial_scopes', 'requested_scopes', 'expected_scopes'), (
    ({},         'a',   {'a'}),
    ({},         'a b', {'a', 'b'}),
    ({'a'},      'a',   {'a'}),
    ({'a'},      'b',   {'a', 'b'}),
    ({'a', 'b'}, 'a',   {'a', 'b'}),
    ({'a', 'b'}, 'a b', {'a', 'b'}),
))
def test_save_token_scopes(dummy_request, create_token, token_data,
                           initial_scopes, requested_scopes, expected_scopes):
    if initial_scopes:
        create_token(scopes=initial_scopes)
    token_data['scope'] = requested_scopes
    initial_access_token = token_data['access_token']
    token = save_token(token_data, dummy_request)
    assert token.scopes == expected_scopes
    if not set(requested_scopes.split()) - set(initial_scopes):
        assert token_data['access_token'] != initial_access_token
    else:
        assert token_data['access_token'] == initial_access_token


@pytest.mark.parametrize('grant_type', ('foo', ''))
def test_save_token_invalid_grant(dummy_request, token_data, grant_type):
    dummy_request.grant_type = grant_type
    with pytest.raises(ValueError):
        save_token(token_data, dummy_request())


def test_save_token_no_application(dummy_application, dummy_request, token_data):
    dummy_request.client.client_id = unicode(uuid4())
    assert not OAuthApplication.find(client_id=dummy_request.client.client_id).count()
    with pytest.raises(NoResultFound):
        save_token(token_data, dummy_request)
