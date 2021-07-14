# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from authlib.oauth2.rfc6750 import InsufficientScopeError
from flask import session
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core.oauth.protector import IndicoAuthlibHTTPError, IndicoResourceProtector
from indico.web.flask.util import make_view_func
from indico.web.rh import RH, allow_signed_url, oauth_scope
from indico.web.util import (_check_request_user, _lookup_request_user, _request_likely_seen_by_user, get_oauth_user,
                             get_request_user, is_legacy_signed_url_valid, signed_url_for_user, verify_signed_user_url)


pytest_plugins = 'indico.core.oauth.testing.fixtures'


@pytest.mark.parametrize(('url', 'valid'), (
    ('/user/70/dashboard/?token=6bO-FgjAvYPiZ8Uft5_DmOC4Oow', True),
    ('/user/71/dashboard/?token=6bO-FgjAvYPiZ8Uft5_DmOC4Oow', False),
    ('/user/71/dashboard/?q=roygbiv&token=YNgcXP02LpIYCWMAN80xXg6l6jM', True),
    ('/user/71/dashboard/?q=roygbeef&token=YNgcXP02LpIYCWMAN80xXg6l6jM', False),
    ('/user/71/dashboard/?q=roygbiv&token=ZNgcXP02LpIYCWMAN80xXg6l6jM', False),
    ('/user/71/dashboard/?q=roygbiv', False),
    ('http://localhost/user/70/dashboard/?token=6bO-FgjAvYPiZ8Uft5_DmOC4Oow', True),
    ('http://localhost:8080/user/70/dashboard/?token=6bO-FgjAvYPiZ8Uft5_DmOC4Oow', True),
    ('https://indico.host/user/70/dashboard/?token=6bO-FgjAvYPiZ8Uft5_DmOC4Oow', True),
))
def test_is_legacy_signed_url_valid(dummy_user, url, valid):
    dummy_user.signing_secret = 'sixtyten'
    assert is_legacy_signed_url_valid(dummy_user, url) == valid


@pytest.mark.parametrize(('endpoint', 'kwargs', 'expected'), (
    ('core.contact', {}, '/contact?user_token=1337_F6kvmhWXsecSPOCqxfvlTCjO0A_Lvp-46SqnI6-LL_4'),
    ('core.contact', {'_external': True},
     'http://localhost/contact?user_token=1337_F6kvmhWXsecSPOCqxfvlTCjO0A_Lvp-46SqnI6-LL_4'),
    ('core.contact', {'foo': 'bar'}, '/contact?foo=bar&user_token=1337_4UAW4-UXy8TbQl_UjAGU3CYj7QQGy2ywybeuoiV5-os'),
    ('events.display', {'event_id': 123, 'a': 'b'},
     '/event/123/?a=b&user_token=1337_oBedsl3f2qDtfHShn7MS8F_Mz58GTtnvHoqP3WzVnBY'),
))
def test_signed_url_for_user(dummy_user, endpoint, kwargs, expected):
    dummy_user.signing_secret = 'sixtynine'
    url = signed_url_for_user(dummy_user, endpoint, **kwargs)
    assert url == expected


def test_signed_url_for_user_sorted(dummy_user):
    dummy_user.signing_secret = 'fourtytwo'
    url = signed_url_for_user(dummy_user, 'core.contact', a=1, b=2)
    url2 = signed_url_for_user(dummy_user, 'core.contact', b=2, a=1)
    assert url == url2


