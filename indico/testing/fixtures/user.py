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

import pytest

from indico.testing.mocks import MockAvatar, MockAvatarHolder, MockGroupHolder, MockGroup
from MaKaC.user import AvatarHolder, GroupHolder


@pytest.yield_fixture
def create_user(monkeypatch_methods):
    """Returns a callable which lets you create dummy users"""
    monkeypatch_methods('MaKaC.user.AvatarHolder', MockAvatarHolder)

    _avatars = []
    ah = AvatarHolder()

    def _create_user(id_, name='Pig', surname='Guinea', rb_admin=False, email=None, groups=None):
        avatar = MockAvatar()
        avatar.id = id_
        avatar.name = name
        avatar.surname = surname
        avatar.email = email or '{}@example.com'.format(id_)
        avatar.groups = groups or set()
        avatar.rb_admin = rb_admin
        ah.add(avatar)
        _avatars.append(avatar)
        return avatar

    yield _create_user

    for avatar in _avatars:
        ah.remove(avatar)


@pytest.fixture
def dummy_user(create_user):
    """Creates a mocked dummy avatar"""
    return create_user('dummy')


@pytest.yield_fixture
def create_group(monkeypatch_methods):
    """Returns a callable which lets you create dummy groups"""
    monkeypatch_methods('MaKaC.user.GroupHolder', MockGroupHolder)

    _groups = []
    gh = GroupHolder()

    def _create_group(id_):
        group = MockGroup()
        group.id = id_
        gh.add(group)
        _groups.append(group)
        return group

    yield _create_group

    for group in _groups:
        gh.remove(group)


@pytest.fixture
def dummy_group(create_group):
    """Creates a mocked dummy group"""
    return create_group('dummy')
