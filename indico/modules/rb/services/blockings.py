# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.util import rb_is_admin
from indico.util.i18n import _
from indico.legacy.services.implementation.base import ServiceBase
from indico.legacy.services.interface.rpc.common import ServiceError


class RoomBookingBlockingProcessBase(ServiceBase):
    UNICODE_PARAMS = True

    def _checkParams(self):
        self.blocked_room = BlockedRoom.get(self._params['blocked_room_id'])

    def _checkProtection(self):
        user = session.user
        if not user or (not rb_is_admin(user) and not self.blocked_room.room.is_owned_by(user)):
            raise ServiceError(_('You are not permitted to modify this blocking'))


class RoomBookingBlockingApprove(RoomBookingBlockingProcessBase):
    def _getAnswer(self):
        self.blocked_room.approve()
        return {'state': self.blocked_room.state_name}


class RoomBookingBlockingReject(RoomBookingBlockingProcessBase):
    def _checkParams(self):
        RoomBookingBlockingProcessBase._checkParams(self)
        self.reason = self._params.get('reason')
        if not self.reason:
            raise ServiceError(_('You have to specify a rejection reason'))

    def _getAnswer(self):
        self.blocked_room.reject(session.user, self.reason)
        return {'state': self.blocked_room.state_name}
