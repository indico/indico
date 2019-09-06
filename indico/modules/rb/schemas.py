# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from operator import itemgetter

from flask import session
from marshmallow import ValidationError, fields, post_dump, validate, validates_schema
from marshmallow.fields import Boolean, DateTime, Function, Method, Nested, Number, Pluck, String
from marshmallow_enum import EnumField

from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.marshmallow import mm
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.rb.models.blocked_rooms import BlockedRoom, BlockedRoomState
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.map_areas import MapArea
from indico.modules.rb.models.principals import RoomPrincipal
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatFrequency, Reservation, ReservationLink, ReservationState
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.modules.users.schemas import UserSchema
from indico.util.i18n import _
from indico.util.marshmallow import NaiveDateTime, Principal, PrincipalList, PrincipalPermissionList
from indico.util.string import natural_sort_key


class RoomAttributeValuesSchema(mm.ModelSchema):
    title = String(attribute='attribute.title')
    name = String(attribute='attribute.name')

    class Meta:
        model = RoomAttributeAssociation
        fields = ('value', 'title', 'name')


class AttributesSchema(mm.ModelSchema):
    class Meta:
        model = RoomAttribute
        fields = ('name', 'title', 'is_required', 'is_hidden')


class RoomSchema(mm.ModelSchema):
    owner_name = String(attribute='owner.full_name')

    class Meta:
        model = Room
        fields = ('id', 'name', 'capacity', 'building', 'floor', 'number', 'is_public', 'location_name', 'full_name',
                  'comments', 'division', 'is_reservable', 'reservations_need_confirmation', 'sprite_position',
                  'surface_area', 'latitude', 'longitude', 'telephone', 'key_location', 'max_advance_days',
                  'owner_name', 'available_equipment', 'has_photo', 'verbose_name')


class AdminRoomSchema(mm.ModelSchema):
    class Meta:
        modal = Room
        fields = ('id', 'location_id', 'name', 'full_name', 'sprite_position', 'owner_name', 'comments')


class RoomUpdateSchema(RoomSchema):
    owner = Principal()
    acl_entries = PrincipalPermissionList(RoomPrincipal)
    protection_mode = EnumField(ProtectionMode)

    class Meta(RoomSchema.Meta):
        fields = RoomSchema.Meta.fields + ('notification_before_days', 'notification_before_days_weekly', 'owner',
                                           'notification_before_days_monthly', 'notifications_enabled',
                                           'end_notification_daily', 'end_notification_weekly',
                                           'end_notification_monthly', 'end_notifications_enabled',
                                           'verbose_name', 'site', 'notification_emails', 'booking_limit_days',
                                           'acl_entries', 'protection_mode')


class RoomUpdateArgsSchema(mm.Schema):
    verbose_name = fields.String(allow_none=True)
    site = fields.String(allow_none=True)
    building = fields.String(validate=lambda x: x is not None)
    floor = fields.String(validate=lambda x: x is not None)
    number = fields.String(validate=lambda x: x is not None)
    longitude = fields.Float(allow_none=True)
    latitude = fields.Float(allow_none=True)
    is_reservable = fields.Boolean(allow_none=True)
    reservations_need_confirmation = fields.Boolean(allow_none=True)
    notification_emails = fields.List(fields.Email())
    notification_before_days = fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True)
    notification_before_days_weekly = fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True)
    notification_before_days_monthly = fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True)
    notifications_enabled = fields.Boolean()
    end_notification_daily = fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True)
    end_notification_weekly = fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True)
    end_notification_monthly = fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True)
    end_notifications_enabled = fields.Boolean()
    booking_limit_days = fields.Int(validate=lambda x: x >= 1, allow_none=True)
    owner = Principal(validate=lambda x: x is not None, allow_none=True)
    key_location = fields.String()
    telephone = fields.String()
    capacity = fields.Int(validate=lambda x: x >= 1)
    division = fields.String(allow_none=True)
    surface_area = fields.Int(validate=lambda x: x >= 0, allow_none=True)
    max_advance_days = fields.Int(validate=lambda x: x >= 1, allow_none=True)
    comments = fields.String()
    acl_entries = PrincipalPermissionList(RoomPrincipal)
    protection_mode = EnumField(ProtectionMode)


