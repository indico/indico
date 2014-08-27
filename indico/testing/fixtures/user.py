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
def dummy_user_factory(monkeypatch_methods):
    """Returns a callable which lets you create dummy users"""
    monkeypatch_methods('MaKaC.user.AvatarHolder', MockAvatarHolder)

    _avatars = []
    ah = AvatarHolder()

    def _dummy_user_factory(id_):
        avatar = MockAvatar()
        avatar.id = id_
        ah.add(avatar)
        _avatars.append(avatar)
        return avatar

    yield _dummy_user_factory

    for avatar in _avatars:
        ah.remove(avatar)


@pytest.fixture
def dummy_user(dummy_user_factory):
    """Creates a mocked dummy avatar"""
    return dummy_user_factory('dummy')
