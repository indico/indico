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

from itertools import chain

from flask import session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import raiseload

from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import escape_like
from indico.modules.rb import rb_is_admin, rb_settings
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.room_attributes import RoomAttributeAssociation
from indico.modules.rb.models.rooms import Room
from indico.util.caching import memoize_redis


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


def _make_room_text_filter(text):
    text = '%{}%'.format(escape_like(text))
    columns = ('name', 'site', 'division', 'building', 'floor', 'number', 'comments', 'full_name')
    return db.or_(getattr(Room, col).ilike(text) for col in columns)


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


def search_for_rooms(filters, availability=None):
    """Search for a room, using the provided filters.

    :param filters: The filters, provided as a dictionary
    :param availability: A boolean specifying whether (un)available rooms should be provided,
                         or `None` in case all rooms should be returned.
    """
    query = (Room.query
             .outerjoin(favorite_room_table, db.and_(favorite_room_table.c.user_id == session.user.id,
                                                     favorite_room_table.c.room_id == Room.id))
             .reset_joinpoint()  # otherwise filter_by() would apply to the favorite table
             .options(raiseload('owner'))
             .filter(Room.is_active)
             .order_by(favorite_room_table.c.user_id.is_(None), db.func.indico.natsort(Room.full_name)))

    criteria = {}
    if 'capacity' in filters:
        query = query.filter(Room.capacity >= filters['capacity'])
    if 'building' in filters:
        criteria['building'] = filters['building']
    if 'floor' in filters:
        criteria['floor'] = filters['floor']
    if 'division' in filters:
        criteria['division'] = filters['division']
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

    if availability is None:
        return query

    start_dt, end_dt = filters['start_dt'], filters['end_dt']
    repeatability = (filters['repeat_frequency'], filters['repeat_interval'])
    availability_query = Room.filter_available(start_dt, end_dt, repeatability, include_pre_bookings=True,
                                               include_pending_blockings=True)

    if availability is False:
        availability_query = ~availability_query

    query = query.filter(availability_query)

    if not rb_is_admin(session.user):
        selected_period_days = (filters['end_dt'] - filters['start_dt']).days
        booking_limit_days = db.func.coalesce(Room.booking_limit_days, rb_settings.get('booking_limit'))

        own_rooms = [r.id for r in Room.get_owned_by(session.user)]
        query = query.filter(db.or_(Room.id.in_(own_rooms) if own_rooms else False,
                                    db.and_(Room.filter_bookable_hours(start_dt.time(), end_dt.time()),
                                            Room.filter_nonbookable_periods(start_dt, end_dt),
                                            db.or_(booking_limit_days.is_(None),
                                                   selected_period_days <= booking_limit_days))))
    return query
