# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import datetime, time
from operator import attrgetter

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.notifications.blockings import notify_request_response
from indico.util.string import return_ascii
from indico.util.struct.enum import RichIntEnum


class BlockedRoomState(RichIntEnum):
    __titles__ = ['Pending', 'Accepted', 'Rejected']
    pending = 0
    accepted = 1
    rejected = 2


class BlockedRoom(db.Model):
    __tablename__ = 'blocked_rooms'
    __table_args__ = {'schema': 'roombooking'}

    State = BlockedRoomState  # make it available here for convenience

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    state = db.Column(
        PyIntEnum(BlockedRoomState),
        nullable=False,
        default=BlockedRoomState.pending
    )
    rejected_by = db.Column(
        db.String
    )
    rejection_reason = db.Column(
        db.String
    )
    blocking_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.blockings.id'),
        nullable=False
    )
    room_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.rooms.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - blocking (Blocking.blocked_rooms)
    # - room (Room.blocked_rooms)

    @property
    def state_name(self):
        return BlockedRoomState(self.state).title if self.state is not None else None

    def reject(self, user=None, reason=None):
        """Reject the room blocking."""
        self.state = BlockedRoomState.rejected
        if reason:
            self.rejection_reason = reason
        if user:
            self.rejected_by = user.full_name
        notify_request_response(self)

    def approve(self, notify_blocker=True):
        """Approve the room blocking, rejecting all colliding reservations/occurrences."""
        self.state = BlockedRoomState.accepted

        # Get colliding reservations
        start_dt = datetime.combine(self.blocking.start_date, time())
        end_dt = datetime.combine(self.blocking.end_date, time(23, 59, 59))

        reservation_criteria = [
            Reservation.room_id == self.room_id,
            ~Reservation.is_rejected,
            ~Reservation.is_cancelled
        ]

        # Whole reservations to reject
        reservations = Reservation.find_all(
            Reservation.start_dt >= start_dt,
            Reservation.end_dt <= end_dt,
            *reservation_criteria
        )

        # Single occurrences to reject
        occurrences = ReservationOccurrence.find_all(
            ReservationOccurrence.start_dt >= start_dt,
            ReservationOccurrence.end_dt <= end_dt,
            ReservationOccurrence.is_valid,
            ~ReservationOccurrence.reservation_id.in_(map(attrgetter('id'), reservations)) if reservations else True,
            *reservation_criteria,
            _join=Reservation
        )

        reason = 'Conflict with blocking {}: {}'.format(self.blocking.id, self.blocking.reason)

        for reservation in reservations:
            if self.blocking.can_override(reservation.created_by_user, room=reservation.room):
                continue
            reservation.reject(self.blocking.created_by_user, reason)

        for occurrence in occurrences:
            reservation = occurrence.reservation
            if self.blocking.can_override(reservation.created_by_user, room=reservation.room):
                continue
            occurrence.reject(self.blocking.created_by_user, reason)

        if notify_blocker:
            # We only need to notify the blocking creator if the blocked room wasn't approved yet.
            # This is the case if it's a new blocking for a room managed by the creator
            notify_request_response(self)

    @return_ascii
    def __repr__(self):
        return '<BlockedRoom({0}, {1}, {2})>'.format(
            self.blocking_id,
            self.room_id,
            self.state_name
        )
