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
    ('xxx', True),
    ('', False)
))
def test_has_booking_groups(create_room_attribute, dummy_room, value, expected):
    create_room_attribute('allowed-booking-group')
    assert not dummy_room.has_booking_groups
    dummy_room.set_attribute_value('allowed-booking-group', value)
    assert dummy_room.has_booking_groups == expected


def test_has_projector(create_equipment_type, dummy_room, db):
    assert not dummy_room.has_projector
    dummy_room.available_equipment.append(create_equipment_type('Computer Projector'))
    db.session.flush()
    assert dummy_room.has_projector


def test_has_webcast_recording(create_equipment_type, dummy_room, db):
    assert not dummy_room.has_webcast_recording
    dummy_room.available_equipment.append(create_equipment_type('Webcast/Recording'))
    db.session.flush()
    assert dummy_room.has_webcast_recording


@pytest.mark.parametrize(('reservable', 'booking_group', 'expected'), (
    (True, '', True),
    (True, 'xxx', False),
    (False, '', False),
    (False, 'xxx', False)
))
def test_is_public(create_room_attribute, dummy_room, reservable, booking_group, expected):
    create_room_attribute('allowed-booking-group')
    dummy_room.set_attribute_value('allowed-booking-group', booking_group)
    dummy_room.is_reservable = reservable
    assert dummy_room.is_public == expected


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
