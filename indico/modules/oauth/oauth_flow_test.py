# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from base64 import b64encode

import pytest
from authlib.common.security import generate_token
from authlib.oauth2.client import OAuth2Client
from werkzeug.urls import url_parse

from indico.modules.oauth.models.applications import SCOPES
from indico.web.flask.util import url_for


pytest_plugins = 'indico.modules.oauth.testing.fixtures'


class MockSession:
    def __init__(self, client):
        self.client = client

    def request(self, method, url, *, data, headers, auth):
        # we need to copy the headers since `prepare()` may modify them in-place,
        # and the initial header dict may be coming from the client's DEFAULT_HEADERS,
        # so without the copy we'd add basic auth headers to the default affecting future
        # requests. usually requests does that, but since we pretend to be requests but
        # use the flask test client instead, we need to take care of making the copy...
        headers = headers.copy()
        url, headers, data = auth.prepare(method, url, headers, data)
        return CallableJsonWrapper(self.client.open(url, method=method, data=data, headers=headers))


class CallableJsonWrapper:
    def __init__(self, resp):
        self.resp = resp

    def json(self):
        return self.resp.json

    def __getattr__(self, attr):
        return getattr(self.resp, attr)


@pytest.mark.parametrize('trusted', (False, True))
@pytest.mark.parametrize(('token_endpoint_auth_method', 'pkce'), (
    ('client_secret_basic', False),
    ('client_secret_post', False),
    ('none', True),
))
def test_oauth_flows(create_application, test_client, dummy_user, db, app, trusted, token_endpoint_auth_method, pkce):
    oauth_app = create_application(name='test', is_trusted=trusted)
    oauth_client = OAuth2Client(MockSession(test_client),
                                oauth_app.client_id,
                                oauth_app.client_secret if not pkce else None,
                                code_challenge_method=('S256' if pkce else None),
                                scope='read:user',
                                response_type='code',
                                token_endpoint=url_for('oauth.oauth_token', _external=True),
                                token_endpoint_auth_method=token_endpoint_auth_method,
                                redirect_uri=oauth_app.default_redirect_uri)

    code_verifier = generate_token(64) if pkce else None
    auth_url, state = oauth_client.create_authorization_url(url_for('oauth.oauth_authorize', _external=True),
                                                            code_verifier=code_verifier)

    with test_client.session_transaction() as sess:
        sess.user = dummy_user

    # get consent page
    resp = test_client.get(auth_url)
    if trusted:
        authorized_resp = resp
    else:
        assert resp.status_code == 200
        assert b'is requesting the following permissions' in resp.data
        assert b'User information (read only)' in resp.data

        # give consent
        authorized_resp = test_client.post(auth_url, data={'confirm': '1'})

    assert authorized_resp.status_code == 302
    target_url = authorized_resp.headers['Location']
    target_url_parts = url_parse(target_url)

    assert f'state={state}' in target_url_parts.query
    assert target_url == f'{oauth_app.default_redirect_uri}?{target_url_parts.query}'

    # for some weird reason there's a collision of two identical User objects in the SA session;
    # probably this happens because the DB session is not fully reset between the test requests?
    db.session.expunge(dummy_user)

    # get a token and make sure it looks fine
    token = oauth_client.fetch_token(authorization_response=target_url, code_verifier=code_verifier)
    assert token == {'access_token': token['access_token'], 'token_type': 'Bearer', 'scope': 'read:user'}

    with app.test_client() as test_client_no_session:
        # make sure we can use our token
        uri, headers, data = oauth_client.token_auth.prepare('/api/user/', {}, '')
        resp = test_client_no_session.get(uri, data=data, headers=headers)
        assert resp.status_code == 200
        assert resp.json['id'] == dummy_user.id

    # authorizing again won't require new consent, regardless of the app being trusted
    assert test_client.get(auth_url).status_code == 302


