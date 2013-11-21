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

from MaKaC.webinterface.wcomponents import WTemplated

from indico.modules.rb.views import WPRoomBookingBase


class WPRoomBookingBlockingDetails(WPRoomBookingBase):

    def __init__(self, rh, block):
        super(WPRoomBookingBlockingDetails, self).__init__(rh)
        self._block = block

    def _getBody(self, params):
        return WRoomBookingBlockingDetails(self._block).getHTML(params)


class WRoomBookingBlockingDetails(WTemplated):

    def __init__(self, block):
        self._block = block

    def getVars(self):
        wvars = super(WRoomBookingBlockingDetails, self).getVars()
        wvars['block'] = self._block
        return wvars


class WPRoomBookingBlockingForm(WPRoomBookingBase):

    def __init__(self, rh, block, errorMessage):
        super(WPRoomBookingBlockingDetails, self).__init__(rh)
        self._block = block
        self._errorMessage = errorMessage

    def _setCurrentMenuItem(self):
        self._blockRooms.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBlockingForm(self._block, self._errorMessage).getHTML(params)


class WRoomBookingBlockingForm(WTemplated):

    def __init__(self, block, errorMessage):
        self._block = block
        self._errorMessage = errorMessage

    def getVars(self):
        wvars = super(WRoomBookingBlockingForm, self).getVars()
        wvars['block'] = self._block
        wvars['errorMessage'] = self._errorMessage
        return wvars


class WPRoomBookingBlockingList(WPRoomBookingBase):

    def __init__(self, rh, blocks):
        super(WPRoomBookingBlockingList, self).__init__(rh)
        self._blocks = blocks

    def _setCurrentMenuItem(self):
        self._myBlockingListOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBlockingList(self._blocks).getHTML(params)


class WRoomBookingBlockingList(WTemplated):

    def __init__(self, blocks):
        self._blocks = blocks

    def getVars(self):
        wvars = super(WRoomBookingBlockingList, self).getVars()

        self._blocks.sort(key=attrgetter('startDate'), reverse=True)
        wvars['blocks'] = self._blocks
        return wvars


class WPRoomBookingBlockingsForMyRooms(WPRoomBookingBase):

    def __init__(self, rh, roomBlocks):
        super(WPRoomBookingBlockingsForMyRooms, self).__init__(rh)
        self._roomBlocks = roomBlocks

    def _setCurrentMenuItem(self):
        self._usersBlockings.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBlockingsForMyRooms(self._roomBlocks).getHTML(params)


class WRoomBookingBlockingsForMyRooms(WTemplated):

    def __init__(self, roomBlocks):
        self._roomBlocks = roomBlocks

    def getVars(self):
        wvars = super(WRoomBookingBlockingsForMyRooms, self).getVars()
        wvars['roomBlocks'] = self._roomBlocks
        return wvars
