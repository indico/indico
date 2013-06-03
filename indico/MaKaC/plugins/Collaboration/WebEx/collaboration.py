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
"""
This file contains the bulk of the logic for the WebEx plugin.
The main functions like create, modify and delete are
defined in here.
"""

import xml.dom.minidom
import re
from time import strptime
from datetime import timedelta, datetime

from MaKaC.common.timezoneUtils import nowutc, naive2local, getAdjustedDate
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.WebEx.common import getMinStartDate, getMaxEndDate,\
    Participant, sendXMLRequest, WebExError, getWebExOptionValueByName, makeTime, findDuration, unescape
from MaKaC.plugins.Collaboration.WebEx.api.operations import WebExOperations
from MaKaC.common.logger import Logger
from MaKaC.i18n import _
from MaKaC.common.Counter import Counter
from MaKaC.plugins.Collaboration.WebEx.mail import NewWebExMeetingNotificationAdmin, \
    WebExMeetingModifiedNotificationAdmin, WebExMeetingRemovalNotificationAdmin, \
  WebExParticipantNotification
from MaKaC.plugins.Collaboration.WebEx.fossils import ICSBookingIndexingFossil, ICSBookingConfModifFossil
from MaKaC.common.fossilize import fossilizes, fossilize
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from indico.util.date_time import format_datetime

from cgi import escape

