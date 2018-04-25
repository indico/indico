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

from indico.core.db.sqlalchemy.util.queries import with_total_rows
from indico.modules.rb import Location
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb_new.schemas import aspects_schema, rooms_schema
from indico.modules.rb_new.util import get_buildings, search_for_rooms


class RHRoomBookingSearch(RHRoomBookingBase):
    @use_args({
        'capacity': fields.Int(),
        'text': fields.Str(),
        'start_dt': fields.DateTime(),
        'end_dt': fields.DateTime(),
        'repeat_frequency': EnumField(RepeatFrequency),
        'repeat_interval': fields.Int(missing=0),
        'building': fields.Str(),
        'floor': fields.Str(),
        'offset': fields.Int(missing=0, validate=lambda x: x >= 0),
        'limit': fields.Int(missing=10, validate=lambda x: x >= 0),
    })
    def _process(self, args):
        filter_availability = args.get('start_dt') and args.get('end_dt')
        query = search_for_rooms(args, only_available=filter_availability)
        query = query.limit(args['limit']).offset(args['offset'])
        rooms, total = with_total_rows(query)
        return jsonify(total=total, rooms=rooms_schema.dump(rooms).data)


class RHRoomBookingAspects(RHRoomBookingBase):
    def _process(self):
        to_cast = ['top_left_latitude', 'top_left_longitude', 'bottom_right_latitude', 'bottom_right_longitude']
        aspects = [
            {k: float(v) if k in to_cast else v for k, v in aspect.viewitems()}
            for aspect in aspects_schema.dump(Location.default_location.aspects).data
        ]
        return jsonify(aspects)


class RHRoomBookingBuildings(RHRoomBookingBase):
    def _process(self):
        return jsonify(get_buildings())
