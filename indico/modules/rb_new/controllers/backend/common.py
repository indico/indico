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
from indico.modules.users import User


_cache = GenericCache('Rooms')


class UserField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        return User.get(value, is_deleted=False)


search_room_args = {
    'capacity': fields.Int(),
    'equipment': fields.List(fields.Str()),
    'features': fields.List(fields.Str(), load_from='feature'),
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


room_args = {
    'verbose_name': fields.Str(allow_none=True),
    'site': fields.Str(allow_none=True),
    'building': fields.String(validate=lambda x: x is not None),
    'floor': fields.String(validate=lambda x: x is not None),
    'number': fields.String(validate=lambda x: x is not None),
    'longitude': fields.Float(allow_none=True),
    'latitude': fields.Float(allow_none=True),
    'is_reservable': fields.Bool(allow_none=True),
    'reservations_need_confirmation': fields.Bool(allow_none=True),
    'notification_for_assistance': fields.Bool(allow_none=True),
    'notification_before_days': fields.Int(validate=lambda x: 1 <= x <= 30, aallow_none=True),
    'notification_before_days_weekly': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
    'notification_before_days_monthly': fields.Int(validate=lambda x: 1 <= x <= 30, allow_none=True),
    'notifications_enabled': fields.Bool(missing=True, allow_missing=True),
    'booking_limit_days': fields.Int(validate=lambda x: x >= 1, allow_none=True),
    'owner': UserField(load_from='owner_id', validate=lambda x: x is not None, allow_none=True),
    'key_location': fields.Str(allow_none=True),
    'telephone': fields.Str(allow_none=True),
    'capacity': fields.Int(validate=lambda x: x >= 1),
    'division': fields.Str(allow_none=True),
    'surface_area': fields.Int(validate=lambda x: x >= 0, allow_none=True),
    'max_advance_days': fields.Int(validate=lambda x: x >= 1, allow_none=True),
    'comments': fields.Str(allow_none=True),
}
