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
from marshmallow_enum import EnumField
from webargs import fields
from webargs.flaskparser import use_args

from indico.modules.rb import Location
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb_new.schemas import aspect_schema, rooms_schema
from indico.modules.rb_new.util import get_buildings, search_for_rooms


class RHRoomBookingSearch(RHRoomBookingBase):
    @use_args({
        'capacity': fields.Int(),
        'room_name': fields.Str(),
        'start_dt': fields.DateTime(),
        'end_dt': fields.DateTime(),
        'repeat_frequency': EnumField(RepeatFrequency),
        'repeat_interval': fields.Int(missing=0),
        'building': fields.Str(),
        'floor': fields.Str()
    })
    def _process(self, args):
        rooms = search_for_rooms(args)
        return jsonify(rooms_schema.dump(rooms).data)


class RHRoomBookingLocation(RHRoomBookingBase):
    def _process(self):
        return jsonify(aspect_schema.dump(Location.default_location.default_aspect).data)


class RHRoomBookingBuildings(RHRoomBookingBase):
    def _process(self):
        return jsonify(get_buildings())
