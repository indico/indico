# -*- coding: utf-8 -*-
##
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

from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.webinterface import urlHandlers

class IConferenceMinimalFossil(IFossil):

    def getId(self):
        """Conference id"""

    def getType(self):
        """ Event type: 'conference', 'meeting', 'simple_event' """

    def getTitle(self):
        """Conference title"""

    def getDescription(self):
        """Conference description"""

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = lambda l: l and l.getName()

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = lambda r: r and r.getName()

    def getStartDate(self):
        """ Start Date """
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        """ End Date """
    getEndDate.convert = Conversion.datetime

    def getSupportEmail(self):
        """ Support Email """

class IConferenceParticipationMinimalFossil(IFossil):

    def getFirstName( self ):
        """ Conference Participation First Name """

    def getFamilyName( self ):
        """ Conference Participation Family Name """


class IConferenceParticipationFossil(IConferenceParticipationMinimalFossil):

    def getId( self ):
        """ Conference Participation Id """

    def getFullName( self ):
        """ Conference Participation Full Name """

    def getFullNameNoTitle(self):
        """ Conference Participation Full Name """
    getFullNameNoTitle.name = "name"

    def getAffiliation(self):
        """Conference Participation Affiliation """

    def getAddress(self):
        """Conference Participation Address """

    def getEmail(self):
        """Conference Participation Email """

    def getFax(self):
        """Conference Participation Fax """

    def getTitle(self):
        """Conference Participation Title """

    def getPhone(self):
        """Conference Participation Phone """



class IResourceFossil(IFossil):

    def getName(self):
        """ Name of the Resource """


class ILinkFossil(IResourceFossil):

    def getURL(self):
        """ URL of the file pointed by the link """
    getURL.name = "url"

class ILocalFileFossil(IResourceFossil):

    def getURL(self):
        """ URL of the Local File """
    getURL.produce = lambda s: str(urlHandlers.UHFileAccess.getURL(s))
    getURL.name = "url"


class IMaterialFossil(IFossil):

    def getTitle( self ):
        """ Material Title """

    def getResourceList(self):
        """ Material Resource List """
    getResourceList.result = {"MaKaC.conference.Link": ILinkFossil, "MaKaC.conference.LocalFile": ILocalFileFossil}
    getResourceList.name = "resources"


class ISessionFossil(IFossil):

    def getTitle(self):
        """ Session Title """

    def getId(self):
        """ Session Id """
    getId.name = "sessionId"

    def getDescription(self):
        """ Session Description """

    def getAllMaterialList(self):
        """ Session List of all material """
    getAllMaterialList.result = IMaterialFossil
    getAllMaterialList.name = "material"

    def getColor(self):
        """ Session Color """

    def getTextColor(self):
        """ Session Text Color """

    def isPoster(self):
        """ Is self a Poster Session ? """
    isPoster.produce = lambda s: s.getScheduleType() == 'poster'


class ISessionSlotFossil(IFossil):

    def getSession(self):
        """ Slot Session """
    getSession.result = ISessionFossil

    def getId(self):
        """ Session Slot Id """
    getId.name = "sessionSlotId"

    def getTitle(self):
        """ Session Slot Title """
    getTitle.name = "slotTitle"

    def getConference(self):
        """ Session Slot Conference """
    getConference.result = IConferenceMinimalFossil

    def getRoom(self):
        """ Session Slot Room """
    getRoom.convert = Conversion.roomName

    def getLocationName(self):
        """ Session Slot Location Name """
    getLocationName.produce = lambda s: s.getLocation()
    getLocationName.convert = Conversion.locationName
    getLocationName.name = "location"

    def getLocationAddress(self):
        """ Session Slot Location Address """
    getLocationAddress.produce = lambda s: s.getLocation()
    getLocationAddress.convert = Conversion.locationAddress
    getLocationAddress.name = "address"

    def inheritRoom(self):
        """ Does the Session inherit a Room ?"""
    inheritRoom.produce = lambda s: s.getOwnRoom() is None
    inheritRoom.name = "inheritRoom"

    def inheritLocation(self):
        """ Does the Session inherit a Location ?"""
    inheritLocation.produce = lambda s: s.getOwnLocation() is None
    inheritLocation.name = "inheritLoc"

    def getOwnConvenerList(self):
        """ Session Slot Conveners List """
    getOwnConvenerList.result = IConferenceParticipationFossil
    getOwnConvenerList.name = "conveners"
