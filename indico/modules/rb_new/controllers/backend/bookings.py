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

import dateutil
from flask import jsonify, request, session
from marshmallow import fields
from marshmallow_enum import EnumField
from webargs.flaskparser import use_args, use_kwargs
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.errors import NoReportError
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.controllers.backend.common import search_room_args
from indico.modules.rb_new.operations.blockings import get_rooms_blockings
from indico.modules.rb_new.operations.bookings import (get_active_bookings, get_booking_occurrences,
                                                       get_matching_events, get_room_bookings, get_room_calendar,
                                                       get_rooms_availability, group_blockings,
                                                       group_nonbookable_periods, has_same_dates, should_split_booking,
                                                       split_booking)
from indico.modules.rb_new.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
from indico.modules.rb_new.operations.suggestions import get_suggestions
from indico.modules.rb_new.schemas import (create_booking_args, reservation_details_schema,
                                           reservation_linked_object_data_schema, reservation_occurrences_schema,
                                           reservation_occurrences_schema_with_permissions,
                                           reservation_user_event_schema)
from indico.modules.rb_new.util import (get_linked_object, group_by_occurrence_date,
                                        is_booking_start_within_grace_period, serialize_blockings,
                                        serialize_nonbookable_periods, serialize_occurrences,
                                        serialize_unbookable_hours)
from indico.modules.users.models.users import User
from indico.util.date_time import now_utc, utc_to_server
from indico.util.i18n import _
from indico.web.util import ExpectedError


NUM_SUGGESTIONS = 5


def _serialize_availability(availability):
    for data in availability.viewvalues():
        data['blockings'] = serialize_blockings(data.get('blockings', {}))
        data['overridable_blockings'] = serialize_blockings(data.get('overridable_blockings', {}))
        data['nonbookable_periods'] = serialize_nonbookable_periods(data.get('nonbookable_periods', {}))
        data['unbookable_hours'] = serialize_unbookable_hours(data.get('unbookable_hours', {}))
        data.update({k: serialize_occurrences(data[k]) if k in data else {}
                     for k in ('candidates', 'conflicting_candidates', 'pre_bookings', 'bookings', 'conflicts',
                               'pre_conflicts', 'rejections', 'cancellations')})
    return availability


def _serialize_booking_details(booking):
    attributes = reservation_details_schema.dump(booking)
    date_range, occurrences = get_booking_occurrences(booking)
    booking_details = dict(attributes)
    occurrences_by_type = dict(bookings={}, cancellations={}, rejections={}, other_bookings={}, blockings={},
                               unbookable_hours={}, nonbookable_periods={})
    booking_details['occurrences'] = occurrences_by_type
    booking_details['date_range'] = [dt.isoformat() for dt in date_range]
    for dt, [occ] in occurrences.iteritems():
        serialized_occ = reservation_occurrences_schema_with_permissions.dump([occ])
        if occ.is_cancelled:
            occurrences_by_type['cancellations'][dt.isoformat()] = serialized_occ
        elif occ.is_rejected:
            occurrences_by_type['rejections'][dt.isoformat()] = serialized_occ
        occurrences_by_type['bookings'][dt.isoformat()] = serialized_occ if occ.is_valid else []

    start_dt = datetime.combine(booking.start_dt, time.min)
    end_dt = datetime.combine(booking.end_dt, time.max)
    unbookable_hours = get_rooms_unbookable_hours([booking.room]).get(booking.room.id, [])
    blockings = get_rooms_blockings([booking.room], start_dt.date(), end_dt.date()).get(booking.room.id, [])
    nonbookable_periods = get_rooms_nonbookable_periods([booking.room], start_dt, end_dt).get(booking.room.id, [])
    nonbookable_periods_grouped = group_nonbookable_periods(nonbookable_periods, date_range)

    occurrences_by_type['other_bookings'] = get_room_bookings(booking.room, start_dt, end_dt,
                                                              skip_booking_id=booking.id)
    occurrences_by_type['blockings'] = serialize_blockings(group_blockings(blockings, date_range))
    occurrences_by_type['unbookable_hours'] = serialize_unbookable_hours(unbookable_hours)
    occurrences_by_type['nonbookable_periods'] = serialize_nonbookable_periods(nonbookable_periods_grouped)
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
        'skip_conflicts_with': fields.List(fields.Int(), missing=None),
        'admin_override_enabled': fields.Bool(missing=False)
    })
    def _process(self, room_ids, **kwargs):
        rooms = [self.room] if self.room else Room.query.filter(Room.id.in_(room_ids), Room.is_active).all()
        date_range, availability = get_rooms_availability(rooms, **kwargs)
        date_range = [dt.isoformat() for dt in date_range]

        for data in availability.viewvalues():
            # add additional helpful attributes
            data.update({
                'num_days_available': len(date_range) - len(data['conflicts']),
                'all_days_available': not data['conflicts'],
                'num_conflicts': len(data['conflicts'])
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
        'start_date': fields.Date(missing=lambda: date.today().isoformat()),
        'end_date': fields.Date(missing=None),
        'my_bookings': fields.Bool(missing=False),
        'show_inactive': fields.Bool(missing=False),
        'room_ids': fields.List(fields.Int(), missing=None)
    })
    def _process(self, start_date, end_date, room_ids, my_bookings, show_inactive):
        booked_for_user = session.user if my_bookings else None
        if end_date is None:
            end_date = start_date
        calendar = get_room_calendar(start_date, end_date, room_ids, booked_for_user=booked_for_user,
                                     include_inactive=show_inactive)
        return jsonify(_serialize_availability(calendar).values())


