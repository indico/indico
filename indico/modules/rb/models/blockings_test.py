# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime

import pytest

from indico.modules.rb.models.blockings import Blocking
from indico.testing.util import bool_matrix


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.mark.parametrize(('check_date', 'expected'), (
    ('2014-12-04', False),
    ('2014-12-05', True),
    ('2014-12-06', True),
    ('2014-12-07', True),
    ('2014-12-08', False),
))
def test_is_active_at(create_blocking, check_date, expected):
    start_date = date(2014, 12, 5)
    end_date = date(2014, 12, 7)
    check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
    blocking = create_blocking(start_date=start_date, end_date=end_date)
    assert blocking.is_active_at(check_date) == expected
    assert Blocking.find_first(Blocking.is_active_at(check_date)) == (blocking if expected else None)


def test_created_by_user(dummy_blocking, dummy_user, create_user):
    assert dummy_blocking.created_by_user == dummy_user
    other_user = create_user(123)
    dummy_blocking.created_by_user = other_user
    assert dummy_blocking.created_by_user == other_user


@pytest.mark.parametrize(('is_admin', 'is_creator', 'expected'), bool_matrix('..', expect=any))
def test_can_edit_delete(dummy_blocking, create_user, is_admin, is_creator, expected):
    user = create_user(123, rb_admin=is_admin)
    if is_creator:
        dummy_blocking.created_by_user = user
    assert dummy_blocking.can_edit(user) == expected
    assert dummy_blocking.can_delete(user) == expected


@pytest.mark.parametrize(
    ('is_creator', 'is_admin', 'has_room', 'is_room_owner', 'expected'),
    bool_matrix('!00..', expect=True) +         # creator or admin
    bool_matrix(' 00..', expect='all_dynamic')  # room owner
)
def test_can_override(dummy_room, dummy_blocking, create_user,
                      is_creator, is_admin, has_room, is_room_owner, expected):
    user = create_user(123, rb_admin=is_admin)
    if is_room_owner:
        dummy_room.update_principal(user, full_access=True)
    if is_creator:
        dummy_blocking.created_by_user = user
    assert dummy_blocking.can_override(user, dummy_room if has_room else None) == expected


@pytest.mark.parametrize(
    ('is_creator', 'is_admin', 'has_room', 'is_room_owner', 'expected'),
    bool_matrix('1...', expect=True) +
    bool_matrix('0...', expect=False)
)
def test_can_override_explicit_only(dummy_room, dummy_blocking, create_user,
                                    is_creator, is_admin, has_room, is_room_owner, expected):
    user = create_user(123, rb_admin=is_admin)
    if is_room_owner:
        dummy_room.update_principal(user, full_access=True)
    if is_creator:
        dummy_blocking.created_by_user = user
    assert dummy_blocking.can_override(user, dummy_room if has_room else None, explicit_only=True) == expected


@pytest.mark.parametrize(('in_acl', 'expected'), (
    ('user',  True),
    ('group', True),
    (False,   False)
))
def test_can_override_acl(dummy_blocking, dummy_user, create_user, dummy_group, in_acl, expected):
    user = create_user(123, groups={dummy_group})
    dummy_blocking.allowed = {dummy_user}
    if in_acl == 'user':
        dummy_blocking.allowed.add(user)
    elif in_acl == 'group':
        dummy_blocking.allowed.add(dummy_group)
    assert dummy_blocking.can_override(user) == expected


def test_can_no_user(dummy_blocking):
    assert not dummy_blocking.can_edit(None)
    assert not dummy_blocking.can_delete(None)
    assert not dummy_blocking.can_override(None)
