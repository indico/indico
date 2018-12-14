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

from flask import jsonify, request, session
from marshmallow import fields
from marshmallow_enum import EnumField
from webargs.flaskparser import use_args, use_kwargs
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.core.errors import NoReportError
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.controllers.backend.common import search_room_args
from indico.modules.rb_new.operations.bookings import get_booking_occurrences, get_room_calendar, get_rooms_availability
from indico.modules.rb_new.operations.suggestions import get_suggestions
from indico.modules.rb_new.schemas import (create_booking_args, reservation_details_occurrences_schema,
                                           reservation_details_schema, reservation_event_data_schema,
                                           reservation_occurrences_schema)
from indico.modules.rb_new.util import (group_by_occurrence_date, serialize_blockings, serialize_nonbookable_periods,
                                        serialize_occurrences, serialize_unbookable_hours)
from indico.modules.users.models.users import User
from indico.util.date_time import now_utc, utc_to_server
from indico.util.i18n import _
from indico.web.util import ExpectedError


NUM_SUGGESTIONS = 5


def _serialize_availability(availability):
    for data in availability.viewvalues():
        data['blockings'] = serialize_blockings(data['blockings'])
        data['nonbookable_periods'] = serialize_nonbookable_periods(data['nonbookable_periods'])
        data['unbookable_hours'] = serialize_unbookable_hours(data['unbookable_hours'])
        data.update({k: serialize_occurrences(data[k]) if k in data else {}
                     for k in ['candidates', 'pre_bookings', 'bookings', 'conflicts', 'pre_conflicts']})
    return availability


def _serialize_booking_details(booking):
    attributes = reservation_details_schema.dump(booking).data
    date_range, occurrences = get_booking_occurrences(booking)
    date_range = [dt.isoformat() for dt in date_range]
    occurrences = {dt.isoformat(): reservation_details_occurrences_schema.dump(data).data
                   for dt, data in occurrences.iteritems()}
    booking_details = dict(attributes)
    booking_details['occurrences'] = occurrences
    booking_details['date_range'] = date_range
    return booking_details


class RHTimeline(RHRoomBookingBase):
    def _process_args(self):
        self.room = None
        if 'room_id' in request.view_args:
            self.room = Room.get_one(request.view_args['room_id'])
            if not self.room.is_active:
                raise NotFound

    @use_kwargs({
        'start_dt': fields.DateTime(required=True),
        'end_dt': fields.DateTime(required=True),
        'repeat_frequency': EnumField(RepeatFrequency, missing='NEVER'),
        'repeat_interval': fields.Int(missing=1),
        'room_ids': fields.List(fields.Int(), missing=[]),
    })
    def _process(self, room_ids, **kwargs):
        rooms = [self.room] if self.room else Room.query.filter(Room.id.in_(room_ids), Room.is_active).all()
        date_range, availability = get_rooms_availability(rooms, **kwargs)
        date_range = [dt.isoformat() for dt in date_range]

        for data in availability.viewvalues():
            # add additional helpful attributes
            data.update({
                'num_days_available': len(date_range) - len(data['conflicts']),
                'all_days_available': not data['conflicts']
            })
        serialized = _serialize_availability(availability)
        if self.room:
            availability = serialized[self.room.id]
        else:
            # keep order of original room id list
            availability = sorted(serialized.items(), key=lambda x: room_ids.index(x[0]))
        return jsonify(availability=availability, date_range=date_range)


class RHCalendar(RHRoomBookingBase):
    @use_kwargs({
        'start_date': fields.Date(),
        'end_date': fields.Date(),
        'my_bookings': fields.Bool(missing=False),
        'room_ids': fields.List(fields.Int(), missing=None)
    })
    def _process(self, start_date, end_date, room_ids, my_bookings):
        booked_for_user = session.user if my_bookings else None
        calendar = get_room_calendar(start_date or date.today(), end_date or date.today(), room_ids,
                                     booked_for_user=booked_for_user)
        return jsonify(_serialize_availability(calendar).values())