@pytest.mark.parametrize('url', (
    '/contact?user_token=1337_F6kvmhWXsecSPOCqxfvlTCjO0A_Lvp-46SqnI6-LL_4',
    'http://localhost/contact?user_token=1337_F6kvmhWXsecSPOCqxfvlTCjO0A_Lvp-46SqnI6-LL_4',
    'http://localhost:8080/contact?user_token=1337_F6kvmhWXsecSPOCqxfvlTCjO0A_Lvp-46SqnI6-LL_4',
    'https://indico.host/contact?user_token=1337_F6kvmhWXsecSPOCqxfvlTCjO0A_Lvp-46SqnI6-LL_4',
    '/contact?foo=bar&user_token=1337_4UAW4-UXy8TbQl_UjAGU3CYj7QQGy2ywybeuoiV5-os',
    '/event/123/?a=b&user_token=1337_oBedsl3f2qDtfHShn7MS8F_Mz58GTtnvHoqP3WzVnBY',
))
def test_verify_signed_user_url(dummy_user, url):
    # valid signature
    dummy_user.signing_secret = 'sixtynine'
    assert verify_signed_user_url(url, 'GET') == dummy_user

    # invalid method
    with pytest.raises(BadRequest) as exc_info:
        verify_signed_user_url(url, 'POST')
    assert 'The persistent link you used is invalid' in str(exc_info.value)

    # invalid url
    with pytest.raises(BadRequest) as exc_info:
        verify_signed_user_url(url.replace('?', '?x=y&'), 'GET')
    assert 'The persistent link you used is invalid' in str(exc_info.value)

    # invalid signature
    dummy_user.signing_secret = 'somethingelse'
    with pytest.raises(BadRequest) as exc_info:
        verify_signed_user_url(url, 'GET')
    assert 'The persistent link you used is invalid' in str(exc_info.value)


@pytest.mark.parametrize('args', ([1, 2], [2, 1]))
def test_verify_signed_user_url_lists(dummy_user, args):
    dummy_user.signing_secret = 'sixtynine'
    url = signed_url_for_user(dummy_user, 'core.contact', foo=args)
    assert verify_signed_user_url(url, 'GET') == dummy_user


def test_verify_signed_user_url_no_token():
    assert verify_signed_user_url('/contact', 'GET') is None


def test_verify_signed_user_url_bad_userid():
    with pytest.raises(BadRequest) as exc_info:
        verify_signed_user_url('/contact?user_token=x', 'GET')
    assert 'The persistent link you used is invalid' in str(exc_info.value)


def test_verify_signed_user_url_wrong_userid(dummy_user, create_user):
    # this test is a bit stupid, because the only way we can fail this
    # check is if two users have the same signing_secret AND someone
    # changes the user id at the beginning of the token
    user = create_user(123)
    user.signing_secret = dummy_user.signing_secret
    url = signed_url_for_user(dummy_user, 'core.contact')
    url = url.replace(f'user_token={dummy_user.id}', f'user_token={user.id}')
    with pytest.raises(BadRequest) as exc_info:
        verify_signed_user_url(url, 'GET')
    assert 'The persistent link you used is invalid' in str(exc_info.value)


def test_verify_signed_user_url_invalid_user(dummy_user):
    url = signed_url_for_user(dummy_user, 'core.contact')
    url = url.replace('user_token=', 'user_token=111')
    with pytest.raises(BadRequest) as exc_info:
        verify_signed_user_url(url, 'GET')
    assert 'The persistent link you used is invalid' in str(exc_info.value)


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('headers', ({}, {'Authorization': 'Basic foo'}))
def test_get_oauth_user_no_token(mocker, headers):
    request = mocker.patch('indico.web.util.request')
    request.headers = headers
    acquire_token = mocker.patch.object(IndicoResourceProtector, 'acquire_token')
    assert get_oauth_user('whatever') is None
    acquire_token.assert_not_called()


@pytest.mark.usefixtures('request_context')
def test_get_oauth_user_oauth_error(mocker):
    request = mocker.patch('indico.web.util.request')
    request.headers = {'Authorization': 'Bearer foo'}
    acquire_token = mocker.patch.object(IndicoResourceProtector, 'acquire_token')
    acquire_token.side_effect = InsufficientScopeError()
    with pytest.raises(IndicoAuthlibHTTPError) as exc_info:
        get_oauth_user('whatever')
    assert 'requires higher privileges than provided' in str(exc_info.value)
    acquire_token.assert_called_with('whatever')


