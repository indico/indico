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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase, WCSCSSBase
from MaKaC.webinterface.common.tools import strip_ml_tags, unescape_html
from MaKaC.i18n import _
from MaKaC.fossils.user import IAvatarFossil
from MaKaC.plugins.Collaboration.pages import WAdvancedTabBase
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools,  getVidyoOptionValue
from datetime import timedelta
from MaKaC.common import info
from MaKaC.plugins.Collaboration.Vidyo.indexes import EventEndDateIndex


class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        variables = WCSPageTemplateBase.getVars(self)

        variables["EventTitle"] = VidyoTools.defaultRoomName(self._conf)
        variables["EventDescription"] = unescape_html(strip_ml_tags(self._conf.getDescription())).strip()

        return variables


class WAdvancedTab(WAdvancedTabBase):

    def getVars(self):
        variables = WAdvancedTabBase.getVars(self)
        return variables


class WMain (WJSBase):

    def getVars(self):
        variables = WJSBase.getVars(self)

        variables["LoggedInUser"] = self._user.fossilize(IAvatarFossil)
        variables["MaxNameLength"] = VidyoTools.maxRoomNameLength()

        return variables


class WExtra (WJSBase):

    def getVars(self):
        variables = WJSBase.getVars(self)
        return variables


class WIndexing(WJSBase):
    pass


class WStyle (WCSCSSBase):
    pass


class WInformationDisplay(WCSPageTemplateBase):

    def __init__(self, booking, displayTz):
        WCSPageTemplateBase.__init__(self, booking.getConference(), 'Vidyo', None)
        self._booking = booking
        self._displayTz = displayTz

    def getVars(self):
        variables = WCSPageTemplateBase.getVars(self)
        variables["Booking"] = self._booking
        variables["PhoneNumbers"] = getVidyoOptionValue("phoneNumbers")

        return variables


class XMLGenerator(object):

    @classmethod
    def getDisplayName(cls):
        return _("Vidyo public room")

    @classmethod
    def getFirstLineInfo(cls, booking, displayTz):
        return booking.getBookingParamByName('roomName')

    @classmethod
    def getCustomBookingXML(cls, booking, displayTz, out):
        if (booking.canBeStarted()):
            out.openTag("launchInfo")
            out.writeTag("launchText", _("Join Now!"))
            out.writeTag("launchLink", booking.getURL())
            out.writeTag("launchTooltip", _('Click here to join the Vidyo room!'))
            out.closeTag("launchInfo")

        out.writeTag("firstLineInfo", booking.getBookingParamByName("roomName"))

        out.openTag("information")

        out.openTag("section")
        out.writeTag("title", _('Room name:'))
        out.writeTag("line", booking.getBookingParamByName("roomName"))
        out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Extension:'))
        out.writeTag("line", booking.getExtension())
        out.closeTag("section")

        if booking.getHasPin():
            out.openTag("section")
            out.writeTag("title", _('Meeting PIN:'))
            if booking.getBookingParamByName("displayPin"):
                out.writeTag("line", booking.getPin())
            else:
                out.writeTag("line", _('This Vidyo room is protected by a PIN'))
            out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Owner:'))
        out.writeTag("line", booking.getOwnerObject().getFullName())
        out.closeTag("section")

        if booking.getBookingParamByName("displayURL"):
            out.openTag("section")
            out.writeTag("title", _('Auto-join URL:'))
            out.openTag("linkLine")
            out.writeTag("href", booking.getURL())
            out.writeTag("caption", booking.getURL())
            out.closeTag("linkLine")
            out.closeTag("section")

        if booking.getBookingParamByName("displayPhoneNumbers") and getVidyoOptionValue("phoneNumbers"):
            out.openTag("section")
            out.writeTag("title", _('Phone access:'))
            out.writeTag("line", ', '.join(getVidyoOptionValue("phoneNumbers")))
            out.closeTag("section")

        out.openTag("section")
        out.writeTag("title", _('Description:'))
        out.writeTag("line", booking.getBookingParamByName("roomDescription"))
        out.closeTag("section")
        out.closeTag("information")


