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

from MaKaC.webinterface.rh import roomBookingPluginAdmin, roomBooking, roomMappers
from indico.web.flask.wrappers import IndicoBlueprint


rooms_admin = IndicoBlueprint('rooms_admin', __name__, url_prefix='/admin/rooms')


# Main settings
rooms_admin.add_url_rule('/config/', 'roomBookingPluginAdmin', roomBookingPluginAdmin.RHRoomBookingPluginAdmin)
rooms_admin.add_url_rule('/config/toggle', 'roomBookingPluginAdmin-switchRoomBookingModuleActive',
                         roomBookingPluginAdmin.RHSwitchRoomBookingModuleActive)
rooms_admin.add_url_rule('/config/save-db', 'roomBookingPluginAdmin-zodbSave', roomBookingPluginAdmin.RHZODBSave,
                         methods=('POST',))

# Locations
rooms_admin.add_url_rule('/locations/', 'roomBooking-admin', roomBooking.RHRoomBookingAdmin)
rooms_admin.add_url_rule('/locations/delete', 'roomBooking-deleteLocation', roomBooking.RHRoomBookingDeleteLocation,
                         methods=('POST',))
rooms_admin.add_url_rule('/locations/add', 'roomBooking-saveLocation', roomBooking.RHRoomBookingSaveLocation,
                         methods=('POST',))
rooms_admin.add_url_rule('/locations/set-default', 'roomBooking-setDefaultLocation',
                         roomBooking.RHRoomBookingSetDefaultLocation, methods=('POST',))
rooms_admin.add_url_rule('/location/<locationId>/', 'roomBooking-adminLocation',
                         roomBooking.RHRoomBookingAdminLocation)
rooms_admin.add_url_rule('/location/<locationId>/attribute/delete', 'roomBooking-deleteCustomAttribute',
                         roomBooking.RHRoomBookingDeleteCustomAttribute)
rooms_admin.add_url_rule('/location/<locationId>/attribute/save', 'roomBooking-saveCustomAttributes',
                         roomBooking.RHRoomBookingSaveCustomAttribute, methods=('POST',))
rooms_admin.add_url_rule('/location/<locationId>/equipment/delete', 'roomBooking-deleteEquipment',
                         roomBooking.RHRoomBookingDeleteEquipment, methods=('POST',))
rooms_admin.add_url_rule('/location/<locationId>/equipment/save', 'roomBooking-saveEquipment',
                         roomBooking.RHRoomBookingSaveEquipment, methods=('POST',))

# Rooms
rooms_admin.add_url_rule('/room/<roomLocation>/<roomID>/delete', 'roomBooking-deleteRoom',
                         roomBooking.RHRoomBookingDeleteRoom, methods=('POST',))
rooms_admin.add_url_rule('/room/<roomLocation>/create', 'roomBooking-roomForm', roomBooking.RHRoomBookingRoomForm)
rooms_admin.add_url_rule('/room/<roomLocation>/create/save', 'roomBooking-saveRoom',
                         roomBooking.RHRoomBookingSaveRoom, methods=('POST',))
rooms_admin.add_url_rule('/room/<roomLocation>/<roomID>/modify', 'roomBooking-roomForm',
                         roomBooking.RHRoomBookingRoomForm, methods=('GET', 'POST'))
rooms_admin.add_url_rule('/room/<roomLocation>/<roomID>/modify/save', 'roomBooking-saveRoom',
                         roomBooking.RHRoomBookingSaveRoom, methods=('POST',))

# Mappers
rooms_admin.add_url_rule('/mappers/', 'roomMapper', roomMappers.RHRoomMappers, methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/create', 'roomMapper-creation', roomMappers.RHRoomMapperCreation,
                         methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/create/save', 'roomMapper-performCreation', roomMappers.RHRoomMapperPerformCreation,
                         methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/<roomMapperId>/', 'roomMapper-details', roomMappers.RHRoomMapperDetails,
                         methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/<roomMapperId>/modify', 'roomMapper-modify', roomMappers.RHRoomMapperModification,
                         methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/<roomMapperId>/modify/save', 'roomMapper-performModify',
                         roomMappers.RHRoomMapperPerformModification, methods=('GET', 'POST'))
