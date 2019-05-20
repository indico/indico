# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import datetime, time

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.permissions import get_unified_permissions, update_principals_permissions
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod


@no_autoflush
def _populate_room(room, properties):
    for prop, value in properties.items():
        if prop not in ['available_equipment', 'bookable_hours', 'bookable_periods']:
            setattr(room, prop, value)


def update_room_equipment(room, available_equipment_ids):
    available_equipment = EquipmentType.query.filter(EquipmentType.id.in_(available_equipment_ids)).all()
    room.available_equipment = available_equipment
    db.session.flush()


def update_room_attributes(room, attributes):
    current_attributes = {x.attribute.name for x in room.attributes}
    new_attributes = {attribute['name'] for attribute in attributes}
    deleted_attributes = current_attributes - new_attributes
    for attribute in attributes:
        room.set_attribute_value(attribute['name'], attribute['value'])
    for deleted_attribute in deleted_attributes:
        room.set_attribute_value(deleted_attribute, None)
    db.session.flush()


def update_room_availability(room, availability):
    if 'bookable_hours' in availability:
        room.bookable_hours.order_by(False).delete()
        unique_bh = set((hours['start_time'], hours['end_time']) for hours in availability['bookable_hours'])
        db.session.add_all(
            [BookableHours(room=room, start_time=hours[0], end_time=hours[1]) for hours in unique_bh])
    if 'nonbookable_periods' in availability:
        room.nonbookable_periods.order_by(False).delete()
        unique_nbp = set((period['start_dt'], period['end_dt']) for period in availability['nonbookable_periods'])
        db.session.add_all(
            [NonBookablePeriod(room=room, start_dt=datetime.combine(period[0], time(0, 0)),
                               end_dt=datetime.combine(period[1], time(23, 59))) for period in unique_nbp])


def update_room(room, args):
    acl_entries = args.pop('acl_entries')
    if acl_entries:
        current = {e.principal: get_unified_permissions(e) for e in room.acl_entries}
        update_principals_permissions(room, current, acl_entries)
    _populate_room(room, args)
    db.session.flush()
