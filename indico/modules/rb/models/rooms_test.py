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

from indico.modules.rb.models.rooms import Room


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_is_auto_confirm(create_room, bool_flag):
    room = create_room(reservations_need_confirmation=bool_flag)
    assert room.is_auto_confirm != bool_flag
    assert Room.find_first(is_auto_confirm=bool_flag) is None
    assert Room.find_first(is_auto_confirm=not bool_flag) == room


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
