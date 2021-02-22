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

from indico.core.oauth.scopes import SCOPES
from indico.web.flask.util import url_for


pytest_plugins = 'indico.core.oauth.testing.fixtures'


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
def test_oauth_flows(create_application, test_client, dummy_user, app, trusted, token_endpoint_auth_method, pkce):
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


@pytest.mark.parametrize('pkce_enabled', (False, True))
def test_pkce_disabled(dummy_application, test_client, dummy_user, pkce_enabled):
    dummy_application.allow_pkce_flow = pkce_enabled
    oauth_client = OAuth2Client(MockSession(test_client),
                                dummy_application.client_id, None,
                                code_challenge_method='S256',
                                token_endpoint=url_for('oauth.oauth_token', _external=True),
                                redirect_uri=dummy_application.default_redirect_uri)

    with test_client.session_transaction() as sess:
        sess.user = dummy_user

    code_verifier = generate_token(64)
    auth_endpoint = url_for('oauth.oauth_authorize', _external=True)
    auth_url = oauth_client.create_authorization_url(auth_endpoint, scope='read:legacy_api',
                                                     code_verifier=code_verifier)[0]

    authorized_resp = test_client.post(auth_url, data={'confirm': '1'})
    assert authorized_resp.status_code == 302
    target_url = authorized_resp.headers['Location']

    if pkce_enabled:
        token = oauth_client.fetch_token(authorization_response=target_url, code_verifier=code_verifier)
        assert token.keys() == {'access_token', 'token_type', 'scope'}
    else:
        with pytest.raises(ValueError) as exc_info:
            oauth_client.fetch_token(authorization_response=target_url, code_verifier=code_verifier)
        assert 'invalid_client' in str(exc_info.value)


def test_no_implicit_flow(dummy_application, test_client, dummy_user):
    oauth_client = OAuth2Client(None,
                                dummy_application.client_id,
                                None,
                                scope='read:user',
                                response_type='token',
                                token_endpoint=url_for('oauth.oauth_token', _external=True),
                                redirect_uri=dummy_application.default_redirect_uri)

    auth_url = oauth_client.create_authorization_url(url_for('oauth.oauth_authorize', _external=True))[0]

    with test_client.session_transaction() as sess:
        sess.user = dummy_user

    resp = test_client.get(auth_url)
    assert b'unsupported_response_type' in resp.data


def test_no_querystring_tokens(dummy_token, test_client):
    resp = test_client.get('/api/user/', headers={'Authorization': f'Bearer {dummy_token.access_token}'})
    assert resp.status_code == 200
    resp = test_client.get(f'/api/user/?access_token={dummy_token.access_token}')
    assert resp.status_code == 401


def test_oauth_scopes(create_application, test_client, dummy_user, app):
    oauth_app = create_application(name='test', is_trusted=False, allowed_scopes=['read:user', 'read:legacy_api'])
    oauth_client = OAuth2Client(MockSession(test_client),
                                oauth_app.client_id, oauth_app.client_secret,
                                token_endpoint=url_for('oauth.oauth_token', _external=True),
                                redirect_uri=oauth_app.default_redirect_uri)

    with test_client.session_transaction() as sess:
        sess.user = dummy_user

    auth_endpoint = url_for('oauth.oauth_authorize', _external=True)
    auth_url = oauth_client.create_authorization_url(auth_endpoint, scope='read:legacy_api')[0]
    assert not oauth_app.user_links.count()

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
    assert not oauth_app.user_links.count()  # giving consent does not create the user/app link yet

    # get a token and make sure it looks fine
    token1 = oauth_client.fetch_token(authorization_response=target_url)
    assert token1 == {'access_token': token1['access_token'], 'token_type': 'Bearer', 'scope': 'read:legacy_api'}
    app_link = oauth_app.user_links.one()
    assert app_link.user == dummy_user
    assert app_link.scopes == ['read:legacy_api']

    # we cannot use a token with an invalid scope
    with app.test_client() as test_client_no_session:
        uri, headers, data = oauth_client.token_auth.prepare('/api/user/', {}, '')
        resp = test_client_no_session.get(uri, data=data, headers=headers)
        assert resp.status_code == 403

    # request a different scope
    auth_url = oauth_client.create_authorization_url(auth_endpoint, scope='read:user')[0]
    authorized_resp = test_client.post(auth_url, data={'confirm': '1'})
    target_url = authorized_resp.headers['Location']
    token2 = oauth_client.fetch_token(authorization_response=target_url)
    assert token2 == {'access_token': token2['access_token'], 'token_type': 'Bearer', 'scope': 'read:user'}
    assert token2['access_token'] != token1['access_token']
    assert app_link.scopes == ['read:legacy_api', 'read:user']

    # this token is already able to access the endpoint
    with app.test_client() as test_client_no_session:
        uri, headers, data = oauth_client.token_auth.prepare('/api/user/', {}, '')
        resp = test_client_no_session.get(uri, data=data, headers=headers)
        assert resp.status_code == 200
        assert resp.json['id'] == dummy_user.id

    # no scope specified, so we should get a token with all authorized scopes
    auth_url = oauth_client.create_authorization_url(auth_endpoint)[0]
    authorized_resp = test_client.post(auth_url, data={'confirm': '1'})
    target_url = authorized_resp.headers['Location']
    token3 = oauth_client.fetch_token(authorization_response=target_url)
    assert set(token3.pop('scope').split()) == {'read:legacy_api', 'read:user'}
    assert token3 == {'access_token': token3['access_token'], 'token_type': 'Bearer'}
    assert token3['access_token'] != token2['access_token']
    assert app_link.scopes == ['read:legacy_api', 'read:user']

    # and of course that token also has access to the endpoint
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


