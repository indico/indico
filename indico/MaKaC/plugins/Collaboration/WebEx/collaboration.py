# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.21 2009/04/25 13:56:05 dmartinc Exp $
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
import datetime
import httplib
from datetime import timedelta, datetime
from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import nowutc, naive2local, getAdjustedDate
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.WebEx.common import WebExControlledException, WebExException,\
    getMinStartDate, getMaxEndDate, Participant, sendXMLRequest, \
    WebExError, getWebExOptionValueByName, makeTime, findDuration, unescape
from MaKaC.plugins.Collaboration.WebEx.api.operations import WebExOperations
from MaKaC.common.logger import Logger
from MaKaC.i18n import _
from MaKaC.common.Counter import Counter
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.Collaboration.WebEx.mail import NewWebExMeetingNotificationAdmin, \
    WebExMeetingModifiedNotificationAdmin, WebExMeetingRemovalNotificationAdmin, \
    NewWebExMeetingNotificationManager, WebExMeetingModifiedNotificationManager,\
    WebExMeetingRemovalNotificationManager, WebExParticipantNotification

from MaKaC.plugins.Collaboration.WebEx.fossils import ICSBookingIndexingFossil, ICSBookingConfModifFossil
from MaKaC.common.fossilize import fossilizes, fossilize
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
#from MaKaC.errors import TimingError
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
#    _canBeNotifiedOfEventDateChanges = True
    _allowMultiple = True 

    _hasEventDisplay = True

    _commonIndexes = ["All Videoconference"]

    _simpleParameters = {
            "meetingTitle": (str, ''),
            "meetingDescription": (str, None),
            "webExUser":(str, None),
            "sendAttendeesEmail":(bool, True)
    }
    _complexParameters = ["accessPassword", "hasAccessPassword", "participants", "webExPass" ]

    def __init__(self, type, conf):
        CSBookingBase.__init__(self, type, conf)
        self._participants = {} 
        self._participantIdCounter = Counter(1)
        self._accessPassword = None
        self._url = None
        self._startURL = None
        self._webExKey = None
        self._phoneNum = None
        self._phoneNumToll = None
        self._duration = None

        self._created = False
        self._error = False
        self._errorMessage = None
        self._errorDetails = None

        self._lastCheck = nowutc()
        self._checksDone = []
        self._bookingChangesHistory = []
        
    def getParticipantList(self, sorted = False):
        Logger.get('WebEx').debug( "In getParticipantList" )
        if sorted:
            keys = self._participants.keys()
            keys.sort()
            for k in keys:
                Logger.get('WebEx').info( "Adding: " + self._participants[k]._email )
            return [self._participants[k] for k in keys]
        else:
            return self._participants.values()
            
    def getParticipants(self):
        Logger.get('WebEx').debug( "In getParticipants" )
        return fossilize(self.getParticipantList(sorted = True))
        
    def setParticipants(self, participants):
        Logger.get('WebEx').debug( "In setParticipants" )
        participantsCopy = dict(self._participants)
        self._participants = {}
        for p in participants:
            id = p.get("participantId", None)
            Logger.get('WebEx').debug( "Adding a participant: %s" % str(id) )
            if id is None or not id in participantsCopy:
                id = self._participantIdCounter.newCount()
            
            participantObject = Participant(self, id, p)
                
            self._participants[id] = participantObject
        
        self._p_changed = 1
        
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

    def setHasAccessPassword(self, value = False):
        return value

    def setAccessPassword(self, accessPassword):
        if accessPassword.strip() == "":
            self._accessPassword = None
        else:
            self._accessPassword = accessPassword
            
    def getHasAccessPassword(self):
        return self._accessPassword is not None
    
    def getUrl(self):
        return self._url

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


    
    def getLastCheck(self):
        if not hasattr(self, "_lastCheck"): #TODO: remove when safe
            self._lastCheck = nowutc()
            self._checksDone = []
        return self._lastCheck

    ## overriding methods
    def _getTitle(self):
        return self._bookingParams["meetingTitle"]

    def _getPluginDisplayName(self):
        return "WebEx"

    def _checkBookingParams(self):
        for participant in self._participants.itervalues():
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", participant._email) == None:
                raise WebExException("Participant email address (" + participant._email + ") for " + participant._firstName + " " + participant._lastName +" is invalid. ")
                
        if len(self._bookingParams["meetingTitle"].strip()) == 0:
            raise WebExException("meetingTitle parameter (" + str(self._bookingParams["meetingTitle"]) +" ) is empty for booking with id: " + str(self._id))

        if len(self._bookingParams["meetingDescription"].strip()) == 0:
            raise WebExException("meetingDescription parameter (" + str(self._bookingParams["meetingDescription"]) +" ) is empty for booking with id: " + str(self._id))

        if len(self._bookingParams["webExUser"].strip()) == 0:
            raise WebExException("WebEx username is empty.  The booking cannot continue without this.")
        
        if len(self.getWebExPass().strip()) == 0:
            raise WebExException("WebEx password is empty.  The booking cannot continue without this.")

        if self._startDate > self._endDate:
            raise WebExException("Start date of booking cannot be after end date. Booking id: " + str(self._id))
        
        allowedStartMinutes = self._WebExOptions["allowedPastMinutes"].getValue()
        if self.getAdjustedStartDate('UTC')  < (nowutc() - timedelta(minutes = allowedStartMinutes )):
            raise WebExException("Cannot create booking before the past %s minutes. Booking id: %s"% (allowedStartMinutes, str(self._id)))
        
        minStartDate = getMinStartDate(self.getConference())
        Logger.get('WebEx').info( "Min start date: " + minStartDate.strftime("%m/%d/%Y %H:%M:%S") )
        if self.getAdjustedStartDate() < minStartDate:
            raise WebExException("Cannot create a booking %s minutes before the Indico event's start date. Please create it after %s"%(self._WebExOptions["allowedMinutes"].getValue(), formatDateTime(minStartDate)))

        maxEndDate = getMaxEndDate(self.getConference())
        Logger.get('WebEx').info( "Max end date: " + minStartDate.strftime("%m/%d/%Y %H:%M:%S") )
        if self.getAdjustedEndDate() > maxEndDate:
            raise WebExException("Cannot create a booking %s minutes after before the Indico event's end date. Please create it before %s"%(self._WebExOptions["allowedMinutes"].getValue(), formatDateTime(maxEndDate)))
        
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
#        self._canBeStarted = False
#        self._statusMessage = _("Ready to start!")
#        self._statusClass = "statusMessageOK"
#        return True
        if self._created:
            now = nowutc()
            self._canBeDeleted = True
