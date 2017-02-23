# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.locations import Location


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_locator(dummy_location):
    assert dummy_location.locator == {'locationId': dummy_location.name}


def test_is_map_available(dummy_location, db):
    assert not dummy_location.is_map_available
    dummy_location.aspects.append(Aspect(name=u'Test', center_latitude=u'', center_longitude=u'', zoom_level=0,
                                         top_left_latitude=0, top_left_longitude=0, bottom_right_latitude=0,
                                         bottom_right_longitude=0))
    db.session.flush()
    assert dummy_location.is_map_available


def test_default_location(create_location):
    assert Location.default_location is None
    location = create_location(u'Foo', is_default=True)
    assert Location.default_location == location
    create_location(name=u'Bar')  # should not change the default
    assert Location.default_location == location


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


def test_get_attribute_by_name(dummy_location, create_room_attribute):
    assert dummy_location.get_attribute_by_name(u'foo') is None
    attr = create_room_attribute(u'foo')
    assert dummy_location.get_attribute_by_name(u'foo') == attr
    assert dummy_location.get_attribute_by_name(u'bar') is None


def test_get_equipment_by_name(dummy_location, create_equipment_type):
    assert dummy_location.get_equipment_by_name(u'foo') is None
    eq = create_equipment_type(u'foo')
    assert dummy_location.get_equipment_by_name(u'foo') == eq
    assert dummy_location.get_equipment_by_name(u'bar') is None


def test_get_buildings(db, dummy_location, create_room):
    room = create_room()
    assert len(dummy_location.rooms) == 1
    assert room.longitude is None
    assert room.latitude is None
    assert not dummy_location.get_buildings()  # no buildings with coordinates
    create_room(building=u'111', longitude=1.23, latitude=4.56)
    create_room(building=u'111', longitude=1.23, latitude=4.56)
    create_room(building=u'222', longitude=1.3, latitude=3.7)
    create_room(building=u'222')
    db.session.flush()
    buildings = dummy_location.get_buildings()
    assert buildings
    for building in buildings:
        rooms = [r for r in dummy_location.rooms if r.building == building['number']]
        assert {r['id'] for r in building['rooms']} == {r.id for r in rooms}
        assert any(r.latitude and r.longitude for r in rooms)  # at least one room in the building needs coordinates
        for room in rooms:
            assert building['number'] == room.building
            if room.longitude and room.latitude:
                assert building['longitude'] == room.longitude
                assert building['latitude'] == room.latitude