@pytest.mark.usefixtures('request_context')
def test_get_oauth_user_oauth(mocker, dummy_user):
    request = mocker.patch('indico.web.util.request')
    request.headers = {'Authorization': 'Bearer foo'}
    acquire_token = mocker.patch.object(IndicoResourceProtector, 'acquire_token')
    acquire_token.return_value.user = dummy_user
    assert get_oauth_user('whatever') == dummy_user
    acquire_token.assert_called_with('whatever')


@pytest.mark.usefixtures('request_context')
def test_lookup_request_user_session(dummy_user):
    assert _lookup_request_user() == (None, None)
    session.set_session_user(dummy_user)
    assert _lookup_request_user() == (dummy_user, 'session')


@pytest.mark.usefixtures('request_context')
def test_lookup_request_user_signed_url(create_user, dummy_user, mocker):
    assert _lookup_request_user(True) == (None, None)
    mocker.patch('indico.web.util.verify_signed_user_url').return_value = dummy_user
    session.set_session_user(create_user(123))  # should be ignored
    assert _lookup_request_user(True) == (dummy_user, 'signed_url')


@pytest.mark.usefixtures('request_context')
def test_lookup_request_user_signed_url_not_allowed(create_user, dummy_user, mocker):
    assert _lookup_request_user(False) == (None, None)
    mocker.patch('indico.web.util.verify_signed_user_url').return_value = dummy_user
    with pytest.raises(BadRequest) as exc_info:
        _lookup_request_user(False)
    assert 'Signature auth is not allowed for this URL' in str(exc_info.value)


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize('method', ('GET', 'POST'))
def test_lookup_request_user_oauth(dummy_user, mocker, method):
    request = mocker.patch('indico.web.util.request')
    request.method = method
    request.full_path = '/test'
    request.headers = {}
    assert _lookup_request_user() == (None, None)
    get_oauth_user = mocker.patch('indico.web.util.get_oauth_user')
    get_oauth_user.return_value = dummy_user
    assert _lookup_request_user() == (dummy_user, 'oauth')
    scopes = ['read:everything', 'full:everything'] if method == 'GET' else ['full:everything']
    get_oauth_user.assert_called_with(scopes)


@pytest.mark.usefixtures('request_context')
def test_lookup_request_user_signed_url_oauth(dummy_user, mocker):
    assert _lookup_request_user() == (None, None)
    mocker.patch('indico.web.util.verify_signed_user_url').return_value = dummy_user
    mocker.patch('indico.web.util.get_oauth_user').return_value = dummy_user
    with pytest.raises(BadRequest) as exc_info:
        _lookup_request_user()
    assert 'OAuth tokens and signed URLs cannot be mixed' in str(exc_info.value)


@pytest.mark.usefixtures('request_context')
def test_lookup_request_user_session_oauth(dummy_user, mocker):
    assert _lookup_request_user() == (None, None)
    session.set_session_user(dummy_user)
    mocker.patch('indico.web.util.get_oauth_user').return_value = dummy_user
    with pytest.raises(BadRequest) as exc_info:
        _lookup_request_user()
    assert 'OAuth tokens and session cookies cannot be mixed' in str(exc_info.value)


@pytest.mark.usefixtures('request_context')
@pytest.mark.parametrize(('xhr', 'json', 'blueprint', 'expected'), (
    (False, False, 'assets', False),
    (True, False, 'assets', False),
    (False, True, 'assets', False),
    (True, True, 'assets', False),
    (False, False, 'foo', True),
    (True, False, 'foo', False),
    (False, True, 'foo', False),
    (True, True, 'foo', False),
))
def test_request_likely_seen_by_user(mocker, xhr, json, blueprint, expected):
    request = mocker.patch('indico.web.util.request')
    request.is_xhr = xhr
    request.is_json = json
    request.blueprint = blueprint
    assert _request_likely_seen_by_user() == expected


def test_check_request_user_no_user():
    assert _check_request_user(None, None) == (None, None)
    assert _check_request_user(None, 'foo') == (None, None)


