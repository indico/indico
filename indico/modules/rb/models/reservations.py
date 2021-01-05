# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict, defaultdict
from datetime import datetime

from sqlalchemy import Date, Time
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import cast
from werkzeug.datastructures import OrderedMultiDict

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.custom import PyIntEnum
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.core.db.sqlalchemy.links import LinkMixin, LinkType
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import limit_groups
from indico.core.errors import NoReportError
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence, ReservationOccurrenceState
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.notifications.reservations import (notify_cancellation, notify_confirmation, notify_creation,
                                                          notify_modification, notify_rejection, notify_reset_approval)
from indico.modules.rb.util import get_prebooking_collisions, rb_is_admin
from indico.util.date_time import format_date, format_time, now_utc
from indico.util.i18n import _
from indico.util.serializer import Serializer
from indico.util.string import format_repr, return_ascii, to_unicode
from indico.util.struct.enum import IndicoEnum
from indico.web.flask.util import url_for


class ConflictingOccurrences(Exception):
    pass


class RepeatFrequency(int, IndicoEnum):
    NEVER = 0
    DAY = 1
    WEEK = 2
    MONTH = 3


class RepeatMapping(object):
    mapping = {
        (RepeatFrequency.NEVER, 0): ('Single reservation',            None, 'none'),  # noqa: E241
        (RepeatFrequency.DAY,   1): ('Repeat daily',                  0,    'daily'),  # noqa: E241
        (RepeatFrequency.WEEK,  1): ('Repeat once a week',            1,    'weekly'),  # noqa: E241
        (RepeatFrequency.WEEK,  2): ('Repeat once every two weeks',   2,    'everyTwoWeeks'),  # noqa: E241
        (RepeatFrequency.WEEK,  3): ('Repeat once every three weeks', 3,    'everyThreeWeeks'),  # noqa: E241
        (RepeatFrequency.MONTH, 1): ('Repeat every month',            4,    'monthly')  # noqa: E241
    }

    @classmethod
    def get_message(cls, repeat_frequency, repeat_interval):
        # XXX: move this somewhere else
        # not translated since it's only used in log messages + emails now
        if repeat_frequency == RepeatFrequency.NEVER:
            return 'single booking'
        elif repeat_frequency == RepeatFrequency.DAY:
            return 'daily booking'
        elif repeat_frequency == RepeatFrequency.WEEK:
            return 'weekly' if repeat_interval == 1 else 'every {} weeks'.format(repeat_interval)
        elif repeat_frequency == RepeatFrequency.MONTH:
            return 'monthly' if repeat_interval == 1 else 'every {} months'.format(repeat_interval)

    @classmethod
    def get_short_name(cls, repeat_frequency, repeat_interval):
        # for the API
        try:
            return cls.mapping[(repeat_frequency, repeat_interval)][2]
        except KeyError:
            # XXX: this is ugly, let's remove it from the API
            return 'periodically'


class ReservationState(int, IndicoEnum):
    pending = 1
    accepted = 2
    cancelled = 3
    rejected = 4


class ReservationLink(LinkMixin, db.Model):
    __tablename__ = 'reservation_links'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='roombooking')

    allowed_link_types = {LinkType.event, LinkType.contribution, LinkType.session_block}
    events_backref_name = 'all_room_reservation_links'
    link_backref_name = 'room_reservation_links'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    def __repr__(self):
        return format_repr(self, 'id', _rawtext=self.link_repr)

    # relationship backrefs:
    # - reservation (Reservation.link)


ReservationLink.register_link_events()


