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

"""
These functions are designed to make changes on the WebEx server. 
They do not modify any of the booking parameters themselves.  
"""


import xml.dom.minidom
from datetime import datetime
from time import strptime
from MaKaC.common.logger import Logger
from MaKaC.plugins.Collaboration.WebEx.common import WebExControlledException, \
    WebExError, WebExWarning, getWebExOptionValueByName, WebExException, \
    makeParticipantXML, sendXMLRequest
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from MaKaC.plugins.Collaboration.WebEx.mail import NewWebExMeetingNotificationAdmin, \
    WebExMeetingModifiedNotificationAdmin, WebExMeetingRemovalNotificationAdmin, \
    NewWebExMeetingNotificationManager, WebExMeetingModifiedNotificationManager,\
    WebExMeetingRemovalNotificationManager, WebExParticipantNotification
from MaKaC.common.mail import GenericMailer

from MaKaC.plugins.Collaboration.WebEx.common import getWebExOptionValueByName

class WebExOperations(object):
    """
    This class does all of the calls to the WebEx servers as well as sending
    notification emails to participants.  The methods are called from the 
    externalOperations class so that they are not called more than once by mistake
    """

    """
    Create the booking on the WebEx server
    """
    @classmethod
    def createBooking( cls, booking ):
        try:
            params = booking.getBookingParams()

            participant_xml = makeParticipantXML(booking._participants)
            start_date = booking.getAdjustedStartDate('UTC').strftime( "%m/%d/%Y %H:%M" )
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

""" % ( { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "meetingPassword": params['accessPassword'], "startDate" : start_date, "duration" : booking.getDuration(), "meetingName" : params['meetingTitle'], "description" : params['meetingDescription'], "participants": participant_xml } )
            Logger.get('WebEx').debug( "WebEx Response:\n\n%s" % ( request_xml ) )
            response_xml = sendXMLRequest( request_xml )
            Logger.get('WebEx').debug( "WebEx Response:\n\n%s" % ( response_xml ) )
            dom = xml.dom.minidom.parseString( response_xml )
            status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
            if status == "SUCCESS":
                booking.setWebExKey( dom.getElementsByTagName( "meet:meetingkey" )[0].firstChild.toxml('utf-8') )
                booking._url = dom.getElementsByTagName( "serv:attendee" )[0].firstChild.toxml('utf-8')
                booking._startURL = dom.getElementsByTagName( "serv:host" )[0].firstChild.toxml('utf-8') 
                #Check if they left the trialing slash in the base URL we need
#                if getWebExOptionValueByName("WEhttpServerLocation")[-1] == "/":
#                    booking._url = getWebExOptionValueByName("WEautoJoinURL") + 'm.php?AT=JM&MK=' + booking._webExKey
#                else:  #Add in the slash for them
#                    booking._url = getWebExOptionValueByName("WEautoJoinURL") + '/m.php?AT=JM&MK=' + booking._webExKey

                recipients = []
                for k in booking._participants.keys():
                    recipients.append( booking._participants[k]._email )
                if len(recipients)>0:
                    notification = WebExParticipantNotification( booking, recipients, 'new' )
                    GenericMailer.send( notification )
            else:
                booking._url = ""
                errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
                errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
                return WebExError( errorID, userMessage = errorReason )

            if MailTools.needToSendEmails('WebEx'):
                try:
                    notification = NewWebExMeetingNotificationAdmin(booking)
                    GenericMailer.sendAndLog(notification, booking.getConference(),
                            "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                            booking.getConference().getCreator())
                except Exception, e:
                    Logger.get('WebEx').error(
        	               """Could not send NewWebExMeetingNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
        	               (booking.getId(), booking.getConference().getId(), str(e)))
                    
            if booking._bookingParams["sendMailToManagers"]:
                try:
                    notification = NewWebExMeetingNotificationManager(booking)
                    GenericMailer.sendAndLog(notification, booking.getConference(),
                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                             booking.getConference().getCreator())
                except Exception, e:
                    Logger.get('WebEx').error(
                        """Could not send NewEVOMeetingNotificationManager for booking with id %s , exception: %s""" % (booking._id, str(e)))
        except WebExControlledException, e:
            Logger.get('WebEx').debug( "caught exception in function _create" )
            raise WebExException(_("The booking could not be created due to a problem with the WebEx Server\n.It sent the following message: ") + e.message, e)
        return None

    @classmethod
    def modifyBooking( cls, booking ):
        try:
            arguments = booking.getCreateModifyArguments()
            params = booking.getBookingParams()
            booking.setAccessPassword( params['accessPassword'] )
            start_time = datetime( *strptime( str(booking.getAdjustedStartDate('UTC'))[:-9], "%Y-%m-%d %H:%M" )[0:7])
            end_time = datetime( *strptime( str(booking.getAdjustedEndDate('UTC'))[:-9], "%Y-%m-%d %H:%M" )[0:7])
            diff = end_time - start_time
            days = diff.days
            minutes, seconds = divmod(diff.seconds, 60)
            duration = minutes + diff.days * 1440
            Logger.get('WebEx').debug( "Found duration %s" % str(duration) )
            start_date = start_time.strftime( "%m/%d/%Y %H:%M" )
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

""" % ( { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "meetingPassword": params['accessPassword'], "startDate" : start_date, "duration" : int(duration), "meetingName" : params['meetingTitle'], "meetingKey" : booking._webExKey, "description": params["meetingDescription"], "participants": makeParticipantXML(booking._participants) } )
            Logger.get('WebEx').debug( "WebEx Modify Request:\n\n%s" % ( request_xml ) )
            response_xml = sendXMLRequest( request_xml )
            Logger.get('WebEx').debug( "WebEx Modify Response:\n\n%s" % ( response_xml ) )
            dom = xml.dom.minidom.parseString( response_xml )
            status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
            if status != "SUCCESS":
                errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
                errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
                return WebExError( errorType = None, userMessage = errorReason )

            booking.bookingOK()
            booking.checkCanStart()
            booking._checkStatus()
            recipients = []
            for k in booking._participants.keys():
                recipients.append( booking._participants[k]._email )
            if len(recipients)>0:
                notification = WebExParticipantNotification( booking, recipients, 'modify' )
                GenericMailer.send( notification )
            if MailTools.needToSendEmails('WebEx'):
                Logger.get('WebEx').info("We need to alert WebEx admins; attempting to send emails")
                try:
                    notification = WebExMeetingModifiedNotificationAdmin(booking)
                    GenericMailer.sendAndLog(notification, booking.getConference(),
                            "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                            booking.getConference().getCreator())
                except Exception, e:
                    Logger.get('WebEx').error(
        	               """Could not send WebExMeetingModifiedNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
        	               (booking.getId(), booking.getConference().getId(), str(e)))
            if booking._bookingParams["sendMailToManagers"]:
                try:
                    notification = WebExMeetingModifiedNotificationManager(booking)
                    GenericMailer.sendAndLog(notification, booking.getConference(),
                                         "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                         booking.getConference().getCreator())
                except Exception, e:
                    Logger.get('WebEx').error(
                        """Could not send WebExMeetingModifiedNotificationManager for booking with id %s , exception: %s""" % (booking._id, str(e)))
                
        except WebExControlledException, e:
            raise WebExException(_("The booking could not be modified due to a problem with the WebEx Server.\n") )
        return None

    @classmethod
    def deleteBooking( cls, booking ):
        booking._warning = WebExWarning( "a test of the warning system" )
        params = booking.getBookingParams()
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
""" % { "username" : params['webExUser'], "password" : params['webExPass'], "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webex_key": booking._webExKey }
        Logger.get('WebEx').debug( "delete func. is booking._created? %s XML:\n%s " % ( booking._created, request_xml ) )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
        if status != "SUCCESS":
            errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
            errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
            Logger.get('WebEx').info( "In delete function, appears to have failed: %s" % response_xml )
            return WebExError( errorID, userMessage = errorReason )
#            booking._warning = WebExWarning( reason )
        else:
            Logger.get('WebEx').info( "In delete function, appears to have been successful" )

        if booking._created:
            if MailTools.needToSendEmails('WebEx'):
                Logger.get('WebEx').info("We need to alert WebEx admins; attempting to send emails")
                try:
                    notification = WebExMeetingRemovalNotificationAdmin(booking)
                    GenericMailer.sendAndLog(notification, booking.getConference(),
                            "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                            booking.getConference().getCreator())
                except Exception, e:
                    Logger.get('WebEx').error(
        	               """Could not send WebExMeetingRemovalNotificationAdmin for booking with id %s of event with id %s, exception: %s""" %
        	               (booking.getId(), booking.getConference().getId(), str(e)))
#            if MailTools.needToSendEmails('WebEx'):
            if True:
                try:
                    Logger.get('WebEx').info("I am in the mailer block")
                    recipients = []
                    for k in booking._participants.keys():
                        recipients.append( booking._participants[k]._email )
                    if len(recipients)>0:
                        notification = WebExParticipantNotification( booking, recipients, 'delete' )
                        GenericMailer.send( notification )
                except Exception, e:
                    Logger.get('WebEx').error(
                        """Could not send notification emails for booking with id %s of event with id %s, exception: %s""" %
                        (booking.getId(), booking.getConference().getId(), str(e)))
               
                if booking._bookingParams["sendMailToManagers"]:
                    try:
                        notification = WebExMeetingRemovalNotificationManager(booking)
                        GenericMailer.sendAndLog(notification, booking.getConference(),
                                             "MaKaC/plugins/Collaboration/WebEx/collaboration.py",
                                             booking.getConference().getCreator())
                    except Exception,e:
                        Logger.get('WebEx').error(
                            """Could not send EVOMeetingRemovalNotificationManager for booking with id %s , exception: %s""" % (booking._id, str(e)))
        return None





