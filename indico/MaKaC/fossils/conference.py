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

class ICategoryFossil(IFossil):

    def getId(self):
        """ Category Id """

    def getName(self):
        """ Category Name """

class IConferenceMinimalFossil(IFossil):

    def getId(self):
        """Conference id"""

    def getTitle(self):
        """Conference title"""

class IConferenceFossil(IConferenceMinimalFossil):

    def getType(self):
        """ Event type: 'conference', 'meeting', 'simple_event' """

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


class IResourceMinimalFossil(IFossil):

    def getName(self):
        """ Name of the Resource """

class ILinkMinimalFossil(IResourceMinimalFossil):

    def getURL(self):
        """ URL of the file pointed by the link """
    getURL.name = "url"

class ILocalFileMinimalFossil(IResourceMinimalFossil):

    def getURL(self):
        """ URL of the Local File """
    getURL.produce = lambda s: str(urlHandlers.UHFileAccess.getURL(s))
    getURL.name = "url"

class IResourceFossil(IResourceMinimalFossil):

    def getId(self):
        """ Resource Id """

    def getDescription(self):
        """ Resource description """

    def getAccessProtectionLevel(self):
        """ Resource Access Protection Level """
    getAccessProtectionLevel.name = "protection"

    def getReviewingState(self):
        """ Resource reviewing state """

class ILinkFossil(IResourceFossil, ILinkMinimalFossil):

    def getType(self):
        """ Type """
    getType.produce = lambda s: 'external'

class ILocalFileFossil(IResourceFossil, ILocalFileMinimalFossil):

    def getType(self):
        """ Type """
    getType.produce = lambda s: 'stored'

class ILocalFileExtendedFossil(ILocalFileFossil):

    def getFileName(self):
        """ Local File Filename """
    getFileName.name = "file.fileName"

    def getFileType(self):
        """ Local File File Type """
    getFileType.name = "file.fileType"

    def getCreationDate(self):
        """ Local File Creation Date """
    getCreationDate.convert = lambda s: s.strftime("%d.%m.%Y %H:%M:%S")
    getCreationDate.name = "file.creationDate"

    def getSize(self):
        """ Local File File Size """
    getSize.name = "file.fileSize"

class IMaterialMinimalFossil(IFossil):

    def getId(self):
        """ Material Id """

    def getTitle( self ):
        """ Material Title """

    def getResourceList(self):
        """ Material Resource List """
    getResourceList.result = {"MaKaC.conference.Link": ILinkMinimalFossil, "MaKaC.conference.LocalFile": ILocalFileMinimalFossil}
    getResourceList.name = "resources"

class IMaterialFossil(IMaterialMinimalFossil):

    def getReviewingState(self):
        """ Material Reviewing State """

    def getAccessProtectionLevel(self):
        """ Material Access Protection Level """
    getAccessProtectionLevel.name = "protection"

    def hasProtectedOwner(self):
        """ Does it have a protected owner ?"""

    def getDescription(self):
        """ Material Description """

    def isHidden(self):
        """ Whether the Material is hidden or not """
    isHidden.name = 'hidden'

    def getAccessKey(self):
        """ Material Access Key """

    def getResourceList(self):
        """ Material Resource List """
    getResourceList.result = {"MaKaC.conference.Link": ILinkFossil, "MaKaC.conference.LocalFile": ILocalFileExtendedFossil}
    getResourceList.name = "resources"

    def getMainResource(self):
        """ The main resource"""

    def getType(self):
        """ The type of material"""


class ISessionFossil(IFossil):

    def getId(self):
        """ Session Id """
    #getId.name = "sessionId"

    def getTitle(self):
        """ Session Title """

    def getAllMaterialList(self):
        """ Session List of all material """
    getAllMaterialList.result = IMaterialFossil
    getAllMaterialList.name = "material"

    def getNumSlots(self):
        """ Number of slots present in the session """
    getNumSlots.produce = lambda s : len(s.getSlotList())

    def getColor(self):
        """ Session Color """

    def getAdjustedStartDate(self):
        """ Session Start Date """
    getAdjustedStartDate.convert = Conversion.datetime
    getAdjustedStartDate.name = "startDate"

    def getLocation(self):
        """ Session Location """
    getLocation.convert = Conversion.locationName

    def getAddress(self):
        """ Session Address """
    getAddress.produce = lambda s: s.getLocation()
    getAddress.convert = Conversion.locationAddress

    def getRoom(self):
        """ Session Room """
    getRoom.convert = Conversion.roomName

    def getConvenerList(self):
        """ Session Conveners list """
    getConvenerList.result = IConferenceParticipationFossil
    getConvenerList.name = "sessionConveners"

    def isPoster(self):
        """ Is self a Poster Session ? """
    isPoster.produce = lambda s: s.getScheduleType() == 'poster'

    def getTextColor(self):
        """ Session Text Color """


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
    getConference.result = IConferenceFossil

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

class IConferenceEventInfoFossil(IConferenceMinimalFossil):
    """
    Fossil used to format the 'eventInfo' javascript object used
    in the timetable operations
    """

    def getAddress(self):
        """ Address """
    getAddress.produce = lambda s: s.getLocation()
    getAddress.convert = Conversion.locationAddress

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = Conversion.locationName

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = Conversion.roomName

    def getAdjustedStartDate(self):
        """ Start Date """
    getAdjustedStartDate.convert = Conversion.datetime
    getAdjustedStartDate.name = "startDate"

    def getAdjustedEndDate(self):
        """ End Date """
    getAdjustedEndDate.convert = Conversion.datetime
    getAdjustedEndDate.name = "endDate"

    def getSessions(self):
        """ Conference Sessions """
    getSessions.produce = lambda s: Conversion.sessionList(s)
    getSessions.result = ISessionFossil

    def isConference(self):
        """ Is this event a conference ? """
    isConference.produce = lambda s : s.getType() == 'conference'

    def getFavoriteRooms(self):
        """ Favorite Rooms """
