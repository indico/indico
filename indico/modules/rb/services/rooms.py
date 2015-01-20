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
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from flask import session
from sqlalchemy.orm.exc import NoResultFound

from indico.core.config import Config
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.util.date_time import get_datetime_from_request
from indico.util.string import natural_sort_key
from MaKaC.services.implementation.base import LoggedOnlyService, ServiceBase
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.webinterface.linking import RoomLinker


class RoomBookingListRooms(ServiceBase):
    UNICODE_PARAMS = True

    def _checkParams(self):
        try:
            location = Location.find_one(name=self._params['location'])
        except NoResultFound:
            raise ServiceError('ERR-RB0', 'Invalid location name: {0}.'.format(self._params['location']))
        self._rooms = sorted(location.rooms, key=lambda r: natural_sort_key(r.full_name))

    def _getAnswer(self):
        return [(room.name, room.name) for room in self._rooms]


class RoomBookingFullNameListRooms(RoomBookingListRooms):
    def _getAnswer(self):
        return [(room.name, room.full_name) for room in self._rooms]


class RoomBookingAvailabilitySearchRooms(ServiceBase):
    UNICODE_PARAMS = True

    def _checkParams(self):
        self._start_dt = get_datetime_from_request(prefix='start_', source=self._params)
        self._end_dt = get_datetime_from_request(prefix='end_', source=self._params)
        repetition = map(int, self._params['repeatability'].split('|'))
        self._repetition = RepeatFrequency(repetition[0]), repetition[1]

    def _getAnswer(self):
        rooms = Room.find_all(Room.filter_available(self._start_dt, self._end_dt, self._repetition))
        return [room.id for room in rooms]


class RoomBookingListLocationsAndRoomsWithGuids(ServiceBase):
    UNICODE_PARAMS = True

    def _checkParams(self):
        self._isActive = self._params.get('isActive', None)

    def _getAnswer(self):
        if not Config.getInstance().getIsRoomBookingActive():
            return {}
        criteria = {'_eager': Room.location}
        if self._isActive is not None:
            criteria['is_active'] = self._isActive
        rooms = Room.find_all(**criteria)
        return {room.id: '{}: {}'.format(room.location_name, room.full_name) for room in rooms}


class RoomBookingLocationsAndRoomsGetLink(ServiceBase):
    UNICODE_PARAMS = True

    def _checkParams(self):
        self._location = self._params['location']
        self._room = self._params['room']

    def _getAnswer(self):
        return RoomLinker().getURLByName(self._room, self._location)


class BookingPermission(LoggedOnlyService):
    UNICODE_PARAMS = True

    def _checkParams(self):
        blocking_id = self._params.get('blocking_id')
        self._room = Room.get(self._params['room_id'])
        self._blocking = Blocking.get(blocking_id) if blocking_id else None

    def _getAnswer(self):
        user = session.user
        return {
            'blocked': not self._blocking.can_be_overridden(user, self._room) if self._blocking else False,
            'is_reservable': self._room.is_reservable,
            'can_book': self._room.can_be_booked(user) or self._room.can_be_prebooked(user),
            'group': self._room.get_attribute_value('allowed-booking-group')
        }
