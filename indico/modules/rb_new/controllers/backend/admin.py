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
from marshmallow import missing, validate
from sqlalchemy.orm import joinedload
from webargs import fields
from webargs.flaskparser import abort, use_args, use_kwargs
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.categories.models.categories import Category
from indico.modules.rb import Room, rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.controllers.backend.rooms import RHRoomsPermissions
from indico.modules.rb_new.operations.admin import (update_room, update_room_attributes, update_room_availability,
                                                    update_room_equipment)
from indico.modules.rb_new.schemas import (admin_equipment_type_schema, admin_locations_schema, bookable_hours_schema,
                                           nonbookable_periods_schema, room_attribute_schema,
                                           room_attribute_values_schema, room_equipment_schema, room_feature_schema,
                                           room_update_schema)
from indico.modules.users.models.users import User
from indico.util.i18n import _
from indico.util.marshmallow import ModelList, Principal, PrincipalList
from indico.web.util import ExpectedError


class RHRoomBookingAdminBase(RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not rb_is_admin(session.user):
            raise Forbidden


class SettingsSchema(mm.Schema):
    admin_principals = PrincipalList(allow_groups=True)
    authorized_principals = PrincipalList(allow_groups=True)
    tileserver_url = fields.String(validate=[
        validate.URL(schemes={'http', 'https'}),
        lambda value: all(x in value for x in ('{x}', '{y}', '{z}'))
    ], allow_none=True)
    booking_limit = fields.Int(validate=[validate.Range(min=1)])
    notifications_enabled = fields.Bool()
    notification_before_days = fields.Int(validate=[validate.Range(min=1, max=30)])
    notification_before_days_weekly = fields.Int(validate=[validate.Range(min=1, max=30)])
    notification_before_days_monthly = fields.Int(validate=[validate.Range(min=1, max=30)])
    end_notifications_enabled = fields.Bool()
    end_notification_daily = fields.Int(validate=[validate.Range(min=1, max=30)])
    end_notification_weekly = fields.Int(validate=[validate.Range(min=1, max=30)])
    end_notification_monthly = fields.Int(validate=[validate.Range(min=1, max=30)])
    excluded_categories = ModelList(Category)


class RHSettings(RHRoomBookingAdminBase):
    def _jsonify_settings(self):
        return SettingsSchema().jsonify(rb_settings.get_all())

    def _process_GET(self):
        return self._jsonify_settings()

    @use_args(SettingsSchema)
    def _process_PATCH(self, args):
        rb_settings.set_multi(args)
        return self._jsonify_settings()


class RHLocations(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('location_id')
        self.location = Location.get_one(id_) if id_ is not None else None

    def _jsonify_one(self, location):
        return jsonify(admin_locations_schema.dump(location, many=False))

    def _jsonify_many(self):
        query = Location.query.options(joinedload('rooms'))
        return jsonify(admin_locations_schema.dump(query.all()))

    def _process_GET(self):
        if self.location:
            return self._jsonify_one(self.location)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        if Room.query.with_parent(self.location).filter_by(is_active=True).has_rows():
            raise ExpectedError(_('Cannot delete location with active rooms'))
        db.session.delete(self.location)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(required=True),
        'room_name_format': fields.String(validate=[
            lambda value: all(x in value for x in ('{building}', '{floor}', '{number}'))
        ], required=True),
        'map_url_template': fields.URL(schemes={'http', 'https'}, allow_none=True, missing=''),
    })
    def _process_POST(self, name, room_name_format, map_url_template):
        self._check_conflict(name)
        loc = Location(name=name, room_name_format=room_name_format, map_url_template=(map_url_template or ''))
        db.session.add(loc)
        db.session.flush()
        return self._jsonify_one(loc), 201

    @use_kwargs({
        'name': fields.String(),
        'room_name_format': fields.String(validate=[
            lambda value: all(x in value for x in ('{building}', '{floor}', '{number}'))
        ]),
        'map_url_template': fields.URL(schemes={'http', 'https'}, allow_none=True),
    })
    def _process_PATCH(self, name=None, room_name_format=None, map_url_template=missing):
        if name is not None:
            self._check_conflict(name)
            self.location.name = name
        if room_name_format is not None:
            self.location.room_name_format = room_name_format
        if map_url_template is not missing:
            self.location.map_url_template = map_url_template or ''
        db.session.flush()
        return self._jsonify_one(self.location)

    def _check_conflict(self, name):
        query = Location.query.filter(db.func.lower(Location.name) == name.lower())
        if self.location:
            query = query.filter(Location.id != self.location.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHFeatures(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('feature_id')
        self.feature = RoomFeature.get_one(id_) if id_ is not None else None

    def _dump_features(self):
        query = RoomFeature.query.order_by(RoomFeature.title)
        return room_feature_schema.dump(query, many=True)

    def _jsonify_one(self, equipment_type):
        return jsonify(room_feature_schema.dump(equipment_type))

    def _jsonify_many(self):
        return jsonify(self._dump_features())

    def _process_GET(self):
        if self.feature:
            return self._jsonify_one(self.feature)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        db.session.delete(self.feature)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2), required=True),
        'title': fields.String(validate=validate.Length(min=2), required=True),
        'icon': fields.String(missing=''),
    })
    def _process_POST(self, name, title, icon):
        self._check_conflict(name)
        feature = RoomFeature(name=name, title=title, icon=icon)
        db.session.add(feature)
        db.session.flush()
        return self._jsonify_one(feature), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'title': fields.String(validate=validate.Length(min=2)),
        'icon': fields.String(),
    })
    def _process_PATCH(self, name=None, title=None, icon=None):
        if name is not None:
            self._check_conflict(name)
            self.feature.name = name
        if title is not None:
            self.feature.title = title
        if icon is not None:
            self.feature.icon = icon
        db.session.flush()
        return self._jsonify_one(self.feature)

    def _check_conflict(self, name):
        query = RoomFeature.query.filter(db.func.lower(RoomFeature.name) == name.lower())
        if self.feature:
            query = query.filter(RoomFeature.id != self.feature.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHEquipmentTypes(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('equipment_type_id')
        self.equipment_type = EquipmentType.get_one(id_) if id_ is not None else None

    def _dump_equipment_types(self):
        query = EquipmentType.query.options(joinedload('features')).order_by(EquipmentType.name)
        return admin_equipment_type_schema.dump(query, many=True)

    def _get_room_counts(self):
        query = (db.session.query(RoomEquipmentAssociation.c.equipment_id, db.func.count())
                 .group_by(RoomEquipmentAssociation.c.equipment_id))
        return dict(query)

    def _jsonify_one(self, equipment_type):
        counts = self._get_room_counts()
        eq = admin_equipment_type_schema.dump(equipment_type)
        eq['num_rooms'] = counts.get(eq['id'], 0)
        return jsonify(eq)

    def _jsonify_many(self):
        counts = self._get_room_counts()
        equipment_types = self._dump_equipment_types()
        for eq in equipment_types:
            eq['num_rooms'] = counts.get(eq['id'], 0)
        return jsonify(equipment_types)

    def _process_GET(self):
        if self.equipment_type:
            return self._jsonify_one(self.equipment_type)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        db.session.delete(self.equipment_type)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2), required=True),
        'features': ModelList(RoomFeature, missing=[])
    })
    def _process_POST(self, name, features):
        self._check_conflict(name)
        equipment_type = EquipmentType(name=name, features=features)
        db.session.add(equipment_type)
        db.session.flush()
        return self._jsonify_one(equipment_type), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'features': ModelList(RoomFeature)
    })
    def _process_PATCH(self, name=None, features=None):
        if name is not None:
            self._check_conflict(name)
            self.equipment_type.name = name
        if features is not None:
            self.equipment_type.features = features
        db.session.flush()
        return self._jsonify_one(self.equipment_type)

    def _check_conflict(self, name):
        query = EquipmentType.query.filter(db.func.lower(EquipmentType.name) == name.lower())
        if self.equipment_type:
            query = query.filter(EquipmentType.id != self.equipment_type.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHAttributes(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('attribute_id')
        self.attribute = RoomAttribute.get_one(id_) if id_ is not None else None

    def _dump_attributes(self):
        query = RoomAttribute.query.order_by(RoomAttribute.title)
        return room_attribute_schema.dump(query, many=True)

    def _get_room_counts(self):
        query = (db.session.query(RoomAttributeAssociation.attribute_id, db.func.count())
                 .group_by(RoomAttributeAssociation.attribute_id))
        return dict(query)

    def _jsonify_one(self, attribute):
        counts = self._get_room_counts()
        attr = room_attribute_schema.dump(attribute)
        attr['num_rooms'] = counts.get(attr['id'], 0)
        return jsonify(attr)

    def _jsonify_many(self):
        counts = self._get_room_counts()
        attributes = self._dump_attributes()
        for attr in attributes:
            attr['num_rooms'] = counts.get(attr['id'], 0)
        return jsonify(attributes)

    def _process_GET(self):
        if self.attribute:
            return self._jsonify_one(self.attribute)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        db.session.delete(self.attribute)
        db.session.flush()
        return '', 204

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2), required=True),
        'title': fields.String(validate=validate.Length(min=2), required=True),
        'hidden': fields.Bool(missing=False),
    })
    def _process_POST(self, name, title, hidden):
        self._check_conflict(name)
        attribute = RoomAttribute(name=name, title=title, is_hidden=hidden)
        db.session.add(attribute)
        db.session.flush()
        return self._jsonify_one(attribute), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'title': fields.String(validate=validate.Length(min=2)),
        'hidden': fields.Bool(),
    })
    def _process_PATCH(self, name=None, title=None, hidden=None):
        if name is not None:
            self._check_conflict(name)
            self.attribute.name = name
        if title is not None:
            self.attribute.title = title
        if hidden is not None:
            self.attribute.is_hidden = hidden
        db.session.flush()
        return self._jsonify_one(self.attribute)

    def _check_conflict(self, name):
        query = RoomAttribute.query.filter(db.func.lower(RoomAttribute.name) == name.lower())
        if self.attribute:
            query = query.filter(RoomAttribute.id != self.attribute.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})


