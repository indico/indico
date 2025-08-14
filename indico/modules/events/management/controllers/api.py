# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify
from marshmallow import fields

from indico.core.config import config
from indico.core.marshmallow import mm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.schemas import RoomSchema
from indico.modules.rb.util import get_locations_with_rooms
from indico.web.rh import RHProtected


class _LocationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        fields = ('id', 'name', 'rooms')

    rooms = fields.List(fields.Nested(RoomSchema, only=('id', 'full_name')))


class RHLocations(RHProtected):
    """API to check if room-booking is enabled, and if so, return the available locations."""

    def _process(self):
        if not config.ENABLE_ROOMBOOKING:
            return jsonify(enabled=False, locations=[])

        return jsonify(enabled=True, locations=_LocationSchema(many=True).dump(get_locations_with_rooms()))
