# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify
from sqlalchemy.orm import contains_eager

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.schemas import locations_schema


class RHLocations(RHRoomBookingBase):
    def _process(self):
        rooms_strategy = contains_eager('rooms')
        rooms_strategy.noload('*')
        rooms_strategy.joinedload('location').load_only('room_name_format')
        locations = (Location.query
                     .filter_by(is_deleted=False)
                     .join(Room, (Location.id == Room.location_id) & ~Room.is_deleted)
                     .options(rooms_strategy)
                     .order_by(Location.name, db.func.indico.natsort(Room.full_name))
                     .all())
        return jsonify(locations_schema.dump(locations))
