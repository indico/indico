# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict, defaultdict
from datetime import date, datetime, time
from itertools import chain, groupby
from operator import attrgetter, itemgetter

from flask import flash, session
from pytz import timezone
from sqlalchemy.orm import contains_eager, joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, with_total_rows
from indico.core.errors import NoReportError
from indico.modules.events.models.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.rb import rb_settings
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation, ReservationLink
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.operations.blockings import filter_blocked_rooms, get_rooms_blockings, group_blocked_rooms
from indico.modules.rb.operations.conflicts import get_concurrent_pre_bookings, get_rooms_conflicts
from indico.modules.rb.operations.misc import get_rooms_nonbookable_periods, get_rooms_unbookable_hours
from indico.modules.rb.util import (group_by_occurrence_date, serialize_availability, serialize_blockings,
                                    serialize_booking_details, serialize_nonbookable_periods, serialize_occurrences,
                                    serialize_unbookable_hours)
from indico.util.date_time import iterdays, overlaps, server_to_utc
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.util.struct.iterables import group_list


def group_blockings(blocked_rooms, dates):
    if not blocked_rooms:
        return {}
    occurrences = {}
    for blocked_room in blocked_rooms:
        blocking = blocked_room.blocking
        for date_ in dates:
            if blocking.start_date <= date_ <= blocking.end_date:
                occurrences[date_] = [blocking]
    return occurrences


def group_nonbookable_periods(periods, dates):
    if not periods:
        return {}
    occurrences = defaultdict(list)
    for period in periods:
        for d in dates:
            if period.start_dt.date() <= d <= period.end_dt.date():
                period_occurrence = NonBookablePeriod()
                period_occurrence.start_dt = ((datetime.combine(d, time(0)))
                                              if period.start_dt.date() != d else period.start_dt)
                period_occurrence.end_dt = ((datetime.combine(d, time(23, 59)))
                                            if period.end_dt.date() != d else period.end_dt)
                occurrences[d].append(period_occurrence)
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


def get_rooms_availability(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, skip_conflicts_with=None,
                           admin_override_enabled=False, skip_past_conflicts=False):
    availability = OrderedDict()
    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    date_range = sorted(set(cand.start_dt.date() for cand in candidates))
    occurrences = get_existing_rooms_occurrences(rooms, start_dt.replace(hour=0, minute=0),
                                                 end_dt.replace(hour=23, minute=59), repeat_frequency, repeat_interval)
    blocked_rooms = get_rooms_blockings(rooms, start_dt.date(), end_dt.date())
    nonoverridable_blocked_rooms = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                            nonoverridable_only=True,
                                                                            explicit=True))
    overridable_blocked_rooms = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                         overridable_only=True,
                                                                         explicit=True))
    unbookable_hours = get_rooms_unbookable_hours(rooms)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    conflicts, pre_conflicts, conflicting_candidates = get_rooms_conflicts(
        rooms, start_dt.replace(tzinfo=None), end_dt.replace(tzinfo=None),
        repeat_frequency, repeat_interval, nonoverridable_blocked_rooms,
        nonbookable_periods, unbookable_hours, skip_conflicts_with,
        allow_admin=admin_override_enabled, skip_past_conflicts=skip_past_conflicts
    )
    dates = list(candidate.start_dt.date() for candidate in candidates)
    for room in rooms:
        room_occurrences = occurrences.get(room.id, [])
        room_conflicting_candidates = conflicting_candidates.get(room.id, [])
        room_conflicts = conflicts.get(room.id, [])
        pre_room_conflicts = pre_conflicts.get(room.id, [])
        pre_bookings = [occ for occ in room_occurrences if not occ.reservation.is_accepted]
        concurrent_pre_bookings = get_concurrent_pre_bookings(pre_bookings) if pre_bookings else []
        existing_bookings = [occ for occ in room_occurrences if occ.reservation.is_accepted]
        room_nonoverridable_blocked_rooms = nonoverridable_blocked_rooms.get(room.id, [])
        room_overridable_blocked_rooms = overridable_blocked_rooms.get(room.id, [])
        room_nonbookable_periods = nonbookable_periods.get(room.id, [])
        room_unbookable_hours = unbookable_hours.get(room.id, [])

        room_candidates = get_room_candidates(candidates, room_conflicts)
        availability[room.id] = {'room_id': room.id,
                                 'candidates': group_by_occurrence_date(room_candidates),
                                 'conflicting_candidates': group_by_occurrence_date(room_conflicting_candidates),
                                 'pre_bookings': group_by_occurrence_date(pre_bookings),
                                 'concurrent_pre_bookings': group_by_occurrence_date(concurrent_pre_bookings),
                                 'bookings': group_by_occurrence_date(existing_bookings),
                                 'conflicts': group_by_occurrence_date(room_conflicts),
                                 'pre_conflicts': group_by_occurrence_date(pre_room_conflicts),
                                 'blockings': group_blockings(room_nonoverridable_blocked_rooms, dates),
                                 'overridable_blockings': group_blockings(room_overridable_blocked_rooms, dates),
                                 'nonbookable_periods': group_nonbookable_periods(room_nonbookable_periods, dates),
                                 'unbookable_hours': room_unbookable_hours}
    return date_range, availability


