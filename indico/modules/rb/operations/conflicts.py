# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime
from itertools import combinations

from flask import session
from sqlalchemy.orm import contains_eager

from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import TempReservationConcurrentOccurrence, TempReservationOccurrence, rb_is_admin
from indico.util.date_time import get_overlap
from indico.util.struct.iterables import group_list


def get_rooms_conflicts(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, blocked_rooms,
                        nonbookable_periods, unbookable_hours, skip_conflicts_with=None, allow_admin=False,
                        skip_past_conflicts=False):
    rooms_conflicts = defaultdict(set)
    rooms_pre_conflicts = defaultdict(set)
    rooms_conflicting_candidates = defaultdict(set)
    skip_conflicts_with = skip_conflicts_with or []

    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    room_ids = [room.id for room in rooms]
    query = (ReservationOccurrence.query
             .filter(Reservation.room_id.in_(room_ids),
                     ReservationOccurrence.is_valid,
                     ReservationOccurrence.filter_overlap(candidates))
             .join(ReservationOccurrence.reservation)
             .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY,
                      contains_eager(ReservationOccurrence.reservation)))

    if skip_conflicts_with:
        query = query.filter(~Reservation.id.in_(skip_conflicts_with))
    if skip_past_conflicts:
        query = query.filter(ReservationOccurrence.start_dt > datetime.now())

    overlapping_occurrences = group_list(query, key=lambda obj: obj.reservation.room.id)
    for room_id, occurrences in overlapping_occurrences.iteritems():
        conflicts = get_room_bookings_conflicts(candidates, occurrences, skip_conflicts_with)
        rooms_conflicts[room_id], rooms_pre_conflicts[room_id], rooms_conflicting_candidates[room_id] = conflicts
    for room_id, occurrences in blocked_rooms.items():
        conflicts, conflicting_candidates = get_room_blockings_conflicts(room_id, candidates, occurrences,
                                                                         allow_admin=allow_admin)
        rooms_conflicts[room_id] |= conflicts
        rooms_conflicting_candidates[room_id] |= conflicting_candidates

    if not (allow_admin and rb_is_admin(session.user)):
        for room_id, occurrences in nonbookable_periods.iteritems():
            room = Room.get_or_404(room_id)
            if not room.can_override(session.user, allow_admin=allow_admin):
                conflicts, conflicting_candidates = get_room_nonbookable_periods_conflicts(candidates, occurrences)
                rooms_conflicts[room_id] |= conflicts
                rooms_conflicting_candidates[room_id] |= conflicting_candidates

        for room_id, occurrences in unbookable_hours.iteritems():
            room = Room.get_or_404(room_id)
            if not room.can_override(session.user, allow_admin=allow_admin):
                conflicts, conflicting_candidates = get_room_unbookable_hours_conflicts(candidates, occurrences)
                rooms_conflicts[room_id] |= conflicts
                rooms_conflicting_candidates[room_id] |= conflicting_candidates
    rooms_conflicting_candidates = defaultdict(list, ((k, list(v)) for k, v in rooms_conflicting_candidates.items()))
    return rooms_conflicts, rooms_pre_conflicts, rooms_conflicting_candidates


def get_room_bookings_conflicts(candidates, occurrences, skip_conflicts_with=frozenset()):
    conflicts = set()
    pre_conflicts = set()
    conflicting_candidates = set()
    for candidate in candidates:
        for occurrence in occurrences:
            if occurrence.reservation.id in skip_conflicts_with:
                continue
            if candidate.overlaps(occurrence):
                overlap = candidate.get_overlap(occurrence)
                obj = TempReservationOccurrence(*overlap, reservation=occurrence.reservation)
                if occurrence.reservation.is_accepted:
                    conflicting_candidates.add(candidate)
                    conflicts.add(obj)
                else:
                    pre_conflicts.add(obj)
    return conflicts, pre_conflicts, conflicting_candidates


def get_room_blockings_conflicts(room_id, candidates, occurrences, allow_admin):
    conflicts = set()
    conflicting_candidates = set()
    for candidate in candidates:
        for occurrence in occurrences:
            blocking = occurrence.blocking
            if blocking.start_date <= candidate.start_dt.date() <= blocking.end_date:
                if blocking.can_override(session.user, room=Room.get(room_id), allow_admin=allow_admin):
                    continue
                conflicting_candidates.add(candidate)
                obj = TempReservationOccurrence(candidate.start_dt, candidate.end_dt, None)
                conflicts.add(obj)
    return conflicts, conflicting_candidates


def get_room_nonbookable_periods_conflicts(candidates, occurrences):
    conflicts = set()
    conflicting_candidates = set()
    for candidate in candidates:
        for occurrence in occurrences:
            overlap = get_overlap((candidate.start_dt, candidate.end_dt), (occurrence.start_dt, occurrence.end_dt))
            if overlap.count(None) != len(overlap):
                conflicting_candidates.add(candidate)
                obj = TempReservationOccurrence(overlap[0], overlap[1], None)
                conflicts.add(obj)
    return conflicts, conflicting_candidates


def get_room_unbookable_hours_conflicts(candidates, occurrences):
    conflicts = set()
    conflicting_candidates = set()
    for candidate in candidates:
        for occurrence in occurrences:
            hours_start_dt = candidate.start_dt.replace(hour=occurrence.start_time.hour,
                                                        minute=occurrence.start_time.minute)
            hours_end_dt = candidate.end_dt.replace(hour=occurrence.end_time.hour,
                                                    minute=occurrence.end_time.minute)
            overlap = get_overlap((candidate.start_dt, candidate.end_dt), (hours_start_dt, hours_end_dt))
            if overlap.count(None) != len(overlap):
                conflicting_candidates.add(candidate)
                obj = TempReservationOccurrence(overlap[0], overlap[1], None)
                conflicts.add(obj)
    return conflicts, conflicting_candidates


def get_concurrent_pre_bookings(pre_bookings, skip_conflicts_with=frozenset()):
    concurrent_pre_bookings = []
    for (x, y) in combinations(pre_bookings, 2):
        if any(pre_booking.reservation.id in skip_conflicts_with for pre_booking in [x, y]):
            continue
        if x.overlaps(y):
            overlap = x.get_overlap(y)
            obj = TempReservationConcurrentOccurrence(*overlap, reservations=[x.reservation, y.reservation])
            concurrent_pre_bookings.append(obj)
    return concurrent_pre_bookings
