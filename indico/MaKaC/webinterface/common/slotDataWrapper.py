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

from datetime import timedelta,datetime
from MaKaC.i18n import _
from MaKaC.errors import MaKaCError, NoReportError
from pytz import timezone

class Convener:

    def __init__(self,id,data={}):
        self._id=id
        self.setValues(data)

    def setValues(self, data):
        self._title=data.get("conv_title","")
        self._firstName=data.get("conv_first_name","")
        self._familyName=data.get("conv_family_name","")
        self._affiliation=data.get("conv_affiliation","")
        self._email=data.get("conv_email","")

    def mapConvener(self,conv):
        self._title=conv.getTitle()
        self._firstName=conv.getFirstName()
        self._familyName=conv.getSurName()
        self._affiliation=conv.getAffiliation()
        self._email=conv.getEmail()

    def getTitle(self):
        return self._title

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getFirstName(self):
        return self._firstName

    def getFamilyName(self):
        return self._familyName

    def getAffiliation(self):
        return self._affiliation

    def getEmail(self):
        return self._email

class Slot:

    def __init__(self, data={}):
        self.setValues(data)

    def setValues(self, data):
        self._id=data.get("id","")
        self._session=data.get("session",None)
        self._title=data.get("title", "")
        if data.get("locationAction","") == "inherit":
            data["locationName"] = ""
        if data.get("roomAction","") == "inherit":
            data["roomName"] = ""
        self._locationName=data.get("locationName","")
        self._locationAddress=data.get("locationAddress","")
        self._roomName=data.get("roomName","")
        self._startDate=None
        self._endDate=None
        if data:
            tz = self._session.getConference().getTimezone()

            if data.has_key("sDate"):
                self._startDate=data["sDate"]
            elif data.get("sYear","")!="" and data.get("sMonth","")!="" and \
                    data.get("sDay","")!="" and data.get("sHour","")!="" and \
                    data.get("sMinute","")!="":
                self._startDate=timezone(tz).localize(datetime( int( data["sYear"] ), \
                                        int( data["sMonth"] ), \
                                        int( data["sDay"] ), \
                                        int( data["sHour"] ), \
                                        int( data["sMinute"] ) ) )

            if data.has_key("eDate"):
                self._endDate=data["eDate"]
            elif data.get("eYear","")!="" and data.get("eMonth","")!="" and \
                    data.get("eDay","")!="" and data.get("eHour","")!="" and \
                    data.get("eMinute","")!="":
                self._endDate=timezone(tz).localize(datetime( int( data["eYear"] ), \
                                    int( data["eMonth"] ), \
                                    int( data["eDay"] ), \
                                    int( data["eHour"] ), \
                                    int( data["eMinute"] ) ) )
        self._duration=None
        if data.get("durHours","")!="" and data.get("durMins","")!="":
            self._duration = timedelta(hours=int(data["durHours"]),minutes=int(data["durMins"]))
        self._contribDuration=None
        if data.get("contribDurHours","")!="" and data.get("contribDurMins","")!="":
            self._contribDuration=timedelta(hours=int(data["contribDurHours"]),minutes=int(data["contribDurMins"]))
        elif data.get("contribDuration","")!="":
            self._contribDuration= data.get("contribDuration")
        self._conveners=[]
        for i in range(len(data.get("conv_id",[]))):
            val={   "conv_title":data["conv_title"][i],
                    "conv_first_name":data["conv_first_name"][i],
                    "conv_family_name":data["conv_family_name"][i],
                    "conv_affiliation":data["conv_affiliation"][i],
                    "conv_email":data["conv_email"][i] }
            id=len(self._conveners)
            self._conveners.append(Convener(id,val))

    def mapSlot(self, slot):
        self._id=slot.getId()
        self._session=slot.getSession()
        self._title=slot.getTitle()
        self._locationName=""
        self._locationAddress=""
        location = slot.getOwnLocation()
        if location is not None:
            self._locationName=location.getName()
            self._locationAddress=location.getAddress()
        self._roomName=""
        room = slot.getOwnRoom()
        if room is not None:
            self._roomName=room.getName()
        self._startDate=slot.getStartDate()
        self._endDate=slot.getEndDate()
        self._duration=slot.getDuration()
        self._contribDuration=slot.getContribDuration()
        self._conveners=[]
        for conv in slot.getOwnConvenerList():
            val={   "conv_title":conv.getTitle(),
                    "conv_first_name":conv.getFirstName(),
                    "conv_family_name":conv.getFamilyName(),
                    "conv_affiliation":conv.getAffiliation(),
                    "conv_email":conv.getEmail() }
            id=len(self._conveners)
            self._conveners.append(Convener(id,val))

    def getId(self):
        return self._id

    def getSession(self):
        return self._session

    def getTitle(self):
        return self._title

    def getLocationName(self):
        return self._locationName

    def getLocationAddress(self):
        return self._locationAddress

    def getRoomName(self):
        return self._roomName

    def getStartDate(self):
        return self._startDate

    def getAdjustedStartDate(self):
        return self._startDate.astimezone(timezone(self.getSession().getTimezone()))

    def getEndDate(self):
        return self._endDate

    def getAdjustedEndDate(self):
        return self._endDate.astimezone(timezone(self.getSession().getTimezone()))

    def getDuration(self):
        return self._duration

    def getContribDuration(self):
        return self._contribDuration

    def getConvenerList(self):
        return self._conveners

    def hasErrors(self):
        return False

    def checkErrors(self):
        for conv in self.getConvenerList():
            if conv.getFirstName().strip() == "":
                raise NoReportError( _("FIRST NAME has not been specified for convener #%s")%idx )
            if conv.getFamilyName().strip() == "":
                raise NoReportError( _("SURNAME has not been specified for convener #%s")%idx )
            if conv.getAffiliation().strip() == "":
                raise NoReportError( _("AFFILIATION has not been specified for convener #%s")%idx )
            if conv.getEmail().strip() == "":
                raise NoReportError( _("EMAIL has not been specified for convener #%s")%idx )

    def updateSlot(self,slot):
        slot.setTitle(self.getTitle())
        slot.setself._locationName=""
        self._locationAddress=""
        location = slot.getOwnLocation()
        if location is not None:
            self._locationName=location.getName()
            self._locationAddress=location.getAddress()
        self._roomName=""
        room = slot.getOwnRoom()
        if room is not None:
            self._roomName=room.getName()
        self._startDate=slot.getStartDate()
        self._endDate=slot.getEndDate()
        self._duration=slot.getDuration()
        self._contribDuration=slot.getContribDuration()
        self._conveners=[]
        for conv in slot.getConvenerList():
            val={   "title":conv.getTitle(),
                    "first_name":conv.getFirstName(),
                    "family_name":conv.getFamilyName(),
                    "affiliation":conv.getAffiliation(),
                    "email":conv.getEmail() }
            id=len(self._conveners)
            self._conveners.append(Convener(id,**val))

    def newConvener(self):
        self._conveners.append(Convener(len(self._conveners)))

    def _resetIds(self, l):
        i = 0
        for conv in l:
            conv.setId(i)
            i += 1

    def removeConveners(self,idList):
        toRem=[]
        for conv in self._conveners:
            if str(conv.getId()) in idList:
                toRem.append(conv)
        for conv in toRem:
            self._conveners.remove(conv)
        self._resetIds(self._conveners)