#            if self.getStartDate() - timedelta(minutes=self._WebExOptions["allowedMinutes"].getValue()) < now and self.getEndDate() + timedelta(self._WebExOptions["allowedMinutes"].getValue()) > now:
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
                elif changeMessage:
                    self.bookingOK()

    def _create(self):
        """ Creates a booking in the WebEx server if all conditions are met.
        """
        params = self.getBookingParams()
        self.setAccessPassword( params['accessPassword'] )
        self._duration = findDuration( self.getAdjustedStartDate('UTC'), self.getAdjustedEndDate('UTC') )
#        self._originalDuration = self._duration
#        self._offsetFromEventStart = findDuration( self._conf.getAdjustedStartDate('UTC'), self.getAdjustedEndDate('UTC') ) 

#        Logger.get('WebEx').info("sendemail to attendees: %s" % params['sendAttendeesEmail'])
        result = ExternalOperationsManager.execute(self, "createBooking", WebExOperations.createBooking, self)
        if isinstance(result, WebExError):
            return result
        #We do this because the call in number is not returned in create response
        self.bookingOK()
        self.checkCanStart()
        return None

    def notifyEventDateChanges(self, oldStartDate, newStartDate, oldEndDate, newEndDate):
#        self._startDate = self.getAdjustedStartDate('UTC') + timedelta( minutes=int( self._offsetFromEventStart ) )
#        self._endDate = self.getAdjustedStartDate('UTC') + timedelta( minutes=int( self._originalDuration ) )
#        result = ExternalOperationsManager.execute(self, "modifyBooking", WebExOperations.modifyBooking, self)
#getAdjustedDate(WE_time, tz=self._conf.getTimezone()) + timedelta( minutes=int( self._duration ) )
#        result = ExternalOperationsManager.execute(self, "createBooking", WebExOperations.createBooking, self)
        Logger.get('WebEx').debug( "In notifyEventDateChanges" )
        Logger.get('WebEx').info( "%s %s %s %s" % (oldStartDate, newStartDate, oldEndDate, newEndDate) )


    def _modify(self, oldBookingParams):
        """ Modifies a booking in the WebEx server if all conditions are met.
        """
        verboseKeyNames = {
            "meetingDescription": "Meeting description",
            "meetingTitle": "Title",
            "webExUser": "WebEx username",
            "webExPass": "WebEx password",
            "meet:meetingPassword": "Meeting password",
            "participants" : "Participants", 
            "startDate" : "Start date",
            "endDate" : "End date",
            "hidden" : "Is hidden",
            "sendAttendeesEmail" : "Send emails to participants",
            "notifyOnDateChanges" : "Keep booking synchronized"
        }
        Logger.get('WebEx').debug( "in _modify" )
        if self._created:
            self._bookingChangesHistory
            params = self.getBookingParams()
            Logger.get('WebEx').debug( "In modify: params = %s" % params )
            for key in oldBookingParams.keys():
