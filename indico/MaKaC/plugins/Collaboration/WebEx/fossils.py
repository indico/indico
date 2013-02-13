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
    def getStartURL(self):
        pass

    def getUrl(self):
        pass

    def getErrorMessage(self):
        pass

    def getErrorDetails(self):
        pass

    def getChangesFromWebEx(self):
        pass

    def getWebExKey(self):
        pass

    def getWebExUser(self):
        pass

def removeComplex(bookingParams):
    del bookingParams["webExPass"]
    del bookingParams["accessPassword"]
    return bookingParams

class ICSBookingIndexingFossil(ICSBookingBaseIndexingFossil):
    def getBookingParams(self):
        """ Remove the booking params that are complex """
    getBookingParams.convert = lambda bookingParams: removeComplex(bookingParams)

class IParticipantFossil(IFossil):
    def getId(self):
        pass

    def getParticipantName(self):
        pass

    def getTitle(self):
        pass

    def getFamilyName(self):
        pass

    def getFirstName(self):
        pass

    def getAffiliation(self):
        pass

    def getEmail(self):
        pass

class IWebExErrorFossil(ICSErrorBaseFossil):
    def getFaultCode(self):
        pass

    def getInfo(self):
        pass
class IChangesFromWebExErrorFossil(IWebExErrorFossil):

    def getChanges(self):
        pass
class IWebExWarningFossil(IFossil):

    def getMessage(self):
        pass

    def getException(self):
        pass
