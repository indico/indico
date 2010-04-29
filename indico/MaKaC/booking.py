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

import os
import re
import tempfile
import sets
import os.path
import copy
from pytz import timezone
from datetime import datetime,timedelta
import ZODB
from persistent import Persistent
from persistent.list import PersistentList
from BTrees.OOBTree import OOBTree
from BTrees.OIBTree import OIBTree,OISet,union
import MaKaC.common.indexes as indexes 
import MaKaC.fileRepository as fileRepository
import MaKaC.schedule as schedule
import MaKaC.review as review
from MaKaC.common import Config, DBMgr
from MaKaC.common.Counter import Counter
from MaKaC.common.ObjectHolders import ObjectHolder, IndexHolder
from MaKaC.common.Locators import Locator
from MaKaC.accessControl import AccessController
from MaKaC.common.timerExec import HelperTaskList, Alarm
from MaKaC.errors import MaKaCError, TimingError, ParentTimingError
from MaKaC import registration
from MaKaC.i18n import _

import urllib,httplib

class Booking(Persistent):
    
    def __init__(self, conference):
        
        self._id = ""
        self._name = ""
        self._avatar = None
        self._description = ""
        self._conf = conference
        self._room = ""
        self._system = ""
        self._startingDate = ""
        self._endingDate = ""
        self._mailingList = ""
        self._tz = self._conf.getTimezone()
        
    def setValues(self, data):
        self.setTitle(data["title"])
        self.setDescription(data["description"])
        self.setStartingDate(timezone(self._tz).localize(datetime(int(data["sYear"]), int(data["sMonth"]), int(data["sDay"]), int(data["sHour"]), int(data["sMinute"]))).astimezone(timezone('UTC')))
        self.setEndingDate(timezone(self._tz).localize(datetime(int(data["eYear"]), int(data["eMonth"]), int(data["eDay"]), int(data["eHour"]), int(data["eMinute"]))).astimezone(timezone('UTC')))
        self.setRoom(data["locationRoom"])
        self.setSupportEmail(data["supportEmail"])
        self.setComments(data["comments"])

    def getId(self):
        return self._id
    
    def setId(self, id):
        self._id = id
    
    def getTitle(self):
        return self._name
    
    def setTitle(self, name):
        self._name = name
    
    def setStartingDate(self, startingDate):
        self._startingDate = startingDate
    
    def setEndingDate(self, endingDate):
        self._endingDate = endingDate
    
    def getEndingDate(self):
        return self._endingDate

    def getStartingDate(self):
        return self._startingDate
    
    def setTitle(self, name):
        self._name = name
    
    def setDescription(self, description):
        self._description = description
    
    def setComments(self, comments):
        self._comments = comments
        
    def getComments(self):
        return self._comments
    
    def getDescription(self):
        return self._description
    
    def setRoom(self,room):
        self._room=room
        
    def getRoom(self):
        return self._room

    def setSupportEmail (self, mailingList):
        self._mailingList = mailingList

    def getSupportEmail (self):
        return self._mailingList

    def getSystem(self):
        return self._system
        
    def setConference(self, conf):
        self._conf = conf
        
    def getConference(self):
        try:
            if self._conf:
                pass
        except AttributeError:
            self._conf=None
        return self._conf
        
    def getLocator( self ):
        """Gives back (Locator) a globally unique identification encapsulated in 
            a Locator object for the booking instance """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        lconf["bookingId"] = self.getId()
        return lconf

    def deleteBooking(self):
        pass

    def getPublicDescription(self):
        pass

class VRVSBooking (Booking):

    def __init__(self, conference):

        Booking.__init__(self, conference)
        self._system = "VRVS"
        self._protectionpasswd = ""
        self._data = {}
        
    def getCommunity(self):
        return self._vrvscommunity
        
    def setCommunity(self, vrvscommunity):
        self._vrvscommunity = vrvscommunity

    def getVirtualRoom(self):
        return self._virtualroom
        
    def setVirtualRoom(self, virtualroom):
        self._virtualroom = virtualroom
        
    def getVRVSuser(self):
        return self._vrvsuser
        
    def setVRVSuser(self, vrvsuser):
        self._vrvsuser = vrvsuser

    def getVRVSpasswd(self):
        return self._vrvspasswd

    def setVRVSpasswd(self, vrvspasswd):
        self._vrvspasswd = vrvspasswd
        
    def getProtectionPasswd (self):
        return self._protectionpasswd
    
    def setProtectionPasswd (self, protectionpasswd):
        self._protectionpasswd = protectionpasswd
        
    def getValues (self,data):
        
        data["title"] = Booking.getTitle(self)
        data["virtualRoom"] = self.getVirtualRoom()
        data["vrvsLogin"] = self.getVRVSuser()
        data["vrvsCommunity"] = self.getCommunity()
        data["startingDateTime"] = self.getStartingDate().strftime("%Y-%m-%d_%H:%M")
        data["endingDateTime"] = self.getEndingDate().strftime("%Y-%m-%d_%H:%M")
        data["vrvsPasswd"]= self.getVRVSpasswd()
        return data
    
    def setValues(self,data):
        Booking.setValues(self, data)
        self.setVirtualRoom(data["virtualRoom"])
        self.setVRVSuser(data["vrvsLogin"])
        self.setVRVSpasswd(data["vrvsPasswd"])
        self.setCommunity(data["vrvsCommunity"])
        if data["accessPasswd"].strip()!="":
            self.setProtectionPasswd(data["accessPasswd"])

    def deleteBooking(self):
        
        params= {}
        self.getValues(params)
        headers={'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        conn = httplib.HTTPConnection("www.vrvs.org:80")
        conn.request("POST", "/cgi-perl/directDeleteBooking?%s::%s::%s::%s::%s::%s::%s" %(\
        params['vrvsLogin'],params['vrvsCommunity'],params['vrvsPasswd'], params['virtualRoom'], params['startingDateTime'], params['endingDateTime'],params['title'].replace(" ","_")), \
        "",headers)
        response = conn.getresponse()
        if response.status != 200:
            data = [response.status, response.reason] 
            return (1, "Server Error") 
        else: 
            data = response.read().split("::")
            if (data[0].strip() == "ERROR" and data[1].strip() == _("Can't find this reservation!")):        
                data[0] = "Warning"
                data[1] = _("The Booking had been already removed in VRVS server!")
                return data
            return data
        
    def getPublicDescription(self):
        return _("Virtual room %s") % self.getVirtualRoom()
