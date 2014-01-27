# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.rh.xmlGateway import RHXMLHandlerBase


class RHStatsRoomBooking(RHXMLHandlerBase):

    def _createIndicator( self, XG, name, fullname, value ):
        XG.openTag("indicator")
        XG.writeTag("name", name)
        XG.writeTag("fullname", fullname)
        XG.writeTag("value", value)
        XG.closeTag("indicator")

    def _process( self ):
        from MaKaC.rb_room import RoomBase
        from datetime import datetime,timedelta
        from MaKaC.rb_reservation import ReservationBase

        startdt = enddt = datetime.now()
        today = startdt.date()
        startdt.replace( hour = 0, minute = 0)
        enddt.replace( hour = 23, minute = 59)

        self._responseUtil.content_type = 'text/xml'
        XG = xmlGen.XMLGen()
        XG.openTag("response")

        rooms = RoomBase.getRooms()
        nbRooms = len(rooms)
        nbPublicRooms = nbPrivateRooms = nbSemiPrivateRooms = 0
        for r in rooms:
            if not r.isReservable:
                nbPrivateRooms += 1
            elif not r.resvsNeedConfirmation:
                nbPublicRooms += 1
            else:
                nbSemiPrivateRooms += 1

        self._createIndicator(XG, "total", "total number of managed rooms", nbRooms)
        self._createIndicator(XG, "public", "number of public rooms", nbPublicRooms)
        self._createIndicator(XG, "semiprivate", "number of semi-private rooms", nbSemiPrivateRooms)
        self._createIndicator(XG, "private", "number of private rooms", nbPrivateRooms)

        resvex = ReservationBase()
        resvex.isConfirmed = True
        resvex.isCancelled = False
        nbResvs = len(ReservationBase.getReservations( resvExample = resvex, days = [ startdt.date() ] ))
        resvex.usesAVC = True
        nbAVResvs = len(ReservationBase.getReservations( resvExample = resvex, days = [ startdt.date() ] ))
        resvex.needsAVCSupport = True
        resvex.needsAssistance = False
        nbAVResvsWithSupport = len(ReservationBase.getReservations( resvExample = resvex, days = [ startdt.date() ] ))

        self._createIndicator(XG, "nbbookings", "total number of bookings for today", nbResvs)
        self._createIndicator(XG, "nbvc", "number of remote collaboration bookings (video or phone conference)", nbAVResvs)
        self._createIndicator(XG, "nbvcsupport", "number of remote collaboration bookings with planned IT support", nbAVResvsWithSupport)

        XG.closeTag("response")
        return XG.getXml()
