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
from datetime import date, datetime, time
from itertools import groupby
from operator import attrgetter, itemgetter

from flask import flash, session
from pytz import timezone
from sqlalchemy.orm import contains_eager, joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, with_total_rows
from indico.core.errors import NoReportError
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
from indico.util.i18n import _
from indico.util.struct.iterables import group_list


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
                                  allow_overlapping=False, only_accepted=False, skip_booking_id=None):
    return get_existing_rooms_occurrences([room], start_dt, end_dt, repeat_frequency, repeat_interval,
                                          allow_overlapping, only_accepted, skip_booking_id).get(room.id, [])


def get_existing_rooms_occurrences(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, allow_overlapping=False,
                                   only_accepted=False, skip_booking_id=None):
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
    if skip_booking_id is not None:
        query = query.filter(ReservationOccurrence.reservation_id != skip_booking_id)

    return group_list(query, key=lambda obj: obj.reservation.room_id,
                      sort_by=lambda obj: (obj.reservation.room_id, obj.start_dt))


def get_rooms_availability(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, skip_conflicts_with=None):
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
                                                   nonbookable_periods, unbookable_hours, skip_conflicts_with)
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


def _bookings_query(filters):
    reservation_strategy = contains_eager('reservation')
    reservation_strategy.noload('room')
    reservation_strategy.noload('booked_for_user')
    reservation_strategy.noload('created_by_user')

    query = (ReservationOccurrence.query
             .filter(ReservationOccurrence.is_valid)
             .join(Reservation)
             .join(Room)
             .filter(Room.is_active)
             .options(reservation_strategy))

    if filters.get('room_ids'):
        query = query.filter(Room.id.in_(filters['room_ids']))
    if filters.get('start_date'):
        query = query.filter(ReservationOccurrence.start_dt >= filters['start_date'])
    if filters.get('end_date'):
        query = query.filter(ReservationOccurrence.end_dt <= filters['end_date'])

    booked_for_user = filters.get('booked_for_user')
    if booked_for_user:
        query = query.filter(db.or_(Reservation.booked_for_user == booked_for_user,
                                    Reservation.created_by_user == booked_for_user))

    return query


def get_room_calendar(start_date, end_date, room_ids, **filters):
    start_dt = datetime.combine(start_date, time(hour=0, minute=0))
    end_dt = datetime.combine(end_date, time(hour=23, minute=59))
    query = _bookings_query(dict(filters, **{'start_date': start_dt, 'end_date': end_dt, 'room_ids': room_ids}))
    query = query.order_by(db.func.indico.natsort(Room.full_name))
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
        nb_periods = serialize_nonbookable_periods(group_nonbookable_periods(nonbookable_periods, dates)).get(iso_day)
        availability.append({
            'bookings': serialize_occurrences(group_by_occurrence_date(bookings)).get(iso_day),
            'blockings': serialize_blockings(group_blockings(blockings, dates)).get(iso_day),
            'nonbookable_periods': nb_periods,
            'unbookable_hours': serialize_unbookable_hours(unbookable_hours),
            'day': iso_day,
        })
    return sorted(availability, key=itemgetter('day'))


def get_room_bookings(room, start_dt, end_dt, skip_booking_id=None):
    bookings = get_existing_room_occurrences(room, start_dt, end_dt, RepeatFrequency.DAY, 1, only_accepted=True,
                                             skip_booking_id=skip_booking_id)
    return serialize_occurrences(group_by_occurrence_date(bookings))


def get_booking_occurrences(booking):
    date_range = sorted(set(cand.start_dt.date() for cand in booking.occurrences))
    occurrences = group_by_occurrence_date(booking.occurrences)
    return date_range, occurrences


def check_room_available(room, start_dt, end_dt):
    occurrences = get_existing_room_occurrences(room, start_dt, end_dt, allow_overlapping=True)
    prebookings = [occ for occ in occurrences if not occ.reservation.is_accepted]
    bookings = [occ for occ in occurrences if occ.reservation.is_accepted]
    unbookable_hours = get_rooms_unbookable_hours([room])
    hours_overlap = any(hours for hours in unbookable_hours
                        if overlaps((start_dt.time(), end_dt.time()), (hours.start_time, hours.end_time)))
    nonbookable_periods = any(get_rooms_nonbookable_periods([room], start_dt, end_dt))
    blockings = get_rooms_blockings([room], start_dt, end_dt).get(room.id, [])
    blocked_for_user = any(blocking for blocking in blockings
                           if not blocking.blocking.can_be_overridden(session.user, room, explicit_only=True))
    user_booking = any(booking for booking in bookings if booking.reservation.booked_for_id == session.user.id)
    user_prebooking = any(prebooking for prebooking in prebookings
                          if prebooking.reservation.booked_for_id == session.user.id)

    return {
        'can_book': room.can_book(session.user, ignore_admin=True),
        'can_prebook': room.can_prebook(session.user, ignore_admin=True),
        'conflict_booking': any(bookings),
        'conflict_prebooking': any(prebookings),
        'unbookable': (hours_overlap or nonbookable_periods or blocked_for_user),
        'user_booking': user_booking,
        'user_prebooking': user_prebooking,
    }


