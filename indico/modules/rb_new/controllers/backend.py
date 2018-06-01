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

from flask import jsonify, request, session
from marshmallow_enum import EnumField
from webargs import fields
from webargs.flaskparser import use_args

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import with_total_rows
from indico.modules.rb import Location
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.schemas import (aspects_schema, map_rooms_schema, reservation_occurrences_schema,
                                           room_details_schema, rooms_schema)
from indico.modules.rb_new.util import get_buildings, get_equipment_types, get_rooms_availability, search_for_rooms
from indico.web.util import jsonify_data


search_room_args = {
    'capacity': fields.Int(),
    'equipment': fields.List(fields.Str()),
    'favorite': fields.Bool(),
    'mine': fields.Bool(),
    'text': fields.Str(),
    'start_dt': fields.DateTime(),
    'end_dt': fields.DateTime(),
    'repeat_frequency': EnumField(RepeatFrequency),
    'repeat_interval': fields.Int(missing=0),
    'building': fields.Str(),
    'floor': fields.Str(),
    'sw_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'sw_lng': fields.Float(validate=lambda x: -180 <= x <= 180),
    'ne_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'ne_lng': fields.Float(validate=lambda x: -180 <= x <= 180)
}


class RHSearchRooms(RHRoomBookingBase):
    @use_args(dict(search_room_args, **{
        'offset': fields.Int(missing=0, validate=lambda x: x >= 0),
        'limit': fields.Int(missing=10, validate=lambda x: x >= 0)
    }))
    def _process(self, args):
        filter_availability = args.get('start_dt') and args.get('end_dt')
        query = search_for_rooms(args, only_available=filter_availability)
        query = query.limit(args['limit']).offset(args['offset'])
        rooms, total = with_total_rows(query)
        return jsonify(total=total, rooms=rooms_schema.dump(rooms).data)


class RHSearchMapRooms(RHRoomBookingBase):
    @use_args(search_room_args)
    def _process(self, args):
        filter_availability = args.get('start_dt') and args.get('end_dt')
        query = search_for_rooms(args, only_available=filter_availability)
        return jsonify(map_rooms_schema.dump(query.all()).data)


class RHRoomDetails(RHRoomBookingBase):
    def _process_args(self):
        self.room = Room.get_one(request.view_args['room_id'])

    def _process(self):
        room_details = room_details_schema.dump(self.room).data
        return jsonify(room_details)


class RHAspects(RHRoomBookingBase):
    def _process(self):
        to_cast = ['top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude']
        aspects = [
            {k: float(v) if k in to_cast else v for k, v in aspect.viewitems()}
            for aspect in aspects_schema.dump(Location.default_location.aspects).data
        ]
        return jsonify(aspects)


class RHBuildings(RHRoomBookingBase):
    def _process(self):
        return jsonify(get_buildings())


class RHEquipmentTypes(RHRoomBookingBase):
    def _process(self):
        return jsonify(get_equipment_types())


class RHTimeline(RHRoomBookingBase):
    @use_args({
        'room_ids': fields.List(fields.Int()),
        'start_dt': fields.DateTime(),
        'end_dt': fields.DateTime(),
        'repeat_frequency': EnumField(RepeatFrequency),
        'repeat_interval': fields.Int(missing=0),
        'flexibility': fields.Int(missing=0)
    })
    def _process(self, args):
        rooms = Room.query.filter(Room.is_active, Room.id.in_(args.pop('room_ids')))
        date_range, availability = get_rooms_availability(rooms, **args)
        date_range = [dt.isoformat() for dt in date_range]
        for room_availability in availability:
            data = availability[room_availability]
            data.update({k: self._serialize_occurrences(data[k])
                         for k in ['candidates', 'pre_bookings', 'bookings', 'conflicts', 'pre_conflicts']})
        return jsonify_data(flash=False, availability=availability, date_range=date_range)

    def _serialize_occurrences(self, data):
        return {dt.isoformat(): reservation_occurrences_schema.dump(data).data for dt, data in data.iteritems()}


class RHRoomFavorites(RHRoomBookingBase):
    def _process_args(self):
        self.room = None
        if 'room_id' in request.view_args:
            self.room = Room.get_one(request.view_args['room_id'])

    def _process_GET(self):
        query = (db.session.query(favorite_room_table.c.room_id)
                 .filter(favorite_room_table.c.user_id == session.user.id))
        favorites = [id_ for id_, in query]
        return jsonify(favorites)

    def _process_PUT(self):
        session.user.favorite_rooms.add(self.room)
        return '', 204

    def _process_DELETE(self):
        session.user.favorite_rooms.discard(self.room)
        return '', 204


class RHUserInfo(RHRoomBookingBase):
    def _process(self):
        # TODO: include acl/egroup-based room ownership
        has_owned_rooms = Room.query.filter(Room.is_active, Room.owner == session.user).has_rows()
        return jsonify(has_owned_rooms=has_owned_rooms)
