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

from indico.core.db import db
from indico.modules.rb.models.equipment import EquipmentType
from indico.modules.rb.models.rooms import Room


def get_equipment_types():
    query = (db.session
             .query(EquipmentType.name)
             .distinct(EquipmentType.name)
             .filter(EquipmentType.rooms.any(Room.is_active))
             .order_by(EquipmentType.name))
    return [row.name for row in query]