class RHRoomAdminBase(RHRoomBookingAdminBase):
    def _process_args(self):
        self.room = Room.get_one(request.view_args['room_id'])


class RHRoomAttributes(RHRoomAdminBase):
    def _process(self):
        return jsonify(room_attribute_values_schema.dump(self.room.attributes))


class RHUpdateRoomAttributes(RHRoomAdminBase):
    @use_kwargs({'attributes': fields.Nested({'title': fields.Str(),
                                              'value': fields.Str(),
                                              'name': fields.Str()}, many=True)})
    def _process(self, attributes):
        update_room_attributes(self.room, attributes)
        return jsonify(room_attribute_values_schema.dump(self.room.attributes))


class RHRoomAvailability(RHRoomAdminBase):
    def _process(self):
        return jsonify(
            nonbookable_periods=nonbookable_periods_schema.dump(self.room.nonbookable_periods, many=True),
            bookable_hours=bookable_hours_schema.dump(self.room.bookable_hours, many=True)
        )


class RHUpdateRoomAvailability(RHRoomAdminBase):
    @use_args({'bookable_hours': fields.Nested({'start_time': fields.Time(),
                                                'end_time': fields.Time()}, many=True),
               'nonbookable_periods': fields.Nested({'start_dt': fields.Date(),
                                                     'end_dt': fields.Date()}, many=True)})
    def _process(self, args):
        if 'bookable_hours' in args:
            self._check_invalid_times(args)
        update_room_availability(self.room, args)
        return jsonify(
            nonbookable_periods=nonbookable_periods_schema.dump(self.room.nonbookable_periods, many=True),
            bookable_hours=bookable_hours_schema.dump(self.room.bookable_hours, many=True)
        )

    def _check_invalid_times(self, availability):
        if any(bh['start_time'] >= bh['end_time'] for bh in availability['bookable_hours']):
            abort(422, messages={'bookable_hours': [_('Start time should not be later than end time')]})


