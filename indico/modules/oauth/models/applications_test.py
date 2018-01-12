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

import pytest


pytest_plugins = 'indico.modules.oauth.testing.fixtures'


def test_client_type(dummy_application):
    assert dummy_application.client_type == 'public'


@pytest.mark.parametrize(('redirect_uris', 'expected'), (
    (None,       None),
    (['a'],      'a'),
    (['a', 'b'], 'a'),
))
def test_default_redirect_uri(dummy_application, redirect_uris, expected):
    dummy_application.redirect_uris = redirect_uris
    assert dummy_application.default_redirect_uri == expected


def test_locator(dummy_application):
    assert dummy_application.locator == {'id': dummy_application.id}


def test_reset_client_secret(dummy_application):
    initial_client_secret = dummy_application.client_secret
    dummy_application.reset_client_secret()
    assert dummy_application.client_secret != initial_client_secret


@pytest.mark.parametrize(('redirect_uris', 'to_validate', 'validates'), (
    ([],                                            'https://test.com',       False),
    (['https://test.com'],                          'https://test.com',       True),
    (['https://test.com'],                          'http://test.com',        False),
    (['https://test.com'],                          'https://scam.com',       False),
    (['https://test.com/'],                         'https://test.com',       False),
    (['https://test.com/'],                         'https://test.com/',      True),
    (['https://test.com/'],                         'https://test.com/?id=1', True),
    (['https://test.com/a'],                        'https://test.com/a/b',   True),
    (['https://test.com/a/b'],                      'https://test.com/a',     False),
    (['https://test.com/a/b', 'https://test2.com'], 'https://test2.com',      True),
))
def test_validate_redirect_uri(dummy_application, redirect_uris, to_validate, validates):
    dummy_application.redirect_uris = redirect_uris
    assert dummy_application.validate_redirect_uri(to_validate) == validates
