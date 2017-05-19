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

import re
from datetime import date, datetime, timedelta, time

from dateutil.relativedelta import relativedelta
from flask import request, session
from sqlalchemy import func
from werkzeug.datastructures import MultiDict

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.decorators import requires_location, requires_room
from indico.modules.rb.forms.rooms import SearchRoomsForm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.statistics import calculate_rooms_occupancy, compose_rooms_stats
from indico.modules.rb.views.user.rooms import (WPRoomBookingSearchRooms, WPRoomBookingMapOfRooms,
                                                WPRoomBookingMapOfRoomsWidget, WPRoomBookingRoomDetails,
                                                WPRoomBookingRoomStats, WPRoomBookingSearchRoomsResults)
from indico.web.forms.base import FormDefaults


class RHRoomBookingMapOfRooms(RHRoomBookingBase):
    def _checkParams(self):
        RHRoomBookingBase._checkParams(self, request.args)
        self._room_id = request.args.get('roomID')

    def _process(self):
        return WPRoomBookingMapOfRooms(self, roomID=self._room_id).display()


class RHRoomBookingMapOfRoomsWidget(RHRoomBookingBase):
    def _checkParams(self):
        RHRoomBookingBase._checkParams(self, request.args)
        self._room_id = request.args.get('roomID')

    def _process(self):
        return WPRoomBookingMapOfRoomsWidget(self, roomID=self._room_id).display()


class RHRoomBookingSearchRooms(RHRoomBookingBase):
    menu_item = 'search_rooms'
    CSRF_ENABLED = False

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
        return WPRoomBookingSearchRooms(self, form=form, errors=form.error_list, rooms=Room.find_all(is_active=True),
                                        equipment_locations=equipment_locations).display()


class RHRoomBookingSearchRoomsShortcutBase(RHRoomBookingSearchRooms):
    """Base class for searches with predefined criteria"""
    search_criteria = {}

    def _is_submitted(self):
        return True

    def _get_form_data(self):
        return MultiDict(self.search_criteria)


class RHRoomBookingSearchMyRooms(RHRoomBookingSearchRoomsShortcutBase):
    menu_item = 'room_list'
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
        occurrences = ReservationOccurrence.find(
            Reservation.room_id == self._room.id,
            ReservationOccurrence.start_dt >= self._calendar_start,
            ReservationOccurrence.end_dt <= self._calendar_end,
            ReservationOccurrence.is_valid,
            _join=ReservationOccurrence.reservation,
            _eager=ReservationOccurrence.reservation
        ).options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY).all()

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
            oldest = db.session.query(func.min(Reservation.start_dt)).filter_by(room_id=self._room.id).scalar()
            self._start = oldest.date() if oldest else self._end
        else:
            match = re.match(r'(\d{4})(?:-(\d{2}))?', self._occupancy_period)
            if match is None:
                raise IndicoError('Invalid period specified')
            year = int(match.group(1))
            month = int(match.group(2)) if match.group(2) else None
            if month:
                try:
                    self._start = date(year, month, 1)
                except ValueError:
                    raise IndicoError('Invalid year or month specified')
                self._end = self._start + relativedelta(months=1)
                self._occupancy_period = '{:d}-{:02d}'.format(year, month)
            else:
                try:
                    self._start = date(year, 1, 1)
                except ValueError:
                    raise IndicoError('Invalid year specified')
                self._end = self._start + relativedelta(years=1)
                self._occupancy_period = str(year)

    def _process(self):
        last_year = str(date.today().year - 1)
        last_month_date = date.today() - relativedelta(months=1, day=1)
        last_month = '{:d}-{:02d}'.format(last_month_date.year, last_month_date.month)
        return WPRoomBookingRoomStats(self,
                                      room=self._room,
                                      period=self._occupancy_period,
                                      last_year=last_year,
                                      last_month=last_month,
                                      occupancy=calculate_rooms_occupancy([self._room], self._start, self._end),
                                      stats=compose_rooms_stats([self._room])).display()
