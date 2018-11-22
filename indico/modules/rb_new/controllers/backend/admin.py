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
from marshmallow import fields, missing, validate
from sqlalchemy.orm import joinedload
from webargs.flaskparser import abort, use_kwargs
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.equipment import EquipmentType, RoomEquipmentAssociation, equipment_features_table
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.room_features import RoomFeature
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb_new.schemas import admin_locations_schema, equipment_type_schema, room_feature_schema
from indico.util.i18n import _
from indico.util.marshmallow import ModelList


class RHRoomBookingAdminBase(RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not rb_is_admin(session.user):
            raise Forbidden


class RHLocations(RHRoomBookingAdminBase):
    def _process(self):
        query = Location.query.options(joinedload('rooms'))
        return jsonify(admin_locations_schema.dump(query.all()).data)


class RHFeatures(RHRoomBookingAdminBase):
    def _process_args(self):
        id_ = request.view_args.get('feature_id')
        self.feature = RoomFeature.get_one(id_) if id_ is not None else None

    def _dump_features(self):
        query = RoomFeature.query.order_by(RoomFeature.title)
        return room_feature_schema.dump(query, many=True).data

    def _get_equipment_counts(self):
        query = (db.session.query(equipment_features_table.c.feature_id, db.func.count())
                 .group_by(equipment_features_table.c.feature_id))
        return dict(query)

    def _jsonify_one(self, equipment_type):
        return jsonify(room_feature_schema.dump(equipment_type).data)

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
    def _process_PATCH(self, name, title, icon):
        if name is not missing:
            self._check_conflict(name)
            self.feature.name = name
        if title is not missing:
            self.feature.title = title
        if icon is not missing:
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
        return equipment_type_schema.dump(query, many=True).data

    def _get_room_counts(self):
        query = (db.session.query(RoomEquipmentAssociation.c.equipment_id, db.func.count())
                 .group_by(RoomEquipmentAssociation.c.equipment_id))
        return dict(query)

    def _jsonify_one(self, equipment_type):
        counts = self._get_room_counts()
        eq = equipment_type_schema.dump(equipment_type).data
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
        'features': ModelList(RoomFeature, column='name', missing=[])
    })
    def _process_POST(self, name, features):
        self._check_conflict(name)
        equipment_type = EquipmentType(name=name, features=features)
        db.session.add(equipment_type)
        db.session.flush()
        return self._jsonify_one(equipment_type), 201

    @use_kwargs({
        'name': fields.String(validate=validate.Length(min=2)),
        'features': ModelList(RoomFeature, column='name')
    })
    def _process_PATCH(self, name, features):
        if name is not missing:
            self._check_conflict(name)
            self.equipment_type.name = name
        if features is not missing:
            self.equipment_type.features = features
        db.session.flush()
        return self._jsonify_one(self.equipment_type)

    def _check_conflict(self, name):
        query = EquipmentType.query.filter(db.func.lower(EquipmentType.name) == name.lower())
        if self.equipment_type:
            query = query.filter(EquipmentType.id != self.equipment_type.id)
        if query.has_rows():
            abort(422, messages={'name': [_('Name must be unique')]})
