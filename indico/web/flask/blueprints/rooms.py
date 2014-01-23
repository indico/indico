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

from MaKaC.webinterface.rh import roomBooking
from indico.web.flask.wrappers import IndicoBlueprint


rooms = IndicoBlueprint('rooms', __name__, url_prefix='/rooms')

# Photos
rooms.add_url_rule('!/images/rooms/large_photos/<room>.<ext>', 'photo_large', build_only=True)
rooms.add_url_rule('!/images/rooms/small_photos/<room>.<ext>', 'photo_small', build_only=True)

# Home, map, lists, search
rooms.add_url_rule('/', 'roomBooking', roomBooking.RHRoomBookingWelcome)
rooms.add_url_rule('/map', 'roomBooking-mapOfRooms', roomBooking.RHRoomBookingMapOfRooms)
rooms.add_url_rule('/map/widget', 'roomBooking-mapOfRoomsWidget', roomBooking.RHRoomBookingMapOfRoomsWidget)
rooms.add_url_rule('/bookings', 'roomBooking-bookingList', roomBooking.RHRoomBookingBookingList,
                   methods=('GET', 'POST'))
rooms.add_url_rule('/rooms', 'roomBooking-roomList', roomBooking.RHRoomBookingRoomList, methods=('GET', 'POST'))
rooms.add_url_rule('/search/bookings', 'roomBooking-search4Bookings', roomBooking.RHRoomBookingSearch4Bookings,
                   methods=('GET', 'POST'))
rooms.add_url_rule('/search/rooms', 'roomBooking-search4Rooms', roomBooking.RHRoomBookingSearch4Rooms,
                   methods=('GET', 'POST'))

# Booking a room
rooms.add_url_rule('/book/', 'roomBooking-bookRoom', roomBooking.RHRoomBookingBookRoom)
rooms.add_url_rule('/book/search', 'roomBooking-bookingListForBooking', roomBooking.RHRoomBookingBookingList,
                   methods=('GET', 'POST'), defaults={'newBooking': 'on'})
rooms.add_url_rule('/book/confirm', 'roomBooking-bookingForm', roomBooking.RHRoomBookingBookingForm,
                   methods=('GET', 'POST'))
rooms.add_url_rule('/book/save', 'roomBooking-saveBooking', roomBooking.RHRoomBookingSaveBooking,
                   methods=('GET', 'POST'))

# Booking info
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/', 'roomBooking-bookingDetails',
                   roomBooking.RHRoomBookingBookingDetails)

# Modify booking
rooms.add_url_rule('/show-message', 'roomBooking-statement', roomBooking.RHRoomBookingStatement)
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/modify', 'roomBooking-modifyBookingForm',
                   roomBooking.RHRoomBookingBookingForm, methods=('GET', 'POST'))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/cancel', 'roomBooking-cancelBooking',
                   roomBooking.RHRoomBookingCancelBooking, methods=('POST',))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/accept', 'roomBooking-acceptBooking',
                   roomBooking.RHRoomBookingAcceptBooking, methods=('POST',))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/reject', 'roomBooking-rejectBooking',
                   roomBooking.RHRoomBookingRejectBooking, methods=('POST',))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/delete', 'roomBooking-deleteBooking',
                   roomBooking.RHRoomBookingDeleteBooking, methods=('POST',))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/clone', 'roomBooking-cloneBooking',
                   roomBooking.RHRoomBookingCloneBooking, methods=('POST',))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/<date>/cancel', 'roomBooking-cancelBookingOccurrence',
                   roomBooking.RHRoomBookingCancelBookingOccurrence, methods=('POST',))
rooms.add_url_rule('/booking/<roomLocation>/<resvID>/<date>/reject', 'roomBooking-rejectBookingOccurrence',
                   roomBooking.RHRoomBookingRejectBookingOccurrence, methods=('POST',))
rooms.add_url_rule('/bookings/reject-all-conflicting', 'roomBooking-rejectAllConflicting',
                   roomBooking.RHRoomBookingRejectALlConflicting)

# Room info
rooms.add_url_rule('/room/<roomLocation>/<roomID>/', 'roomBooking-roomDetails',
                   roomBooking.RHRoomBookingRoomDetails)
rooms.add_url_rule('/room/<roomLocation>/<roomID>/stats', 'roomBooking-roomStats',
                   roomBooking.RHRoomBookingRoomStats, methods=('GET', 'POST'))

# Room blocking
rooms.add_url_rule('/blocking/<blockingId>/', 'roomBooking-blockingDetails', roomBooking.RHRoomBookingBlockingDetails)
rooms.add_url_rule('/blocking/<blockingId>/modify', 'roomBooking-blockingForm', roomBooking.RHRoomBookingBlockingForm,
                   methods=('GET', 'POST'))
rooms.add_url_rule('/blocking/<blockingId>/delete', 'roomBooking-deleteBlocking', roomBooking.RHRoomBookingDelete,
                   methods=('POST',))
rooms.add_url_rule('/blocking/create', 'roomBooking-blockingForm', roomBooking.RHRoomBookingBlockingForm,
                   methods=('GET', 'POST'))
rooms.add_url_rule('/blocking/list', 'roomBooking-blockingList', roomBooking.RHRoomBookingBlockingList)
rooms.add_url_rule('/blocking/list/my-rooms', 'roomBooking-blockingsForMyRooms',
                   roomBooking.RHRoomBookingBlockingsForMyRooms)
