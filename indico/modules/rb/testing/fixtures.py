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

from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room


@pytest.fixture
def test_location(db):
    loc = Location(name='Test')
    db.session.add(loc)
    return loc


@pytest.fixture
def create_room(db, test_location):
    def _create_room(**params):
        room = Room(location=test_location, **params)
        room.update_name()
        db.session.add(room)
        db.session.flush()
        return room

    return _create_room


@pytest.fixture
def test_room(db, create_room, dummy_user):
    room = create_room(building='123', floor='4', number='56', name='', owner_id=dummy_user.id)
    db.session.add(room)
    db.session.flush()
    return room
