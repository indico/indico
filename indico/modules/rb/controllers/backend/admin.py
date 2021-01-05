# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from io import BytesIO

from flask import jsonify, request, session
from marshmallow import missing
from PIL import Image
from sqlalchemy.orm import joinedload
from webargs import fields
from webargs.flaskparser import abort
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.core.errors import UserValueError
from indico.modules.rb import logger, rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.backend.rooms import RHRoomsPermissions
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.map_areas import MapArea
from indico.modules.rb.models.photos import Photo
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.operations.admin import (create_area, delete_areas, update_area, update_room,
                                                update_room_attributes, update_room_availability, update_room_equipment)
from indico.modules.rb.operations.rooms import has_managed_rooms
from indico.modules.rb.schemas import (AdminRoomSchema, EquipmentTypeArgs, FeatureArgs, LocationArgs, RoomAttributeArgs,
                                       RoomAttributeValuesSchema, RoomUpdateArgsSchema, SettingsSchema,
                                       admin_equipment_type_schema, admin_locations_schema, bookable_hours_schema,
                                       map_areas_schema, nonbookable_periods_schema, room_attribute_schema,
                                       room_equipment_schema, room_feature_schema, room_update_schema)
from indico.modules.rb.util import (build_rooms_spritesheet, get_resized_room_photo, rb_is_admin,
                                    remove_room_spritesheet_photo)
from indico.util.i18n import _
from indico.web.args import use_args, use_kwargs, use_rh_kwargs
from indico.web.flask.util import send_file
from indico.web.util import ExpectedError


class RHRoomBookingAdminBase(RHRoomBookingBase):
    def _skip_admin_check(self):
        return False

    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not rb_is_admin(session.user) and not self._skip_admin_check():
            raise Forbidden


class RHSettings(RHRoomBookingAdminBase):
    def _jsonify_settings(self):
        return SettingsSchema().jsonify(rb_settings.get_all())

    def _process_GET(self):
        return self._jsonify_settings()

    @use_args(SettingsSchema, partial=True)
    def _process_PATCH(self, args):
        rb_settings.set_multi(args)
        return self._jsonify_settings()


