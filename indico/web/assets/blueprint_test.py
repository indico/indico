# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest


@pytest.fixture
def mock_js_vars(mocker):
    mocker.patch('indico.web.assets.blueprint.generate_global_file',
                 return_value='var Indico = {};')
    mocker.patch('indico.web.assets.blueprint.generate_user_file',
                 return_value='Indico.User = {};')


def test_js_vars_global_cache_control(test_client, mock_js_vars):
    resp = test_client.get('/assets/js-vars/global.js')
    assert resp.status_code == 200
    assert resp.cache_control.private


def test_js_vars_user_cache_control(test_client, mock_js_vars):
    resp = test_client.get('/assets/js-vars/user.js')
    assert resp.status_code == 200
    assert resp.cache_control.private