#                try:
#                    Logger.get('WebEx').debug( "New Param: %s = %s" % ( key, params[key]) )
#                    Logger.get('WebEx').debug( "Old Param: %s = %s" % ( key, oldBookingParams[key]) )

                    if key == "hidden" or key == "notifyOnDateChanges" or key == "sendAttendeesEmail":
                        if oldBookingParams.has_key( key ) != params.has_key( key ) or oldBookingParams[key] != params[key]:
                            self._bookingChangesHistory.append( "%s has changed." % ( verboseKeyNames[key] ) )
                            continue
                    if oldBookingParams[key] != params[key]:
                        if key == "participants":
                            #Number of participants changed - report this 
                            if len(params[key]) != len(oldBookingParams[key]):
                                self._bookingChangesHistory.append( "%s has changed." % ( verboseKeyNames[key] ) )
                                continue
                            count = -1
                            for participant in params[key]:
                                count = count + 1
                                for participantKey in participant.keys():
                                    if participantKey=="id":
                                        continue
#                                        Logger.get('WebEx').debug( "Evaluating %s vs %s" % ( params[key][0], oldBookingParams[key][0] ) )
                                    if oldBookingParams[key][count].get(participantKey) != params[key][count].get(participantKey):
                                        self._bookingChangesHistory.append( "%s has changed." % ( verboseKeyNames[key] ) )
                                        break
                        else:
                            self._bookingChangesHistory.append( "%s has changed: %s" % ( verboseKeyNames[key], params[key] ) )
                        
#                except:
#                    Logger.get('WebEx').debug( "Error on key name in modify:\n\n%s" % ( key ) )
            result = ExternalOperationsManager.execute(self, "modifyBooking", WebExOperations.modifyBooking, self)
            if isinstance(result, WebExError):
