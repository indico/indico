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

"""
Sent notifications of a reservation
"""

from datetime import datetime, timedelta

from dateutil import rrule
from sqlalchemy import or_
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.errors import IndicoError
from indico.util import date_time
from indico.util.date_time import server_to_utc, iterdays, as_utc
from indico.util.string import return_ascii


class ReservationOccurrence(db.Model):
    __tablename__ = 'reservation_occurrences'

    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('reservations.id'),
        nullable=False,
        primary_key=True
    )
    start = db.Column(
        UTCDateTime,
        nullable=False,
        primary_key=True
    )
    end = db.Column(
        UTCDateTime,
        nullable=False
    )
    is_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    is_cancelled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    rejection_reason = db.Column(
        db.String,
    )

    @return_ascii
    def __repr__(self):
        return u'<ReservationOccurrence({0}, {1}, {2}, {3}, {4})>'.format(
            self.reservation_id,
            self.start,
            self.end,
            self.is_cancelled,
            self.is_sent
        )

    @property
    def date(self):
        return self.start.date()

    @classmethod
    def create_series_for_reservation(cls, reservation):
        for o in cls.iter_create_occurrences(reservation.start_date, reservation.end_date, reservation.repetition):
            o.reservation = reservation

    @classmethod
    def create_series(cls, start, end, repetition):
        return list(cls.iter_create_occurrences(start, end, repetition))

    @classmethod
    def iter_create_occurrences(cls, start, end, repetition):
        for start in cls.iter_start_time(start, end, repetition):
            end = datetime.combine(start.date(), end.time())
            end = start.tzinfo.localize(end)
            yield ReservationOccurrence(start=start, end=end)

    @staticmethod
    def iter_start_time(start, end, repetition):
        from .reservations import RepeatUnit
        repeat_unit, repeat_step = repetition

        if repeat_unit == RepeatUnit.NEVER:
            return [start]

        if repeat_unit == RepeatUnit.DAY:
            return rrule.rrule(rrule.DAILY, dtstart=start, until=end)

        elif repeat_unit == RepeatUnit.WEEK:
            if 0 < repeat_step < 4:
                return rrule.rrule(rrule.WEEKLY, dtstart=start, until=end, interval=repeat_step)
            else:
                raise IndicoError('Unsupported interval')

        elif repeat_unit == RepeatUnit.MONTH:
            if repeat_step == 1:
                position = start.day // 7 + 1
                return rrule.rrule(rrule.MONTHLY, dtstart=start, until=end, byweekday=start.weekday(), bysetpos=position)
            else:
                raise IndicoError('Unsupported interval')

        elif repeat_unit == RepeatUnit.YEAR:
            raise IndicoError('Unsupported frequency')

        raise IndicoError('Unexpected frequency')

    @staticmethod
    def find_with_filters(filters, avatar=None):
        from indico.modules.rb.models.rooms import Room
        from indico.modules.rb.models.reservations import Reservation

        q = ReservationOccurrence.find(Room.is_active, _join=[Reservation, Room],
                                       _eager=ReservationOccurrence.reservation)

        if 'start_dt' in filters and 'end_dt' in filters:
            start_dt = server_to_utc(filters['start_dt'])
            end_dt = server_to_utc(filters['end_dt'])
            criteria = []
            # We have to check the time range for EACH DAY
            for day_start_dt in iterdays(start_dt, end_dt):
                # Same date, but the end time
                day_end_dt = as_utc(datetime.combine(day_start_dt.date(), end_dt.time()))
                # But this breaks wih some times because converting to UTC may cause the date to change
                # In this case we can simply fix the end date by adding 1 day
                if day_end_dt < day_start_dt:
                    day_end_dt += timedelta(days=1)
                criteria += [
                    (ReservationOccurrence.start >= day_start_dt) & (ReservationOccurrence.start < day_end_dt),
                    (ReservationOccurrence.end > day_start_dt) & (ReservationOccurrence.end <= day_end_dt)
                ]
            q = q.filter(or_(*criteria))

        if filters.get('is_only_my_rooms') and avatar:
            q = q.filter(Room.owner_id == avatar.id)
        if filters.get('is_only_mine') and avatar:
            q = q.filter(Reservation.booked_for_id == avatar.id)
        if filters.get('room_ids'):
            q = q.filter(Room.id.in_(filters['room_ids']))

        if filters.get('is_only_confirmed_bookings') and not filters.get('is_only_pending_bookings'):
            q = q.filter(Reservation.is_confirmed)
        elif not filters.get('is_only_confirmed_bookings') and filters.get('is_only_pending_bookings'):
            q = q.filter(~Reservation.is_confirmed)

        if filters.get('is_rejected'):
            q = q.filter(Reservation.is_rejected | ReservationOccurrence.is_rejected)
        else:
            q = q.filter(~Reservation.is_rejected & ~ReservationOccurrence.is_rejected)
        if filters.get('is_cancelled'):
            q = q.filter(Reservation.is_cancelled | ReservationOccurrence.is_cancelled)
        else:
            q = q.filter(~Reservation.is_cancelled & ~ReservationOccurrence.is_cancelled)
        if filters.get('is_archived'):
            q = q.filter(Reservation.is_archived)

        if filters.get('uses_video_conference'):
            q = q.filter(Reservation.uses_video_conference)
        if filters.get('needs_video_conference_setup'):
            q = q.filter(Reservation.needs_video_conference_setup)
        if filters.get('needs_general_assistance'):
            q = q.filter(Reservation.needs_general_assistance)

        if filters.get('booked_for_name'):
            qs = u'%{}%'.format(filters['booked_for_name'])
            q = q.filter(Reservation.booked_for_name.ilike(qs))
        if filters.get('reason'):
            qs = u'%{}%'.format(filters['reason'])
            q = q.filter(Reservation.booking_reason.ilike(qs))

        q = q.order_by(Room.id)
        return q

    def overlaps(self, occurrence, skip_self=False):
        if self.reservation and occurrence.reservation and self.reservation.room_id != occurrence.reservation.room_id:
            raise ValueError('ReservationOccurrence objects of different rooms')
        if skip_self and self.reservation and occurrence.reservation and self.reservation == occurrence.reservation:
            return False
        return date_time.overlaps((self.start, self.end), (occurrence.start, occurrence.end))

    def get_overlap(self, occurrence, skip_self=False):
        if self.reservation and occurrence.reservation and self.reservation.room_id != occurrence.reservation.room_id:
            raise ValueError('ReservationOccurrence objects of different rooms')
        if skip_self and self.reservation and occurrence.reservation and self.reservation == occurrence.reservation:
            return None, None
        return date_time.get_overlap((self.start, self.end), (occurrence.start, occurrence.end))

    def cancel(self, reason):
        print 'CANCEL', self, reason
        self.is_cancelled = True
        self.rejection_reason = reason

    def reject(self, reason):
        # TODO: is_rejected
        print 'REJECT', self, reason
        self.cancel(reason)

    @hybrid_property
    def is_rejected(self):
        return self.is_cancelled

    @hybrid_property
    def is_valid(self):
        return not self.is_rejected and not self.is_cancelled

    @is_valid.expression
    def is_valid(self):
        return ~self.is_rejected & ~self.is_cancelled

    def notify_rejection(self, reason=''):
        return self.reservation.notify_rejection(reason, self.date)

    def notify_cancellation(self):
        return self.reservation.notify_cancellation(self.date)

