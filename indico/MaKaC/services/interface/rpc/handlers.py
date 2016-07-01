# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from MaKaC.services.implementation import resources
from MaKaC.services.implementation import error

from MaKaC.services.interface.rpc import description

from indico.modules.rb import services as rb_services
from indico.modules.rb.services import (
    aspects as rb_aspect_services,
    blockings as rb_blocking_services,
    rooms as rb_room_services
)


def importModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


methodMap = {
    'resources.timezones.getAll': resources.GetTimezones,
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
    # system
    'system.describe': description.describe,
    'system.error.report': error.SendErrorReport
}


endpointMap = {
    "event": importModule("MaKaC.services.implementation.conference"),
    "user": importModule('MaKaC.services.implementation.user'),
    "search": importModule('MaKaC.services.implementation.search'),
    "reviewing": importModule('MaKaC.services.implementation.reviewing'),
    "category": importModule('MaKaC.services.implementation.category'),
    "upcomingEvents": importModule('MaKaC.services.implementation.upcoming'),
    "timezone": importModule('MaKaC.services.implementation.timezone'),
    "abstractReviewing": importModule('MaKaC.services.implementation.abstractReviewing'),
    "abstract": importModule('MaKaC.services.implementation.abstract'),
    "abstracts": importModule('MaKaC.services.implementation.abstracts'),
    "admin": importModule('MaKaC.services.implementation.admin')
}
