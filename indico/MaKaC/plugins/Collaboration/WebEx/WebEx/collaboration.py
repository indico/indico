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
import xml.dom.minidom
import re
import datetime
#from MaKaC.common.PickleJar import DictPickler
from datetime import timedelta, datetime
from time import strftime, strptime
from MaKaC.common.PickleJar import Retrieves
from MaKaC.common.utils import formatDateTime
from MaKaC.common.timezoneUtils import nowutc, utctimestamp2date, naive2local, datetimeToUnixTime, getAdjustedDate
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.WebEx.common import WebExControlledException, WebExException,\
    getMinStartDate, getMaxEndDate, ChangesFromWebExError,\
    WebExError, WebExWarning, getWebExOptionValueByName, sendXMLRequest, makeTime, findDuration, \
    Participant, makeParticipantXML
from MaKaC.plugins.Collaboration.WebEx.mail import NewWebExMeetingNotificationAdmin, \
    WebExMeetingModifiedNotificationAdmin, WebExMeetingRemovalNotificationAdmin, \
    NewWebExMeetingNotificationManager, WebExMeetingModifiedNotificationManager,\
    WebExMeetingRemovalNotificationManager, WebExParticipantNotification
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import personMail, Mailer
from MaKaC.common.logger import Logger
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from MaKaC.services.interface.rpc.common import ProcessError
from MaKaC.common.Counter import Counter

from MaKaC.plugins.Collaboration.WebEx.fossils import ICSBookingIndexingFossil, ICSBookingConfModifFossil
from MaKaC.common.fossilize import fossilizes
from MaKaC.plugins.Collaboration.fossils import ICSBookingBaseConfModifFossil

