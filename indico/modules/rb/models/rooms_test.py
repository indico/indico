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

from operator import itemgetter

import pytest

from indico.modules.rb.models.rooms import Room


pytest_plugins = 'indico.modules.rb.testing.fixtures'
_notset = object()


def test_is_auto_confirm(create_room, bool_flag):
    room = create_room(reservations_need_confirmation=bool_flag)
    assert room.is_auto_confirm != bool_flag
    assert Room.find_first(is_auto_confirm=bool_flag) is None
    assert Room.find_first(is_auto_confirm=not bool_flag) == room


def test_booking_url(dummy_room):
    assert Room().booking_url is None
    assert dummy_room.booking_url is not None


def test_details_url(dummy_room):
    assert Room().details_url is None
    assert dummy_room.details_url is not None


def test_large_photo_url(dummy_room):
    assert Room().large_photo_url is None
    assert dummy_room.large_photo_url is not None


def test_small_photo_url(dummy_room):
    assert Room().small_photo_url is None
    assert dummy_room.small_photo_url is not None


def test_has_photo(dummy_room):
    assert not dummy_room.has_photo
    dummy_room.photo_id = 0
    assert dummy_room.has_photo


@pytest.mark.parametrize(('building', 'floor', 'number', 'name', 'expected_name'), (
    (u'1', u'2', u'3', u'',       u'1-2-3'),
    (u'1', u'2', u'X', u'',       u'1-2-X'),
    (u'1', u'X', u'3', u'',       u'1-X-3'),
    (u'X', u'2', u'3', u'',       u'X-2-3'),
    (u'1', u'2', u'3', u'Test',   u'1-2-3 - Test'),
    (u'1', u'2', u'3', u'm\xf6p', u'1-2-3 - m\xf6p')
))
def test_full_name(create_room, building, floor, number, name, expected_name):
    room = create_room(building=building, floor=floor, number=number, name=name)
    assert room.full_name == expected_name


@pytest.mark.parametrize(('name', 'expected'), (
    (u'',      False),
    (u'1-2-3', False),
    (u'Test',  True),
))
def test_has_special_name(create_room, name, expected):
    room = create_room(name=name)
    assert room.has_special_name == expected


@pytest.mark.parametrize(('value', 'expected'), (
    (u'foo', True),
    (u'',    False)
))
def test_has_booking_groups(create_room_attribute, dummy_room, value, expected):
    create_room_attribute(u'allowed-booking-group')
    assert not dummy_room.has_booking_groups
    dummy_room.set_attribute_value(u'allowed-booking-group', value)
    assert dummy_room.has_booking_groups == expected


def test_has_projector(create_equipment_type, dummy_room, db):
    assert not dummy_room.has_projector
    dummy_room.available_equipment.append(create_equipment_type(u'Computer Projector'))
    db.session.flush()
    assert dummy_room.has_projector


def test_has_webcast_recording(create_equipment_type, dummy_room, db):
    assert not dummy_room.has_webcast_recording
    dummy_room.available_equipment.append(create_equipment_type(u'Webcast/Recording'))
    db.session.flush()
    assert dummy_room.has_webcast_recording


def test_has_vc(create_equipment_type, dummy_room, db):
    assert not dummy_room.has_vc
    dummy_room.available_equipment.append(create_equipment_type(u'Video conference'))
    db.session.flush()
    assert dummy_room.has_vc


@pytest.mark.parametrize(('reservable', 'booking_group', 'expected'), (
    (True,  u'',    True),
    (True,  u'foo', False),
    (False, u'',    False),
    (False, u'foo', False)
))
def test_is_public(create_room_attribute, dummy_room, reservable, booking_group, expected):
    create_room_attribute(u'allowed-booking-group')
    dummy_room.set_attribute_value(u'allowed-booking-group', booking_group)
    dummy_room.is_reservable = reservable
    assert dummy_room.is_public == expected


