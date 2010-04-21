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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase, WCSCSSBase
from MaKaC.common.utils import formatDateTime
from datetime import timedelta
from MaKaC.webinterface.common.tools import strip_ml_tags, unescape_html
from MaKaC.plugins.Collaboration.EVO.common import getMinStartDate, getMaxEndDate,\
    getEVOOptionValueByName
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.plugins.Collaboration.EVO.common import getMinStartDate, getMaxEndDate
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.collaboration import WAdvancedTabBase

class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        vars["EventTitle"] = self._conf.getTitle()
        vars["EventDescription"] = unescape_html(strip_ml_tags( self._conf.getDescription())).strip()

        defaultStartDate = self._conf.getAdjustedStartDate() - timedelta(0, 0, 0, 0, self._EVOOptions["defaultMinutesBefore"].getValue())
        nowStartDate = getAdjustedDate(nowutc() - timedelta(0, 0, 0, 0, self._EVOOptions["allowedPastMinutes"].getValue() / 2), self._conf)
        vars["DefaultStartDate"] = formatDateTime(max(defaultStartDate, nowStartDate))

        defaultEndDate = self._conf.getAdjustedEndDate() + timedelta(0, 0, 0, 0, self._EVOOptions["defaultMinutesAfter"].getValue())
        nowEndDate = nowStartDate + timedelta(0, 0, 0, 0, self._EVOOptions["extraMinutesAfter"].getValue())
        vars["DefaultEndDate"] = formatDateTime(max(defaultEndDate, nowEndDate))

        communities = self._EVOOptions["communityList"].getValue() #a dict communityId : communityName
        communityItems = communities.items() # a list of tuples (communityId, communityName)
        communityItems.sort(key = lambda t: t[1]) # we sort by the second member of the tuple (the name)
        vars["Communities"] = communityItems

        return vars

class WAdvancedTab(WAdvancedTabBase):

    def getVars(self):
        variables = WAdvancedTabBase.getVars(self)

        variables["PhoneBridgeListLink"] = getEVOOptionValueByName("phoneBridgeNumberList")

        return variables

class WMain (WJSBase):

    def getVars(self):
        vars = WJSBase.getVars( self )

        vars["AllowedStartMinutes"] = self._EVOOptions["allowedPastMinutes"].getValue()
        vars["MinStartDate"] = formatDateTime(getMinStartDate(self._conf))
        vars["MaxEndDate"] = formatDateTime(getMaxEndDate(self._conf))
        vars["ExtraMinutesBefore"] = self._EVOOptions["extraMinutesBefore"].getValue()
        vars["ExtraMinutesAfter"] = self._EVOOptions["extraMinutesAfter"].getValue()
        vars["PossibleToCreateOrModify"] = getAdjustedDate(nowutc(), self._conf) < getMaxEndDate(self._conf)
        vars["GeneralSettingsURL"] = urlHandlers.UHConferenceModification.getURL(self._conf)

        return vars

class WExtra (WJSBase):

    def getVars(self):
        vars = WJSBase.getVars( self )

        vars["AllowedStartMinutes"] = self._EVOOptions["allowedPastMinutes"].getValue()
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
        WCSPageTemplateBase.__init__(self, booking.getConference(), 'EVO', None)
        self._booking = booking
        self._displayTz = displayTz

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        vars["Booking"] = self._booking
        vars["ListOfPhoneBridgeNumbersURL"] = getEVOOptionValueByName("phoneBridgeNumberList")

        return vars

class WStyle(WCSCSSBase):
    pass

class XMLGenerator(object):

    @classmethod
    def getDisplayName(cls):
        return "EVO Meeting"

    @classmethod
    def getFirstLineInfo(cls, booking, displayTz):
        return _('Phone Bridge ID:') + booking.getPhoneBridgeId()+ '.'

    @classmethod
    def getCustomBookingXML(cls, booking, displayTz, out):
        booking.checkCanStart()
        if (booking.canBeStarted()):
            out.openTag("launchInfo")
            out.writeTag("launchText", _("Join Now!"))
            out.writeTag("launchLink", booking.getUrl())
            out.writeTag("launchTooltip", _('Click here to join the EVO meeting!'))
            out.closeTag("launchInfo")

        if booking.getBookingParamByName("displayPhoneBridgeId"):
            out.writeTag("firstLineInfo", XMLGenerator.getFirstLineInfo(booking, displayTz))

        out.openTag("information")

        out.openTag("section")
        out.writeTag("title", _('Title:'))
        out.writeTag("line", booking._bookingParams["meetingTitle"])
        out.closeTag("section")

        if booking.getHasAccessPassword():
            if not booking.getBookingParamByName("displayPassword") and not booking.getBookingParamByName("displayPhonePassword"):
                out.openTag("section")
                out.writeTag("title", _('Password:'))
                out.writeTag("line", _('This EVO meeting is protected by a private password.'))
                out.closeTag("section")
            else:
                if booking.getBookingParamByName("displayPassword"):
                    out.openTag("section")
                    out.writeTag("title", _('Password:'))
                    out.writeTag("line", booking.getAccessPassword())
                    out.closeTag("section")
                if booking.getBookingParamByName("displayPhonePassword"):
                    out.openTag("section")
                    out.writeTag("title", _('Phone Bridge Password:'))
                    out.writeTag("line", booking.getPhoneBridgePassword())
                    out.closeTag("section")

        if booking.getBookingParamByName("displayPhoneBridgeNumbers"):
            out.openTag("section")
            out.writeTag("title", _('Phone bridge numbers:'))
            out.openTag("linkLine")
            out.writeTag("href", getEVOOptionValueByName("phoneBridgeNumberList"))
            out.writeTag("caption", _("List of phone bridge numbers"))
            out.closeTag("linkLine")
            out.closeTag("section")

        if booking.getBookingParamByName("displayURL"):
            out.openTag("section")
            out.writeTag("title", _('Auto-join URL:'))
            out.writeTag("line", booking.getUrl())
            out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Description:'))
        out.writeTag("line", booking._bookingParams["meetingDescription"])
        out.closeTag("section")

        out.closeTag("information")
