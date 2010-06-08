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


class IFakeAvatarOwnerFossil(IFossil):

    def getId(self):
        """ returns None, always """
    def getName(self):
        """ returns the account name """
