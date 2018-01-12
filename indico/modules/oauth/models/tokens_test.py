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

from indico.modules.oauth.models.tokens import OAuthGrant


pytest_plugins = 'indico.modules.oauth.testing.fixtures'


@pytest.fixture
def create_grant(dummy_user):
    def _create_grant_token(**params):
        params.setdefault('client_id', str(uuid4()))
        params.setdefault('code', 'foobar')
        params.setdefault('redirect_uri', 'http://localhost:5000')
        params.setdefault('user', dummy_user)
        params.setdefault('scopes', 'api')
        params.setdefault('expires', datetime.utcnow() + timedelta(seconds=120))
        grant = OAuthGrant(**params)
        return grant
    return _create_grant_token


@pytest.fixture
def dummy_grant(create_grant):
    return create_grant()


# -- OAuthToken tests ----------------------------------------------------------

def test_token_locator(dummy_token):
    assert dummy_token.locator == {'id': dummy_token.id}


def test_token_expires(dummy_token):
    assert dummy_token.expires is None


def test_token_scopes(dummy_token):
    assert dummy_token.scopes == set(dummy_token._scopes)
    new_scopes = ['c', 'b', 'a']
    dummy_token.scopes = new_scopes
    assert dummy_token._scopes == sorted(new_scopes)
    assert dummy_token.scopes == set(new_scopes)


def test_token_type(dummy_token):
    assert dummy_token.type == 'bearer'


# -- OAuthGrant tests ----------------------------------------------------------

def test_grant_key(mocker, dummy_grant):
    mocker.patch.object(OAuthGrant, 'make_key')
    dummy_grant.key
    OAuthGrant.make_key.assert_called_with(dummy_grant.client_id, dummy_grant.code)


def test_grant_ttl(freeze_time, dummy_grant):
    freeze_time(datetime.utcnow())
    ttl = dummy_grant.expires - datetime.utcnow()
    assert dummy_grant.ttl == ttl


def test_grant_get(mocker):
    mocker.patch.object(OAuthGrant, '_cache')
    client_id = str(uuid4())
    code = 'foobar'
    OAuthGrant.get(client_id, code)
    key = OAuthGrant.make_key(client_id, code)
    OAuthGrant._cache.get.assert_called_with(key)


def test_grant_make_key():
    client_id = str(uuid4())
    code = 'foobar'
    key = '{}:{}'.format(client_id, code)
    assert OAuthGrant.make_key(client_id, code) == key


def test_grant_delete(mocker, dummy_grant):
    mocker.patch.object(OAuthGrant, '_cache')
    dummy_grant.delete()
    OAuthGrant._cache.delete.assert_called_with(dummy_grant.key)


def test_grant_save(freeze_time, mocker, dummy_grant):
    freeze_time(datetime.utcnow())
    mocker.patch.object(OAuthGrant, '_cache')
    dummy_grant.save()
    OAuthGrant._cache.set.assert_called_with(key=dummy_grant.key, val=dummy_grant, time=dummy_grant.ttl)
