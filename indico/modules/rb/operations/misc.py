# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import time
from operator import attrgetter

from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.util import WEEKDAYS
from indico.util.iterables import group_list


def get_rooms_unbookable_hours(rooms):
    room_ids = [room.id for room in rooms]
    query = BookableHours.query.filter(BookableHours.room_id.in_(room_ids))
    rooms_hours = group_list(query, key=attrgetter('room_id'), sort_by=attrgetter('room_id'))
    return {room_id: _get_hours_by_weekday(hours) for room_id, hours in rooms_hours.items()}


def _get_hours_by_weekday(all_hours):
    if not all_hours:
        return []
    by_weekday = dict(group_list(all_hours, key=lambda x: x.weekday or '',
                                 sort_by=lambda x: (x.weekday or '', x.start_time)))
    inverted_hours = {}
    for weekday in WEEKDAYS:
        weekday_hours = by_weekday.get(weekday, [])
        if not (hours := sorted(by_weekday.get('', []) + weekday_hours, key=attrgetter('start_time'))):
            continue
        inverted_hours[weekday] = _invert_hours(hours)
    # any weekday with no entries is fully unbookable
    inverted_hours |= {weekday: [BookableHours(start_time=time(), end_time=time(23, 59), weekday=weekday)]
                       for weekday in set(WEEKDAYS) - set(inverted_hours)}
    return inverted_hours


def _invert_hours(hours):
    # XXX this does not support overlaps and creates nonsense in that case, but we now have validation when
    # saving a room's availability, so unless there's already bad data we don't have any problems in here
    inverted = [
        BookableHours(start_time=time(), end_time=hours[0].start_time),
        *(BookableHours(start_time=hours[i - 1].end_time, end_time=hours[i].start_time) for i in range(1, len(hours))),
        BookableHours(start_time=hours[-1].end_time, end_time=time(23, 59))
    ]
    # filter out "invalid" entries caused by two consecutive periods
    return [x for x in inverted if x.start_time != x.end_time]


def get_rooms_nonbookable_periods(rooms, start_dt, end_dt):
    room_ids = [room.id for room in rooms]
    query = (NonBookablePeriod.query
             .filter(NonBookablePeriod.room_id.in_(room_ids),
                     NonBookablePeriod.start_dt <= end_dt.replace(hour=23, minute=59),
                     NonBookablePeriod.end_dt >= start_dt.replace(hour=0, minute=0)))
    return group_list(query, key=attrgetter('room_id'), sort_by=attrgetter('room_id'))
