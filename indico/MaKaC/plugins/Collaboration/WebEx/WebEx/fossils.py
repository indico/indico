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

class ICSBookingIndexingFossil(ICSBookingBaseIndexingFossil):

    def getBookingParams(self):
        """ Overloading of ICSBookingBaseFossil's getBookingParams to remove the pin """
    getBookingParams.convert = lambda bookingParams: removePin(bookingParams)


class IParticipantFossil(IFossil):

    def getType(self):
        pass

    def getId(self):
        pass
    getId.name = "participantId"

    def getParticipantName(self):
        pass

    def getDisplayName(self):
        pass

    def getParticipantType(self):
        pass

    def getParticipantProtocol(self):
        pass

    def getCallState(self):
        pass

    def getTitle(self):
        pass

    def getFamilyName(self):
        pass

    def getFirstName(self):
        pass

    def getAffiliation(self):
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
