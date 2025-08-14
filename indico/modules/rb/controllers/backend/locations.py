# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify

from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.schemas import locations_schema
from indico.modules.rb.util import get_locations_with_rooms


class RHLocations(RHRoomBookingBase):
    def _process(self):
        return jsonify(locations_schema.dump(get_locations_with_rooms()))
