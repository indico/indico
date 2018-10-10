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

from flask import jsonify
from sqlalchemy.orm import contains_eager

from indico.core.db import db
from indico.modules.rb import Location, Room
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb_new.operations.locations import get_equipment_types
from indico.modules.rb_new.schemas import aspects_schema, locations_schema


class RHLocations(RHRoomBookingBase):
    def _process(self):
        locations = (Location.query
                     .join(Room, (Location.id == Room.location_id) & Room.is_active)
                     .options(contains_eager('rooms').noload('*'))
                     .order_by(Location.name, db.func.indico.natsort(Room.full_name))
                     .all())
        return jsonify(locations_schema.dump(locations).data)


class RHAspects(RHRoomBookingBase):
    def _process(self):
        if not Location.query.has_rows():
            return jsonify([])

        to_cast = ['top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude']
        aspects = [
            {k: float(v) if k in to_cast else v for k, v in aspect.viewitems()}
            for aspect in aspects_schema.dump(Location.default_location.aspects).data
        ]
        return jsonify(aspects)


class RHEquipmentTypes(RHRoomBookingBase):
    def _process(self):
        return jsonify(get_equipment_types())
