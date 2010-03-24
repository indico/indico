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

from datetime import timedelta
from MaKaC.common.PickleJar import Retrieves
from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import nowutc, unixTimeToDatetime
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.EVO.common import EVOControlledException, getEVOAnswer, parseEVOAnswer, EVOException, \
    getMinStartDate, getMaxEndDate, OverlappedError, EVOError, getRequestURL, EVOWarning, getEVOOptionValueByName
from MaKaC.plugins.Collaboration.EVO.mail import NewEVOMeetingNotificationAdmin, EVOMeetingModifiedNotificationAdmin, EVOMeetingRemovalNotificationAdmin
#    NewEVOMeetingNotificationManager, EVOMeetingModifiedNotificationManager,\
#    EVOMeetingRemovalNotificationManager
from MaKaC.common.mail import GenericMailer
from MaKaC.common.logger import Logger
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.collaborationTools import MailTools

class CSBooking(CSBookingBase):

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

    _simpleParamaters = {
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

    @Retrieves(['MaKaC.plugins.Collaboration.EVO.collaboration.CSBooking'], 'url')
    def getURL(self):
        if self._url.startswith("meeting"): #the first part of the URL is not there
            self._url = getEVOOptionValueByName("koalaLocation") + '?' + self._url
        return self._url

    @Retrieves(['MaKaC.plugins.Collaboration.EVO.collaboration.CSBooking'], 'phoneBridgeId')
    def getPhoneBridgeId(self):
        if not hasattr(self, '_phoneBridgeId'):
            self._phoneBridgeId = None
        return self._phoneBridgeId

    @Retrieves(['MaKaC.plugins.Collaboration.EVO.collaboration.CSBooking'], 'phoneBridgePassword')
    def getPhoneBridgePassword(self):
        if not hasattr(self, '_phoneBridgePassword'):
            self._phoneBridgePassword = None
        return self._phoneBridgePassword


    def isDisplayPhoneBridgeId(self):
        if not "displayPhoneBridgeId" in self._bookingParams:
            self._bookingParams["displayPhoneBridgeId"] = True
        return self._bookingParams["displayPhoneBridgeId"]

    def isDisplayPassword(self):
        if not "displayPassword" in self._bookingParams:
            self._bookingParams["displayPassword"] = False
        return self._bookingParams["displayPassword"]

    def isDisplayPhoneBridgePassword(self):
        if not "displayPhonePassword" in self._bookingParams:
            self._bookingParams["displayPhonePassword"] = False
        return self._bookingParams["displayPhonePassword"]

    def isDisplayPhoneBridgeNumbers(self):
        if not "displayPhoneBridgeNumbers" in self._bookingParams:
            self._bookingParams["displayPhoneBridgeNumbers"] = True
        return self._bookingParams["displayPhoneBridgeNumbers"]

    def isDisplayURL(self):
        if not "displayURL" in self._bookingParams:
            self._bookingParams["displayURL"] = False
        return self._bookingParams["displayURL"]


    @Retrieves(['MaKaC.plugins.Collaboration.EVO.collaboration.CSBooking'], 'errorMessage')
    def getErrorMessage(self):
        return self._errorMessage

    @Retrieves(['MaKaC.plugins.Collaboration.EVO.collaboration.CSBooking'], 'errorDetails')
    def getErrorDetails(self):
        return self._errorDetails

    @Retrieves(['MaKaC.plugins.Collaboration.EVO.collaboration.CSBooking'], 'changesFromEVO')
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
            raise EVOException("Cannot create a booking %s minutes before the Indico event's start date. Please create it after %s"%(self._EVOOptions["allowedMinutes"].getValue(), formatDateTime(minStartDate)))

        maxEndDate = getMaxEndDate(self.getConference())
        if self.getAdjustedEndDate() > maxEndDate:
            raise EVOException("Cannot create a booking %s minutes after before the Indico event's end date. Please create it before %s"%(self._EVOOptions["allowedMinutes"].getValue(), formatDateTime(maxEndDate)))

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
            self.checkCanStart()

            if MailTools.needToSendEmails('EVO'):
                try:
                    notification = NewEVOMeetingNotificationAdmin(self)
                    GenericMailer.sendAndLog(notification, self.getConference(),
                                         "MaKaC/plugins/Collaboration/EVO/collaboration.py",
                                         self.getConference().getCreator())
                except Exception,e:
                    Logger.get('EVO').error(
                        """Could not send NewEVOMeetingNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                        (self.getId(), self.getConference().getId(), str(e)))

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


    def _modify(self):
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
                self.checkCanStart()

                if MailTools.needToSendEmails('EVO'):
                    try:
                        notification = EVOMeetingModifiedNotificationAdmin(self)
                        GenericMailer.sendAndLog(notification, self.getConference(),
                                             "MaKaC/plugins/Collaboration/EVO/collaboration.py",
                                             self.getConference().getCreator())
                    except Exception,e:
                        Logger.get('EVO').error(
                            """Could not send EVOMeetingModifiedNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                            (self.getId(), self.getConference().getId(), str(e)))

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
                    return EVOError('deletedByEVO', str(requestURL), 'This EVO meeting could not be modified because it was deleted in the EVO system')

                raise EVOException(_("The booking could not be modified due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)

        else:
            self._create()

    def _start(self):
        """ Starts an EVO meeting.
            A last check on the EVO server is performed.
        """
        self._checkStatus()
        if self._canBeStarted:
            self._permissionToStart = True

    def _notifyOnView(self):
        """ This method is called every time that the user sees a booking.
            It will check the booking status according to the times defined in the 'verifyMinutes' option.
            If a check must be done, the EVO Server will be contacted.
        """
        checksToDo = [timedelta(minutes = int(minutes)) for minutes in self._EVOOptions["verifyMinutes"].getValue()]
        checksToDo.sort()

        remainingTime = self.getAdjustedStartDate('UTC') - nowutc()

        checkDone = False

        for index, check in enumerate(checksToDo):
            if remainingTime < check and not check in self._checksDone:
                self._checkStatus()
                self._checksDone.extend(checksToDo[index:])
                checkDone = True
                break

        if not checkDone:
            self.checkCanStart()

    def _checkStatus(self):
        if self._created:
            arguments = {"meet": self._EVOID}
            try:
                requestURL = getRequestURL("getInfo", arguments)
                answer = getEVOAnswer("getInfo", arguments , self.getConference().getId(), self._id)
                returnedAttributes = parseEVOAnswer(answer)

                self.assignAttributes(returnedAttributes)
                self.checkCanStart()

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

                if MailTools.needToSendEmails('EVO'):
                    try:
                        notification = EVOMeetingRemovalNotificationAdmin(self)
                        GenericMailer.sendAndLog(notification, self.getConference(),
                                             "MaKaC/plugins/Collaboration/EVO/collaboration.py",
                                             self.getConference().getCreator())
                    except Exception,e:
                        Logger.get('EVO').error(
                            """Could not send EVOMeetingRemovalNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                            (self.getId(), self.getConference().getId(), str(e)))

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
                'launchLink' : str(self.getURL()),
                'launchTooltip': _("Click here to join the EVO meeting!")}

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

        self.checkCanStart()

    def bookingOK(self):
        self._statusMessage = _("Booking created")
        self._statusClass = "statusMessageOK"
        self._created = True

    def checkCanStart(self, changeMessage = True):
        if self._created:
            now = nowutc()
            self._canBeDeleted = True
            self._canBeNotifiedOfEventDateChanges = CSBooking._canBeNotifiedOfEventDateChanges
            if self.getStartDate() < now and self.getEndDate() > now:
                self._canBeStarted = True
                self._canBeDeleted = False
                if changeMessage:
                    self._statusMessage = _("Ready to start!")
                    self._statusClass = "statusMessageOK"
            else:
                self._canBeStarted = False
                if now > self.getEndDate() and changeMessage:
                    self._canBeDeleted = False
                    self._statusMessage = _("Already took place")
                    self._statusClass = "statusMessageOther"
                    self._needsToBeNotifiedOfDateChanges = False
                    self._canBeNotifiedOfEventDateChanges = False
                elif changeMessage:
                    self.bookingOK()
