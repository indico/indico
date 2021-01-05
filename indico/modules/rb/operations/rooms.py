# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta
from flask import session
from sqlalchemy.orm import joinedload, load_only

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, escape_like
from indico.modules.rb import rb_settings
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.principals import RoomPrincipal
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.statistics import calculate_rooms_occupancy
from indico.modules.rb.util import rb_is_admin
from indico.util.caching import memoize_redis


def _filter_coordinates(query, filters):
    try:
        sw_lat = filters['sw_lat']
        sw_lng = filters['sw_lng']
        ne_lat = filters['ne_lat']
        ne_lng = filters['ne_lng']
    except KeyError:
        return query

    return query.filter(Room.latitude >= sw_lat,
                        Room.latitude <= ne_lat,
                        Room.longitude >= sw_lng,
                        Room.longitude <= ne_lng)


def _make_room_text_filter(text):
    text = '%{}%'.format(escape_like(text))
    columns = ('site', 'division', 'building', 'floor', 'number', 'comments', 'full_name')
    return db.or_(getattr(Room, col).ilike(text) for col in columns)


def _query_managed_rooms(user):
    criteria = [db.and_(RoomPrincipal.type == PrincipalType.user,
                        RoomPrincipal.user_id == user.id,
                        RoomPrincipal.has_management_permission())]
    for group in user.local_groups:
        criteria.append(db.and_(RoomPrincipal.type == PrincipalType.local_group,
                                RoomPrincipal.local_group_id == group.id,
                                RoomPrincipal.has_management_permission()))
    for group in user.iter_all_multipass_groups():
        criteria.append(db.and_(RoomPrincipal.type == PrincipalType.multipass_group,
                                RoomPrincipal.multipass_group_provider == group.provider.name,
                                db.func.lower(RoomPrincipal.multipass_group_name) == group.name.lower(),
                                RoomPrincipal.has_management_permission()))
    return Room.query.filter(~Room.is_deleted, Room.acl_entries.any(db.or_(*criteria)) | (Room.owner == user))


def _query_all_rooms_for_acl_check():
    return (Room.query
            .filter(~Room.is_deleted)
            .options(load_only('id', 'protection_mode', 'reservations_need_confirmation'),
                     joinedload('owner').load_only('id'),
                     joinedload('acl_entries')))


@memoize_redis(900)
def has_managed_rooms(user):
    if user.can_get_all_multipass_groups:
        return _query_managed_rooms(user).has_rows()
    else:
        query = _query_all_rooms_for_acl_check()
        return any(r.can_manage(user, allow_admin=False) for r in query)


@memoize_redis(900)
def get_managed_room_ids(user):
    if user.can_get_all_multipass_groups:
        return {id_ for id_, in _query_managed_rooms(user).with_entities(Room.id)}
    else:
        query = _query_all_rooms_for_acl_check()
        return {r.id for r in query if r.can_manage(user, allow_admin=False)}


@memoize_redis(3600)
def get_room_statistics(room):
    data = {
        'count': {
            'id': 'times_booked',
            'values': [],
            'note': False
        },
        'percentage': {
            'id': 'occupancy',
            'values': [],
            'note': True
        }
    }
    ranges = [7, 30, 365]
    end_date = date.today()
    for days in ranges:
        start_date = date.today() - relativedelta(days=days)
        count = (ReservationOccurrence.query
                 .join(ReservationOccurrence.reservation)
                 .join(Reservation.room)
                 .filter(Room.id == room.id,
                         ReservationOccurrence.is_valid,
                         db_dates_overlap(ReservationOccurrence,
                                          'start_dt', datetime.combine(start_date, time()),
                                          'end_dt', datetime.combine(end_date, time.max)))
                 .count())
        percentage = calculate_rooms_occupancy([room], start_date, end_date) * 100
        if count > 0 or percentage > 0:
            data['count']['values'].append({'days': days, 'value': count})
            data['percentage']['values'].append({'days': days, 'value': percentage})
    return data


def search_for_rooms(filters, allow_admin=False, availability=None):
    """Search for a room, using the provided filters.

    :param filters: The filters, provided as a dictionary
    :param allow_admin: A boolean specifying whether admins have override privileges
    :param availability: A boolean specifying whether (un)available rooms should be provided,
                         or `None` in case all rooms should be returned.
    """
    query = (Room.query
             .outerjoin(favorite_room_table, db.and_(favorite_room_table.c.user_id == session.user.id,
                                                     favorite_room_table.c.room_id == Room.id))
             .reset_joinpoint()  # otherwise filter_by() would apply to the favorite table
             .options(joinedload('owner').load_only('id'))
             .filter(~Room.is_deleted)
             .order_by(favorite_room_table.c.user_id.is_(None), db.func.indico.natsort(Room.full_name)))

    criteria = {}
    if 'capacity' in filters:
        query = query.filter(Room.capacity >= filters['capacity'])
    if 'building' in filters:
        criteria['building'] = filters['building']
    if 'division' in filters:
        criteria['division'] = filters['division']
    query = query.filter_by(**criteria)
    if 'text' in filters:
        text = ' '.join(filters['text'].strip().split())
        if text.startswith('#') and text[1:].isdigit():
            query = query.filter(Room.id == int(text[1:]))
        else:
            query = query.filter(_make_room_text_filter(text))
    if filters.get('equipment'):
        subquery = (db.session.query(RoomEquipmentAssociation)
                    .with_entities(db.func.count(RoomEquipmentAssociation.c.room_id))
                    .filter(RoomEquipmentAssociation.c.room_id == Room.id,
                            EquipmentType.name.in_(filters['equipment']))
                    .join(EquipmentType, RoomEquipmentAssociation.c.equipment_id == EquipmentType.id)
                    .correlate(Room)
                    .as_scalar())
        query = query.filter(subquery == len(filters['equipment']))
    if filters.get('features'):
        for feature in filters['features']:
            query = query.filter(Room.available_equipment.any(EquipmentType.features.any(RoomFeature.name == feature)))
    if filters.get('favorite'):
        query = query.filter(favorite_room_table.c.user_id.isnot(None))
    if filters.get('mine'):
        ids = get_managed_room_ids(session.user)
        query = query.filter(Room.id.in_(ids))
    query = _filter_coordinates(query, filters)

    if availability is None:
        return query

    start_dt, end_dt = filters['start_dt'], filters['end_dt']
    repeatability = (filters['repeat_frequency'], filters['repeat_interval'])
    availability_filters = [Room.filter_available(start_dt, end_dt, repeatability, include_blockings=False,
                                                  include_pre_bookings=False)]
    if not (allow_admin and rb_is_admin(session.user)):
        selected_period_days = (filters['end_dt'] - filters['start_dt']).days
        booking_limit_days = db.func.coalesce(Room.booking_limit_days, rb_settings.get('booking_limit'))

        criterion = db.and_(Room.filter_bookable_hours(start_dt.time(), end_dt.time()),
                            Room.filter_nonbookable_periods(start_dt, end_dt),
                            db.or_(booking_limit_days.is_(None),
                            selected_period_days <= booking_limit_days))
        unbookable_ids = [room.id
                          for room in query.filter(db.and_(*availability_filters), ~criterion)
                          if not room.can_override(session.user, allow_admin=False)]
        availability_filters.append(~Room.id.in_(unbookable_ids))
    availability_criterion = db.and_(*availability_filters)
    if availability is False:
        availability_criterion = ~availability_criterion
    return query.filter(availability_criterion)
