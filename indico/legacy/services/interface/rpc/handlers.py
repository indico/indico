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

from importlib import import_module

from indico.modules.rb import services as rb_services
from indico.modules.rb.services import aspects as rb_aspect_services
from indico.modules.rb.services import blockings as rb_blocking_services
from indico.modules.rb.services import rooms as rb_room_services


methodMap = {
    # rb base
    'roomBooking.getDateWarning': rb_services.GetDateWarning,
    # rb rooms
    'roomBooking.rooms.availabilitySearch': rb_room_services.RoomBookingAvailabilitySearchRooms,
    'roomBooking.locationsAndRooms.listWithGuids': rb_room_services.RoomBookingListLocationsAndRoomsWithGuids,
    'roomBooking.room.bookingPermission': rb_room_services.BookingPermission,
    # rb aspects
    'roomBooking.mapaspects.create': rb_aspect_services.RoomBookingMapCreateAspect,
    'roomBooking.mapaspects.update': rb_aspect_services.RoomBookingMapUpdateAspect,
    'roomBooking.mapaspects.remove': rb_aspect_services.RoomBookingMapRemoveAspect,
    'roomBooking.mapaspects.list': rb_aspect_services.RoomBookingMapListAspects,
    # rb blockings
    'roombooking.blocking.approve': rb_blocking_services.RoomBookingBlockingApprove,
    'roombooking.blocking.reject': rb_blocking_services.RoomBookingBlockingReject,
}


endpointMap = {
    "search": import_module('indico.legacy.services.implementation.search')
}
