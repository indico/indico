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

from operator import itemgetter

from flask import session
from marshmallow import Schema, ValidationError, fields, post_dump, validate, validates_schema
from marshmallow.fields import Boolean, DateTime, Function, Method, Nested, Number, String
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.rb.models.blocked_rooms import BlockedRoom, BlockedRoomState
from indico.modules.rb.models.blocking_principals import BlockingPrincipal
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.map_areas import MapArea
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation, ReservationState
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.modules.users.schemas import UserSchema
from indico.util.i18n import _
from indico.util.marshmallow import NaiveDateTime
from indico.util.string import natural_sort_key


class RoomAttributeValuesSchema(mm.ModelSchema):
    title = String(attribute='attribute.title')

    class Meta:
        model = RoomAttributeAssociation
        fields = ('value', 'title')


class RoomSchema(mm.ModelSchema):
    owner_name = String(attribute='owner.full_name')

    class Meta:
        model = Room
        fields = ('id', 'name', 'capacity', 'building', 'floor', 'number', 'is_public', 'location_name', 'full_name',
                  'comments', 'division', 'is_reservable', 'is_auto_confirm', 'sprite_position', 'surface_area',
                  'latitude', 'longitude', 'telephone', 'key_location', 'max_advance_days', 'owner_name',
                  'available_equipment')


class MapAreaSchema(mm.ModelSchema):
    class Meta:
        model = MapArea
        fields = ('name', 'top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude',
                  'is_default')


class ReservationSchema(mm.ModelSchema):
    class Meta:
        model = Reservation
        fields = ('id', 'booking_reason', 'booked_for_name', 'room_id', 'is_accepted')


class ReservationEventDataSchema(Schema):
    id = Number()
    title = String()
    url = String()
    can_access = Function(lambda event: event.can_access(session.user))


class ReservationUserEventSchema(Schema):
    id = Number()
    title = String()
    url = String()
    start_dt = DateTime()
    end_dt = DateTime()


class ReservationOccurrenceSchema(mm.ModelSchema):
    reservation = Nested(ReservationSchema)
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

    class Meta:
        model = ReservationOccurrence
        fields = ('start_dt', 'end_dt', 'is_valid', 'reservation')


class ReservationDetailsOccurrenceSchema(mm.ModelSchema):
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

    class Meta:
        model = ReservationOccurrence
        fields = ('start_dt', 'end_dt', 'is_valid', 'rejection_reason')


class ReservationEditLogSchema(UserSchema):
    class Meta:
        model = ReservationEditLog
        fields = ('id', 'timestamp', 'info', 'user_name')

    @post_dump(pass_many=True)
    def sort_logs(self, data, many):
        if many:
            data = sorted(data, key=itemgetter('timestamp'), reverse=True)
        return data


class ReservationDetailsSchema(mm.ModelSchema):
    booked_for_user = Nested(UserSchema, only=('id', 'identifier', 'full_name', 'phone', 'email'))
    created_by_user = Nested(UserSchema, only=('id', 'identifier', 'full_name', 'email'))
    edit_logs = Nested(ReservationEditLogSchema, many=True)
    can_accept = Function(lambda booking: booking.can_accept(session.user))
    can_cancel = Function(lambda booking: booking.can_cancel(session.user))
    can_delete = Function(lambda booking: booking.can_delete(session.user))
    can_edit = Function(lambda booking: booking.can_edit(session.user))
    can_reject = Function(lambda booking: booking.can_reject(session.user))
    permissions = Method('_get_permissions')
    state = EnumField(ReservationState)
    is_linked_to_event = Function(lambda booking: booking.event_id is not None)
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

    class Meta:
        model = Reservation
        fields = ('id', 'start_dt', 'end_dt', 'repetition', 'booking_reason', 'created_dt', 'booked_for_user',
                  'room_id', 'created_by_user', 'edit_logs', 'permissions',
                  'is_cancelled', 'is_rejected', 'is_accepted', 'is_pending', 'rejection_reason',
                  'is_linked_to_event', 'state')

    def _get_permissions(self, booking):
        methods = ('can_accept', 'can_cancel', 'can_delete', 'can_edit', 'can_reject')
        admin_permissions = None
        user_permissions = {x: getattr(booking, x)(session.user, allow_admin=False) for x in methods}
        if rb_is_admin(session.user):
            admin_permissions = {x: getattr(booking, x)(session.user) for x in methods}
        return {'user': user_permissions, 'admin': admin_permissions}


class BlockedRoomSchema(mm.ModelSchema):
    room = Nested(RoomSchema, only=('id', 'name', 'sprite_position', 'full_name'))
    state = EnumField(BlockedRoomState)

    class Meta:
        model = BlockedRoom
        fields = ('room', 'state', 'rejection_reason', 'rejected_by')

    @post_dump(pass_many=True)
    def sort_rooms(self, data, many):
        if many:
            data = sorted(data, key=lambda x: natural_sort_key(x['room']['full_name']))
        return data


class BlockingPrincipalSchema(mm.ModelSchema):
    identifier = Function(lambda blocking_principal: blocking_principal.identifier)
    full_name = String()
    provider = String(missing=None)
    email = String(missing=None)
    is_group = Boolean(missing=False)

    class Meta:
        model = BlockingPrincipal
        fields = ('id', 'identifier', 'name', 'is_group', 'email', 'full_name', 'provider')