class CSBooking(CSBookingBase):
    """
    The class to hold the WebEx video bookings
    """
    fossilizes(ICSBookingConfModifFossil, ICSBookingIndexingFossil)

    _hasTitle = True
    _hasStart = True
    _hasStop = False
    _hasCheckStatus = True

    _requiresServerCallForStart = True
    _requiresClientCallForStart = True

    _needsBookingParamsCheck = True
    _needsToBeNotifiedOnView = True
    _canBeNotifiedOfEventDateChanges = True
    _allowMultiple = True

    _hasEventDisplay = True

    _commonIndexes = ["All Videoconference"]

    _simpleParameters = {
            "meetingTitle": (str, ''),
            "meetingDescription": (str, None),
            "webExUser":(str, None),
            "sendAttendeesEmail":(bool, True),
            "sendCreatorEmail":(bool, False),
            "sendSelfEmail":(bool, False),
            "loggedInEmail":(str, ''),
            "showAccessPassword":(bool,False),
            "session": (str,""),
            "seeParticipants": (bool, True),
            "enableChat": (bool, True),
            "joinBeforeHost": (bool,True),
            "joinBeforeTime":(str,"900"),
    }
    _complexParameters = ["accessPassword", "hasAccessPassword", "participants", "webExPass" ]

    def __init__(self, type, conf):
        CSBookingBase.__init__(self, type, conf)
        self._participants = {}
        self._participantIdCounter = Counter(1)
        self._accessPassword = None
        self._url = None # The URL to join the meeting
        self._startURL = None  #The URL the admin can visit to start the meeting and be automatically logged in
        self._webExKey = None
        self._phoneNum = None
        self._phoneNumToll = None
        self._duration = None
        self._permissionToStart = True

        self._created = False
        self._error = False
        self._errorMessage = None
        self._errorDetails = None

        self._lastCheck = nowutc()
        self._checksDone = []
        self._bookingChangesHistory = []
        self._latestChanges = []
        self._webExPass = ""

    def getParticipantList(self, sorted = False):
        if sorted:
            keys = self._participants.keys()
            keys.sort()
            return [self._participants[k] for k in keys]
        else:
            return self._participants.values()

    def getParticipants(self):
        return fossilize(self.getParticipantList(sorted = True))

    def getSessionId(self):
        if self._bookingParams.has_key( 'session' ):
            return self._bookingParams["session"]

    def setParticipants(self, participants):
        participantsCopy = dict(self._participants)
        self._participants = {}
        for p in participants:
            id = p.get("participantId", None)
            if id is None or not id in participantsCopy:
                id = self._participantIdCounter.newCount()
            participantObject = Participant(self, id, p)
            self._participants[id] = participantObject

    def getAccessPassword(self):
        """ This method returns the access password that will be displayed in the indico page
        """
        if self._accessPassword is None:
            return ""
        else:
            return self._accessPassword

    def getWebExPass(self):
        return self._webExPass

    def setWebExPass(self, webExPass):
        self._webExPass = webExPass


    def setAccessPassword(self, accessPassword):
        if accessPassword.strip() == "":
            self._accessPassword = None
        else:
            self._accessPassword = accessPassword

    def setHasAccessPassword(self, value=False):
        return value

    def getHasAccessPassword(self):
        return self._accessPassword is not None

    def getUrl(self):
        return self._url

    def getPhoneNum(self):
        return self._phoneNum

    def getPhoneNumToll(self):
        return self._phoneNumToll

    def getJoinBeforeHost(self):
        params = self.getBookingParams()
        if not params.has_key('joinBeforeHost'): # or params['joinBeforeHost'] != "yes":
            return "false"
        return "true"

    def getEnableChat(self):
        params = self.getBookingParams()
        if not params.has_key('enableChat'): # 'or params['enableChat'] != "yes":
            return "false"
        return "true"

    def getSeeParticipants(self):
        params = self.getBookingParams()
        if not params.has_key('seeParticipants'): # or params['seeParticipants'] != "yes":
            return "false"
        return "true"

    def getPhoneAccessCode(self):
        return re.sub(r'(\d{3})(?=\d)',r'\1 ', str(self._webExKey)[::-1])[::-1]

    def showAccessPassword(self):
        params = self.getBookingParams()
        if not params.has_key('showAccessPassword'):
            return False;
        return params["showAccessPassword"]

    def getStartURL(self):
        return self._startURL

    def getErrorMessage(self):
        return self._errorMessage

    def getWebExUser(self):
        return self._bookingParams['webExUser']

    def getDuration(self):
        return self._duration

    def getWebExKey(self):
        return self._webExKey

    def setWebExKey( self, webExKey ):
        self._webExKey = webExKey

    def getErrorDetails(self):
        return self._errorDetails

    def getChangesFromWebEx(self):
        return self._bookingChangesHistory

    def getLatestChanges(self):
        return self._latestChanges

    def getLastCheck(self):
        return self._lastCheck

    def _getTitle(self):
        return self._bookingParams["meetingTitle"]

    def _checkBookingParams(self):
        params = self.getBookingParams()
        for participant in self._participants.itervalues():
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", participant._email) == None:
                return WebExError(errorType = None, userMessage = "Participant email address (" + participant._email + ") for " + participant._firstName + " " + participant._lastName +" is invalid. ")

        if len(params["meetingTitle"].strip()) == 0:
            return WebExError(errorType = None, userMessage = _("Title cannot be left blank"))

        if len(params["webExUser"].strip()) == 0:
            return WebExError(errorType = None, userMessage = _("WebEx username is empty.  The booking cannot continue without this."))

        if len(self.getWebExPass().strip()) == 0:
            return WebExError(errorType = None, userMessage = _("WebEx password is empty.  The booking cannot continue without this."))

        if self._startDate >= self._endDate:
            return WebExError(errorType = None, userMessage = _("Start date of booking cannot be after end date."))

        return False

    def getWebExTimeZoneToUTC( self, tz_id, the_date ):
        """
        The date is required because the WebEx server
        responds with the offset of GMT time based
        on that date, adjusted for daylight savings, etc
        """
        params = self.getBookingParams()
        request_xml = """<?xml version="1.0\" encoding="UTF-8"?>
<serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:serv=\"http://www.webex.com/schemas/2002/06/service" >
<header>
  <securityContext>
    <webExID>%(username)s</webExID>
    <password>%(password)s</password>
    <siteID>%(siteID)s</siteID>
    <partnerID>%(partnerID)s</partnerID>
  </securityContext>
</header>
<body>
  <bodyContent xsi:type="site.LstTimeZone" >
    <timeZoneID>%(tz_id)s</timeZoneID>
    <date>%(date)s</date>
  </bodyContent>
</body>
</serv:message>
""" % ( { "username" : params['webExUser'], "password" : self.getWebExPass(), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "tz_id":tz_id, "date":the_date } )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        offset = dom.getElementsByTagName( "ns1:gmtOffset" )[0].firstChild.toxml('utf-8')
        try:
            return int(offset)
        except:
            Logger.get('WebEx').debug( "Eror requesting time zone offset from WebEx:\n\n%s" % ( response_xml ) )
            return None

    def bookingOK(self):
        """
        This function is called after the booking parameters are
        checked and the booking appears to have been successful.
        """
        self._statusMessage = _("Booking created")
        self._statusClass = "statusMessageOK"
        self._created = True

    def checkCanStart(self, changeMessage = True):
        if self._created:
            now = nowutc()
            self._canBeDeleted = True
            if self.getStartDate() < now and now < self.getEndDate():
                self._canBeStarted = True
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
                elif changeMessage:
                    self.bookingOK()

    def _create(self):
        """ Creates a booking in the WebEx server if all conditions are met.
        """
        params = self.getBookingParams()
        self.setAccessPassword( params['accessPassword'] )
        self._duration = findDuration( self.getStartDate(), self.getEndDate() )
        try:
            result = ExternalOperationsManager.execute(self, "createBooking", WebExOperations.createBooking, self)
        except Exception,e:
            Logger.get('WebEx').error(
                """Could not create booking with id %s of event with id %s, exception: %s""" %
                (self.getId(), self.getConference().getId(), str(e)))
            return WebExError( errorType = None, userMessage = _("""There was an error communicating with the WebEx server.  The request was unsuccessful.  Error information: %s""" % str(e)) )
        if isinstance(result, WebExError):
            return result
        #self.getLoginURL()
        #We do this because the call in number is not returned in create response
        self.bookingOK()
        self.checkCanStart()
        self._checkStatus()
        self.getLoginURL()
        self.sendParticipantsEmail('new')
        return None

    def _modify(self, oldBookingParams):
        """ Modifies a booking in the WebEx server if all conditions are met.
        """
        verboseKeyNames = {
            "meetingDescription": _("Meeting description"),
            "meetingTitle": _("Title"),
            "webExUser": _("WebEx username"),
            "webExPass": _("WebEx password"),
            "meet:meetingPassword": _("Meeting password"),
            "participants" : _("Participants"),
            "startDate" : _("Start date"),
            "endDate" : _("End date"),
            "hidden" : _("Is hidden"),
            "sendAttendeesEmail" : _("Send emails to participants"),
            "sendCreatorEmail" : _("Send emails to event managers"),
            "sendSelfEmail":_("Send user booking WebEx an email copy"),
            "showAccessPassword" : _("Show meeting password on event page"),
            "seeParticipants" : _("See participants"),
            "enableChat" : _("Participant chat"),
            "joinBeforeHost" : _("Participants can join before host"),
            "joinBeforeTime": _("Time an attendee can join a meeting before the official start time"),
            "notifyOnDateChanges" : _("Keep booking synchronized"),
            "accessPassword" : _("Meeting password"),
            "session" : _("Session")
        }
        self._latestChanges = []
        self._warning = None
        if self._created:
            params = self.getBookingParams()
            # Create entries for the keys that aren't always present
            hidden_keys = ["hidden", "notifyOnDateChanges", "sendAttendeesEmail", "sendCreatorEmail", "sendSelfEmail", "showAccessPassword", "seeParticipants", "enableChat", "joinBeforeHost", "joinBeforeTime"]
            for key in hidden_keys:
                if not params.has_key( key ):
                    params[key] = "no"
                if not oldBookingParams.has_key( key ):
                    oldBookingParams[key] = "no"
            try:
                result = ExternalOperationsManager.execute(self, "modifyBooking", WebExOperations.modifyBooking, self)
                if isinstance(result, WebExError):
                    return result
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not modify booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))
                return WebExError( errorType = None, userMessage = _("""There was an error communicating with the WebEx server.  The request was unsuccessful.  Error information: %s""" % str(e)) )
            for key in params.keys():
                    if key == "loggedInEmail":
                        continue
                    if key in hidden_keys:
                        if oldBookingParams.has_key( key ) != params.has_key( key ) or oldBookingParams[key] != params[key]:
                            self._bookingChangesHistory.append( "%s has changed." % ( verboseKeyNames[key] ) )
                            self._latestChanges.append( "%s has changed." % ( verboseKeyNames[key] ) )
                            continue
                    if oldBookingParams[key] != params[key]:
                        if key == "participants":
                            #Number of participants changed - report this
                            if len(params[key]) != len(oldBookingParams[key]):
                                self._bookingChangesHistory.append( "%s has changed." % ( verboseKeyNames[key] ) )
                                self._latestChanges.append( "%s has changed." % ( verboseKeyNames[key] ) )
                                continue
                            count = -1
                            for participant in params[key]:
                                count = count + 1
                                for participantKey in participant.keys():
                                    if participantKey=="id":
                                        continue
                                    if oldBookingParams[key][count].get(participantKey) != params[key][count].get(participantKey):
                                        self._bookingChangesHistory.append( "%s has changed." % ( verboseKeyNames[key] ) )
                                        self._latestChanges.append( "%s has changed." % ( verboseKeyNames[key] ) )
                                        break
                        else:
                            self._bookingChangesHistory.append( "%s has changed: %s" % ( verboseKeyNames[key], params[key] ) )
                            self._latestChanges.append( "%s has changed." % ( verboseKeyNames[key] ) )
            self._checkStatus()
            self.getLoginURL()
            self.sendParticipantsEmail('modify')
        else:
            return WebExError( errorType = None, userMessage = _("This video booking could not be found.") )
        return None

    def _delete(self):
        """
        This function will delete the specified video booking from the WebEx server
        """
        try:
            result = ExternalOperationsManager.execute(self, "deleteBooking", WebExOperations.deleteBooking, self)
            if isinstance(result, WebExError):
                return result
        except Exception,e:
            Logger.get('WebEx').error(
                """Could not delete booking with id %s of event with id %s, exception: %s""" %
                (self.getId(), self.getConference().getId(), str(e)))
            return WebExError( errorType = None, userMessage = _("""There was an error communicating with the WebEx server.  The request was unsuccessful.  Error information: %s""" % str(e)) )
        self.sendParticipantsEmail('delete')
        self._warning = _("The booking was deleted successfully.")


    def _start(self):
        """ Starts an WebEx meeting.
            A last check on the WebEx server is performed.
        """
        self._checkStatus()
        if self._canBeStarted:
            params = self.getBookingParams()
            request_xml = """<?xml version="1.0\" encoding="UTF-8"?>
<serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:serv=\"http://www.webex.com/schemas/2002/06/service" >
<header>
  <securityContext>
    <webExID>%(username)s</webExID>
    <password>%(password)s</password>
    <siteID>%(siteID)s</siteID>
    <partnerID>%(partnerID)s</partnerID>
  </securityContext>
</header>
<body>
  <bodyContent xsi:type="java:com.webex.service.binding.meeting.GethosturlMeeting" >
    <sessionKey>%(webExKey)s</sessionKey>
  </bodyContent>
</body>
</serv:message>
""" % ( { "username" : params['webExUser'], "password" : self.getWebExPass(), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webExKey":self.getWebExKey() } )
            try:
                response_xml = sendXMLRequest( request_xml )
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not start booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))
                self._warning = _("There was an error in sending the emails to administrators: %s" % str(e) )
            dom = xml.dom.minidom.parseString( response_xml )
            status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
            if status == "SUCCESS":
                self._startURL = dom.getElementsByTagName( "meet:hostMeetingURL" )[0].firstChild.toxml('utf-8')
            else:
                return WebExError( errorType = None, userMessage = _("There was an error attempting to get the start booking URL from the WebEx server.") )
        else:
            return WebExError( errorType = None, userMessage = _("The booking cannot be started at this time.") )
        return None

    def getLoginURL(self):
        """ Starts an WebEx meeting.
            A last check on the WebEx server is performed.
        """
        params = self.getBookingParams()
        request_xml = """<?xml version="1.0\" encoding="UTF-8"?>
<serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:serv=\"http://www.webex.com/schemas/2002/06/service" >
<header>
  <securityContext>
    <webExID>%(username)s</webExID>
    <password>%(password)s</password>
    <siteID>%(siteID)s</siteID>
    <partnerID>%(partnerID)s</partnerID>
  </securityContext>
</header>
<body>
  <bodyContent xsi:type="java:com.webex.service.binding.meeting.GetjoinurlMeeting" >
    <sessionKey>%(webExKey)s</sessionKey>
    <meetingPW>%(meetingPW)s</meetingPW>
  </bodyContent>
</body>
</serv:message>
""" % ( { "username" : params['webExUser'], "password" : self.getWebExPass(), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webExKey":self.getWebExKey(), 'meetingPW':self.getAccessPassword() } )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
        if status == "SUCCESS":
            self._url = dom.getElementsByTagName( "meet:joinMeetingURL" )[0].firstChild.toxml('utf-8').replace('&amp;','&')
        else:
            return WebExError( errorType = None, userMessage = _("There was an error attempting to get the join booking URL from the WebEx server.") )
        return None

    def _notifyOnView(self):
        """ This method is called every time that the user sees a booking.
            It will check the booking status according to the times defined in the 'verifyMinutes' option.
            If a check must be done, the WebEx Server will be contacted.
        """
        checksToDo = [timedelta(minutes = int(minutes)) for minutes in self._WebExOptions["verifyMinutes"].getValue()]
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

    def _getLaunchDisplayInfo(self):
        return {'launchText' : _("Join Now!"),
                'launchLink' : str(self.getUrl()),
                'launchTooltip': _("Click here to join the WebEx meeting!") if self.canBeStarted() else _('This meeting starts on %s so you cannot join it yet')%format_datetime(self.getStartDate())}

    def getCreateModifyArguments(self):
        arguments = {
            "meet:meetingkey": self.getWebExKey(),
            "meet:agenda": escape( self._bookingParams["meetingDescription"].replace("\n","") ),
            "meet:confName": escape( self._bookingParams["meetingTitle"] ),
            "meet:hostWebExID": self._bookingParams["webExUser"],
            "meet:startDate": makeTime( self.getAdjustedStartDate('UTC') ),
            "meet:duration": self._duration,
            "meet:meetingPassword": self.getAccessPassword(),
        }
        return arguments

    def _checkStatus(self):
        if self._created:
            params = self.getBookingParams()
            request_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
<serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
   <header>
      <securityContext>
         <webExID>%(username)s</webExID>
         <password>%(password)s</password>
         <siteID>%(siteID)s</siteID>
         <partnerID>%(partnerID)s</partnerID>
      </securityContext>
   </header>
   <body>
      <bodyContent xsi:type="java:com.webex.service.binding.meeting.GetMeeting">
         <meetingKey>%(webex_key)s</meetingKey>
      </bodyContent>
   </body>
</serv:message>

""" % { "username" : params['webExUser'], "password" : self.getWebExPass(), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webex_key": self.getWebExKey() }
            response_xml = sendXMLRequest( request_xml )
            dom = xml.dom.minidom.parseString( response_xml )
            status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
            if status != "SUCCESS":
                errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
                errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
                return WebExError( errorID, userMessage = errorReason )
            self.assignAttributes( response_xml )
        return None

    def assignAttributes(self, response_xml):
        verboseKeyNames = {
            "meet:meetingkey": "WebEx Meeting ID",
            "meet:agenda": _("Meeting description"),
            "meet:confName": _("Title"),
            "meet:hostWebExID": _("WebEx host account"),
            "meet:startDate": _("Start time"),
            "meet:duration": _("Duration"),
            "meet:meetingPassword": _("Meeting password"),
        }

        dom = xml.dom.minidom.parseString( response_xml )
        oldArguments = self.getCreateModifyArguments()
        changesFromWebEx = self._bookingChangesHistory
        latestChanges = []


        start_date = makeTime( self.getAdjustedStartDate('UTC') ).strftime( "%m/%d/%Y %H:%M:%S" )
        time_discrepancy = False
        for key in oldArguments:
            if not verboseKeyNames.has_key( key ):
                continue
            if key == "meet:startDate" or key == "meet:duration":
                if key == "meet:startDate":
                    if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != start_date:
                        time_discrepancy = True
                if key == "meet:duration":
                    if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != str(self._duration):
                        time_discrepancy = True
                        user_msg = _("Updated booking duration from ") + str(self._duration) + _(" minutes to ") + str( dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') + _(" minutes"))
                        self._duration = int( dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') )
                continue
            try:
                if unescape(dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8')) != unescape(str(oldArguments[key])) and key in verboseKeyNames:
                    changesFromWebEx.append(verboseKeyNames[key] + ": " + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))
                    latestChanges.append(verboseKeyNames[key] + ": " + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))
                    if key == "meet:confName":
                        self._bookingParams["meetingTitle"] = unescape(dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))
                    elif key == "meet:agenda":
                        self._bookingParams["meetingDescription"] = unescape(dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))

            except:
                Logger.get('WebEx').info( "caught exception on: " + key )
                pass
        self._phoneNum = dom.getElementsByTagName( "serv:tollFreeNum" )[0].firstChild.toxml('utf-8')
        self._phoneNumToll = dom.getElementsByTagName( "serv:tollNum" )[0].firstChild.toxml('utf-8')

        # We calculate the time from WebEx first assuming it is in UTC.
        # If not, we then apply the offset to keep it simple
        calc_time = naive2local( datetime( *strptime( dom.getElementsByTagName( "meet:startDate" )[0].firstChild.toxml('utf-8'), "%m/%d/%Y %H:%M:%S" )[0:7]), 'UTC' )
        tz_id = dom.getElementsByTagName( "meet:timeZoneID" )[0].firstChild.toxml('utf-8')
        # If the specified time zone is not UTC, contact WebEx
        # and find the offset from UTC we must account for
        if tz_id != 20:
            time_offset_mins = self.getWebExTimeZoneToUTC( tz_id, calc_time.strftime("%m/%d/%Y %H:%M:%S"))
            WE_time = calc_time + timedelta( minutes= -1*int( time_offset_mins ) )
            #Now that we have the REAL time, figure out if there REALLY is a time difference
            if time_discrepancy == True:
                if self._startDate != getAdjustedDate(WE_time, tz=self._conf.getTimezone()):
                    self._startDate = getAdjustedDate(WE_time, tz=self._conf.getTimezone())
                    changesFromWebEx.append(_("Updated start time to match WebEx entry"))
                    latestChanges.append(_("Updated start time to match WebEx entry"))
                if self._endDate != getAdjustedDate(WE_time, tz=self._conf.getTimezone()) + timedelta( minutes=int( self._duration ) ):
                    self._endDate = getAdjustedDate(WE_time, tz=self._conf.getTimezone()) + timedelta( minutes=int( self._duration ) )
                    changesFromWebEx.append(_("Updated end time to match WebEx entry"))
                    latestChanges.append(_("Updated start time to match WebEx entry"))
        self.checkCanStart()
        self._bookingChangesHistory = changesFromWebEx
        self._latestChanges = latestChanges

    def sendParticipantsEmail(self, operation):
        params = self.getBookingParams()
        try:
            if params.has_key('sendAttendeesEmail') and params['sendAttendeesEmail'][0].lower() == 'yes':
                recipients = []
                for k in self._participants.keys():
                    recipients.append( self._participants[k]._email )
                if len(recipients)>0:
                    if operation == 'remove':
                        notification = WebExParticipantNotification( self,recipients, operation )
                        GenericMailer.send( notification )
                    else:
                        notification = WebExParticipantNotification( self,recipients, operation, additionalText="This is a WebEx meeting invitation.<br/><br/>" )
                        GenericMailer.send( notification )
            if params.has_key('sendCreatorEmail') and params['sendCreatorEmail'][0].lower() == 'yes':
                recipients = MailTools.getManagersEmailList(self.getConference(), 'WebEx')
                notification = WebExParticipantNotification( self,recipients, operation, additionalText="Dear event manager:<br/><br/>\n\n  " )
                GenericMailer.send( notification )
            if params.has_key('sendSelfEmail') and params['sendSelfEmail'][0].lower() == 'yes' and params.has_key("loggedInEmail") and params["loggedInEmail"] != "":
                recipients = [ params["loggedInEmail"] ]
                notification = WebExParticipantNotification( self,recipients, operation, additionalText="You are receiving this email because you requested it when creating a WebEx booking via Indico.<br/><br/>\n\n  " )
                GenericMailer.send( notification )
        except Exception,e:
            Logger.get('WebEx').error(
                """Could not send participant email for booking with id %s of event with id %s, operation %s, exception: %s""" %
                (self.getId(), self.getConference().getId(), operation, str(e)))
            Logger.get('WebEx').error( MailTools.getManagersEmailList(self.getConference(), 'WebEx') )
            self._warning = _("The operation appears to have been successful, however there was an error in sending the emails to participants: %s" % str(e) )

    def _sendMail(self, operation):
        """
        Overloading the _sendMail behavior for WebEx
        """
        if operation == 'new':
            try:
                notification = NewWebExMeetingNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName(),
                                         self.getConference().getCreator())
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not send NewWebExMeetingNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))
                self._warning = _("There was an error in sending the emails to administrators: %s" % str(e) )

        elif operation == 'modify':
            try:
                notification = WebExMeetingModifiedNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not send WebExMeetingModifiedNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))
                self._warning = _("There was an error in sending the emails to administrators: %s" % str(e) )

        elif operation == 'remove':
            try:
                notification = WebExMeetingRemovalNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not send WebExMeetingRemovalNotification for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))
                self._warning = _("There was an error in sending the emails to administrators: %s" % str(e) )

