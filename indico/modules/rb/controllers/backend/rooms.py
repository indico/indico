# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import date, datetime, time, timedelta
from io import BytesIO

from flask import jsonify, request, session
from sqlalchemy.orm import subqueryload
from webargs import fields
from werkzeug.exceptions import NotFound, UnprocessableEntity

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.backend.common import search_room_args
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.operations.blockings import filter_blocked_rooms, get_blockings_with_rooms
from indico.modules.rb.operations.bookings import check_room_available, get_room_details_availability
from indico.modules.rb.operations.rooms import get_room_statistics, search_for_rooms
from indico.modules.rb.schemas import room_attribute_values_schema, rooms_schema
from indico.modules.rb.util import rb_is_admin
from indico.util.caching import memoize_redis
from indico.util.marshmallow import NaiveDateTime
from indico.util.string import natural_sort_key
from indico.web.args import use_args, use_kwargs
from indico.web.flask.util import send_file


class RHRooms(RHRoomBookingBase):
    def _process(self):
        rooms = (Room.query
                 .filter_by(is_deleted=False)
                 .options(subqueryload('available_equipment').load_only('id'))
                 .all())
        return jsonify(rooms_schema.dump(rooms))


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
        'admin_override_enabled': fields.Bool(missing=False)
    }))
    def _process(self, args):
        filter_availability = all(x in args for x in ('start_dt', 'end_dt', 'repeat_frequency', 'repeat_interval'))
        only_unavailable = args.pop('unavailable')
        admin_override_enabled = args.pop('admin_override_enabled')
        if not filter_availability:
            availability = None
            if only_unavailable:
                raise UnprocessableEntity('Required data to filter by availability is not present')
        else:
            availability = not only_unavailable
        search_query = search_for_rooms(args, allow_admin=admin_override_enabled, availability=availability)
        rooms = [(id_, room_name) for id_, room_name, in search_query.with_entities(Room.id, Room.full_name)]

        # We can't filter by blocking's acl in the search_query, so we need to adjust the results
        rooms = self._adjust_blockings(rooms, args, availability)
        room_ids = [room[0] for room in rooms]
        if filter_availability:
            room_ids_without_availability_filter = [
                id_ for id_, in search_for_rooms(args, allow_admin=admin_override_enabled).with_entities(Room.id)
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

    def _adjust_blockings(self, rooms, filters, availability):
        if availability is None:
            return rooms
        blocked_rooms = get_blockings_with_rooms(filters['start_dt'], filters['end_dt'])
        nonoverridable_blocked_rooms = filter_blocked_rooms(blocked_rooms, nonoverridable_only=True)
        if availability:
            # Remove nonoverridable blockings from available rooms
            nonoverridable_blocked_rooms_ids = [room.room_id for room in nonoverridable_blocked_rooms]
            rooms = [room for room in rooms if room[0] not in nonoverridable_blocked_rooms_ids]
        else:
            # Add nonoverridable blockings to unavailable rooms and re-sort results
            rooms_ids = [room[0] for room in rooms]
            missing_rooms = [(room.room_id, room.room.full_name) for room in nonoverridable_blocked_rooms
                             if room.room_id not in rooms_ids]
            if filters.get('favorite'):
                favorites = {r.id for r in session.user.favorite_rooms if not r.is_deleted}
                missing_rooms = [(room_id, room_name) for room_id, room_name in missing_rooms
                                 if room_id in favorites]
            rooms = sorted(rooms + missing_rooms, key=lambda room: natural_sort_key(room[1]))
        return rooms


class RHRoomBase(RHRoomBookingBase):
    def _process_args(self):
        self.room = Room.get_or_404(request.view_args['room_id'], is_deleted=False)


class RHRoom(RHRoomBase):
    def _process(self):
        return jsonify(rooms_schema.dump(self.room, many=False))


class RHRoomPermissions(RHRoomBase):
    def _get_permissions(self, allow_admin):
        return {
            'book': self.room.can_book(session.user, allow_admin=allow_admin),
            'prebook': self.room.can_prebook(session.user, allow_admin=allow_admin),
            'override': self.room.can_override(session.user, allow_admin=allow_admin),
            'moderate': self.room.can_moderate(session.user, allow_admin=allow_admin),
            'manage': self.room.can_manage(session.user, allow_admin=allow_admin),
        }

    def _process(self):
        return jsonify(user=self._get_permissions(allow_admin=False),
                       admin=(self._get_permissions(allow_admin=True) if rb_is_admin(session.user) else None))


class RHRoomAvailability(RHRoomBase):
    def _process(self):
        today = date.today()
        start_dt = datetime.combine(today, time(0, 0))
        end_dt = datetime.combine(today + timedelta(days=4), time(23, 59))
        return jsonify(get_room_details_availability(self.room, start_dt, end_dt))


class RHRoomAttributes(RHRoomBase):
    def _process(self):
        attributes = self.room.attributes.filter(RoomAttributeAssociation.attribute.has(~RoomAttribute.is_hidden)).all()
        return jsonify(room_attribute_values_schema.dump(attributes))


class RHRoomStats(RHRoomBase):
    def _process(self):
        return jsonify(get_room_statistics(self.room))


class RHRoomFavorites(RHRoomBookingBase):
    def _process_args(self):
        self.room = None
        if 'room_id' in request.view_args:
            self.room = Room.get_or_404(request.view_args['room_id'])

    def _process_GET(self):
        query = (db.session.query(favorite_room_table.c.room_id)
                 .filter(favorite_room_table.c.user_id == session.user.id)
                 .join(Room)
                 .filter(~Room.is_deleted))
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


class RHRoomPhoto(RHRoomBase):
    def _process(self):
        if not self.room.has_photo:
            raise NotFound
        return send_file('room.jpg', BytesIO(self.room.photo.data), 'image/jpeg')
