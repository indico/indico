# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import datetime

from indico.core.db import db
from indico.modules.rb.models.map_areas import MapArea
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.util.struct.iterables import group_list


def get_rooms_unbookable_hours(rooms):
    room_ids = [room.id for room in rooms]
    query = BookableHours.query.filter(BookableHours.room_id.in_(room_ids))
    rooms_hours = group_list(query, key=lambda obj: obj.room_id)
    inverted_rooms_hours = {}
    for room_id, hours in rooms_hours.iteritems():
        hours.sort(key=lambda x: x.start_time)
        inverted_hours = []
        first = BookableHours(start_time=datetime.strptime('00:00', '%H:%M').time(), end_time=hours[0].start_time)
        inverted_hours.append(first)
        for i in range(1, len(hours)):
            hour = BookableHours(start_time=hours[i - 1].end_time, end_time=hours[i].start_time)
            inverted_hours.append(hour)
        last = BookableHours(start_time=hours[-1].end_time,
                             end_time=datetime.strptime('23:59', '%H:%M').time())
        inverted_hours.append(last)
        inverted_rooms_hours[room_id] = inverted_hours
    return inverted_rooms_hours


def get_rooms_nonbookable_periods(rooms, start_dt, end_dt):
    room_ids = [room.id for room in rooms]
    query = (NonBookablePeriod.query
             .filter(NonBookablePeriod.room_id.in_(room_ids),
                     NonBookablePeriod.start_dt <= end_dt.replace(hour=23, minute=59),
                     NonBookablePeriod.end_dt >= start_dt.replace(hour=0, minute=0)))
    return group_list(query, key=lambda obj: obj.room_id)


def create_area(area_data):
    bounds = area_data['bounds']
    top, bottom = bounds['north_east'], bounds['south_west']
    is_default = area_data.get('default', False)

    if is_default:
        MapArea.query.update({MapArea.is_default: False}, synchronize_session='fetch')

    new_area = MapArea()
    new_area.name = area_data['name']
    new_area.is_default = is_default
    new_area.top_left_latitude = top['lat']
    new_area.top_left_longitude = top['lng']
    new_area.bottom_right_latitude = bottom['lat']
    new_area.bottom_right_longitude = bottom['lng']
    db.session.add(new_area)
    db.session.flush()
    return new_area


def update_area(area_id, area_data):
    top = area_data['bounds']['north_east']
    bottom = area_data['bounds']['south_west']
    map_area = MapArea.get_one(area_id)
    if 'name' in area_data:
        map_area.name = area_data['name']
    if 'default' in area_data:
        if area_data['default']:
            MapArea.query.update({MapArea.is_default: False}, synchronize_session='fetch')
        map_area.is_default = area_data['default']
    map_area.top_left_latitude = top['lat']
    map_area.top_left_longitude = top['lng']
    map_area.bottom_right_latitude = bottom['lat']
    map_area.bottom_right_longitude = bottom['lng']
    db.session.flush()


def delete_areas(area_ids):
    MapArea.query.filter(MapArea.id.in_(area_ids)).delete(synchronize_session='fetch')
    db.session.flush()
