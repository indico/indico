# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify
from marshmallow.fields import Method
from sqlalchemy.orm import joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.util.string import natural_sort_key
from indico.web.rh import RHProtected


class _RoomSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Room
        fields = ('id', 'full_name')


class _LocationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        fields = ('id', 'name', 'rooms')

    rooms = Method('_serialize_rooms')

    def _serialize_rooms(self, location):
        rooms = sorted(location.rooms, key=lambda room: natural_sort_key(room.full_name))
        return _RoomSchema(many=True).dump(rooms)


class RHLocations(RHProtected):
    """API to check if room-booking is enabled, and if so, return the available locations."""

    def _process(self):
        if not config.ENABLE_ROOMBOOKING:
            return jsonify(enabled=False, locations=[])

        locations = (Location.query
                     .filter_by(is_deleted=False)
                     .join(Room, (Location.id == Room.location_id) & ~Room.is_deleted)
                     .options(joinedload('rooms'))
                     .order_by(db.func.lower(Location.name))
                     .all())
        return jsonify(enabled=True, locations=_LocationSchema(many=True).dump(locations))
