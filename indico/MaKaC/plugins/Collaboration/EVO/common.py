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


from MaKaC.plugins.Collaboration.base import CollaborationException, CSErrorBase
from urllib2 import HTTPError, URLError, urlopen
from datetime import timedelta
from BaseHTTPServer import BaseHTTPRequestHandler
from MaKaC.common.url import URL
from array import array
from MaKaC.common.timezoneUtils import nowutc, datetimeToUnixTime
from MaKaC.common.logger import Logger
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.plugins.Collaboration.EVO.fossils import IEVOWarningFossil,\
    IEVOErrorFossil, IOverlappedErrorFossil, IChangesFromEVOErrorFossil

readLimit = 100000;
secondsToWait = 15;
encodingTextStart = '<fmt:requestEncoding value='
encodingTextEnd = '/>'

def getEVOOptionValueByName(optionName):
    return CollaborationTools.getOptionValue('EVO', optionName)

def getActionURL(actionString):
    EVOServerURL = getEVOOptionValueByName("httpServerLocation")
    actionServlet = getEVOOptionValueByName("APIMap")[actionString]
    if EVOServerURL.endswith('/'):
        return EVOServerURL + actionServlet
    else:
        return EVOServerURL + '/' + actionServlet

def getRequestURL(action, arguments = {}):

    actionURL = getActionURL(action)

    indicoID = getEVOOptionValueByName("indicoUserID")
    indicoPassword = getEVOOptionValueByName("indicoPassword")
    expirationTime = int(datetimeToUnixTime(nowutc() + timedelta(minutes = getEVOOptionValueByName('expirationTime'))) * 1000)

    arguments["from"] = createLoginKey(indicoID, indicoPassword, expirationTime)

    url = URL(actionURL)
    url.setParams(arguments)

    return url

def getEVOAnswer(action, arguments = {}, eventId = '', bookingId = ''):

    url = getRequestURL(action, arguments)

    Logger.get('EVO').info("""Evt:%s, booking:%s, sending request to EVO: [%s]""" % (eventId, bookingId, str(url)))

    try:
        answer = urlopen(str(url), timeout=secondsToWait).read(readLimit).strip() #we remove any whitespaces, etc. We won't read more than 100k characters
        Logger.get('EVO').info("""Evt:%s, booking:%s, got answer (unprocessed): [%s]""" % (eventId, bookingId, str(answer)))

    except HTTPError, e:
        code = e.code
        shortMessage = BaseHTTPRequestHandler.responses[code][0]
        longMessage = BaseHTTPRequestHandler.responses[code][1]

        Logger.get('EVO').error("""Evt:%s, booking:%s, request: [%s] triggered HTTPError: %s (code = %s, shortMessage = '%s', longMessage = '%s'""" % (eventId, bookingId, str(url), str(e), code, shortMessage, longMessage))

        if str(code) == '404':
            raise EVOException('Indico could not find the EVO Server at ' + getEVOOptionValueByName("httpServerLocation") + "(HTTP error 404)")
        elif str(code) == '500':
            raise EVOException("The EVO server has an internal problem (HTTP error 500)", e)
        else:
            raise EVOException("""Problem when Indico tried to contact the EVO Server.\nReason: HTTPError: %s (code = %s, shortMessage = '%s', longMessage = '%s', url = '%s'""" % (str(e), code, shortMessage, longMessage, str(url)), e)

    except URLError, e:
        Logger.get('EVO').error("""Evt:%s, booking:%s, request: [%s] triggered exception: %s""" % (eventId, bookingId, str(url), str(e)))
        if str(e.reason).strip() == 'timed out':
            raise EVOException("The EVO server is not responding.", e)
        raise EVOException('URLError when contacting the EVO server for action: ' + action + '. Reason="' + str(e.reason)+'"', e)

    else: #we parse the answer
        encodingTextStart = '<fmt:requestEncoding value='
        encodingTextEnd = '/>'

        answer = answer.strip()

        #we parse an eventual encoding specification, like <fmt:requestEncoding value="UTF-8"/>
        if answer.startswith(encodingTextStart):
            endOfEncondingStart = answer.find(encodingTextStart) + len(encodingTextStart)
            endOfEncodingEnd = answer.find(encodingTextEnd) + len(encodingTextEnd)
            valueStartIndex = max(answer.find('"', endOfEncondingStart, endOfEncodingEnd), answer.find("'", endOfEncondingStart, endOfEncodingEnd)) + 1 #find returns -1 if not found
            valueEndIndex = max(answer.find('"', valueStartIndex, endOfEncodingEnd), answer.find("'", valueStartIndex, endOfEncodingEnd))
            encoding = answer[valueStartIndex:valueEndIndex].strip()

            answer = answer[endOfEncodingEnd:].strip()
            answer = answer.decode(encoding).encode('utf-8')

        if answer.startswith("OK:"):
            answer = answer[3:].strip() #we remove the "OK:"
            Logger.get('EVO').info("""Evt:%s, booking:%s, got answer (processed): [%s]""" % (eventId, bookingId, str(answer)))
            return answer

        elif answer.startswith("ERROR:"):
            error = answer[6:].strip()
            Logger.get('EVO').warning("""Evt:%s, booking:%s, request: [%s] triggered EVO error: %s""" % (eventId, bookingId, str(url), error))
            if error == 'YOU_ARE_NOT_OWNER_OF_THE_MEETING' or error == 'NOT_AUTHORIZED_SERVER' or error == 'NOT_AUTHORIZED' or\
                error == 'LOGIN_KEY_WRONG_LENGTH':
                raise EVOException("Indico's EVO ID / pwd do not seem to be right. Please report to Indico support.", error)
            elif error == 'REQUEST_EXPIRED':
                raise EVOException("Problem contacting EVO: REQUEST_EXPIRED", 'REQUEST_EXPIRED. Something is going wrong with the UNIX timestamp?');
            elif error == 'WRONG_EXPIRATION_TIME':
                raise EVOException("Problem contacting EVO; WRONG_EXPIRATION_TIME", 'REQUEST_EXPIRED. Something is going wrong with the UNIX timestamp?');
            else:
                raise EVOControlledException(error)
        else:
            raise EVOException('Error when contacting the EVO server for action: ' + action + '. Message from the EVO server did not start by ERROR or OK', answer)

