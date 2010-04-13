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

from persistent import Persistent
from MaKaC.plugins.Collaboration.base import CollaborationException, CSErrorBase
from MaKaC.plugins.base import PluginsHolder
from random import Random
from MaKaC.common.PickleJar import Retrieves
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
import socket
import errno

secondsToWait = 10
    
def getCERNMCUOptionValueByName(optionName):
    return CollaborationTools.getOptionValue('CERNMCU', optionName)
    
def getMinMaxId():
    idRangeString = getCERNMCUOptionValueByName("idRange")
    return tuple([int(s) for s in idRangeString.split('-')])

def getRangeLength():
    idRangeString = getCERNMCUOptionValueByName("idRange")
    min, max = [int(s) for s in idRangeString.split('-')]
    return max - min

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
            id = self._idList[self._counter % len(self._idList)]
            self._counter = self._counter + 1
            if not id in self._usedIds:
                break
        
        return id
    
    def getMinMax(self):
        return self._min, self._max
    
    def resetIdList(self):
        self._idList = None
    
    def addConferenceId(self, id):
        self._usedIds.add(id)
    
    def returnConferenceId(self, id):
        self._usedIds.remove(id)
        
class Participant(Persistent):
    def __init__(self, type, booking, id, ip, createdByIndico = True):
        self._type = type
        self._booking = booking
        self._id = id
        self._ip = ip
        self._createdByIndico = createdByIndico
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson',
                'MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantRoom'], 'type')
    def getType(self):
        return self._type
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson',
                'MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantRoom'], 'participantId')
    def getId(self):
        return self._id
    
    def getParticipantName(self):
        if self._createdByIndico:
            confId = self._booking.getConference().getId()
            bookingId = self._booking.getId()
            return "p%sb%sc%s"%(self._id, bookingId, confId)
        else:
            return self._id
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson',
                'MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantRoom'], 'ip')
    def getIp(self):
        return self._ip
        
class ParticipantPerson(Participant):
    def __init__(self, booking, id, data):
        Participant.__init__(self, 'person', booking, id, data.get("ip",''))
        self._title = data.get("title", '')
        self._familyName = data.get("familyName", '')
        self._firstName = data.get("firstName", '')
        self._affiliation = data.get("affiliation", '')
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson'], 'title')
    def getTitle(self):
        return self._title
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson'], 'familyName')
    def getFamilyName(self):
        return self._familyName
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson'], 'firstName')
    def getFirstName(self):
        return self._firstName
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantPerson'], 'affiliation')
    def getAffiliation(self):
        return self._affiliation
    
    def getDisplayName(self):
        result = []
        if self._title:
            result.append(self._title)
            result.append(' ')
        result.append(self._familyName.upper())
        result.append(', ')
        result.append(self._firstName)
        if self._affiliation:
            result.append(' (')
            result.append(self._affiliation)
            result.append(')')
        return ("".join(result))[:31] #31 is the max length accepted by the MCU
        
    
    
class ParticipantRoom(Participant):
    def __init__(self, booking, id, data):
        Participant.__init__(self, 'room', booking, id, data.get("ip",''))
        self._name = data.get("name",'')
        self._institution = data.get("institution", '')
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantRoom'], 'name')
    def getName(self):
        return self._name
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.ParticipantRoom'], 'institution')
    def getInstitution(self):
        if not hasattr(self, '_institution'):
            self._institution = ''
        return self._institution
    
    def getDisplayName(self):
        result = self._name
        if self._institution:
            result = result + ' (' + self._institution + ')'
        return result[:31] #31 is the max length accepted by the MCU
    
class RoomWithH323(object):
    def __init__(self, institution, name, ip):
        self._institution = institution
        self._name = name
        self._ip = ip
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.RoomWithH323'], 'institution')
    def getLocation(self):
        return self._institution
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.RoomWithH323'], 'name')
    def getName(self):
        return self._name
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.RoomWithH323'], 'ip')
    def getIP(self):
        return self._ip
    
    
class CERNMCUError(CSErrorBase):
    
    def __init__(self, faultCode, info = ''):
        CSErrorBase.__init__(self)
        self._faultCode = faultCode
        self._info = info
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUError'], 'origin')
    def getOrigin(self):
        return 'CERNMCU'
        
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUError'], 'faultCode')
    def getFaultCode(self):
        return self._faultCode
    
    @Retrieves(['MaKaC.plugins.Collaboration.CERNMCU.common.CERNMCUError'], 'info')
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