class CSBooking(CSBookingBase):
    fossilizes(ICSBookingConfModifFossil, ICSBookingIndexingFossil)

    _hasTitle = True
    _hasStart = True
    _hasStop = False
    _hasCheckStatus = True

    _requiresServerCallForStart = True
    _requiresClientCallForStart = False

    _needsBookingParamsCheck = True
    _needsToBeNotifiedOnView = True
    _needsToBeNotifiedOfDateChanges = True
    _canBeNotifiedOfEventDateChanges = True
    _allowMultiple = True 

    _hasEventDisplay = True

    _commonIndexes = ["All Videoconference"]
    _changesFromWebEx = []

    _simpleParameters = {
            "meetingTitle": (str, ''),
            "meetingDescription": (str, None),
            "sendMailToManagers": (bool, False),
            "webExUser":(str, None),
            "webExPass":(str, None),
            "webExKey":(str, None),  #The meeting key / ID number in the WebEx system
            "sendAttendeesEmail":(bool, True)
    }
    _complexParameters = ["accessPassword", "hasAccessPassword", "participants" ]

    def __init__(self, type, conf):
        CSBookingBase.__init__(self, type, conf)
        self._participants = {} 
        self._participantIdCounter = Counter(1)
        self._accessPassword = None
        self._url = None
        self._webExKey = None
        self._phoneNum = None
        self._duration = None
        self._iCalURL = None
        
        self._created = False
        self._error = False
        self._errorMessage = None
        self._errorDetails = None

        self._lastCheck = nowutc()
        self._checksDone = []
        
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
        return self.getParticipantList(sorted = True)
        
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

    def getErrorMessage(self):
        return self._errorMessage

    def getWebExUser(self):
        return self._bookingParams['webExUser']

    def getWebExKey(self):
        try:
            return self._webExKey
        except:
            return "No key set"
    
    def getErrorDetails(self):
        return self._errorDetails
    
    def getChangesFromWebEx(self):
        return self._changesFromWebEx
    
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
        for p in self._participants.itervalues():
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", p._email) == None:
                raise WebExException("Participant email address (" + p._email + ") for " + p._firstName + " " + p._lastName +" is invalid. ")
                
        if len(self._bookingParams["meetingTitle"].strip()) == 0:
            raise WebExException("meetingTitle parameter (" + str(self._bookingParams["meetingTitle"]) +" ) is empty for booking with id: " + str(self._id))

        if len(self._bookingParams["meetingDescription"].strip()) == 0:
            raise WebExException("meetingDescription parameter (" + str(self._bookingParams["meetingDescription"]) +" ) is empty for booking with id: " + str(self._id))
        
        if self._startDate > self._endDate:
            raise WebExException("Start date of booking cannot be after end date. Booking id: " + str(self._id))
        
        allowedStartMinutes = self._WebExOptions["allowedPastMinutes"].getValue()
        if self.getAdjustedStartDate('UTC')  < (nowutc() - timedelta(minutes = allowedStartMinutes )):
            raise WebExException("Cannot create booking before the past %s minutes. Booking id: %s"% (allowedStartMinutes, str(self._id)))
        
        minStartDate = getMinStartDate(self.getConference())
        if self.getAdjustedStartDate() < minStartDate:
            raise WebExException("Cannot create a booking %s minutes before the Indico event's start date. Please create it after %s"%(self._WebExOptions["allowedMinutes"].getValue(), formatDateTime(minStartDate)))

        maxEndDate = getMaxEndDate(self.getConference())
        if self.getAdjustedEndDate() > maxEndDate:
            raise WebExException("Cannot create a booking %s minutes after before the Indico event's end date. Please create it before %s"%(self._WebExOptions["allowedMinutes"].getValue(), formatDateTime(maxEndDate)))
        
        if False: #for now, we don't detect overlapping
            for booking in self.getBookingsOfSameType():
                if self._id != booking.getId():
                    if not ((self._startDate < booking.getStartDate() and self._endDate <= booking.getStartDate()) or
                            (self._startDate >= booking.getEndDate() and self._endDate > booking.getEndDate())):
                        return OverlappedError(booking)
        
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
""" % ( { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "tz_id":tz_id, "date":the_date } )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        offset = dom.getElementsByTagName( "ns1:gmtOffset" )[0].firstChild.toxml('utf-8')
        try:        
            return int(offset)
        except:
            Logger.get('WebEx').debug( "Eror requesting time zone offset from WebEx:\n\n%s" % ( response_xml ) )
            return None
   
    def bookingOK(self):
        self._statusMessage = _("Booking created")
        self._statusClass = "statusMessageOK"
        self._created = True
        
    def checkCanStart(self, changeMessage = True):
        if self._created:
###############
            self._canBeStarted = True
            return True 
##########Remove above here; in for testing
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

    def _create(self):
        """ Creates a booking in the EVO server if all conditions are met.
        """
        try:
            params = self.getBookingParams()
            self.setAccessPassword( params['accessPassword'] )
            
            participant_xml = makeParticipantXML(self._participants)
            
            t1 = makeTime( self.getAdjustedStartDate('UTC') )
            self._duration = findDuration( self.getAdjustedStartDate('UTC'), self.getAdjustedEndDate('UTC') )
            start_date = t1.strftime( "%m/%d/%Y %H:%M" )
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
  <bodyContent xsi:type="java:com.webex.service.binding.meeting.CreateMeeting" xmlns:meet="http://www.webex.com/schemas/2002/06/service/meeting" >
    <accessControl>
      <meetingPassword>%(meetingPassword)s</meetingPassword>
    </accessControl>
    <metaData>
      <confName>%(meetingName)s</confName>
      <agenda>%(description)s</agenda>
    </metaData>
    %(participants)s
    <enableOptions>
      <chat>true</chat>
      <poll>true</poll>
      <audioVideo>true</audioVideo>
    </enableOptions>
    <schedule>
      <startDate>%(startDate)s:00</startDate>
      <joinTeleconfBeforeHost>false</joinTeleconfBeforeHost>
      <duration>%(duration)s</duration>
      <timeZoneID>20</timeZoneID><!--Zone 20 is Greenwich GMT/UTC-->
    </schedule>
    <telephony>
      <telephonySupport>CALLIN</telephonySupport>
    </telephony>
  </bodyContent>
</body>
</serv:message>

""" % ( { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "meetingPassword": params['accessPassword'], "startDate" : start_date, "duration" : self._duration, "meetingName" : params['meetingTitle'], "description" : params['meetingDescription'], "participants": participant_xml } )
            Logger.get('WebEx').debug( "WebEx Response:\n\n%s" % ( request_xml ) )
            response_xml = sendXMLRequest( request_xml )
            Logger.get('WebEx').debug( "WebEx Response:\n\n%s" % ( response_xml ) )
            dom = xml.dom.minidom.parseString( response_xml )
            status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
            if status == "SUCCESS":
                self._webExKey = dom.getElementsByTagName( "meet:meetingkey" )[0].firstChild.toxml('utf-8')
                self._iCalURL = dom.getElementsByTagName( "serv:attendee" )[0].firstChild.toxml('utf-8')
                #Check if they left the trialing slash in the base URL we need
                if getWebExOptionValueByName("WEhttpServerLocation")[-1] == "/":
                    self._url = getWebExOptionValueByName("WEautoJoinURL") + 'm.php?AT=JM&MK=' + self._webExKey
                else:  #Add in the slash for them
                    self._url = getWebExOptionValueByName("WEautoJoinURL") + '/m.php?AT=JM&MK=' + self._webExKey
                #We do this because the call in number is not returned in create response
                self.bookingOK()
                self.checkCanStart()
                self._checkStatus()
                recipients = []
                for k in self._participants.keys():
                    recipients.append( self._participants[k]._email )
                if len(recipients)>0:
                    notification = WebExParticipantNotification( self, recipients, 'new' )
                    GenericMailer.send( notification )
            else:
                self._url = ""
                errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
                errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
                return WebExError( errorID, userMessage = errorReason )

            if MailTools.needToSendEmails('WebEx'):
                try:
                    notification = NewWebExMeetingNotificationAdmin(self)
                    GenericMailer.sendAndLog(notification, self.getConference(),
                            "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                            self.getConference().getCreator())
                except Exception,e:
                    Logger.get('WebEx').error(
        	               """Could not send NewWebExMeetingNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
        	               (self.getId(), self.getConference().getId(), str(e)))
                    
            if self._bookingParams["sendMailToManagers"]:
                try:
                    notification = NewWebExMeetingNotificationManager(self)
                    GenericMailer.sendAndLog(notification, self.getConference(),
                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                             self.getConference().getCreator())
                except Exception,e:
                    Logger.get('WebEx').error(
                        """Could not send NewEVOMeetingNotificationManager for booking with id %s , exception: %s""" % (self._id, str(e)))
        except WebExControlledException, e:
            Logger.get('WebEx').debug( "caught exception in function _create" )
            raise WebExException(_("The booking could not be created due to a problem with the WebEx Server\n.It sent the following message: ") + e.message, e)

    def _modify(self):
        """ Modifies a booking in the EVO server if all conditions are met.
        """
        Logger.get('WebEx').debug( "in _modify" )
        if self._created:
            arguments = self.getCreateModifyArguments()
            #we take care of the participants 

            try:
                params = self.getBookingParams()
                self.setAccessPassword( params['accessPassword'] )
                t1 = datetime( *strptime( str(self.getAdjustedStartDate('UTC'))[:-9], "%Y-%m-%d %H:%M" )[0:7])
                t2 = datetime( *strptime( str(self.getAdjustedEndDate('UTC'))[:-9], "%Y-%m-%d %H:%M" )[0:7])
                diff = t2 - t1
                days = diff.days
                minutes,seconds = divmod(diff.seconds, 60)
                duration = minutes + diff.days * 1440
                start_date = t1.strftime( "%m/%d/%Y %H:%M" )
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
  <bodyContent xsi:type="java:com.webex.service.binding.meeting.SetMeeting" xmlns:meet="http://www.webex.com/schemas/2002/06/service/meeting" >
    <meetingkey>%(meetingKey)s</meetingkey>
    <accessControl>
      <meetingPassword>%(meetingPassword)s</meetingPassword>
    </accessControl>
    <metaData>
      <confName>%(meetingName)s</confName>
      <agenda>%(description)s</agenda>
    </metaData>
    %(participants)s
    <enableOptions>
      <chat>true</chat>
      <poll>true</poll>
      <audioVideo>true</audioVideo>
    </enableOptions>
    
    <schedule>
      <startDate>%(startDate)s:00</startDate>
      <joinTeleconfBeforeHost>false</joinTeleconfBeforeHost>
      <duration>%(duration)s</duration>
      <timeZoneID>20</timeZoneID><!--Zone 20 is Greenwich GMT/UTC-->
    </schedule>
    <telephony>
      <telephonySupport>CALLIN</telephonySupport>
    </telephony>
  </bodyContent>
</body>
</serv:message>

""" % ( { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "meetingPassword": params['accessPassword'], "startDate" : start_date, "duration" : self._duration, "meetingName" : params['meetingTitle'], "meetingKey" : self._webExKey, "description": params["meetingDescription"], "participants": makeParticipantXML(self._participants) } )
                Logger.get('WebEx').debug( "WebEx Modify Request:\n\n%s" % ( request_xml ) )
                response_xml = sendXMLRequest( request_xml )
                Logger.get('WebEx').debug( "WebEx Modify Response:\n\n%s" % ( response_xml ) )
                dom = xml.dom.minidom.parseString( response_xml )
                status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
                if status != "SUCCESS":
                    errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
                    errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
                    return WebExError( errorID, userMessage = errorReason )

                self.bookingOK()
                self.checkCanStart()
                self._checkStatus()
                recipients = []
                for k in self._participants.keys():
                    recipients.append( self._participants[k]._email )
                if len(recipients)>0:
                    notification = WebExParticipantNotification( self, recipients, 'modify' )
                    GenericMailer.send( notification )

                if MailTools.needToSendEmails('WebEx'):
                    try:
                        notification = WebExMeetingModifiedNotificationAdmin(self)
                        GenericMailer.sendAndLog(notification, self.getConference(),
                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                             self.getConference().getCreator())
                    except Exception,e:
                        Logger.get('WebEx').error(
                            """Could not send WebExMeetingModifiedNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                            (self.getId(), self.getConference().getId(), str(e)))
                        
                if self._bookingParams["sendMailToManagers"]:
                    try:
                        notification = WebExMeetingModifiedNotificationManager(self)
                        GenericMailer.sendAndLog(notification, self.getConference(),
                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                             self.getConference().getCreator())
                    except Exception,e:
                        Logger.get('WebEx').error(
                            """Could not send WebExMeetingModifiedNotificationManager for booking with id %s , exception: %s""" % (self._id, str(e)))

                
            except WebExControlledException, e:
                raise WebExException(_("The booking could not be modified due to a problem with the WebEx Server.\n") )
        else:
            self._create()
            
    def _start(self):
        """ Starts an EVO meeting.
            A last check on the EVO server is performed.
        """
        Logger.get('WebEx').debug( "in _start" )
        #Check if they left the trialing slash in the base URL we need
        if getWebExOptionValueByName("WEhttpServerLocation")[-1] == "/":
            start_url = getWebExOptionValueByName("WEautoJoinURL") + 'm.php?AT=HM&AS=WebTour&WL=http://www.aol.com&MK=' + self._webExKey
        else:  #Add in the slash for them
            start_url = getWebExOptionValueByName("WEautoJoinURL") + '/m.php?AT=HM&MK=' + self._webExKey
#        urllib.urllibopen( getWebExOptionValueByName("WEhttpServerLocation") )
        self._checkStatus()
        if self._canBeStarted:
            self._permissionToStart = True
        
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

""" % { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webex_key": self._webExKey }
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
                raise WebExException(_("Information could not be retrieved due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)

    def _delete(self):
        self._warning = WebExWarning( "a test of the warning system" )
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
      <bodyContent xsi:type="java:com.webex.service.binding.meeting.DelMeeting">
         <meetingKey>%(webex_key)s</meetingKey>
      </bodyContent>
   </body>
</serv:message>
""" % { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webex_key": self._webExKey }
        Logger.get('WebEx').debug( "delete func. is self._created? %s XML:\n%s " % ( self._created, request_xml ) )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
        if status != "SUCCESS":
            errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
            errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
            Logger.get('WebEx').info( "In delete function, appears to have failed: %s" % response_xml )
            return WebExError( errorID, userMessage = errorReason )
#            self._warning = WebExWarning( reason )
        else:
            Logger.get('WebEx').info( "In delete function, appears to have been successful" )

        if self._created:
            try:
#                if MailTools.needToSendEmails('WebEx'):
                if True:
                    try:
#                        notification = WebExParticipantNotification(self, [ "flannery@gmail.com", "flannery@fnal.gov", "flannery@imsa.edu" ])
                        #send(addto, addcc, addfrom, subject, body):
                        Logger.get('WebEx').info("I am in the mailer block")
                        recipients = ""
                        for k in participants.keys():
                            recipients += participants[k]._email + " , "
                        Logger.get('WebEx').info("Recipients: " + recipients )
                        personMail.send(recipients, "", "Kevin O'Flannery", "A Subject", "Some body in here" )
#notification, self.getConference(),
#                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
#                                             self.getConference().getCreator())
                    except Exception,e:
                        Logger.get('WebEx').error(
                            """Could not send WebExMeetingRemovalNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
                            (self.getId(), self.getConference().getId(), str(e)))
               
#                if self._bookingParams["sendMailToManagers"]:
#                    try:
#                        notification = EVOMeetingRemovalNotificationManager(self)
#                        GenericMailer.sendAndLog(notification, self.getConference(),
#                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
#                                             self.getConference().getCreator())
#                    except Exception,e:
#                        Logger.get('EVO').error(
#                            """Could not send EVOMeetingRemovalNotificationManager for booking with id %s , exception: %s""" % (self._id, str(e)))
                
            except WebExControlledException, e:                
                if e.message == "DELETE_MEETING_OVER":
                    return WebExError('cannotDeleteOld', str(requestURL))
                if e.message == "DELETE_MEETING_ONGOING":
                    return WebExError('cannotDeleteOngoing', str(requestURL))
                if e.message == "DELETE_MEETING_NO_ID":
                    self._warning = EVOWarning('cannotDeleteNonExistant')
                else:
                    return WebExError( userMessage = "The booking could not be deleted due to a problem with the WebEx Server" )
                    raise WebExException(_("The booking could not be deleted due to a problem with the EVO Server\n.The EVO Server sent the following error message: ") + e.message, e)
                
        self._error = False
        
        
    def _getLaunchDisplayInfo(self):
        return {'launchText' : _("Join Now!"),
                'launchLink' : str(self.getURL()),
                'launchTooltip': _("Click here to join the WebEx meeting!")}
            
    def getCreateModifyArguments(self):
        arguments = {
            "meet:meetingkey": self._webExKey, 
            "meet:agenda": self._bookingParams["meetingDescription"].replace("\n",""),
            "meet:confName": self._bookingParams["meetingTitle"],
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
        
        changesFromWebEx = self._changesFromWebEx
#        changesFromWebEx = []
        
        start_date = makeTime( self.getAdjustedStartDate('UTC') ).strftime( "%m/%d/%Y %H:%M:%S" )
        time_discrepancy = False
        for key in oldArguments:
            if not verboseKeyNames.has_key( key ):
                continue
            if key == "meet:startDate" or key == "meet:duration":
                if key == "meet:startDate":
#                    Logger.get('WebEx').info( "calc_start_date: " + start_date )
#                    Logger.get('WebEx').info( "found_start_date: " + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') ) 
                    if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != start_date:
                        time_discrepancy = True
                        Logger.get('WebEx').info( "Local and WebEx time are different. We will need to calculate it." )
                if key == "meet:duration":
                    if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != str(self._duration):
                        time_discrepancy = True
                        user_msg = "Updated booking duration - old:" + str(self._duration) + " new:" + int( dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') )
                        self._duration = int( dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') )
                        Logger.get('WebEx').info( user_msg )
                        changesFromWebEx.append( user_msg )
                continue
            try:
                if dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') != str(oldArguments[key]) and key in verboseKeyNames:
                    changesFromWebEx.append(verboseKeyNames[key] + ": " + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8'))
                    Logger.get('WebEx').info( "WebEx Val: '" + dom.getElementsByTagName( key )[0].firstChild.toxml('utf-8') + "' and local:'" + str(oldArguments[key]) ) 
            except:
                Logger.get('WebEx').info( "caught exception on: " + key )
                pass
        self._phoneNum = dom.getElementsByTagName( "serv:tollFreeNum" )[0].firstChild.toxml('utf-8') 
        
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
                changesFromWebEx.append("Updated start time to match WebEx start time (displayed in event timezone): " + getAdjustedDate(WE_time, tz=self._conf.getTimezone()).strftime("%m/%d/%Y %H:%M:%S") )  
            self._startDate = getAdjustedDate(WE_time, tz=self._conf.getTimezone())
            self._endDate = getAdjustedDate(WE_time, tz=self._conf.getTimezone()) + timedelta( minutes=int( self._duration ) )
        if time_discrepancy == True:
            recipients = []
            for k in self._participants.keys():
                recipients.append( self._participants[k]._email )
            notification = WebExParticipantNotification( self, recipients, 'modify' )
            GenericMailer.send( notification )

        self.checkCanStart()
        self._changesFromWebEx = changesFromWebEx

