# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from mock import MagicMock

from indico.modules.groups import GroupProxy
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.users import User
from indico.util.user import iter_acl


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