class Reservation(Serializer, db.Model):
    __tablename__ = 'reservations'

    __api_public__ = [
        'id', ('start_dt', 'startDT'), ('end_dt', 'endDT'), 'repeat_frequency', 'repeat_interval',
        ('booked_for_name', 'bookedForName'), ('external_details_url', 'bookingUrl'), ('booking_reason', 'reason'),
        ('is_accepted', 'isConfirmed'), ('is_accepted', 'isValid'), 'is_cancelled',
        'is_rejected', ('location_name', 'location'), ('contact_email', 'booked_for_user_email')
    ]

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_reservations_start_dt_date', cast(cls.start_dt, Date)),
                db.Index('ix_reservations_end_dt_date', cast(cls.end_dt, Date)),
                db.Index('ix_reservations_start_dt_time', cast(cls.start_dt, Time)),
                db.Index('ix_reservations_end_dt_time', cast(cls.end_dt, Time)),
                db.CheckConstraint("rejection_reason != ''", 'rejection_reason_not_empty'),
                {'schema': 'roombooking'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    start_dt = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )
    end_dt = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )
    repeat_frequency = db.Column(
        PyIntEnum(RepeatFrequency),
        nullable=False,
        default=RepeatFrequency.NEVER
    )  # week, month, year, etc.
    repeat_interval = db.Column(
        db.SmallInteger,
        nullable=False,
        default=0
    )  # 1, 2, 3, etc.
    booked_for_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True,
        # Must be nullable for legacy data :(
    )
    booked_for_name = db.Column(
        db.String,
        nullable=False
    )
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True,
        # Must be nullable for legacy data :(
    )
    room_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.rooms.id'),
        nullable=False,
        index=True
    )
    state = db.Column(
        PyIntEnum(ReservationState),
        nullable=False,
        default=ReservationState.accepted
    )
    booking_reason = db.Column(
        db.Text,
        nullable=False
    )
    rejection_reason = db.Column(
        db.String,
        nullable=True
    )
    link_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.reservation_links.id'),
        nullable=True,
        index=True
    )
    end_notification_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    edit_logs = db.relationship(
        'ReservationEditLog',
        backref='reservation',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    occurrences = db.relationship(
        'ReservationOccurrence',
        backref='reservation',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    #: The user this booking was made for.
    #: Assigning a user here also updates `booked_for_name`.
    booked_for_user = db.relationship(
        'User',
        lazy=False,
        foreign_keys=[booked_for_id],
        backref=db.backref(
            'reservations_booked_for',
            lazy='dynamic'
        )
    )
    #: The user who created this booking.
    created_by_user = db.relationship(
        'User',
        lazy=False,
        foreign_keys=[created_by_id],
        backref=db.backref(
            'reservations',
            lazy='dynamic'
        )
    )

    link = db.relationship(
        'ReservationLink',
        lazy=True,
        backref=db.backref(
            'reservation',
            uselist=False
        )
    )

    # relationship backrefs:
    # - room (Room.reservations)

    @hybrid_property
    def is_pending(self):
        return self.state == ReservationState.pending

    @hybrid_property
    def is_accepted(self):
        return self.state == ReservationState.accepted

    @hybrid_property
    def is_cancelled(self):
        return self.state == ReservationState.cancelled

    @hybrid_property
    def is_rejected(self):
        return self.state == ReservationState.rejected

    @hybrid_property
    def is_archived(self):
        return self.end_dt < datetime.now()

    @hybrid_property
    def is_repeating(self):
        return self.repeat_frequency != RepeatFrequency.NEVER

    @property
    def contact_email(self):
        return self.booked_for_user.email if self.booked_for_user else None

    @property
    def external_details_url(self):
        return url_for('rb.booking_link', booking_id=self.id, _external=True)

    @property
    def location_name(self):
        return self.room.location_name

    @property
    def repetition(self):
        return self.repeat_frequency, self.repeat_interval

    @property
    def linked_object(self):
        return self.link.object if self.link else None

    @linked_object.setter
    def linked_object(self, obj):
        assert self.link is None
        self.link = ReservationLink(object=obj)

    @property
    def event(self):
        return self.link.event if self.link else None

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'room_id', 'start_dt', 'end_dt', 'state', _text=self.booking_reason)

    @classmethod
    def create_from_data(cls, room, data, user, prebook=None, ignore_admin=False):
        """Create a new reservation.

        :param room: The Room that's being booked.
        :param data: A dict containing the booking data, usually from a :class:`NewBookingConfirmForm` instance
        :param user: The :class:`.User` who creates the booking.
        :param prebook: Instead of determining the booking type from the user's
                        permissions, always use the given mode.
        :param ignore_admin: Whether to ignore the user's admin status.
        """

        populate_fields = ('start_dt', 'end_dt', 'repeat_frequency', 'repeat_interval', 'room_id', 'booking_reason')
        if data['repeat_frequency'] == RepeatFrequency.NEVER and data['start_dt'].date() != data['end_dt'].date():
            raise ValueError('end_dt != start_dt for non-repeating booking')

        if prebook is None:
            prebook = not room.can_book(user, allow_admin=(not ignore_admin))
            if prebook and not room.can_prebook(user, allow_admin=(not ignore_admin)):
                raise NoReportError('You cannot book this room')

        room.check_advance_days(data['end_dt'].date(), user)
        room.check_bookable_hours(data['start_dt'].time(), data['end_dt'].time(), user)

        reservation = cls()
        for field in populate_fields:
            if field in data:
                setattr(reservation, field, data[field])
        reservation.room = room
        reservation.booked_for_user = data.get('booked_for_user') or user
        reservation.booked_for_name = reservation.booked_for_user.full_name
        reservation.state = ReservationState.pending if prebook else ReservationState.accepted
        reservation.created_by_user = user
        reservation.create_occurrences(True, allow_admin=(not ignore_admin))
        if not any(occ.is_valid for occ in reservation.occurrences):
            raise NoReportError(_('Reservation has no valid occurrences'))
        db.session.flush()
        signals.rb.booking_created.send(reservation)
        notify_creation(reservation)
        return reservation

    @staticmethod
    def get_with_data(*args, **kwargs):
        filters = kwargs.pop('filters', None)
        limit = kwargs.pop('limit', None)
        offset = kwargs.pop('offset', 0)
        order = kwargs.pop('order', Reservation.start_dt)
        limit_per_room = kwargs.pop('limit_per_room', False)
        occurs_on = kwargs.pop('occurs_on')
        if kwargs:
            raise ValueError('Unexpected kwargs: {}'.format(kwargs))

        query = Reservation.query.options(joinedload(Reservation.room))
        if filters:
            query = query.filter(*filters)
        if occurs_on:
            query = query.filter(
                Reservation.id.in_(db.session.query(ReservationOccurrence.reservation_id)
                                   .filter(ReservationOccurrence.date.in_(occurs_on),
                                           ReservationOccurrence.is_valid))
            )
        if limit_per_room and (limit or offset):
            query = limit_groups(query, Reservation, Reservation.room_id, order, limit, offset)

        query = query.order_by(order, Reservation.created_dt)

        if not limit_per_room:
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

        result = OrderedDict((r.id, {'reservation': r}) for r in query)

        if 'occurrences' in args:
            occurrence_data = OrderedMultiDict(db.session.query(ReservationOccurrence.reservation_id,
                                                                ReservationOccurrence)
                                               .filter(ReservationOccurrence.reservation_id.in_(result.iterkeys()))
                                               .order_by(ReservationOccurrence.start_dt))
            for id_, data in result.iteritems():
                data['occurrences'] = occurrence_data.getlist(id_)

        return result.values()

    @staticmethod
    def find_overlapping_with(room, occurrences, skip_reservation_id=None):
        return Reservation.find(Reservation.room == room,
                                Reservation.id != skip_reservation_id,
                                ReservationOccurrence.is_valid,
                                ReservationOccurrence.filter_overlap(occurrences),
                                _join=ReservationOccurrence)

    def accept(self, user, reason=None):
        self.state = ReservationState.accepted
        if reason:
            log_msg = 'Reservation accepted: {}'.format(reason)
        else:
            log_msg = 'Reservation accepted'
        self.add_edit_log(ReservationEditLog(user_name=user.full_name, info=[log_msg]))
        notify_confirmation(self, reason)
        signals.rb.booking_state_changed.send(self)
        pre_occurrences = get_prebooking_collisions(self)
        for occurrence in pre_occurrences:
            occurrence.reject(user, 'Rejected due to collision with a confirmed reservation')

    def reset_approval(self, user):
        self.state = ReservationState.pending
        notify_reset_approval(self)
        self.add_edit_log(ReservationEditLog(user_name=user.full_name, info=['Requiring new approval due to change']))

    def cancel(self, user, reason=None, silent=False):
        self.state = ReservationState.cancelled
        self.rejection_reason = reason or None
        criteria = (ReservationOccurrence.is_valid, ReservationOccurrence.is_within_cancel_grace_period)
        self.occurrences.filter(*criteria).update({
            ReservationOccurrence.state: ReservationOccurrenceState.cancelled,
            ReservationOccurrence.rejection_reason: reason
        }, synchronize_session='fetch')
        signals.rb.booking_state_changed.send(self)
        if not silent:
            notify_cancellation(self)
            log_msg = 'Reservation cancelled: {}'.format(reason) if reason else 'Reservation cancelled'
            self.add_edit_log(ReservationEditLog(user_name=user.full_name, info=[log_msg]))

    def reject(self, user, reason, silent=False):
        self.state = ReservationState.rejected
        self.rejection_reason = reason or None
        self.occurrences.filter_by(is_valid=True).update({
            ReservationOccurrence.state: ReservationOccurrenceState.rejected,
            ReservationOccurrence.rejection_reason: reason
        }, synchronize_session='fetch')
        signals.rb.booking_state_changed.send(self)
        if not silent:
            notify_rejection(self)
            log_msg = 'Reservation rejected: {}'.format(reason)
            self.add_edit_log(ReservationEditLog(user_name=user.full_name, info=[log_msg]))

    def add_edit_log(self, edit_log):
        self.edit_logs.append(edit_log)
        db.session.flush()

    def can_accept(self, user, allow_admin=True):
        if user is None:
            return False
        return self.is_pending and self.room.can_moderate(user, allow_admin=allow_admin)

    def can_reject(self, user, allow_admin=True):
        if user is None:
            return False
        if self.is_rejected or self.is_cancelled:
            return False
        return self.room.can_moderate(user, allow_admin=allow_admin)

    def can_cancel(self, user, allow_admin=True):
        if user is None:
            return False
        if self.is_rejected or self.is_cancelled or self.is_archived:
            return False

        is_booked_or_owned_by_user = self.is_owned_by(user) or self.is_booked_for(user)
        return is_booked_or_owned_by_user or (allow_admin and rb_is_admin(user))

    def can_edit(self, user, allow_admin=True):
        if user is None:
            return False
        if self.is_rejected or self.is_cancelled:
            return False
        if self.is_archived and not (allow_admin and rb_is_admin(user)):
            return False
        return self.is_owned_by(user) or self.is_booked_for(user) or self.room.can_manage(user, allow_admin=allow_admin)

    def can_delete(self, user, allow_admin=True):
        if user is None:
            return False
        return allow_admin and rb_is_admin(user) and (self.is_cancelled or self.is_rejected)

    def create_occurrences(self, skip_conflicts, user=None, allow_admin=True):
        ReservationOccurrence.create_series_for_reservation(self)
        db.session.flush()

        if user is None:
            user = self.created_by_user

        # Check for conflicts with nonbookable periods
        admin = allow_admin and rb_is_admin(user)
        if not admin and not self.room.can_manage(user, permission='override'):
            nonbookable_periods = self.room.nonbookable_periods.filter(NonBookablePeriod.end_dt > self.start_dt)
            for occurrence in self.occurrences:
                if not occurrence.is_valid:
                    continue
                for nbd in nonbookable_periods:
                    if nbd.overlaps(occurrence.start_dt, occurrence.end_dt):
                        if not skip_conflicts:
                            raise ConflictingOccurrences()
                        occurrence.cancel(user, 'Skipped due to nonbookable date', silent=True, propagate=False)
                        break

        # Check for conflicts with blockings
        blocked_rooms = self.room.get_blocked_rooms(*(occurrence.start_dt for occurrence in self.occurrences))
        for br in blocked_rooms:
            blocking = br.blocking
            if blocking.can_override(user, room=self.room, allow_admin=allow_admin):
                continue
            for occurrence in self.occurrences:
                if occurrence.is_valid and blocking.is_active_at(occurrence.start_dt.date()):
                    # Cancel OUR occurrence
                    msg = 'Skipped due to collision with a blocking ({})'
                    occurrence.cancel(user, msg.format(blocking.reason), silent=True, propagate=False)

        # Check for conflicts with other occurrences
        conflicting_occurrences = self.get_conflicting_occurrences()
        for occurrence, conflicts in conflicting_occurrences.iteritems():
            if not occurrence.is_valid:
                continue
            if conflicts['confirmed']:
                if not skip_conflicts:
                    raise ConflictingOccurrences()
                # Cancel OUR occurrence
                msg = 'Skipped due to collision with {} reservation(s)'
                occurrence.cancel(user, msg.format(len(conflicts['confirmed'])), silent=True, propagate=False)
            elif conflicts['pending'] and self.is_accepted:
                # Reject OTHER occurrences
                for conflict in conflicts['pending']:
                    conflict.reject(user, 'Rejected due to collision with a confirmed reservation')

    def find_excluded_days(self):
        return self.occurrences.filter(~ReservationOccurrence.is_valid)

    def find_overlapping(self):
        occurrences = self.occurrences.filter(ReservationOccurrence.is_valid).all()
        return Reservation.find_overlapping_with(self.room, occurrences, self.id)

    def get_conflicting_occurrences(self):
        valid_occurrences = self.occurrences.filter(ReservationOccurrence.is_valid).all()
        if not valid_occurrences:
            raise NoReportError(_('Reservation has no valid occurrences'))
        colliding_occurrences = ReservationOccurrence.find_overlapping_with(self.room, valid_occurrences, self.id).all()
        conflicts = defaultdict(lambda: dict(confirmed=[], pending=[]))
        for occurrence in valid_occurrences:
            for colliding in colliding_occurrences:
                if occurrence.overlaps(colliding):
                    key = 'confirmed' if colliding.reservation.is_accepted else 'pending'
                    conflicts[occurrence][key].append(colliding)
        return conflicts

    def is_booked_for(self, user):
        return user is not None and self.booked_for_user == user

    def is_owned_by(self, user):
        return self.created_by_user == user

    def modify(self, data, user):
        """Modify an existing reservation.

        :param data: A dict containing the booking data, usually from a :class:`ModifyBookingForm` instance
        :param user: The :class:`.User` who modifies the booking.
        """

        populate_fields = ('start_dt', 'end_dt', 'repeat_frequency', 'repeat_interval', 'booked_for_user',
                           'booking_reason')
        # fields affecting occurrences
        occurrence_fields = {'start_dt', 'end_dt', 'repeat_frequency', 'repeat_interval'}
        # fields where date and time are compared separately
        date_time_fields = {'start_dt', 'end_dt'}
        # fields for the repetition
        repetition_fields = {'repeat_frequency', 'repeat_interval'}
        # pretty names for logging
        field_names = {
            'start_dt/date': u"start date",
            'end_dt/date': u"end date",
            'start_dt/time': u"start time",
            'end_dt/time': u"end time",
            'repetition': u"booking type",
            'booked_for_user': u"'Booked for' user",
            'booking_reason': u"booking reason",
        }

        self.room.check_advance_days(data['end_dt'].date(), user)
        self.room.check_bookable_hours(data['start_dt'].time(), data['end_dt'].time(), user)

        changes = {}
        update_occurrences = False
        old_repetition = self.repetition

        for field in populate_fields:
            if field not in data:
                continue
            old = getattr(self, field)
            new = data[field]
            converter = unicode
            if old != new:
                # Booked for user updates the (redundant) name
                if field == 'booked_for_user':
                    old = self.booked_for_name
                    new = self.booked_for_name = data[field].full_name
                # Apply the change
                setattr(self, field, data[field])
                # If any occurrence-related field changed we need to recreate the occurrences
                if field in occurrence_fields:
                    update_occurrences = True
                # Record change for history entry
                if field in date_time_fields:
                    # The date/time fields create separate entries for the date and time parts
                    if old.date() != new.date():
                        changes[field + '/date'] = {'old': old.date(), 'new': new.date(), 'converter': format_date}
                    if old.time() != new.time():
                        changes[field + '/time'] = {'old': old.time(), 'new': new.time(), 'converter': format_time}
                elif field in repetition_fields:
                    # Repetition needs special handling since it consists of two fields but they are tied together
                    # We simply update it whenever we encounter such a change; after the last change we end up with
                    # the correct change data
                    changes['repetition'] = {'old': old_repetition,
                                             'new': self.repetition,
                                             'converter': lambda x: RepeatMapping.get_message(*x)}
                else:
                    changes[field] = {'old': old, 'new': new, 'converter': converter}

        if not changes:
            return False

        # Create a verbose log entry for the modification
        log = ['Booking modified']
        for field, change in changes.iteritems():
            field_title = field_names.get(field, field)
            converter = change['converter']
            old = to_unicode(converter(change['old']))
            new = to_unicode(converter(change['new']))
            if not old:
                log.append(u"The {} was set to '{}'".format(field_title, new))
            elif not new:
                log.append(u"The {} was cleared".format(field_title))
            else:
                log.append(u"The {} was changed from '{}' to '{}'".format(field_title, old, new))

        self.edit_logs.append(ReservationEditLog(user_name=user.full_name, info=log))

        # Recreate all occurrences if necessary
        if update_occurrences:
            cols = [col.name for col in ReservationOccurrence.__table__.columns
                    if not col.primary_key and col.name not in {'start_dt', 'end_dt'}]

            old_occurrences = {occ.date: occ for occ in self.occurrences}
            self.occurrences.delete(synchronize_session='fetch')
            self.create_occurrences(True, user)
            db.session.flush()
            # Restore rejection data etc. for recreated occurrences
            for occurrence in self.occurrences:
                old_occurrence = old_occurrences.get(occurrence.date)
                # Copy data from old occurrence UNLESS the new one is invalid (e.g. because of collisions)
                # Otherwise we'd end up with valid occurrences ignoring collisions!
                if old_occurrence and occurrence.is_valid:
                    for col in cols:
                        setattr(occurrence, col, getattr(old_occurrence, col))
            # Don't cause new notifications for the entire booking in case of daily repetition
            if self.repeat_frequency == RepeatFrequency.DAY and all(occ.notification_sent
                                                                    for occ in old_occurrences.itervalues()):
                for occurrence in self.occurrences:
                    occurrence.notification_sent = True

        # Sanity check so we don't end up with an "empty" booking
        if not any(occ.is_valid for occ in self.occurrences):
            raise NoReportError(_('Reservation has no valid occurrences'))

        notify_modification(self, changes)
        return True


@listens_for(Reservation.booked_for_user, 'set')
def _booked_for_user_set(target, user, *unused):
    target.booked_for_name = user.full_name if user else ''
