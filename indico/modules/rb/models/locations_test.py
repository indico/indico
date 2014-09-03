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

from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.rooms import Room


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_getLocator(dummy_location):
    assert dummy_location.getLocator() == {'locationId': dummy_location.name}


def test_is_map_available(dummy_location, db):
    assert not dummy_location.is_map_available
    dummy_location.aspects.append(Aspect(name='Test', center_latitude='', center_longitude='', zoom_level=0,
                                         top_left_latitude=0, top_left_longitude=0, bottom_right_latitude=0,
                                         bottom_right_longitude=0))
    db.session.flush()
    assert dummy_location.is_map_available


def test_default_location(dummy_location, create_location):
    assert Location.default_location == dummy_location
    create_location(name='Foo')  # should not change the default
    assert Location.default_location == dummy_location


def test_set_default(dummy_location, create_location):
    assert dummy_location.is_default
    other_location = create_location(name='Foo')
    assert not other_location.is_default
    other_location.set_default()
    assert other_location.is_default
    assert not dummy_location.is_default
    # Make sure calling it again does not flip the default state
    other_location.set_default()
    assert other_location.is_default
    assert not dummy_location.is_default
    assert Location.default_location == other_location


def test_get_attribute_by_name(db, dummy_location):
    assert dummy_location.get_attribute_by_name('foo') is None
    attr = RoomAttribute(name='foo', title='foo', type='str', is_required=False, is_hidden=False)
    dummy_location.attributes.append(attr)
    db.session.flush()
    assert dummy_location.get_attribute_by_name('foo') == attr
    assert dummy_location.get_attribute_by_name('bar') is None


def test_get_equipment_by_name(db, dummy_location):
    assert dummy_location.get_equipment_by_name('foo') is None
    eq = EquipmentType(name='foo')
    dummy_location.equipment_types.append(eq)
    db.session.flush()
    assert dummy_location.get_equipment_by_name('foo') == eq
    assert dummy_location.get_equipment_by_name('bar') is None


def test_get_buildings(db, dummy_location, dummy_user, create_room, dummy_room):
    assert dummy_room.longitude is None
    assert dummy_room.latitude is None
    assert not dummy_location.get_buildings()  # no buildings with coordinates
    create_room(building='111', floor='1', number='1', name='', owner_id=dummy_user.id, longitude=1.23, latitude=4.56)
    create_room(building='111', floor='1', number='2', name='', owner_id=dummy_user.id, longitude=1.23, latitude=4.56)
    create_room(building='222', floor='1', number='1', name='', owner_id=dummy_user.id, longitude=1.3, latitude=3.7)
    create_room(building='222', floor='1', number='1', name='', owner_id=dummy_user.id)
    db.session.flush()
    buildings = dummy_location.get_buildings()
    for building in buildings:
        rooms = Room.find_all(building=building['number'])
        assert {r['id'] for r in building['rooms']} == {r.id for r in rooms}
        assert any(r.latitude and r.longitude for r in rooms)  # at least one room in the building needs coordinates
        for room in rooms:
            assert building['number'] == room.building
            if room.longitude and room.latitude:
                assert building['longitude'] == room.longitude
                assert building['latitude'] == room.latitude
