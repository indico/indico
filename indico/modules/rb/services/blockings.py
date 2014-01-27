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


from ..models.blockings import Blocking
from . import ServiceBase


class RoomBookingBlockingProcessBase(ServiceBase):

    def _checkParams(self):
        self._blocking = RoomBlockingBase.getById(int(self._params["blockingId"]))
        self._room = RoomGUID.parse(self._params["room"]).getRoom()
        self._roomBlocking = self._blocking.getBlockedRoom(self._room)

    def _checkProtection(self):
        user = self._aw.getUser()
        if not user or (not user.isAdmin() and not self._room.isOwnedBy(user)):
            raise ServiceError(_('You are not permitted to modify this blocking'))


class RoomBookingBlockingApprove(RoomBookingBlockingProcessBase):

    def _getAnswer(self):
        self._roomBlocking.approve()
        return {"active": self._roomBlocking.getActiveString()}


class RoomBookingBlockingReject(RoomBookingBlockingProcessBase):

    def _checkParams(self):
        RoomBookingBlockingProcessBase._checkParams(self)
        self._reason = self._params.get('reason')
        if not self._reason:
            raise ServiceError(_('You have to specify a rejection reason'))

    def _getAnswer(self):
        self._roomBlocking.reject(self._getUser(), self._reason)
        return {"active": self._roomBlocking.getActiveString()}