def get_room_candidates(candidates, conflicts):
    return [candidate for candidate in candidates
            if not (any(candidate.overlaps(conflict) for conflict in conflicts))]


def _bookings_query(filters, noload_room=False):
    reservation_strategy = contains_eager('reservation')
    if noload_room:
        reservation_strategy.raiseload('room')
    else:
        reservation_strategy.joinedload('room')
    reservation_strategy.noload('booked_for_user')
    reservation_strategy.noload('created_by_user')

    query = (ReservationOccurrence.query
             .join(Reservation)
             .join(Room)
             .filter(~Room.is_deleted)
             .options(reservation_strategy))

    text = filters.get('text')
    room_ids = filters.get('room_ids')
    booking_criteria = [Reservation.booking_reason.ilike('%{}%'.format(text)),
                        Reservation.booked_for_name.ilike('%{}%'.format(text))]
    if room_ids and text:
        query = query.filter(db.or_(Room.id.in_(room_ids), *booking_criteria))
    elif room_ids:
        query = query.filter(Room.id.in_(room_ids))
    elif text:
        query = query.filter(db.or_(*booking_criteria))

    if filters.get('start_dt'):
        query = query.filter(ReservationOccurrence.start_dt >= filters['start_dt'])
    if filters.get('end_dt'):
        query = query.filter(ReservationOccurrence.end_dt <= filters['end_dt'])

    booked_for_user = filters.get('booked_for_user')
    if booked_for_user:
        query = query.filter(db.or_(Reservation.booked_for_user == booked_for_user,
                                    Reservation.created_by_user == booked_for_user))

    if not filters.get('include_inactive'):
        query = query.filter(ReservationOccurrence.is_valid)

    return query


def get_room_calendar(start_date, end_date, room_ids, include_inactive=False, **filters):
    start_dt = datetime.combine(start_date, time(hour=0, minute=0))
    end_dt = datetime.combine(end_date, time(hour=23, minute=59))
    query = _bookings_query(dict(filters, start_dt=start_dt, end_dt=end_dt, room_ids=room_ids,
                                 include_inactive=include_inactive))
    bookings = query.order_by(db.func.indico.natsort(Room.full_name)).all()
    rooms = set()
    if room_ids:
        rooms = set(Room.query
                    .filter(~Room.is_deleted, Room.id.in_(room_ids))
                    .options(joinedload('location')))

    rooms.update(b.reservation.room for b in bookings)
    rooms = sorted(rooms, key=lambda r: natural_sort_key(r.full_name))
    occurrences_by_room = groupby(bookings, attrgetter('reservation.room_id'))
    unbookable_hours = get_rooms_unbookable_hours(rooms)
    nonbookable_periods = get_rooms_nonbookable_periods(rooms, start_dt, end_dt)
    blocked_rooms = get_rooms_blockings(rooms, start_dt, end_dt)
    nonoverridable_blocked_rooms = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                            nonoverridable_only=True,
                                                                            explicit=True))
    overridable_blocked_rooms = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                         overridable_only=True,
                                                                         explicit=True))
    dates = [d.date() for d in iterdays(start_dt, end_dt)]

    calendar = OrderedDict((room.id, {
        'room_id': room.id,
        'nonbookable_periods': group_nonbookable_periods(nonbookable_periods.get(room.id, []), dates),
        'unbookable_hours': unbookable_hours.get(room.id, []),
        'blockings': group_blockings(nonoverridable_blocked_rooms.get(room.id, []), dates),
        'overridable_blockings': group_blockings(overridable_blocked_rooms.get(room.id, []), dates),
    }) for room in rooms)

    for room_id, occurrences in occurrences_by_room:
        occurrences = list(occurrences)
        pre_bookings = [occ for occ in occurrences if occ.reservation.is_pending]
        existing_bookings = [occ for occ in occurrences if not occ.reservation.is_pending and occ.is_valid]
        concurrent_pre_bookings = get_concurrent_pre_bookings(pre_bookings)

        additional_data = {
            'bookings': group_by_occurrence_date(existing_bookings),
            'pre_bookings': group_by_occurrence_date(pre_bookings),
            'concurrent_pre_bookings': group_by_occurrence_date(concurrent_pre_bookings)
        }

        if include_inactive:
            additional_data.update({
                'cancellations': group_by_occurrence_date(occ for occ in occurrences if occ.is_cancelled),
                'rejections': group_by_occurrence_date(occ for occ in occurrences if occ.is_rejected)
            })

        calendar[room_id].update(additional_data)
    return calendar


