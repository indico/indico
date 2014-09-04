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
def create_location(db):
    """Returns a callable which lets you create locations"""

    def _create_location(**params):
        location = Location(**params)
        db.session.add(location)
        db.session.flush()
        return location

    return _create_location


@pytest.fixture
def dummy_location(db, create_location):
    """Gives you a dummy default location"""
    loc = create_location(name='Test')
    loc.set_default()
    db.session.flush()
    return loc


@pytest.fixture
def create_room(db, dummy_location, dummy_user):
    """Returns a callable which lets you create rooms"""

    def _create_room(**params):
        params.setdefault('building', '1')
        params.setdefault('floor', '2')
        params.setdefault('number', '3')
        params.setdefault('name', '')
        params.setdefault('owner_id', dummy_user.id)
        params.setdefault('location', dummy_location)
        room = Room(**params)
        room.update_name()
        db.session.add(room)
        db.session.flush()
        return room

    return _create_room


@pytest.fixture
def dummy_room(create_room):
    """Gives you a dummy room"""
    return create_room()
