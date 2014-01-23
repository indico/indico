# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from flask import request

from indico.util.fossilize import fossilize

# legacy MaKaC imports
from MaKaC.services.implementation.base import ServiceError
from MaKaC.plugins.Collaboration.services import CollaborationBookingModifBase
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools


class ConnectVidyoBookingBase(CollaborationBookingModifBase):
    """ Base class for services on booking objects for connect/disconnect
    """

    def _checkProtection(self):
        if self.getAW().getUser() and request.remote_addr == VidyoTools.getLinkRoomAttribute(self._booking.getLinkObject(),
                                                                                             attName='IP'):
            return
        elif not hasattr(self._booking, "getOwnerObject") or self._booking.getOwnerObject() != self.getAW().getUser():
            CollaborationBookingModifBase._checkProtection(self)

    def _getAnswer(self):
        if self._booking.isLinkedToEquippedRoom():
            return self._operation()
        else:
            raise ServiceError("", _("Booking is not linked to conference-enabled room"))



class ConnectVidyoBooking(ConnectVidyoBookingBase):
    """ Performs server-side actions when a booking is connected
    """

    def _operation(self):
        self._force = self._pm.extract("force", pType=bool, allowEmpty=True)
        return fossilize(self._booking._connect(force=self._force), timezone=self._conf.getTimezone())


class CollaborationDisconnectVidyoBooking(ConnectVidyoBookingBase):
    """ Performs server-side actions when a booking is disconnected
    """

    def _operation(self):
        return fossilize(self._booking._disconnect(), timezone=self._conf.getTimezone())


class CollaborationCheckVidyoBookingConnection(ConnectVidyoBookingBase):
    """ Performs server-side actions when a booking's status is checked
    """
    def _operation(self):
        return fossilize(self._booking.connectionStatus(), timezone=self._conf.getTimezone())


methodMap = {
    "vidyo.connectVidyoBooking": ConnectVidyoBooking,
    "vidyo.disconnectVidyoBooking": CollaborationDisconnectVidyoBooking,
    "vidyo.checkVidyoBookingConnection": CollaborationCheckVidyoBookingConnection
}
