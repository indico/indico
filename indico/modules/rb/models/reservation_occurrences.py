# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta
from math import ceil

from dateutil import rrule
from sqlalchemy import Date, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import defaultload
from sqlalchemy.sql import cast

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.errors import IndicoError
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.util import proxy_to_reservation_if_last_valid_occurrence
from indico.modules.rb.util import rb_is_admin
from indico.util import date_time
from indico.util.date_time import format_date
from indico.util.serializer import Serializer
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import IndicoEnum
from indico.web.flask.util import url_for


class ReservationOccurrenceState(int, IndicoEnum):
    # XXX: 1 is omitted on purpose to keep the values in sync with ReservationState
    valid = 2
    cancelled = 3
    rejected = 4


class ReservationOccurrence(db.Model, Serializer):
    __tablename__ = 'reservation_occurrences'
    __table_args__ = (db.CheckConstraint("rejection_reason != ''", 'rejection_reason_not_empty'),
                      {'schema': 'roombooking'})
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
    state = db.Column(
        PyIntEnum(ReservationOccurrenceState),
        nullable=False,
        default=ReservationOccurrenceState.valid
    )
    rejection_reason = db.Column(
        db.String,
        nullable=True
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
        return self.state == ReservationOccurrenceState.valid

    @hybrid_property
    def is_cancelled(self):
        return self.state == ReservationOccurrenceState.cancelled

    @hybrid_property
    def is_rejected(self):
        return self.state == ReservationOccurrenceState.rejected

    @hybrid_property
    def is_within_cancel_grace_period(self):
        return self.start_dt >= datetime.now() - timedelta(minutes=10)

    @property
    def external_cancellation_url(self):
        return url_for(
            'rb.booking_cancellation_link',
            booking_id=self.reservation_id,
            date=self.start_dt.date(),
            _external=True,
        )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'reservation_id', 'start_dt', 'end_dt', 'state')

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

        elif repeat_frequency == RepeatFrequency.DAY:
            if repeat_interval != 1:
                raise IndicoError(u'Unsupported interval')
            return rrule.rrule(rrule.DAILY, dtstart=start, until=end)

        elif repeat_frequency == RepeatFrequency.WEEK:
            if repeat_interval <= 0:
                raise IndicoError(u'Unsupported interval')
            return rrule.rrule(rrule.WEEKLY, dtstart=start, until=end, interval=repeat_interval)

        elif repeat_frequency == RepeatFrequency.MONTH:
            if repeat_interval == 0:
                raise IndicoError(u'Unsupported interval')
            position = int(ceil(start.day / 7.0))
            if position == 5:
                # The fifth weekday of the month will always be the last one
                position = -1
            return rrule.rrule(rrule.MONTHLY, dtstart=start, until=end, byweekday=start.weekday(),
                               bysetpos=position, interval=repeat_interval)

        raise IndicoError(u'Unexpected frequency {}'.format(repeat_frequency))

    @staticmethod
    def filter_overlap(occurrences):
        if not occurrences:
            raise RuntimeError('Cannot check for overlap with empty occurrence list')
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

    def can_reject(self, user, allow_admin=True):
        if not self.is_valid:
            return False
        return self.reservation.can_reject(user, allow_admin=allow_admin)

    def can_cancel(self, user, allow_admin=True):
        if user is None:
            return False
        if not self.is_valid or self.end_dt < datetime.now():
            return False
        booking = self.reservation
        booked_or_owned_by_user = booking.is_owned_by(user) or booking.is_booked_for(user)
        if booking.is_rejected or booking.is_cancelled or booking.is_archived:
            return False
        if booked_or_owned_by_user and self.is_within_cancel_grace_period:
            return True
        return allow_admin and rb_is_admin(user)

    @proxy_to_reservation_if_last_valid_occurrence
    def cancel(self, user, reason=None, silent=False):
        self.state = ReservationOccurrenceState.cancelled
        self.rejection_reason = reason or None
        signals.rb.booking_occurrence_state_changed.send(self)
        if not silent:
            log = [u'Day cancelled: {}'.format(format_date(self.date).decode('utf-8'))]
            if reason:
                log.append(u'Reason: {}'.format(reason))
            self.reservation.add_edit_log(ReservationEditLog(user_name=user.full_name, info=log))
            from indico.modules.rb.notifications.reservation_occurrences import notify_cancellation
            notify_cancellation(self)

    @proxy_to_reservation_if_last_valid_occurrence
    def reject(self, user, reason, silent=False):
        self.state = ReservationOccurrenceState.rejected
        self.rejection_reason = reason or None
        signals.rb.booking_occurrence_state_changed.send(self)
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
