# -*- coding: utf-8 -*-
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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.plugins.Collaboration.fossils import ICSErrorBaseFossil, \
    ICSBookingBaseConfModifFossil, ICSBookingBaseIndexingFossil
from MaKaC.common.fossilize import IFossil


class ICSBookingConfModifFossil(ICSBookingBaseConfModifFossil):

    def getRoomId(self):
        """ returns the public room Vidyo id """

    def getExtension(self):
        """ returns the public room's extension """

    def getOwnerAccount(self):
        """ returns the Viydo account of the owner that was used to create the room """

    def getURL(self):
        """ returns the public room auto-join url """
    getURL.name = 'url'

    def getLinkVideoText(self):
        """returns the link to the booking"""

    def getLinkVideoRoomLocation(self):
        """returns the room location of the booking"""

    def getLinkId(self):
        """returns the uniqueId"""

    def isRoomInMultipleBookings(self):
        """ If different CSBookings contains the same Vidyo Room"""


def removePin(bookingParams):
    del bookingParams["pin"]
    return bookingParams

class ICSBookingIndexingFossil(ICSBookingBaseIndexingFossil):

    def getBookingParams(self):
        """ Overloading of ICSBookingBaseFossil's getBookingParams to remove the pin """
    getBookingParams.convert = lambda bookingParams: removePin(bookingParams)

    def getExtension(self):
        """ returns the public room's extension """

    def isCreated(self):
        """ Returns False if the public room is no longer in Vidyo and someone tried to checkStatus / modify it,
            otherwise True.
        """


class IVidyoErrorFossil(ICSErrorBaseFossil):

    def getErrorType(self):
        """ A string with the error type """

    def getOperation(self):
        """ A string with the operation (creation, edition, etc.) that produced the error """

    def getUserMessage(self):
        """ A string with the user message"""

class IFakeAvatarOwnerFossil(IFossil):

    def getId(self):
        """ returns None, always """
    def getName(self):
        """ returns the account name """
