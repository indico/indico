# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2011 CERN.
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

import pytz
from indico.web.http_api import ExportInterface, LimitExceededException, Exporter
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError
from indico.web.wsgi import webinterface_handler_config as apache
from indico.util.fossilize import fossilize, IFossil
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.timezoneUtils import utc2server
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_room import RoomBase
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.rb_reservation import RepeatabilityEnum, ReservationBase
from MaKaC.fossils.roomBooking import IReservationFossil
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails

globalExporters = ['RoomExporter']

class RoomExporter(Exporter):
    TYPES = ('room', )
    RE = r'(?P<location>\w+)/(?P<idlist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 1000,
        'reservations': 10
    }

    def _getParams(self):
        super(RoomExporter, self)._getParams()
        self._location = self._urlParams['location']
        self._idList = self._urlParams['idlist'].split('-')

    def export_room(self, aw):
        expInt = RoomExportInterface(aw, self)
        return expInt.room(self._location, self._idList, self._qdata)

class IRoomMetadataFossil(IFossil):

    def id(self):
        pass
    def name(self):
        pass
    def locationName(self):
        pass
    def floor(self):
        pass
    def roomNr(self):
        pass
    def building(self):
        pass
    def getBookingUrl(self):
        pass
    def getFullName(self):
        pass

class IRoomMetadataWithReservationsFossil(IRoomMetadataFossil):
    pass

class IReservationMetadataFossil(IFossil):
    def startDT(self):
        pass
    def endDT(self):
        pass
    def repeatability(self):
        pass # None or a nice short name
    repeatability.convert = lambda r: RepeatabilityEnum.rep2shortname[r] if r is not None else None
    def bookedForName(self):
        pass
    def getBookingUrl(self):
        pass
    getBookingUrl.produce = lambda s: str(UHRoomBookingBookingDetails.getURL(s))
    def reason(self):
        pass
    def isCancelled(self):
        pass
    isCancelled.name = 'cancelled'
    def isRejected(self):
        pass
    isRejected.name = 'rejected'

class RoomExportInterface(ExportInterface):
    DETAIL_INTERFACES = {
        'rooms': IRoomMetadataFossil,
        'reservations': IRoomMetadataWithReservationsFossil
    }

    def _postprocess(self, obj, fossil, iface):
        if iface is IRoomMetadataWithReservationsFossil:
            if self._fromDT or self._toDT:
                resvEx = ReservationBase()
                resvEx.startDT = self._fromDT
                resvEx.endDT = self._toDT
                resvEx.room = obj
                if self._fromDT.date() != self._toDT.date():
                    resvEx.repeatability = RepeatabilityEnum.daily
                resvs = list(set(c.withReservation for c in resvEx.getCollisions()))
            else:
                resvs = obj.getReservations()
            fossil['reservations'] = fossilize(resvs, IReservationMetadataFossil)
        return fossil

    def room(self, location, idlist, qdata):
        fromDT = get_query_parameter(qdata, ['f', 'from'])
        toDT = get_query_parameter(qdata, ['t', 'to'])
        self._fromDT = utc2server(ExportInterface._getDateTime('from', fromDT, self._tz)) if fromDT != None else None
        self._toDT = utc2server(ExportInterface._getDateTime('to', toDT, self._tz, aux=fromDT)) if toDT != None else None

        Factory.getDALManager().connect()
        rooms = CrossLocationQueries.getRooms(location)

        def _iterate_rooms(objIds):
            objIds = map(int, objIds)
            return (room for room in rooms if room.id in objIds)

        for obj in self._process(_iterate_rooms(idlist)):
            yield obj
        Factory.getDALManager().disconnect()