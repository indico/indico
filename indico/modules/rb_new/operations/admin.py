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
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod


@no_autoflush
def _populate_room(room, properties):
    basic_props = [prop for prop in properties if prop not in ['available_equipment', 'unbookable_periods',
                                                                      'bookable_periods']]
    for prop in basic_props:
        if prop in properties:
            setattr(room, prop, properties[prop])
    return room


def update_room_equipment(room, properties):
    if 'available_equipment' in properties:
        available_equipment_ids = properties['available_equipment']
        available_equipment = EquipmentType.query.filter(EquipmentType.id.in_(available_equipment_ids)).all()
        room.available_equipment = available_equipment
        db.session.flush()


def update_room_attributes(room, attributes):
    current_associations = {association.attribute.name: association for association in room.attributes}
    for attribute, value in attributes.items():
        if attribute in current_associations:
            current_associations[attribute].value = value
        else:
            room_attr = RoomAttribute.query.filter_by(name=attribute).first()
            if room_attr is not None:
                room.attributes.append(RoomAttributeAssociation(room=room, attribute=room_attr, value=value))
    db.session.flush()


def update_room_availability(room, availability):
    if 'bookable_hours' in availability:
        room.bookable_hours.order_by(False).delete()
        db.session.add_all([BookableHours(room=room, **hours) for hours in availability['bookable_hours']])
    if 'nonbookable_periods' in availability:
        room.nonbookable_periods.order_by(False).delete()
        db.session.add_all([NonBookablePeriod(room=room, **periods) for periods in availability['nonbookable_periods']])


def update_room(room, args):
    _populate_room(room, args)
    db.session.flush()