class RHLocations(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('location_id')
        self.location = Location.get_or_404(id_, is_deleted=False) if id_ is not None else None

    def _jsonify_one(self, location):
        return jsonify(admin_locations_schema.dump(location, many=False))

    def _jsonify_many(self):
        query = Location.query.filter_by(is_deleted=False)
        return jsonify(admin_locations_schema.dump(query.all()))

    def _process_GET(self):
        if self.location:
            return self._jsonify_one(self.location)
        else:
            return self._jsonify_many()

    def _process_DELETE(self):
        # XXX: we could safely allow deleting any locations regardless of whether there
        # are rooms now that we soft-delete them. but it's probably safer to disallow
        # deletion of locations with rooms, simply to prevent accidental deletions.
        if self.location.rooms:
            raise ExpectedError(_('Cannot delete location with active rooms'))
        self.location.is_deleted = True
        logger.info('Location %r deleted by %r', self.location, session.user)
        # this code currently doesn't do anything since we don't allow deleting locations
        # that have non-deleted rooms, but if we change this in the future it's needed
        for room in self.location.rooms:
            logger.info('Deleting room %r', room)
            room.is_deleted = True
        db.session.flush()
        return '', 204

    @use_rh_kwargs(LocationArgs)
    def _process_POST(self, name, room_name_format, map_url_template):
        loc = Location(name=name, room_name_format=room_name_format, map_url_template=(map_url_template or ''))
        db.session.add(loc)
        db.session.flush()
        return self._jsonify_one(loc), 201

    @use_rh_kwargs(LocationArgs, partial=True)
    def _process_PATCH(self, name=None, room_name_format=None, map_url_template=missing):
        if name is not None:
            self.location.name = name
        if room_name_format is not None:
            self.location.room_name_format = room_name_format
        if map_url_template is not missing:
            self.location.map_url_template = map_url_template or ''
        db.session.flush()
        return self._jsonify_one(self.location)


class RHFeatures(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('feature_id')
        self.feature = RoomFeature.get_or_404(id_) if id_ is not None else None

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

    @use_rh_kwargs(FeatureArgs)
    def _process_POST(self, name, title, icon):
        feature = RoomFeature(name=name, title=title, icon=icon)
        db.session.add(feature)
        db.session.flush()
        return self._jsonify_one(feature), 201

    @use_rh_kwargs(FeatureArgs, partial=True)
    def _process_PATCH(self, name=None, title=None, icon=None):
        if name is not None:
            self.feature.name = name
        if title is not None:
            self.feature.title = title
        if icon is not None:
            self.feature.icon = icon
        db.session.flush()
        return self._jsonify_one(self.feature)


class RHEquipmentTypes(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('equipment_type_id')
        self.equipment_type = EquipmentType.get_or_404(id_) if id_ is not None else None

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

    @use_rh_kwargs(EquipmentTypeArgs)
    def _process_POST(self, name, features):
        equipment_type = EquipmentType(name=name, features=features)
        db.session.add(equipment_type)
        db.session.flush()
        return self._jsonify_one(equipment_type), 201

    @use_rh_kwargs(EquipmentTypeArgs, partial=True)
    def _process_PATCH(self, name=None, features=None):
        if name is not None:
            self.equipment_type.name = name
        if features is not None:
            self.equipment_type.features = features
        db.session.flush()
        return self._jsonify_one(self.equipment_type)


class RHAttributes(RHRoomBookingAdminBase):
    def _skip_admin_check(self):
        # GET on this endpoint does not expose anything sensitive, so
        # we allow any room manager to use it if they can edit rooms
        return request.method == 'GET' and rb_settings.get('managers_edit_rooms') and has_managed_rooms(session.user)

    def _process_args(self):
        id_ = request.view_args.get('attribute_id')
        self.attribute = RoomAttribute.get_or_404(id_) if id_ is not None else None

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

    @use_rh_kwargs(RoomAttributeArgs)
    def _process_POST(self, name, title, hidden):
        attribute = RoomAttribute(name=name, title=title, is_hidden=hidden)
        db.session.add(attribute)
        db.session.flush()
        return self._jsonify_one(attribute), 201

    @use_rh_kwargs(RoomAttributeArgs, partial=True)
    def _process_PATCH(self, name=None, title=None, hidden=None):
        if name is not None:
            self.attribute.name = name
        if title is not None:
            self.attribute.title = title
        if hidden is not None:
            self.attribute.is_hidden = hidden
        db.session.flush()
        return self._jsonify_one(self.attribute)


class RHRoomAdminBase(RHRoomBookingAdminBase):
    def _process_args(self):
        self.room = Room.get_or_404(request.view_args['room_id'], is_deleted=False)

    def _skip_admin_check(self):
        return rb_settings.get('managers_edit_rooms') and self.room.can_manage(session.user)


class RHRoomAttributes(RHRoomAdminBase):
    def _process(self):
        return RoomAttributeValuesSchema(many=True, only=('name', 'value')).jsonify(self.room.attributes)


class RHUpdateRoomAttributes(RHRoomAdminBase):
    @use_kwargs({'attributes': fields.Nested({'value': fields.Str(),
                                              'name': fields.Str()}, many=True)})
    def _process(self, attributes):
        update_room_attributes(self.room, attributes)
        return '', 204


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
    def _process_GET(self):
        return jsonify(room_update_schema.dump(self.room))

    @use_args(RoomUpdateArgsSchema)
    def _process_PATCH(self, args):
        update_room(self.room, args)
        RHRoomsPermissions._jsonify_user_permissions.clear_cached(session.user)
        return '', 204

    def _process_DELETE(self):
        if not rb_is_admin(session.user):
            raise Forbidden
        logger.info('Room %r deleted by %r', self.room, session.user)
        self.room.is_deleted = True
        return '', 204


class RHRoomPhoto(RHRoomAdminBase):
    def _process_GET(self):
        if not self.room.has_photo:
            raise NotFound
        return send_file('room.jpg', BytesIO(get_resized_room_photo(self.room)), 'image/jpeg')

    def _process_DELETE(self):
        self.room.photo = None
        remove_room_spritesheet_photo(self.room)
        return '', 204

    def _process_POST(self):
        f = request.files['photo']
        try:
            photo = Image.open(f)
        except IOError:
            raise UserValueError(_('You cannot upload this file as a room picture.'))
        if photo.format.lower() not in {'jpeg', 'png', 'gif'}:
            raise UserValueError(_('The file has an invalid format ({format}).').format(format=photo.format))
        if photo.mode != 'RGB':
            photo = photo.convert('RGB')
        image_bytes = BytesIO()
        photo.save(image_bytes, 'JPEG')
        image_bytes.seek(0)
        self.room.photo = Photo(data=image_bytes.read())
        token = build_rooms_spritesheet()
        return jsonify(rooms_sprite_token=unicode(token))


class RHRooms(RHRoomBookingAdminBase):
    def _process_GET(self):
        rooms = Room.query.filter_by(is_deleted=False).order_by(db.func.indico.natsort(Room.full_name)).all()
        return AdminRoomSchema().jsonify(rooms, many=True)

    @use_kwargs({'location_id': fields.Int(required=True)})
    @use_args(RoomUpdateArgsSchema)
    def _process_POST(self, args, location_id):
        room = Room()
        args['location_id'] = location_id
        update_room(room, args)
        db.session.add(room)
        db.session.flush()
        RHRoomsPermissions._jsonify_user_permissions.clear_cached(session.user)
        return jsonify(id=room.id)


_base_args = {
    'default': fields.Bool(),
    'bounds': fields.Nested({
        'north_east': fields.Nested({'lat': fields.Float(), 'lng': fields.Float()}, required=True),
        'south_west': fields.Nested({'lat': fields.Float(), 'lng': fields.Float()}, required=True)
    }, required=True)
}

_create_args = dict(_base_args, **{
    'name': fields.String(required=True)
})

_update_args = {
    'areas': fields.List(
        fields.Nested(dict(_base_args, **{
            'id': fields.Int(required=True),
            'name': fields.String()
        }), required=True)
    )
}


class RHMapAreas(RHRoomBookingAdminBase):
    @use_args(_create_args)
    def _process_POST(self, args):
        create_area(**args)
        return map_areas_schema.jsonify(MapArea.query)

    @use_kwargs(_update_args)
    def _process_PATCH(self, areas):
        for area in areas:
            update_area(area.pop('id'), area)
        return map_areas_schema.jsonify(MapArea.query)

    @use_kwargs({
        'area_ids': fields.List(fields.Int(), required=True)
    })
    def _process_DELETE(self, area_ids):
        delete_areas(area_ids)
        return '', 204
