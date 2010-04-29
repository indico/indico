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

from MaKaC.plugins.Collaboration.fossils import ICSBookingBaseConfModifFossil,\
    ICSErrorBaseFossil, ICSBookingBaseIndexingFossil
from MaKaC.common.fossilize import IFossil

class ICSBookingConfModifFossil(ICSBookingBaseConfModifFossil):

    def getUrl(self):
        pass

    def getPhoneBridgeId(self):
        pass

    def getPhoneBridgePassword(self):
        pass

    def getErrorMessage(self):
        pass

    def getErrorDetails(self):
        pass

    def getChangesFromEVO(self):
        pass


def removeAccessPassword(bookingParams):
    del bookingParams["accessPassword"]
    return bookingParams

class ICSBookingIndexingFossil(ICSBookingBaseIndexingFossil):

    def getBookingParams(self):
        """ Overloading of ICSBookingBaseFossil's getBookingParams to remove the pin """
    getBookingParams.convert = lambda bookingParams: removeAccessPassword(bookingParams)


class IEVOErrorFossil(ICSErrorBaseFossil):

    def getErrorType(self):
        pass

    def getRequestURL(self):
        pass

class IOverlappedErrorFossil(IEVOErrorFossil):

    def getSuperposedBooking(self):
        return self._overlappedBooking
    getSuperposedBooking.name = 'overlappedBooking'
    getSuperposedBooking.result = ICSBookingConfModifFossil


class IChangesFromEVOErrorFossil(IEVOErrorFossil):

    def getChanges(self):
        pass


class IEVOWarningFossil(IFossil):

    def getMessage(self):
        pass

    def getException(self):
        pass
