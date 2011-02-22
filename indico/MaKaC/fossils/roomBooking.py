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

from MaKaC.common.fossilize import IFossil, Fossilizable, fossilizes
from MaKaC.common.Conversion import Conversion
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails
from MaKaC.common.TemplateExec import roomClass

class IRoomFossil(IFossil):

    def id(self):
        """ Room ID """

    def name(self):
        """ Room name """

    def locationName(self):
        """ Room location """

    def floor(self):
        """ Room floor """

    def roomNr(self):
        """ Room number """

    def building(self):
        """ Building number """

    def getBookingUrl(self):
        """ Room booking URL """

class IRoomMapFossil(IRoomFossil):


    def capacity(self):
        """ Room capacity """

    def comments(self):
        """ Room comments """

    def responsibleId(self):
        """ ID of the responsible person for the room """

    def getTipPhotoURL(self):
        """ URL of the tip photo of the room """

    def isActive(self):
        """ Is the room active? """

    def isReservable(self):
        """ Is the room public? """

    def getIsAutoConfirm(self):
        """ Has the room auto-confirmation of schedule? """

    def getDetailsUrl(self):
        """ Room details URL """

    def getMarkerDescription(self):
        """ Room description for the map marker """

    def needsAVCSetup(self):
        """ Setup for for audio and video conference """

    def getAvailableVC(self):
        """ Available equipment for audio and video conference """


class IReservationFossil(IFossil):
    """ Fossil inteface for reservation """

    def id(self):
        """ Id of the reservation """

    def bookedForName(self):
        """ Name of the reservation owner """

    def getBookingUrl(self):
        """ URL to reservation details webpage """
    getBookingUrl.produce = lambda s: str(UHRoomBookingBookingDetails.getURL( s ))

    def reason(self):
        """ Reason of the reservation """

class IBarFossil(IFossil):
    """ Fossil interafce for reservation bar """

    def startDT(self):
        """ Start date/time """
    startDT.convert = Conversion.datetime

    def endDT(self):
        """ End date/time """
    endDT.convert = Conversion.datetime

    def type(self):
        """ Type of bar (booking, pre-booking, conflict etc.) """

    def forReservation(self):
        """ Reservation out of which bar was created """
    forReservation.result = IReservationFossil

    def getCanReject(self):
        """
            Indicates if the current user can reject the reservation.
            This property is not stored in IReservationFossil because,
            in contrary to Bar objects, Reservation objects are stored
            in the database and this field has to recalculated for every
            user, so it cannot be stored there.
        """
    getCanReject.produce = lambda s: 1 if s.canReject and not s.forReservation.isCancelled and not s.forReservation.isRejected else 0

    def rejectURL(self):
        """ URL to reject reservation webpage. Stored here for simillar reasons. """

class IRoomCalendarFossil( IRoomFossil ):

    def getType(self):
        """ Room type """
    getType.produce = lambda s: roomClass(s)


class IRoomBarFossil(IFossil):
    """ Fossil interaface for RoomBar """

    def room(self):
        """ Room fossil """
    room.result = IRoomCalendarFossil

    def bars(self):
        """ List of bars (bookings) """
    bars.result = IBarFossil