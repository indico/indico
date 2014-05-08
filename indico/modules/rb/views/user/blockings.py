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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from indico.modules.rb.views import WPRoomBookingBase
from MaKaC.webinterface.wcomponents import WTemplated


class WPRoomBookingBlockingDetails(WPRoomBookingBase):
    def __init__(self, rh, blocking):
        WPRoomBookingBase.__init__(self, rh)
        self._blocking = blocking

    def _getBody(self, params):
        params = dict(params, blocking=self._blocking)
        return WTemplated('RoomBookingBlockingDetails').getHTML(params)


class WPRoomBookingBlockingForm(WPRoomBookingBase):
    def __init__(self, rh, form, errors, blocking=None):
        WPRoomBookingBase.__init__(self, rh)
        self._form = form
        self._errors = errors
        self._blocking = blocking

    def _setCurrentMenuItem(self):
        self._blockRooms.setActive(True)

    def _getBody(self, params):
        params = dict(params, form=self._form, blocking=self._blocking, errors=self._errors)
        return WTemplated('RoomBookingBlockingForm').getHTML(params)


class WPRoomBookingBlockingList(WPRoomBookingBase):
    def __init__(self, rh, blocks):
        WPRoomBookingBase.__init__(self, rh)
        self._blocks = blocks

    def _setCurrentMenuItem(self):
        self._myBlockingListOpt.setActive(True)

    def _getBody(self, params):
        params = dict(params, blocks=self._blocks)
        return WTemplated('RoomBookingBlockingList').getHTML(params)


class WPRoomBookingBlockingsForMyRooms(WPRoomBookingBase):
    def __init__(self, rh, roomBlocks):
        WPRoomBookingBase.__init__(self, rh)
        self._roomBlocks = roomBlocks

    def _setCurrentMenuItem(self):
        self._usersBlockings.setActive(True)

    def _getBody(self, params):
        params = dict(params, roomBlocks=self._roomBlocks)
        return WTemplated('RoomBookingBlockingsForMyRooms').getHTML(params)
