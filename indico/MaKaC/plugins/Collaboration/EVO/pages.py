# -*- coding: utf-8 -*-
##
## $Id: pages.py,v 1.9 2009/04/25 13:56:04 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase
from MaKaC.common.utils import formatDateTime
from datetime import timedelta
from MaKaC.webinterface.common.tools import strip_ml_tags, unescape_html
from MaKaC.plugins.Collaboration.EVO.common import getMinStartDate,\
    getMaxEndDate
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

class WNewBookingForm(WCSPageTemplateBase):
        
    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        
        vars["EventTitle"] = self._conf.getTitle()
        vars["EventDescription"] = unescape_html(strip_ml_tags( self._conf.getDescription())).strip()
        vars["DefaultStartDate"] = formatDateTime(self._conf.getAdjustedStartDate() - timedelta(0,0,0,0,CollaborationTools.getCollaborationPluginType().getOption("startMinutes").getValue()))
        vars["DefaultEndDate"] = formatDateTime(self._conf.getAdjustedEndDate())
        vars["MinStartDate"] = formatDateTime(getMinStartDate(self._conf))
        vars["MaxEndDate"] = formatDateTime(getMaxEndDate(self._conf))
        vars["Communities"] = self._EVOOptions["communityList"].getValue()
        
        return vars

class WMain (WJSBase):
    
    def getVars(self):
        vars = WJSBase.getVars( self )
        
        vars["AllowedStartMinutes"] = self._EVOOptions["allowedPastMinutes"].getValue()
        vars["MinStartDate"] = formatDateTime(getMinStartDate(self._conf))
        vars["MaxEndDate"] = formatDateTime(getMaxEndDate(self._conf))
        vars["AllowedMarginMinutes"] = self._EVOOptions["allowedMinutes"].getValue()
        
        return vars
    
class WIndexing(WJSBase):
    pass
    
class WDisplay(WCSPageTemplateBase):
    
    def __init__(self, conf, displayTz):
        WCSPageTemplateBase.__init__(self, conf, 'EVO', None)
        self._displayTz = displayTz
    
    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        
        evoBookings = self._conf.getCSBookingManager().getBookingList(filterByType="EVO", notify = True)
        currentBookings = []
        futureBookings = []
        
        for b in evoBookings:
            if b.canBeStarted():
                currentBookings.append(b)
            if b.getAdjustedStartDate('UTC') > nowutc():
                futureBookings.append(b)
        
        vars["CurrentBookings"] = currentBookings
        vars["FutureBookings"] = futureBookings
        vars["Today"] = getAdjustedDate(nowutc(), tz = self._displayTz).date()
        vars["DisplayTz"] = self._displayTz
        
        return vars
    
    def shouldShow(self):
        return self._currentBooking or len(self._futureBookings) > 0
    
class XMLGenerator(object):
    
    @classmethod
    def getXML(cls, csbm, displayTz, out):
        """ csbm: a CSBookingManager object
            out: an XML outpout stream
        """
        evoBookings = csbm.getBookingList(filterByType="EVO", notify = True)
        currentBookings = []
        futureBookings = []
        
        for b in evoBookings:
            if b.canBeStarted():
                currentBookings.append(b)
            if b.getAdjustedStartDate('UTC') > nowutc():
                futureBookings.append(b)
        
        if currentBookings:
            out.openTag("ongoing")
            for booking in currentBookings:
                cls.getBookingXML(booking, displayTz, out)
            out.closeTag("ongoing")
        
        if futureBookings:
            out.openTag("scheduled")
            for booking in futureBookings:
                cls.getBookingXML(booking, displayTz, out)
            out.closeTag("scheduled")
            
    @classmethod
    def getBookingXML(cls, booking, displayTz, out):
        out.openTag("booking")
        out.writeTag("title", booking._bookingParams["meetingTitle"])
        out.writeTag("startDate", booking.getAdjustedStartDate(displayTz).strftime("%Y-%m-%dT%H:%M:%S"))
        out.writeTag("endDate",booking.getAdjustedEndDate(displayTz).strftime("%Y-%m-%dT%H:%M:%S"))
        out.writeTag("url", booking.getURL())
        if booking.getHasAccessPassword():
            out.writeTag("hasPassword", "yes")
        else:
            out.writeTag("hasPassword", "no")
        out.closeTag("booking")
        
            