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


from MaKaC.plugins.Collaboration.base import CollaborationException, CSErrorBase
from persistent import Persistent
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.plugins.Collaboration.Vidyo.fossils import IVidyoErrorFossil, \
    IFakeAvatarOwnerFossil
from MaKaC.i18n import _
import re
from MaKaC.authentication.AuthenticationMgr import AuthenticatorMgr
from MaKaC.plugins.Collaboration.Vidyo.indexes import EventEndDateIndex, BOOKINGS_BY_VIDYO_ROOMS_INDEX
from MaKaC.common.timezoneUtils import nowutc
from datetime import timedelta
from MaKaC.common.logger import Logger
from MaKaC.rb_location import CrossLocationQueries, CrossLocationDB
from MaKaC.common import info
from indico.core.index import Catalog



def getVidyoOptionValue(optionName):
    """ Shortcut to return the value of a Vidyo option
    """
    return CollaborationTools.getOptionValue('Vidyo', optionName)


class VidyoTools(object):
    """ Several utility functions, related to API arguments / result processing,
        Vidyo user <-> Avatar translation, and the old booking Index
    """

    __vidyoRoomNameRE = None
    __vidyoRecoverNameRE = None

    @classmethod
    def defaultRoomName(cls, conf):
        title = conf.getTitle()
        # Ensure first character is not a number or non-alphanumerical character (underscore is fine)
        title = re.compile(ur"^[\W\d]$", re.UNICODE).sub('_', title)
        # Get rid of everything else that's not allowed
        title = re.compile(ur"[^\w._\- ]|'$", re.UNICODE).sub('_', title)
        return cls.replaceSpacesInName(title)[:cls.maxRoomNameLength()]

    @classmethod
    def maxRoomNameLength(cls):
        suffix = cls.roomNameForVidyo('')
        return 61 - len(suffix)

    @classmethod
    def roomNameForVidyo(cls, roomName):
        """ We apply the _indico_ suffix
            and we turn the name into an unicode object, since suds
            works with either ascii-encoded str objects or unicode objects
            (not utf-8 encoded str objects), and the name may have unicode chars
        """
        try:
            return roomName.decode('utf-8')
        except UnicodeDecodeError:
            return VidyoError("invalidName")

    @classmethod
    def descriptionForVidyo(cls, description):
        """ We turn the name into an unicode object, since suds
            works with either ascii-encoded str objects or unicode objects
            (not utf-8 encoded str objects) and the description may have unicode chars
        """
        try:
            return description.decode('utf-8')
        except UnicodeDecodeError:
            return VidyoError("invalidDescription")

    @classmethod
    def verifyRoomName(cls, name):
        """ Checks if a room name entered by an Indico user is valid
            We must check that the name starts by an alphanumeric character,
            and that it does not contain punctuation except periods (.), underscores (_) or dashes (\-).
            It can have spaces (they will be converted to underscores when sent to Vidyo)
            Returns True or False
        """
        if not cls.__vidyoRoomNameRE:
            cls.__vidyoRoomNameRE = re.compile(ur"^[^\W\d][\w._\- ]*$", re.UNICODE) #re.UNICODE to accept é, ñ, 漢字 ...

        try:
            unicodeName = name.decode('utf-8') #unicodeName will be a unicode object
        except UnicodeDecodeError:
            return False

        return bool(cls.__vidyoRoomNameRE.match(unicodeName))

    @classmethod
    def replaceSpacesInName(cls, name):
        return name.replace(" ", "_")

    @classmethod
    def recoverVidyoName(cls, name):
        """ Recovers the name given by an Indico user to a Public Room.
            Example: when the user created the room, he entered "Hello Kitty" which was turned into
            "Hello_Kitty_indico_5423"
            This function turns "Hello_Kitty_indico_5423" back into "Hello_Kitty" (note: the _ are not turned back into spaces).
            The value returned is always a utf-8 encoded str object.
        """
        try:
            name = str(name)
            name = unicode(name)
            name = name.encode('utf-8')
        except UnicodeEncodeError:
            return None
        return name

    @classmethod
    def recoverVidyoDescription(cls, description):
        try:
            description = str(description)
        except UnicodeEncodeError:
            try:
                description = unicode(description)
                description = description.encode('utf-8')
            except UnicodeEncodeError:
                return None

        return description

    @classmethod
    def getAvatarLoginList(cls, avatar):
        loginList = []
        for authenticatorId in getVidyoOptionValue("authenticatorList"):
            loginList.extend([identity.getLogin() for identity in avatar.getIdentityByAuthenticatorId(authenticatorId)])
        return loginList

    @classmethod
    def getAvatarByAccountName(cls, accountName):
        """
        Retrieves the first avatar found using the authenticators in the
        authenticatorList option (order is respected)
        """
        availableAuths = getVidyoOptionValue("authenticatorList")
        foundAvatarDict = AuthenticatorMgr().getAvatarByLogin(accountName, availableAuths)

        for authName in availableAuths:
            foundAvatar = foundAvatarDict.get(authName, None)
            if foundAvatar:
                return foundAvatar
        else:
            return None

    @classmethod
    def getEventEndDateIndex(cls):
        """ Will return the EventEndDateIndex instance
            and will initialize it, if it does not exist.
        """
        return CollaborationTools.getGlobalData("Vidyo").getEventEndDateIndex()

    @classmethod
    def needToSendCleaningReminder(cls):
        """ Returns if we need to send a notification to the admins
            reminding them that it is time to clean the old rooms.
            We do it the first time we exceed the maximum number and then
            again everytime we exceed another 10%
        """
        baseAmount = getVidyoOptionValue("cleanWarningAmount")
        increment = max(baseAmount / 10, 1)
        currentCount = cls.getEventEndDateIndex().getCount()
        return currentCount >= baseAmount and (currentCount - baseAmount) % increment == 0

    @classmethod
    def getBookingsOldDate(cls):
        """ Returns a datetime object, with UTC timezone, before which Vidyo
            rooms are considered "old" (we look at the end date of the event
            the booking is attached to)
        """
        return nowutc() - timedelta(days = getVidyoOptionValue("maxDaysBeforeClean"))

    @classmethod
    def getLinkRoomAttribute(cls, linkVideo, attName="H323 IP"):
        if linkVideo is None:
            return ""
        location = linkVideo.getLocation()
        room = linkVideo.getRoom()
        roomAttribute = ""
        if location and room and location.getName() and room.getName() and location.getName().strip() and room.getName().strip():
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            if minfo.getRoomBookingModuleActive():
                CrossLocationDB.connect()
                try:
                    roomInfo = CrossLocationQueries.getRooms(location=location.getName(), roomName=room.getName())
                    roomAttribute = roomInfo.customAtts[attName]
                except Exception, e:
                    Logger.get("Vidyo").warning("Location: '%s' - Problem with CrossLocationQueries: '%s'" % (location.getName(), str(e)))
        return roomAttribute

    @classmethod
    def getContactSupportText(cls):
        contactSupport = ""
        if getVidyoOptionValue("contactSupport"):
            contactSupport += _("""\nPlease contact %s for help.""") % getVidyoOptionValue("contactSupport")
        return contactSupport

    @classmethod
    def getIndexByVidyoRoom(cls):
        return Catalog.getIdx(BOOKINGS_BY_VIDYO_ROOMS_INDEX)


