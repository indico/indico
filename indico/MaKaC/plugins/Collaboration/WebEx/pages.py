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
from MaKaC.plugins.Collaboration.WebEx.common import getMinStartDate,\
    getMaxEndDate
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate
import re

from MaKaC.common.logger import Logger

class WNewBookingForm(WCSPageTemplateBase):
        
    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        
        vars["EventTitle"] = self._conf.getTitle()
        vars["EventDescription"] = unescape_html(strip_ml_tags( self._conf.getDescription())).strip()
        
        vars["DefaultStartDate"] = formatDateTime(self._conf.getAdjustedStartDate())
        vars["DefaultEndDate"] = formatDateTime(self._conf.getAdjustedEndDate())

        vars["DefaultWebExUser"] = ""
        vars["DefaultWebExPass"] = ""
        vars["TimeZone"] = self._conf.getTimezone()
        sessions = "<select name='session' id='session' onchange='updateSessionTimes()'><option value=''>None</option>"
        count = 0
        sessionList = self._conf.getSessionList()
        for session  in sessionList: 
            count = count + 1
            sessions = sessions + "<option value='%s'>%s</option>" % (str(session.getId()), session.getTitle() )
        sessions += "</select>"
        vars["SessionList"] = sessions

        return vars

class WMain (WJSBase):
    
    def getVars(self):
        vars = WJSBase.getVars( self )
        
        vars["AllowedStartMinutes"] = self._WebExOptions["allowedPastMinutes"].getValue()
        vars["MinStartDate"] = formatDateTime(getMinStartDate(self._conf))
        vars["MaxEndDate"] = formatDateTime(getMaxEndDate(self._conf))
        vars["AllowedMarginMinutes"] = self._WebExOptions["allowedMinutes"].getValue()
        
        return vars
    
class WExtra (WJSBase):
    
    def getVars(self):
        vars = WJSBase.getVars( self )
        sessionTimes = ""
        sessionList = self._conf.getSessionList()
        for session  in sessionList: 
            sessionTimes = sessionTimes + """{"id":"%s", "start":"%s", "end":"%s" },""" % (str(session.getId()), formatDateTime(session.getAdjustedStartDate()), formatDateTime(session.getAdjustedEndDate()) )
        vars["SessionTimes"] = '{ "sessions": [' + sessionTimes[:-1] + ']}'
        vars["AllowedStartMinutes"] = self._WebExOptions["allowedPastMinutes"].getValue()
        if self._conf:
            vars["MinStartDate"] = formatDateTime(getMinStartDate(self._conf), format = "%a %d/%m %H:%M")
            vars["MaxEndDate"] = formatDateTime(getMaxEndDate(self._conf), format = "%a %d/%m %H:%M")
        else:
            vars["MinStartDate"] = ''
            vars["MaxEndDate"] = ''
        
        return vars
    
class WIndexing(WJSBase):
    pass
    
class WInformationDisplay(WCSPageTemplateBase):
    
    def __init__(self, booking, displayTz):
        WCSPageTemplateBase.__init__(self, booking.getConference(), 'WebEx', None)
        self._booking = booking
        self._displayTz = displayTz
    
    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        vars["Booking"] = self._booking
        return vars
    
class XMLGenerator(object):
    @classmethod
    def getFirstLineInfo(cls, booking, displayTz):
         return booking._bookingParams["meetingTitle"]
    @classmethod
    def getDisplayName(cls):
        return "WebEx"
            
    @classmethod
    def getCustomBookingXML(cls, booking, displayTz, out):
        booking.checkCanStart()
        if (booking.canBeStarted()):
            out.openTag("launchInfo")
            out.writeTag("launchText", _("Join Now!"))
            out.writeTag("launchLink", booking.getUrl())
            out.writeTag("launchTooltip", _('Click here to join the WebEx meeting!'))
            out.closeTag("launchInfo")
        out.openTag("information")
        
        if booking.getHasAccessPassword():
            out.openTag("section")
            out.writeTag("title", _('Protection:'))
            out.writeTag("line", _('This WebEx meeting is protected by a password'))
            out.closeTag("section")
        out.openTag("section")
        out.writeTag("title", _('Title:'))
        out.writeTag("line", booking._bookingParams["meetingTitle"])
        out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Agenda:'))
        out.writeTag("line", booking._bookingParams["meetingDescription"])
        out.closeTag("section")
        out.openTag("section")
        out.writeTag("title", _('Join URL:'))
        out.openTag("linkLineNewWindow")
        out.writeTag("href", booking.getUrl())
        out.writeTag("caption", "Click here to go to the WebEx meeting page")
        out.closeTag("linkLineNewWindow")
        out.closeTag("section")
        out.openTag("section")
        out.writeTag("title", _('Toll free call-in number (US/Canada):'))
        out.writeTag("line", booking._phoneNum)
        out.closeTag("section")
        out.openTag("section")
        out.writeTag("title", _('Toll call-in number: (US/Canada)'))
        out.writeTag("line", booking._phoneNumToll)
        out.closeTag("section")
        out.openTag("section")
        out.writeTag("title", _('Call-in access code:'))
        out.writeTag("line", re.sub(r'(\d{3})(?=\d)',r'\1 ', str(booking._webExKey)[::-1])[::-1])
        out.closeTag("section")
        out.closeTag("information")

