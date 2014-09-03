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


pytest_plugins = 'indico.modules.rb.testing.fixtures'


class TestRoom:
    def test_owner(self, dummy_room, dummy_user):
        assert dummy_room.owner.id == dummy_user.id

    def test_full_name(self, dummy_room):
        assert dummy_room.full_name == '123-4-56'
        dummy_room.name = 'Test'
        assert dummy_room.full_name == '123-4-56 - Test'