class ServiceInformation(object):

    @classmethod
    def getDisplayName(cls):
        return _("Vidyo public room")

    @classmethod
    def getFirstLineInfo(cls, booking, displayTz=None):
        return booking.getBookingParamByName('roomName')

    @classmethod
    def getLaunchInfo(cls, booking, displayTz=None):
        launchInfo = {
            "launchText":  _("Join Now!"),
            "launchLink": ""
        }
        if (booking.canBeStarted()):
                launchInfo["launchLink"] = booking.getURL()
                launchInfo["launchTooltip"] = _('Click here to join the Vidyo room!')
        else:
            launchInfo["launchTooltip"] = _('You cannot join to the Vidyo room because the room does not exist')
        return launchInfo

    @classmethod
    def getInformation(cls, booking, displayTz=None):
        sections = []
        sections.append({
            "title": _('Room name'),
            'lines': [booking.getBookingParamByName("roomName")],
        })
        sections.append({
            "title": _('Extension'),
            'lines': [booking.getExtension()],
        })
        if booking.getHasPin():
            pinSection = {}
            pinSection['title'] = _('Meeting PIN')
            if booking.getBookingParamByName("displayPin"):
                pinSection['lines'] = [booking.getPin()]
            else:
                pinSection['lines'] = [_('This Vidyo room is protected by a PIN')]
            sections.append(pinSection)

        sections.append({
            "title": _('Moderator'),
            'lines': [booking.getOwnerObject().getStraightFullName()],
        })

        if booking.getBookingParamByName("displayPhoneNumbers") and getVidyoOptionValue("phoneNumbers"):
            sections.append({
                "title": _('Phone access numbers'),
                'lines': [', '.join(getVidyoOptionValue("phoneNumbers"))],
            })
        sections.append({
            "title": _('Description'),
            'lines': [booking.getBookingParamByName("roomDescription")],
        })
        if booking.getBookingParamByName("displayURL"):
            autojoinSection = {}
            autojoinSection['title'] = _('Auto-join URL')
            autojoinSection['linkLines'] = [(booking.getURL(), booking.getURL())]
            sections.append(autojoinSection)
        return sections


## Vidyo custom classes for action results

class WShowOldRoomIndexActionResult(WCSPageTemplateBase):

    def __init__(self, maxDate):
        WCSPageTemplateBase.__init__(self, None, "Vidyo", None)
        self._maxDate = maxDate

    def _postProcessingClones(self, oldBookingsPerConfIterator, newBookingsPerConfIterator):
        oldBookingsPerConf = {}
        newBookingsPerConf = {}

        for booking in newBookingsPerConfIterator:
            key = EventEndDateIndex._bookingToKey(booking)
            newBookingsPerConf[key][booking.getConference()] = newBookingsPerConf.setdefault(key, {}).setdefault(booking.getConference(), 0) + 1

        for booking in oldBookingsPerConfIterator:
            key = EventEndDateIndex._bookingToKey(booking)
            if booking.hasToBeDeleted(True, self._maxDate):
                oldBookingsPerConf[key][booking.getConference()] = oldBookingsPerConf.setdefault(key, {}).setdefault(booking.getConference(), 0) + 1
            else:
                newBookingsPerConf[key][booking.getConference()] = newBookingsPerConf.setdefault(key, {}).setdefault(booking.getConference(), 0) + 1

        return oldBookingsPerConf, newBookingsPerConf

    def getVars(self):
        variables = WCSPageTemplateBase.getVars(self)

        variables["MaxDate"] = self._maxDate
        variables["TotalRoomCount"] = VidyoTools.getEventEndDateIndex().getCount()
        oldBookingsPerConfIterator = VidyoTools.getEventEndDateIndex().iterbookings(maxDate=self._maxDate)
        newBookingsPerConfIterator = VidyoTools.getEventEndDateIndex().iterbookings(minDate=self._maxDate + timedelta(seconds=1))
        oldBookingsPerConf, newBookingsPerConf = self._postProcessingClones(oldBookingsPerConfIterator, newBookingsPerConfIterator)

        variables["OldBookings"] = WBookingsList(oldBookingsPerConf).getHTML()
        variables["NewBookings"] = WBookingsList(newBookingsPerConf).getHTML()
        variables["ServerTZ"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()

        return variables


class WBookingsList(WCSPageTemplateBase):

    def __init__(self, bookingsPerConfIterator):
        WCSPageTemplateBase.__init__(self, None, "Vidyo", None)
        self._bookingsPerConfIterator = bookingsPerConfIterator

    def getVars(self):
        variables = WCSPageTemplateBase.getVars(self)

        variables["BookingsPerConfIterator"] = self._bookingsPerConfIterator
        variables["ServerTZ"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        variables["PairSorter"] = lambda pair: pair[0].getTitle()  # we cannot have ":" in the template

        return variables


class WDeleteOldRoomsActionResult(WCSPageTemplateBase):

    def __init__(self, maxDate, previousTotal, newTotal, error=False, attainedDate=None):
        WCSPageTemplateBase.__init__(self, None, "Vidyo", None)
        self._maxDate = maxDate
        self._previousTotal = previousTotal
        self._newTotal = newTotal
        self._error = error
        self._attainedDate = attainedDate

    def getVars(self):
        variables = WCSPageTemplateBase.getVars(self)

        variables["MaxDate"] = self._maxDate
        variables["ServerTZ"] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        variables["PreviousTotal"] = self._previousTotal
        variables["NewTotal"] = self._newTotal
        variables["Error"] = self._error
        variables["AttainedDate"] = self._attainedDate

        return variables
