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

from persistent import Persistent
from MaKaC.plugins.Collaboration.base import CollaborationException, CSErrorBase
from MaKaC.plugins import PluginsHolder
from random import Random
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from datetime import timedelta
import socket
import errno
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.plugins.Collaboration.CERNMCU.fossils import IRoomWithH323Fossil, ICERNMCUErrorFossil
from MaKaC.plugins.Collaboration.CERNMCU.fossils import IParticipantPersonFossil,\
    IParticipantRoomFossil, IRoomWithH323Fossil, ICERNMCUErrorFossil
from indico.util.string import safe_upper

secondsToWait = 10

def getCERNMCUOptionValueByName(optionName):
    return CollaborationTools.getOptionValue('CERNMCU', optionName)

def getMinMaxId():
    idRangeString = getCERNMCUOptionValueByName("idRange")
    return tuple([int(s) for s in idRangeString.split('-')])

def getRangeLength():
    idRangeString = getCERNMCUOptionValueByName("idRange")
    minimum, maximum = [int(s) for s in idRangeString.split('-')]
    return maximum - minimum

def getMinStartDate(conference):
    return conference.getAdjustedStartDate() - timedelta(0,0,0,0, getCERNMCUOptionValueByName("extraMinutesBefore"))

def getMaxEndDate(conference):
    return conference.getAdjustedEndDate() + timedelta(0,0,0,0, getCERNMCUOptionValueByName("extraMinutesAfter"))

def getGlobalData():
    return PluginsHolder().getPluginType('Collaboration').getPlugin('CERNMCU').getGlobalData()

class GlobalData(Persistent):

    def __init__(self):
        self._usedIds = set()
        self._randomGenerator = Random()
        self._min = None
        self._max = None
        self._idList = None
        self._counter = 0

    def getNewConferenceId(self):
        if self._idList is None:
            self._min, self._max = getMinMaxId()
            self._idList = range(self._min, self._max + 1)
            self._randomGenerator.shuffle(self._idList)
            self._counter = 0

        if len(self._usedIds) > self._max - self._min + 1:
            raise CERNMCUException("No more Conference ids available for the MCU")

        while True:
            mcuConferenceId = self._idList[self._counter % len(self._idList)]
            self._counter = self._counter + 1
            if not mcuConferenceId in self._usedIds:
                break

        return mcuConferenceId

    def getMinMax(self):
        return self._min, self._max

    def resetIdList(self):
        self._idList = None

    def addConferenceId(self, mcuConferenceId):
        self._usedIds.add(mcuConferenceId)

    def removeConferenceId(self, mcuConferenceId):
        self._usedIds.remove(mcuConferenceId)


class Participant(Persistent):

    def __init__(self, personOrRoom, booking, participantIndicoId, ip,
                 participantName = None, participantType = "by_address", participantProtocol = "h323",
                 createdByIndico = True):
        """ personOrRoom: a string which can be "person" or "room"
            booking: the CSBooking object parent of this participant
            participantIndicoId: an auto-increment integer, indexing the participants of the same booking, no matter their nature
            participantName: if left to None, we will generate it, example: i-c10b2p4
                             otherwise, we pick whatever comes as argument (useful for ad-hoc participants)
            participantType: the participantType attribute of this participant in the MCU (can be by_address for Indico created
                             participants, ad_hoc for ad_hoc ones, by_name for permanent ones pre-configured in the MCU)
            participantProtocol: the participantProtocol attribute of the participant in the MCU
            createdByIndico: a boolean stating if the participant was created by Indico or was created by someone else in the MCU.
        """

        self._type = personOrRoom
        self._booking = booking
        self._id = participantIndicoId
        self._ip = ip

        self._participantName = participantName

        self._participantType = participantType
        self._participantProtocol = participantProtocol
        self._createdByIndico = createdByIndico

        self._callState = "dormant" #dormant: at creation, before start. others: connected (after start), disconnected (after stop or ad hoc when leaves)

    def updateData(self, newData):
        """ To be overloaded by inheriting classes
        """
        pass

    def isCreatedByIndico(self):
        """
        Who created it? Indico or MCU, remotely?
        """
        return self._createdByIndico

    def getType(self):
        return self._type

    def getId(self):
        return self._id

    def getParticipantName(self):
        """ During booking creation, this method should not be called before
            the booking object has an id (see CSBookingManager.createBooking method).
        """
        if not hasattr(self, "_participantName") or self._participantName is None:
            self._participantName = self._createParticipantName()
        return self._participantName

    def getDisplayName(self):
        """ To be overloaded by inheriting classes
        """
        pass

    def getIp(self):
        return self._ip

    def setIp(self, ip):
        self._ip = ip

    def getParticipantType(self):
        if not hasattr(self, "_participantType"):
            self._participantType = "by_address"
        return self._participantType

    def setParticipantType(self, participantType):
        self._participantType = participantType

    def getParticipantProtocol(self):
        if not hasattr(self, "_participantProtocol"):
            self._participantProtocol = "h323"
        return self._participantProtocol

    def setParticipantProtocol(self, participantProtocol):
        self._participantProtocol = participantProtocol

    def getCallState(self):
        if not hasattr(self, "_callState"):
            self._callState = "dormant"
        return self._callState

    def setCallState(self, callState):
        self._callState = callState

    def _createParticipantName(self):
        confId = self._booking.getConference().getId()
        bookingId = self._booking.getId()
        participantName = "i-c%sb%sp%s" % (confId, bookingId, self._id)
        if len(participantName) > 31:
            raise CERNMCUException("Generated participantName is longer than 31 characters. Conf %s, booking %s, participant %s (%s)" %
                                   (confId, bookingId, self._id, self.getDisplayName()))
        return participantName


