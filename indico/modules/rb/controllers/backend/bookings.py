# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import uuid
from datetime import date, datetime, time

import dateutil
from flask import jsonify, request, session
from marshmallow import fields, validate
from marshmallow_enum import EnumField
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.errors import NoReportError
from indico.legacy.common.cache import GenericCache
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.backend.common import search_room_args
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.operations.bookings import (get_active_bookings, get_booking_edit_calendar_data,
                                                   get_matching_events, get_room_calendar, get_rooms_availability,
                                                   has_same_slots, should_split_booking, split_booking)
from indico.modules.rb.operations.suggestions import get_suggestions
from indico.modules.rb.schemas import (CreateBookingSchema, reservation_details_schema,
                                       reservation_linked_object_data_schema, reservation_occurrences_schema,
                                       reservation_user_event_schema)
from indico.modules.rb.util import (generate_spreadsheet_from_occurrences, get_linked_object, get_prebooking_collisions,
                                    group_by_occurrence_date, is_booking_start_within_grace_period,
                                    serialize_availability, serialize_booking_details, serialize_occurrences)
from indico.util.date_time import now_utc, utc_to_server
from indico.util.i18n import _
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.args import use_args, use_kwargs
from indico.web.flask.util import url_for
from indico.web.util import ExpectedError


NUM_SUGGESTIONS = 5


_export_cache = GenericCache('bookings-export')


class RHTimeline(RHRoomBookingBase):
    def _process_args(self):
        self.room = None
        if 'room_id' in request.view_args:
            self.room = Room.get_or_404(request.view_args['room_id'], is_deleted=False)

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
        rooms = [self.room] if self.room else Room.query.filter(Room.id.in_(room_ids), ~Room.is_deleted).all()
        date_range, availability = get_rooms_availability(rooms, **kwargs)
        date_range = [dt.isoformat() for dt in date_range]

        for data in availability.viewvalues():
            # add additional helpful attributes
            data.update({
                'num_days_available': len(date_range) - len(data['conflicts']),
                'all_days_available': not data['conflicts'],
                'num_conflicts': len(data['conflicts'])
            })
        serialized = serialize_availability(availability)
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
        'room_ids': fields.List(fields.Int(), missing=None),
        'text': fields.String(missing=None)
    })
    def _process(self, start_date, end_date, room_ids, my_bookings, show_inactive, text):
        booked_for_user = session.user if my_bookings else None
        if end_date is None:
            end_date = start_date
        calendar = get_room_calendar(start_date, end_date, room_ids, booked_for_user=booked_for_user,
                                     include_inactive=show_inactive, text=text)
        return jsonify(serialize_availability(calendar).values())


class RHActiveBookings(RHRoomBookingBase):
    @use_kwargs({
        'room_ids': fields.List(fields.Int(), missing=None),
        'start_dt': fields.DateTime(missing=None),
        'last_reservation_id': fields.Int(missing=None),
        'my_bookings': fields.Bool(missing=False),
        'limit': fields.Int(missing=40),
        'text': fields.String(missing=None)
    })
    def _process(self, room_ids, start_dt, last_reservation_id, my_bookings, limit, text):
        start_dt = start_dt or datetime.combine(date.today(), time(0, 0))
        booked_for_user = session.user if my_bookings else None
        bookings, rows_left = get_active_bookings(limit=limit,
                                                  start_dt=start_dt,
                                                  last_reservation_id=last_reservation_id,
                                                  room_ids=room_ids,
                                                  booked_for_user=booked_for_user,
                                                  text=text)
        return jsonify(bookings=serialize_occurrences(bookings), rows_left=rows_left)


class RHCreateBooking(RHRoomBookingBase):
    @use_args(CreateBookingSchema)
    def _process_args(self, args):
        self.args = args
        self.prebook = args.pop('is_prebooking')
        self.room = Room.get_or_404(self.args.pop('room_id'), is_deleted=False)

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
        self.booking = Reservation.get_or_404(request.view_args['booking_id'])
        if self.booking.room.is_deleted:
            raise NotFound(_('The room has been deleted'))


