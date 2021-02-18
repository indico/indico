# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

pytest_plugins = 'indico.core.oauth.testing.fixtures'


def test_token_locator(dummy_token):
    assert dummy_token.locator == {'id': dummy_token.id}


def test_token_expires(dummy_token):
    assert dummy_token.get_expires_in() == 0


def test_token_scopes(dummy_token):
    assert dummy_token.scopes == set(dummy_token._scopes)
    new_scopes = ['c', 'b', 'a']
    dummy_token.scopes = new_scopes
    assert dummy_token._scopes == sorted(new_scopes)
    assert dummy_token.scopes == set(new_scopes)
