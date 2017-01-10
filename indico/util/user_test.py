# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from mock import MagicMock

from indico.modules.groups import GroupProxy
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.users import User
from indico.util.user import iter_acl, unify_user_args


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


def test_unify_user_args_new(dummy_avatar):
    avatar = dummy_avatar
    user = dummy_avatar.user

    @unify_user_args
    def fn(a, b, c, d, e, f):
        # posargs
        assert a == 'foo'
        assert b == user
        assert c == user
        # kwargs
        assert d == 'bar'
        assert e == user
        assert f == user

    fn('foo', user, avatar, d='bar', e=user, f=avatar)


def test_unify_user_args_legacy(dummy_avatar):
    avatar = dummy_avatar
    user = dummy_avatar.user

    @unify_user_args(legacy=True)
    def fn(a, b, c, d, e, f):
        # posargs
        assert a == 'foo'
        assert b == avatar
        assert c == avatar
        # kwargs
        assert d == 'bar'
        assert e == avatar
        assert f == avatar

    fn('foo', user, avatar, d='bar', e=user, f=avatar)