class BlockingSchema(mm.ModelSchema):
    blocked_rooms = Nested(BlockedRoomSchema, many=True)
    allowed = Nested(BlockingPrincipalSchema, many=True)
    permissions = Method('_get_permissions')
    created_by = Nested(UserSchema, attribute='created_by_user', only='full_name')

    class Meta:
        model = Blocking
        fields = ('id', 'start_date', 'end_date', 'reason', 'blocked_rooms', 'allowed', 'created_by', 'permissions')

    def _get_permissions(self, blocking):
        methods = ('can_delete', 'can_edit')
        admin_permissions = None
        user_permissions = {x: getattr(blocking, x)(session.user, allow_admin=False) for x in methods}
        if rb_is_admin(session.user):
            admin_permissions = {x: getattr(blocking, x)(session.user) for x in methods}
        return {'user': user_permissions, 'admin': admin_permissions}


class NonBookablePeriodSchema(mm.ModelSchema):
    class Meta:
        model = NonBookablePeriod
        fields = ('start_dt', 'end_dt')


class BookableHoursSchema(mm.ModelSchema):
    class Meta:
        model = BookableHours
        fields = ('start_time', 'end_time')


class LocationsSchema(mm.ModelSchema):
    rooms = Nested(RoomSchema, many=True, only=('id', 'name', 'full_name', 'sprite_position'))

    class Meta:
        model = Location
        fields = ('id', 'name', 'rooms')


class AdminLocationsSchema(LocationsSchema):
    rooms = Nested(RoomSchema, only=LocationsSchema._declared_fields['rooms'].only + ('owner_name', 'comments'),
                   many=True)

    @post_dump
    def sort_rooms(self, location):
        location['rooms'] = sorted(location['rooms'], key=lambda x: natural_sort_key(x['full_name']))
        return location


class RBUserSchema(UserSchema):
    has_owned_rooms = mm.Method('has_managed_rooms')
    is_rb_admin = mm.Function(lambda user: rb_is_admin(user))
    favorite_users = Nested(UserSchema, many=True)

    class Meta:
        fields = UserSchema.Meta.fields + ('has_owned_rooms', 'favorite_users', 'is_admin', 'is_rb_admin', 'identifier',
                                           'full_name')

    def has_managed_rooms(self, user):
        from indico.modules.rb_new.operations.rooms import has_managed_rooms
        return has_managed_rooms(user)


class CreateBookingSchema(Schema):
    start_dt = fields.DateTime(required=True)
    end_dt = fields.DateTime(required=True)
    repeat_frequency = EnumField(RepeatFrequency, required=True)
    repeat_interval = fields.Int(missing=0, validate=lambda x: x >= 0)
    room_id = fields.Int(required=True)
    user_id = fields.Int()
    event_id = fields.Int()
    booking_reason = fields.String(load_from='reason', validate=validate.Length(min=3))
    is_prebooking = fields.Bool(missing=False)

    class Meta:
        strict = True

    @validates_schema
    def validate_dts(self, data):
        if data['start_dt'] >= data['end_dt']:
            raise ValidationError(_('Booking cannot end before it starts'))


class RoomFeatureSchema(mm.ModelSchema):
    class Meta:
        model = RoomFeature
        fields = ('id', 'name', 'title', 'icon')


class EquipmentTypeSchema(mm.ModelSchema):
    features = Nested(RoomFeatureSchema, many=True)

    class Meta:
        model = EquipmentType
        fields = ('id', 'name', 'features')


class AdminEquipmentTypeSchema(mm.ModelSchema):
    class Meta:
        model = EquipmentType
        fields = ('id', 'name', 'features')


class RoomAttributeSchema(mm.ModelSchema):
    hidden = Boolean(attribute='is_hidden')

    class Meta:
        model = RoomAttribute
        fields = ('id', 'name', 'title', 'hidden')


rb_user_schema = RBUserSchema()
rooms_schema = RoomSchema(many=True)
room_attribute_values_schema = RoomAttributeValuesSchema(many=True)
map_areas_schema = MapAreaSchema(many=True)
reservation_occurrences_schema = ReservationOccurrenceSchema(many=True)
reservation_schema = ReservationSchema()
reservation_details_schema = ReservationDetailsSchema()
reservation_event_data_schema = ReservationEventDataSchema()
reservation_user_event_schema = ReservationUserEventSchema(many=True)
reservation_details_occurrences_schema = ReservationDetailsOccurrenceSchema(many=True)
blockings_schema = BlockingSchema(many=True)
simple_blockings_schema = BlockingSchema(many=True, only=('id', 'reason'))
nonbookable_periods_schema = NonBookablePeriodSchema(many=True)
bookable_hours_schema = BookableHoursSchema()
locations_schema = LocationsSchema(many=True)
admin_locations_schema = AdminLocationsSchema(many=True)
create_booking_args = CreateBookingSchema()
equipment_type_schema = EquipmentTypeSchema()
admin_equipment_type_schema = AdminEquipmentTypeSchema()
room_feature_schema = RoomFeatureSchema()
room_attribute_schema = RoomAttributeSchema()
