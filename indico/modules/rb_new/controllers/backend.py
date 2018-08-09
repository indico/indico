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
from operator import itemgetter

from flask import jsonify, request, session
from marshmallow_enum import EnumField
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import with_total_rows
from indico.core.errors import NoReportError
from indico.modules.groups import GroupProxy
from indico.modules.rb import Location, rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.favorites import favorite_room_table
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb_new.schemas import (aspects_schema, blockings_schema, locations_schema, map_rooms_schema,
                                           reservation_schema, room_details_schema, rooms_schema)
from indico.modules.rb_new.util import (approve_or_request_blocking, create_blocking, get_buildings,
                                        get_equipment_types, get_existing_room_occurrences, get_room_blockings,
                                        get_room_calendar, get_rooms_availability, get_suggestions,
                                        group_by_occurrence_date, has_managed_rooms, search_for_rooms,
                                        serialize_blockings, serialize_nonbookable_periods, serialize_occurrences,
                                        serialize_unbookable_hours)
from indico.modules.users.models.users import User
from indico.util.date_time import iterdays
from indico.util.i18n import _
from indico.web.util import ExpectedError, jsonify_data


NUM_SUGGESTIONS = 5

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


def _serialize_availability(availability):
    for data in availability.viewvalues():
        data['room'] = rooms_schema.dump(data['room'], many=False).data
        data['blockings'] = serialize_blockings(data['blockings'])
        data['nonbookable_periods'] = serialize_nonbookable_periods(data['nonbookable_periods'])
        data['unbookable_hours'] = serialize_unbookable_hours(data['unbookable_hours'])
        data.update({k: serialize_occurrences(data[k]) if k in data else []
                     for k in ['candidates', 'pre_bookings', 'bookings', 'conflicts', 'pre_conflicts']})
    return availability


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
        start_dt = datetime.combine(date.today(), time(0, 0))
        end_dt = datetime.combine(start_dt + timedelta(days=4), time(23, 59))
        last_bookings = group_by_occurrence_date(get_existing_room_occurrences(self.room, start_dt, end_dt,
                                                                               RepeatFrequency.DAY, 1,
                                                                               only_accepted=True))
        range_bookings = {day.date(): last_bookings.get(day.date()) for day in iterdays(start_dt, end_dt)}
        bookings = [
            {
                'availability': {'usage': bookings or []},
                'label': dt,
                'conflictIndicator': False,
                'id': dt
            } for dt, bookings in serialize_occurrences(range_bookings).iteritems()
        ]

        room_details['bookings'] = sorted(bookings, key=itemgetter('id'))
        return jsonify(room_details)


class RHAspects(RHRoomBookingBase):
    def _process(self):
        if not Location.query.has_rows():
            return jsonify([])

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
    @use_args(dict(search_room_args, **{
        'limit': fields.Int(missing=None),
        'additional_room_ids': fields.List(fields.Int())
    }))
    def _process(self, args):
        query = search_for_rooms(args, only_available=True)
        if 'limit' in args:
            query = query.limit(args.pop('limit'))

        rooms = query.all()
        if 'additional_room_ids' in args:
            rooms.extend(Room.query.filter(Room.is_active, Room.id.in_(args.pop('additional_room_ids'))))

        date_range, availability = get_rooms_availability(rooms, args['start_dt'], args['end_dt'],
                                                          args['repeat_frequency'], args['repeat_interval'],
                                                          flexibility=0)
        date_range = [dt.isoformat() for dt in date_range]

        for data in availability.viewvalues():
            # add additional helpful attributes
            data.update({
                'num_days_available': len(date_range) - len(data['conflicts']),
                'all_days_available': not data['conflicts']
            })

        return jsonify_data(flash=False,
                            availability=_serialize_availability(availability),
                            date_range=date_range)


class RHCalendar(RHRoomBookingBase):
    @use_kwargs({
        'start_dt': fields.DateTime(),
        'end_dt': fields.DateTime(),
    })
    def _process(self, start_dt, end_dt):
        calendar = get_room_calendar(start_dt, end_dt)
        return jsonify_data(flash=False, calendar=_serialize_availability(calendar).values())


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
        return jsonify(has_owned_rooms=has_managed_rooms(session.user))


