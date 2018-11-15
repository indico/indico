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
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.room_attributes import RoomAttribute, RoomAttributeAssociation


@no_autoflush
def _populate_room(room, properties):
    basic_props = [prop for prop in properties.keys() if prop not in ['available_equipment', 'unbookable_periods',
                                                                      'bookable_periods']]
    for prop in basic_props:
        if prop in properties:
            setattr(room, prop, properties[prop])
    return room


def get_room_attributes(room_id):
    attributes = RoomAttributeAssociation.query.filter(RoomAttributeAssociation.room_id.in_([room_id])).all()
    custom_attributes = {}
    for attribute in attributes:
        custom_attributes[attribute.attribute.name] = attribute.value
    return custom_attributes


def update_room_equipment(room, properties):
    if 'available_equipment' in properties:
        available_equipment_ids = properties['available_equipment']
        available_equipment = EquipmentType.query.filter(EquipmentType.id.in_(available_equipment_ids)).all()
        room.available_equipment = available_equipment
        db.session.flush()


def update_room(room, args):
    _populate_room(room, args)
    db.session.flush()
