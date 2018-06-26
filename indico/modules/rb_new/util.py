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

from collections import defaultdict, namedtuple
from datetime import timedelta
from itertools import chain

from flask import session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import contains_eager, raiseload

from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, escape_like
from indico.modules.rb import rb_is_admin, rb_settings
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.room_attributes import RoomAttributeAssociation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.schemas import reservation_occurrences_schema, rooms_schema
from indico.util.caching import memoize_redis
from indico.util.struct.iterables import group_list


BOOKING_TIME_DIFF = 20  # (minutes)
DURATION_FACTOR = 0.25


def _filter_coordinates(query, filters):
    try:
        sw_lat = filters['sw_lat']
        sw_lng = filters['sw_lng']
        ne_lat = filters['ne_lat']
        ne_lng = filters['ne_lng']
    except KeyError:
        return query

    return query.filter(db.cast(Room.latitude, db.Float) >= sw_lat,
                        db.cast(Room.latitude, db.Float) <= ne_lat,
                        db.cast(Room.longitude, db.Float) >= sw_lng,
                        db.cast(Room.longitude, db.Float) <= ne_lng)


def search_for_rooms(filters, only_available=False):
    query = (Room.query
             .outerjoin(favorite_room_table, db.and_(favorite_room_table.c.user_id == session.user.id,
                                                     favorite_room_table.c.room_id == Room.id))
             .reset_joinpoint()  # otherwise filter_by() would apply to the favorite table
             .options(raiseload('owner'))
             .filter(Room.is_active)
             .order_by(favorite_room_table.c.user_id.is_(None), db.func.indico.natsort(Room.full_name)))

    criteria = {}
    if 'capacity' in filters:
        query = query.filter(db.or_(Room.capacity >= (filters['capacity'] * 0.8), Room.capacity.is_(None)))
    if 'building' in filters:
        criteria['building'] = filters['building']
    if 'floor' in filters:
        criteria['floor'] = filters['floor']
    query = query.filter_by(**criteria)
    if 'text' in filters:
        query = query.filter(_make_room_text_filter(filters['text']))
    if filters.get('equipment'):
        subquery = (db.session.query(RoomEquipmentAssociation)
                    .with_entities(db.func.count(RoomEquipmentAssociation.c.room_id))
                    .filter(
                        RoomEquipmentAssociation.c.room_id == Room.id,
                        EquipmentType.name.in_(filters['equipment'])
                    )
                    .join(EquipmentType, RoomEquipmentAssociation.c.equipment_id == EquipmentType.id)
                    .correlate(Room)
                    .as_scalar())
        query = query.filter(subquery == len(filters['equipment']))
    if filters.get('favorite'):
        query = query.filter(favorite_room_table.c.user_id.isnot(None))
    if filters.get('mine'):
        ids = get_managed_room_ids(session.user)
        if ids:
            query = query.filter(Room.id.in_(ids))
    query = _filter_coordinates(query, filters)

    if not only_available:
        return query

    start_dt, end_dt = filters['start_dt'], filters['end_dt']
    repeatability = (filters['repeat_frequency'], filters['repeat_interval'])
    query = query.filter(Room.filter_available(start_dt, end_dt, repeatability, include_pre_bookings=True,
                                               include_pending_blockings=True))
    if not rb_is_admin(session.user):
        selected_period_days = (filters['end_dt'] - filters['start_dt']).days
        booking_limit_days = db.func.coalesce(Room.booking_limit_days, rb_settings.get('booking_limit'))

        own_rooms = [r.id for r in Room.get_owned_by(session.user)]
        query = query.filter(db.or_(Room.id.in_(own_rooms) if own_rooms else False,
                                    db.and_(Room.filter_bookable_hours(start_dt.time(), end_dt.time()),
                                            db.or_(booking_limit_days.is_(None),
                                                   selected_period_days <= booking_limit_days))))
    return query


def _make_room_text_filter(text):
    text = '%{}%'.format(escape_like(text))
    columns = ('name', 'site', 'division', 'building', 'floor', 'number', 'comments', 'full_name')
    return db.or_(getattr(Room, col).ilike(text) for col in columns)