def parseEVOAnswer(answer):
    """ Parses an answer such as
        meet=48760&&start=0&&end=1000&&com=4&&type=0&&title=NewTestTitle&&desc=TestDesc&&url=[meeting=e9eIeivDveaeaBIDaaI9]
        and returns a tuple of attributes.
        the url attribute is transformed to the real koala URL
    """

    attributesStringList = answer.split('&&')
    attributes = {}
    for attributeString in attributesStringList:
        name, value = attributeString.split('=',1)
        name = name.strip()
        value = value.strip()
        if name == 'url':
            value = value[1:-1].strip() #we remove the brackets
            if value.startswith("meeting"): #the first part of the URL is not there
                value = getEVOOptionValueByName("koalaLocation") + '?' + value
        attributes[name] = value
    return attributes


def createLoginKey(EVOID, password, time):
    """ Obfuscates an EVOID / password couple with a unix timestamp
        EVOID has to be an 8 digit (max) number / string number, ex: 123 or '123'
        password has to be a 4 digits password, ex: 1234 or '1234'
        time is unix time in milliseconds (13 digits max), ex: 12345

        Returns an "obfuscated" EVO login key of 25 characters.
    """
    EVOID = str(EVOID)
    password = str(password)
    time = str(time)

    if len(EVOID) > 8:
        raise EVOException("EVOID has to be 8 digits max")
    if len(password) != 4:
        raise EVOException("password has to be 4 digits")
    if len(time) > 13:
        raise EVOException("unix time has to be 13 digits max")

    key = array('c', ' '*25)
    EVOID = EVOID.zfill(8)
    time = time.zfill(13)

    for index, char in enumerate(time):
        key[index*2] = char

    for index, char in enumerate(EVOID):
        key[19 - index * 2] = char

    key[1] = password[0]
    key[21] = password[1]
    key[3] = password[2]
    key[23] = password[3]

    return key.tostring()


def parseLoginKey(key):
    """ Parses an "obfuscated" EVO login key of 25 characters.
        Returns a tuple (EVOID, password, time)
        EVOID will be an string with a number of maximum 8 digits.
        time will be an integer, UNIX time in millesconds (13 digits max)
        password will be a string of 4 characters
    """
    if len(key) != 25:
        raise EVOException("key has to be a string of 25 characters")

    EVOID = str(int("".join([key[i] for i in range (19,3,-2)])))
    time = int("".join([key[i] for i in range(0,25,2)]))
    password = "".join([key[1],key[21], key[3], key[23]])

    return (EVOID, password, time)

def getMinStartDate(conference):
    return conference.getAdjustedStartDate() - timedelta(0,0,0,0, getEVOOptionValueByName("extraMinutesBefore"))

def getMaxEndDate(conference):
    return conference.getAdjustedEndDate() + timedelta(0,0,0,0, getEVOOptionValueByName("extraMinutesAfter"))

class EVOError(CSErrorBase): #already Fossilizable
    fossilizes(IEVOErrorFossil)

    def __init__(self, errorType, requestURL = None, userMessage = None):
        CSErrorBase.__init__(self)
        self._errorType = errorType
        self._requestURL = requestURL
        self._userMessage = None

    def getErrorType(self):
        return self._errorType

    def getRequestURL(self):
        return self._requestURL

    def getUserMessage(self):
        if self._userMessage:
            return self._userMessage
        else:
            if self._errorType == 'duplicated':
                return "This EVO meeting could not be created or changed because EVO considers the resulting meeting as duplicated."
            elif self._errorType == 'start_in_past':
                return "This EVO meeting could not be created or changed because EVO does not allow meetings starting in the past."
            else:
                return self._errorType

    def getLogMessage(self):
        return "EVO Error: " + str(self._errorType) + " for request " + str(self._requestURL)



class OverlappedError(EVOError): #already Fossilizable
    fossilizes(IOverlappedErrorFossil)

    def __init__(self, overlappedBooking):
        EVOError.__init__(self, 'overlapped')
        self._overlappedBooking = overlappedBooking

    def getSuperposedBooking(self):
        return self._overlappedBooking

class ChangesFromEVOError(EVOError): #already Fossilizable
    fossilizes(IChangesFromEVOErrorFossil)

    def __init__(self, changes):
        EVOError.__init__(self, 'changesFromEVO')
        self._changes = changes

    def getChanges(self):
        return self._changes


class EVOException(CollaborationException):
    def __init__(self, msg, inner = None):
        CollaborationException.__init__(self, msg, 'EVO', inner)

class EVOControlledException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "EVOControlledException. Message = " + self.message

class EVOWarning(Fossilizable):
    fossilizes(IEVOWarningFossil)

    def __init__(self, msg, exception = None):
        self._msg = msg
        self._exception = exception

    def getMessage(self):
        return self._msg

    def getException(self):
        return self._exception
