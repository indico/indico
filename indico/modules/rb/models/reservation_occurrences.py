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

from datetime import datetime

from dateutil import rrule
from sqlalchemy import Date, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import cast

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.utils import proxy_to_reservation_if_single_occurrence, Serializer
from indico.util import date_time
from indico.util.date_time import iterdays, format_date
from indico.util.string import return_ascii


class ReservationOccurrence(db.Model, Serializer):
    __tablename__ = 'reservation_occurrences'
    __api_public__ = (('start', 'startDT'), ('end', 'endDT'), 'is_cancelled', 'is_rejected')

    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('reservations.id'),
        nullable=False,
        primary_key=True
    )
    start = db.Column(
        db.DateTime,
        nullable=False,
        primary_key=True,
        index=True
    )
    end = db.Column(
        db.DateTime,
        nullable=False,
        index=True
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
    is_rejected = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    rejection_reason = db.Column(
        db.String
    )

    @hybrid_property
    def date(self):
        return self.start.date()

    @date.expression
    def date(self):
        return cast(self.start, Date)

    @hybrid_property
    def is_valid(self):
        return not self.is_rejected and not self.is_cancelled

    @is_valid.expression
    def is_valid(self):
        return ~self.is_rejected & ~self.is_cancelled

    @return_ascii
    def __repr__(self):
        return u'<ReservationOccurrence({0}, {1}, {2}, {3}, {4}, {5})>'.format(
            self.reservation_id,
            self.start,
            self.end,
            self.is_cancelled,
            self.is_rejected,
            self.is_sent
        )

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
    def filter_overlap(occurrences):
        criteria = []
        for occurrence in occurrences:
            criteria += [
                # other starts after or at our start time         & other starts before our end time
                (ReservationOccurrence.start >= occurrence.start) & (ReservationOccurrence.start < occurrence.end),
                # other ends after our start time              & other ends before or when we end
                (ReservationOccurrence.end > occurrence.start) & (ReservationOccurrence.end <= occurrence.end)
            ]
        return or_(*criteria)

    @staticmethod
    def find_overlapping_with(room, occurrences, reservation_id=None):
        from indico.modules.rb.models.reservations import Reservation

        return ReservationOccurrence.find(Reservation.room == room,
                                          Reservation.id != reservation_id,
                                          ReservationOccurrence.is_valid,
                                          ReservationOccurrence.filter_overlap(occurrences),
                                          _eager=ReservationOccurrence.reservation,
                                          _join=Reservation)

    @staticmethod
    def find_with_filters(filters, avatar=None):
        from indico.modules.rb.models.rooms import Room
        from indico.modules.rb.models.reservations import Reservation

        q = ReservationOccurrence.find(Room.is_active, _join=[Reservation, Room],
                                       _eager=ReservationOccurrence.reservation)

        if 'start_dt' in filters and 'end_dt' in filters:
            start_dt = filters['start_dt']
            end_dt = filters['end_dt']
            criteria = []
            # We have to check the time range for EACH DAY
            for day_start_dt in iterdays(start_dt, end_dt):
                # Same date, but the end time
                day_end_dt = datetime.combine(day_start_dt.date(), end_dt.time())
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

    @proxy_to_reservation_if_single_occurrence
    def cancel(self, user, reason=None, silent=False):
        self.is_cancelled = True
        self.rejection_reason = reason
        if not silent:
            log_msg = 'Day cancelled: {}'.format(format_date(self.date))
            self.reservation.add_edit_log(ReservationEditLog(user_name=user.getFullName(), info=[log_msg]))
            # Notification sent only when the reservation is still valid
            if self.reservation.occurrences.filter_by(is_valid=True).count():
                from indico.modules.rb.notifications.reservation_occurrences import notify_cancellation
                notify_cancellation(self)


    @proxy_to_reservation_if_single_occurrence
    def reject(self, user, reason, silent=False):
        self.is_rejected = True
        self.rejection_reason = reason
        if not silent:
            log = ['Day rejected: {}'.format(format_date(self.date)),
                   'Reason: {}'.format(reason)]
            self.reservation.add_edit_log(ReservationEditLog(user_name=user.getFullName(), info=log))
            # Notification sent only when the reservation is still valid
            if self.reservation.occurrences.filter_by(is_valid=True).count():
                from indico.modules.rb.notifications.reservation_occurrences import notify_rejection
                notify_rejection(self)
