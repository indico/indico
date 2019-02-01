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
from sqlalchemy.orm import subqueryload
from webargs import fields
from webargs.flaskparser import use_args, use_kwargs
from werkzeug.exceptions import NotFound, UnprocessableEntity

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.controllers.backend.common import search_room_args
from indico.modules.rb_new.operations.bookings import check_room_available, get_room_details_availability
from indico.modules.rb_new.operations.rooms import get_room_statistics, search_for_rooms
from indico.modules.rb_new.schemas import room_attribute_values_schema, rooms_schema
from indico.util.caching import memoize_redis
from indico.util.marshmallow import NaiveDateTime


class RHRooms(RHRoomBookingBase):
    def _process(self):
        rooms = (Room.query
                 .filter_by(is_active=True)
                 .options(subqueryload('available_equipment').load_only('id'))
                 .all())
        return jsonify(rooms_schema.dump(rooms).data)


class RHRoomsPermissions(RHRoomBookingBase):
    @staticmethod
    @memoize_redis(900)
    def _jsonify_user_permissions(user):
        permissions = Room.get_permissions_for_user(user, allow_admin=False)
        return jsonify(user=permissions, admin=(Room.get_permissions_for_user(user) if rb_is_admin(user) else None))

    def _process(self):
        return self._jsonify_user_permissions(session.user)


class RHSearchRooms(RHRoomBookingBase):
    @use_args(dict(search_room_args, **{
        'unavailable': fields.Bool(missing=False),
        'is_admin': fields.Bool()
    }))
    def _process(self, args):
        filter_availability = all(x in args for x in ('start_dt', 'end_dt', 'repeat_frequency', 'repeat_interval'))
        only_unavailable = args.pop('unavailable')
        is_admin_override = args.pop('is_admin')
        if not filter_availability:
            availability = None
            if only_unavailable:
                raise UnprocessableEntity('Required data to filter by availability is not present')
        else:
            availability = not only_unavailable

        search_query = search_for_rooms(args, is_admin_override, availability=availability)
        room_ids = [id_ for id_, in search_query.with_entities(Room.id)]
        if filter_availability:
            room_ids_without_availability_filter = [
                id_ for id_, in search_for_rooms(args, is_admin_override).with_entities(Room.id)
            ]
        else:
            room_ids_without_availability_filter = room_ids
        return jsonify(rooms=room_ids, rooms_without_availability_filter=room_ids_without_availability_filter,
                       total=len(room_ids_without_availability_filter), availability_days=self._get_date_range(args))

    def _get_date_range(self, filters):
        try:
            start_dt, end_dt = filters['start_dt'], filters['end_dt']
            repetition = filters['repeat_frequency'], filters['repeat_interval']
        except KeyError:
            return None
        return [dt.date().isoformat() for dt in ReservationOccurrence.iter_start_time(start_dt, end_dt, repetition)]


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
        return jsonify(room_attribute_values_schema.dump(self.room.attributes).data)


class RHRoomStats(RHRoomBase):
    def _process(self):
        return jsonify(get_room_statistics(self.room))


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


class RHCheckRoomAvailable(RHRoomBase):
    @use_kwargs({
        'start_dt': NaiveDateTime(),
        'end_dt': NaiveDateTime(),
    })
    def _process(self, start_dt, end_dt):
        return jsonify(check_room_available(self.room, start_dt, end_dt))
