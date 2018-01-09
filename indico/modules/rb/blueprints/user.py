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

from indico.modules.rb.controllers.admin import reservations as reservation_admin_handlers
from indico.modules.rb.controllers.user import blockings as blocking_handlers
from indico.modules.rb.controllers.user import index as index_handler
from indico.modules.rb.controllers.user import photos as photo_handlers
from indico.modules.rb.controllers.user import reservations as reservation_handlers
from indico.modules.rb.controllers.user import rooms as room_handlers
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('rooms', __name__, template_folder='../templates', virtual_template_folder='rb',
                      url_prefix='/rooms')


# Photos
_bp.add_url_rule('/room/<roomLocation>/<int:roomID>/photo-<any(small,large):size>.jpg', 'photo',
                 photo_handlers.room_photo)


# Home, map, lists, search
_bp.add_url_rule('/',
                 'roomBooking',
                 index_handler.RHRoomBookingWelcome)

_bp.add_url_rule('/map',
                 'roomBooking-mapOfRooms',
                 room_handlers.RHRoomBookingMapOfRooms)

_bp.add_url_rule('/map/widget',
                 'roomBooking-mapOfRoomsWidget',
                 room_handlers.RHRoomBookingMapOfRoomsWidget)

_bp.add_url_rule('/calendar', 'calendar', reservation_handlers.RHRoomBookingCalendar)

_bp.add_url_rule('/bookings/search/', 'roomBooking-search4Bookings', reservation_handlers.RHRoomBookingSearchBookings,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/bookings/search/mine/', 'my_bookings', reservation_handlers.RHRoomBookingSearchMyBookings,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/bookings/search/my-rooms/', 'bookings_my_rooms',
                 reservation_handlers.RHRoomBookingSearchBookingsMyRooms, methods=('GET', 'POST'))

_bp.add_url_rule('/bookings/search/my-rooms/pending', 'pending_bookings_my_rooms',
                 reservation_handlers.RHRoomBookingSearchPendingBookingsMyRooms, methods=('GET', 'POST'))

# Search for rooms (not for booking)
_bp.add_url_rule('/rooms/search/', 'search_rooms', room_handlers.RHRoomBookingSearchRooms, methods=('GET', 'POST'))
_bp.add_url_rule('/rooms/search/mine', 'search_my_rooms', room_handlers.RHRoomBookingSearchMyRooms)


# Booking a room
_bp.add_url_rule('/book', 'book', reservation_handlers.RHRoomBookingNewBooking, methods=('GET', 'POST'))
_bp.add_url_rule('/room/<roomLocation>/<int:roomID>/book',
                 'room_book',
                 reservation_handlers.RHRoomBookingNewBookingSimple,
                 methods=('GET', 'POST'))


# Modify a booking
_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/modify',
                 'roomBooking-modifyBookingForm',
                 reservation_handlers.RHRoomBookingModifyBooking,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/cancel',
                 'roomBooking-cancelBooking',
                 reservation_handlers.RHRoomBookingCancelBooking,
                 methods=('POST',))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/accept',
                 'roomBooking-acceptBooking',
                 reservation_handlers.RHRoomBookingAcceptBooking,
                 methods=('POST',))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/reject',
                 'roomBooking-rejectBooking',
                 reservation_handlers.RHRoomBookingRejectBooking,
                 methods=('POST',))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/delete',
                 'roomBooking-deleteBooking',
                 reservation_admin_handlers.RHRoomBookingDeleteBooking,
                 methods=('POST',))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/clone',
                 'roomBooking-cloneBooking',
                 reservation_handlers.RHRoomBookingCloneBooking,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/<date>/cancel',
                 'roomBooking-cancelBookingOccurrence',
                 reservation_handlers.RHRoomBookingCancelBookingOccurrence,
                 methods=('POST',))

_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/<date>/reject',
                 'roomBooking-rejectBookingOccurrence',
                 reservation_handlers.RHRoomBookingRejectBookingOccurrence,
                 methods=('POST',))


# Booking info
_bp.add_url_rule('/booking/<roomLocation>/<int:resvID>/',
                 'roomBooking-bookingDetails',
                 reservation_handlers.RHRoomBookingBookingDetails)


# Room info
_bp.add_url_rule('/room/<roomLocation>/<int:roomID>/',
                 'roomBooking-roomDetails',
                 room_handlers.RHRoomBookingRoomDetails)

_bp.add_url_rule('/room/<roomLocation>/<int:roomID>/stats',
                 'roomBooking-roomStats',
                 room_handlers.RHRoomBookingRoomStats)


# Room blocking
_bp.add_url_rule('/blocking/<int:blocking_id>/',
                 'blocking_details',
                 blocking_handlers.RHRoomBookingBlockingDetails)

_bp.add_url_rule('/blocking/<int:blocking_id>/modify',
                 'modify_blocking',
                 blocking_handlers.RHRoomBookingModifyBlocking,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/blocking/<int:blocking_id>/delete',
                 'delete_blocking',
                 blocking_handlers.RHRoomBookingDeleteBlocking,
                 methods=('POST',))

_bp.add_url_rule('/blocking/create',
                 'create_blocking',
                 blocking_handlers.RHRoomBookingCreateBlocking,
                 methods=('GET', 'POST'))

_bp.add_url_rule('/blocking/list',
                 'blocking_list',
                 blocking_handlers.RHRoomBookingBlockingList)

_bp.add_url_rule('/blocking/list/my-rooms',
                 'blocking_my_rooms',
                 blocking_handlers.RHRoomBookingBlockingsForMyRooms)


_compat_bp = IndicoBlueprint('compat_rooms', __name__)
_compat_bp.add_url_rule('/roomBooking.py', 'roomBooking',
                        make_compat_redirect_func(_bp, 'roomBooking'))
_compat_bp.add_url_rule('/roomBooking.py/mapOfRooms', 'roomBooking-mapOfRooms',
                        make_compat_redirect_func(_bp, 'roomBooking-mapOfRooms'))
_compat_bp.add_url_rule('/roomBooking.py/search4Bookings', 'roomBooking-search4Bookings',
                        make_compat_redirect_func(_bp, 'roomBooking-search4Bookings'))
_compat_bp.add_url_rule('/roomBooking.py/bookingDetails', 'roomBooking-bookingDetails',
                        make_compat_redirect_func(_bp, 'roomBooking-bookingDetails'))
_compat_bp.add_url_rule('/roomBooking.py/roomDetails', 'roomBooking-roomDetails',
                        make_compat_redirect_func(_bp, 'roomBooking-roomDetails'))
_compat_bp.add_url_rule('/roomBooking.py/roomStats', 'roomBooking-roomStats',
                        make_compat_redirect_func(_bp, 'roomBooking-roomStats'))
