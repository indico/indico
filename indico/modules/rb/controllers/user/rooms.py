# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from datetime import date, datetime, timedelta, time

from dateutil.relativedelta import relativedelta
from flask import request, session
from sqlalchemy import func
from werkzeug.datastructures import MultiDict

from indico.core.errors import IndicoError
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.decorators import requires_location, requires_room
from indico.modules.rb.forms.rooms import SearchRoomsForm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatMapping, RepeatFrequency, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.statistics import calculate_rooms_occupancy, compose_rooms_stats
from indico.modules.rb.views.user.rooms import (WPRoomBookingSearchRooms, WPRoomBookingMapOfRooms,
                                                WPRoomBookingMapOfRoomsWidget, WPRoomBookingRoomDetails,
                                                WPRoomBookingRoomStats, WPRoomBookingSearchRoomsResults)
from indico.web.forms.base import FormDefaults
from MaKaC.common.cache import GenericCache


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
        key = str(sorted(dict(request.args, lang=session.lang, user=session.user.id).items()))
        html = self._cache.get(key)
        if not html:
            default_location = Location.default_location
            aspects = [a.to_serializable() for a in default_location.aspects]
            buildings = default_location.get_buildings()
            html = WPRoomBookingMapOfRoomsWidget(self,
                                                 aspects=aspects,
                                                 buildings=buildings,
                                                 room_id=self._room_id,
                                                 default_repeat='{}|0'.format(int(RepeatFrequency.NEVER)),
                                                 default_start_dt=datetime.combine(date.today(),
                                                                                   Location.working_time_start),
                                                 default_end_dt=datetime.combine(date.today(),
                                                                                 Location.working_time_end),
                                                 repeat_mapping=RepeatMapping.mapping).display()
            self._cache.set(key, html, 3600)
        return html


class RHRoomBookingSearchRooms(RHRoomBookingBase):
    menu_item = 'roomSearch'

    def _get_form_data(self):
        return request.form

    def _checkParams(self):
        defaults = FormDefaults(location=Location.default_location)
        self._form = SearchRoomsForm(self._get_form_data(), obj=defaults, csrf_enabled=False)
        if (not session.user or not Room.user_owns_rooms(session.user)) and not hasattr(self, 'search_criteria'):
            # Remove the form element if the user has no rooms and we are not using a shortcut
            del self._form.is_only_my_rooms

    def _is_submitted(self):
        return self._form.is_submitted()

    def _process(self):
        form = self._form
        if self._is_submitted() and form.validate():
            rooms = Room.find_with_filters(form.data, session.user)
            return WPRoomBookingSearchRoomsResults(self, self.menu_item, rooms=rooms).display()
        equipment_locations = {eq.id: eq.location_id for eq in EquipmentType.find()}
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
        'is_only_my_rooms': True,
        'location': None
    }


class RHRoomBookingRoomDetails(RHRoomBookingBase):
    @requires_location
    @requires_room
    def _checkParams(self):
        self._calendar_start = datetime.combine(date.today(), time())
        self._calendar_end = datetime.combine(date.today(), time(23, 59))
        try:
            preview_months = int(request.args.get('preview_months', '0'))
        except (TypeError, ValueError):
            preview_months = 0
        self._calendar_end += timedelta(days=31 * preview_months)

    def _get_view(self, **kwargs):
        return WPRoomBookingRoomDetails(self, **kwargs)

    def _process(self):
        occurrences = ReservationOccurrence.find_all(
            Reservation.room_id == self._room.id,
            ReservationOccurrence.start_dt >= self._calendar_start,
            ReservationOccurrence.end_dt <= self._calendar_end,
            ReservationOccurrence.is_valid,
            _join=ReservationOccurrence.reservation,
            _eager=ReservationOccurrence.reservation
        )

        return self._get_view(room=self._room, start_dt=self._calendar_start, end_dt=self._calendar_end,
                              occurrences=occurrences).display()


class RHRoomBookingRoomStats(RHRoomBookingBase):
    def _checkParams(self):
        self._room = Room.get(request.view_args['roomID'])
        self._occupancy_period = request.args.get('period', 'pastmonth')
        self._end = date.today()
        if self._occupancy_period == 'pastmonth':
            self._end = self._end - relativedelta(days=1)
            self._start = self._end - relativedelta(days=29)
        elif self._occupancy_period == 'thisyear':
            self._start = date(self._end.year, 1, 1)
        elif self._occupancy_period == 'sinceever':
            self._start = Reservation.query.with_entities(func.min(Reservation.start_dt)).one()[0].date()
        else:
            raise IndicoError('Invalid period specified')

    def _process(self):
        return WPRoomBookingRoomStats(self,
                                      room=self._room,
                                      period=self._occupancy_period,
                                      occupancy=calculate_rooms_occupancy([self._room], self._start, self._end),
                                      stats=compose_rooms_stats([self._room])).display()
