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

from datetime import date, datetime, time, timedelta

from flask import jsonify, request, session
from webargs import fields
from webargs.flaskparser import use_args
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import with_total_rows
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.controllers.backend.common import search_room_args
from indico.modules.rb_new.schemas import map_rooms_schema, room_attributes_schema, room_details_schema, rooms_schema
from indico.modules.rb_new.util import get_room_details_availability, search_for_rooms


class RHRooms(RHRoomBookingBase):
    def _process(self):
        rooms = Room.query.filter_by(is_active=True).all()
        return jsonify(room_details_schema.dump(rooms, many=True).data)


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


class RHRoomBase(RHRoomBookingBase):
    def _process_args(self):
        self.room = Room.get_one(request.view_args['room_id'])
        if not self.room.is_active:
            raise NotFound


class RHRoomAvailability(RHRoomBase):
    def _process(self):
        today = date.today()
        start_dt = datetime.combine(today, time(0, 0))
        end_dt = datetime.combine(today + timedelta(days=4), time(23, 59))
        return jsonify(get_room_details_availability(self.room, start_dt, end_dt))


class RHRoomAttributes(RHRoomBase):
    def _process(self):
        return jsonify(room_attributes_schema.dump(self.room.attributes).data)


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
