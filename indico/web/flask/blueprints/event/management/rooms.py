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

from indico.modules.rb.controllers.user.event import (RHRoomBookingEventBookingList, RHRoomBookingEventBookingDetails,
                                                      RHRoomBookingEventBookingModifyBooking,
                                                      RHRoomBookingEventBookingCloneBooking,
                                                      RHRoomBookingEventRoomDetails, RHRoomBookingEventNewBookingSimple,
                                                      RHRoomBookingEventChooseEvent, RHRoomBookingEventNewBooking)
from indico.web.flask.blueprints.event.management import event_mgmt


# Booking and event assignment list
event_mgmt.add_url_rule('/rooms/', 'rooms_booking_list', RHRoomBookingEventBookingList)
event_mgmt.add_url_rule('/rooms/choose-event', 'rooms_choose_event', RHRoomBookingEventChooseEvent)

# View/modify booking
event_mgmt.add_url_rule('/rooms/booking/<roomLocation>/<int:resvID>/', 'rooms_booking_details',
                        RHRoomBookingEventBookingDetails)
event_mgmt.add_url_rule('/rooms/booking/<roomLocation>/<int:resvID>/modify', 'rooms_booking_modify',
                        RHRoomBookingEventBookingModifyBooking, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/rooms/booking/<roomLocation>/<int:resvID>/clone', 'rooms_booking_clone',
                        RHRoomBookingEventBookingCloneBooking, methods=('GET', 'POST'))

# Book room
event_mgmt.add_url_rule('/rooms/room/<roomLocation>/<int:roomID>/book', 'rooms_room_book',
                        RHRoomBookingEventNewBookingSimple, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/rooms/book', 'rooms_book', RHRoomBookingEventNewBooking, methods=('GET', 'POST'))

# Room details
event_mgmt.add_url_rule('/rooms/room/<roomLocation>/<int:roomID>/', 'rooms_room_details', RHRoomBookingEventRoomDetails,
                        methods=('GET', 'POST'))
