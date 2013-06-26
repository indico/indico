# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint


rooms_admin = IndicoBlueprint('rooms_admin', __name__, url_prefix='/admin/rooms')


# Main settings
rooms_admin.add_url_rule('/config/', 'roomBookingPluginAdmin',
                         rh_as_view(roomBookingPluginAdmin.RHRoomBookingPluginAdmin))
rooms_admin.add_url_rule('/config/toggle', 'roomBookingPluginAdmin-switchRoomBookingModuleActive',
                         rh_as_view(roomBookingPluginAdmin.RHSwitchRoomBookingModuleActive))
rooms_admin.add_url_rule('/config/save-db', 'roomBookingPluginAdmin-zodbSave',
                         rh_as_view(roomBookingPluginAdmin.RHZODBSave), methods=('POST',))

# Locations
rooms_admin.add_url_rule('/locations/', 'roomBooking-admin', rh_as_view(roomBooking.RHRoomBookingAdmin))
rooms_admin.add_url_rule('/locations/delete', 'roomBooking-deleteLocation',
                         rh_as_view(roomBooking.RHRoomBookingDeleteLocation), methods=('POST',))
rooms_admin.add_url_rule('/locations/add', 'roomBooking-saveLocation',
                         rh_as_view(roomBooking.RHRoomBookingSaveLocation), methods=('POST',))
rooms_admin.add_url_rule('/locations/set-default', 'roomBooking-setDefaultLocation',
                         rh_as_view(roomBooking.RHRoomBookingSetDefaultLocation), methods=('POST',))
rooms_admin.add_url_rule('/location/<path:locationId>/', 'roomBooking-adminLocation',
                         rh_as_view(roomBooking.RHRoomBookingAdminLocation))
rooms_admin.add_url_rule('/location/<path:locationId>/attribute/delete', 'roomBooking-deleteCustomAttribute',
                         rh_as_view(roomBooking.RHRoomBookingDeleteCustomAttribute))
rooms_admin.add_url_rule('/location/<path:locationId>/attribute/save', 'roomBooking-saveCustomAttributes',
                         rh_as_view(roomBooking.RHRoomBookingSaveCustomAttribute), methods=('POST',))
rooms_admin.add_url_rule('/location/<path:locationId>/equipment/delete', 'roomBooking-deleteEquipment',
                         rh_as_view(roomBooking.RHRoomBookingDeleteEquipment), methods=('POST',))
rooms_admin.add_url_rule('/location/<path:locationId>/equipment/save', 'roomBooking-saveEquipment',
                         rh_as_view(roomBooking.RHRoomBookingSaveEquipment), methods=('POST',))

# Rooms
rooms_admin.add_url_rule('/room/<path:roomLocation>/<roomID>/delete', 'roomBooking-deleteRoom',
                         rh_as_view(roomBooking.RHRoomBookingDeleteRoom), methods=('POST',))
rooms_admin.add_url_rule('/room/<path:roomLocation>/create', 'roomBooking-roomForm',
                         rh_as_view(roomBooking.RHRoomBookingRoomForm))
rooms_admin.add_url_rule('/room/<path:roomLocation>/create/save', 'roomBooking-saveRoom',
                         rh_as_view(roomBooking.RHRoomBookingSaveRoom), methods=('POST',))
rooms_admin.add_url_rule('/room/<path:roomLocation>/<roomID>/modify', 'roomBooking-roomForm',
                         rh_as_view(roomBooking.RHRoomBookingRoomForm), methods=('GET', 'POST'))
rooms_admin.add_url_rule('/room/<path:roomLocation>/<roomID>/modify/save', 'roomBooking-saveRoom',
                         rh_as_view(roomBooking.RHRoomBookingSaveRoom), methods=('POST',))

# Mappers
rooms_admin.add_url_rule('/mappers/', 'roomMapper', rh_as_view(roomMappers.RHRoomMappers), methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/create', 'roomMapper-creation', rh_as_view(roomMappers.RHRoomMapperCreation),
                         methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/create/save', 'roomMapper-performCreation',
                         rh_as_view(roomMappers.RHRoomMapperPerformCreation), methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/<roomMapperId>/', 'roomMapper-details', rh_as_view(roomMappers.RHRoomMapperDetails),
                         methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/<roomMapperId>/modify', 'roomMapper-modify',
                         rh_as_view(roomMappers.RHRoomMapperModification), methods=('GET', 'POST'))
rooms_admin.add_url_rule('/mappers/<roomMapperId>/modify/save', 'roomMapper-performModify',
                         rh_as_view(roomMappers.RHRoomMapperPerformModification), methods=('GET', 'POST'))
