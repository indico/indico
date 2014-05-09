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

from datetime import datetime

from dateutil import rrule

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.errors import IndicoError
from indico.util import date_time
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
        for o in cls.iter_create_occurrences(reservation.start, reservation.end, reservation.repetition):
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
                position = start.day // 7
                return rrule.rrule(rrule.MONTHLY, dtstart=start, until=end, byweekday=start.weekday(), bysetpos=position)
            else:
                raise IndicoError('Unsupported interval')

        elif repeat_unit == RepeatUnit.YEAR:
            raise IndicoError('Unsupported frequency')

        raise IndicoError('Unexpected frequency')

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

    def reject(self, reason):
        self.is_cancelled = True
        self.rejection_reason = reason

    def notify_rejection(self, reason=''):
        return self.reservation.notify_rejection(reason, self.date)

    def notify_cancellation(self):
        return self.reservation.notify_cancellation(self.date)

