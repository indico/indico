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

from pytz import timezone
import fnmatch
import itertools
from dateutil import rrule
from datetime import datetime, timedelta
from indico.web.http_api import ExportInterface, Exporter
from indico.web.http_api.util import get_query_parameter
from indico.util.fossilize import fossilize, IFossil
from indico.util.fossilize.conversion import Conversion
from MaKaC.common.timezoneUtils import utc2server
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.rb_location import CrossLocationQueries, Location
from MaKaC.rb_tools import Period
from MaKaC.rb_reservation import RepeatabilityEnum, ReservationBase
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails


globalExporters = ['RoomExporter', 'ReservationExporter']
MAX_DATETIME = datetime(2099, 12, 31, 23, 59, 00)
MIN_DATETIME = datetime(2000, 1, 1, 00, 00, 00)


def utcdate(datet):
    d = datet.astimezone(timezone('UTC'))
    return utc2server(d)


class RoomExporter(Exporter):
    """
    Example: /room/CERN/23.xml
    """
    TYPES = ('room', )
    RE = r'(?P<location>\w+)/(?P<idlist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 1000,
        'reservations': 10
    }
    SERIALIZER_TYPE_MAP = {
        'RoomCERN': 'Room',
        'ReservationCERN': 'Reservation'
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml')

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
    SERIALIZER_TYPE_MAP = {
        'RoomCERN': 'Room',
        'ReservationCERN': 'Reservation'
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml', 'ics')

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
    startDT.convert = Conversion.naive

    def endDT(self):
        pass
    endDT.convert = Conversion.naive

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

    def usesAVC(self):
        pass

    def needsAVCSupport(self):
        pass

    def useVC(self):
        pass

    def isConfirmed(self):
        pass

    def isValid(self):
        pass

    useVC.name = 'vcList'
    useVC.produce = lambda x: x.useVC if hasattr(x, 'useVC') else None


class IRoomReservationMetadataFossil(IReservationMetadataFossilBase):
    pass


class IPeriodFossil(IFossil):
    def startDT(self):
        pass
    startDT.convert = Conversion.naive

    def endDT(self):
        pass
    endDT.convert = Conversion.naive


class IReservationMetadataFossil(IReservationMetadataFossilBase):
    def locationName(self):
        pass
    locationName.name = 'location'

    def room(self):
        pass
    room.result = IMinimalRoomMetadataFossil


class RoomBookingExportInterface(ExportInterface):
    """
    Base export interface for RB related stuff
    """

    def _getQueryParams(self, qdata):
        super(RoomBookingExportInterface, self)._getQueryParams(qdata)

        self._fromDT = utcdate(self._fromDT) if self._fromDT else None
        self._toDT = utcdate(self._toDT) if self._toDT else None
        self._resvFilter = getResvStateFilter(qdata)

    @staticmethod
    def _repeatingIterator(resv):
        """
        Iterates over all repeatings of a booking
        """
        last = resv.startDT - timedelta(days=1)
        while True:
            rep = resv.getNextRepeating(last)
            if rep == None:
                break
            else:
                yield rep
                last = rep.startDT

    def _addOccurrences(self, fossil, obj, startDT, endDT):
        if self._detail == 'occurrences':
            # get occurrences in the date interval
            fossil['occurrences'] = fossilize(itertools.ifilter(
                lambda x: x.startDT >= startDT and x.endDT <= endDT, self._repeatingIterator(obj)),
                                             {Period: IPeriodFossil}, tz=self._tz, naiveTZ=self._serverTZ)

        return fossil


class RoomExportInterface(RoomBookingExportInterface):
    DETAIL_INTERFACES = {
        'rooms': IRoomMetadataFossil,
        'reservations': IRoomMetadataWithReservationsFossil,
        'occurrences': IRoomMetadataWithReservationsFossil
    }

    def _postprocess(self, obj, fossil, iface):

        if iface is IRoomMetadataWithReservationsFossil:
            (startDT, endDT) = (self._fromDT or MIN_DATETIME,
                                self._toDT or MAX_DATETIME)

            if self._fromDT or self._toDT:
                toDate = self._toDT.date() if self._toDT else None
                fromDate = self._fromDT.date() if self._fromDT else None

                resvEx = ReservationBase()
                resvEx.startDT = startDT
                resvEx.endDT = endDT
                resvEx.room = obj
                resvEx.isRejected = False
                resvEx.isCancelled = False

                if fromDate != toDate:
                    resvEx.repeatability = RepeatabilityEnum.daily

                resvs = set(c.withReservation for c in resvEx.getCollisions())
            else:
                resvs = obj.getReservations()

            iresvs1, iresvs2 = itertools.tee(itertools.ifilter(self._resvFilter, resvs), 2)
            fresvs = fossilize(iresvs1, IRoomReservationMetadataFossil, tz=self._tz, naiveTZ=self._serverTZ)

            for fresv, resv in itertools.izip(iter(fresvs), iresvs2):
                self._addOccurrences(fresv, resv, startDT, endDT)

            fossil['reservations'] = fresvs

        return fossil

    def room(self, location, idlist, qdata):

        self._getQueryParams(qdata)

        Factory.getDALManager().connect()
        rooms = CrossLocationQueries.getRooms(location=location)

        def _iterate_rooms(objIds):
            objIds = map(int, objIds)
            return (room for room in rooms if room.id in objIds)

        for obj in self._process(_iterate_rooms(idlist)):
            yield obj
        Factory.getDALManager().disconnect()


class ReservationExportInterface(RoomBookingExportInterface):
    DETAIL_INTERFACES = {
        'reservations': IReservationMetadataFossil,
        'occurrences': IReservationMetadataFossil
    }

    def _postprocess(self, obj, fossil, iface):
        return self._addOccurrences(fossil, obj, self._fromDT, self._toDT)


    def reservation(self, locList, qdata):

        self._getQueryParams(qdata)

        Factory.getDALManager().connect()

        resvEx = ReservationBase()
        resvEx.startDT = self._fromDT
        resvEx.endDT = self._toDT

        locList = filter(lambda loc: Location.parse(loc) is not None, locList)

        if self._fromDT or self._toDT:
            daysParam = (day.date() for day in rrule.rrule(rrule.DAILY, dtstart=self._fromDT, until=self._toDT))
        else:
            # slow!
            daysParam = None

        for loc in sorted(locList):
            resvs = CrossLocationQueries.getReservations(location=loc, resvExample=resvEx, days=daysParam)
            for obj in self._process(resvs, filter=self._resvFilter):
                yield obj

        Factory.getDALManager().disconnect()


def getResvStateFilter(qdata):
    cancelled = get_query_parameter(qdata, ['cxl', 'cancelled'])
    rejected = get_query_parameter(qdata, ['rej', 'rejected'])
    confirmed = get_query_parameter(qdata, ['confirmed'], -1)
    archival = get_query_parameter(qdata, ['arch', 'archival'])
    repeating = get_query_parameter(qdata, ['rec', 'recurring', 'rep', 'repeating'])
    avc = get_query_parameter(qdata, ['avc'])
    avcSupport = get_query_parameter(qdata, ['avcs', 'avcsupport'])
    bookedFor = get_query_parameter(qdata, ['bf', 'bookedfor'])
    if not any((cancelled, rejected, confirmed != -1, archival, repeating, avc, avcSupport, bookedFor)):
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
    if repeating is not None:
        repeating = (repeating == 'yes')
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
        if repeating is not None and repeating == (obj.repeatability is None):
            return False
        if avc is not None and obj.usesAVC != avc:
            return False
        if avcSupport is not None and obj.needsAVCSupport != avcSupport:
            return False
        if bookedFor and not fnmatch.fnmatch(obj.bookedForName.lower(), bookedFor.lower()):
            return False
        return True
    return _filter
