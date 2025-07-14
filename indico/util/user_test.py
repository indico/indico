# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import MagicMock

import pytest
from itsdangerous import BadSignature

from indico.modules.groups import GroupProxy
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.users import User
from indico.util.user import iter_acl, principal_from_identifier


def test_iter_acl():
    user = User()
    user_p = MagicMock(principal=user, spec=['principal'])
    ipn = IPNetworkGroup()
    ipn_p = MagicMock(principal=ipn, spec=['principal'])
    local_group = GroupProxy(123, _group=MagicMock())
    local_group_p = MagicMock(principal=local_group, spec=['principal'])
    remote_group = GroupProxy('foo', 'bar')
    remote_group_p = MagicMock(principal=remote_group, spec=['principal'])
    acl = [ipn, user_p, remote_group, local_group_p, user, local_group, remote_group_p, ipn_p]
    assert list(iter_acl(iter(acl))) == [user_p, user,
                                         ipn, ipn_p,
                                         local_group_p, local_group,
                                         remote_group, remote_group_p]


def test_principal_from_identifier_users(dummy_user, create_user):
    other_user = create_user(123)
    zero_user = create_user(0)
    assert principal_from_identifier(dummy_user.identifier) == dummy_user
    assert principal_from_identifier(other_user.identifier) == other_user
    assert principal_from_identifier(zero_user.identifier) == zero_user
    assert principal_from_identifier(dummy_user.identifier, require_user_token=False) == dummy_user
    assert principal_from_identifier(dummy_user.persistent_identifier, require_user_token=False) == dummy_user
    # missing signature
    with pytest.raises(ValueError):
        principal_from_identifier(dummy_user.persistent_identifier)
    # nonsense
    with pytest.raises(ValueError):
        principal_from_identifier('User:meow')
    with pytest.raises(ValueError):
        principal_from_identifier('User:meow:woof')
    # garbage signature
    with pytest.raises(BadSignature):
        principal_from_identifier(f'{dummy_user.persistent_identifier}:meow')
    # signature for different user
    sig = other_user.identifier.split(':')[-1]
    with pytest.raises(ValueError):
        principal_from_identifier(f'{dummy_user.persistent_identifier}:{sig}')
