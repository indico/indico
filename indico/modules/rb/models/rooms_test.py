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


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_owner(dummy_room, dummy_user):
    assert dummy_room.owner.id == dummy_user.id
    dummy_room.owner_id = 'xxx'
    assert dummy_room.owner is None


@pytest.mark.parametrize(('room_args', 'expected_name'), (
    ({}, u'1-2-3'),
    ({'building': u'X'}, u'X-2-3'),
    ({'name': u'Test'}, u'1-2-3 - Test'),
    ({'name': u'm\xf6p'}, u'1-2-3 - m\xf6p')
))
def test_full_name(create_room, room_args, expected_name):
    room = create_room(**room_args)
    assert room.full_name == expected_name
