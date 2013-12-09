# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Equipments for rooms
"""

from indico.core.db import db
from indico.modules.rb.models import utils


RoomEquipmentAssociation = db.Table(
    'rooms_equipments',
    db.metadata,
    db.Column(
        'equipment_id',
        db.Integer,
        db.ForeignKey(
            'room_equipments.id',
            ondelete='cascade'
        ),
        primary_key=True,
    ),
    db.Column(
        'room_id',
        db.Integer,
        db.ForeignKey(
            'rooms.id',
            ondelete='cascade'
        ),
        primary_key=True
    )
)


class RoomEquipment(db.Model):
    __tablename__ = 'room_equipments'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        unique=True,
        index=True
    )

    # core

    def __repr__(self):
        return '<RoomEquipment({0}, {1})>'.format(self.id, self.name)

    # getters

    @staticmethod
    def getEquipmentById(eid):
        return RoomEquipment.query.get(eid)

    @staticmethod
    @utils.filtered
    def getEquipments(**filters):
        return RoomEquipment, RoomEquipment.query

    @staticmethod
    def getEquipmentByName(name):
        return RoomEquipment.query.filter_by(name=name).first()
        # return RoomEquipment.getEquipments(name=name)
