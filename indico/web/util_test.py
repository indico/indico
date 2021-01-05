# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest

from indico.web.util import is_signed_url_valid, signed_url_for


@pytest.mark.usefixtures('request_context')
def test_signing_url(dummy_user):
    dummy_user.signing_secret = 'sixtyten'
    url = signed_url_for(dummy_user, 'users.user_dashboard', url_params={'user_id': '70'})
    assert url == '/user/70/dashboard/?token=6bO-FgjAvYPiZ8Uft5_DmOC4Oow'
    url = signed_url_for(dummy_user, 'users.user_dashboard', url_params={'user_id': '71'}, q='roygbiv')
    assert url == '/user/71/dashboard/?q=roygbiv&token=YNgcXP02LpIYCWMAN80xXg6l6jM'


@pytest.mark.usefixtures('request_context')
def test_checking_signature(dummy_user):
    dummy_user.signing_secret = 'sixtyten'
    assert is_signed_url_valid(dummy_user, '/user/71/dashboard/?q=roygbiv&token=YNgcXP02LpIYCWMAN80xXg6l6jM')
    assert not is_signed_url_valid(dummy_user, '/user/71/dashboard/?q=roygbeef&token=YNgcXP02LpIYCWMAN80xXg6l6jM')
    assert not is_signed_url_valid(dummy_user, '/user/71/dashboard/?q=roygbiv&token=ZNgcXP02LpIYCWMAN80xXg6l6jM')
    assert not is_signed_url_valid(dummy_user, '/user/71/dashboard/?q=roygbiv')


@pytest.mark.usefixtures('request_context')
def test_full_urls(dummy_user):
    dummy_user.signing_secret = 'aquarius'
    url = signed_url_for(dummy_user, 'users.user_dashboard', url_params={'user_id': '71'}, _external=True)
    assert url == 'http://localhost/user/71/dashboard/?token=OsONJbxTpPzUYtSxgykZP7NZUHg'
    assert is_signed_url_valid(dummy_user, url)
    # the hostname part, etc... shouldn't be included in the signature
    assert is_signed_url_valid(dummy_user, 'http://indico.test/user/71/dashboard/?token=OsONJbxTpPzUYtSxgykZP7NZUHg')
