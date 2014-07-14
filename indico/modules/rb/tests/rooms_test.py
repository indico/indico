# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
## You should have received a copy of the GNU General Public License.
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import transaction

from datetime import date, time
from nose.tools import assert_equal, assert_not_equal, assert_is, assert_is_not,\
    assert_in, assert_not_in, assert_true, assert_false

from indico.core.db import db
from indico.modules.rb.models.rooms import Room
from indico.tests.db.data import ROOMS, LOCATIONS, ROOM_WITH_DUMMY_MANAGER_GROUP, \
    ROOM_WITH_DUMMY_ALLOWED_BOOKING_GROUP, ROOM_ATTRIBUTE_ASSOCIATIONS, NOT_FITTING_HOURS
from indico.tests.db.environment import DBTest
from indico.tests.db.util import diff
from indico.tests.python.unit.util import with_context


class TestRoom(DBTest):
    """
    Testing the most important functions of the Room class from
    the room booking models.
    """

    def iterRooms(self):
        for r in ROOMS:
            room = Room.find_first(Room.name == r['name'])
            yield r, room
            db.session.add(room)
        transaction.commit()

    def test_is_auto_confirm(self):
        for r, room in self.iterRooms():
            needs_confirmation = 'reservations_need_confirmation' in r and r['reservations_need_confirmation']
            assert_not_equal(room.is_auto_confirm, needs_confirmation)

    def test_booking_url(self):
        for r, room in self.iterRooms():
            if room.id is None:
                assert_is(room.booking_url, None)
            else:
                assert_is_not(room.booking_url, None)

    def test_details_url(self):
        for r, room in self.iterRooms():
            if room.id is None:
                assert_is(room.details_url, None)
            else:
                assert_is_not(room.details_url, None)

    def test_full_name(self):
        for r, room in self.iterRooms():
            if room.has_special_name:
                assert_in(r['name'], room.full_name)
            assert_in(room.generate_name(), room.full_name)

    def test_has_booking_groups(self):
        for r, room in self.iterRooms():
            assert_equal(room.has_booking_groups,
                         'attributes' in r and
                         any(attr['name'] == 'allowed-booking-group' for attr in r['attributes']))

    def test_has_vc(self):
        for r, room in self.iterRooms():
            assert_equal('available_equipment' in r and 'Video conference' in r['available_equipment'],
                         room.has_vc)

    def test_has_projector(self):
        for r, room in self.iterRooms():
            assert_equal('available_equipment' in r and 'Computer Projector' in r['available_equipment'],
                         room.has_projector)

    def test_has_special_name(self):
        for r, room in self.iterRooms():
            assert_equal(room.has_special_name, 'name' in r and r['name'] is not None)

    def test_has_webcast_recording(self):
        for r, room in self.iterRooms():
            assert_equal('available_equipment' in r and 'Webcast/Recording' in r['available_equipment'],
                         room.has_webcast_recording)

    def test_is_public(self):
        for r, room in self.iterRooms():
            assert_equal(room.is_public, room.is_reservable and (not room.has_booking_groups))

    def test_kind(self):
        for r, room in self.iterRooms():
            if room.is_public:
                if room.is_auto_confirm:
                    assert_equal(room.kind, 'basicRoom')
                else:
                    assert_equal(room.kind, 'moderatedRoom')
            else:
                assert_equal(room.kind, 'privateRoom')

    def test_location_name(self):
        for r, room in self.iterRooms():
            found_in_data = False
            for loc in LOCATIONS:
                if room.location_name == loc['name']:
                    location_rooms = []
                    for loc_room in loc['rooms']:
                        location_rooms.append(loc_room['name'])
                    assert_in(room.name, location_rooms)
                    found_in_data = True
            assert_true(found_in_data)

    def test_marker_description(self):
        for r, room in self.iterRooms():
            description = room.marker_description
            if room.capacity:
                assert_in(str(room.capacity), description)
            if room.is_public:
                assert_in('public', description)
            else:
                assert_in('private', description)
            if room.is_auto_confirm:
                assert_in('auto-confirmation', description)
            else:
                assert_in('needs confirmation', description)

    def test_large_photo_url(self):
        for r, room in self.iterRooms():
            if room.id is None:
                assert_is(room.large_photo_url, None)
            else:
                assert_is_not(room.large_photo_url, None)

    def test_small_photo_url(self):
        for r, room in self.iterRooms():
            if room.id is None:
                assert_is(room.small_photo_url, None)
            else:
                assert_is_not(room.small_photo_url, None)

    def test_has_photo(self):
        for r, room in self.iterRooms():
            if room.photo_id is None:
                assert_false(room.has_photo)
            else:
                assert_true(room.has_photo)

    def test_has_equipment(self):
        for r, room in self.iterRooms():
            if 'available_equipment' in r:
                for equip in r['available_equipment']:
                    assert_true(room.has_equipment(equip))
            assert_false(room.has_equipment('This equipment does not exist'))

    def test_find_available_vc_equipment(self):
        pass

    def test_get_attribute_by_name(self):
        for r, room in self.iterRooms():
            if 'attributes' in r:
                for attr in r['attributes']:
                    assert_is_not(room.get_attribute_by_name(attr['name']), None)
            assert_is(room.get_attribute_by_name('This attribute does not exist'), None)

    def test_has_attribute(self):
        for r, room in self.iterRooms():
            if 'attributes' in r:
                for attr in r['attributes']:
                    assert_true(room.has_attribute(attr['name']))
            assert_false(room.has_attribute('This attribute does not exist'))

    def testGetLocator(self):
        for r, room in self.iterRooms():
            l = room.getLocator()
            assert_equal(l['roomLocation'], room.location.name)
            assert_equal(l['roomID'], room.id)

    def test_generate_name(self):
        for r, room in self.iterRooms():
            if room.building:
                assert_in(r['building'], room.generate_name())
            if room.floor:
                assert_in(r['floor'], room.generate_name())
            if room.number:
                assert_in(r['number'], room.generate_name())

    def test_full_name(self):
        for r, room in self.iterRooms():
            assert_in(room.name, room.full_name)
            assert_in(room.generate_name(), room.full_name)

    def test_update_name(self):
        for r, room in self.iterRooms():
            if room.building and room.floor and room.number:
                room.name = ''
                room.update_name()
                assert_true(len(room.name) > 0)

    def test_find_all(self):
        all_rooms = Room.find_all()

        lista = []
        #we get the concatenation of location.name and full name because
        #these values are used for sorting in the find_all method.
        for r, room in self.iterRooms():
            lista.append(room.location.name + room.full_name)

        lista = sorted(lista)
        assert_equal(len(all_rooms), len(lista))

        for i in range(len(all_rooms)):
            assert_equal(all_rooms[i].location.name + all_rooms[i].full_name, lista[i])

    def test_find_with_attribute(self):
        for r, room in self.iterRooms():
            for attr in r['attributes']:
                rooms_with_attr = []
                for room_with_attr in Room.find_with_attribute(attr['name']):
                    rooms_with_attr.append(room_with_attr[0])
                assert_in(room, rooms_with_attr)

    def getRoomsWithData(*args, **kwargs):
        pass

    def test_max_capacity(self):
        max_capacity = 0
        for r, room in self.iterRooms():
            if 'capacity' in r:
                max_capacity = r['capacity'] if r['capacity'] > max_capacity else max_capacity
        assert_equal(max_capacity, Room.max_capacity)

    def filter_available(start_dt, end_dt, repetition, include_pre_bookings=True, include_pending_blockings=True):
        pass

    def has_live_reservations(self):
        for r, room in self.iterRooms():
            def is_live(resv):
                #Live reservations: Happening now or future reservations.
                return resv['start_date'] >= datetime.utcnow() or \
                    resv['end_date'] >= datetime.utcnow()
            c = len(filter(is_live, r.get('reservations', []))) > 0
            assert_equal(c, room.doesHaveLiveReservations())

    def get_blocked_rooms(self, *dates, **kwargs):
        pass

    def test_get_attribute_value(self):
        for r, room in self.iterRooms():
            for attr in r['attributes']:
                assoc_value = ""
                for item in ROOM_ATTRIBUTE_ASSOCIATIONS:
                    if item["attribute"] == attr['name'] and item["room"] == room.name:
                            assoc_value = item["value"]
                assert_true(room.get_attribute_value(attr['name']) == assoc_value)

    @with_context('database')
    def test_can_be_booked(self):
        for r, room in self.iterRooms():
            if r['name'] == ROOMS[ROOM_WITH_DUMMY_MANAGER_GROUP]['name']:
                #check for room's owner
                if r['is_active'] and r['is_reservable']:
                    assert_true(room.can_be_booked(self._avatar1))
                else:
                    raise Exception("This room needs to be reservable and active.")
            elif r['name'] == ROOMS[ROOM_WITH_DUMMY_ALLOWED_BOOKING_GROUP]['name']:
                #check for room's with allowed booking group
                if r['is_active'] and r['is_reservable']:
                    self._dummy_group_with_users.removeMember(self._avatar1)
                    assert_true(room.can_be_booked(self._avatar1))
                    self._dummy_group_with_users.addMember(self._avatar1)
                else:
                    raise Exception("This room needs to be reservable and active.")
            else:
                if room.is_active and room.is_reservable and not room.reservations_need_confirmation:
                    #check for any user.
                    assert_true(room.can_be_booked(self._avatar1))
                else:
                    assert_true(room.can_be_booked(self._dummy))

    @with_context('database')
    def test_can_be_overriden(self):
        for r, room in self.iterRooms():
            if room.is_owned_by(self._avatar1):
                assert_true(room.can_be_overriden(self._avatar1))
                assert_true(room.can_be_overriden(self._dummy))
            else:
                assert_true(room.can_be_overriden(self._dummy))

    @with_context('database')
    def test_can_be_modified(self):
        for r, room in self.iterRooms():
            #checking with an avatar and not an accessWrapper
            assert_false(room.can_be_modified(self._avatar1))
            assert_true(room.can_be_modified(self._dummy))

    @with_context('database')
    def test_can_be_deleted(self):
        for r, room in self.iterRooms():
            #checking with an avatar and not an accessWrapper
            assert_false(room.can_be_deleted(self._avatar1))
            assert_true(room.can_be_deleted(self._dummy))

    @with_context('database')
    def test_is_owned_by(self):
        for r, room in self.iterRooms():
            if r['name'] == ROOMS[ROOM_WITH_DUMMY_MANAGER_GROUP]['name']:
                assert_true(room.is_owned_by(self._avatar1))
            else:
                assert_true(room.is_owned_by(self._dummy))
                assert_false(room.is_owned_by(self._avatar1))

    def test_check_advance_days(self):
        pass
        #needs fixing

    @with_context('database')
    def test_check_bookable_hours(self):
        for r, room in self.iterRooms():
            assert_true(room.check_bookable_hours(time(10, 30), time(17, 30), self._dummy, True))
            if room.is_owned_by(self._avatar1):
                assert_true(room.check_bookable_hours(time(10, 30), time(17, 30), self._avatar1, True))
            if 'bookable_hours' in r and r['bookable_hours']:
                for bk_hour in r['bookable_hours']:
                    assert_true(room.check_bookable_hours(bk_hour['start_time'], bk_hour['end_time'], None, True))
                assert_false(room.check_bookable_hours(NOT_FITTING_HOURS['start_time'],
                                                       NOT_FITTING_HOURS['end_time'], None, True))
