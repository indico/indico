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

from collections import defaultdict

from flask import session
from sqlalchemy.orm import raiseload

from indico.core.db import db
from indico.modules.rb import rb_is_admin, rb_settings
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.schemas import rooms_schema


def search_for_rooms(filters, only_available=False):
    query = (Room.query
             .options(raiseload('owner'))
             .filter(Room.is_active)
             .order_by(db.func.indico.natsort(Room.full_name)))

    criteria = {}
    if 'capacity' in filters:
        query = query.filter(db.or_(Room.capacity >= (filters['capacity'] * 0.8), Room.capacity.is_(None)))
    if 'room_name' in filters:
        query = query.filter(Room.name.ilike('%{}%'.format(filters['room_name'])))
    if 'building' in filters:
        criteria['building'] = filters['building']
    if 'floor' in filters:
        criteria['floor'] = filters['floor']
    query = query.filter_by(**criteria)
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
