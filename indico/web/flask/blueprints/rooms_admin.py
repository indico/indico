# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from indico.modules.rb.controllers.admin import (
    index as index_handler,
    locations as location_handlers,
    mappers as mapper_handlers,
    rooms as room_handlers
)
from indico.web.flask.wrappers import IndicoBlueprint


rooms_admin = IndicoBlueprint('rooms_admin', __name__, url_prefix='/admin/rooms')


# Main settings
rooms_admin.add_url_rule('/config/',
                         'roomBookingPluginAdmin',
                         index_handler.RHRoomBookingPluginAdmin)

rooms_admin.add_url_rule('/config/toggle',
                         'roomBookingPluginAdmin-switchRoomBookingModuleActive',
                         index_handler.RHSwitchRoomBookingModuleActive)


# Locations
rooms_admin.add_url_rule('/locations/',
                         'roomBooking-admin',
                         location_handlers.RHRoomBookingAdmin)

rooms_admin.add_url_rule('/locations/delete',
                         'roomBooking-deleteLocation',
                         location_handlers.RHRoomBookingDeleteLocation,
                         methods=('POST',))

rooms_admin.add_url_rule('/locations/add',
                         'roomBooking-saveLocation',
                         location_handlers.RHRoomBookingSaveLocation,
                         methods=('POST',))

rooms_admin.add_url_rule('/locations/set-default',
                         'roomBooking-setDefaultLocation',
                         location_handlers.RHRoomBookingSetDefaultLocation,
                         methods=('POST',))

rooms_admin.add_url_rule('/location/<locationId>/',
                         'roomBooking-adminLocation',
                         location_handlers.RHRoomBookingAdminLocation)

rooms_admin.add_url_rule('/location/<locationId>/attribute/delete',
                         'roomBooking-deleteCustomAttribute',
                         location_handlers.RHRoomBookingDeleteCustomAttribute)

rooms_admin.add_url_rule('/location/<locationId>/attribute/save',
                         'roomBooking-saveCustomAttributes',
                         location_handlers.RHRoomBookingSaveCustomAttribute,
                         methods=('POST',))

rooms_admin.add_url_rule('/location/<locationId>/equipment/delete',
                         'roomBooking-deleteEquipment',
                         location_handlers.RHRoomBookingDeleteEquipment,
                         methods=('POST',))

rooms_admin.add_url_rule('/location/<locationId>/equipment/save',
                         'roomBooking-saveEquipment',
                         location_handlers.RHRoomBookingSaveEquipment,
                         methods=('POST',))


# Rooms
rooms_admin.add_url_rule('/room/<roomLocation>/<roomID>/delete',
                         'roomBooking-deleteRoom',
                         room_handlers.RHRoomBookingDeleteRoom,
                         methods=('POST',))

rooms_admin.add_url_rule('/room/<roomLocation>/create',
                         'roomBooking-roomForm',
                         room_handlers.RHRoomBookingRoomForm)

rooms_admin.add_url_rule('/room/<roomLocation>/create/save',
                         'roomBooking-saveRoom',
                         room_handlers.RHRoomBookingSaveRoom,
                         methods=('POST',))

rooms_admin.add_url_rule('/room/<roomLocation>/<roomID>/modify',
                         'roomBooking-roomForm',
                         room_handlers.RHRoomBookingRoomForm,
                         methods=('GET', 'POST'))

rooms_admin.add_url_rule('/room/<roomLocation>/<roomID>/modify/save',
                         'roomBooking-saveRoom',
                         room_handlers.RHRoomBookingSaveRoom,
                         methods=('POST',))


# Mappers
rooms_admin.add_url_rule('/mappers/',
                         'roomMapper',
                         mapper_handlers.RHRoomMappers,
                         methods=('GET', 'POST'))

rooms_admin.add_url_rule('/mappers/create',
                         'roomMapper-creation',
                         mapper_handlers.RHRoomMapperCreation,
                         methods=('GET', 'POST'))

rooms_admin.add_url_rule('/mappers/create/save',
                         'roomMapper-performCreation',
                         mapper_handlers.RHRoomMapperPerformCreation,
                         methods=('GET', 'POST'))

rooms_admin.add_url_rule('/mappers/<roomMapperId>/',
                         'roomMapper-details',
                         mapper_handlers.RHRoomMapperDetails,
                         methods=('GET', 'POST'))

rooms_admin.add_url_rule('/mappers/<roomMapperId>/modify',
                         'roomMapper-modify',
                         mapper_handlers.RHRoomMapperModification,
                         methods=('GET', 'POST'))

rooms_admin.add_url_rule('/mappers/<roomMapperId>/modify/save',
                         'roomMapper-performModify',
                         mapper_handlers.RHRoomMapperPerformModification,
                         methods=('GET', 'POST'))
