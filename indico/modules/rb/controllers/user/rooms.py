# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timedelta, time

from flask import request, session
from werkzeug.datastructures import MultiDict

from MaKaC.common.cache import GenericCache
from MaKaC.webinterface.locators import WebLocator
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.decorators import requires_location, requires_room
from indico.modules.rb.forms.base import FormDefaults
from indico.modules.rb.forms.rooms import SearchRoomsForm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatMapping, RepeatUnit, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.room_equipments import RoomEquipment
from indico.modules.rb.models.utils import next_work_day
from indico.modules.rb.views.user.rooms import (WPRoomBookingSearchRooms, WPRoomBookingMapOfRooms,
                                                WPRoomBookingMapOfRoomsWidget, WPRoomBookingRoomDetails,
                                                WPRoomBookingRoomStats, WPRoomBookingSearchRoomsResults)


class RHRoomBookingMapOfRooms(RHRoomBookingBase):
    def _checkParams(self):
        RHRoomBookingBase._checkParams(self, request.args)
        self._room_id = request.args.get('roomID')

    def _process(self):
        return WPRoomBookingMapOfRooms(self, roomID=self._room_id).display()


class RHRoomBookingMapOfRoomsWidget(RHRoomBookingBase):
    def __init__(self, *args, **kwargs):
        RHRoomBookingBase.__init__(self, *args, **kwargs)
        self._cache = GenericCache('MapOfRooms')

    def _checkParams(self):
        RHRoomBookingBase._checkParams(self, request.args)
        self._room_id = request.args.get('roomID')

    def _process(self):
        key = str(sorted(dict(request.args, lang=session.lang, user=session.user.getId()).items()))
        html = self._cache.get(key)
        if not html:
            default_location = Location.getDefaultLocation()
            aspects = default_location.getAspectsAsDictionary()
            for_video_conference = request.args.get('avc') == 'y' and default_location.hasEquipment('Video conference')
            buildings = default_location.getBuildings(with_rooms=not for_video_conference)
            html = WPRoomBookingMapOfRoomsWidget(self,
                                                 aspects=aspects,
                                                 buildings=buildings,
                                                 room_id=self._room_id,
                                                 default_repeat=(RepeatUnit.NEVER, 0),
                                                 default_start_dt=datetime.combine(next_work_day(), time(8)),
                                                 default_end_dt=datetime.combine(next_work_day(), time(17)),
                                                 repeat_mapping=RepeatMapping.getMapping()).display()
            self._cache.set(key, html, 3600)
        return html


class RHRoomBookingSearchRooms(RHRoomBookingBase):
    menu_item = 'roomSearch'

    def _get_form_data(self):
        return request.form

    def _checkParams(self):
        defaults = FormDefaults(location=Location.getDefaultLocation())
        self._form = SearchRoomsForm(self._get_form_data(), obj=defaults)
        if not session.user.has_rooms:
            del self._form.is_only_my_rooms

    def _is_submitted(self):
        return self._form.is_submitted()

    def _process(self):
        form = self._form
        if self._is_submitted() and form.validate():
            rooms = Room.getRoomsForRoomList(form, session.user)
            return WPRoomBookingSearchRoomsResults(self, self.menu_item, rooms=rooms).display()
        equipment_locations = {eq.id: eq.location_id for eq in RoomEquipment.find()}
        return WPRoomBookingSearchRooms(self, form=form, errors=form.error_list, rooms=Room.find_all(),
                                        equipment_locations=equipment_locations).display()


class RHRoomBookingSearchRoomsShortcutBase(RHRoomBookingSearchRooms):
    """Base class for searches with predefined criteria"""
    search_criteria = {}

    def _is_submitted(self):
        return True

    def _get_form_data(self):
        return MultiDict(self.search_criteria)


class RHRoomBookingSearchMyRooms(RHRoomBookingSearchRoomsShortcutBase):
    menu_item = 'myRoomList'
    search_criteria = {
        'is_only_my_rooms': True
    }


# TODO: remove with legacy makac code. still referenced in book-room-for-event code
class RHRoomBookingRoomList(RHRoomBookingBase):
    pass


# TODO: remove with legacy makac code. still referenced in book-room-for-event code
class RHRoomBookingSearch4Rooms(RHRoomBookingBase):
    pass


class RHRoomBookingRoomDetails(RHRoomBookingBase):
    @requires_location
    @requires_room
    def _checkParams(self):
        self._target = self._room

        # TODO: flash() messages instead!!!
        self._afterActionSucceeded = session.get('rbActionSucceeded')
        self._afterDeletionFailed = session.get('rbDeletionFailed')

        self._calendar_start = next_work_day()
        self._calendar_end = datetime.combine(self._calendar_start, time(23, 59))
        try:
            preview_months = int(request.args.get('preview_months', '0'))
        except (TypeError, ValueError):
            preview_months = 0
        self._calendar_end += timedelta(days=31 * preview_months)

    def _process(self):
        occurrences = ReservationOccurrence.find_all(
            Reservation.room_id == self._room.id,
            ReservationOccurrence.start >= self._calendar_start,
            ReservationOccurrence.end <= self._calendar_end,
            ReservationOccurrence.is_valid,
            _join=Reservation,
            _eager=ReservationOccurrence.reservation
        )

        return WPRoomBookingRoomDetails(self, room=self._room, start_dt=self._calendar_start, end_dt=self._calendar_end,
                                        occurrences=occurrences).display()


# TODO
class RHRoomBookingRoomStats(RHRoomBookingBase):
    def _checkParams(self):
        params = request.args if request.method == 'GET' else request.form
        locator = WebLocator()
        locator.setRoom(params)
        self._period = params.get('period', default='pastmonth')
        self._room = self._target = locator.getObject()

    def _businessLogic(self):
        pass
        # self._kpiAverageOccupation = self._room.getMyAverageOccupation(self._period)
        # self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms()
        # self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms()
        # self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity()
        # # Bookings
        # st = ReservationBase.getRoomReservationStats(self._room)
        # self._booking_stats = st
        # self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

    def _process(self):
        self._businessLogic()
        return WPRoomBookingRoomStats(self).display()
