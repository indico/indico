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

from datetime import date

import pytest
from dateutil.relativedelta import relativedelta

from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.room_attributes import RoomAttribute
from indico.modules.rb.models.rooms import Room


@pytest.fixture
def create_location(db):
    """Returns a callable which lets you create locations"""

    def _create_location(name, **params):
        location = Location(name=name, **params)
        db.session.add(location)
        db.session.flush()
        return location

    return _create_location


@pytest.fixture
def dummy_location(db, create_location):
    """Gives you a dummy default location"""
    loc = create_location('Test')
    loc.set_default()
    db.session.flush()
    return loc


@pytest.fixture
def create_reservation(db, dummy_room, dummy_user):
    def _create_reservation(**params):
        params.setdefault('start_dt', date.today() + relativedelta(hour=8, minute=30))
        params.setdefault('end_dt', date.today() + relativedelta(hour=17, minute=30))
        params.setdefault('repeat_frequency', RepeatFrequency.NEVER)
        params.setdefault('repeat_interval', int(params['repeat_frequency'] != RepeatFrequency.NEVER))
        params.setdefault('contact_email', dummy_user.email)
        params.setdefault('is_accepted', True)
        params.setdefault('booking_reason', 'Testing')
        params.setdefault('room', dummy_room)
        reservation = Reservation(**params)
        reservation.booked_for_user = dummy_user
        reservation.created_by_user = dummy_user
        reservation.create_occurrences(skip_conflicts=False)
        db.session.add(reservation)
        db.session.flush()
        return reservation

    return _create_reservation


@pytest.fixture
def dummy_reservation(create_reservation):
    return create_reservation()


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


@pytest.fixture
def create_room_attribute(db, dummy_location):
    """Returns a callable which let you create room attributes"""

    def _create_attribute(name, **params):
        params.setdefault('location', dummy_location)
        params.setdefault('title', name)
        params.setdefault('type', 'str')
        params.setdefault('is_required', False)
        params.setdefault('is_hidden', False)
        attr = RoomAttribute(name=name, **params)
        db.session.flush()
        return attr

    return _create_attribute


@pytest.fixture
def create_equipment_type(db, dummy_location):
    """Returns a callable which let you create equipment types"""

    def _create_equipment_type(name, **params):
        params.setdefault('location', dummy_location)
        eq = EquipmentType(name=name, **params)
        db.session.flush()
        return eq

    return _create_equipment_type
