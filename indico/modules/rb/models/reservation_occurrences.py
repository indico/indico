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

from datetime import datetime
from math import ceil

from dateutil import rrule
from sqlalchemy import Date, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import defaultload
from sqlalchemy.sql import cast

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.errors import IndicoError
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.util import proxy_to_reservation_if_last_valid_occurrence
from indico.util import date_time
from indico.util.date_time import iterdays, format_date
from indico.util.serializer import Serializer
from indico.util.string import return_ascii
from indico.util.user import unify_user_args


class ReservationOccurrence(db.Model, Serializer):
    __tablename__ = 'reservation_occurrences'
    __table_args__ = {'schema': 'roombooking'}
    __api_public__ = (('start_dt', 'startDT'), ('end_dt', 'endDT'), 'is_cancelled', 'is_rejected')

    #: A relationship loading strategy that will avoid loading the
    #: users linked to a reservation.  You want to use this in pretty
    #: much all cases where you eager-load the `reservation` relationship.
    NO_RESERVATION_USER_STRATEGY = defaultload('reservation')
    NO_RESERVATION_USER_STRATEGY.lazyload('created_by_user')
    NO_RESERVATION_USER_STRATEGY.noload('booked_for_user')

    reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.reservations.id'),
        nullable=False,
        primary_key=True
    )
    start_dt = db.Column(
        db.DateTime,
        nullable=False,
        primary_key=True,
        index=True
    )
    end_dt = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )
    notification_sent = db.Column(
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

    # relationship backrefs:
    # - reservation (Reservation.occurrences)

    @hybrid_property
    def date(self):
        return self.start_dt.date()

    @date.expression
    def date(self):
        return cast(self.start_dt, Date)

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
            self.start_dt,
            self.end_dt,
            self.is_cancelled,
            self.is_rejected,
            self.notification_sent
        )

    @classmethod
    def create_series_for_reservation(cls, reservation):
        for o in cls.iter_create_occurrences(reservation.start_dt, reservation.end_dt, reservation.repetition):
            o.reservation = reservation

    @classmethod
    def create_series(cls, start, end, repetition):
        return list(cls.iter_create_occurrences(start, end, repetition))

    @classmethod
    def iter_create_occurrences(cls, start, end, repetition):
        for start in cls.iter_start_time(start, end, repetition):
            end = datetime.combine(start.date(), end.time())
            yield ReservationOccurrence(start_dt=start, end_dt=end)

    @staticmethod
    def iter_start_time(start, end, repetition):
        from indico.modules.rb.models.reservations import RepeatFrequency

        repeat_frequency, repeat_interval = repetition

        if repeat_frequency == RepeatFrequency.NEVER:
            return [start]

        if repeat_frequency == RepeatFrequency.DAY:
            if repeat_interval == 1:
                return rrule.rrule(rrule.DAILY, dtstart=start, until=end)
            else:
                raise IndicoError('Unsupported interval')

        elif repeat_frequency == RepeatFrequency.WEEK:
            if 0 < repeat_interval < 4:
                return rrule.rrule(rrule.WEEKLY, dtstart=start, until=end, interval=repeat_interval)
            else:
                raise IndicoError('Unsupported interval')

        elif repeat_frequency == RepeatFrequency.MONTH:

            if repeat_interval == 1:
                position = int(ceil(start.day / 7.0))
                if position == 5:
                    # The fifth weekday of the month will always be the last one
                    position = -1
                return rrule.rrule(rrule.MONTHLY, dtstart=start, until=end, byweekday=start.weekday(),
                                   bysetpos=position)
            else:
                raise IndicoError('Unsupported interval {}'.format(repeat_interval))

        raise IndicoError('Unexpected frequency {}'.format(repeat_frequency))

    @staticmethod
    def filter_overlap(occurrences):
        return or_(db_dates_overlap(ReservationOccurrence, 'start_dt', occ.start_dt, 'end_dt', occ.end_dt)
                   for occ in occurrences)

    @classmethod
    def find_overlapping_with(cls, room, occurrences, skip_reservation_id=None):
        from indico.modules.rb.models.reservations import Reservation

        return (ReservationOccurrence
                .find(Reservation.room == room,
                      Reservation.id != skip_reservation_id,
                      ReservationOccurrence.is_valid,
                      ReservationOccurrence.filter_overlap(occurrences),
                      _eager=ReservationOccurrence.reservation,
                      _join=ReservationOccurrence.reservation)
                .options(cls.NO_RESERVATION_USER_STRATEGY))

    @classmethod
    def find_with_filters(cls, filters, user=None):
        from indico.modules.rb.models.rooms import Room
        from indico.modules.rb.models.reservations import Reservation

        q = (ReservationOccurrence
             .find(Room.is_active,
                   _join=[ReservationOccurrence.reservation, Room], _eager=ReservationOccurrence.reservation)
             .options(cls.NO_RESERVATION_USER_STRATEGY))

        if 'start_dt' in filters and 'end_dt' in filters:
            start_dt = filters['start_dt']
            end_dt = filters['end_dt']
            criteria = []
            # We have to check the time range for EACH DAY
            for day_start_dt in iterdays(start_dt, end_dt):
                # Same date, but the end time
                day_end_dt = datetime.combine(day_start_dt.date(), end_dt.time())
                criteria.append(db_dates_overlap(ReservationOccurrence, 'start_dt', day_start_dt, 'end_dt', day_end_dt))
            q = q.filter(or_(*criteria))

        if filters.get('is_only_mine') and user:
            q = q.filter((Reservation.booked_for_id == user.id) | (Reservation.created_by_id == user.id))
        if filters.get('room_ids'):
            q = q.filter(Room.id.in_(filters['room_ids']))

        if filters.get('is_only_confirmed_bookings') and not filters.get('is_only_pending_bookings'):
            q = q.filter(Reservation.is_accepted)
        elif not filters.get('is_only_confirmed_bookings') and filters.get('is_only_pending_bookings'):
            q = q.filter(~Reservation.is_accepted)

        if filters.get('is_rejected') and filters.get('is_cancelled'):
            q = q.filter(Reservation.is_rejected | ReservationOccurrence.is_rejected
                         | Reservation.is_cancelled | ReservationOccurrence.is_cancelled)
        else:
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

        if filters.get('uses_vc'):
            q = q.filter(Reservation.uses_vc)
        if filters.get('needs_vc_assistance'):
            q = q.filter(Reservation.needs_vc_assistance)
        if filters.get('needs_assistance'):
            q = q.filter(Reservation.needs_assistance)

        if filters.get('booked_for_name'):
            qs = u'%{}%'.format(filters['booked_for_name'])
            q = q.filter(Reservation.booked_for_name.ilike(qs))
        if filters.get('reason'):
            qs = u'%{}%'.format(filters['reason'])
            q = q.filter(Reservation.booking_reason.ilike(qs))

        return q.order_by(Room.id)

    @proxy_to_reservation_if_last_valid_occurrence
    @unify_user_args
    def cancel(self, user, reason=None, silent=False):
        self.is_cancelled = True
        self.rejection_reason = reason
        if not silent:
            log = [u'Day cancelled: {}'.format(format_date(self.date).decode('utf-8'))]
            if reason:
                log.append(u'Reason: {}'.format(reason))
            self.reservation.add_edit_log(ReservationEditLog(user_name=user.full_name, info=log))
            from indico.modules.rb.notifications.reservation_occurrences import notify_cancellation
            notify_cancellation(self)

    @proxy_to_reservation_if_last_valid_occurrence
    @unify_user_args
    def reject(self, user, reason, silent=False):
        self.is_rejected = True
        self.rejection_reason = reason
        if not silent:
            log = [u'Day rejected: {}'.format(format_date(self.date).decode('utf-8')),
                   u'Reason: {}'.format(reason)]
            self.reservation.add_edit_log(ReservationEditLog(user_name=user.full_name, info=log))
            from indico.modules.rb.notifications.reservation_occurrences import notify_rejection
            notify_rejection(self)

    def get_overlap(self, occurrence, skip_self=False):
        if self.reservation and occurrence.reservation and self.reservation.room_id != occurrence.reservation.room_id:
            raise ValueError('ReservationOccurrence objects of different rooms')
        if skip_self and self.reservation and occurrence.reservation and self.reservation == occurrence.reservation:
            return None, None
        return date_time.get_overlap((self.start_dt, self.end_dt), (occurrence.start_dt, occurrence.end_dt))

    def overlaps(self, occurrence, skip_self=False):
        if self.reservation and occurrence.reservation and self.reservation.room_id != occurrence.reservation.room_id:
            raise ValueError('ReservationOccurrence objects of different rooms')
        if skip_self and self.reservation and occurrence.reservation and self.reservation == occurrence.reservation:
            return False
        return date_time.overlaps((self.start_dt, self.end_dt), (occurrence.start_dt, occurrence.end_dt))