class RoomEquipmentSchema(mm.ModelSchema):
    class Meta:
        model = Room
        fields = ('available_equipment',)


class MapAreaSchema(mm.ModelSchema):
    class Meta:
        model = MapArea
        fields = ('name', 'top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude',
                  'is_default', 'id')


class ReservationSchema(mm.ModelSchema):
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

    class Meta:
        model = Reservation
        fields = ('id', 'booking_reason', 'booked_for_name', 'room_id', 'is_accepted', 'start_dt', 'end_dt')


class ReservationLinkedObjectDataSchema(mm.Schema):
    id = Number()
    title = Method('_get_title')
    event_title = Function(lambda obj: obj.event.title)
    event_url = Function(lambda obj: obj.event.url)
    own_room_id = Number()
    own_room_name = Function(lambda obj: (obj.own_room.name if obj.own_room else obj.own_room_name) or None)

    def _get_title(self, obj):
        if isinstance(obj, SessionBlock):
            return obj.full_title
        return obj.title


class ReservationUserEventSchema(mm.Schema):
    id = Number()
    title = String()
    url = String()
    start_dt = DateTime()
    end_dt = DateTime()


class ReservationOccurrenceSchema(mm.ModelSchema):
    reservation = Nested(ReservationSchema)
    state = EnumField(ReservationState)
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

    class Meta:
        model = ReservationOccurrence
        fields = ('start_dt', 'end_dt', 'is_valid', 'reservation', 'rejection_reason', 'state')


class ReservationOccurrenceSchemaWithPermissions(ReservationOccurrenceSchema):
    permissions = Method('_get_permissions')

    class Meta:
        fields = ReservationOccurrenceSchema.Meta.fields + ('permissions',)

    def _get_permissions(self, occurrence):
        methods = ('can_cancel', 'can_reject')
        admin_permissions = None
        user_permissions = {x: getattr(occurrence, x)(session.user, allow_admin=False) for x in methods}
        if rb_is_admin(session.user):
            admin_permissions = {x: getattr(occurrence, x)(session.user) for x in methods}
        return {'user': user_permissions, 'admin': admin_permissions}


class ReservationConcurrentOccurrenceSchema(ReservationOccurrenceSchema):
    reservations = Nested(ReservationSchema, many=True)

    class Meta:
        fields = ReservationOccurrenceSchema.Meta.fields + ('reservations',)
        exclude = ('reservation',)


class ReservationEditLogSchema(UserSchema):
    class Meta:
        model = ReservationEditLog
        fields = ('id', 'timestamp', 'info', 'user_name')

    @post_dump(pass_many=True)
    def sort_logs(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=itemgetter('timestamp'), reverse=True)
        return data


class ReservationLinkSchema(mm.ModelSchema):
    type = EnumField(LinkType, attribute='link_type')
    id = Function(lambda link: link.object.id)

    class Meta:
        model = ReservationLink
        fields = ('type', 'id')


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
    is_linked_to_object = Function(lambda booking: booking.link is not None)
    link = Nested(ReservationLinkSchema)
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

    class Meta:
        model = Reservation
        fields = ('id', 'start_dt', 'end_dt', 'repetition', 'booking_reason', 'created_dt', 'booked_for_user',
                  'room_id', 'created_by_user', 'edit_logs', 'permissions',
                  'is_cancelled', 'is_rejected', 'is_accepted', 'is_pending', 'rejection_reason',
                  'is_linked_to_object', 'link', 'state')

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
    def sort_rooms(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda x: natural_sort_key(x['room']['full_name']))
        return data


class BlockingSchema(mm.ModelSchema):
    blocked_rooms = Nested(BlockedRoomSchema, many=True)
    allowed = PrincipalList()
    permissions = Method('_get_permissions')
    created_by = Pluck(UserSchema, 'full_name', attribute='created_by_user')

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
    start_dt = NaiveDateTime()
    end_dt = NaiveDateTime()

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


