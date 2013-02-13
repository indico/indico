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
(Except after the booking is created, we DO save the WebEx ID (meeting key)
and the auto-join URL, because we have no way to keep track of that booking
on the WebEx server otherwise...)
"""


import xml.dom.minidom
from datetime import datetime
from time import strptime
from MaKaC.plugins.Collaboration.WebEx.common import  WebExError,\
    WebExWarning, getWebExOptionValueByName,\
    makeParticipantXML, sendXMLRequest
from cgi import escape

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
      <attendeeList>%(seeParticipants)s</attendeeList>
      <audioVideo>true</audioVideo>
      <chat>true</chat>
      <chatAllAttendees>%(enableChat)s</chatAllAttendees>
      <chatHost>true</chatHost>
      <chatPresenter>true</chatPresenter>
      <desktopShare>true</desktopShare>
      <fullScreen>true</fullScreen>
      <poll>true</poll>
      <presentation>true</presentation>
    </enableOptions>
    <schedule>
      <duration>%(duration)s</duration>
      <joinTeleconfBeforeHost>%(joinBeforeHost)s</joinTeleconfBeforeHost>
      <openTime>%(openTime)s</openTime>
      <startDate>%(startDate)s:00</startDate>
      <timeZoneID>20</timeZoneID><!--Zone 20 is Greenwich GMT/UTC-->
    </schedule>
    <telephony>
      <telephonySupport>CALLIN</telephonySupport>
    </telephony>
  </bodyContent>
</body>
</serv:message>

""" % ( { "username" : params['webExUser'], "password" : escape(params['webExPass']), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "meetingPassword": escape(params['accessPassword']), "startDate" : start_date, "duration" : booking.getDuration(), "meetingName" : escape(params['meetingTitle']), "description" : escape(params['meetingDescription']), "participants": participant_xml, "openTime":params['joinBeforeTime'], "seeParticipants": booking.getSeeParticipants(), "enableChat": booking.getEnableChat(), "joinBeforeHost": booking.getJoinBeforeHost() } )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
        if status == "SUCCESS":
            booking.setWebExKey( dom.getElementsByTagName( "meet:meetingkey" )[0].firstChild.toxml('utf-8') )
        else:
            booking._url = ""
            errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
            errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
            return WebExError( errorID, userMessage = errorReason )

    @classmethod
    def modifyBooking( cls, booking ):
        params = booking.getBookingParams()
        booking.setAccessPassword( params['accessPassword'] )
        start_time = datetime( *strptime( str(booking.getAdjustedStartDate('UTC'))[:-9], "%Y-%m-%d %H:%M" )[0:7])
        end_time = datetime( *strptime( str(booking.getAdjustedEndDate('UTC'))[:-9], "%Y-%m-%d %H:%M" )[0:7])
        diff = end_time - start_time
        minutes, seconds = divmod(diff.seconds, 60)
        duration = minutes + diff.days * 1440
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
      <attendeeList>%(seeParticipants)s</attendeeList>
      <audioVideo>true</audioVideo>
      <chat>true</chat>
      <chatAllAttendees>%(enableChat)s</chatAllAttendees>
      <chatHost>true</chatHost>
      <chatPresenter>true</chatPresenter>
      <desktopShare>true</desktopShare>
      <fullScreen>true</fullScreen>
      <poll>true</poll>
      <presentation>true</presentation>
    </enableOptions>
    <schedule>
      <duration>%(duration)s</duration>
      <joinTeleconfBeforeHost>%(joinBeforeHost)s</joinTeleconfBeforeHost>
      <openTime>%(openTime)s</openTime>
      <startDate>%(startDate)s:00</startDate>
      <timeZoneID>20</timeZoneID><!--Zone 20 is Greenwich GMT/UTC-->
    </schedule>
    <telephony>
      <telephonySupport>CALLIN</telephonySupport>
    </telephony>
  </bodyContent>
</body>
</serv:message>

""" % ( { "username" : params['webExUser'], "password" : escape(params['webExPass']), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "meetingPassword": escape(params['accessPassword']), "startDate" : start_date, "duration" : int(duration), "meetingName" : escape(params['meetingTitle']), "meetingKey" : booking._webExKey, "description": escape(params["meetingDescription"]), "participants": makeParticipantXML(booking._participants), "openTime":params['joinBeforeTime'], "seeParticipants": booking.getSeeParticipants(), "enableChat": booking.getEnableChat(), "joinBeforeHost": booking.getJoinBeforeHost() } )
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
        if status != "SUCCESS":
            errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
            errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
            return WebExError( errorID, userMessage = errorReason )
        return None

    @classmethod
    def deleteBooking( cls, booking ):
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
""" % { "username" : params['webExUser'], "password" : escape(params['webExPass']), "siteID" : getWebExOptionValueByName("WESiteID"), "partnerID" : getWebExOptionValueByName("WEPartnerID"), "webex_key": booking._webExKey }
        response_xml = sendXMLRequest( request_xml )
        dom = xml.dom.minidom.parseString( response_xml )
        status = dom.getElementsByTagName( "serv:result" )[0].firstChild.toxml('utf-8')
        if status != "SUCCESS":
            errorID = dom.getElementsByTagName( "serv:exceptionID" )[0].firstChild.toxml('utf-8')
            errorReason = dom.getElementsByTagName( "serv:reason" )[0].firstChild.toxml('utf-8')
            booking._warning = WebExWarning( "WebEx error reported: %s" % errorReason )
            return WebExError( errorID, userMessage = errorReason )
        return None

