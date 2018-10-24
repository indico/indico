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

ReservationEquipmentAssociation = db.Table(
    'reservation_equipment',
    db.metadata,
    db.Column(
        'equipment_id',
        db.Integer,
        db.ForeignKey('roombooking.equipment_types.id'),
        primary_key=True,
    ),
    db.Column(
        'reservation_id',
        db.Integer,
        db.ForeignKey('roombooking.reservations.id'),
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
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.equipment_types.id')
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True,
        unique=True
    )

    children = db.relationship(
        'EquipmentType',
        backref=db.backref(
            'parent',
            remote_side=[id]
        )
    )

    # relationship backrefs:
    # - parent (EquipmentType.children)
    # - reservations (Reservation.used_equipment)
    # - rooms (Room.available_equipment)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name')
