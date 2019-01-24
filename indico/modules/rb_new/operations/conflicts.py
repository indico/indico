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

from collections import defaultdict

from flask import session
from sqlalchemy.orm import contains_eager

from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.util import TempReservationOccurrence
from indico.util.date_time import get_overlap
from indico.util.struct.iterables import group_list


def get_rooms_conflicts(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, blocked_rooms,
                        nonbookable_periods, unbookable_hours):
    rooms_conflicts = defaultdict(list)
    rooms_pre_conflicts = defaultdict(list)

    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    room_ids = [room.id for room in rooms]
    query = (ReservationOccurrence.query
             .filter(Reservation.room_id.in_(room_ids),
                     ReservationOccurrence.is_valid,
                     ReservationOccurrence.filter_overlap(candidates))
             .join(ReservationOccurrence.reservation)
             .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY,
                      contains_eager(ReservationOccurrence.reservation)))

    overlapping_occurrences = group_list(query, key=lambda obj: obj.reservation.room.id)
    for room_id, occurrences in overlapping_occurrences.iteritems():
        rooms_conflicts[room_id], rooms_pre_conflicts[room_id] = get_room_bookings_conflicts(candidates, occurrences)

    for room_id, occurrences in blocked_rooms.iteritems():
        rooms_conflicts[room_id] += get_room_blockings_conflicts(room_id, candidates, occurrences)

    # TODO: do proper per-room override checks
    if not rb_is_admin(session.user):
        for room_id, occurrences in nonbookable_periods.iteritems():
            rooms_conflicts[room_id] += get_room_nonbookable_periods_conflicts(candidates, occurrences)

        for room_id, occurrences in unbookable_hours.iteritems():
            rooms_conflicts[room_id] += get_room_unbookable_hours_conflicts(candidates, occurrences)
    return rooms_conflicts, rooms_pre_conflicts


def get_room_bookings_conflicts(candidates, occurrences):
    conflicts = []
    pre_conflicts = []
    for candidate in candidates:
        for occurrence in occurrences:
            if candidate.overlaps(occurrence):
                overlap = candidate.get_overlap(occurrence)
                obj = TempReservationOccurrence(*overlap, reservation=occurrence.reservation)
                if occurrence.reservation.is_accepted:
                    conflicts.append(obj)
                else:
                    pre_conflicts.append(obj)
    return conflicts, pre_conflicts


def get_room_blockings_conflicts(room_id, candidates, occurrences):
    conflicts = []
    for candidate in candidates:
        for occurrence in occurrences:
            blocking = occurrence.blocking
            if blocking.start_date <= candidate.start_dt.date() <= blocking.end_date:
                if blocking.can_be_overridden(session.user, room=Room.get(room_id)):
                    continue
                obj = TempReservationOccurrence(candidate.start_dt, candidate.end_dt, None)
                conflicts.append(obj)
    return conflicts


def get_room_nonbookable_periods_conflicts(candidates, occurrences):
    conflicts = []
    for candidate in candidates:
        for occurrence in occurrences:
            overlap = get_overlap((candidate.start_dt, candidate.end_dt), (occurrence.start_dt, occurrence.end_dt))
            if overlap.count(None) != len(overlap):
                obj = TempReservationOccurrence(overlap[0], overlap[1], None)
                conflicts.append(obj)
    return conflicts


def get_room_unbookable_hours_conflicts(candidates, occurrences):
    conflicts = []
    for candidate in candidates:
        for occurrence in occurrences:
            hours_start_dt = candidate.start_dt.replace(hour=occurrence.start_time.hour,
                                                        minute=occurrence.start_time.minute)
            hours_end_dt = candidate.end_dt.replace(hour=occurrence.end_time.hour,
                                                    minute=occurrence.end_time.minute)
            overlap = get_overlap((candidate.start_dt, candidate.end_dt), (hours_start_dt, hours_end_dt))
            if overlap.count(None) != len(overlap):
                obj = TempReservationOccurrence(overlap[0], overlap[1], None)
                conflicts.append(obj)
    return conflicts
