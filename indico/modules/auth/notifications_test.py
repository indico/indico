# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from datetime import datetime
from pathlib import Path

import pytest
from pytz import utc

from indico.core.config import config
from indico.testing.util import assert_email_snapshot
from indico.web.flask.templating import get_template_module


def _assert_snapshot(snapshot, template_name, *, has_alternatives=False, **context):
    __tracebackhide__ = True
    template = get_template_module(f'auth/emails/{template_name}', **context)
    name, ext = os.path.splitext(template_name)
    alternatives_suffix = '_alternatives' if has_alternatives else ''
    usernames_suffix = '' if config.LOCAL_USERNAMES else '_nousernames'
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    assert_email_snapshot(snapshot, template, f'{name}{alternatives_suffix}{usernames_suffix}{ext}')


@pytest.fixture
def alternatives(request):
    if not request.param:
        return []
    return [
        {'name': 'SSO', 'identifier': 'foo.bar', 'last_login_dt': datetime(2025, 1, 9, 13, 37, tzinfo=utc)},
        {'name': 'Something', 'identifier': 'foo@bar', 'last_login_dt': datetime(2024, 12, 24, 12, 0, tzinfo=utc)},
    ]


@pytest.mark.usefixtures('request_context')  # need to access session tzinfo for date format
@pytest.mark.parametrize('alternatives', (False, True), indirect=True)
@pytest.mark.parametrize('local_usernames', (False, True))
def test_reset_password_email(patch_indico_config, snapshot, dummy_user, alternatives, local_usernames):
    patch_indico_config('LOCAL_USERNAMES', local_usernames)
    _assert_snapshot(snapshot, 'reset_password.txt', has_alternatives=bool(alternatives),
                     user=dummy_user, username='foobar', alternatives=alternatives, url='<link>')


@pytest.mark.usefixtures('request_context')  # need to access session tzinfo for date format
@pytest.mark.parametrize('alternatives', (False, True), indirect=True)
@pytest.mark.parametrize('local_usernames', (False, True))
def test_create_local_identity_email(patch_indico_config, snapshot, dummy_user, alternatives, local_usernames):
    patch_indico_config('LOCAL_USERNAMES', local_usernames)
    _assert_snapshot(snapshot, 'create_local_identity.txt', has_alternatives=bool(alternatives),
                     user=dummy_user, alternatives=alternatives, url='<link>')