@pytest.mark.parametrize('source', ('session', 'foo'))
def test_check_request_user(dummy_user, source):
    assert _check_request_user(dummy_user, source) == (dummy_user, source)


def test_check_request_user_blocked(mocker, dummy_user):
    _request_likely_seen_by_user = mocker.patch('indico.web.util._request_likely_seen_by_user', return_value=False)
    dummy_user.is_blocked = True
    with pytest.raises(Forbidden) as exc_info:
        _check_request_user(dummy_user, 'foo')
    assert 'User has been blocked' in str(exc_info.value)
    _request_likely_seen_by_user.assert_not_called()


@pytest.mark.usefixtures('request_context')
def test_check_request_user_blocked_session(mocker, dummy_user):
    session = mocker.patch('indico.web.util.session')
    flash = mocker.patch('indico.web.util.flash')
    _request_likely_seen_by_user = mocker.patch('indico.web.util._request_likely_seen_by_user')
    dummy_user.is_blocked = True

    # request not likely seen by the end user
    _request_likely_seen_by_user.return_value = False
    assert _check_request_user(dummy_user, 'session') == (None, None)
    session.clear.assert_not_called()
    flash.assert_not_called()

    # request likely seen by the user
    _request_likely_seen_by_user.return_value = True
    assert _check_request_user(dummy_user, 'session') == (None, None)
    session.clear.assert_called()
    flash.assert_called()
    assert 'Your profile has been blocked' in flash.call_args.args[0]


def test_check_request_user_deleted(mocker, dummy_user, create_user):
    _request_likely_seen_by_user = mocker.patch('indico.web.util._request_likely_seen_by_user', return_value=False)
    dummy_user.is_deleted = True

    # just deleted
    with pytest.raises(Forbidden) as exc_info:
        _check_request_user(dummy_user, 'foo')
    assert 'User has been deleted' in str(exc_info.value)
    _request_likely_seen_by_user.assert_not_called()

    # merged into another user
    dummy_user.merged_into_user = create_user(123)
    with pytest.raises(Forbidden) as exc_info:
        _check_request_user(dummy_user, 'foo')
    assert 'User has been merged into another user' in str(exc_info.value)
    _request_likely_seen_by_user.assert_not_called()


@pytest.mark.usefixtures('request_context')
def test_check_request_user_deleted_session(mocker, dummy_user):
    session = mocker.patch('indico.web.util.session')
    flash = mocker.patch('indico.web.util.flash')
    _request_likely_seen_by_user = mocker.patch('indico.web.util._request_likely_seen_by_user')
    dummy_user.is_deleted = True

    # request not likely seen by the end user
    _request_likely_seen_by_user.return_value = False
    assert _check_request_user(dummy_user, 'session') == (None, None)
    session.clear.assert_not_called()
    flash.assert_not_called()

    # request likely seen by the user
    _request_likely_seen_by_user.return_value = True
    assert _check_request_user(dummy_user, 'session') == (None, None)
    session.clear.assert_called()
    flash.assert_called()
    assert 'Your profile has been deleted' in flash.call_args.args[0]


@pytest.mark.usefixtures('request_context')
def test_check_request_user_deleted_merged_session(mocker, dummy_user, create_user):
    session = mocker.patch('indico.web.util.session')
    flash = mocker.patch('indico.web.util.flash')
    _request_likely_seen_by_user = mocker.patch('indico.web.util._request_likely_seen_by_user')
    dummy_user.is_deleted = True
    dummy_user.merged_into_user = create_user(123)

    # request not likely seen by the end user
    _request_likely_seen_by_user.return_value = False
    assert _check_request_user(dummy_user, 'session') == (None, None)
    session.clear.assert_not_called()
    flash.assert_not_called()

    # request likely seen by the user
    _request_likely_seen_by_user.return_value = True
    assert _check_request_user(dummy_user, 'session') == (None, None)
    session.clear.assert_called()
    flash.assert_called()
    assert 'Your profile has been merged into' in flash.call_args.args[0]


