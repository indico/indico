# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta
from math import ceil

from dateutil import rrule
from sqlalchemy import Date, or_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import contains_eager, defaultload
from sqlalchemy.sql import cast

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.links import LinkMixin, LinkType
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.errors import IndicoError
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.util import proxy_to_reservation_if_last_valid_occurrence
from indico.modules.rb.util import rb_is_admin
from indico.util import date_time
from indico.util.date_time import format_date
from indico.util.enum import IndicoIntEnum
from indico.util.string import format_repr
from indico.web.flask.util import url_for


class ReservationOccurrenceState(IndicoIntEnum):
    # XXX: 1 is omitted on purpose to keep the values in sync with ReservationState
    valid = 2
    cancelled = 3
    rejected = 4


class ReservationOccurrenceLink(LinkMixin, db.Model):
    __tablename__ = 'reservation_occurrence_links'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='roombooking')

    allowed_link_types = {LinkType.event, LinkType.contribution, LinkType.session_block}
    events_backref_name = 'all_room_reservation_occurrence_links'
    link_backref_name = 'room_reservation_occurrence_links'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    def __repr__(self):
        return format_repr(self, 'id', _rawtext=self.link_repr)

    # relationship backrefs:
    # - reservation_occurrence (ReservationOccurrence.link)


ReservationOccurrenceLink.register_link_events()


class ReservationOccurrence(db.Model):
    __tablename__ = 'reservation_occurrences'
    __table_args__ = (db.CheckConstraint("rejection_reason != ''", 'rejection_reason_not_empty'),
                      {'schema': 'roombooking'})

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
    link_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.reservation_occurrence_links.id'),
        nullable=True,
        index=True
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

    link = db.relationship(
        'ReservationOccurrenceLink',
        lazy=True,
        backref=db.backref(
            'reservation_occurrence',
            uselist=False
        )
    )

    # relationship backrefs:
    # - reservation (Reservation.occurrences)

    @hybrid_property
    def date(self):
        return self.start_dt.date()

    @date.expression
    def date(cls):
        return cast(cls.start_dt, Date)

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
        for occ_start in cls.iter_start_time(start, end, repetition):
            end = datetime.combine(occ_start.date(), end.time())
            yield ReservationOccurrence(start_dt=occ_start, end_dt=end)

    @staticmethod
    def map_recurrence_weekdays_to_rrule(weekdays):
        """Map weekdays from database to rrule weekdays."""
        # Return none if no weekdays are provided
        if not weekdays:
            return None

        weekdays_map = {
            'mon': rrule.MO,
            'tue': rrule.TU,
            'wed': rrule.WE,
            'thu': rrule.TH,
            'fri': rrule.FR,
            'sat': rrule.SA,
            'sun': rrule.SU
        }

        return [weekdays_map[day] for day in weekdays]

    @staticmethod
    def iter_start_time(start, end, repetition):
        from indico.modules.rb.models.reservations import RepeatFrequency

        repeat_frequency, repeat_interval, recurrence_weekdays = repetition
        if repeat_frequency == RepeatFrequency.NEVER:
            return [start]

        elif repeat_frequency == RepeatFrequency.DAY:
            if repeat_interval != 1:
                raise IndicoError('Unsupported interval')
            return rrule.rrule(rrule.DAILY, dtstart=start, until=end)

        elif repeat_frequency == RepeatFrequency.WEEK:
            if repeat_interval <= 0:
                raise IndicoError('Unsupported interval')
            return rrule.rrule(rrule.WEEKLY, dtstart=start, until=end,
                               interval=repeat_interval,
                               byweekday=ReservationOccurrence.map_recurrence_weekdays_to_rrule(recurrence_weekdays))

        elif repeat_frequency == RepeatFrequency.MONTH:
            if repeat_interval == 0:
                raise IndicoError('Unsupported interval')
            position = int(ceil(start.day / 7.0))
            if position == 5:
                # The fifth weekday of the month will always be the last one
                position = -1
            return rrule.rrule(rrule.MONTHLY, dtstart=start, until=end, byweekday=start.weekday(),
                               bysetpos=position, interval=repeat_interval)

        raise IndicoError(f'Unexpected frequency {repeat_frequency}')

    @staticmethod
    def filter_overlap(occurrences):
        if not occurrences:
            raise RuntimeError('Cannot check for overlap with empty occurrence list')
        return or_(db_dates_overlap(ReservationOccurrence, 'start_dt', occ.start_dt, 'end_dt', occ.end_dt)
                   for occ in occurrences)

    @classmethod
    def find_overlapping_with(cls, room, occurrences, skip_reservation_id=None):
        from indico.modules.rb.models.reservations import Reservation

        return (ReservationOccurrence.query
                .filter(Reservation.room == room,
                        Reservation.id != skip_reservation_id,
                        ReservationOccurrence.is_valid,
                        ReservationOccurrence.filter_overlap(occurrences))
                .join(ReservationOccurrence.reservation)
                .options(contains_eager(ReservationOccurrence.reservation))
                .options(cls.NO_RESERVATION_USER_STRATEGY))

    @property
    def linked_object(self):
        return self.link.object if self.link else None

    @linked_object.setter
    def linked_object(self, obj):
        assert self.link is None
        self.link = ReservationOccurrenceLink(object=obj)

    def can_reject(self, user, allow_admin=True):
        if not self.is_valid:
            return False
        return self.reservation.can_reject(user, allow_admin=allow_admin)

    def can_link(self, user, allow_admin=True):
        if not self.is_valid:
            return False
        return (
            self.reservation.is_booked_for(user) or
            self.reservation.is_owned_by(user) or
            (allow_admin and rb_is_admin(user))
        )

    def can_cancel(self, user, allow_admin=True):
        if user is None:
            return False
        if not self.is_valid or self.end_dt < datetime.now():
            return False
        booking = self.reservation
        booked_or_owned_by_user = booking.is_owned_by(user) or booking.is_booked_for(user)
        if booking.is_rejected or booking.is_cancelled or booking.is_archived:
            return False
        if booked_or_owned_by_user and (booking.is_pending or self.is_within_cancel_grace_period):
            return True
        return allow_admin and rb_is_admin(user)

    @proxy_to_reservation_if_last_valid_occurrence
    def cancel(self, user, reason=None, silent=False):
        self.state = ReservationOccurrenceState.cancelled
        self.rejection_reason = reason or None
        signals.rb.booking_occurrence_state_changed.send(self)
        if not silent:
            log = [f'Day cancelled: {format_date(self.date)}']
            if reason:
                log.append(f'Reason: {reason}')
            self.reservation.add_edit_log(ReservationEditLog(user_name=user.full_name, info=log))
            from indico.modules.rb.notifications.reservation_occurrences import notify_cancellation
            notify_cancellation(self)

    @proxy_to_reservation_if_last_valid_occurrence
    def reject(self, user, reason, silent=False):
        self.state = ReservationOccurrenceState.rejected
        self.rejection_reason = reason or None
        signals.rb.booking_occurrence_state_changed.send(self)
        if not silent:
            log = [f'Day rejected: {format_date(self.date)}',
                   f'Reason: {reason}']
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
