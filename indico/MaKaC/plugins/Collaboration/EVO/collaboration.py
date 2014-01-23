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

from datetime import timedelta

from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import nowutc, unixTimeToDatetime
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.EVO.common import EVOControlledException, getEVOAnswer, parseEVOAnswer, EVOException, \
    getMinStartDate, getMaxEndDate, OverlappedError, EVOError, ChangesFromEVOError, getRequestURL, EVOWarning, getEVOOptionValueByName
from MaKaC.plugins.Collaboration.EVO.mail import NewEVOMeetingNotificationAdmin, EVOMeetingModifiedNotificationAdmin, EVOMeetingRemovalNotificationAdmin
from MaKaC.common.mail import GenericMailer
from MaKaC.common.logger import Logger
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.EVO.fossils import ICSBookingConfModifFossil,\
    ICSBookingIndexingFossil
from MaKaC.common.fossilize import fossilizes
from indico.util.date_time import format_datetime

class CSBooking(CSBookingBase): #already Fossilizable
    fossilizes(ICSBookingConfModifFossil, ICSBookingIndexingFossil)

    _hasTitle = True
    _hasStart = True
    _hasStop = False
    _hasCheckStatus = True

    _requiresServerCallForStart = True
    _requiresClientCallForStart = True

    _needsBookingParamsCheck = True
    _needsToBeNotifiedOnView = True

    _hasEventDisplay = True

    _commonIndexes = ["All Videoconference"]

    _simpleParameters = {
        "communityId": (str, ''),
        "meetingTitle": (str, ''),
        "meetingDescription": (str, None),
        "sendMailToManagers": (bool, False),
        "type": (int, 0),
        "displayPhoneBridgeId": (bool, True),
        "displayPassword": (bool, False),
        "displayPhonePassword": (bool, False),
        "displayPhoneBridgeNumbers": (bool, True),
        "displayURL": (bool, True)}

    _complexParameters = ["communityName", "accessPassword", "hasAccessPassword"]

    def __init__(self, type, conf):
        CSBookingBase.__init__(self, type, conf)
        self._accessPassword = None
        self._EVOID = None
        self._url = None
        self._phoneBridgeId = None
        self._phoneBridgePassword = None

        self._created = False
        self._error = False
        self._errorMessage = None
        self._errorDetails = None
        self._changesFromEVO = []

        self._lastCheck = nowutc()
        self._checksDone = []

    def getCommunityName(self):
        try:
            return self.getPluginOptionByName("communityList").getValue()[self._bookingParams["communityId"]]
        except KeyError:
            return _("Non-existant community")

    def getAccessPassword(self):
        """ This method returns the access password that will be displayed in the indico page
        """
        if self._accessPassword is None:
            return ""
        else:
            return self._accessPassword

    def setAccessPassword(self, accessPassword):
        if accessPassword.strip() == "":
            self._accessPassword = None
        else:
            self._accessPassword = accessPassword

    def getHasAccessPassword(self):
        return self._accessPassword is not None

    def getUrl(self):
        if self._url.startswith("meeting"): #the first part of the URL is not there
            self._url = getEVOOptionValueByName("koalaLocation") + '?' + self._url
        return self._url

    def getPhoneBridgeId(self):
        if not hasattr(self, '_phoneBridgeId'):
            self._phoneBridgeId = None
        return self._phoneBridgeId

    def getPhoneBridgePassword(self):
        if not hasattr(self, '_phoneBridgePassword'):
            self._phoneBridgePassword = None
        return self._phoneBridgePassword

    def getErrorMessage(self):
        return self._errorMessage

    def getErrorDetails(self):
        return self._errorDetails

    def getChangesFromEVO(self):
        return self._changesFromEVO

    def getLastCheck(self):
        if not hasattr(self, "_lastCheck"): #TODO: remove when safe
            self._lastCheck = nowutc()
            self._checksDone = []
        return self._lastCheck

    ## overriding methods
    def _getTitle(self):
        return self._bookingParams["meetingTitle"]


    def _checkBookingParams(self):
        if self._bookingParams["communityId"] not in self._EVOOptions["communityList"].getValue(): #change when list of community names is ok
            raise EVOException("communityId parameter (" + str(self._bookingParams["communityId"]) +" ) does not correspond to one of the available communities for booking with id: " + str(self._id))

        if len(self._bookingParams["meetingTitle"].strip()) == 0:
            raise EVOException("meetingTitle parameter (" + str(self._bookingParams["meetingTitle"]) +" ) is empty for booking with id: " + str(self._id))

        if len(self._bookingParams["meetingDescription"].strip()) == 0:
            raise EVOException("meetingDescription parameter (" + str(self._bookingParams["meetingDescription"]) +" ) is empty for booking with id: " + str(self._id))

        if self._startDate > self._endDate:
            raise EVOException("Start date of booking cannot be after end date. Booking id: " + str(self._id))

        allowedStartMinutes = self._EVOOptions["allowedPastMinutes"].getValue()
        if self.getAdjustedStartDate('UTC')  < (nowutc() - timedelta(minutes = allowedStartMinutes )):
            raise EVOException("Cannot create booking before the past %s minutes. Booking id: %s"% (allowedStartMinutes, str(self._id)))

        minStartDate = getMinStartDate(self.getConference())
        if self.getAdjustedStartDate() < minStartDate:
            raise EVOException("Cannot create a booking %s minutes before the Indico event's start date. Please create it after %s"%(self._EVOOptions["extraMinutesBefore"].getValue(), formatDateTime(minStartDate)))

        maxEndDate = getMaxEndDate(self.getConference())
        if self.getAdjustedEndDate() > maxEndDate:
            raise EVOException("Cannot create a booking %s minutes after before the Indico event's end date. Please create it before %s"%(self._EVOOptions["extraMinutesAfter"].getValue(), formatDateTime(maxEndDate)))

        if False: #for now, we don't detect overlapping
            for booking in self.getBookingsOfSameType():
                if self._id != booking.getId():
                    if not ((self._startDate < booking.getStartDate() and self._endDate <= booking.getStartDate()) or
                            (self._startDate >= booking.getEndDate() and self._endDate > booking.getEndDate())):
                        return OverlappedError(booking)

        return False


    def _create(self):
        """ Creates a booking in the EVO server if all conditions are met.
        """
        arguments = self.getCreateModifyArguments()

        try:
            requestURL = getRequestURL("create", arguments)
            answer = getEVOAnswer("create", arguments, self.getConference().getId(), self._id)

            returnedAttributes = parseEVOAnswer(answer)

            self._EVOID = returnedAttributes["meet"]
            self._url = returnedAttributes["url"]
            self._phoneBridgeId = returnedAttributes.get("phone", None)
            self._phoneBridgePassword = returnedAttributes.get("phonepass", None)

            self.bookingOK()