def get_buildings():
    buildings = defaultdict(dict)
    for room in Room.query.filter_by(is_active=True):
        buildings[room.building].setdefault('rooms', []).append(room)

    buildings_tmp = defaultdict(dict)
    for building_name, building_data in buildings.iteritems():
        room_with_lat_lon = next((r for r in building_data['rooms'] if r.longitude and r.latitude), None)
        if not room_with_lat_lon:
            continue

        buildings_tmp[building_name]['rooms'] = rooms_schema.dump(building_data['rooms']).data
        buildings_tmp[building_name]['floors'] = sorted({room.floor for room in building_data['rooms']})
        buildings_tmp[building_name]['number'] = building_name
        buildings_tmp[building_name]['longitude'] = room_with_lat_lon.longitude
        buildings_tmp[building_name]['latitude'] = room_with_lat_lon.latitude
    return buildings_tmp


def get_existing_room_occurrences(room, start_dt, end_dt, allow_overlapping=False, only_accepted=False):
    query = (ReservationOccurrence.query
             .filter(Reservation.room_id == room.id, ReservationOccurrence.is_valid)
             .join(ReservationOccurrence.reservation)
             .order_by(ReservationOccurrence.start_dt.asc())
             .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY,
                      contains_eager(ReservationOccurrence.reservation)))

    if allow_overlapping:
        query = query.filter(db_dates_overlap(ReservationOccurrence, 'start_dt', start_dt, 'end_dt', end_dt))
    else:
        query = query.filter(ReservationOccurrence.start_dt >= start_dt, ReservationOccurrence.end_dt <= end_dt)
    if only_accepted:
        query = query.filter(Reservation.is_accepted)
    return query.all()


def get_room_conflicts(room, start_dt, end_dt, repeat_frequency, repeat_interval):
    conflicts = []
    pre_conflicts = []

    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    occurrences = ReservationOccurrence.find_overlapping_with(room, candidates).all()

    ReservationOccurrenceTmp = namedtuple('ReservationOccurrenceTmp', ('start_dt', 'end_dt', 'reservation'))
    for candidate in candidates:
        for occurrence in occurrences:
            if candidate.overlaps(occurrence):
                overlap = candidate.get_overlap(occurrence)
                obj = ReservationOccurrenceTmp(*overlap, reservation=occurrence.reservation)
                if occurrence.reservation.is_accepted:
                    conflicts.append(obj)
                else:
                    pre_conflicts.append(obj)
    return conflicts, pre_conflicts


def get_rooms_availability(rooms, start_dt, end_dt, repeat_frequency, repeat_interval, flexibility):
    period_days = (end_dt - start_dt).days
    availability = {}
    candidates = ReservationOccurrence.create_series(start_dt, end_dt, (repeat_frequency, repeat_interval))
    date_range = sorted(set(cand.start_dt.date() for cand in candidates))

    for room in rooms:
        booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
        if period_days > booking_limit_days:
            continue

        start_dt = start_dt + timedelta(days=flexibility)
        end_dt = end_dt + timedelta(days=flexibility)
        occurrences = get_existing_room_occurrences(room, start_dt.replace(hour=0, minute=0),
                                                    end_dt.replace(hour=23, minute=59))
        conflicts, pre_conflicts = get_room_conflicts(room, start_dt.replace(tzinfo=None), end_dt.replace(tzinfo=None),
                                                      repeat_frequency, repeat_interval)

        pre_bookings = [occ for occ in occurrences if not occ.reservation.is_accepted]
        existing_bookings = [occ for occ in occurrences if occ.reservation.is_accepted]
        availability[room.id] = {'room': room,
                                 'candidates': group_by_occurrence_date(candidates),
                                 'pre_bookings': group_by_occurrence_date(pre_bookings),
                                 'bookings': group_by_occurrence_date(existing_bookings),
                                 'conflicts': group_by_occurrence_date(conflicts),
                                 'pre_conflicts': group_by_occurrence_date(pre_conflicts)}
    return date_range, availability


def group_by_occurrence_date(occurrences):
    return group_list(occurrences, key=lambda obj: obj.start_dt.date())


def get_equipment_types():
    query = (db.session
             .query(EquipmentType.name)
             .distinct(EquipmentType.name)
             .filter(EquipmentType.rooms.any(Room.is_active))
             .order_by(EquipmentType.name))
    return [row.name for row in query]


def _can_get_all_groups(user):
    return all(multipass.identity_providers[x.provider].supports_get_identity_groups for x in user.identities)


