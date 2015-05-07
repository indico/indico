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

from indico.util.user import unify_user_args


def test_unify_user_args_new(dummy_user):
    avatar = dummy_user
    user = dummy_user.user

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


def test_unify_user_args_legacy(dummy_user):
    avatar = dummy_user
    user = dummy_user.user

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