class ParticipantPerson(Participant, Fossilizable):
    fossilizes(IParticipantPersonFossil)

    def __init__(self, booking, participantIndicoId, data):

        self._title = data.get("title", '')
        self._familyName = data.get("familyName", '')
        self._firstName = data.get("firstName", '')
        self._affiliation = data.get("affiliation", '')

        Participant.__init__(self, 'person', booking, participantIndicoId, data.get("ip",''),
                             participantName = None, participantType = "by_address", participantProtocol = data.get("participantProtocol", "h323"),
                             createdByIndico = True)

    def updateData(self, newData):
        self._title = newData.get("title", '')
        self._familyName = newData.get("familyName", '')
        self._firstName = newData.get("firstName", '')
        self._affiliation = newData.get("affiliation", '')
        self._participantProtocol = newData.get("participantProtocol", '')
        self.setIp(newData.get("ip", ''))

    def getTitle(self):
        return self._title

    def getFamilyName(self):
        return self._familyName

    def getFirstName(self):
        return self._firstName

    def getAffiliation(self):
        return self._affiliation

    def getDisplayName(self, truncate=True):
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
        result = "".join(result)
        if truncate:
            return result[:31] #31 is the max length accepted by the MCU
        else:
            return result

class ParticipantRoom(Participant, Fossilizable):
    fossilizes(IParticipantRoomFossil)

    def __init__(self, booking, participantIndicoId, data,
                 participantName = None, participantType = "by_address",
                 createdByIndico = True):

        self._name = data.get("name",'')
        self._institution = data.get("institution", '')

        Participant.__init__(self, 'room', booking, participantIndicoId, data.get("ip",''),
                             participantName, participantType, data.get("participantProtocol", "h323"),
                             createdByIndico)

    def updateData(self, newData):
        self._name = newData.get("name",'')
        self._institution = newData.get("institution", '')
        self._participantProtocol = newData.get("participantProtocol", '')
        self.setIp(newData.get("ip", ''))

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name

    def getInstitution(self):
        if not hasattr(self, '_institution'):
            self._institution = ''
        return self._institution

    def setInstitution(self, institution):
        self._institution = institution

    def getDisplayName(self, truncate=True):
        result = self._name
        if self._institution:
            result = result + ' (' + self._institution + ')'
        if truncate:
            return result[:31] #31 is the max length accepted by the MCU
        else:
            return result


class RoomWithH323(Fossilizable):
    fossilizes(IRoomWithH323Fossil)

    def __init__(self, institution, name, ip):
        self._institution = institution
        self._name = name
        self._ip = ip

    def getLocation(self):
        return self._institution

    def getName(self):
        return self._name

    def getIp(self):
        return self._ip



class CERNMCUError(CSErrorBase): #already fossilizable
    fossilizes(ICERNMCUErrorFossil)

    def __init__(self, faultCode, info = ''):
        self._faultCode = faultCode
        self._info = info

    def getFaultCode(self):
        return self._faultCode

    def getInfo(self):
        return self._info

    def setInfo(self, info):
        self._info = info

    def getUserMessage(self):
        return ''

    def getLogMessage(self):
        message = "CERNMCU Error. Fault code: " + str(self._faultCode)
        if self._info:
            message += ". Info: " + str(self._info)
        return message

class CERNMCUException(CollaborationException):
    def __init__(self, msg, inner = None):
        CollaborationException.__init__(self, msg, 'CERN MCU', inner)

def handleSocketError(e):
    if e.args[0] == errno.ETIMEDOUT:
        raise CERNMCUException("CERN's MCU may be offline. Indico encountered a network problem while connecting with the MCU at " + getCERNMCUOptionValueByName('MCUAddress') + ". Connection with the MCU timed out after %s seconds"%secondsToWait)
    elif e.args[0] == errno.ECONNREFUSED:
        raise CERNMCUException("CERN's MCU seems to have problems. Network problem while connecting with the MCU at " + getCERNMCUOptionValueByName('MCUAddress') + ". The connection with the MCU was refused.")
    elif isinstance(e, socket.gaierror) and e.args[0] == socket.EAI_NODATA:
        raise CERNMCUException("Network problem while connecting with the MCU at " + getCERNMCUOptionValueByName('MCUAddress') + ". Indico could not resolve the IP address for that host name.")
    else:
        raise CERNMCUException("Network problem while connecting with the MCU at " + getCERNMCUOptionValueByName('MCUAddress') + ". Problem: " + str(e))

