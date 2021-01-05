# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import datetime, timedelta

from indico.modules.rb import rb_settings
from indico.modules.rb.models.blocked_rooms import BlockedRoomState
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.operations.blockings import get_blocked_rooms, get_rooms_blockings, group_blocked_rooms
from indico.modules.rb.operations.bookings import get_existing_rooms_occurrences
from indico.modules.rb.operations.conflicts import get_rooms_conflicts
from indico.modules.rb.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
from indico.modules.rb.operations.rooms import search_for_rooms
from indico.modules.rb.util import group_by_occurrence_date
from indico.util.date_time import overlaps


BOOKING_TIME_DIFF = 20  # (minutes)
DURATION_FACTOR = 0.25


def get_suggestions(filters, limit=None):
    blocked_rooms = get_blocked_rooms(filters['start_dt'], filters['end_dt'], [BlockedRoomState.accepted])
    rooms = [room for room in search_for_rooms(filters, availability=False) if room not in blocked_rooms]
    if filters['repeat_frequency'] == RepeatFrequency.NEVER:
        suggestions = sort_suggestions(get_single_booking_suggestions(rooms, filters['start_dt'], filters['end_dt'],
                                                                      limit=limit))
    else:
        suggestions = sort_suggestions(get_recurring_booking_suggestions(rooms, filters['start_dt'], filters['end_dt'],
                                                                         filters['repeat_frequency'],
                                                                         filters['repeat_interval'], limit=limit))
    for entry in suggestions:
        entry['room_id'] = entry.pop('room').id
    return suggestions


def get_single_booking_suggestions(rooms, start_dt, end_dt, limit=None):
    data = []
    new_start_dt = start_dt - timedelta(minutes=BOOKING_TIME_DIFF)
    new_end_dt = end_dt + timedelta(minutes=BOOKING_TIME_DIFF)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    rooms = [room for room in rooms if room.id not in nonbookable_periods]

    if not rooms:
        return data

    unbookable_hours = get_rooms_unbookable_hours(rooms)
    rooms_occurrences = get_existing_rooms_occurrences(rooms, new_start_dt, new_end_dt, RepeatFrequency.NEVER, None,
                                                       allow_overlapping=True)
    for room in rooms:
        if limit and len(data) == limit:
            break

        suggestions = {}
        taken_periods = [(occ.start_dt, occ.end_dt) for occ in rooms_occurrences.get(room.id, [])]
        if room.id in unbookable_hours:
            taken_periods.extend((datetime.combine(start_dt, uh.start_time), datetime.combine(end_dt, uh.end_time))
                                 for uh in unbookable_hours[room.id])

        taken_periods = sorted(taken_periods)
        suggested_time = get_start_time_suggestion(taken_periods, start_dt, end_dt)
        if suggested_time:
            suggested_time_change = (suggested_time - start_dt).total_seconds() / 60
            if suggested_time_change and abs(suggested_time_change) <= BOOKING_TIME_DIFF:
                suggestions['time'] = suggested_time_change

        duration_suggestion = get_duration_suggestion(taken_periods, start_dt, end_dt)
        original_duration = (end_dt - start_dt).total_seconds() / 60
        if duration_suggestion and duration_suggestion <= DURATION_FACTOR * original_duration:
            suggestions['duration'] = duration_suggestion
        if suggestions:
            data.append({'room': room, 'suggestions': suggestions})
    return data


def get_recurring_booking_suggestions(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, limit=None):
    data = []
    booking_days = end_dt - start_dt
    booking_length = booking_days.days + 1
    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    blocked_rooms = group_blocked_rooms(get_rooms_blockings(rooms, start_dt.date(), end_dt.date()))
    unbookable_hours = get_rooms_unbookable_hours(rooms)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    conflicts = get_rooms_conflicts(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, blocked_rooms,
                                    nonbookable_periods, unbookable_hours)[0]
    for room in rooms:
        if limit and len(data) == limit:
            break

        suggestions = {}
        booking_limit = room.booking_limit_days or rb_settings.get('booking_limit')
        limit_exceeded = booking_limit is not None and booking_limit < booking_length
        if limit_exceeded:
            excess_days = booking_length - booking_limit
            suggestions['shorten'] = excess_days

        if not limit_exceeded:
            number_of_conflicting_days = len(group_by_occurrence_date(conflicts.get(room.id, [])))
            if number_of_conflicting_days and number_of_conflicting_days < len(candidates):
                suggestions['skip'] = number_of_conflicting_days
        if suggestions:
            data.append({'room': room, 'suggestions': suggestions})
    return data


def get_start_time_suggestion(occurrences, from_, to):
    duration = (to - from_).total_seconds() / 60
    new_start_dt = from_ - timedelta(minutes=BOOKING_TIME_DIFF)
    new_end_dt = to + timedelta(minutes=BOOKING_TIME_DIFF)

    if not occurrences:
        return new_start_dt

    candidates = []
    period_start = new_start_dt
    for (occ_start, occ_end) in occurrences:
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
    all_occurrences_overlap = all(overlaps((from_, to), occ) for occ in occurrences)

    # Don't calculate duration suggestion, if there are at least
    # two existing bookings conflicting with the specified dates
    if all_occurrences_overlap and len(occurrences) > 1:
        return

    for (start, end) in occurrences:
        if start <= from_:
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