def _query_managed_rooms(user):
    # We can get a list of all groups for the user
    iterator = chain.from_iterable(multipass.identity_providers[x.provider].get_identity_groups(x.identifier)
                                   for x in user.identities)
    groups = {(g.provider.name, g.name) for g in iterator}
    # XXX: refactor this once we have a proper ACL for rooms
    if multipass.default_group_provider:
        groups = {name for provider, name in groups if provider == multipass.default_group_provider.name}
    else:
        groups = {unicode(group.id) for group in user.local_groups}
    attrs = [db.cast(x, JSONB) for x in groups]
    is_manager = Room.attributes.any(db.cast(RoomAttributeAssociation.value, JSONB).in_(attrs))
    return Room.query.filter(Room.is_active, db.or_(Room.owner == user, is_manager))


@memoize_redis(900)
def has_managed_rooms(user):
    if _can_get_all_groups(user):
        return _query_managed_rooms(user).has_rows()
    else:
        return Room.user_owns_rooms(user)


@memoize_redis(900)
def get_managed_room_ids(user):
    if _can_get_all_groups(user):
        return {id_ for id_, in _query_managed_rooms(user).with_entities(Room.id)}
    else:
        return {r.id for r in Room.get_owned_by(user)}


def get_suggestions(filters):
    room_filters = {key: value for key, value in filters.iteritems()
                    if key in ('capacity', 'equipment', 'building', 'text', 'floor')}

    query = search_for_rooms(room_filters, only_available=False)
    query = query.filter(~Room.filter_available(filters['start_dt'], filters['end_dt'],
                                                (filters['repeat_frequency'], filters['repeat_interval'])))
    rooms = query.all()
    if filters['repeat_frequency'] == RepeatFrequency.NEVER:
        return sort_suggestions(get_single_booking_suggestions(rooms, filters['start_dt'], filters['end_dt']))
    else:
        return get_number_of_skipped_days_for_rooms(rooms, filters['start_dt'], filters['end_dt'],
                                                    filters['repeat_frequency'], filters['repeat_interval'])


def get_single_booking_suggestions(rooms, start_dt, end_dt):
    data = []
    for room in rooms:
        suggestions = {}
        suggested_time = get_start_time_suggestion(room, start_dt, end_dt)
        if suggested_time:
            suggested_time_change = (suggested_time - start_dt).total_seconds() / 60
            if suggested_time_change:
                suggestions['time'] = suggested_time_change

        duration_suggestion = get_duration_suggestion(room, start_dt, end_dt)
        original_duration = (end_dt - start_dt).total_seconds() / 60
        if duration_suggestion and duration_suggestion <= DURATION_FACTOR * original_duration:
            suggestions['duration'] = duration_suggestion
        if suggestions:
            data.append({'room': room, 'suggestions': suggestions})
    return data


def get_number_of_skipped_days_for_rooms(rooms, start_dt, end_dt, repeat_frequency, repeat_interval):
    data = []
    for room in rooms:
        conflicts = get_room_conflicts(room, start_dt, end_dt, repeat_frequency, repeat_interval)
        number_of_conflicting_days = len(group_by_occurrence_date(conflicts[0]))
        if number_of_conflicting_days:
            data.append({'room': room, 'suggestions': {'skip': number_of_conflicting_days}})
    return sorted(data, key=lambda item: item['suggestions']['skip'])


def get_start_time_suggestion(room, from_, to):
    duration = (to - from_).total_seconds() / 60
    new_start_dt = from_ - timedelta(minutes=BOOKING_TIME_DIFF)
    new_end_dt = to + timedelta(minutes=BOOKING_TIME_DIFF)
    occurrences = get_existing_room_occurrences(room, new_start_dt, new_end_dt, allow_overlapping=True)

    if not occurrences:
        return from_ - timedelta(minutes=BOOKING_TIME_DIFF)

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


def get_duration_suggestion(room, from_, to):
    occurrences = get_existing_room_occurrences(room, from_, to, allow_overlapping=True)
    old_duration = (to - from_).total_seconds() / 60
    duration = old_duration
    for occurrence in occurrences:
        start, end = occurrence.start_dt, occurrence.end_dt
        if end > from_ and end < to:
            if start > from_:
                continue
            duration -= (end - from_).total_seconds() / 60
        if start > from_ and start < to:
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


def serialize_occurrences(data):
    return {dt.isoformat(): reservation_occurrences_schema.dump(data).data for dt, data in data.iteritems()}