@pytest.mark.parametrize(('is_reservable', 'reservations_need_confirmation', 'booking_group', 'expected_kind'), (
    (False, False, u'foo', u'privateRoom'),
    (False, True,  u'foo', u'privateRoom'),
    (True,  False, u'foo', u'privateRoom'),
    (True,  True,  u'foo', u'privateRoom'),
    (False, False, u'',    u'privateRoom'),
    (False, True,  u'',    u'privateRoom'),
    (True,  False, u'',    u'basicRoom'),
    (True,  True,  u'',    u'moderatedRoom')
))
def test_kind(create_room, create_room_attribute,
              is_reservable, reservations_need_confirmation, booking_group, expected_kind):
    room = create_room(is_reservable=is_reservable, reservations_need_confirmation=reservations_need_confirmation)
    create_room_attribute(u'allowed-booking-group')
    room.set_attribute_value(u'allowed-booking-group', booking_group)
    assert room.kind == expected_kind


def test_location_name(dummy_room, dummy_location):
    assert dummy_room.location_name == dummy_location.name


@pytest.mark.parametrize(('capacity', 'is_reservable', 'reservations_need_confirmation', 'has_vc', 'expected'), (
    (1, False, True,  False, u'1 person, private, needs confirmation'),
    (2, False, True,  False, u'2 people, private, needs confirmation'),
    (2, True,  True,  False, u'2 people, public, needs confirmation'),
    (2, False, False, False, u'2 people, private, auto-confirmation'),
    (2, False, True,  True,  u'2 people, private, needs confirmation, video conference')
))
def test_marker_description(db, create_room, create_equipment_type,
                            capacity, is_reservable, reservations_need_confirmation, has_vc, expected):
    room = create_room(capacity=capacity, is_reservable=is_reservable,
                       reservations_need_confirmation=reservations_need_confirmation)
    if has_vc:
        room.available_equipment.append(create_equipment_type(u'Video conference'))
        db.session.flush()
    assert room.marker_description == expected


def test_owner(dummy_room, dummy_user):
    assert dummy_room.owner.id == dummy_user.id
    dummy_room.owner_id = u'xxx'
    assert dummy_room.owner is None


@pytest.mark.parametrize(('value', 'emails'), (
    (u'', set()),
    (u'example@example.com', {u'example@example.com'}),
    (u'  example@example.com   ,m\xf6p@example.cm\xf6pm  ', {u'example@example.com', u'm\xf6p@example.cm\xf6pm'}),
))
def test_notification_emails(create_room_attribute, dummy_room, value, emails):
    create_room_attribute(u'notification-email')
    dummy_room.set_attribute_value(u'notification-email', value)
    assert dummy_room.notification_emails == emails


@pytest.mark.parametrize(('name', 'expected'), (
    (u'foo', True),
    (u'bar', True),
    (u'xxx', False),  # existent
    (u'yyy', False),  # not existent
))
def test_has_equipment(create_equipment_type, dummy_room, name, expected):
    dummy_room.available_equipment.append(create_equipment_type(u'foo'))
    dummy_room.available_equipment.append(create_equipment_type(u'bar'))
    create_equipment_type(u'xxx')
    assert dummy_room.has_equipment(name) == expected


def test_find_available_vc_equipment(db, dummy_room, create_equipment_type):
    foo = create_equipment_type(u'foo')
    vc = create_equipment_type(u'Video conference')
    vc_items = [create_equipment_type(u'vc1'), create_equipment_type(u'vc2')]
    vc.children += vc_items
    dummy_room.available_equipment.extend(vc_items + [vc, foo])
    db.session.flush()
    assert set(dummy_room.find_available_vc_equipment()) == set(vc_items)


def test_get_attribute_by_name(create_room_attribute, dummy_room):
    attr = create_room_attribute(u'foo')
    assert dummy_room.get_attribute_by_name(u'foo') is None
    dummy_room.set_attribute_value(u'foo', u'bar')
    assert dummy_room.get_attribute_by_name(u'foo').attribute == attr


def test_has_attribute(create_room_attribute, dummy_room):
    create_room_attribute(u'foo')
    assert not dummy_room.has_attribute(u'foo')
    dummy_room.set_attribute_value(u'foo', u'bar')
    assert dummy_room.has_attribute(u'foo')


