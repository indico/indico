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

from collections import OrderedDict, defaultdict
from datetime import datetime, time
from itertools import groupby
from operator import attrgetter, itemgetter

from flask import session
from pytz import timezone
from sqlalchemy.orm import contains_eager, joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap
from indico.core.errors import NoReportError
from indico.modules.rb import rb_settings
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.operations.blockings import get_rooms_blockings
from indico.modules.rb_new.operations.conflicts import get_rooms_conflicts
from indico.modules.rb_new.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
from indico.modules.rb_new.util import (group_by_occurrence_date, serialize_blockings, serialize_nonbookable_periods,
                                        serialize_occurrences, serialize_unbookable_hours)
from indico.util.date_time import iterdays, overlaps
from indico.util.struct.iterables import group_list
from indico.web.util import ExpectedError


def group_blockings(blocked_rooms, dates):
    if not blocked_rooms:
        return {}
    occurrences = {}
    for blocked_room in blocked_rooms:
        blocking = blocked_room.blocking
        for date in dates:
            if blocking.start_date <= date <= blocking.end_date:
                occurrences[date] = [blocking]
    return occurrences


def group_nonbookable_periods(periods, dates):
    if not periods:
        return {}
    occurrences = defaultdict(list)
    for period in periods:
        for date in dates:
            if period.start_dt.date() <= date <= period.end_dt.date():
                period_occurrence = NonBookablePeriod()
                period_occurrence.start_dt = ((datetime.combine(date, time(0)))
                                              if period.start_dt.date() != date else period.start_dt)
                period_occurrence.end_dt = ((datetime.combine(date, time(23, 59)))
                                            if period.end_dt.date() != date else period.end_dt)
                occurrences[date].append(period_occurrence)
    return occurrences


def get_existing_room_occurrences(room, start_dt, end_dt, repeat_frequency=RepeatFrequency.NEVER, repeat_interval=None,
                                  allow_overlapping=False, only_accepted=False):
    return get_existing_rooms_occurrences([room], start_dt, end_dt, repeat_frequency, repeat_interval,
                                          allow_overlapping, only_accepted).get(room.id, [])


def get_existing_rooms_occurrences(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, allow_overlapping=False,
                                   only_accepted=False):
    room_ids = [room.id for room in rooms]
    query = (ReservationOccurrence.query
             .filter(ReservationOccurrence.is_valid, Reservation.room_id.in_(room_ids))
             .join(ReservationOccurrence.reservation)
             .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY,
                      contains_eager(ReservationOccurrence.reservation)))

    if allow_overlapping:
        query = query.filter(db_dates_overlap(ReservationOccurrence, 'start_dt', start_dt, 'end_dt', end_dt))
    else:
        query = query.filter(ReservationOccurrence.start_dt >= start_dt, ReservationOccurrence.end_dt <= end_dt)
    if only_accepted:
        query = query.filter(Reservation.is_accepted)
    if repeat_frequency != RepeatFrequency.NEVER:
        candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
        dates = [candidate.start_dt for candidate in candidates]
        query = query.filter(db.cast(ReservationOccurrence.start_dt, db.Date).in_(dates))

    return group_list(query, key=lambda obj: obj.reservation.room.id,
                      sort_by=lambda obj: (obj.reservation.room_id, obj.start_dt))


def get_rooms_availability(rooms, start_dt, end_dt, repeat_frequency, repeat_interval):
    availability = OrderedDict()
    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    date_range = sorted(set(cand.start_dt.date() for cand in candidates))
    occurrences = get_existing_rooms_occurrences(rooms, start_dt.replace(hour=0, minute=0),
                                                 end_dt.replace(hour=23, minute=59), repeat_frequency, repeat_interval)
    blocked_rooms = get_rooms_blockings(rooms, start_dt.date(), end_dt.date())
    unbookable_hours = get_rooms_unbookable_hours(rooms)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    conflicts, pre_conflicts = get_rooms_conflicts(rooms, start_dt.replace(tzinfo=None), end_dt.replace(tzinfo=None),
                                                   repeat_frequency, repeat_interval, blocked_rooms,
                                                   nonbookable_periods, unbookable_hours)
    dates = list(candidate.start_dt.date() for candidate in candidates)
    for room in rooms:
        room_occurrences = occurrences.get(room.id, [])
        room_conflicts = conflicts.get(room.id, [])
        pre_room_conflicts = pre_conflicts.get(room.id, [])
        pre_bookings = [occ for occ in room_occurrences if not occ.reservation.is_accepted]
        existing_bookings = [occ for occ in room_occurrences if occ.reservation.is_accepted]
        room_blocked_rooms = blocked_rooms.get(room.id, [])
        room_nonbookable_periods = nonbookable_periods.get(room.id, [])
        room_unbookable_hours = unbookable_hours.get(room.id, [])
        availability[room.id] = {'room_id': room.id,
                                 'candidates': group_by_occurrence_date(candidates),
                                 'pre_bookings': group_by_occurrence_date(pre_bookings),
                                 'bookings': group_by_occurrence_date(existing_bookings),
                                 'conflicts': group_by_occurrence_date(room_conflicts),
                                 'pre_conflicts': group_by_occurrence_date(pre_room_conflicts),
                                 'blockings': group_blockings(room_blocked_rooms, dates),
                                 'nonbookable_periods': group_nonbookable_periods(room_nonbookable_periods, dates),
                                 'unbookable_hours': room_unbookable_hours}
    return date_range, availability