def get_room_details_availability(room, start_dt, end_dt):
    dates = [d.date() for d in iterdays(start_dt, end_dt)]

    occurrences = get_existing_room_occurrences(room, start_dt, end_dt, RepeatFrequency.DAY, 1)
    pre_bookings = [occ for occ in occurrences if not occ.reservation.is_accepted]
    bookings = [occ for occ in occurrences if occ.reservation.is_accepted]
    blocked_rooms = get_rooms_blockings([room], start_dt.date(), end_dt.date())
    nonoverridable_blocked_rooms = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                            nonoverridable_only=True,
                                                                            explicit=True)).get(room.id, [])
    overridable_blocked_rooms = group_blocked_rooms(filter_blocked_rooms(blocked_rooms,
                                                                         overridable_only=True,
                                                                         explicit=True)).get(room.id, [])
    unbookable_hours = get_rooms_unbookable_hours([room]).get(room.id, [])
    nonbookable_periods = get_rooms_nonbookable_periods([room], start_dt, end_dt).get(room.id, [])

    availability = []
    for day in dates:
        iso_day = day.isoformat()
        nb_periods = serialize_nonbookable_periods(group_nonbookable_periods(nonbookable_periods, dates)).get(iso_day)
        availability.append({
            'bookings': serialize_occurrences(group_by_occurrence_date(bookings)).get(iso_day),
            'pre_bookings': serialize_occurrences(group_by_occurrence_date(pre_bookings)).get(iso_day),
            'blockings': serialize_blockings(group_blockings(nonoverridable_blocked_rooms, dates)).get(iso_day),
            'overridable_blockings': (serialize_blockings(group_blockings(overridable_blocked_rooms, dates))
                                      .get(iso_day)),
            'nonbookable_periods': nb_periods,
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
    unbookable_hours = get_rooms_unbookable_hours([room]).get(room.id, [])
    hours_overlap = any(hours for hours in unbookable_hours
                        if overlaps((start_dt.time(), end_dt.time()), (hours.start_time, hours.end_time)))
    nonbookable_periods = any(get_rooms_nonbookable_periods([room], start_dt, end_dt))
    blocked_rooms = get_rooms_blockings([room], start_dt, end_dt)
    nonoverridable_blocked_rooms = filter_blocked_rooms(blocked_rooms, nonoverridable_only=True, explicit=True)
    blocked_for_user = any(nonoverridable_blocked_rooms)
    user_booking = any(booking for booking in bookings if booking.reservation.booked_for_id == session.user.id)
    user_prebooking = any(prebooking for prebooking in prebookings
                          if prebooking.reservation.booked_for_id == session.user.id)

    return {
        'can_book': room.can_book(session.user, allow_admin=False),
        'can_prebook': room.can_prebook(session.user, allow_admin=False),
        'conflict_booking': any(bookings),
        'conflict_prebooking': any(prebookings),
        'unbookable': (hours_overlap or nonbookable_periods or blocked_for_user),
        'user_booking': user_booking,
        'user_prebooking': user_prebooking,
    }


def create_booking_for_event(room_id, event):
    try:
        room = Room.get_or_404(room_id)
        default_timezone = timezone(config.DEFAULT_TIMEZONE)
        start_dt = event.start_dt.astimezone(default_timezone).replace(tzinfo=None)
        end_dt = event.end_dt.astimezone(default_timezone).replace(tzinfo=None)
        booking_reason = "Event '{}'".format(event.title)
        data = dict(start_dt=start_dt, end_dt=end_dt, booked_for_user=event.creator, booking_reason=booking_reason,
                    repeat_frequency=RepeatFrequency.NEVER, event_id=event.id)
        booking = Reservation.create_from_data(room, data, session.user, ignore_admin=True)
        booking.linked_object = event
        return booking
    except NoReportError:
        flash(_("Booking could not be created. Probably somebody else booked the room in the meantime."), 'error')
        return None


def get_active_bookings(limit, start_dt, last_reservation_id=None, **filters):
    criteria = [ReservationOccurrence.start_dt > start_dt]
    if last_reservation_id is not None:
        criteria.append(db.and_(db.cast(ReservationOccurrence.start_dt, db.Date) >= start_dt,
                                ReservationOccurrence.reservation_id > last_reservation_id))

    query = (_bookings_query(filters, noload_room=True)
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


def has_same_slots(old_booking, new_booking):
    if (
        old_booking.repeat_interval != new_booking['repeat_interval']
        or old_booking.repeat_frequency != new_booking['repeat_frequency']
    ):
        return False
    return old_booking.start_dt <= new_booking['start_dt'] and old_booking.end_dt >= new_booking['end_dt']


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

    cancelled_dates = []
    rejected_occs = {}
    room = booking.room
    occurrences = sorted(booking.occurrences, key=attrgetter('start_dt'))
    old_frequency = booking.repeat_frequency
    occurrences_to_cancel = [occ for occ in occurrences if occ.start_dt >= datetime.now() and occ.is_valid]

    if old_frequency != RepeatFrequency.NEVER and new_booking_data['repeat_frequency'] == RepeatFrequency.NEVER:
        new_start_dt = new_booking_data['start_dt']
    else:
        new_start_dt = datetime.combine(occurrences_to_cancel[0].start_dt.date(), new_booking_data['start_dt'].time())
        cancelled_dates = [occ.start_dt.date() for occ in occurrences if occ.is_cancelled]
        rejected_occs = {occ.start_dt.date(): occ.rejection_reason for occ in occurrences if occ.is_rejected}

        new_end_dt = [occ for occ in occurrences if occ.start_dt < datetime.now()][-1].end_dt
        old_booking_data = {
            'booking_reason': booking.booking_reason,
            'booked_for_user': booking.booked_for_user,
            'start_dt': booking.start_dt,
            'end_dt': new_end_dt,
            'repeat_frequency': booking.repeat_frequency,
            'repeat_interval': booking.repeat_interval,
        }

        booking.modify(old_booking_data, session.user)

    for occurrence_to_cancel in occurrences_to_cancel:
        occurrence_to_cancel.cancel(session.user, silent=True)

    prebook = not room.can_book(session.user, allow_admin=False) and room.can_prebook(session.user, allow_admin=False)
    resv = Reservation.create_from_data(room, dict(new_booking_data, start_dt=new_start_dt), session.user,
                                        prebook=prebook)
    for new_occ in resv.occurrences:
        new_occ_start = new_occ.start_dt.date()
        if new_occ_start in cancelled_dates:
            new_occ.cancel(None, silent=True)
        if new_occ_start in rejected_occs:
            new_occ.reject(None, rejected_occs[new_occ_start], silent=True)

    booking.edit_logs.append(ReservationEditLog(user_name=session.user.full_name, info=[
        'Split into a new booking',
        'booking_link:{}'.format(resv.id)
    ]))
    resv.edit_logs.append(ReservationEditLog(user_name=session.user.full_name, info=[
        'Split from another booking',
        'booking_link:{}'.format(booking.id)
    ]))
    return resv


def get_matching_events(start_dt, end_dt, repeat_frequency, repeat_interval):
    """Get events suitable for booking linking.

    This finds events that overlap with an occurrence of a booking
    with the given dates where the user is a manager.
    """
    occurrences = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    excluded_categories = rb_settings.get('excluded_categories')
    return (Event.query
            .filter(~Event.is_deleted,
                    ~Event.room_reservation_links.any(ReservationLink.reservation.has(Reservation.is_accepted)),
                    db.or_(Event.happens_between(server_to_utc(occ.start_dt), server_to_utc(occ.end_dt))
                           for occ in occurrences),
                    Event.timezone == config.DEFAULT_TIMEZONE,
                    db.and_(Event.category_id != cat.id for cat in excluded_categories),
                    Event.acl_entries.any(db.and_(EventPrincipal.type == PrincipalType.user,
                                                  EventPrincipal.user_id == session.user.id,
                                                  EventPrincipal.full_access)))
            .all())


def get_booking_edit_calendar_data(booking, booking_changes):
    """Return calendar-related data for the booking edit modal."""
    room = booking.room
    booking_details = serialize_booking_details(booking)
    old_date_range = booking_details['date_range']
    booking_availability = dict(booking_details['occurrences'], candidates={}, conflicts={}, conflicting_candidates={},
                                pre_bookings={}, pre_conflicts={}, pending_cancellations={}, num_days_available=None,
                                num_conflicts=None)
    response = {
        'will_be_split': False,
        'calendars': [{'date_range': old_date_range, 'data': booking_availability}]
    }
    cancelled_dates = [occ.start_dt.date() for occ in booking.occurrences if occ.is_cancelled]
    rejected_dates = [occ.start_dt.date() for occ in booking.occurrences if occ.is_rejected]

    if should_split_booking(booking, booking_changes):
        old_frequency = booking.repeat_frequency
        future_occurrences = [occ for occ in sorted(booking.occurrences, key=attrgetter('start_dt'))
                              if occ.start_dt >= datetime.now()]
        if old_frequency != RepeatFrequency.NEVER and booking_changes['repeat_frequency'] == RepeatFrequency.NEVER:
            cancelled_dates = []
            rejected_dates = []
            new_date_range, data = get_rooms_availability([room], skip_conflicts_with=[booking.id], **booking_changes)
        else:
            new_booking_start_dt = datetime.combine(future_occurrences[0].start_dt.date(),
                                                    booking_changes['start_dt'].time())
            availability_filters = dict(booking_changes, start_dt=new_booking_start_dt)
            new_date_range, data = get_rooms_availability([room], skip_conflicts_with=[booking.id],
                                                          **availability_filters)

        for occ in booking.occurrences:
            serialized = serialize_occurrences({occ.start_dt.date(): [occ]})
            if occ in future_occurrences and occ.is_valid:
                booking_availability['pending_cancellations'].update(serialized)
            elif not occ.is_rejected and not occ.is_cancelled:
                booking_availability['bookings'].update(serialized)

        response['will_be_split'] = True
    elif not has_same_dates(booking, booking_changes):
        new_date_range, data = get_rooms_availability([room], skip_conflicts_with=[booking.id],
                                                      skip_past_conflicts=True, **booking_changes)
    else:
        return response

    room_availability = data[room.id]
    room_availability['cancellations'] = {}
    room_availability['rejections'] = {}
    others = defaultdict(list)
    for k, v in chain(room_availability['bookings'].iteritems(), room_availability['pre_bookings'].iteritems()):
        others[k].extend(v)
    other_bookings = {dt: filter(lambda x: x.reservation.id != booking.id, other) for dt, other in others.iteritems()}
    candidates = room_availability['candidates']

    for dt, dt_candidates in candidates.iteritems():
        if dt in cancelled_dates:
            candidates[dt] = []
            room_availability['cancellations'].update({dt: dt_candidates})
        elif dt in rejected_dates:
            candidates[dt] = []
            room_availability['rejections'].update({dt: dt_candidates})

    room_availability['num_days_available'] = (
        len(new_date_range) -
        len(room_availability['conflicts']) -
        len(room_availability['cancellations']) -
        len(room_availability['rejections'])
    )
    room_availability['num_conflicts'] = len(room_availability['conflicts'])
    room_availability['bookings'] = {}
    room_availability['other'] = serialize_occurrences(other_bookings)
    room_availability['pending_cancellations'] = {}
    response['calendars'].append({'date_range': new_date_range, 'data': serialize_availability(data)[room.id]})
    return response
