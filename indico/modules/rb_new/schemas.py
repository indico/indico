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

from marshmallow.fields import Nested, String

from indico.core.marshmallow import mm
from indico.modules.rb import Blocking
from indico.modules.rb.models.aspects import Aspect
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.room_attributes import RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room


_room_fields = ('id', 'name', 'capacity', 'building', 'floor', 'number', 'is_public', 'location_name', 'has_vc',
                'has_projector', 'has_webcast_recording', 'large_photo_url', 'full_name', 'comments', 'division',
                'is_reservable', 'is_auto_confirm')


class RoomAttributesSchema(mm.ModelSchema):
    title = String(attribute='attribute.title')

    class Meta:
        model = RoomAttributeAssociation
        fields = ('value', 'title')


class RoomSchema(mm.ModelSchema):
    owner_name = String(attribute='owner.full_name')
    attributes = Nested(RoomAttributesSchema, many=True)

    class Meta:
        model = Room
        fields = _room_fields + ('surface_area', 'latitude', 'longitude', 'telephone', 'key_location',
                                 'max_advance_days', 'owner_name', 'attributes')


class MapRoomSchema(mm.ModelSchema):
    class Meta:
        model = Room
        fields = ('id', 'full_name', 'latitude', 'longitude')


class AspectSchema(mm.ModelSchema):
    class Meta:
        model = Aspect
        fields = ('name', 'top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude',
                  'default_on_startup')


class ReservationSchema(mm.ModelSchema):
    class Meta:
        model = Reservation
        fields = ('booking_reason', 'booked_for_name')


class ReservationOccurrenceSchema(mm.ModelSchema):
    reservation = Nested(ReservationSchema)

    class Meta:
        model = ReservationOccurrence
        fields = ('start_dt', 'end_dt', 'is_valid', 'reservation')


class BlockingSchema(mm.ModelSchema):
    class Meta:
        model = Blocking
        fields = ('reason',)


class NonBookablePeriodSchema(mm.ModelSchema):

    class Meta:
        model = NonBookablePeriod
        fields = ('start_dt', 'end_dt')


class UnbookableHoursSchema(mm.ModelSchema):

    class Meta:
        model = BookableHours
        fields = ('start_time', 'end_time')


rooms_schema = RoomSchema(many=True, only=_room_fields)
room_details_schema = RoomSchema()
map_rooms_schema = MapRoomSchema(many=True)
aspects_schema = AspectSchema(many=True)
reservation_occurrences_schema = ReservationOccurrenceSchema(many=True)
reservation_schema = ReservationSchema()
blocking_schema = BlockingSchema(many=True)
nonbookable_periods_schema = NonBookablePeriodSchema(many=True)
unbookable_hours_schema = UnbookableHoursSchema(many=True)
