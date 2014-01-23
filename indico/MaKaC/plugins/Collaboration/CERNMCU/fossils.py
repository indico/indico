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

from MaKaC.common.fossilize import IFossil
from MaKaC.plugins.Collaboration.fossils import ICSErrorBaseFossil,\
    ICSBookingBaseIndexingFossil



def removePin(bookingParams):
    del bookingParams["pin"]
    return bookingParams

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

    def getIp(self):
        pass

    def getParticipantType(self):
        pass

    def getParticipantProtocol(self):
        pass

    def getCallState(self):
        pass

class IParticipantPersonFossil(IParticipantFossil):

    def getTitle(self):
        pass

    def getFamilyName(self):
        pass

    def getFirstName(self):
        pass

    def getAffiliation(self):
        pass


class IParticipantRoomFossil(IParticipantFossil):

    def getName(self):
        pass

    def getInstitution(self):
        pass


class IRoomWithH323Fossil(IFossil):

    def getLocation(self):
        pass
    getLocation.name = "institution"

    def getName(self):
        pass

    def getIp(self):
        pass


class ICERNMCUErrorFossil(ICSErrorBaseFossil):

    def getFaultCode(self):
        pass

    def getInfo(self):
        pass