class RHBookingDetails(RHBookingBase):
    def _process(self):
        return jsonify(serialize_booking_details(self.booking))


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

    @use_kwargs({
        'reason': fields.String(required=False),
        'force': fields.Bool(required=False)
    })
    def accept(self, reason=None, force=False):
        if not force:
            collisions = get_prebooking_collisions(self.booking)
            if collisions:
                collision_data = reservation_occurrences_schema.dump(collisions)
                raise ExpectedError('prebooking_collision', data=collision_data)
        self.booking.accept(session.user, reason)

    def _process(self):
        if self.action == 'approve':
            self.accept()
        elif self.action == 'reject':
            self.reject()
        elif self.action == 'cancel':
            self.booking.cancel(session.user)
        return jsonify(booking=serialize_booking_details(self.booking))


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


class RHBookingEditCalendars(RHBookingBase):
    @use_kwargs({
        'start_dt': fields.DateTime(required=True),
        'end_dt': fields.DateTime(required=True),
        'repeat_frequency': EnumField(RepeatFrequency, missing='NEVER'),
        'repeat_interval': fields.Int(missing=1),
    })
    def _process(self, **kwargs):
        return jsonify(get_booking_edit_calendar_data(self.booking, kwargs))


class RHUpdateBooking(RHBookingBase):
    def _check_access(self):
        RHBookingBase._check_access(self)
        if not self.booking.can_edit(session.user):
            raise Forbidden

    @use_args(CreateBookingSchema)
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
            has_slot_changed = not has_same_slots(self.booking, new_booking_data)
            room = self.booking.room
            self.booking.modify(new_booking_data, session.user)
            if (has_slot_changed and not room.can_book(session.user, allow_admin=False) and
                    room.can_prebook(session.user, allow_admin=False) and self.booking.is_accepted):
                self.booking.reset_approval(session.user)
        else:
            new_booking = split_booking(self.booking, new_booking_data)
            additional_booking_attrs['new_booking_id'] = new_booking.id

        db.session.flush()
        today = date.today()
        calendar = get_room_calendar(args['start_dt'] or today, args['end_dt'] or today, [args['room_id']])
        return jsonify(booking=dict(serialize_booking_details(self.booking), **additional_booking_attrs),
                       room_calendar=serialize_availability(calendar).values())


class RHMyUpcomingBookings(RHRoomBookingBase):
    def _process(self):
        q = (ReservationOccurrence.query
             .filter(ReservationOccurrence.start_dt > utc_to_server(now_utc()),
                     ReservationOccurrence.is_valid,
                     db.or_(Reservation.booked_for_user == session.user,
                            Reservation.created_by_user == session.user),
                     ~Room.is_deleted)
             .join(Reservation)
             .join(Room)
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


class RHBookingExport(RHRoomBookingBase):
    @use_kwargs({
        'room_ids': fields.List(fields.Int(), required=True),
        'start_date': fields.Date(required=True),
        'end_date': fields.Date(required=True),
        'format': fields.Str(validate.OneOf({'csv', 'xlsx'}), required=True),
    })
    def _process(self, room_ids, start_date, end_date, format):
        occurrences = (ReservationOccurrence.query
                       .join(ReservationOccurrence.reservation)
                       .filter(Reservation.room_id.in_(room_ids),
                               ReservationOccurrence.is_valid,
                               db_dates_overlap(ReservationOccurrence,
                                                'start_dt', datetime.combine(start_date, time()),
                                                'end_dt', datetime.combine(end_date, time.max)))).all()

        token = unicode(uuid.uuid4())
        headers, rows = generate_spreadsheet_from_occurrences(occurrences)
        _export_cache.set(token, {'headers': headers, 'rows': rows}, time=1800)
        download_url = url_for('rb.export_bookings_file', format=format, token=token)
        return jsonify(url=download_url)


class RHBookingExportFile(RHRoomBookingBase):
    def _process(self):
        data = _export_cache.get(request.args['token'])
        file_format = request.view_args['format']
        if file_format == 'csv':
            return send_csv('bookings.csv', **data)
        elif file_format == 'xlsx':
            return send_xlsx('bookings.xlsx', **data)
