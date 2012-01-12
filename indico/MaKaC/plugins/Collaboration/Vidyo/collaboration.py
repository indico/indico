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

from MaKaC.common.fossilize import fossilizes, fossilize
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoException, VidyoError, \
    FakeAvatarOwner, VidyoTools, getVidyoOptionValue
import MaKaC.plugins.Collaboration.Vidyo.mail as notifications
from MaKaC.user import AvatarHolder, Avatar
from MaKaC.plugins.Collaboration.Vidyo.api.operations import VidyoOperations
from MaKaC.plugins.Collaboration.Vidyo.fossils import ICSBookingConfModifFossil, \
    ICSBookingIndexingFossil
from MaKaC.common.utils import unicodeLength
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.logger import Logger
from MaKaC.common.mail import GenericMailer
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from MaKaC.plugins.Collaboration.Vidyo.pages import ServiceInformation
from MaKaC.conference import Contribution, Session

class CSBooking(CSBookingBase):
    fossilizes(ICSBookingConfModifFossil, ICSBookingIndexingFossil)

    _hasTitle = True
    _hasStart = True
    _hasStop = False
    _hasConnect = True
    _hasCheckStatus = True

    _hasStartDate = False
    _canBeNotifiedOfEventDateChanges = False

    _requiresServerCallForStart = False
    _requiresClientCallForStart = True

    _requiresServerCallForConnect = True
    _requiresClientCallForConnect = False

    _needsBookingParamsCheck = True
    _needsToBeNotifiedOnView = True

    _hasEventDisplay = True

    _commonIndexes = ["All Videoconference"]

    _simpleParameters = {
        "roomName": (str, ''),
        "roomDescription": (str, ''),
        "displayPin": (bool, False),
        "displayURL": (bool, True),
        "displayPhoneNumbers": (bool, True),
        "videoLinkType": (str, 'event'),
        "videoLinkContribution": (str, ''),
        "videoLinkSession": (str, '')}

    _complexParameters = ["pin", "hasPin", "owner"]


    def __init__(self, bookingType, conf):
        CSBookingBase.__init__(self, bookingType, conf)
        self._pin = None
        self._owner = None
        self._ownerVidyoAccount = None
        self._roomId = None
        self._extension = None
        self._url = None
        self._created = False
        self._checksDone = []

    ## setters and getters for complex params and internal params ##

    def canBeStarted(self):
        return self._created

    def canBeStopped(self):
        return False

    def canBeConnected(self):
        return self._created and VidyoTools.getLinkRoomIp(self.getLinkObject())!=""

    def canBeDeleted(self):
        return True

    def getPin(self):
        """ This method returns the PIN that will be displayed in the indico page
        """
        return self._pin

    def setPin(self, pin):
        if not pin or pin.strip() == "":
            self._pin = ""
        else:
            self._pin = pin

    def getHasPin(self):
        return self._pin is not None and len(self._pin) > 0

    def setHasPin(self, value):
        #ignore, will be called only on rollback
        pass

    def getOwner(self):
        """ Returns the owner, fossilized, so that it is used by the collaboration core
        """
        return fossilize(self._owner) #will use either IAvatarFossil or  IFakeAvatarOwnerFossil

    def getOwnerObject(self):
        return self._owner

    def setOwner(self, owner):
        """ Sets the owner of this public room
            :param owner: The owner of this public room. Can be a fossilized avatar, an Avatar or a FakeAvatarOwner object
            _type owner: dict, Avatar or FakeAvatarOwner
        """
        if type(owner) is dict and owner["_type"] == "Avatar":
            self._owner = AvatarHolder().getById(owner["id"])
        elif isinstance(owner, Avatar) or type(owner) is FakeAvatarOwner:
            self._owner = owner

    def getOwnerAccount(self):
        """ Returns the string used as Vidyo account for this room
        """
        return self._ownerVidyoAccount

    def setOwnerAccount(self, ownerAccount, updateAvatar = False):
        """ Sets the Vidyo account used.
            Also will try to update the _owner Avatar attribute depending on how it is called.
        """
        self._ownerVidyoAccount = ownerAccount
        if updateAvatar:
            avatar = VidyoTools.getAvatarByAccountName(ownerAccount)
            if avatar:
                self._owner = avatar
            else:
                self._owner = FakeAvatarOwner(ownerAccount)

    def getLinkVideoText(self):
        return self._generateLinkVideoText()

    def getLinkVideoRoomLocation(self):
        linkObject = self.getLinkObject()
        return linkObject.getRoom().getName() if linkObject and linkObject.getRoom() else ""

    def getEndDate(self):
        """ Returns the end date of the link object
        """
        linkObject = self.getLinkObject()
        return linkObject.getEndDate()

    def getStartDate(self):
        """ Returns the start date of the link object
        """
        linkObject = self.getLinkObject()
        return linkObject.getStartDate()

    def getRoomId(self):
        """ The Viydo internal room id for this booking
        """
        return self._roomId

    def setRoomId(self, roomId):
        """ The Viydo internal room id for this booking
        """
        self._roomId = roomId

    def getExtension(self):
        return self._extension

    def setExtension(self, extension):
        self._extension = extension

    def getURL(self):
        return self._url

    def setURL(self,url):
        self._url = url

    def isCreated(self):
        """ Returns if the room exists in Vidyo or not
        """
        return self._created

    def setCreated(self, created):
        """ Set if the room exists in Vidyo or not
        """
        self._created = created

    def getChecksDone(self):
        if not hasattr(self, "_checksDone"):
            self._checksDone = []
        return self._checksDone

    def setChecksDone(self, checksDone):
        self._checksDone = checksDone

    def getBookingInformation(self):
        """ For retreiving the ServiceInformation sections dict built for the
            Event Header, delegated here for use with Vidyo only at this time.
            If event linking is required for other video services, this will
            need to be moved to parent or some other mechanism implemented.
        """
        return ServiceInformation().getInformation(self, True)

    ## overriding methods
    def _getTitle(self):
        return self._bookingParams["roomName"]


    def _checkBookingParams(self):

        if len(self._bookingParams["roomName"].strip()) == 0:
            raise VidyoException("roomName parameter (" + str(self._bookingParams["roomName"]) + " ) is empty for Vidyo booking with id: " + str(self._id))
        elif unicodeLength(self._bookingParams["roomName"]) > VidyoTools.maxRoomNameLength(self._conf):
            return VidyoError("nameTooLong")
        else:
            if not VidyoTools.verifyRoomName(self._bookingParams["roomName"]):
                return VidyoError("invalidName")
            else:
                self._bookingParams["roomName"] = VidyoTools.replaceSpacesInName(self._bookingParams["roomName"])

        if len(self._bookingParams["roomDescription"].strip()) == 0:
            raise VidyoException("roomDescription parameter (" + str(self._bookingParams["roomDescription"]) + " ) is empty for Vidyo booking with id: " + str(self._id))

        if self._pin:
            try:
                int(self._pin)
            except ValueError:
                raise VidyoException("pin parameter (" + str(self._pin) + ") is not an integer for Vidyo booking with id: " + str(self._id))

        return False

    def getLinkObject(self):
        import re

        if self.getLinkId():
            sessId = re.search('(?<=s)\d+', self._linkVideoId)
            slotId = re.search('(?<=l)\d+', self._linkVideoId)
            contId = re.search('(?<=t)\d+', self._linkVideoId)
        else:
            return self._conf

        linkObject = self._conf
        if contId:
            linkObject = self._conf.getContributionById(contId.group())
        elif sessId:
            session = self._conf.getSessionById(sessId.group())
            if session is not None:
                linkObject = session.getSlotById (slotId.group())
        return linkObject

    def _generateLinkVideoText(self):
        linkVideoText = ""

        if self.hasSessionOrContributionLink():
            title = ""

            linkObject = self.getLinkObject()
            if linkObject is None:
                return _("Removed %s")%_("contribution") if self.isLinkedToContribution() else _("session")
            if self.isLinkedToContribution() and isinstance(linkObject, Contribution):
                title = linkObject.getTitle()
                linkVideoText = title + " (" + self._linkVideoType + ")"
            elif self.isLinkedToSession() and isinstance(linkObject, Session):
                title = linkObject.getSession().getTitle() + (" - " + linkObject.getTitle() if linkObject.getTitle() else "")
                linkVideoText = title + " (" + self._linkVideoType + ")"
            else:
                linkVideoText = _("Link removed")
        else:
            linkVideoText = _("Whole event")

        return linkVideoText

    def _create(self):
        """ Creates the Vidyo public room that will be associated to this CSBooking,
            based on the booking params.
            After creation, it also retrieves some more information from the newly created room.
            Returns None if success.
            Returns a VidyoError if there is a problem, such as the name being duplicated.
        """
        result = ExternalOperationsManager.execute(self, "createRoom", VidyoOperations.createRoom, self)
        if isinstance(result, VidyoError):
            return result

        else:
            # Link to a Session or Contribution if requested
            self._roomId = str(result.roomID) #we need to convert values read to str or there will be a ZODB exception
            self._extension = str(result.extension)
            self._url = str(result.RoomMode.roomURL)
            self.setOwnerAccount(str(result.ownerName))
            self.setBookingOK()
            VidyoTools.getEventEndDateIndex().indexBooking(self)


    def _modify(self, oldBookingParams):
        """ Modifies the Vidyo public room in the remote system
        """
        result = ExternalOperationsManager.execute(self, "modifyRoom", VidyoOperations.modifyRoom, self, oldBookingParams)
        if isinstance(result, VidyoError):
            if result.getErrorType() == 'unknownRoom':
                self.setBookingNotPresent()
            return result
        else:
            self._extension = str(result.extension)
            self._url = str(result.RoomMode.roomURL)
            self.setOwnerAccount(str(result.ownerName))
            self.setBookingOK()

            if oldBookingParams["owner"]["id"] != self.getOwnerObject().getId():
                self._sendNotificationToOldNewOwner(oldBookingParams["owner"])


    def _notifyOnView(self):
        """ Will get called when manager sees list of bookings in management interface,
            or user sees bookings in event display list.
            If the room is still considered as being present in Vidyo,
            and we should do a programmed check, we do it.
            We do not do checks if the room was already marked as non present
            or if there are no more checks to do.
        """
        pass


    def notifyEventDateChanges(self, oldStartDate, newStartDate, oldEndDate, newEndDate):
        """ Moves the booking in the old bookings index
        """
        VidyoTools.getEventEndDateIndex().moveBooking(self, oldEndDate)

    def _connect(self):
        self._checkStatus()
        if self.canBeConnected():
            confRoomIp = VidyoTools.getLinkRoomIp(self.getLinkObject())
            if confRoomIp == "":
                return VidyoError("noValidConferenceRoom", "connect")
            prefixConnect = getVidyoOptionValue("prefixConnect")
            result = ExternalOperationsManager.execute(self, "connectRoom", VidyoOperations.connectRoom, self, self._roomId, prefixConnect + confRoomIp)
            if isinstance(result, VidyoError):
                return result
            return self

    def _checkStatus(self):
        """ Queries the data for the Vidyo Public room associated to this CSBooking
            and updates the locally stored data.
            When API problems are solved, uncomment and test the commented code.
            The User API call of VidyoOperations.queryRoom will not be necessary any more.
        """
        result = VidyoOperations.queryRoom(self, self._roomId)
        if isinstance(result, VidyoError):
            self.setBookingNotPresent()
            return result

        else:
            adminApiResult = result[0]
            userApiResult = result[1]

            recoveredVidyoName = VidyoTools.recoverVidyoName(userApiResult.displayName)
            if recoveredVidyoName:
                self._bookingParams["roomName"] = recoveredVidyoName
            else:
                self._warning = "invalidName"
            self._extension = str(adminApiResult.extension)

            if bool(adminApiResult.RoomMode.hasPin):
                self._pin = str(adminApiResult.RoomMode.roomPIN)
            else:
                self._pin = ""

            self._url = str(adminApiResult.RoomMode.roomURL)
            self.setOwnerAccount(str(adminApiResult.ownerName), updateAvatar = True)

            # no description returned in User API and Admin API's getRoom returns a bad value. Great
            #recoveredDescription = VidyoTools.recoverVidyoDescription(adminApiResult.description)
            #if recoveredDescription:
            #    self._bookingParams["roomDescription"] = recoveredDescription
            #else:
            #    self._warning = "invalidDescription"

            # no groupName returned in User API and Admin API's getRoom returns a bad value. Great
            # if str(adminApiResult.groupName) != getVidyoOptionValue("indicoGroup"):
            #     return VidyoError("invalidGroup", "checkStatus")


    def _delete(self, fromDeleteOld = False):
        """ Deletes the Vidyo Public room associated to this CSBooking, based on the roomId
            Returns None if success.
            If trying to delete a non existing room, there will be a message in self._warning
            so that it is caught by Main.js's postDelete function.
        """
        result = ExternalOperationsManager.execute(self, "deleteRoom", VidyoOperations.deleteRoom, self, self._roomId)

        if isinstance(result, VidyoError):
            if result.getErrorType() == "unknownRoom" and result.getOperation() == "delete":
                if not fromDeleteOld:
                    self._warning = "cannotDeleteNonExistant"
            else:
                return result

        if not fromDeleteOld:
            VidyoTools.getEventEndDateIndex().unindexBooking(self)


    def _getLaunchDisplayInfo(self):
        return {'launchText' : _("Join Now!"),
                'launchLink' : str(self.getURL()),
                'launchTooltip': _("Click here to join the Vidyo room!")}

    def getStatusMessage(self):
        """ Returns the status message as a string.
            This attribute will be available in Javascript with the "statusMessage"
        """
        status = self.getPlayStatus()
        if not self._created:
            return _("Room no longer exists")
        elif status == None:
                return _("Public room created")
        elif status:
            return _("Conference started")
        elif not status:
            return _("Conference stopped")

    ## end of overriding methods

    def setBookingOK(self):
        """ Changes some of the booking's attributes when the room has been properly created
        """
        self._created = True

    def setBookingNotPresent(self):
        """ Changes some of the booking's attributes when the room is still in the Indico DB
            but not in the remote system any more.
        """
        self._created = False
        #booking is not present remotely so no need to delete it later
        VidyoTools.getEventEndDateIndex().unindexBooking(self)

    def _sendNotificationToOldNewOwner(self, oldOwner):

        #notification to new owner
        if isinstance(self.getOwnerObject(), Avatar):
            try:
                notification = notifications.VidyoOwnerChosenNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                     self.getConference().getCreator())

            except Exception, e:
                Logger.get('Vidyo').error(
                    """Could not send VidyoOwnerChosenNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

        #notification to old owner
        if oldOwner["_type"] == "Avatar":
            try:
                oldOwnerAvatar = AvatarHolder().getById(oldOwner["id"])
                if oldOwnerAvatar:
                    notification = notifications.VidyoOwnerRemovedNotification(self, oldOwnerAvatar)
                    GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                     self.getConference().getCreator())

            except Exception, e:
                Logger.get('Vidyo').error(
                    """Could not send VidyoOwnerRemovedNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))


    def _sendMail(self, operation):
        """
        Overloads _sendMail behavior for EVO
        """

        if operation == 'new':
            #notification to admin
            try:
                notification = notifications.NewVidyoPublicRoomNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                     self.getConference().getCreator())
            except Exception, e:
                Logger.get('Vidyo').error(
                    """Could not send NewVidyoPublicRoomNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

            #notification to owner
            if isinstance(self.getOwnerObject(), Avatar):
                try:
                    notification = notifications.VidyoOwnerChosenNotification(self)
                    GenericMailer.sendAndLog(notification, self.getConference(),
                                         "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                         self.getConference().getCreator())

                except Exception, e:
                    Logger.get('Vidyo').error(
                        """Could not send VidyoOwnerChosenNotification for booking with id %s of event with id %s, exception: %s""" %
                        (self.getId(), self.getConference().getId(), str(e)))

            #notification to admin if too many rooms in index
            if VidyoTools.needToSendCleaningReminder():
                try:
                    notification = notifications.VidyoCleaningNotification(self)
                    GenericMailer.send(notification)
                except Exception, e:
                    Logger.get('Vidyo').error(
                        """Could not send VidyoCleaningNotification for booking with id %s of event with id %s, exception: %s""" %
                        (self.getId(), self.getConference().getId(), str(e)))


        elif operation == 'modify':
            #notification to admin
            try:
                notification = notifications.VidyoPublicRoomModifiedNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                     self.getConference().getCreator())
            except Exception, e:
                Logger.get('Vidyo').error(
                    """Could not send VidyoPublicRoomModifiedNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))


        elif operation == 'remove':
            #notification to admin
            try:
                notification = notifications.VidyoPublicRoomRemovalNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                     "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                     self.getConference().getCreator())
            except Exception, e:
                Logger.get('Vidyo').error(
                    """Could not send VidyoPublicRoomRemovalNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

            #notification to owner
            if isinstance(self.getOwnerObject(), Avatar):
                try:
                    notification = notifications.VidyoRoomDeletedOwnerNotification(self)
                    GenericMailer.sendAndLog(notification, self.getConference(),
                                         "MaKaC/plugins/Collaboration/Vidyo/collaboration.py",
                                         self.getConference().getCreator())
                except Exception, e:
                    Logger.get('Vidyo').error(
                        """Could not send VidyoRoomDeletedOwnerNotification for booking with id %s of event with id %s, exception: %s""" %
                        (self.getId(), self.getConference().getId(), str(e)))


    def clone ( self, conf):
        """
        Clones a CSBooking from an existing.

        conf: the conference to put the CSBooking
        """
        cs = CSBooking(self.getType(),conf)
        cs.setBookingParams(self.getBookingParams())
        cs.setId(self.getId())
        cs.setWarning(self.getWarning())
        cs.setStartDate(self.getStartDate())
        cs.setEndDate(self.getEndDate())
        cs.setCanBeDeleted(self.canBeDeleted())
        cs.setHidden(self.isHidden())
        cs.setPin(self.getPin())
        cs.setOwnerAccount(self.getOwnerAccount())
        cs.setRoomId(self.getRoomId())
        cs.setExtension(self.getExtension())
        cs.setURL(self.getURL())
        cs.setChecksDone(self.getChecksDone())
        cs.setCreated(self.isCreated())
        cs.setLinkType(self.getLinkIdDict())
        return cs