def get_room_calendar(start_date, end_date, room_ids, **filters):
    start_dt = datetime.combine(start_date, time(hour=0, minute=0))
    end_dt = datetime.combine(end_date, time(hour=23, minute=59))
    reservation_strategy = contains_eager('reservation')
    reservation_strategy.noload('room')
    reservation_strategy.noload('booked_for_user')
    reservation_strategy.noload('created_by_user')
    query = (ReservationOccurrence.query
             .filter(ReservationOccurrence.is_valid)
             .filter(ReservationOccurrence.start_dt >= start_dt, ReservationOccurrence.end_dt <= end_dt)
             .join(Reservation)
             .join(Room)
             .filter(Room.is_active, Room.id.in_(room_ids) if room_ids else True)
             .order_by(db.func.indico.natsort(Room.full_name))
             .options(reservation_strategy))

    booked_for_user = filters.get('booked_for_user')
    if booked_for_user:
        query = query.filter(db.or_(Reservation.booked_for_user == booked_for_user,
                                    Reservation.created_by_user == booked_for_user))

    rooms = (Room.query
             .filter(Room.is_active, Room.id.in_(room_ids) if room_ids else True)
             .options(joinedload('location'))
             .order_by(db.func.indico.natsort(Room.full_name))
             .all())

    unbookable_hours = get_rooms_unbookable_hours(rooms)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    occurrences_by_room = groupby(query, attrgetter('reservation.room_id'))
    blocked_rooms = get_rooms_blockings(rooms, start_dt, end_dt)

    dates = [d.date() for d in iterdays(start_dt, end_dt)]

    calendar = OrderedDict((room.id, {
        'room_id': room.id,
        'nonbookable_periods': group_nonbookable_periods(nonbookable_periods.get(room.id, []), dates),
        'unbookable_hours': unbookable_hours.get(room.id, []),
        'blockings': group_blockings(blocked_rooms.get(room.id, []), dates),
    }) for room in rooms)

    for room_id, occurrences in occurrences_by_room:
        occurrences = list(occurrences)
        pre_bookings = [occ for occ in occurrences if not occ.reservation.is_accepted]
        existing_bookings = [occ for occ in occurrences if occ.reservation.is_accepted]

        calendar[room_id].update({
            'bookings': group_by_occurrence_date(existing_bookings),
            'pre_bookings': group_by_occurrence_date(pre_bookings)
        })
    return calendar


def get_room_details_availability(room, start_dt, end_dt):
    dates = [d.date() for d in iterdays(start_dt, end_dt)]

    bookings = get_existing_room_occurrences(room, start_dt, end_dt, RepeatFrequency.DAY, 1, only_accepted=True)
    blockings = get_rooms_blockings([room], start_dt.date(), end_dt.date()).get(room.id, [])
    unbookable_hours = get_rooms_unbookable_hours([room]).get(room.id, [])
    nonbookable_periods = get_rooms_nonbookable_periods([room], start_dt, end_dt).get(room.id, [])

    availability = []
    for day in dates:
        iso_day = day.isoformat()
        availability.append({
            'bookings': serialize_occurrences(group_by_occurrence_date(bookings)).get(iso_day),
            'blockings': serialize_blockings(group_blockings(blockings, dates)).get(iso_day),
            'nonbookable_periods': serialize_nonbookable_periods(
                group_nonbookable_periods(nonbookable_periods, dates)).get(iso_day),
            'unbookable_hours': serialize_unbookable_hours(unbookable_hours),
            'day': iso_day,
        })
    return sorted(availability, key=itemgetter('day'))


def get_booking_occurrences(booking):
    date_range = sorted(set(cand.start_dt.date() for cand in booking.occurrences))
    occurrences = group_by_occurrence_date(booking.occurrences)
    return date_range, occurrences


def check_room_available(room, start_dt, end_dt):
    occurrences = get_existing_room_occurrences(room, start_dt, end_dt, allow_overlapping=True)
    prebookings = [occ for occ in occurrences if not occ.reservation.is_accepted]
    bookings = [occ for occ in occurrences if occ.reservation.is_accepted]
    unbookable_hours = get_rooms_unbookable_hours([room])
    hours_overlap = [hours for hours in unbookable_hours
                     if overlaps((start_dt.time(), end_dt.time()), (hours.start_time, hours.end_time))]
    nonbookable_periods = get_rooms_nonbookable_periods([room], start_dt, end_dt)
    blockings = get_rooms_blockings([room], start_dt, end_dt).get(room.id, [])
    blocked_for_user = [blocking for blocking in blockings
                        if not blocking.blocking.can_be_overridden(session.user, room)]
    user_bookings = [booking for booking in bookings if booking.reservation.booked_for_id == session.user.id]
    user_prebookings = [prebooking for prebooking in prebookings
                        if prebooking.reservation.booked_for_id == session.user.id]

    return {
        'can_book': room.can_be_booked(session.user),
        'can_prebook': room.can_be_prebooked(session.user),
        'conflict_booking': bool(bookings),
        'conflict_prebooking': bool(prebookings),
        'unbookable': bool(hours_overlap or nonbookable_periods or blocked_for_user),
        'user_booking': bool(user_bookings),
        'user_prebooking': bool(user_prebookings),
    }


def create_booking_for_event(room_id, event):
    try:
        room = Room.get_one(room_id)
        default_timezone = timezone(config.DEFAULT_TIMEZONE)
        start_dt = event.start_dt.astimezone(default_timezone).replace(tzinfo=None)
        end_dt = event.end_dt.astimezone(default_timezone).replace(tzinfo=None)
        booking_reason = "Event '%s'" % (event.title)
        data = dict(start_dt=start_dt, end_dt=end_dt, booked_for_user=event.creator, booking_reason=booking_reason,
                    repeat_frequency=RepeatFrequency.NEVER, event_id=event.id)
        resv = Reservation.create_from_data(room, data, session.user)
        db.session.flush()
    except NoReportError as e:
        db.session.rollback()
        raise ExpectedError(unicode(e))
    return resv
