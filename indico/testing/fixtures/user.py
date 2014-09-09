## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import pytest

from indico.testing.mocks import MockAvatar, MockAvatarHolder
from MaKaC.user import AvatarHolder


@pytest.yield_fixture
def create_user(monkeypatch_methods):
    """Returns a callable which lets you create dummy users"""
    monkeypatch_methods('MaKaC.user.AvatarHolder', MockAvatarHolder)

    _avatars = []
    ah = AvatarHolder()

    def _create_user(id_, name='Pig', surname='Guinea', rb_admin=False, **kwargs):
        email = kwargs.get('email', '{}@example.com'.format(id_))
        avatar = MockAvatar()
        avatar.id = id_
        avatar.name = name
        avatar.surname = surname
        avatar.email = email
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