def create_booking_for_event(room_id, event):
    try:
        room = Room.get_one(room_id)
        default_timezone = timezone(config.DEFAULT_TIMEZONE)
        start_dt = event.start_dt.astimezone(default_timezone).replace(tzinfo=None)
        end_dt = event.end_dt.astimezone(default_timezone).replace(tzinfo=None)
        booking_reason = "Event '{}'".format(event.title)
        data = dict(start_dt=start_dt, end_dt=end_dt, booked_for_user=event.creator, booking_reason=booking_reason,
                    repeat_frequency=RepeatFrequency.NEVER, event_id=event.id)
        return Reservation.create_from_data(room, data, session.user, ignore_admin=True)
    except NoReportError:
        flash(_("Booking could not be created. Probably somebody else booked the room in the meantime."), 'error')


def get_active_bookings(limit, start_dt, last_reservation_id=None, **filters):
    criteria = [ReservationOccurrence.start_dt > start_dt]
    if last_reservation_id is not None:
        criteria.append(db.and_(db.cast(ReservationOccurrence.start_dt, db.Date) >= start_dt,
                                ReservationOccurrence.reservation_id > last_reservation_id))

    query = (_bookings_query(filters)
             .filter(db.or_(*criteria))
             .order_by(ReservationOccurrence.start_dt,
                       ReservationOccurrence.reservation_id,
                       db.func.indico.natsort(Room.full_name))
             .limit(limit))

    bookings, total = with_total_rows(query)
    rows_left = total - limit if total > limit else total
    return group_by_occurrence_date(query, sort_by=lambda obj: (obj.start_dt, obj.reservation_id)), rows_left


def has_same_dates(old_booking, new_booking):
    return (old_booking.start_dt == new_booking['start_dt'] and
            old_booking.end_dt == new_booking['end_dt'] and
            old_booking.repeat_interval == new_booking['repeat_interval'] and
            old_booking.repeat_frequency == new_booking['repeat_frequency'])


def should_split_booking(booking, new_data):
    today = date.today()
    is_ongoing_booking = booking.start_dt.date() < today < booking.end_dt.date()
    old_start_time = booking.start_dt.time()
    old_end_time = booking.end_dt.time()
    old_repeat_frequency = booking.repeat_frequency
    old_repeat_interval = booking.repeat_interval
    times_changed = new_data['start_dt'].time() != old_start_time or new_data['end_dt'].time() != old_end_time
    new_repeat_frequency = new_data['repeat_frequency']
    new_repeat_interval = new_data['repeat_interval']
    repetition_changed = (new_repeat_frequency, new_repeat_interval) != (old_repeat_frequency, old_repeat_interval)
    return is_ongoing_booking and (times_changed or repetition_changed)


def split_booking(booking, new_booking_data):
    is_ongoing_booking = booking.start_dt.date() < date.today() < booking.end_dt.date()
    if not is_ongoing_booking:
        return

    room = booking.room
    occurrences = sorted(booking.occurrences, key=attrgetter('start_dt'))
    occurrences_to_cancel = [occ for occ in occurrences if occ.start_dt.date() >= date.today()]
    new_start_dt = datetime.combine(occurrences_to_cancel[0].start_dt.date(), new_booking_data['start_dt'].time())
    for occurrence_to_cancel in occurrences_to_cancel:
        occurrence_to_cancel.cancel(session.user, silent=True)

    new_end_dt = [occ for occ in occurrences if occ.start_dt.date() < date.today()][-1].end_dt
    old_booking_data = {
        'booking_reason': booking.booking_reason,
        'room_usage': 'current_user' if booking.booked_for_user == session.user else 'someone',
        'booked_for_user': booking.booked_for_user,
        'start_dt': booking.start_dt,
        'end_dt': new_end_dt,
        'repeat_frequency': booking.repeat_frequency,
        'repeat_interval': booking.repeat_interval,
    }

    booking.modify(old_booking_data, session.user)
    prebook = not room.can_book(session.user, allow_admin=False) and room.can_prebook(session.user, allow_admin=False)
    return Reservation.create_from_data(room, dict(new_booking_data, start_dt=new_start_dt), session.user,
                                        prebook=prebook)
