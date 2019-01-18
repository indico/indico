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

from datetime import timedelta

from indico.modules.rb.models.blocked_rooms import BlockedRoomState
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb_new.operations.blockings import get_blocked_rooms, get_rooms_blockings
from indico.modules.rb_new.operations.bookings import get_existing_rooms_occurrences
from indico.modules.rb_new.operations.conflicts import get_rooms_conflicts
from indico.modules.rb_new.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
from indico.modules.rb_new.operations.rooms import search_for_rooms
from indico.modules.rb_new.util import group_by_occurrence_date
from indico.util.date_time import overlaps


BOOKING_TIME_DIFF = 20  # (minutes)
DURATION_FACTOR = 0.25


def get_suggestions(filters, limit=None):
    blocked_rooms = get_blocked_rooms(filters['start_dt'], filters['end_dt'], [BlockedRoomState.accepted])
    rooms = [room for room in search_for_rooms(filters, False) if room not in blocked_rooms]
    if filters['repeat_frequency'] == RepeatFrequency.NEVER:
        suggestions = sort_suggestions(get_single_booking_suggestions(rooms, filters['start_dt'], filters['end_dt'],
                                                                      limit=limit))
    else:
        suggestions = get_number_of_skipped_days_for_rooms(rooms, filters['start_dt'], filters['end_dt'],
                                                           filters['repeat_frequency'], filters['repeat_interval'],
                                                           limit=limit)
    for entry in suggestions:
        entry['room_id'] = entry.pop('room').id
    return suggestions


def get_single_booking_suggestions(rooms, start_dt, end_dt, limit=None):
    data = []
    new_start_dt = start_dt - timedelta(minutes=BOOKING_TIME_DIFF)
    new_end_dt = end_dt + timedelta(minutes=BOOKING_TIME_DIFF)
    rooms_occurrences = get_existing_rooms_occurrences(rooms, new_start_dt, new_end_dt, RepeatFrequency.NEVER, None,
                                                       allow_overlapping=True)

    for room in rooms:
        if limit and len(data) == limit:
            break

        suggestions = {}
        suggested_time = get_start_time_suggestion(rooms_occurrences.get(room.id, []), start_dt, end_dt)
        if suggested_time:
            suggested_time_change = (suggested_time - start_dt).total_seconds() / 60
            if suggested_time_change:
                suggestions['time'] = suggested_time_change

        duration_suggestion = get_duration_suggestion(rooms_occurrences.get(room.id, []), start_dt, end_dt)
        original_duration = (end_dt - start_dt).total_seconds() / 60
        if duration_suggestion and duration_suggestion <= DURATION_FACTOR * original_duration:
            suggestions['duration'] = duration_suggestion
        if suggestions:
            data.append({'room': room, 'suggestions': suggestions})
    return data


def get_number_of_skipped_days_for_rooms(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, limit=None):
    data = []
    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    blocked_rooms = get_rooms_blockings(rooms, start_dt.date(), end_dt.date())
    unbookable_hours = get_rooms_unbookable_hours(rooms)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    conflicts, _ = get_rooms_conflicts(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, blocked_rooms,
                                       nonbookable_periods, unbookable_hours)
    for room in rooms:
        if limit and len(data) == limit:
            break

        number_of_conflicting_days = len(group_by_occurrence_date(conflicts.get(room.id, [])))
        if number_of_conflicting_days and number_of_conflicting_days < len(candidates):
            data.append({'room': room, 'suggestions': {'skip': number_of_conflicting_days}})
    return sorted(data, key=lambda item: item['suggestions']['skip'])


def get_start_time_suggestion(occurrences, from_, to):
    duration = (to - from_).total_seconds() / 60
    new_start_dt = from_ - timedelta(minutes=BOOKING_TIME_DIFF)
    new_end_dt = to + timedelta(minutes=BOOKING_TIME_DIFF)

    if not occurrences:
        return new_start_dt

    candidates = []
    period_start = new_start_dt
    for occurrence in occurrences:
        occ_start, occ_end = occurrence.start_dt, occurrence.end_dt
        if period_start < occ_start:
            candidates.append((period_start, occ_start))
        period_start = occ_end

    if period_start < new_end_dt:
        candidates.append((period_start, new_end_dt))

    for candidate in candidates:
        start, end = candidate
        candidate_duration = (end - start).total_seconds() / 60
        if duration <= candidate_duration:
            return start


def get_duration_suggestion(occurrences, from_, to):
    old_duration = (to - from_).total_seconds() / 60
    duration = old_duration
    all_occurrences_overlap = all(overlaps((from_, to), (occ.start_dt, occ.end_dt)) for occ in occurrences)

    # Don't calculate duration suggestion, if there are at least
    # two existing bookings conflicting with the specified dates
    if all_occurrences_overlap and len(occurrences) > 1:
        return

    for occurrence in occurrences:
        start, end = occurrence.start_dt, occurrence.end_dt
        if start < from_:
            continue
        if from_ < end < to:
            if start > from_:
                continue
            duration -= (end - from_).total_seconds() / 60
        if from_ < start < to:
            if end < to:
                continue
            duration -= (to - start).total_seconds() / 60
    return abs(duration - old_duration) if old_duration != duration else None


def sort_suggestions(suggestions):
    def cmp_fn(a, b):
        a_time, a_duration = abs(a.get('time', 0)), a.get('duration', 0)
        b_time, b_duration = abs(b.get('time', 0)), b.get('duration', 0)
        return int(a_time + a_duration * 0.2) - int(b_time + b_duration * 0.2)
    return sorted(suggestions, cmp=cmp_fn, key=lambda item: item['suggestions'])
