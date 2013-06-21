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

from flask import Blueprint

from MaKaC.webinterface.rh import roomBooking
from indico.web.flask.util import rh_as_view

rooms = Blueprint('rooms', __name__)

# Photos
rooms.add_url_rule('/images/rooms/large_photos/<room>.jpg', 'photo_large', build_only=True)
rooms.add_url_rule('/images/rooms/small_photos/<room>.jpg', 'photo_small', build_only=True)

# Home, map, lists, search
rooms.add_url_rule('/rooms/', 'roomBooking', rh_as_view(roomBooking.RHRoomBookingWelcome))
rooms.add_url_rule('/rooms/map', 'roomBooking-mapOfRooms', rh_as_view(roomBooking.RHRoomBookingMapOfRooms))
rooms.add_url_rule('/rooms/map/widget', 'roomBooking-mapOfRoomsWidget',
                   rh_as_view(roomBooking.RHRoomBookingMapOfRoomsWidget))
rooms.add_url_rule('/rooms/bookings', 'roomBooking-bookingList', rh_as_view(roomBooking.RHRoomBookingBookingList),
                   methods=('GET', 'POST'))
rooms.add_url_rule('/rooms/search/bookings', 'roomBooking-search4Bookings',
                   rh_as_view(roomBooking.RHRoomBookingSearch4Bookings), methods=('GET', 'POST'))
rooms.add_url_rule('/rooms/search/rooms', 'roomBooking-search4Rooms', rh_as_view(roomBooking.RHRoomBookingSearch4Rooms),
                   methods=('GET', 'POST'))

# Booking a room
rooms.add_url_rule('/rooms/book/', 'roomBooking-bookRoom', rh_as_view(roomBooking.RHRoomBookingBookRoom))
rooms.add_url_rule('/rooms/book/search', 'roomBooking-bookingListForBooking',
                   rh_as_view(roomBooking.RHRoomBookingBookingList), methods=('GET', 'POST'),
                   defaults={'newBooking': 'on'})
rooms.add_url_rule('/rooms/book/confirm', 'roomBooking-bookingForm', rh_as_view(roomBooking.RHRoomBookingBookingForm),
                   methods=('GET', 'POST'))
rooms.add_url_rule('/rooms/book/save', 'roomBooking-saveBooking', rh_as_view(roomBooking.RHRoomBookingSaveBooking),
                   methods=('GET', 'POST'))

# Booking info
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/', 'roomBooking-bookingDetails',
                   rh_as_view(roomBooking.RHRoomBookingBookingDetails))

# Modify booking
rooms.add_url_rule('/rooms/show-message', 'roomBooking-statement', rh_as_view(roomBooking.RHRoomBookingStatement))
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/modify', 'roomBooking-modifyBookingForm',
                   rh_as_view(roomBooking.RHRoomBookingBookingForm), methods=('GET', 'POST'))
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/cancel', 'roomBooking-cancelBooking',
                   rh_as_view(roomBooking.RHRoomBookingCancelBooking), methods=('POST',))
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/reject', 'roomBooking-rejectBooking',
                   rh_as_view(roomBooking.RHRoomBookingRejectBooking), methods=('POST',))
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/delete', 'roomBooking-deleteBooking',
                   rh_as_view(roomBooking.RHRoomBookingDeleteBooking), methods=('POST',))
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/<date>/cancel', 'roomBooking-cancelBookingOccurrence',
                   rh_as_view(roomBooking.RHRoomBookingCancelBookingOccurrence), methods=('POST',))
rooms.add_url_rule('/rooms/booking/<roomLocation>/<resvID>/<date>/reject', 'roomBooking-rejectBookingOccurrence',
                   rh_as_view(roomBooking.RHRoomBookingRejectBookingOccurrence), methods=('POST',))

# Room info
rooms.add_url_rule('/rooms/room/<roomLocation>/<roomID>/', 'roomBooking-roomDetails',
                   rh_as_view(roomBooking.RHRoomBookingRoomDetails))
rooms.add_url_rule('/rooms/room/<roomLocation>/<roomID>/stats', 'roomBooking-roomStats',
                   rh_as_view(roomBooking.RHRoomBookingRoomStats), methods=('GET', 'POST'))