@pytest.mark.parametrize(('value', 'expected'), (
    (u'',        _notset),
    (None,       _notset),
    (0,          _notset),
    ([],         _notset),
    (u'foo',     u'foo'),
    (123,        123),
    (True,       True),
    (['a', 'b'], ['a', 'b']),
))
def test_get_attribute_value(create_room_attribute, dummy_room, value, expected):
    assert dummy_room.get_attribute_value(u'foo', _notset) is _notset
    create_room_attribute(u'foo')
    assert dummy_room.get_attribute_value(u'foo', _notset) is _notset
    dummy_room.set_attribute_value(u'foo', value)
    assert dummy_room.get_attribute_value(u'foo', _notset) == expected


def test_set_attribute_value(create_room_attribute, dummy_room):
    # setting an attribute that doesn't exist fails
    with pytest.raises(ValueError):
        dummy_room.set_attribute_value(u'foo', u'something')
    create_room_attribute(u'foo')
    # the value can be cleared even if it is not set
    dummy_room.set_attribute_value(u'foo', None)
    assert dummy_room.get_attribute_value(u'foo', _notset) is _notset
    # set it to some value
    dummy_room.set_attribute_value(u'foo', u'test')
    assert dummy_room.get_attribute_value(u'foo') == u'test'
    # set to some other value while we have an existing association entry
    dummy_room.set_attribute_value(u'foo', u'something')
    assert dummy_room.get_attribute_value(u'foo') == u'something'
    # clear it
    dummy_room.set_attribute_value(u'foo', None)
    assert dummy_room.get_attribute_value(u'foo', _notset) is _notset


def test_getLocator(dummy_location, dummy_room):
    assert dummy_room.getLocator() == {'roomLocation': dummy_location.name, 'roomID': dummy_room.id}


@pytest.mark.parametrize(('building', 'floor', 'number', 'name', 'expected_name'), (
    (u'1', u'2', u'3', u'',       u'1-2-3'),
    (u'1', u'2', u'X', u'',       u'1-2-X'),
    (u'1', u'X', u'3', u'',       u'1-X-3'),
    (u'X', u'2', u'3', u'',       u'X-2-3'),
    (u'1', u'2', u'3', u'Test',   u'Test')
))
def test_update_name(create_room, building, floor, number, name, expected_name):
    room = create_room()
    room.building = building
    room.floor = floor
    room.number = number
    room.name = name
    assert room.name == name
    room.update_name()
    assert room.name == expected_name


def test_find_all(create_location, create_room):
    # Here we just test if we get the rooms in natural sort order
    loc1 = create_location('Z')
    loc2 = create_location('A')
    data = [
        (2, dict(location=loc1, building=u'1',   floor=u'2', number=u'3', name=u'')),
        (3, dict(location=loc1, building=u'2',   floor=u'2', number=u'3', name=u'')),
        (5, dict(location=loc1, building=u'100', floor=u'2', number=u'3', name=u'')),
        (4, dict(location=loc1, building=u'10',  floor=u'2', number=u'3', name=u'')),
        (1, dict(location=loc2, building=u'999', floor=u'2', number=u'3', name=u''))
    ]
    rooms = [(pos, create_room(**params)) for pos, params in data]
    sorted_rooms = map(itemgetter(1), sorted(rooms, key=itemgetter(0)))
    assert sorted_rooms == Room.find_all()


def test_find_with_attribute(dummy_room, create_room, create_room_attribute):
    assert Room.find_all() == [dummy_room]  # one room without the attribute
    assert not Room.find_with_attribute(u'foo')
    create_room_attribute(u'foo')
    assert not Room.find_with_attribute(u'foo')
    expected = set()
    for room in [create_room(), create_room()]:
        value = u'bar-{}'.format(room.id)
        room.set_attribute_value(u'foo', value)
        expected.add((room, value))
    assert set(Room.find_with_attribute(u'foo')) == expected