@pytest.mark.parametrize('endpoint_auth', ('client_secret_post', 'client_secret_basic'))
def test_revocation(db, dummy_application, dummy_token, test_client, endpoint_auth):
    data = {'token': dummy_token.access_token}
    headers = {}
    if endpoint_auth == 'client_secret_post':
        data['client_id'] = dummy_application.client_id
        data['client_secret'] = dummy_application.client_secret
    elif endpoint_auth == 'client_secret_basic':
        basic_auth = b64encode(f'{dummy_application.client_id}:{dummy_application.client_secret}'.encode()).decode()
        headers['Authorization'] = f'Basic {basic_auth}'
    resp = test_client.post('/oauth/revoke', data=data, headers=headers)
    assert resp.status_code == 200
    assert resp.json == {}
    assert dummy_token not in db.session
    # make sure we can no longer use the token
    resp = test_client.get('/api/user/', headers={'Authorization': f'Bearer {dummy_token.access_token}'})
    assert resp.status_code == 401


def test_revocation_wrong_app(db, create_application, dummy_token, test_client):
    other_app = create_application(name='test')
    data = {
        'token': dummy_token.access_token,
        'client_id': other_app.client_id,
        'client_secret': other_app.client_secret
    }
    resp = test_client.post('/oauth/revoke', data=data)
    assert resp.status_code == 200
    assert resp.json == {}
    assert dummy_token in db.session
    # make sure we can still use the token
    resp = test_client.get('/api/user/', headers={'Authorization': f'Bearer {dummy_token.access_token}'})
    assert resp.status_code == 200


@pytest.mark.parametrize(('reason', 'status_code', 'error'), (
    ('nouuid', 401, 'invalid_token'),
    ('invalid', 401, 'invalid_token'),
    ('appdisabled', 401, 'invalid_token'),
    ('badscope', 403, 'insufficient_scope'),
    ('badapplinkscope', 403, 'insufficient_scope'),
    ('badappscope', 403, 'insufficient_scope')
))
def test_invalid_token(dummy_application, dummy_token, test_client, reason, status_code, error):
    token = dummy_token.access_token
    if reason == 'nouuid':
        token = 'garbage'
    elif reason == 'invalid':
        token = '00000000-0000-0000-0000-000000000000'
    elif reason == 'appdisabled':
        dummy_application.is_enabled = False

    if reason == 'badscope':
        dummy_token._scopes.remove('read:user')
    elif reason == 'badapplinkscope':
        dummy_token.app_user_link.scopes.remove('read:user')
    elif reason == 'badappscope':
        dummy_application.allowed_scopes.remove('read:user')

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
        'revocation_endpoint': 'http://localhost/oauth/revoke',
        'revocation_endpoint_auth_methods_supported': ['client_secret_basic', 'client_secret_post'],
        'scopes_supported': list(SCOPES),
        'token_endpoint': 'http://localhost/oauth/token',
        'token_endpoint_auth_methods_supported': ['client_secret_basic',  'client_secret_post', 'none']
    }
