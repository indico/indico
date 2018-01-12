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

from datetime import datetime, time
from operator import attrgetter

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.rb.models.blockings import Blocking
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
        return BlockedRoomState(self.state).title

    @classmethod
    def find_with_filters(cls, filters):
        q = cls.find(_eager=BlockedRoom.blocking, _join=BlockedRoom.blocking)
        if filters.get('room_ids'):
            q = q.filter(BlockedRoom.room_id.in_(filters['room_ids']))
        if filters.get('start_date') and filters.get('end_date'):
            q = q.filter(Blocking.start_date <= filters['end_date'],
                         Blocking.end_date >= filters['start_date'])
        if 'state' in filters:
            q = q.filter(BlockedRoom.state == filters['state'])
        return q

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
            if self.blocking.can_be_overridden(reservation.created_by_user, reservation.room):
                continue
            reservation.reject(self.blocking.created_by_user, reason)

        for occurrence in occurrences:
            reservation = occurrence.reservation
            if self.blocking.can_be_overridden(reservation.created_by_user, reservation.room):
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