class RHCreateBooking(RHRoomBookingBase):
    def _validate_room_booking_limit(self, start_dt, end_dt, booking_limit_days):
        day_start_dt = datetime.combine(start_dt.date(), time())
        day_end_dt = datetime.combine(end_dt.date(), time(23, 59))
        selected_period_days = (day_end_dt - day_start_dt).days
        return selected_period_days <= booking_limit_days

    @use_args({
        'start_dt': fields.DateTime(required=True),
        'end_dt': fields.DateTime(required=True),
        'repeat_frequency': EnumField(RepeatFrequency, required=True),
        'repeat_interval': fields.Int(missing=0),
        'room_id': fields.Int(required=True),
        'user_id': fields.Int(),
        'booking_reason': fields.String(load_from='reason', validate=validate.Length(min=3)),
        'is_prebooking': fields.Bool(missing=False)
    })
    def _process(self, args):
        room = Room.get_one(args.pop('room_id'))
        user_id = args.pop('user_id', None)
        booked_for = User.get_one(user_id) if user_id else session.user
        is_prebooking = args.pop('is_prebooking')

        # Check that the booking is not longer than allowed
        booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
        if not self._validate_room_booking_limit(args['start_dt'], args['end_dt'], booking_limit_days):
            msg = (_('Bookings for the room "{}" may not be longer than {} days')
                   .format(room.name, booking_limit_days))
            return jsonify(success=False, msg=msg)

        try:
            resv = Reservation.create_from_data(room, dict(args, booked_for_user=booked_for), session.user,
                                                prebook=is_prebooking)
            db.session.flush()
        except NoReportError as e:
            db.session.rollback()
            raise ExpectedError(unicode(e))
        return jsonify(booking=reservation_schema.dump(resv).data)


class RHRoomSuggestions(RHRoomBookingBase):
    @use_args(search_room_args)
    def _process(self, args):
        return jsonify([dict(suggestion, room=rooms_schema.dump(suggestion['room'], many=False).data)
                        for suggestion in get_suggestions(args, limit=NUM_SUGGESTIONS)])


class RHRoomBlockings(RHRoomBookingBase):
    @use_kwargs({
        'start_dt': fields.Date(),
        'end_dt': fields.Date(),
        'blockings_in_my_rooms': fields.Bool(),
        'my_blockings': fields.Bool()
    })
    def _process(self, start_dt, end_dt, blockings_in_my_rooms, my_blockings):
        filters = {'start_dt': start_dt, 'end_dt': end_dt,
                   'created_by': session.user if my_blockings else None,
                   'in_rooms_owned_by': session.user if blockings_in_my_rooms else None}
        blockings = get_room_blockings(**filters)
        return jsonify(blockings_schema.dump(blockings).data)


class RHLocations(RHRoomBookingBase):
    def _process(self):
        locations = Location.query.all()
        return jsonify(locations_schema.dump(locations).data)


class RHCreateRoomBlocking(RHRoomBookingBase):
    @use_args({
        'room_ids': fields.List(fields.Int(), missing=[]),
        'start_date': fields.Date(),
        'end_date': fields.Date(),
        'reason': fields.Str(),
        'allowed_principals': fields.List(fields.Dict(), missing=[])
    })
    def _process(self, args):
        rooms = Room.query.filter(Room.id.in_(args['room_ids'])).all()
        allowed_principals = []
        for obj in args['allowed_principals']:
            if obj.get('is_group'):
                allowed_principals.extend(GroupProxy.search(obj['id'], exact=True))
            else:
                allowed_principals.append(User.query.filter(User.id == obj['id']).one())
        blocking = create_blocking(rooms, args['start_date'], args['end_date'], args['reason'],
                                   allowed_principals)
        approve_or_request_blocking(blocking)
        return jsonify_data(flash=False)
