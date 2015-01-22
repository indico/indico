# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
    def _setCurrentMenuItem(self):
        self._blockRoomsOpt.setActive(True)

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingDetails').getHTML(params)


class WPRoomBookingBlockingForm(WPRoomBookingBase):
    def _setCurrentMenuItem(self):
        self._blockRoomsOpt.setActive(True)

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingForm').getHTML(params)


class WPRoomBookingBlockingList(WPRoomBookingBase):
    def _setCurrentMenuItem(self):
        self._blockingListOpt.setActive(True)

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingList').getHTML(params)


class WPRoomBookingBlockingsForMyRooms(WPRoomBookingBase):
    def _setCurrentMenuItem(self):
        self._usersBlockingsOpt.setActive(True)

    def _getBody(self, params):
        return WTemplated('RoomBookingBlockingsForMyRooms').getHTML(params)