class RHRoomEquipment(RHRoomAdminBase):
    def _process(self):
        return jsonify(room_equipment_schema.dump(self.room))


class RHUpdateRoomEquipment(RHRoomAdminBase):
    @use_args({
        'available_equipment': fields.List(fields.Int(), required=True)
    })
    def _process(self, args):
        update_room_equipment(self.room, args['available_equipment'])
        return jsonify(room_update_schema.dump(self.room, many=False))


class RHRoom(RHRoomAdminBase):
    def _process(self):
        return jsonify(room_update_schema.dump(self.room))


class RHUpdateRoom(RHRoomAdminBase):
    @use_args({
        'verbose_name': fields.Str(allow_none=True),
        'site': fields.Str(allow_none=True),
        'building': fields.String(validate=lambda x: x is not None),
        'floor': fields.String(validate=lambda x: x is not None),
        'number': fields.String(validate=lambda x: x is not None),
        'longitude': fields.Float(allow_none=True),
        'latitude': fields.Float(allow_none=True),
        'is_reservable': fields.Bool(allow_none=True),
        'reservations_need_confirmation': fields.Bool(allow_none=True),
        'notification_emails': fields.List(fields.Email()),
        'notification_before_days': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
        'notification_before_days_weekly': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
        'notification_before_days_monthly': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
        'notifications_enabled': fields.Bool(),
        'end_notification_daily': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
        'end_notification_weekly': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
        'end_notification_monthly': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
        'end_notifications_enabled': fields.Bool(),
        'booking_limit_days': fields.Int(validate=lambda x: x >= 1, allow_none=True),
        'owner': Principal(validate=lambda x: x is not None, allow_none=True),
        'key_location': fields.Str(),
        'telephone': fields.Str(),
        'capacity': fields.Int(validate=lambda x: x >= 1),
        'division': fields.Str(allow_none=True),
        'surface_area': fields.Int(validate=lambda x: x >= 0, allow_none=True),
        'max_advance_days': fields.Int(validate=lambda x: x >= 1, allow_none=True),
        'comments': fields.Str(),
    })
    def _process(self, args):
        update_room(self.room, args)
        RHRoomsPermissions._jsonify_user_permissions.clear_cached(session.user)
        return jsonify(room_update_schema.dump(self.room, many=False))