#                raise TimingError("The WebEx system was not able to perform the booking modification")
                return WebExError( errorType = None, userMessage = "The booking appears to have not been created according to the Indico system" )
                #Logger.get('WebEx').debug( "returning error" )
                #return result
        else:
            return WebExError( errorType = None, userMessage = "The booking appears to have not been created according to the Indico system" )
        return None

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
            Logger.get('WebEx').debug( "Start request XML:\n %s" % request_xml )
            response_xml = sendXMLRequest( request_xml )
            Logger.get('WebEx').debug( "Start response XML:\n %s" % response_xml )
            dom = xml.dom.minidom.parseString( response_xml )
            status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
            if status == "SUCCESS":
                self._startURL = dom.getElementsByTagName( "meet:hostMeetingURL" )[0].firstChild.toxml('utf-8')
                self._permissionToStart = True
            else:
                return WebExError( errorType = None, userMessage = "There was an error attempting to get the start booking URL from the WebEx server." ) 
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

    def _checkStatus(self):
        if self._created:
            try:
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
                Logger.get('WebEx').debug( "Check status request XML:\n%s " % ( request_xml ) )
                response_xml = sendXMLRequest( request_xml )
                Logger.get('WebEx').debug( "Check status response XML:\n%s " % ( response_xml ) )
                dom = xml.dom.minidom.parseString( response_xml )
                status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
                if status != "SUCCESS":
                    errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
                    errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
                    return WebExError( errorID, userMessage = errorReason )
                self.assignAttributes( response_xml )

            except WebExControlledException, e:                
                raise WebExException(_("Information could not be retrieved due to a problem with the WebEx Server\n.The WebEx Server sent the following error message: ") + e.message, e)
            return None

    def _delete(self):
        """
        This function will delete the specified video booking from the WebEx server
        """
        result = ExternalOperationsManager.execute(self, "deleteBooking", WebExOperations.deleteBooking, self)
        if isinstance(result, WebExError):
            return None
        self.warning = "The booking was deleted successfully."
        
    def _getLaunchDisplayInfo(self):
        return {'launchText' : _("Join Now!"),
                'launchLink' : str(self.getURL()),
                'launchTooltip': _("Click here to join the WebEx meeting!")}
            
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
    
    def assignAttributes(self, response_xml):
        
        verboseKeyNames = {
            "meet:meetingkey": "WebEx Meeting ID", 
            "meet:agenda": "Meeting description",
            "meet:confName": "Title",
            "meet:hostWebExID": "WebEx host account",
            "meet:startDate": "Start time",
            "meet:duration": "Duration",
            "meet:meetingPassword": "Meeting password",
        }
        
        dom = xml.dom.minidom.parseString( response_xml )
        oldArguments = self.getCreateModifyArguments()
        
        changesFromWebEx = self._bookingChangesHistory
        
        start_date = makeTime( self.getAdjustedStartDate('UTC') ).strftime( "%m/%d/%Y %H:%M:%S" )
        time_discrepancy = False
        for key in oldArguments:
            if not verboseKeyNames.has_key( key ):
                continue
            if key == "meet:startDate" or key == "meet:duration":
                if key == "meet:startDate":
                    if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != start_date:
                        time_discrepancy = True
                        Logger.get('WebEx').info( "Local and WebEx time are different. We will need to calculate it." )
                if key == "meet:duration":
                    if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != str(self._duration):
                        time_discrepancy = True
                        user_msg = "Updated booking duration from " + str(self._duration) + " minutes to " + str( dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') + " minutes")
                        self._duration = int( dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') )
                        Logger.get('WebEx').info( user_msg )
                continue
            try:
                if unescape(dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8')) != unescape(str(oldArguments[key])) and key in verboseKeyNames:
                    changesFromWebEx.append(verboseKeyNames[key] + ": " + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))
                    if key == "meet:confName":
                        self._bookingParams["meetingTitle"] = unescape(dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))
                    elif key == "meet:agenda":
                        self._bookingParams["meetingDescription"] = unescape(dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))

                    Logger.get('WebEx').info( "WebEx Val: '" + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') + "' and local:'" + str(oldArguments[key]) ) 
            except:
                Logger.get('WebEx').info( "caught exception on: " + key )
                pass
        self._phoneNum = dom.getElementsByTagName( "serv:tollFreeNum" )[0].firstChild.toxml('utf-8') 
        self._phoneNumToll = dom.getElementsByTagName( "serv:tollNum" )[0].firstChild.toxml('utf-8') 
        
        #We calculate the time from WebEx first assuming it is in UTC.
        #If not, we then apply the offset to keep it simple
        calc_time = naive2local( datetime.strptime( dom.getElementsByTagName( "meet:startDate" )[0].firstChild.toxml('utf-8'), "%m/%d/%Y %H:%M:%S" ), 'UTC' )
        tz_id = dom.getElementsByTagName( "meet:timeZoneID" )[0].firstChild.toxml('utf-8')
        Logger.get('WebEx').info( "webex TZ id: " + tz_id )
        Logger.get('WebEx').info( "my start date: " + self.getAdjustedStartDate('UTC').strftime("%m/%d/%Y %H:%M:%S") )
        #If the specified time zone is not UTC, contact WebEx 
        #and find the offset from UTC we must account for 
        if tz_id != 20:
            time_offset_mins = self.getWebExTimeZoneToUTC( tz_id, calc_time.strftime("%m/%d/%Y %H:%M:%S"))
            Logger.get('WebEx').info( "raw webex time: " + calc_time.strftime("%A, %d. %B %Y %I:%M%p") )        
            Logger.get('WebEx').info( "time_offset_mins: " + str(time_offset_mins)) 
            WE_time = calc_time + timedelta( minutes= -1*int( time_offset_mins ) ) 
            if time_discrepancy == True:
                Logger.get('WebEx').info( "webex time with offset in event time zone: " + getAdjustedDate(WE_time, tz=self._conf.getTimezone()).strftime("%m/%d/%Y %H:%M:%S") )
#                changesFromWebEx.append("Updated time to match WebEx time (displayed in event timezone) <br/>Start: " \
#                    + getAdjustedDate(WE_time, tz=self._conf.getTimezone()).strftime("%m/%d/%Y %H:%M:%S") \
#                    + "<br/>End: " \
#                    + (getAdjustedDate(WE_time, tz=self._conf.getTimezone()) + timedelta( minutes=int( self._duration ) )).strftime("%m/%d/%Y %H:%M:%S") )  
            self._startDate = getAdjustedDate(WE_time, tz=self._conf.getTimezone())
            self._endDate = getAdjustedDate(WE_time, tz=self._conf.getTimezone()) + timedelta( minutes=int( self._duration ) )

        self.checkCanStart()
        self._bookingChangesHistory = changesFromWebEx
    def _sendMail(self, operation):
        """
        Overloads _sendMail behavior for WebEx
        """

        if operation == 'new':
            try:
                notification = NewWebExMeetingNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                         self.getConference().getCreator())
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not send NewWebExMeetingNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

        elif operation == 'modify':
            try:
                notification = WebExMeetingModifiedNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                         self.getConference().getCreator())
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not send WebExMeetingModifiedNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

        elif operation == 'remove':
            try:
                notification = WebExMeetingRemovalNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                         self.getConference().getCreator())
            except Exception,e:
                Logger.get('WebEx').error(
                    """Could not send WebExMeetingRemovalNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                    (self.getId(), self.getConference().getId(), str(e)))

