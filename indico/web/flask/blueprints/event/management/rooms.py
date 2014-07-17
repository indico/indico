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

from MaKaC.webinterface.rh import conferenceModif
from indico.modules.rb.controllers.user.event_reservations import (RHRoomBookingEventBookingList,
                                                                   RHRoomBookingEventBookingDetails)
from indico.web.flask.blueprints.event.management import event_mgmt


# Booking and event assignment list
event_mgmt.add_url_rule('/rooms/', 'rooms_booking_list', RHRoomBookingEventBookingList)
event_mgmt.add_url_rule('/rooms/book/select-event', 'conferenceModification-roomBookingChooseEvent',
                        conferenceModif.RHConfModifRoomBookingChooseEvent)

# View/modify booking
event_mgmt.add_url_rule('/rooms/booking/<roomLocation>/<int:resvID>/', 'rooms_booking_details',
                        RHRoomBookingEventBookingDetails)
event_mgmt.add_url_rule('/rooms/booking/<roomLocation>/<int:resvID>/modify',
                        'conferenceModification-roomBookingModifyBookingForm',
                        conferenceModif.RHConfModifRoomBookingBookingForm, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/rooms/booking/<roomLocation>/<int:resvID>/clone',
                        'conferenceModification-roomBookingCloneBooking',
                        conferenceModif.RHConfModifRoomBookingCloneBooking, methods=('GET', 'POST'))

# Book room
event_mgmt.add_url_rule('/rooms/book/search', 'conferenceModification-roomBookingSearch4Rooms',
                        conferenceModif.RHConfModifRoomBookingSearch4Rooms, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/rooms/book/search/results', 'conferenceModification-roomBookingRoomList',
                        conferenceModif.RHConfModifRoomBookingRoomList, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/rooms/book/confirm', 'conferenceModification-roomBookingBookingForm',
                        conferenceModif.RHConfModifRoomBookingBookingForm, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/rooms/book/save', 'conferenceModification-roomBookingSaveBooking',
                        conferenceModif.RHConfModifRoomBookingSaveBooking, methods=('GET', 'POST'))

# Room details
event_mgmt.add_url_rule('/rooms/room/<roomLocation>/<int:roomID>/', 'conferenceModification-roomBookingRoomDetails',
                        conferenceModif.RHConfModifRoomBookingRoomDetails, methods=('GET', 'POST'))