class AdminLocationsSchema(mm.ModelSchema):
    can_delete = Function(lambda loc: not loc.rooms)

    class Meta:
        model = Location
        fields = ('id', 'name', 'can_delete', 'map_url_template', 'room_name_format')


class RBUserSchema(UserSchema):
    has_owned_rooms = mm.Method('has_managed_rooms')
    is_rb_admin = mm.Function(lambda user: rb_is_admin(user))

    class Meta:
        fields = UserSchema.Meta.fields + ('has_owned_rooms', 'is_admin', 'is_rb_admin', 'identifier', 'full_name')

    def has_managed_rooms(self, user):
        from indico.modules.rb.operations.rooms import has_managed_rooms
        return has_managed_rooms(user)


class CreateBookingSchema(mm.Schema):
    start_dt = fields.DateTime(required=True)
    end_dt = fields.DateTime(required=True)
    repeat_frequency = EnumField(RepeatFrequency, required=True)
    repeat_interval = fields.Int(missing=0, validate=lambda x: x >= 0)
    room_id = fields.Int(required=True)
    booked_for_user = Principal(data_key='user', allow_external_users=True)
    booking_reason = fields.String(data_key='reason', validate=validate.Length(min=3), required=True)
    is_prebooking = fields.Bool(missing=False)
    link_type = EnumField(LinkType)
    link_id = fields.Int()
    link_back = fields.Bool(missing=False)
    admin_override_enabled = fields.Bool(missing=False)

    @validates_schema(skip_on_field_errors=True)
    def validate_dts(self, data):
        if data['start_dt'] >= data['end_dt']:
            raise ValidationError(_('Booking cannot end before it starts'))


class RoomFeatureSchema(mm.ModelSchema):
    class Meta:
        model = RoomFeature
        fields = ('id', 'name', 'title', 'icon')


class EquipmentTypeSchema(mm.ModelSchema):
    features = Nested(RoomFeatureSchema, many=True)
    used = Function(lambda eq, ctx: eq.id in ctx['used_ids'])

    class Meta:
        model = EquipmentType
        fields = ('id', 'name', 'features', 'used')


class AdminEquipmentTypeSchema(mm.ModelSchema):
    class Meta:
        model = EquipmentType
        fields = ('id', 'name', 'features')


class RoomAttributeSchema(mm.ModelSchema):
    hidden = Boolean(attribute='is_hidden')

    class Meta:
        model = RoomAttribute
        fields = ('id', 'name', 'title', 'hidden')


attributes_schema = AttributesSchema(many=True)
rb_user_schema = RBUserSchema()
rooms_schema = RoomSchema(many=True)
room_attribute_values_schema = RoomAttributeValuesSchema(many=True)
room_update_schema = RoomUpdateSchema()
room_update_args_schema = RoomUpdateArgsSchema()
room_equipment_schema = RoomEquipmentSchema()
map_areas_schema = MapAreaSchema(many=True)
reservation_occurrences_schema = ReservationOccurrenceSchema(many=True)
reservation_occurrences_schema_with_permissions = ReservationOccurrenceSchemaWithPermissions(many=True)
concurrent_pre_bookings_schema = ReservationConcurrentOccurrenceSchema(many=True)
reservation_schema = ReservationSchema()
reservation_details_schema = ReservationDetailsSchema()
reservation_linked_object_data_schema = ReservationLinkedObjectDataSchema()
reservation_user_event_schema = ReservationUserEventSchema(many=True)
blockings_schema = BlockingSchema(many=True)
simple_blockings_schema = BlockingSchema(many=True, only=('id', 'reason'))
nonbookable_periods_schema = NonBookablePeriodSchema(many=True)
bookable_hours_schema = BookableHoursSchema()
locations_schema = LocationsSchema(many=True)
admin_locations_schema = AdminLocationsSchema(many=True)
create_booking_args = CreateBookingSchema()
admin_equipment_type_schema = AdminEquipmentTypeSchema()
room_feature_schema = RoomFeatureSchema()
room_attribute_schema = RoomAttributeSchema()
