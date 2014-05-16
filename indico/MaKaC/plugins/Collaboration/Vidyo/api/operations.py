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

from MaKaC.plugins.Collaboration.Vidyo.common import getVidyoOptionValue, VidyoError, VidyoTools
from MaKaC.plugins.Collaboration.Vidyo.api.factory import SOAPObjectFactory
from MaKaC.plugins.Collaboration.Vidyo.api.api import AdminApi, UserApi
from MaKaC.plugins.Collaboration.ravem import RavemApi
from suds import WebFault
from MaKaC.plugins.Collaboration.base import CollaborationException
from MaKaC.common.logger import Logger


class VidyoOperations(object):
    """ This class has several class methods,
        each of which represents a high-level operation,
        which sometimes involve several actual SOAP service calls.

        The objective is to not clutter the CSBooking methods with API logic.
        None of these methods should change the Indico DB, so they should not set any value on any object.
    """

    @classmethod
    def roomWithSameOwner(cls, owner, roomName):
        # we retrieve the just created room; we need to do this because Vidyo will have
        # added extra data like the room id, the url
        searchFilter = SOAPObjectFactory.createFilter('admin', roomName)
        answer = AdminApi.getRooms(searchFilter)
        createdRooms = answer.room

        for room in createdRooms:
            if str(room.name) == roomName and str(room.ownerName) == owner:
                return room
        return None

    @classmethod
    def createRoom(cls, booking):
        """ Attempts to create a public room in Vidyo.
            Returns None on success. Will also set booking.setAccountName() if success, with the Indico & Vidyo login used successfully.
            Returns a VidyoError instance if there are problems.

            :param booking: the CSBooking object inside which we try to create the room
            :type booking: MaKaC.plugins.Collaboration.Vidyo.collaboration.CSBooking
        """
        # we extract the different parameters
        # We set the original conference id because the bookings can belong to more than one conference and being cloned
        # and it is used for the long name, we need to keep always the same confId
        confId = booking.getConference().getId()

        bookingId = booking.getId()
        roomName = booking.getBookingParamByName("roomName")
        description = booking.getBookingParamByName("roomDescription")
        owner = booking.getOwnerObject()
        pin = booking.getPin()
        moderatorPin = booking.getModeratorPin()

        #we obtain the unicode object with the proper format for the room name
        roomNameForVidyo = VidyoTools.roomNameForVidyo(roomName)
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

        # We check the moderator PIN is a 3-10 digit number
        if moderatorPin and (not moderatorPin.isdigit() or len(moderatorPin) < 3 or len(moderatorPin) > 10):
            return VidyoError("PINLength", "create")

        roomCreated = False
        loginToUse = 0

        while not roomCreated and loginToUse < len(possibleLogins):
            #we loop changing the ownerName and the extension until room is created

            newRoom = SOAPObjectFactory.createRoom(roomNameForVidyo, description, possibleLogins[loginToUse], extension, pin, moderatorPin)
            try:
                AdminApi.addRoom(newRoom)
                roomCreated = True

            except WebFault, e:
                faultString = e.fault.faultstring

                if faultString.startswith('Room exist for name'):
                    if VidyoOperations.roomWithSameOwner(possibleLogins[loginToUse], roomNameForVidyo):
                        return VidyoError("duplicatedWithOwner", "create")
                    else:
                        return VidyoError("duplicated", "create")

                elif faultString.startswith('Member not found for ownerName'):
                    loginToUse = loginToUse + 1

                elif faultString.startswith('PIN should be a 3-10 digit number'):
                        return VidyoError("PINLength", "create")

                elif faultString.startswith('Room exist for extension'):
                    extension = baseExtension + str(extensionSuffix)
                    extensionSuffix = extensionSuffix + 1
                else:
                    Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's addRoom operation got WebFault: %s""" %
                                (confId, bookingId, e.fault.faultstring))
                    raise

        #if we could not create the room, the owner did not have any Vidyo accounts
        if not roomCreated and loginToUse == len(possibleLogins):
            return VidyoError("badOwner", "create")

        # we retrieve the just created room; we need to do this because Vidyo will have
        # added extra data like the room id, the url
        searchFilter = SOAPObjectFactory.createFilter('admin', extension)
        answer = AdminApi.getRooms(searchFilter)
        createdRooms = answer.room

        for room in createdRooms:
            if str(room.extension) == extension:
                return room
        return None

    @classmethod
    def attachRoom(cls, booking):
        owner = booking.getOwnerObject()
        possibleLogins = VidyoTools.getAvatarLoginList(owner)
        if not possibleLogins:
            return VidyoError("userHasNoAccounts", "attach")
        roomName = booking.getBookingParamByName("roomName")
        searchFilter = SOAPObjectFactory.createFilter('admin', roomName)

        # TODO: Do several calls if needed
        # Vidyo should have an exact match feature too
        searchFilter.limit = 100

        answer = AdminApi.getRooms(searchFilter)
        createdRooms = answer.room

        for room in createdRooms:
            for login in possibleLogins:
                if str(room.name) == roomName and str(room.ownerName) == login:
                    return room
        else:
            return VidyoError("notValidRoom", "attach")

    @classmethod
    def modifyRoom(cls, booking, oldBookingParams):

        # we extract the different parameters
        # We set the original conference id because the bookings can belong to more than one conference and being cloned
        # and it is used for the long name, we need to keep always the same confId
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        roomId = booking.getRoomId()
        roomName = booking.getBookingParamByName("roomName")
        description = booking.getBookingParamByName("roomDescription")
        newOwner = booking.getOwnerObject() #an avatar object
        ownerAccountName = booking.getOwnerAccount() #a str
        oldOwner = oldBookingParams["owner"] #an IAvatarFossil fossil
        pin = booking.getPin()
        moderatorPin = booking.getModeratorPin()

        #we obtain the unicode object with the proper format for the room name
        roomNameForVidyo = VidyoTools.roomNameForVidyo(roomName)
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
                raise CollaborationException(_("The moderator has no login information"))

        # We check the moderator PIN is a 3-10 digit number
        if moderatorPin and (not moderatorPin.isdigit() or len(moderatorPin) < 3 or len(moderatorPin) > 10):
            return VidyoError("PINLength", "modify")

        roomModified = False
        loginToUse = 0
        while not roomModified and (useOldAccountName or loginToUse < len(possibleLogins)):

            if not useOldAccountName:
                ownerAccountName = possibleLogins[loginToUse]

            newRoom = SOAPObjectFactory.createRoom(roomNameForVidyo, description, ownerAccountName, booking.getExtension(), pin, moderatorPin)
            try:
                AdminApi.updateRoom(roomId, newRoom)
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

                elif faultString.startswith('PIN should be a 3-10 digit number'):
                        return VidyoError("PINLength", "modify")

                else:
                    Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's updateRoom operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
                    raise

        #if we could not create the room, the owner did not have any Vidyo accounts
        if not roomModified and loginToUse == len(possibleLogins):
            return VidyoError("badOwner", "modify")


        # we retrieve the just created room; we need to do this because Vidyo will have
        # added extra data like the room id, the url
        try:
            modifiedRoom = AdminApi.getRoom(roomId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "modify")
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's getRoom operation got WebFault: %s""" %
                            (confId, bookingId, e.fault.faultstring))
                raise

        return modifiedRoom

    @classmethod
    def setAutomute(cls, booking):
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        roomId = booking.getRoomId()
        autoMute = booking.getBookingParamByName("autoMute")

        try:
            AdminApi.setAutomute(roomId, autoMute)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "setAutomute")
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's setAutomute operation got WebFault: %s""" %
                            (confId, bookingId, e.fault.faultstring))

    @classmethod
    def getAutomute(cls, booking):
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        roomId = booking.getRoomId()

        try:
            return AdminApi.getAutomute(roomId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "getAutomute")
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's getAutomute operation got WebFault: %s""" %
                            (confId, bookingId, e.fault.faultstring))
    @classmethod
    def setModeratorPIN(cls, booking):
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        roomId = booking.getRoomId()
        moderatorPIN = booking.getModeratorPin()

        try:
            AdminApi.setModeratorPIN(roomId, moderatorPIN)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "setModeratorPIN")
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's setModeratorPIN operation got WebFault: %s""" %
                            (confId, bookingId, e.fault.faultstring))

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
            adminApiRoom = AdminApi.getRoom(roomId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "checkStatus")
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's getRoom operation got WebFault: %s""" %
                            (confId, bookingId, e.fault.faultstring))
                raise

        return adminApiRoom

    @classmethod
    def deleteRoom(cls, booking, roomId):
        confId = booking.getConference().getId()
        bookingId = booking.getId()

        try:
            AdminApi.deleteRoom(roomId)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('Room not found for roomID'):
                return VidyoError("unknownRoom", "delete")
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's deleteRoom operation got WebFault: %s""" %
                            (confId, bookingId, e.fault.faultstring))
                raise

    @classmethod
    def connectRoom(cls, booking, roomId, query):
        confId = booking.getConference().getId()
        bookingId = booking.getId()
        try:
            searchFilter = SOAPObjectFactory.createFilter('user', query)
            userApiAnswer = UserApi.search(searchFilter)
            if userApiAnswer.total == 0:
                return VidyoError("noExistsRoom", "connect", _("The conference room is not registered in the vidyo service. ") + VidyoTools.getContactSupportText())
            legacyMember = userApiAnswer.Entity[0].entityID
            AdminApi.connectRoom(roomId, legacyMember)
        except WebFault, e:
            faultString = e.fault.faultstring
            if faultString.startswith('ConferenceID is invalid'):
                return VidyoError("unknownRoom", "connect")
            elif (faultString.startswith('Failed to Invite to Conference') or
                  faultString.startswith('Status of invited member is not Online')):
                message = _("The connection has failed. ") + VidyoTools.getContactSupportText()
                return VidyoError("connectFailed", "connect", message)
            else:
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s, Admin API's connectRoom operation got WebFault: %s""" %
                        (confId, bookingId, e.fault.faultstring))
                raise

    @classmethod
    def disconnectRoom(cls, booking, connectionStatus, roomIp="", roomPanoramaUser=""):
        serviceType = connectionStatus.get("service")
        # roomName should be empty if we are forcing disconnection (otherwise we'd be sending the wrong name and
        # disconnetion would fail)
        if connectionStatus.get("roomName") == booking.getBookingParamByName("roomName"):
            roomName = booking.getBookingParamByName("roomName")
        else:
            roomName = ""
        try:
            if roomIp != "":
                answer = RavemApi.disconnectLegacyEndpoint(roomIp, serviceType, roomName)
            else:
                answer = RavemApi.disconnectVidyoPanorama(roomPanoramaUser, serviceType, roomName)
            if not answer.ok or "error" in answer.json():
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s,
                                              Ravem API's disconnect operation not successfull: %s""" %
                                              (booking.getConference().getId(), booking.getId(), answer.text))
                return VidyoError("disconnectFailed", "disconnect",
                                  _("Vidyo was unable to disconnect the conference room. {0}").format(VidyoTools.getContactSupportText()))
        except Exception:
            return VidyoError("disconnectFailed", "disconnect",
                              _("Vidyo was unable to disconnect the conference room. {0}").format(VidyoTools.getContactSupportText()))

    @classmethod
    def isRoomConnected(cls, booking, roomIp="", roomPanoramaUser=""):
        try:
            if roomIp != "":
                answer = RavemApi.isLegacyEndpointConnected(roomIp)
            else:
                answer = RavemApi.isVidyoPanoramaConnected(roomPanoramaUser)
            if not answer.ok or "error" in answer.json():
                Logger.get('Vidyo').exception("""Evt:%s, booking:%s,
                                              Ravem API's isConnected operation not successfull: %s""" %
                                              (booking.getConference().getId(), booking.getId(), answer.text))
                return VidyoError("roomCheckFailed", "roomConnected",
                                  _("There was a problem obtaining the room status from Vidyo. {0}").format(VidyoTools.getContactSupportText()))
            result = {"roomName": None, "isConnected": False, "service": None}
            answer = answer.json()
            if "result" in answer:
                for service in answer.get("result").get("services"):
                    if service.get("name", "") == "videoconference":
                        result["roomName"] = VidyoTools.recoverVidyoName(service.get("event_name"))
                        result["isConnected"] = service.get("status") == 1
                        result["service"] = VidyoTools.recoverVidyoDescription(service.get("event_type"))
            return result
        except Exception:
            return VidyoError("roomCheckFailed", "roomConnected",
                              _("There was a problem obtaining the room status from Vidyo. {0}").format(
                                    VidyoTools.getContactSupportText()))

    @classmethod
    def searchRooms(cls, query, offset=None, limit=None):
        try:
            search_filter = SOAPObjectFactory.createFilter('admin', "%%%s%%" % VidyoTools.replaceSpacesInName(query))

            if offset is not None:
                search_filter.start = offset
            if limit is not None:
                search_filter.limit = limit

            rooms = AdminApi.getRooms(search_filter)

            if rooms.total:
                return rooms.room
            return []

        except WebFault, e:
            Logger.get('Vidyo').exception("""Admin API's searchRooms operation got WebFault: %s"""
                                          % e.fault.faultstring)
            raise
