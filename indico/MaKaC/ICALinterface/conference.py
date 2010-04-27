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

from xml.sax.saxutils import quoteattr, escape
from textwrap import wrap, fill
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.review as review
from MaKaC.ICALinterface.base import ICALBase
from MaKaC.common.utils import encodeUnicode
from pytz import timezone


class ProgrammeToiCal(ICALBase):

    def __init__(self, conf):
        self._conf = conf

    def getBody(self):
        return ""

class WebcastToiCal(ICALBase):

    def __init__(self, webcastManager):
        self._wm = webcastManager

    def getBody(self):
        text = self._printHeader()
        for webcast in self._wm.getWebcasts():
            if webcast.getEvent() != None:
                text += ConferenceToiCal(webcast.getEvent()).getCore()
        text += self._printFooter()
        return text

class CategoryToiCal(ICALBase):

    def __init__(self, categ):
        self._categ = categ

    def getBody(self):
        text = self._printHeader()
        for conf in self._categ.getAllConferenceList():
            text += ConferenceToiCal(conf).getCore()
        text += self._printFooter()
        return text

class ConferenceToiCal(ICALBase):

    def __init__(self, conf):
        self._conf = conf
        self._protected = conf.hasAnyProtection()

    def _lt(self, text):
        return "\\n".join(encodeUnicode(text).splitlines())

    def getCore(self):
        url = str( urlHandlers.UHConferenceDisplay.getURL( self._conf ) )
        text = self._printEventHeader(self._conf)
        text += "URL;VALUE=URI:%s\n" % url
        text += "DTSTART;TZID=%s:%s\n" % (self._conf.getTimezone(), escape(self._conf.getAdjustedStartDate().strftime("%Y%m%dT%H%M00")))
        text += "DTEND;TZID=%s:%s\n" % (self._conf.getTimezone(), escape(self._conf.getAdjustedEndDate().strftime("%Y%m%dT%H%M00")))
        desc = ""
        chair = fullchair = ""
        if len(self._conf.getChairList()) != 0:
            av = self._conf.getChairList()[0]
            chair = fullchair = av.getDirectFullName()
            if av.getAffiliation() != "":
                fullchair = "%s (%s)" % (fullchair,av.getAffiliation())
        if not self._protected:
            if self._conf.getDescription() != "":
                desc = self._lt(self._conf.getDescription())+"\\n"
            if fullchair != "":
                desc = "%s%s\\n" % (desc,self._lt(fullchair))

        text += "DESCRIPTION:%s%s\n" % (desc,url)
        room=""
        if self._conf.getRoom() is not None:
            room="%s"%self._conf.getRoom().getName()
        if self._conf.getLocation() is not None:
            if room!="":
                room=" (%s)"%room
            text += "LOCATION:%s%s\n"%(self._lt(self._conf.getLocation().getName()),self._lt(room))
        elif room!="":
            text += "LOCATION:%s\n"%(self._lt(room))
        title = self._conf.getTitle()
        if chair != "":
            title = "%s (%s)" % (title, chair)
        text += "SUMMARY:%s\n" % self._lt(title)
        text += self._printEventFooter()
        return text

    def getBody(self):
        text = self._printHeader()
        text += self.getCore()
        text += self._printFooter()
        return text

    def getDetailedBody(self):
        text = self._printHeader()
        for contrib in self._conf.getContributionList():
            text+=ContribToiCal(self._conf,contrib).getCore()
            for subcontrib in contrib.getSubContributionList():
                text+=ContribToiCal(self._conf,subcontrib).getCore()
        text  += self._printFooter()
        return text

class SessionToiCal(ICALBase):

    def __init__(self, conf, session):
        self._conf = conf
        self._session = session

    def getCore(self):

        url = quoteattr( str( urlHandlers.UHSessionDisplay.getURL( self._session ) ) )
        text = self._printEventHeader(self._session)
        text += "URL;VALUE=URI:%s\n" % url
        text += "DTSTART:%s\n" % escape(self._session.getStartDate().strftime("%Y%m%dT%H%M00Z"))
        text += "DTEND:%s\n" % escape(self._session.getEndDate().strftime("%Y%m%dT%H%M00Z"))
        text += "DESCRIPTION:[%s]\n" % url
        room=""
        if self._session.getRoom() is not None:
            room="%s"%self._session.getRoom().getName()
        if self._session.getLocation() is not None:
            if room!="":
                room=" (%s)"%room
            text += "LOCATION:%s%s\n" % (self._session.getLocation().getName(),room)
        elif room!="":
            text += "LOCATION:%s\n"%(room)
        text += "SUMMARY:%s\n" % self._session.getTitle()
        text += self._printEventFooter()
        return text

    def getBody(self):
        text = self._printHeader()
        if len(self._session.getContributionList()) > 0:
            for cont in self._session.getContributionList():
                if cont.isScheduled():
                    text += ContribToiCal(self._conf, cont).getCore()
        else:
            text += self.getCore()
        text += self._printFooter()
        return text

class ContribToiCal(ICALBase):

    def __init__(self, conf, contrib):
        self._conf = conf
        self._contrib = contrib

    def getCore(self):
        url = quoteattr( str( urlHandlers.UHContributionDisplay.getURL( self._contrib ) ) )
        text = self._printEventHeader(self._contrib)
        text += "URL;VALUE=URI:%s\n" % url
        if self._contrib.isScheduled():
            text += "DTSTART:%s\n" % escape(self._contrib.getStartDate().strftime("%Y%m%dT%H%M00Z"))
            text += "DTEND:%s\n" % escape(self._contrib.getEndDate().strftime("%Y%m%dT%H%M00Z"))
        text += "DESCRIPTION:[%s]\n" % url
        room=""
        if self._contrib.getRoom() is not None:
            room="%s"%self._contrib.getRoom().getName()
        if self._contrib.getLocation() is not None:
            if room!="":
                room=" (%s)"%room
            text += "LOCATION:%s%s\n" % (self._contrib.getLocation().getName(),room)
        elif room!="":
            text += "LOCATION:%s\n"%(room)
        text += "SUMMARY:%s\n" % self._contrib.getTitle()
        text += self._printEventFooter()
        return text

    def getBody(self):
        url = quoteattr( str( urlHandlers.UHContributionDisplay.getURL( self._contrib ) ) )
        text = self._printHeader()
        text += self.getCore()
        text += self._printFooter()
        return text


