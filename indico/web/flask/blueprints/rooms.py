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

from indico.modules.rb.controllers.admin import reservations as reservation_admin_handlers
from indico.modules.rb.controllers.user import (
    blockings as blocking_handlers,
    index as index_handler,
    photos as photo_handlers,
    reservations as reservation_handlers,
    rooms as room_handlers
)
from indico.web.flask.wrappers import IndicoBlueprint


rooms = IndicoBlueprint('rooms', __name__, url_prefix='/rooms')


# Photos
rooms.add_url_rule('!/images/rooms/large_photos/<room>.<ext>', 'photo_large', build_only=True)
rooms.add_url_rule('!/images/rooms/small_photos/<room>.<ext>', 'photo_small', build_only=True)


# Home, map, lists, search
rooms.add_url_rule('/',
                   'roomBooking',
                   index_handler.RHRoomBookingWelcome)

rooms.add_url_rule('/map',
                   'roomBooking-mapOfRooms',
                   room_handlers.RHRoomBookingMapOfRooms)

rooms.add_url_rule('/map/widget',
                   'roomBooking-mapOfRoomsWidget',
                   room_handlers.RHRoomBookingMapOfRoomsWidget)

rooms.add_url_rule('/bookings',
                   'roomBooking-bookingList',
                   reservation_handlers.RHRoomBookingBookingList,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/rooms',
                   'roomBooking-roomList',
                   room_handlers.RHRoomBookingRoomList,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/search/bookings',
                   'roomBooking-search4Bookings',
                   reservation_handlers.RHRoomBookingSearch4Bookings,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/search/rooms',
                   'roomBooking-search4Rooms',
                   room_handlers.RHRoomBookingSearch4Rooms,
                   methods=('GET', 'POST'))


# Booking a room
rooms.add_url_rule('/book/',
                   'roomBooking-bookRoom',
                   reservation_handlers.RHRoomBookingBookRoom)

rooms.add_url_rule('/book/search',
                   'roomBooking-bookingListForBooking',
                   reservation_handlers.RHRoomBookingBookingList,
                   methods=('GET', 'POST'),
                   defaults={'newBooking': 'on'})

rooms.add_url_rule('/book/confirm',
                   'roomBooking-bookingForm',
                   reservation_handlers.RHRoomBookingBookingForm,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/book/save',
                   'roomBooking-saveBooking',
                   reservation_handlers.RHRoomBookingSaveBooking,
                   methods=('GET', 'POST'))


# Modify a booking
rooms.add_url_rule('/show-message',
                   'roomBooking-statement',
                   reservation_handlers.RHRoomBookingStatement)

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/modify',
                   'roomBooking-modifyBookingForm',
                   reservation_handlers.RHRoomBookingBookingForm,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/cancel',
                   'roomBooking-cancelBooking',
                   reservation_handlers.RHRoomBookingCancelBooking,
                   methods=('POST',))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/accept',
                   'roomBooking-acceptBooking',
                   reservation_handlers.RHRoomBookingAcceptBooking,
                   methods=('POST',))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/reject',
                   'roomBooking-rejectBooking',
                   reservation_handlers.RHRoomBookingRejectBooking,
                   methods=('POST',))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/delete',
                   'roomBooking-deleteBooking',
                   reservation_admin_handlers.RHRoomBookingDeleteBooking,
                   methods=('POST',))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/clone',
                   'roomBooking-cloneBooking',
                   reservation_handlers.RHRoomBookingCloneBooking,
                   methods=('POST',))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/<date>/cancel',
                   'roomBooking-cancelBookingOccurrence',
                   reservation_handlers.RHRoomBookingCancelBookingOccurrence,
                   methods=('POST',))

rooms.add_url_rule('/booking/<roomLocation>/<resvID>/<date>/reject',
                   'roomBooking-rejectBookingOccurrence',
                   reservation_handlers.RHRoomBookingRejectBookingOccurrence,
                   methods=('POST',))

rooms.add_url_rule('/bookings/reject-all-conflicting',
                   'roomBooking-rejectAllConflicting',
                   reservation_handlers.RHRoomBookingRejectALlConflicting)


# Booking info
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/',
                   'roomBooking-bookingDetails',
                   reservation_handlers.RHRoomBookingBookingDetails)


# Room info
rooms.add_url_rule('/room/<roomLocation>/<roomID>/',
                   'roomBooking-roomDetails',
                   room_handlers.RHRoomBookingRoomDetails)

rooms.add_url_rule('/room/<roomLocation>/<roomID>/stats',
                   'roomBooking-roomStats',
                   room_handlers.RHRoomBookingRoomStats,
                   methods=('GET', 'POST'))


# Room blocking
rooms.add_url_rule('/blocking/<blockingId>/',
                   'roomBooking-blockingDetails',
                   blocking_handlers.RHRoomBookingBlockingDetails)

rooms.add_url_rule('/blocking/<blockingId>/modify',
                   'roomBooking-blockingForm',
                   blocking_handlers.RHRoomBookingBlockingForm,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/blocking/<blockingId>/delete',
                   'roomBooking-deleteBlocking',
                   blocking_handlers.RHRoomBookingDelete,
                   methods=('POST',))

rooms.add_url_rule('/blocking/create',
                   'roomBooking-blockingForm',
                   blocking_handlers.RHRoomBookingBlockingForm,
                   methods=('GET', 'POST'))

rooms.add_url_rule('/blocking/list',
                   'roomBooking-blockingList',
                   blocking_handlers.RHRoomBookingBlockingList)

rooms.add_url_rule('/blocking/list/my-rooms',
                   'roomBooking-blockingsForMyRooms',
                   blocking_handlers.RHRoomBookingBlockingsForMyRooms)
