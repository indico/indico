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

from datetime import date, datetime, time

from flask import jsonify, session
from marshmallow_enum import EnumField
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs

from indico.core.db import db
from indico.core.errors import NoReportError
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.controllers.backend.common import search_room_args
from indico.modules.rb_new.schemas import reservation_schema, rooms_schema
from indico.modules.rb_new.util import (get_room_calendar, get_rooms_availability, get_suggestions, search_for_rooms,
                                        serialize_blockings, serialize_nonbookable_periods, serialize_occurrences,
                                        serialize_unbookable_hours)
from indico.modules.users.models.users import User
from indico.util.i18n import _
from indico.web.util import jsonify_data, ExpectedError


NUM_SUGGESTIONS = 5


def _serialize_availability(availability):
    for data in availability.viewvalues():
        data['room'] = rooms_schema.dump(data['room'], many=False).data
        data['blockings'] = serialize_blockings(data['blockings'])
        data['nonbookable_periods'] = serialize_nonbookable_periods(data['nonbookable_periods'])
        data['unbookable_hours'] = serialize_unbookable_hours(data['unbookable_hours'])
        data.update({k: serialize_occurrences(data[k]) if k in data else []
                     for k in ['candidates', 'pre_bookings', 'bookings', 'conflicts', 'pre_conflicts']})
    return availability


class RHTimeline(RHRoomBookingBase):
    @use_args(dict(search_room_args, **{
        'limit': fields.Int(missing=None),
        'additional_room_ids': fields.List(fields.Int())
    }))
    def _process(self, args):
        query = search_for_rooms(args, only_available=True)
        if 'limit' in args:
            query = query.limit(args.pop('limit'))

        rooms = query.all()
        if 'additional_room_ids' in args:
            rooms.extend(Room.query.filter(Room.is_active, Room.id.in_(args.pop('additional_room_ids'))))

        date_range, availability = get_rooms_availability(rooms, args['start_dt'], args['end_dt'],
                                                          args['repeat_frequency'], args['repeat_interval'],
                                                          flexibility=0)
        date_range = [dt.isoformat() for dt in date_range]

        for data in availability.viewvalues():
            # add additional helpful attributes
            data.update({
                'num_days_available': len(date_range) - len(data['conflicts']),
                'all_days_available': not data['conflicts']
            })

        return jsonify_data(flash=False,
                            availability=_serialize_availability(availability),
                            date_range=date_range)


class RHCalendar(RHRoomBookingBase):
    @use_kwargs({
        'start_date': fields.Date(),
        'end_date': fields.Date(),
    })
    def _process(self, start_date, end_date):
        calendar = get_room_calendar(start_date or date.today(), end_date or date.today())
        return jsonify_data(flash=False, calendar=_serialize_availability(calendar).values())


class RHCreateBooking(RHRoomBookingBase):
    def _validate_room_booking_limit(self, start_dt, end_dt, booking_limit_days):
        day_start_dt = datetime.combine(start_dt.date(), time())
        day_end_dt = datetime.combine(end_dt.date(), time(23, 59))
        selected_period_days = (day_end_dt - day_start_dt).days
        return selected_period_days <= booking_limit_days

    @use_args({
        'start_dt': fields.DateTime(required=True),
        'end_dt': fields.DateTime(required=True),
        'repeat_frequency': EnumField(RepeatFrequency, required=True),
        'repeat_interval': fields.Int(missing=0),
        'room_id': fields.Int(required=True),
        'user_id': fields.Int(),
        'booking_reason': fields.String(load_from='reason', validate=validate.Length(min=3)),
        'is_prebooking': fields.Bool(missing=False)
    })
    def _process(self, args):
        room = Room.get_one(args.pop('room_id'))
        user_id = args.pop('user_id', None)
        booked_for = User.get_one(user_id) if user_id else session.user
        is_prebooking = args.pop('is_prebooking')

        # Check that the booking is not longer than allowed
        booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
        if not self._validate_room_booking_limit(args['start_dt'], args['end_dt'], booking_limit_days):
            msg = (_('Bookings for the room "{}" may not be longer than {} days')
                   .format(room.name, booking_limit_days))
            return jsonify(success=False, msg=msg)

        try:
            resv = Reservation.create_from_data(room, dict(args, booked_for_user=booked_for), session.user,
                                                prebook=is_prebooking)
            db.session.flush()
        except NoReportError as e:
            db.session.rollback()
            raise ExpectedError(unicode(e))
        return jsonify(booking=reservation_schema.dump(resv).data)


class RHRoomSuggestions(RHRoomBookingBase):
    @use_args(search_room_args)
    def _process(self, args):
        return jsonify([dict(suggestion, room=rooms_schema.dump(suggestion['room'], many=False).data)
                        for suggestion in get_suggestions(args, limit=NUM_SUGGESTIONS)])
