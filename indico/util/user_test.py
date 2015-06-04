# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.util.user import iter_acl, unify_user_args


def test_iter_acl():
    user = MagicMock(is_group=False, spec=['is_group'])
    local_group = MagicMock(is_group=True, is_local=True)
    remote_group = MagicMock(is_group=True, is_local=False)
    acl = [remote_group, user, local_group]
    assert list(iter_acl(iter(acl))) == [user, local_group, remote_group]


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