class RHCreateBooking(RHRoomBookingBase):
    def _validate_room_booking_limit(self, start_dt, end_dt, booking_limit_days):
        day_start_dt = datetime.combine(start_dt.date(), time())
        day_end_dt = datetime.combine(end_dt.date(), time(23, 59))
        selected_period_days = (day_end_dt - day_start_dt).days
        return selected_period_days <= booking_limit_days

    @use_args(create_booking_args)
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
            raise ExpectedError(msg)

        try:
            resv = Reservation.create_from_data(room, dict(args, booked_for_user=booked_for), session.user,
                                                prebook=is_prebooking)
            db.session.flush()
        except NoReportError as e:
            db.session.rollback()
            raise ExpectedError(unicode(e))

        serialized_occurrences = serialize_occurrences(group_by_occurrence_date(resv.occurrences.all()))
        if is_prebooking:
            data = {'pre_bookings': serialized_occurrences}
        else:
            data = {'bookings': serialized_occurrences}
        return jsonify(room_id=room.id, booking=reservation_details_schema.dump(resv).data, calendar_data=data)


class RHRoomSuggestions(RHRoomBookingBase):
    @use_args(search_room_args)
    def _process(self, args):
        return jsonify(get_suggestions(args, limit=NUM_SUGGESTIONS))


class RHBookingBase(RHRoomBookingBase):
    def _process_args(self):
        self.booking = Reservation.get_one(request.view_args['booking_id'])


class RHBookingDetails(RHBookingBase):
    def _process(self):
        return jsonify(_serialize_booking_details(self.booking))


class RHBookingStateActions(RHBookingBase):
    def _process_args(self):
        RHBookingBase._process_args(self)
        self.action = request.view_args['action']

    def _check_access(self):
        RHBookingBase._check_access(self)
        funcs = {'approve': self.booking.can_be_accepted,
                 'reject': self.booking.can_be_rejected,
                 'cancel': self.booking.can_be_cancelled}

        if self.action not in funcs or not funcs[self.action](session.user):
            raise Forbidden

    @use_kwargs({
        'reason': fields.String(required=True)
    })
    def reject(self, reason):
        self.booking.reject(session.user, reason)

    def _process(self):
        if self.action == 'approve':
            self.booking.accept(session.user)
            state = 'approved'
        elif self.action == 'reject':
            self.reject()
            state = 'rejected'
        elif self.action == 'cancel':
            self.booking.cancel(session.user)
            state = 'cancelled'
        return jsonify(booking=reservation_details_schema.dump(self.booking).data, booking_state=state)


class RHBookingDelete(RHBookingBase):
    def _check_access(self):
        RHBookingBase._check_access(self)
        if not self.booking.can_be_deleted(session.user):
            raise Forbidden

    def _process(self):
        booking_id = self.booking.id
        room_id = self.booking.room.id
        db.session.delete(self.booking)
        return jsonify(booking_id=booking_id, room_id=room_id)


class RHBookingEventData(RHBookingBase):
    def _process(self):
        if self.booking.event is None:
            raise NotFound
        if not self.booking.event.can_access(session.user):
            return jsonify(can_access=False)
        return jsonify(reservation_event_data_schema.dump(self.booking.event).data)


class RHUpdateBooking(RHBookingBase):
    @use_args(create_booking_args)
    def _process(self, args):
        data = {
            'booking_reason': args['booking_reason'],
            'room_usage': 'current_user' if args.get('user_id', None) is None else 'someone',
            'booked_for_user': User.get(args.get('user_id', session.user.id)),
            'start_dt': args['start_dt'],
            'end_dt': args['end_dt'],
            'repeat_frequency': args['repeat_frequency'],
            'repeat_interval': args['repeat_interval'],
        }

        self.booking.modify(data, session.user)
        db.session.flush()

        start_date = args['start_dt']
        end_date = args['end_dt']
        calendar = get_room_calendar(start_date or date.today(), end_date or date.today(), [args['room_id']])
        return jsonify(booking=_serialize_booking_details(self.booking),
                       room_calendar=_serialize_availability(calendar).values())


class RHMyUpcomingBookings(RHRoomBookingBase):
    def _process(self):
        q = (ReservationOccurrence.query
             .filter(ReservationOccurrence.start_dt > utc_to_server(now_utc()),
                     db.or_(
                         Reservation.booked_for_user == session.user,
                         Reservation.created_by_user == session.user))
             .join(Reservation)
             .order_by(ReservationOccurrence.start_dt.asc())
             .limit(5))
        return jsonify(reservation_occurrences_schema.dump(q).data)
