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

from marshmallow_enum import EnumField
from webargs import fields

from indico.legacy.common.cache import GenericCache
from indico.modules.rb.models.reservations import RepeatFrequency


_cache = GenericCache('Rooms')


search_room_args = {
    'capacity': fields.Int(),
    'equipment': fields.List(fields.Str()),
    'features': fields.List(fields.Str(), data_key='feature'),
    'favorite': fields.Bool(),
    'mine': fields.Bool(),
    'text': fields.Str(),
    'division': fields.Str(),
    'start_dt': fields.DateTime(),
    'end_dt': fields.DateTime(),
    'repeat_frequency': EnumField(RepeatFrequency),
    'repeat_interval': fields.Int(missing=0),
    'building': fields.Str(),
    'sw_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'sw_lng': fields.Float(validate=lambda x: -180 <= x <= 180),
    'ne_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'ne_lng': fields.Float(validate=lambda x: -180 <= x <= 180)
}
