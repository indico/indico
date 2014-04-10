# -*- coding: utf-8 -*-
##
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
from MaKaC.common.Conversion import Conversion
from MaKaC.webinterface import urlHandlers

from indico.core.fossils.event import ISupportInfoFossil


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

    def getAddress(self):
        """ Address of the event """
    getAddress.produce = lambda s: s.getLocation().getAddress() if s.getLocation() is not None else None

    def getRoomBookingList(self):
        """ Reservations """
    getRoomBookingList.convert = Conversion.reservationsList
    getRoomBookingList.name = "bookedRooms"

    def getStartDate(self):
        """ Start Date """
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        """ End Date """
    getEndDate.convert = Conversion.datetime

    def getAdjustedStartDate(self):
        """ Adjusted Start Date """
    getAdjustedStartDate.convert = Conversion.datetime

    def getAdjustedEndDate(self):
        """ Adjusted End Date """
    getAdjustedEndDate.convert = Conversion.datetime

    def getTimezone(self):
        """ Time zone """

    def getSupportInfo(self):
        """ Support Info"""
    getSupportInfo.result = ISupportInfoFossil


class IConferenceParticipationMinimalFossil(IFossil):

    def getFirstName( self ):
        """ Conference Participation First Name """

    def getFamilyName( self ):
        """ Conference Participation Family Name """

    def getDirectFullName(self):
        """ Conference Participation Full Name """

    getDirectFullName.name = "name"



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

class IResourceBasicFossil(IFossil):

    def getName(self):
        """ Name of the Resource """

    def getDescription(self):
        """ Resource Description """

class IResourceMinimalFossil(IResourceBasicFossil):

    def getProtectionURL(self):
        """ Resource protection URL """
    getProtectionURL.produce = lambda s: str(urlHandlers.UHMaterialModification.getURL(s.getOwner()))

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

    def getPDFConversionStatus(self):
        """ Resource PDF conversion status"""
    getPDFConversionStatus.name = "pdfConversionStatus"

class ILinkFossil(IResourceFossil, ILinkMinimalFossil):

    def getType(self):
        """ Type """
    getType.produce = lambda s: 'external'

class ILocalFileFossil(IResourceFossil, ILocalFileMinimalFossil):

    def getType(self):
        """ Type """
    getType.produce = lambda s: 'stored'

class ILocalFileInfoFossil(IFossil):

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

class ILocalFileExtendedFossil(ILocalFileFossil, ILocalFileInfoFossil):
    pass


class ILocalFileAbstractMaterialFossil(IResourceBasicFossil, ILocalFileInfoFossil):

    def getURL(self):
        """ URL of the Local File """
    getURL.produce = lambda s: str(urlHandlers.UHAbstractAttachmentFileAccess.getURL(s))
    getURL.name = "url"



class IMaterialMinimalFossil(IFossil):

    def getId(self):
        """ Material Id """

    def getTitle( self ):
        """ Material Title """

    def getDescription( self ):
        """ Material Description """

    def getResourceList(self):
        """ Material Resource List """
    getResourceList.result = {"MaKaC.conference.Link": ILinkMinimalFossil, "MaKaC.conference.LocalFile": ILocalFileMinimalFossil}
    getResourceList.name = "resources"

    def getType(self):
        """ The type of material"""

    def getProtectionURL(self):
        """ Material protection URL """
    getProtectionURL.produce = lambda s: str(urlHandlers.UHMaterialModification.getURL(s))


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
    getMainResource.result = {"MaKaC.conference.Link": ILinkFossil, "MaKaC.conference.LocalFile": ILocalFileExtendedFossil}

    def isBuiltin(self):
        """ The material is a default one (builtin) """


class ISessionBasicFossil(IFossil):

    def getId(self):
        """ Session Id """

    def getTitle(self):
        """ Session Title """

    def getDescription(self):
        """ Session Description """


class ISessionFossil(ISessionBasicFossil):

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

    def getAdjustedEndDate(self):
        """ Session End Date """
    getAdjustedEndDate.convert = Conversion.datetime
    getAdjustedEndDate.name = "endDate"

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

    def getRoomFullName(self):
        """ Session Room """
    getRoomFullName.produce = lambda s: s.getRoom()
    getRoomFullName.convert = Conversion.roomFullName
    getRoomFullName.name = 'roomFullname'

    def getConvenerList(self):
        """ Session Conveners list """
    getConvenerList.produce = lambda s: s.getAllConvenerList()
    getConvenerList.result = IConferenceParticipationFossil
    getConvenerList.name = "sessionConveners"

    def isPoster(self):
        """ Is self a Poster Session ? """
    isPoster.produce = lambda s: s.getScheduleType() == 'poster'

    def getTextColor(self):
        """ Session Text Color """

    def getLocator(self):
        pass
    getLocator.convert = Conversion.url(urlHandlers.UHSessionDisplay)
    getLocator.name = 'url'

    def getProtectionURL(self):
        """Session protection URL"""
    getProtectionURL.produce = lambda s: str(urlHandlers.UHSessionModifAC.getURL(s))

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

    def getRoomFullName(self):
        """ SessionSlot Room """
    getRoomFullName.produce = lambda s: s.getRoom()
    getRoomFullName.convert = Conversion.roomFullName
    getRoomFullName.name = 'roomFullname'

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

    def getStartDate(self):
        """ """
    getStartDate.produce = lambda s: s.getAdjustedStartDate()
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        """ """
    getEndDate.produce = lambda s: s.getAdjustedEndDate()
    getEndDate.convert = Conversion.datetime

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

    def getRoomBookingList(self):
        """ Reservations """
    getRoomBookingList.convert = Conversion.reservationsList
    getRoomBookingList.name = "bookedRooms"
