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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.services.implementation import resources
from MaKaC.services.implementation import error

from MaKaC.services.interface.rpc import description
from MaKaC.plugins import PluginsHolder

from indico.modules.rb import services as rb_services
from indico.modules.rb.services import (
    aspects as rb_aspect_services,
    blockings as rb_blocking_services,
    locations as rb_location_services,
    rooms as rb_room_services
)


def importModule(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def updateMethodMapWithPlugins():
    methodMap.update(PluginsHolder().getById('ajaxMethodMap').getAJAXDict())


methodMap = {
    'resources.timezones.getAll': resources.GetTimezones,
    # rb base
    'roomBooking.getDateWarning': rb_services.GetDateWarning,
    # rb locations
    'roomBooking.locations.list': rb_location_services.RoomBookingListLocations,
    # rb rooms
    'roomBooking.rooms.list': rb_room_services.RoomBookingListRooms,
    'roomBooking.rooms.availabilitySearch': rb_room_services.RoomBookingAvailabilitySearchRooms,
    'roomBooking.rooms.fullNameList': rb_room_services.RoomBookingFullNameListRooms,
    'roomBooking.locationsAndRooms.listWithGuids': rb_room_services.RoomBookingListLocationsAndRoomsWithGuids,
    'roomBooking.locationsAndRooms.getLink': rb_room_services.RoomBookingLocationsAndRoomsGetLink,
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
    "contribution": importModule('MaKaC.services.implementation.contribution'),
    "session": importModule('MaKaC.services.implementation.session'),
    "schedule": importModule('MaKaC.services.implementation.schedule'),
    "search": importModule('MaKaC.services.implementation.search'),
    "material": importModule('MaKaC.services.implementation.material'),
    "reviewing": importModule('MaKaC.services.implementation.reviewing'),
    "minutes": importModule('MaKaC.services.implementation.minutes'),
    "news": importModule('MaKaC.services.implementation.news'),
    "plugins": importModule('MaKaC.services.implementation.plugins'),
    "category": importModule('MaKaC.services.implementation.category'),
    "upcomingEvents": importModule('MaKaC.services.implementation.upcoming'),
    "timezone": importModule('MaKaC.services.implementation.timezone'),
    "scheduler": importModule('MaKaC.services.implementation.scheduler'),
    "abstractReviewing": importModule('MaKaC.services.implementation.abstractReviewing'),
    "abstract": importModule('MaKaC.services.implementation.abstract'),
    "abstracts": importModule('MaKaC.services.implementation.abstracts'),
    "admin": importModule('MaKaC.services.implementation.admin'),
    "reportNumbers": importModule('MaKaC.services.implementation.reportNumbers'),
    "oauth": importModule('MaKaC.services.implementation.oauth'),
    "registration": importModule('MaKaC.services.implementation.registration')
}