def test_get_request_user(dummy_user, mocker, monkeypatch):
    _lookup_request_user = mocker.patch('indico.web.util._lookup_request_user', return_value=(dummy_user, 'whatever'))
    monkeypatch.setattr('indico.web.util._check_request_user', lambda user, source: (user, source))
    assert get_request_user() == (dummy_user, 'whatever')
    _lookup_request_user.assert_called_once()
    assert get_request_user() == (dummy_user, 'whatever')
    assert _lookup_request_user.call_count == 2


def test_get_request_user_lookup_failure(mocker, monkeypatch):
    _lookup_request_user = mocker.patch('indico.web.util._lookup_request_user', side_effect=Exception('kaboom'))
    monkeypatch.setattr('indico.web.util._check_request_user', lambda user, source: (user, source))
    with pytest.raises(Exception) as exc_info:
        get_request_user()
    assert str(exc_info.value) == 'kaboom'
    _lookup_request_user.assert_called_once()
    # after a failure, we always return None
    assert get_request_user() == (None, None)
    # the lookup should not be done again once a failure is cached
    _lookup_request_user.assert_called_once()


def test_get_request_user_check_failure(dummy_user, mocker):
    _lookup_request_user = mocker.patch('indico.web.util._lookup_request_user', return_value=(dummy_user, 'whatever'))
    _check_request_user = mocker.patch('indico.web.util._check_request_user', side_effect=Exception('kaboom'))
    with pytest.raises(Exception) as exc_info:
        get_request_user()
    assert str(exc_info.value) == 'kaboom'
    _lookup_request_user.assert_called_once()
    _check_request_user.assert_called_once()
    # after a failure, we always return None
    assert get_request_user() == (None, None)
    # the lookup/check should not be done again once a failure is cached
    _lookup_request_user.assert_called_once()
    _check_request_user.assert_called_once()