def test_oauth_scopes(create_application, test_client, dummy_user, db, app):
    oauth_app = create_application(name='test', is_trusted=False, default_scopes=['read:user', 'read:legacy_api'])
    oauth_client = OAuth2Client(MockSession(test_client),
                                oauth_app.client_id, oauth_app.client_secret,
                                token_endpoint=url_for('oauth.oauth_token', _external=True),
                                redirect_uri=oauth_app.default_redirect_uri)

    with test_client.session_transaction() as sess:
        sess.user = dummy_user

    auth_endpoint = url_for('oauth.oauth_authorize', _external=True)
    auth_url = oauth_client.create_authorization_url(auth_endpoint, scope='read:legacy_api')[0]

    # get consent page
    resp = test_client.get(auth_url)
    assert resp.status_code == 200
    assert b'is requesting the following permissions' in resp.data
    assert b'Legacy API (read only)' in resp.data
    assert b'User information (read only)' not in resp.data

    # give consent
    authorized_resp = test_client.post(auth_url, data={'confirm': '1'})
    assert authorized_resp.status_code == 302
    target_url = authorized_resp.headers['Location']

    # for some weird reason there's a collision of two identical User objects in the SA session;
    # probably this happens because the DB session is not fully reset between the test requests?
    db.session.expunge(dummy_user)

    # get a token and make sure it looks fine
    token = oauth_client.fetch_token(authorization_response=target_url)
    assert token == {'access_token': token['access_token'], 'token_type': 'Bearer', 'scope': 'read:legacy_api'}

    # we cannot use a token with an invalid scope
    with app.test_client() as test_client_no_session:
        uri, headers, data = oauth_client.token_auth.prepare('/api/user/', {}, '')
        resp = test_client_no_session.get(uri, data=data, headers=headers)
        assert resp.status_code == 403

    # XXX: we should probably add scopes instead of replacing them. when we change that in the oauth
    # backend let's stop requesting the existing scope here but only ask for the new one. AFAIK most
    # oauth providers in the wild do this already...
    auth_url = oauth_client.create_authorization_url(auth_endpoint, scope='read:legacy_api read:user')[0]
    authorized_resp = test_client.post(auth_url, data={'confirm': '1'})
    target_url = authorized_resp.headers['Location']
    token = oauth_client.fetch_token(authorization_response=target_url)
    assert set(token.pop('scope').split()) == {'read:legacy_api', 'read:user'}
    assert token == {'access_token': token['access_token'], 'token_type': 'Bearer'}

    # now that we authorized the proper scope, we can use our token
    with app.test_client() as test_client_no_session:
        uri, headers, data = oauth_client.token_auth.prepare('/api/user/', {}, '')
        resp = test_client_no_session.get(uri, data=data, headers=headers)
        assert resp.status_code == 200
        assert resp.json['id'] == dummy_user.id


@pytest.mark.parametrize('endpoint_auth', ('client_secret_post', 'client_secret_basic'))
def test_introspection(dummy_application, dummy_token, test_client, endpoint_auth):
    data = {'token': dummy_token.access_token}
    headers = {}
    if endpoint_auth == 'client_secret_post':
        data['client_id'] = dummy_application.client_id
        data['client_secret'] = dummy_application.client_secret
    elif endpoint_auth == 'client_secret_basic':
        basic_auth = b64encode(f'{dummy_application.client_id}:{dummy_application.client_secret}'.encode()).decode()
        headers['Authorization'] = f'Basic {basic_auth}'
    resp = test_client.post('/oauth/introspect', data=data, headers=headers)
    assert resp.json == {
        'active': True,
        'client_id': dummy_application.client_id,
        'token_type': 'Bearer',
        'scope': dummy_token.get_scope(),
        'sub': str(dummy_token.user.id),
        'iss': 'http://localhost'
    }


@pytest.mark.parametrize('reason', ('nouuid', 'invalid', 'appdisabled'))
def test_introspection_inactive(dummy_application, dummy_token, test_client, reason):
    token = dummy_token.access_token
    if reason == 'nouuid':
        token = 'garbage'
    elif reason == 'invalid':
        token = '00000000-0000-0000-0000-000000000000'
    elif reason == 'appdisabled':
        dummy_application.is_enabled = False

    data = {
        'token': token,
        'client_id': dummy_application.client_id,
        'client_secret': dummy_application.client_secret
    }
    resp = test_client.post('/oauth/introspect', data=data)
    if reason == 'appdisabled':
        assert resp.status_code == 400
        assert resp.json == {'error': 'invalid_client'}
    else:
        assert resp.json == {'active': False}


def test_introspection_wrong_app(create_application, dummy_token, test_client):
    other_app = create_application(name='test')
    data = {
        'token': dummy_token.access_token,
        'client_id': other_app.client_id,
        'client_secret': other_app.client_secret
    }
    resp = test_client.post('/oauth/introspect', data=data)
    assert resp.json == {'active': False}


@pytest.mark.parametrize(('reason', 'status_code', 'error'), (
    ('nouuid', 401, 'invalid_token'),
    ('invalid', 401, 'invalid_token'),
    ('appdisabled', 401, 'invalid_token'),
    ('badscope', 403, 'insufficient_scope')
))
def test_invalid_token(dummy_application, dummy_token, test_client, reason, status_code, error):
    token = dummy_token.access_token
    if reason == 'nouuid':
        token = 'garbage'
    elif reason == 'invalid':
        token = '00000000-0000-0000-0000-000000000000'
    elif reason == 'appdisabled':
        dummy_application.is_enabled = False

    if reason != 'badscope':
        dummy_token._scopes.append('read:user')

    resp = test_client.get('/api/user/', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == status_code
    assert resp.json['error'] == error


def test_metadata_endpoint(test_client):
    resp = test_client.get('/.well-known/oauth-authorization-server')
    assert resp.status_code == 200
    assert resp.json == {
        'authorization_endpoint': 'http://localhost/oauth/authorize',
        'code_challenge_methods_supported': ['S256'],
        'grant_types_supported': ['authorization_code'],
        'introspection_endpoint': 'http://localhost/oauth/introspect',
        'introspection_endpoint_auth_methods_supported': ['client_secret_basic', 'client_secret_post'],
        'issuer': 'http://localhost',
        'response_modes_supported': ['query'],
        'response_types_supported': ['code'],
        'scopes_supported': list(SCOPES),
        'token_endpoint': 'http://localhost/oauth/token',
        'token_endpoint_auth_methods_supported': ['client_secret_basic',  'client_secret_post', 'none']
    }
