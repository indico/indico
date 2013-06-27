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

from MaKaC.webinterface.rh import roomBooking
from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint


rooms = IndicoBlueprint('rooms', __name__, url_prefix='/rooms')

# Photos
rooms.add_url_rule('!/images/rooms/large_photos/<room>.jpg', 'photo_large', build_only=True)
rooms.add_url_rule('!/images/rooms/small_photos/<room>.jpg', 'photo_small', build_only=True)

# Home, map, lists, search
rooms.add_url_rule('/', 'roomBooking', rh_as_view(roomBooking.RHRoomBookingWelcome))
rooms.add_url_rule('/map', 'roomBooking-mapOfRooms', rh_as_view(roomBooking.RHRoomBookingMapOfRooms))
rooms.add_url_rule('/map/widget', 'roomBooking-mapOfRoomsWidget',
                   rh_as_view(roomBooking.RHRoomBookingMapOfRoomsWidget))
rooms.add_url_rule('/bookings', 'roomBooking-bookingList', rh_as_view(roomBooking.RHRoomBookingBookingList),
                   methods=('GET', 'POST'))
rooms.add_url_rule('/rooms', 'roomBooking-roomList', rh_as_view(roomBooking.RHRoomBookingRoomList),
                   methods=('GET', 'POST'))
rooms.add_url_rule('/search/bookings', 'roomBooking-search4Bookings',
                   rh_as_view(roomBooking.RHRoomBookingSearch4Bookings), methods=('GET', 'POST'))
rooms.add_url_rule('/search/rooms', 'roomBooking-search4Rooms', rh_as_view(roomBooking.RHRoomBookingSearch4Rooms),
                   methods=('GET', 'POST'))

# Booking a room
rooms.add_url_rule('/book/', 'roomBooking-bookRoom', rh_as_view(roomBooking.RHRoomBookingBookRoom))
rooms.add_url_rule('/book/search', 'roomBooking-bookingListForBooking',
                   rh_as_view(roomBooking.RHRoomBookingBookingList), methods=('GET', 'POST'),
                   defaults={'newBooking': 'on'})
rooms.add_url_rule('/book/confirm', 'roomBooking-bookingForm', rh_as_view(roomBooking.RHRoomBookingBookingForm),
                   methods=('GET', 'POST'))
rooms.add_url_rule('/book/save', 'roomBooking-saveBooking', rh_as_view(roomBooking.RHRoomBookingSaveBooking),
                   methods=('GET', 'POST'))

# Booking info
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/', 'roomBooking-bookingDetails',
                   rh_as_view(roomBooking.RHRoomBookingBookingDetails))

# Modify booking
rooms.add_url_rule('/show-message', 'roomBooking-statement', rh_as_view(roomBooking.RHRoomBookingStatement))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/modify', 'roomBooking-modifyBookingForm',
                   rh_as_view(roomBooking.RHRoomBookingBookingForm), methods=('GET', 'POST'))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/cancel', 'roomBooking-cancelBooking',
                   rh_as_view(roomBooking.RHRoomBookingCancelBooking), methods=('POST',))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/accept', 'roomBooking-acceptBooking',
                   rh_as_view(roomBooking.RHRoomBookingAcceptBooking), methods=('POST',))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/reject', 'roomBooking-rejectBooking',
                   rh_as_view(roomBooking.RHRoomBookingRejectBooking), methods=('POST',))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/delete', 'roomBooking-deleteBooking',
                   rh_as_view(roomBooking.RHRoomBookingDeleteBooking), methods=('POST',))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/clone', 'roomBooking-cloneBooking',
                   rh_as_view(roomBooking.RHRoomBookingCloneBooking), methods=('POST',))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/<date>/cancel', 'roomBooking-cancelBookingOccurrence',
                   rh_as_view(roomBooking.RHRoomBookingCancelBookingOccurrence), methods=('POST',))
rooms.add_url_rule('/booking/<path:roomLocation>/<resvID>/<date>/reject', 'roomBooking-rejectBookingOccurrence',
                   rh_as_view(roomBooking.RHRoomBookingRejectBookingOccurrence), methods=('POST',))
rooms.add_url_rule('/bookings/reject-all-conflicting', 'roomBooking-rejectAllConflicting',
                   rh_as_view(roomBooking.RHRoomBookingRejectALlConflicting))

# Room info
rooms.add_url_rule('/room/<path:roomLocation>/<roomID>/', 'roomBooking-roomDetails',
                   rh_as_view(roomBooking.RHRoomBookingRoomDetails))
rooms.add_url_rule('/room/<path:roomLocation>/<roomID>/stats', 'roomBooking-roomStats',
                   rh_as_view(roomBooking.RHRoomBookingRoomStats), methods=('GET', 'POST'))

# Room blocking
rooms.add_url_rule('/blocking/<blockingId>/', 'roomBooking-blockingDetails',
                   rh_as_view(roomBooking.RHRoomBookingBlockingDetails))
rooms.add_url_rule('/blocking/<blockingId>/modify', 'roomBooking-blockingForm',
                   rh_as_view(roomBooking.RHRoomBookingBlockingForm), methods=('GET', 'POST'))
rooms.add_url_rule('/blocking/<blockingId>/delete', 'roomBooking-deleteBlocking',
                   rh_as_view(roomBooking.RHRoomBookingDelete), methods=('POST',))
rooms.add_url_rule('/blocking/create', 'roomBooking-blockingForm',
                   rh_as_view(roomBooking.RHRoomBookingBlockingForm), methods=('GET', 'POST'))
rooms.add_url_rule('/blocking/list', 'roomBooking-blockingList',
                   rh_as_view(roomBooking.RHRoomBookingBlockingList))
rooms.add_url_rule('/blocking/list/my-rooms', 'roomBooking-blockingsForMyRooms',
                   rh_as_view(roomBooking.RHRoomBookingBlockingsForMyRooms))
