# -*- coding: utf-8 -*-
##
## $Id: common.py,v 1.12 2009/04/25 13:56:05 dmartinc Exp $
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


import httplib
from persistent import Persistent
from MaKaC.plugins.Collaboration.base import CSErrorBase
from datetime import timedelta, datetime
from time import strptime
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.plugins.Collaboration.WebEx.fossils import IWebExWarningFossil, IWebExErrorFossil, \
    IChangesFromWebExErrorFossil, IParticipantFossil
from indico.util.string import safe_upper
from cgi import escape
from MaKaC.i18n import _

def unescape(s):
    s = s.replace("&lt;","<")
    s = s.replace("&gt;",">")
    s = s.replace("&apos;","'")
    s = s.replace("&quot;",'"')
    s = s.replace("&amp;","&")
    return s

def sendXMLRequest(xml):
    conn = httplib.HTTPSConnection( getWebExOptionValueByName("WEhttpServerLocation") )
    conn.request( "POST", "/WBXService/XMLService", xml )
    r = conn.getresponse()
    response_xml = r.read()
#    Logger.get('WebEx').debug( "WebEx Response:\n\n\n\n%s" % ( response_xml ) )
    return response_xml

def getWebExOptionValueByName(optionName):
    return CollaborationTools.getOptionValue('WebEx', optionName)

def makeParticipantXML( participants ):
    """
    This function takes a string of email addresses (seperated by "\n" or "," or ";"
    and will return WebEx compliant <participant><attendee></attendee></participant>
    tags
    """
    if len(participants) < 1:
        return ""
    participants_xml = "<participants><attendees>\n"
    for p in participants.itervalues():
        p_xml = """<attendee>
  <person>
    <firstName>%(firstName)s</firstName>
    <lastName>%(lastName)s</lastName>
    <email>%(email)s</email>
  </person>
</attendee>
""" % { "firstName": escape(p._firstName), "lastName":escape(p._familyName), "email":p._email }
        participants_xml = participants_xml + p_xml
    participants_xml = participants_xml + "</attendees></participants>\n"
    return participants_xml

def findDuration(start, finish):
    """
    This function returns the duration of the meeting in minues
    Pass in dates of the form self.getAdjustedStartDate('UTC'))[:-9]
    self.getAdjustedEndDate('UTC'))[:-9]
    """
    t1 = makeTime( start )
    t2 = makeTime( finish )
    diff = t2 - t1
    minutes,seconds = divmod(diff.seconds, 60)
    return minutes + diff.days * 1440

def makeTime(the_dateTime):
    """
    This function will return a datetime object
    representing the time passed in in the form created from the
    timezone functions like getAdjustedStartDate('UTC')
    """
    return datetime( *strptime( str(the_dateTime)[0:16], "%Y-%m-%d %H:%M" )[0:7])

def getMinStartDate(conference):
    return conference.getAdjustedStartDate() - timedelta(0,0,0,0, getWebExOptionValueByName("allowedMinutes"))

def getMaxEndDate(conference):
    return conference.getAdjustedEndDate() + timedelta(0,0,0,0, getWebExOptionValueByName("allowedMinutes"))

