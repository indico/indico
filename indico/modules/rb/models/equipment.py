# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


RoomEquipmentAssociation = db.Table(
    'room_equipment',
    db.metadata,
    db.Column(
        'equipment_id',
        db.Integer,
        db.ForeignKey('roombooking.equipment_types.id'),
        primary_key=True,
    ),
    db.Column(
        'room_id',
        db.Integer,
        db.ForeignKey('roombooking.rooms.id'),
        primary_key=True
    ),
    schema='roombooking'
)


equipment_features_table = db.Table(
    'equipment_features',
    db.metadata,
    db.Column(
        'equipment_id',
        db.Integer,
        db.ForeignKey('roombooking.equipment_types.id'),
        primary_key=True,
    ),
    db.Column(
        'feature_id',
        db.Integer,
        db.ForeignKey('roombooking.features.id'),
        primary_key=True
    ),
    schema='roombooking'
)


class EquipmentType(db.Model):
    __tablename__ = 'equipment_types'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True,
        unique=True
    )

    features = db.relationship(
        'RoomFeature',
        secondary=equipment_features_table,
        backref='equipment_types',
        lazy=True
    )

    # relationship backrefs:
    # - rooms (Room.available_equipment)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name')
