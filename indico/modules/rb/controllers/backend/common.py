# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import validate
from marshmallow_enum import EnumField
from webargs import fields

from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.util import WEEKDAYS


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
    'repeat_interval': fields.Int(load_default=0),
    'recurrence_weekdays': fields.List(fields.Str(validate=validate.OneOf(WEEKDAYS))),
    'building': fields.Str(),
    'sw_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'sw_lng': fields.Float(validate=lambda x: -180 <= x <= 180),
    'ne_lat': fields.Float(validate=lambda x: -90 <= x <= 90),
    'ne_lng': fields.Float(validate=lambda x: -180 <= x <= 180),
    'location_id': fields.Int(),
}