def test_get_request_user_complete(dummy_user, app, test_client, dummy_token, dummy_personal_token, create_user):
    class RHTest(RH):
        def _process(self):
            user, source = get_request_user()
            assert session.user == user
            if not user:
                return 'none'
            return f'{user.id}|{source}'

    @allow_signed_url
    class RHTestSigned(RHTest):
        pass

    @oauth_scope('read:user')
    class RHTestScope(RHTest):
        pass

    app.add_url_rule('/test/default', 'test_default', make_view_func(RHTest), methods=('GET', 'POST'))
    app.add_url_rule('/test/signed', 'test_signed', make_view_func(RHTestSigned))
    app.add_url_rule('/test/scope', 'test_scope', make_view_func(RHTestScope), methods=('GET', 'POST'))

    # no auth
    assert test_client.get('/test/default').data == b'none'
    assert test_client.get('/test/signed').data == b'none'
    assert test_client.get('/test/scope').data == b'none'

    # signature auth
    resp = test_client.get(signed_url_for_user(dummy_user, 'test_default'))
    assert resp.status_code == 400
    assert b'Signature auth is not allowed for this URL' in resp.data

    resp = test_client.get(signed_url_for_user(dummy_user, 'test_signed'))
    assert resp.status_code == 200
    assert resp.data == b'1337|signed_url'

    resp = test_client.get(signed_url_for_user(dummy_user, 'test_scope'))
    assert resp.status_code == 400
    assert b'Signature auth is not allowed for this URL' in resp.data

    # personal oauth-like token - token with read:user scope
    personal_oauth_headers = {'Authorization': f'Bearer {dummy_personal_token._plaintext_token}'}
    resp = test_client.get('/test/default', headers=personal_oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.post('/test/default', headers=personal_oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.get('/test/signed', headers=personal_oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.get('/test/scope', headers=personal_oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    resp = test_client.post('/test/scope', headers=personal_oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    # oauth - token with read:user scope
    oauth_headers = {'Authorization': f'Bearer {dummy_token._plaintext_token}'}
    resp = test_client.get('/test/default', headers=oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.post('/test/default', headers=oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.get('/test/signed', headers=oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.get('/test/scope', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    resp = test_client.post('/test/scope', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    # oauth - token with read:everything scope
    dummy_token._scopes.append('read:everything')
    dummy_token.app_user_link.scopes.append('read:everything')
    dummy_token.app_user_link.application.allowed_scopes.append('read:everything')

    resp = test_client.get('/test/default', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    # default post requires full:everything
    resp = test_client.post('/test/default', headers=oauth_headers)
    assert resp.status_code == 403
    assert b'insufficient_scope' in resp.data

    resp = test_client.get('/test/signed', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    resp = test_client.get('/test/scope', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    # custom scopes are not method-specific
    resp = test_client.post('/test/scope', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    # full:everything should allow posting to any endpoint
    dummy_token._scopes.append('full:everything')
    dummy_token.app_user_link.scopes.append('full:everything')
    dummy_token.app_user_link.application.allowed_scopes.append('full:everything')

    resp = test_client.post('/test/default', headers=oauth_headers)
    assert resp.status_code == 200
    assert resp.data == b'1337|oauth'

    # personal token + signature is not allowed
    dummy_personal_token._scopes.append('read:everything')
    resp = test_client.get(signed_url_for_user(dummy_user, 'test_signed'), headers=personal_oauth_headers)
    assert resp.status_code == 400
    assert b'OAuth tokens and signed URLs cannot be mixed' in resp.data

    # oauth + signature is not allowed
    resp = test_client.get(signed_url_for_user(dummy_user, 'test_signed'), headers=oauth_headers)
    assert resp.status_code == 400
    assert b'OAuth tokens and signed URLs cannot be mixed' in resp.data

    # request with a user being set in the actual session (session cookies in the browser)
    with test_client.session_transaction() as sess:
        sess.set_session_user(create_user(123))

    assert test_client.get('/test/default').data == b'123|session'
    assert test_client.get('/test/signed').data == b'123|session'
    assert test_client.get('/test/scope').data == b'123|session'

    # personal token + session is not allowed
    resp = test_client.get('/test/default', headers=personal_oauth_headers)
    assert resp.status_code == 400
    assert b'OAuth tokens and session cookies cannot be mixed' in resp.data

    # oauth + session is not allowed
    resp = test_client.get('/test/default', headers=oauth_headers)
    assert resp.status_code == 400
    assert b'OAuth tokens and session cookies cannot be mixed' in resp.data

    # regular requests still need a CSRF token
    resp = test_client.post('/test/default')
    assert resp.status_code == 400
    assert b'problem with your current session' in resp.data

    # signed links override the session user
    resp = test_client.get(signed_url_for_user(dummy_user, 'test_signed'))
    assert resp.status_code == 200
    assert resp.data == b'1337|signed_url'


def test_get_request_user_nested_exceptions(mocker, app, test_client):
    process_called = False

    class RHFail(RH):
        def _process(self):
            nonlocal process_called
            process_called = True
            raise Exception('badaboom')

    app.add_url_rule('/test/fail', 'test_fail', make_view_func(RHFail))

    # page does not exist
    resp = test_client.get('/test/this-does-not-exist?user_token=garbage')
    assert resp.status_code == 404
    assert b'Not Found' in resp.data

    # existing page but invalid token, just making sure we never get into processing that
    resp = test_client.get('/test/fail?user_token=garbage')
    assert resp.status_code == 400
    assert b'The persistent link you used is invalid' in resp.data

    # random failure during authentication on an existing page
    mocker.patch('indico.web.util._lookup_request_user', side_effect=Exception('kaboom'))
    resp = test_client.get('/test/fail?user_token=garbage')
    assert resp.status_code == 500
    assert b'kaboom' in resp.data

    # random failure during authentication on 404ing page
    resp = test_client.get('/test/this-does-not-exist?user_token=garbage')
    assert resp.status_code == 404
    assert b'Not Found' in resp.data

    # none of the requests should have ended up in the RH
    assert not process_called
