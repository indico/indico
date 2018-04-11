# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

import dateutil
from flask import request

from indico.core.db import db
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.views.base import WPRoomBookingBase
from indico.util.string import natural_sort_key


class RHRoomBookingLanding(RHRoomBookingBase):
    def _process(self):
        return WPRoomBookingBase.display('room_booking.html')


class RHRoomBookingSearch(RHRoomBookingBase):
    def _process(self):
        from indico.modules.rb.schemas import rooms_schema

        min_capacity = int(request.args['capacity']) if 'capacity' in request.args else None
        room_name = request.args.get('title')
        start_dt = dateutil.parser.parse(request.args['start_dt'])
        end_dt = dateutil.parser.parse(request.args['end_dt'])
        repeat_frequency = (RepeatFrequency.get(request.args['repeat_frequency'])
                            if 'repeat_frequency' in request.args else 0)
        repeat_interval = int(request.args.get('repeat_interval', 0))
        selected_period_days = (end_dt - start_dt).days or 1

        query = Room.query.filter(Room.is_active,
                                  Room.filter_available(start_dt, end_dt, (repeat_frequency, repeat_interval),
                                                        include_pre_bookings=True, include_pending_blockings=True))

        if min_capacity is not None:
            query = query.filter(db.or_(Room.capacity >= (min_capacity * 0.8), Room.capacity.is_(None)))
        if room_name:
            query = query.filter(Room.name.ilike('%{}%'.format(room_name)))

        rooms = []
        for room in query:
            booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
            if booking_limit_days is not None and selected_period_days > booking_limit_days:
                continue
            if not room.check_bookable_hours(start_dt.time(), end_dt.time(), quiet=True):
                continue
            rooms.append(room)

        rooms = sorted(rooms, key=lambda r: natural_sort_key(r.full_name))
        return rooms_schema.dumps(rooms).data