class RHActiveBookings(RHRoomBookingBase):
    @use_kwargs({
        'room_ids': fields.List(fields.Int(), missing=None),
        'start_dt': fields.DateTime(missing=None),
        'last_reservation_id': fields.Int(missing=None),
        'my_bookings': fields.Bool(missing=False),
        'limit': fields.Int(missing=40),
    })
    def _process(self, room_ids, start_dt, last_reservation_id, my_bookings, limit):
        start_dt = start_dt or datetime.combine(date.today(), time(0, 0))
        booked_for_user = session.user if my_bookings else None
        bookings, rows_left = get_active_bookings(limit=limit,
                                                  start_dt=start_dt,
                                                  last_reservation_id=last_reservation_id,
                                                  room_ids=room_ids,
                                                  booked_for_user=booked_for_user)
        return jsonify(bookings=serialize_occurrences(bookings), rows_left=rows_left)


class RHCreateBooking(RHRoomBookingBase):
    @use_args(create_booking_args)
    def _process_args(self, args):
        self.args = args
        self.prebook = args.pop('is_prebooking')
        self.room = Room.get_one(self.args.pop('room_id'))
        if not self.room.is_active:
            raise BadRequest

    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if (self.prebook and not self.room.can_prebook(session.user) or
                (not self.prebook and not self.room.can_book(session.user))):
            raise Forbidden('Not authorized to book this room')

    def _validate_room_booking_limit(self, start_dt, end_dt, booking_limit_days):
        day_start_dt = datetime.combine(start_dt.date(), time())
        day_end_dt = datetime.combine(end_dt.date(), time(23, 59))
        selected_period_days = (day_end_dt - day_start_dt).days
        return selected_period_days <= booking_limit_days

    def _link_booking(self, booking, type_, id_, link_back):
        obj = get_linked_object(type_, id_)
        if obj is None or not obj.event.can_manage(session.user):
            return
        booking.linked_object = obj
        if link_back:
            obj.inherit_location = False
            obj.room = self.room

    def _process(self):
        args = self.args
        args.setdefault('booked_for_user', session.user)

        if not is_booking_start_within_grace_period(args['start_dt'], session.user, args['admin_override_enabled']):
            raise ExpectedError(_('You cannot create a booking which starts in the past'))

        # Check that the booking is not longer than allowed
        booking_limit_days = self.room.booking_limit_days or rb_settings.get('booking_limit')
        if not self._validate_room_booking_limit(args['start_dt'], args['end_dt'], booking_limit_days):
            msg = (_('Bookings for the room "{}" may not be longer than {} days')
                   .format(self.room.name, booking_limit_days))
            raise ExpectedError(msg)

        try:
            resv = Reservation.create_from_data(self.room, args, session.user, prebook=self.prebook)
            if args.get('link_type') is not None and args.get('link_id') is not None:
                self._link_booking(resv, args['link_type'], args['link_id'], args['link_back'])
            db.session.flush()
        except NoReportError as e:
            db.session.rollback()
            raise ExpectedError(unicode(e))

        serialized_occurrences = serialize_occurrences(group_by_occurrence_date(resv.occurrences.all()))
        if self.prebook:
            data = {'pre_bookings': serialized_occurrences}
        else:
            data = {'bookings': serialized_occurrences}
        return jsonify(room_id=self.room.id, booking=reservation_details_schema.dump(resv), calendar_data=data)


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
        funcs = {'approve': self.booking.can_accept,
                 'reject': self.booking.can_reject,
                 'cancel': self.booking.can_cancel}

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
        elif self.action == 'reject':
            self.reject()
        elif self.action == 'cancel':
            self.booking.cancel(session.user)
        return jsonify(booking=reservation_details_schema.dump(self.booking))


