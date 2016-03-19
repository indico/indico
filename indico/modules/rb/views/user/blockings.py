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

from indico.modules.rb.views import WPRoomBookingBase
from MaKaC.webinterface.wcomponents import WTemplated


class WPRoomBookingBlockingDetails(WPRoomBookingBase):
    sidemenu_option = 'blocking_create'

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingDetails').getHTML(params)


class WPRoomBookingBlockingForm(WPRoomBookingBase):
    sidemenu_option = 'blocking_create'

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingForm').getHTML(params)


class WPRoomBookingBlockingList(WPRoomBookingBase):
    sidemenu_option = 'my_blockings'

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingList').getHTML(params)


class WPRoomBookingBlockingsForMyRooms(WPRoomBookingBase):
    sidemenu_option = 'blockings_my_rooms'

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingsForMyRooms').getHTML(params)
