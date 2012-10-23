# -*- coding: utf-8 -*-
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


from indico.util.fossilize import fossilize

# legacy MaKaC imports
from MaKaC.services.implementation.collaboration import CollaborationBookingModifBase
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools


class ConnectVidyoBookingBase(CollaborationBookingModifBase):
    """ Base class for services on booking objects for connect/disconnect
    """

    def _checkProtection(self):
        booking = self._CSBookingManager.getBooking(self._bookingId)

        if self.getAW().getUser() and self.getHostIP() == VidyoTools.getLinkRoomIp(booking.getLinkObject(), ipAttName='IP'):
            return
        elif not hasattr(booking, "getOwnerObject") or booking.getOwnerObject() != self.getAW().getUser():
            CollaborationBookingModifBase._checkProtection(self)


class ConnectVidyoBooking(ConnectVidyoBookingBase):
    """ Performs server-side actions when a booking is connected
    """

    def _getAnswer(self):
        self._force = self._pm.extract("force", pType=bool, allowEmpty=True)
        return fossilize(self._booking._connect(force=self._force), timezone=self._conf.getTimezone())


class CollaborationDisconnectVidyoBooking(ConnectVidyoBookingBase):
    """ Performs server-side actions when a booking is disconnected
    """

    def _getAnswer(self):
        return fossilize(self._booking._disconnect(), timezone=self._conf.getTimezone())


class CollaborationCheckVidyoBookingConnection(ConnectVidyoBookingBase):
    """ Performs server-side actions when a booking's status is checked
    """
    def _getAnswer(self):
        return fossilize(self._booking.connectionStatus(), timezone=self._conf.getTimezone())


methodMap = {
    "vidyo.connectVidyoBooking": ConnectVidyoBooking,
    "vidyo.disconnectVidyoBooking": CollaborationDisconnectVidyoBooking,
    "vidyo.checkVidyoBookingConnection": CollaborationCheckVidyoBookingConnection
}