#            if self._bookingParams["sendMailToManagers"]:
#                try:
#                    notification = NewEVOMeetingNotificationManager(self)
#                    GenericMailer.sendAndLog(notification, self.getConference(),
#                                             "MaKaC/plugins/Collaboration/EVO/collaboration.py",
#                                             self.getConference().getCreator())
#                except Exception,e:
#                    Logger.get('EVO').error(
#                        """Could not send NewEVOMeetingNotificationManager for booking with id %s , exception: %s""" % (self._id, str(e)))


        except EVOControlledException, e:
            if e.message == "ALREADY_EXIST":
                return EVOError('duplicated', str(requestURL))
            if e.message == "START_IN_PAST":
                return EVOError('start_in_past', str(requestURL))
            else:
                raise EVOException(_("The booking could not be created due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)



    def _modify(self, oldBookingParams):
        """ Modifies a booking in the EVO server if all conditions are met.
        """
        if self._created:
            arguments = self.getCreateModifyArguments()
            arguments["meet"] = self._EVOID

            try:
                requestURL = getRequestURL("modify", arguments)
                answer = getEVOAnswer("modify", arguments, self.getConference().getId(), self._id)
                returnedAttributes = parseEVOAnswer(answer)

                self._EVOID = returnedAttributes["meet"]
                self._url = returnedAttributes["url"]
                self._phoneBridgeId = returnedAttributes.get("phone", None)
                self._phoneBridgePassword = returnedAttributes.get("phonepass", None)

                self.bookingOK()

#                if self._bookingParams["sendMailToManagers"]:
#                    try:
#                        notification = EVOMeetingModifiedNotificationManager(self)
#                        GenericMailer.sendAndLog(notification, self.getConference(),
#                                             "MaKaC/plugins/Collaboration/EVO/collaboration.py",
#                                             self.getConference().getCreator())
#                    except Exception,e:
#                        Logger.get('EVO').error(
#                            """Could not send EVOMeetingModifiedNotificationManager for booking with id %s , exception: %s""" % (self._id, str(e)))


            except EVOControlledException, e:
                if e.message == "ALREADY_EXIST":
                    return EVOError('duplicated', str(requestURL))
                if e.message == "START_IN_PAST":
                    return EVOError('start_in_past', str(requestURL))
                if e.message == "UNKNOWN_MEETING":
                    return EVOError('deletedByEVO', str(requestURL), _('This EVO meeting could not be modified because it was deleted in the EVO system'))
                if e.message == "END_BEFORE_START":
                    return EVOError('end_before_start', str(requestURL),
                                    _("This EVO meeting could not be moved because it would have been resulting in the end date being before the start date"))

                raise EVOException(_("The booking could not be modified due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)

        else:
            self._create()

    def _start(self):
        """ Starts an EVO meeting.
            A last check on the EVO server is performed.
        """
        self._checkStatus()
        if self.canBeStarted():
            self._permissionToStart = True

    def canBeDeleted(self):
        return not (self.isHappeningNow() or self.hasHappened())

    def _canBeNotifiedOfEventDateChanges(self):
        return not self.hasHappened()

    def needsToBeNotifiedOfDateChanges(self):
        """ Returns if this booking in particular needs to be notified
            of their owner Event changing start date, end date or timezone.
        """
        if self.hasHappened():
            return False
        else:
            return self._needsToBeNotifiedOfDateChanges

    def _notifyOnView(self):
        """ This method is called every time that the user sees a booking.
            It will check the booking status according to the times defined in the 'verifyMinutes' option.
            If a check must be done, the EVO Server will be contacted.
        """
        checksToDo = [timedelta(minutes = int(minutes)) for minutes in self._EVOOptions["verifyMinutes"].getValue()]
        checksToDo.sort()

        remainingTime = self.getAdjustedStartDate('UTC') - nowutc()

        for index, check in enumerate(checksToDo):
            if remainingTime < check and not check in self._checksDone:
                self._checkStatus()
                self._checksDone.extend(checksToDo[index:])
                break

    def _checkStatus(self):
        if self._created:
            arguments = {"meet": self._EVOID}
            try:
                requestURL = getRequestURL("getInfo", arguments)
                answer = getEVOAnswer("getInfo", arguments , self.getConference().getId(), self._id)
                returnedAttributes = parseEVOAnswer(answer)

                self.assignAttributes(returnedAttributes)

            except EVOControlledException, e:
                if e.message == "UNKNOWN_MEETING":
                    return EVOError('deletedByEVO', str(requestURL))
                else:
                    raise EVOException(_("Information could not be retrieved due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)

    def _delete(self):
        if self._created:
            arguments = {"meet": self._EVOID}
            try:
                requestURL = getRequestURL("delete", arguments)
                getEVOAnswer("delete", arguments, self.getConference().getId(), self._id)

#                if self._bookingParams["sendMailToManagers"]:
#                    try:
#                        notification = EVOMeetingRemovalNotificationManager(self)
#                        GenericMailer.sendAndLog(notification, self.getConference(),
#                                             "MaKaC/plugins/Collaboration/EVO/collaboration.py",
#                                             self.getConference().getCreator())
#                    except Exception,e:
#                        Logger.get('EVO').error(
#                            """Could not send EVOMeetingRemovalNotificationManager for booking with id %s , exception: %s""" % (self._id, str(e)))

            except EVOControlledException, e:
                if e.message == "DELETE_MEETING_OVER":
                    return EVOError('cannotDeleteOld', str(requestURL))
                if e.message == "DELETE_MEETING_ONGOING":
                    return EVOError('cannotDeleteOngoing', str(requestURL))
                if e.message == "DELETE_MEETING_NO_ID":
                    self._warning = EVOWarning('cannotDeleteNonExistant')
                else:
                    raise EVOException(_("The booking could not be deleted due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)

        self._error = False


    def _getLaunchDisplayInfo(self):
        return {'launchText' : _("Join Now!"),
                'launchLink' : str(self.getUrl()),
                'launchTooltip': _("Click here to join the EVO meeting!") if self.canBeStarted() else _('This meeting starts on %s so you cannot join it yet')%format_datetime(self.getStartDate())}

    ## end of overrigind methods

    def getCreateModifyArguments(self):
        arguments = {
            "title" : self._bookingParams["meetingTitle"],
            "desc" : self._bookingParams["meetingDescription"],
            "start": int(self.getStartDateTimestamp() * 1000), #milliseconds
            "end": int(self.getEndDateTimestamp() * 1000), #milliseconds
            "type": 0,
            "com": self._bookingParams["communityId"]
        }
        if self.getHasAccessPassword():
            arguments["pwd"] = self._accessPassword
        else:
            arguments["pwd"] = ''

        return arguments

    def assignAttributes(self, attributes):

        verboseKeyNames = {
            "meet": "EVO Meeting ID",
            "url": "Koala URL",
            "title": "Title",
            "desc": "Description",
            "start": "Start time",
            "end": "End time",
            "type": "Meeting type",
            "com": "Community",
            "phone": "Phone Bridge ID",
            "phonepass": "Phone Bridge password"
        }

        oldArguments = self.getCreateModifyArguments()
        oldArguments["phone"] = self.getPhoneBridgeId()
        if self.getHasAccessPassword():
            oldArguments["phonepass"] = self.getPhoneBridgePassword()

        changesFromEVO = []

        for key in oldArguments:
            if (not key in attributes or attributes[key] != str(oldArguments[key])) and key in verboseKeyNames:
                changesFromEVO.append(verboseKeyNames[key])

        self._changesFromEVO = changesFromEVO

        self._EVOID = attributes["meet"]
        self._url = attributes["url"]
        self._phoneBridgeId = attributes.get("phone", None)
        self._phoneBridgePassword = attributes.get("phonepass", None)

        self._bookingParams["meetingTitle"] = attributes["title"]
        self._bookingParams["meetingDescription"] = attributes["desc"]
        self.setStartDate(unixTimeToDatetime(int(attributes["start"]) / 1000.0, "UTC"))
        self.setEndDate(unixTimeToDatetime(int(attributes["end"]) / 1000.0, "UTC"))
        self._bookingParams["type"] = attributes["type"]
        self._bookingParams["communityId"] = attributes["com"]

        if changesFromEVO:
            return ChangesFromEVOError(changesFromEVO)

    def bookingOK(self):
        self._created = True

    def _sendMail(self, operation):
        """
        Overloads _sendMail behavior for EVO
        """

        if operation == 'new':
            try:
                notification = NewEVOMeetingNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('EVO').error(
                    """Could not send NewEVOMeetingNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

        elif operation == 'modify':
            try:
                notification = EVOMeetingModifiedNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('EVO').error(
                    """Could not send EVOMeetingModifiedNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

        elif operation == 'remove':
            try:
                notification = EVOMeetingRemovalNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('EVO').error(
                    """Could not send EVOMeetingRemovalNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

