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

import fnmatch
import itertools
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
from MaKaC.rb_location import CrossLocationQueries, Location
from MaKaC.rb_reservation import RepeatabilityEnum, ReservationBase
from MaKaC.fossils.roomBooking import IReservationFossil
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails

globalExporters = ['RoomExporter', 'ReservationExporter']

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

class ReservationExporter(Exporter):
    TYPES = ('reservation', )
    RE = r'(?P<loclist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'reservations'
    MAX_RECORDS = {
        'reservations': 10000
    }

    def _getParams(self):
        super(ReservationExporter, self)._getParams()
        self._locList = self._urlParams['loclist'].split('-')

    def export_reservation(self, aw):
        expInt = ReservationExportInterface(aw, self)
        return expInt.reservation(self._locList, self._qdata)

class IRoomMetadataFossil(IFossil):

    def id(self):
        pass
    def name(self):
        pass
    def locationName(self):
        pass
    locationName.name = 'location'
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
    def needsAVCSetup(self):
        pass
    needsAVCSetup.name = 'avc'
    def getEquipment(self):
        pass
    getEquipment.convert = lambda eq: ''.join(eq) and eq or []
    def getAvailableVC(self):
        pass
    getAvailableVC.name = 'vcList'

class IMinimalRoomMetadataFossil(IFossil):
    def id(self):
        pass
    def getFullName(self):
        pass

class IRoomMetadataWithReservationsFossil(IRoomMetadataFossil):
    pass

class IReservationMetadataFossilBase(IFossil):
    def id(self):
        pass
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
    def usesAVC(self):
        pass
    def needsAVCSupport(self):
        pass
    def useVC(self):
        pass
    useVC.name = 'vcList'

class IRoomReservationMetadataFossil(IReservationMetadataFossilBase):
    pass

class IReservationMetadataFossil(IReservationMetadataFossilBase):
    def locationName(self):
        pass
    locationName.name = 'location'
    def room(self):
        pass
    room.result = IMinimalRoomMetadataFossil

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
            resvs = itertools.ifilter(self._resvFilter, resvs)
            fossil['reservations'] = fossilize(resvs, IRoomReservationMetadataFossil)
        return fossil

    def room(self, location, idlist, qdata):
        fromDT = get_query_parameter(qdata, ['f', 'from'])
        toDT = get_query_parameter(qdata, ['t', 'to'])
        self._fromDT = utc2server(ExportInterface._getDateTime('from', fromDT, self._tz)) if fromDT != None else None
        self._toDT = utc2server(ExportInterface._getDateTime('to', toDT, self._tz, aux=fromDT)) if toDT != None else None
        self._resvFilter = getResvStateFilter(qdata)

        Factory.getDALManager().connect()
        rooms = CrossLocationQueries.getRooms(location=location)

        def _iterate_rooms(objIds):
            objIds = map(int, objIds)
            return (room for room in rooms if room.id in objIds)

        for obj in self._process(_iterate_rooms(idlist)):
            yield obj
        Factory.getDALManager().disconnect()

class ReservationExportInterface(ExportInterface):
    DETAIL_INTERFACES = {
        'reservations': IReservationMetadataFossil
    }

    def reservation(self, locList, qdata):
        fromDT = get_query_parameter(qdata, ['f', 'from'])
        toDT = get_query_parameter(qdata, ['t', 'to'])
        fromDT = utc2server(ExportInterface._getDateTime('from', fromDT, self._tz)) if fromDT != None else None
        toDT = utc2server(ExportInterface._getDateTime('to', toDT, self._tz, aux=fromDT)) if toDT != None else None
        _filter = getResvStateFilter(qdata)

        Factory.getDALManager().connect()

        resvEx = ReservationBase()
        resvEx.startDT = fromDT
        resvEx.endDT = toDT

        locList = filter(lambda loc: Location.parse(loc) is not None, locList)

        for loc in sorted(locList):
            resvs = CrossLocationQueries.getReservations(location=loc, resvExample=resvEx)
            for obj in self._process(resvs, filter=_filter):
                yield obj
        Factory.getDALManager().disconnect()

def getResvStateFilter(qdata):
    cancelled = get_query_parameter(qdata, ['cxl', 'cancelled'])
    rejected = get_query_parameter(qdata, ['rej', 'rejected'])
    confirmed = get_query_parameter(qdata, ['confirmed'], -1)
    archival = get_query_parameter(qdata, ['arch', 'archival'])
    avc = get_query_parameter(qdata, ['avc'])
    avcSupport = get_query_parameter(qdata, ['avcs', 'avcsupport'])
    bookedFor = get_query_parameter(qdata, ['bf', 'bookedfor'])
    if not any((cancelled, rejected, confirmed != -1, archival, avc, avcSupport, bookedFor)):
        return None
    if cancelled is not None:
        cancelled = (cancelled == 'yes')
    if rejected is not None:
        rejected = (rejected == 'yes')
    if confirmed != -1:
        if confirmed == 'pending':
            confirmed = None
        else:
            confirmed = (confirmed == 'yes')
    if archival is not None:
        archival = (archival == 'yes')
    if avc is not None:
        avc = (avc == 'yes')
    if avcSupport is not None:
        avcSupport = (avcSupport == 'yes')
    def _filter(obj):
        if cancelled is not None and obj.isCancelled != cancelled:
            return False
        if rejected is not None and obj.isRejected != rejected:
            return False
        if confirmed != -1 and obj.isConfirmed != confirmed:
            return False
        if archival is not None and obj.isArchival != archival:
            return False
        if avc is not None and obj.usesAVC != avc:
            return False
        if avcSupport is not None and obj.needsAVCSupport != avcSupport:
            return False
        if bookedFor and not fnmatch.fnmatch(obj.bookedForName.lower(), bookedFor.lower()):
            return False
        return True
    return _filter