class FakeAvatarOwner(Persistent, Fossilizable):
    """ Used when a Vidyo admin changes the owner of a room to an account
        that cannot be translated to an Avatar
    """
    fossilizes(IFakeAvatarOwnerFossil)

    def __init__(self, accountName):
        self._accountName = accountName

    @classmethod
    def getId(cls):
        return None

    def getName(self):
        return self._accountName
    getStraightFullName = getName


class VidyoError(CSErrorBase):
    """ Object to be returned by operations that capture an expectable problem,
        such as a duplicate name for a room, etc.
    """
    fossilizes(IVidyoErrorFossil)

    def __init__(self, errorType, operation = None, userMessage = None):
        CSErrorBase.__init__(self)
        self._errorType = errorType
        self._operation = operation
        self._userMessage = userMessage

    def getErrorType(self):
        return self._errorType

    def getOperation(self):
        return self._operation

    def getUserMessage(self):
        """ This is actually only used to display messages to the user
            when there's a change in the event and the plugin is notified
            (such as when the event changes dates, etc).
        """
        if self._userMessage:
            return self._userMessage
        else:
            if self._errorType == "duplicated":
                return _("This Public room could not be created or changed because Vidyo considers the resulting public room name as duplicated.")

            elif self._errorType == "duplicatedWithOwner":
                return _("""There is already a room with this name in the system. Would you like to attach it to this event?""")

            elif self._errorType == "PINLength":
                return _("""The PIN for the vidyo room has to be a 3-10 digit number.""")

            elif self._errorType == "badOwner":
                return _("This Public room could not be created or changed because the specified moderator does not have a Vidyo account.")

            elif self._errorType == "unknownRoom" and self._operation == "delete":
                return _("This Public room could not be deleted because it did not exist.")

            elif self._errorType == "unknownRoom" and self._operation == "modify":
                return _("It was not possible to modify this Vidyo room because it does not exist anymore.")

            elif self._errorType == "unknownRoom" and self._operation == "checkStatus":
                return _("It was not possible to retrieve information about this Vidyo room.")

            elif self._errorType == "invalidGroup" and self._operation == "checkStatus":
                return _("It was not possible to retrieve information about this Vidyo room because its group is no longer ") + getVidyoOptionValue("indicoGroup")

            elif self._errorType == "invalidName":
                return _("That room name is not valid; it may contain illegal characters.")

            elif self._errorType == "invalidDescription":
                return _("That description is not valid; it may contain illegal characters.")

            elif self._errorType == "nameTooLong":
                return _("That room name is not valid; it cannot have more than 61 characters.")

            elif self._errorType == "userHasNoAccounts":
                return _("The user selected as owner has no login information")

            elif self._errorType == "notValidRoom" and self._operation == "attach":
                return _("Either there is no room with this name or you are not its owner. Please select another one.")

            else:
                return self._errorType

    def getLogMessage(self):
        return "Vidyo Error: " + str(self._errorType) + " for operation " + str(self._operation)


class VidyoException(CollaborationException):
    """ Exception to be thrown when unexpected problems happen
        (such as a parameter having an incorrect value even if the interface should have checked it)
    """
    def __init__(self, msg, inner = None):
        CollaborationException.__init__(self, msg, 'Vidyo', inner)

class VidyoConnectionException(VidyoException):
    """ Exception to be thrown when there are connection problems to Vidyo
        (bad url, no network, incorrect login)
    """
    def __init__(self, innerException):
        VidyoException.__init__(self, "Could not connect to Vidyo, reason: " + str(innerException), innerException)


class GlobalData(Persistent):
    """ Place where the plugin stores server-wide data.
        Stores the old booking index.
    """

    def __init__(self):
        self._endDateIndex = EventEndDateIndex()

    def getEventEndDateIndex(self):
        return self._endDateIndex
