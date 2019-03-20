# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_locator(dummy_location):
    assert dummy_location.locator == {'locationId': dummy_location.name}


def test_default_location(create_location):
    assert Location.default_location is None
    location = create_location(u'Foo', is_default=True)
    assert Location.default_location == location
    create_location(name=u'Bar')  # should not change the default
    assert Location.default_location == location


def test_room_name_format(create_location, create_room, db, dummy_user):
    location = create_location(u'Foo', is_default=True)
    location.room_name_format = '{building}|{floor}|{number}'
    assert location._room_name_format == '%1$s|%2$s|%3$s'

    Room(building=1, floor=2, number=3, verbose_name='First amphitheater', location=location, owner=dummy_user)
    Room(building=1, floor=3, number=4, verbose_name='Second amphitheater', location=location, owner=dummy_user)
    Room(building=1, floor=2, number=4, verbose_name='Room 3', location=location, owner=dummy_user)
    db.session.flush()
    assert Room.query.filter(Room.full_name.contains('|3')).count() == 2


def test_set_default(create_location):
    location = create_location(u'Foo')
    other_location = create_location(u'Bar')
    assert not location.is_default
    assert not other_location.is_default
    location.set_default()
    assert location.is_default
    assert not other_location.is_default
    assert Location.default_location == location
    # Make sure calling it again does not flip the default state
    location.set_default()
    assert location.is_default
    assert not other_location.is_default
    # Change the default
    other_location.set_default()
    assert not location.is_default
    assert other_location.is_default
