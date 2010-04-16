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

from MaKaC.plugins.Collaboration.Vidyo.common import getVidyoOptionValue, VidyoError, VidyoTools
from MaKaC.plugins.Collaboration.Vidyo.api.factory import SOAPObjectFactory
from MaKaC.plugins.Collaboration.Vidyo.api.api import AdminApi, UserApi
from suds import WebFault


class VidyoOperations(object):
    """ This class has several class methods,
        each of which represents a high-level operation,
        which sometimes involve several actual SOAP service calls.

        The objective is to not clutter the CSBooking methods with API logic.
        None of these methods should change the Indico DB, so they should not set any value on any object.
    """

    @classmethod
    def createRoom(cls, booking):
        """ Attempts to create a public room in Vidyo.
            Returns None on success. Will also set booking.setAccountName() if success, with the Indico & Vidyo login used successfully.
            Returns a VidyoError instance if there are problems.

            :param booking: the CSBooking object inside which we try to create the room
            :type booking: MaKaC.plugins.Collaboration.Vidyo.collaboration.CSBooking
        """
        #we extract the different parameters
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        roomName = booking.getBookingParamByName("roomName")
        description = booking.getBookingParamByName("roomDescription")
        owner = booking.getOwnerObject()
        pin = booking.getPin()

        #we obtain the unicode object with the proper format for the room name
        roomNameForVidyo = VidyoTools.roomNameForVidyo(roomName, confId)
        if isinstance(roomNameForVidyo, VidyoError):
            return roomNameForVidyo

        #we turn the description into a unicode object
        description = VidyoTools.descriptionForVidyo(description)
        if isinstance(description, VidyoError):
            return description

        #we obtain the most probable extension
        #TODO: there's a length limit for extensions, check this
        baseExtension = getVidyoOptionValue("prefix") + confId
        extension = baseExtension
        extensionSuffix = 1

        #we produce the list of possible account names. We will loop through them to attempt to create the room
        possibleLogins = VidyoTools.getAvatarLoginList(owner)
        if not possibleLogins:
            return VidyoError("userHasNoAccounts", "create")

        roomCreated = False
        loginToUse = 0
        while not roomCreated and loginToUse < len(possibleLogins):
            #we loop changing the ownerName and the extension until room is created

            newRoom = SOAPObjectFactory.createRoom(roomNameForVidyo, description, possibleLogins[loginToUse], extension, pin)
            try:
                AdminApi.addRoom(newRoom, confId, bookingId)
                roomCreated = True

            except WebFault, e:
                faultString = e.fault.faultstring

                if faultString.startswith('Room exist for name'):
                    return VidyoError("duplicated", "create")

                elif faultString.startswith('Member not found for ownerName'):
                    loginToUse = loginToUse + 1

                elif faultString.startswith('Room exist for extension'):
                    extension = baseExtension + str(extensionSuffix)
                    extensionSuffix = extensionSuffix + 1
                else:
                    raise e

        #if we could not create the room, the owner did not have any Vidyo accounts
        if not roomCreated and loginToUse == len(possibleLogins):
            return VidyoError("badOwner", "create")

        # we retrieve the just created room; we need to do this because Vidyo will have
        # added extra data like the room id, the url
        searchFilter = SOAPObjectFactory.createFilter('admin', extension)
        answer = AdminApi.getRooms(searchFilter, confId, bookingId)
        createdRooms = answer.room

        for room in createdRooms:
            if str(room.extension) == extension:
                return room

        return None


    @classmethod
    def modifyRoom(cls, booking, oldBookingParams):

        #we extract the different parameters
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        roomId = booking.getRoomId()
        roomName = booking.getBookingParamByName("roomName")
        description = booking.getBookingParamByName("roomDescription")
        newOwner = booking.getOwnerObject() #an avatar object
        ownerAccountName = booking.getOwnerAccount() #a str
        oldOwner = oldBookingParams["owner"] #an IAvatarFossil fossil
        pin = booking.getPin()

        #we obtain the unicode object with the proper format for the room name
        roomNameForVidyo = VidyoTools.roomNameForVidyo(roomName, confId)
        if isinstance(roomNameForVidyo, VidyoError):
            return roomNameForVidyo

        #we turn the description into a unicode object
        description = VidyoTools.descriptionForVidyo(description)
        if isinstance(description, VidyoError):
            return description

        #(the extension will not change)

        #we check if the owner has changed. If not, we reuse the same accountName
        useOldAccountName = True
        possibleLogins = []
        if newOwner.getId() != oldOwner["id"]:
            useOldAccountName = False
            #we produce the list of possible account names. We will loop through them to attempt to create the room
            possibleLogins = VidyoTools.getAvatarLoginList(newOwner)
            if not possibleLogins:
                return VidyoError("userHasNoAccounts", "modify")


        roomModified = False
        loginToUse = 0
        while not roomModified and (useOldAccountName or loginToUse < len(possibleLogins)):

            if not useOldAccountName:
                ownerAccountName = possibleLogins[loginToUse]

            newRoom = SOAPObjectFactory.createRoom(roomNameForVidyo, description, ownerAccountName, booking.getExtension(), pin)
            try:
                AdminApi.updateRoom(roomId, newRoom, confId, bookingId)
                roomModified = True

            except WebFault, e:
                faultString = e.fault.faultstring

                if faultString.startswith('Room not exist for roomID'):
                    return VidyoError("unknownRoom", "modify")

                elif faultString.startswith('Room exist for name'):
                    return VidyoError("duplicated", "modify")

                elif faultString.startswith('Member not found for ownerName'):
                    if useOldAccountName:
                        #maybe the user was deleted between the time the room was created and now
                        return VidyoError("badOwner", "modify")
                    else:
                        loginToUse = loginToUse + 1

                else:
                    raise e

        #if we could not create the room, the owner did not have any Vidyo accounts
        if not roomModified and loginToUse == len(possibleLogins):
            return VidyoError("badOwner", "modify")


        # we retrieve the just created room; we need to do this because Vidyo will have
        # added extra data like the room id, the url
        try:
            modifiedRoom = AdminApi.getRoom(roomId, confId, bookingId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "modify")

        return modifiedRoom


    @classmethod
    def queryRoom(cls, booking, roomId):
        """ Searches for room information via the admin api's getRoom function and the
            user api's search function (currently the admin api's getRoom is not reliable
            to retrieve name, description and groupName).
            Tries to find the room providing the extension as query (since only
            the room name and extension are checked by the search op).
            Returns None if not found
        """
        confId = booking.getConference().getId()
        bookingId = booking.getId()

        roomId = booking.getRoomId()

        try:
            adminApiRoom = AdminApi.getRoom(roomId, confId, bookingId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "checkStatus")
            else:
                raise e

        extension = str(adminApiRoom.extension)

        searchFilter = SOAPObjectFactory.createFilter('user', extension)
        userApiAnswer = UserApi.search(searchFilter, confId, bookingId)
        foundEntities = userApiAnswer.Entity

        userApiRoom = None
        for entity in foundEntities:
            if str(entity.extension) == extension and str(entity.entityID) == roomId:
                userApiRoom = entity

        return (adminApiRoom, userApiRoom)


    @classmethod
    def deleteRoom(cls, booking, roomId):
        confId = booking.getConference().getId()
        bookingId = booking.getId()

        try:
            AdminApi.deleteRoom(roomId, confId, bookingId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "delete")
            else:
                raise e

