# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.modules.rb.controllers.admin import (
    index as index_handler,
    locations as location_handlers,
    rooms as room_handlers
)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('rooms_admin', __name__, template_folder='../templates', virtual_template_folder='rb',
                      url_prefix='/admin/rooms')


# Main settings
_bp.add_url_rule('/config/',
                 'settings',
                 index_handler.RHRoomBookingSettings,
                 methods=('GET', 'POST'))


# Locations
_bp.add_url_rule('/locations/',
                 'roomBooking-admin',
                 location_handlers.RHRoomBookingAdmin)

_bp.add_url_rule('/locations/delete',
                 'roomBooking-deleteLocation',
                 location_handlers.RHRoomBookingDeleteLocation,
                 methods=('POST',))

_bp.add_url_rule('/locations/add',
                 'roomBooking-saveLocation',
                 location_handlers.RHRoomBookingSaveLocation,
                 methods=('POST',))

_bp.add_url_rule('/locations/set-default',
                 'roomBooking-setDefaultLocation',
                 location_handlers.RHRoomBookingSetDefaultLocation,
                 methods=('POST',))

_bp.add_url_rule('/location/<locationId>/',
                 'roomBooking-adminLocation',
                 location_handlers.RHRoomBookingAdminLocation)

_bp.add_url_rule('/location/<locationId>/attribute/delete',
                 'roomBooking-deleteCustomAttribute',
                 location_handlers.RHRoomBookingDeleteCustomAttribute,
                 methods=('POST',))

_bp.add_url_rule('/location/<locationId>/attribute/save',
                 'roomBooking-saveCustomAttributes',
                 location_handlers.RHRoomBookingSaveCustomAttribute,
                 methods=('POST',))

_bp.add_url_rule('/location/<locationId>/equipment/delete',
                 'roomBooking-deleteEquipment',
                 location_handlers.RHRoomBookingDeleteEquipment,
                 methods=('POST',))

_bp.add_url_rule('/location/<locationId>/equipment/save',
                 'roomBooking-saveEquipment',
                 location_handlers.RHRoomBookingSaveEquipment,
                 methods=('POST',))


# Rooms
_bp.add_url_rule('/room/<roomLocation>/<int:roomID>/delete',
                 'delete_room',
                 room_handlers.RHRoomBookingDeleteRoom,
                 methods=('POST',))

_bp.add_url_rule('/room/<roomLocation>/create',
                 'create_room',
                 room_handlers.RHRoomBookingCreateRoom,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/room/<roomLocation>/<int:roomID>/modify',
                 'modify_room',
                 room_handlers.RHRoomBookingModifyRoom,
                 methods=('GET', 'POST'))