class RHDeleteBooking(RHBookingBase):
    def _check_access(self):
        RHBookingBase._check_access(self)
        if not self.booking.can_delete(session.user):
            raise Forbidden

    def _process(self):
        booking_id = self.booking.id
        room_id = self.booking.room.id
        signals.rb.booking_deleted.send(self.booking)
        db.session.delete(self.booking)
        return jsonify(booking_id=booking_id, room_id=room_id)


class RHLinkedObjectData(RHRoomBookingBase):
    """Fetch data from event, contribution or session block"""

    def _process_args(self):
        type_ = LinkType[request.view_args['type']]
        id_ = request.view_args['id']
        self.linked_object = get_linked_object(type_, id_)

    def _process(self):
        if not self.linked_object or not self.linked_object.can_access(session.user):
            return jsonify(can_access=False)
        return jsonify(can_access=True, **reservation_linked_object_data_schema.dump(self.linked_object))


class RHUpdateBooking(RHBookingBase):
    def _check_access(self):
        RHBookingBase._check_access(self)
        if not self.booking.can_edit(session.user):
            raise Forbidden

    @use_args(create_booking_args)
    def _process(self, args):
        new_booking_data = {
            'booking_reason': args['booking_reason'],
            'booked_for_user': args.get('booked_for_user', self.booking.booked_for_user),
            'start_dt': args['start_dt'],
            'end_dt': args['end_dt'],
            'repeat_frequency': args['repeat_frequency'],
            'repeat_interval': args['repeat_interval'],
        }

        additional_booking_attrs = {}
        if not should_split_booking(self.booking, new_booking_data):
            has_date_changed = not has_same_dates(self.booking, new_booking_data)
            room = self.booking.room
            self.booking.modify(new_booking_data, session.user)
            if (has_date_changed and not room.can_book(session.user, allow_admin=False) and
                    room.can_prebook(session.user, allow_admin=False) and self.booking.is_accepted):
                self.booking.reset_approval(session.user)
        else:
            new_booking = split_booking(self.booking, new_booking_data)
            additional_booking_attrs['new_booking_id'] = new_booking.id

        db.session.flush()
        today = date.today()
        calendar = get_room_calendar(args['start_dt'] or today, args['end_dt'] or today, [args['room_id']])
        return jsonify(booking=dict(_serialize_booking_details(self.booking), **additional_booking_attrs),
                       room_calendar=_serialize_availability(calendar).values())


class RHMyUpcomingBookings(RHRoomBookingBase):
    def _process(self):
        q = (ReservationOccurrence.query
             .filter(ReservationOccurrence.start_dt > utc_to_server(now_utc()),
                     ReservationOccurrence.is_valid,
                     db.or_(Reservation.booked_for_user == session.user,
                            Reservation.created_by_user == session.user))
             .join(Reservation)
             .order_by(ReservationOccurrence.start_dt.asc())
             .limit(5))
        return jsonify(reservation_occurrences_schema.dump(q))


class RHMatchingEvents(RHRoomBookingBase):
    """Get events suitable for booking linking."""

    @use_kwargs({
        'start_dt': fields.DateTime(),
        'end_dt': fields.DateTime(),
        'repeat_frequency': EnumField(RepeatFrequency, missing='NEVER'),
        'repeat_interval': fields.Int(missing=1),
    })
    def _process(self, start_dt, end_dt, repeat_frequency, repeat_interval):
        events = get_matching_events(start_dt, end_dt, repeat_frequency, repeat_interval)
        return jsonify(reservation_user_event_schema.dump(events))


class RHBookingOccurrenceStateActions(RHBookingBase):
    """Reject or cancel booking occurrence."""

    def _process_args(self):
        RHBookingBase._process_args(self)
        date = dateutil.parser.parse(request.view_args['date'], yearfirst=True).date()
        self.occurrence = self.booking.occurrences.filter(ReservationOccurrence.date == date).one()
        self.action = request.view_args['action']

    def _check_access(self):
        RHBookingBase._check_access(self)
        funcs = {'reject': self.occurrence.can_reject,
                 'cancel': self.occurrence.can_cancel}

        if self.action not in funcs or not funcs[self.action](session.user):
            raise Forbidden

    @use_kwargs({
        'reason': fields.String(required=True)
    })
    def reject(self, reason):
        self.occurrence.reject(session.user, reason)

    def _process(self):
        if self.action == 'reject':
            self.reject()
        elif self.action == 'cancel':
            self.occurrence.cancel(session.user)
        return jsonify(occurrence=reservation_occurrences_schema.dump(self.occurrence, many=False))