class WebExError(CSErrorBase):
    fossilizes(IWebExErrorFossil)

    def __init__(self, errorID = None, errorType = None, requestURL = None, userMessage = None):
        self._errorID = errorID
        self._errorType = errorType
        self._requestURL = requestURL
        self._userMessage = userMessage

        if self._errorID == "000000":
            self._errorType = "webex_server_error"
            self._userMessage = _("Unknown error with WebEx server.")
        elif self._errorID == "019011":
            self._errorType = "webex_invalid_pass_characters"  #The message from WebEx is descriptive
        elif self._errorID == "030001" or self._errorID == "030006":
            self._errorType = "webex_invalid_user"
            self._userMessage = _("This WebEx server does not recognize the user ID provided.")
        elif self._errorID == "030007" or self._errorID == "030008":
            self._errorType = "webex_expired_user"
            self._userMessage = _("This WebEx user account is expired or inactive.")
        elif self._errorID == "030002":
            self._errorType = "webex_invalid_pass"
            self._userMessage = _("Invalid password for this WebEx user")
        elif self._errorID == "060001":
            self.errorType = "webex_meeting_not_found_error"
            self._userMessage = _("This WebEx meeting ID could not be located on the WebEx server")
        elif self._errorID == "060017":
            self._errorType = "webex_duration_error"
            self._userMessage = _("The booking duration exceeds the maximum time duration limit set on this WebEx server.")
        elif self._errorID == "060026":
            self._errorType = "webex_blank_password"
            self._userMessage = _("The meeting password cannot be left blank on this WebEx server.")
        elif self._errorID == "009001" or self._errorID == "009002" or self._errorID == "009003" or self._errorID == "009004":
            self._errorType = "webex_access_denied"
            self._userMessage = _("The server returned an access denied error")
        elif self._errorID == "009007" or self._errorID == "009008" or self._errorID == "009009":
            self._errorType = "webex_date_error"
            self._userMessage = _("The WebEx server did not accept the dates chosen.")
        elif self._errorID == "009010" or self._errorID == "009011" or self._errorType == "webex_record_not_found":
            self._errorType = "webex_record_not_found"
            self._userMessage = _("The WebEx server was unable to locate the record.")

        if self._errorType == None:
            self._errorType = "webex_unknown"

    def getOrigin(self):
        return 'WebEx'

    def getFaultCode(self):
        return self._errorType

    def getInfo(self):
        return self._userMessage

    def getErrorType(self):
        return self._errorType

    def getRequestURL(self):
        return ""
#        return self._requestURL

    def getUserMessage(self):
        if self._userMessage:
            return self._userMessage
        else:
            return "Unknown error"

    def getLogMessage(self):
        return "WebEx Error: " + str(self._errorType) + " for request " + str(self._requestURL)

class Participant(Persistent,Fossilizable):
    fossilizes(IParticipantFossil)
    def __init__(self, booking, participantIndicoId, data):
        self._id = participantIndicoId
        self._title = data.get("title", '')
        self._familyName = data.get("familyName", '')
        self._firstName = data.get("firstName", '')
        self._affiliation = data.get("affiliation", '')
        self._email = data.get("email", '')

    def updateData(self, newData):
        self._title = newData.get("title", '')
        self._familyName = newData.get("familyName", '')
        self._firstName = newData.get("firstName", '')
        self._affiliation = newData.get("affiliation", '')
        self._email = newData.get("email", '')

    def getId(self):
        return self._id

    def getParticipantName(self):
        return "%s, %s" % ( self.getFamilyName(), self.getFirstName() )

    def getTitle(self):
        return self._title

    def getFamilyName(self):
        return self._familyName

    def getFirstName(self):
        return self._firstName

    def getAffiliation(self):
        return self._affiliation

    def getEmail(self):
        return self._email

    def getDisplayName(self):
        result = []
        if self._title:
            result.append(self._title)
            result.append(' ')
        result.append(safe_upper(self._familyName))
        result.append(', ')
        result.append(self._firstName)
        if self._affiliation:
            result.append(' (')
            result.append(self._affiliation)
            result.append(')')
        return ("".join(result))

class OverlappedError(WebExError):
    def __init__(self, overlappedBooking):
        WebExError.__init__(self, 'overlapped')
        self._overlappedBooking = overlappedBooking

    def getSuperposedBookingId(self):
        return self._overlappedBooking

class ChangesFromWebExError(WebExError):
    fossilizes(IChangesFromWebExErrorFossil)
    def __init__(self, changes):
        WebExError.__init__(self, 'changesFromWebEx')
        self._changes = changes

    def getChanges(self):
        return self._changes

class WebExWarning(Fossilizable):
    fossilizes(IWebExWarningFossil)
    def __init__(self, msg = None, exception = None):
        self._msg = msg
        self._exception = exception

    def getMessage(self):
        return self._msg

    def getException(self):
        return self._exception

