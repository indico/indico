# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from MaKaC.common.fossilize import IFossil
from MaKaC.common.Conversion import Conversion

from indico.core.fossils.event import ISupportInfoFossil


class ICategoryFossil(IFossil):

    def getId(self):
        """ Category Id """

    def getName(self):
        """ Category Name """


class IConferenceMinimalFossil(IFossil):

    def getId(self):
        """Conference id"""

    def getTitle(self):
        """Conference title"""


class IConferenceFossil(IConferenceMinimalFossil):

    def getType(self):
        """ Event type: 'conference', 'meeting', 'simple_event' """

    def getDescription(self):
        """Conference description"""

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = lambda l: l and l.getName()

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = lambda r: r and r.getName()

    def getAddress(self):
        """ Address of the event """
    getAddress.produce = lambda s: s.getLocation().getAddress() if s.getLocation() is not None else None

    def getRoomBookingList(self):
        """ Reservations """
    getRoomBookingList.convert = Conversion.reservationsList
    getRoomBookingList.name = "bookedRooms"

    def getStartDate(self):
        """ Start Date """
    getStartDate.convert = Conversion.datetime

    def getEndDate(self):
        """ End Date """
    getEndDate.convert = Conversion.datetime

    def getAdjustedStartDate(self):
        """ Adjusted Start Date """
    getAdjustedStartDate.convert = Conversion.datetime

    def getAdjustedEndDate(self):
        """ Adjusted End Date """
    getAdjustedEndDate.convert = Conversion.datetime

    def getTimezone(self):
        """ Time zone """

    def getSupportInfo(self):
        """ Support Info"""
    getSupportInfo.result = ISupportInfoFossil


class IConferenceEventInfoFossil(IConferenceMinimalFossil):
    """
    Fossil used to format the 'eventInfo' javascript object used
    in the timetable operations
    """

    def getAddress(self):
        """ Address """
    getAddress.produce = lambda s: s.getLocation()
    getAddress.convert = Conversion.locationAddress

    def getLocation(self):
        """ Location (CERN/...) """
    getLocation.convert = Conversion.locationName

    def getRoom(self):
        """ Room (inside location) """
    getRoom.convert = Conversion.roomName

    def getAdjustedStartDate(self):
        """ Start Date """
    getAdjustedStartDate.convert = Conversion.datetime
    getAdjustedStartDate.name = "startDate"

    def getAdjustedEndDate(self):
        """ End Date """
    getAdjustedEndDate.convert = Conversion.datetime
    getAdjustedEndDate.name = "endDate"

    def isConference(self):
        """ Is this event a conference ? """
    isConference.produce = lambda s: s.getType() == 'conference'

    def getFavoriteRooms(self):
        """ Favorite Rooms """

    def getRoomBookingList(self):
        """ Reservations """
    getRoomBookingList.convert = Conversion.reservationsList
    getRoomBookingList.name = "bookedRooms"
