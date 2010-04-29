# -*- coding: utf-8 -*-
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

from MaKaC.common.timezoneUtils import getAdjustedDate, nowutc
from datetime import timedelta
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

class OutputGenerator(object):

    @classmethod
    def collaborationToXML(cls, out, conf, tz):
        """ Generates the xml corresponding to the collaboration plugin system
            for an event.
        """

        #collaboration XML
        out.openTag("collaboration")
        csbm = conf.getCSBookingManager()

        out.writeComment("Needed for timezone awareness")
        out.writeTag("todayReference", getAdjustedDate(nowutc(), None, tz).strftime("%Y-%m-%d"))
        out.writeTag("tomorrowReference", getAdjustedDate(nowutc() + timedelta(days = 1), None, tz).strftime("%Y-%m-%d"))

        pluginNames = csbm.getEventDisplayPlugins()

        bookingXmlGenerators = {}

        for pluginName in pluginNames:
            xmlGenerator = CollaborationTools.getXMLGenerator(pluginName)
            bookingXmlGenerators[pluginName] = xmlGenerator

        bookings = csbm.getBookingList(filterByType = pluginNames, notify = True, onlyPublic = True)
        bookings.sort(key = lambda b: b.getStartDate())

        ongoingBookings = []
        scheduledBookings = []

        for b in bookings:
            if b.canBeStarted():
                ongoingBookings.append(b)
            if b.hasStartDate() and b.getAdjustedStartDate('UTC') > nowutc():
                scheduledBookings.append(b)

        for b in ongoingBookings :
            bookingType = b.getType()
            out.openTag("booking")
            out.writeTag("id", b.getId())
            out.writeTag("kind", "ongoing")
            out.writeTag("type", bookingType)
            out.writeTag("typeDisplayName", bookingXmlGenerators[bookingType].getDisplayName())
            out.writeTag("startDate", b.getAdjustedStartDate(tz).strftime("%Y-%m-%dT%H:%M:%S"))
            out.writeTag("endDate",b.getAdjustedEndDate(tz).strftime("%Y-%m-%dT%H:%M:%S"))
            bookingXmlGenerators[bookingType].getCustomBookingXML(b, tz, out)
            out.closeTag("booking")

        for b in scheduledBookings :
            bookingType = b.getType()
            out.openTag("booking")
            out.writeTag("id", b.getId())
            out.writeTag("title", b._getTitle())
            out.writeTag("kind", "scheduled")
            out.writeTag("type", bookingType)
            out.writeTag("typeDisplayName", bookingXmlGenerators[bookingType].getDisplayName())
            out.writeTag("startDate", b.getAdjustedStartDate(tz).strftime("%Y-%m-%dT%H:%M:%S"))
            out.writeTag("endDate",b.getAdjustedEndDate(tz).strftime("%Y-%m-%dT%H:%M:%S"))
            bookingXmlGenerators[bookingType].getCustomBookingXML(b, tz, out)
            out.closeTag("booking")

        out.closeTag("collaboration")
