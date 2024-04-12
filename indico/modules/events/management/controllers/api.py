# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify
from marshmallow.fields import Nested
from sqlalchemy.orm import joinedload

from indico.core.config import config
from indico.core.db import db
from indico.core.marshmallow import mm
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.web.rh import RHProtected


class _RoomSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Room
        fields = ('id', 'full_name')


class _LocationsSchema(mm.SQLAlchemyAutoSchema):
    rooms = Nested(_RoomSchema, many=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'rooms')


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
        return jsonify(enabled=True, locations=_LocationsSchema(many=True).dump(locations))
