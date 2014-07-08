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

# stdlib imports
import fnmatch
import itertools
from datetime import datetime, timedelta

# 3rd party imports
from pytz import timezone
from dateutil import rrule

# legacy imports
from MaKaC.common.timezoneUtils import utc2server
from MaKaC.plugins.RoomBooking.default.factory import Factory
from MaKaC.plugins.base import PluginsHolder
from MaKaC.rb_tools import Period
from MaKaC.rb_reservation import RepeatabilityEnum, ReservationBase
from MaKaC.user import Group, Avatar
from MaKaC.webinterface.urlHandlers import UHRoomBookingBookingDetails
from MaKaC.rb_room import RoomBase
from MaKaC.common.logger import Logger
from MaKaC.rb_location import CrossLocationFactory, CrossLocationQueries, Location
from MaKaC.rb_tools import doesPeriodOverlap
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.plugins.RoomBooking.common import rb_check_user_access

# indico imports
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.hooks.base import IteratedDataFetcher, HTTPAPIHook
from indico.web.http_api.util import get_query_parameter
from indico.util.fossilize import fossilize, IFossil
from indico.util.fossilize.conversion import Conversion

globalHTTPAPIHooks = ['RoomHook', 'RoomNameHook', 'ReservationHook', 'BookRoomHook']
MAX_DATETIME = datetime(2099, 12, 31, 23, 59, 00)
MIN_DATETIME = datetime(2000, 1, 1, 00, 00, 00)


def utcdate(datet):
    d = datet.astimezone(timezone('UTC'))
    return utc2server(d)

class RoomBookingHook(HTTPAPIHook):
    GUEST_ALLOWED = False

    def _getParams(self):
        super(RoomBookingHook, self)._getParams()

        self._fromDT = utcdate(self._fromDT) if self._fromDT else None
        self._toDT = utcdate(self._toDT) if self._toDT else None
        self._occurrences = get_query_parameter(self._queryParams, ['occ', 'occurrences'], 'no') == 'yes'
        self._resvFilter = getResvStateFilter(self._queryParams)

    def _hasAccess(self, aw):
        """
        Check if the user may access the RB module
        """
        return rb_check_user_access(aw.getUser())


class RoomHook(RoomBookingHook):
    """
    Example: /room/CERN/23.xml
    """
    TYPES = ('room', )
    RE = r'(?P<location>[\w\s]+)/(?P<idlist>\w+(?:-[\w\s]+)*)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 500,
        'reservations': 10
    }
    SERIALIZER_TYPE_MAP = {
        'RoomCERN': 'Room',
        'ReservationCERN': 'Reservation'
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(RoomHook, self)._getParams()
        self._location = self._pathParams['location']
        self._idList = self._pathParams['idlist'].split('-')

    def export_room(self, aw):
        expInt = RoomFetcher(aw, self)
        return expInt.room(self._location, self._idList)


class RoomNameHook(RoomBookingHook):
    GUEST_ALLOWED = True
    TYPES = ('roomName', )
    RE = r'(?P<location>[\w\s]+)/(?P<room_name>[\w\s\-]+)'
    DEFAULT_DETAIL = 'rooms'
    MAX_RECORDS = {
        'rooms': 500
    }
    SERIALIZER_TYPE_MAP = {
        'RoomCERN': 'Room'
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):

        super(RoomNameHook, self)._getParams()
        self._location = self._pathParams['location']
        self._room_name = self._pathParams['room_name']

    def export_roomName(self, aw):
        expInt = RoomNameFetcher(aw, self)
        return expInt.search(self._location, self._room_name)

    def _hasAccess(self, aw):
        """
        Access to RB data (no reservations) is public
        """
        return True


class ReservationHook(RoomBookingHook):
    TYPES = ('reservation', )
    RE = r'(?P<loclist>[\w\s]+(?:-[\w\s]+)*)'
    DEFAULT_DETAIL = 'reservations'
    MAX_RECORDS = {
        'reservations': 100
    }
    SERIALIZER_TYPE_MAP = {
        'RoomCERN': 'Room',
        'ReservationCERN': 'Reservation'
    }
    VALID_FORMATS = ('json', 'jsonp', 'xml', 'ics')

    def _getParams(self):
        super(ReservationHook, self)._getParams()
        self._locList = self._pathParams['loclist'].split('-')

    def export_reservation(self, aw):
        expInt = ReservationFetcher(aw, self)
        return expInt.reservation(self._locList)


class BookRoomHook(HTTPAPIHook):
    PREFIX = 'api'
    TYPES = ('roomBooking',)
    RE = r'bookRoom'
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json', 'xml')
    COMMIT = True
    HTTP_POST = True

    def _getParams(self):
        super(BookRoomHook, self)._getParams()

        username = get_query_parameter(self._queryParams, ['username'])
        booked_for = AuthenticatorMgr().getAvatarByLogin(username).values()

        if not booked_for:
            raise HTTPAPIError('Username does not exist.')

        self._params = {
            'roomid': get_query_parameter(self._queryParams, ['roomid']),
            'location': get_query_parameter(self._queryParams, ['location']),
            'username': username,
            'reason': get_query_parameter(self._queryParams, ['reason']),
            'userBookedFor': booked_for[0],
            'from': self._fromDT,
            'to': self._toDT
            }

        # calculate missing arguments
        missing = list(name for (name, value) in (self._params.iteritems()) if not value)

        if missing:
            raise HTTPAPIError('Argument(s) missing: {0}'.format(', '.join(missing)), 400)

        self._room = CrossLocationQueries.getRooms(location=self._params['location'], roomID=int(self._params['roomid']))

    def _hasAccess(self, aw):
        """
        Check if the API user may book a room
        """
        self._user = aw.getUser()

        if self._room.resvsNeedConfirmation and self._user and not self._user.isAdmin(): # Admins can book, even if only pre-booking enabled.
            raise HTTPAPIError('This room does not accept direct bookings and it '
                               'is not possible to pre-book rooms through the API.')

        return self._room.canBook(self._user)

    def api_roomBooking(self, aw):
        resv = CrossLocationFactory.newReservation(location=self._params['location'])
        resv.room = self._room
        resv.startDT = self._fromDT.replace(tzinfo=None)
        resv.endDT = self._toDT.replace(tzinfo=None)

        # checking room availability
        for nbd in resv.room.getNonBookableDates():
            if (doesPeriodOverlap(nbd.getStartDate(), nbd.getEndDate(), resv.startDT, resv.endDT)):
                raise HTTPAPIError('Failed to create the booking. You cannot book this room because it is unavailable during this time period.')

        roomBlocked = resv.room.getBlockedDay(resv.startDT)

        # checking room blocking
        if roomBlocked and not roomBlocked.block.canOverride(self._user):
            raise HTTPAPIError('Failed to create the booking. You cannot book this room because it is blocked during this time period.')

        resv.repeatability = None
        resv.reason = self._params['reason']
        resv.createdDT = datetime.now()
        resv.createdBy = str(self._user.getId())
        resv.bookedForName = self._params['userBookedFor'].getFullName()
        resv.contactEmail = self._params['userBookedFor'].getEmail()
        resv.contactPhone = self._params['userBookedFor'].getTelephone()
        resv.isRejected = False
        resv.isCancelled = False
        resv.isConfirmed = True

        if resv.getCollisions():
            raise HTTPAPIError('Failed to create the booking. There is a collision with another booking.')

        resv.insert()

        return {'reservationID': resv.id}


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

    def latitude(self):
        """ Room latitude """
        pass

    def longitude(self):
        """ Room longitude """
        pass


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


class INaivePeriodFossil(IFossil):
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


class RoomBookingFetcher(IteratedDataFetcher):
    """
    Base export interface for RB related stuff
    """

    def __init__(self, aw, hook):
        super(RoomBookingFetcher, self).__init__(aw, hook)
        self._occurrences = hook._occurrences
        self._resvFilter = hook._resvFilter

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
        if self._occurrences:
            (startDT, endDT) = (startDT or MIN_DATETIME,
                                endDT or MAX_DATETIME)
            # get occurrences in the date interval
            fossil['occurrences'] = fossilize(itertools.ifilter(
                lambda x: x.startDT >= startDT and x.endDT <= endDT, self._repeatingIterator(obj)),
                                             {Period: INaivePeriodFossil}, tz=self._tz, naiveTZ=self._serverTZ)

        return fossil


class RoomFetcher(RoomBookingFetcher):
    DETAIL_INTERFACES = {
        'rooms': IRoomMetadataFossil,
        'reservations': IRoomMetadataWithReservationsFossil
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

    def room(self, location, idlist):

        Factory.getDALManager().connect()
        rooms = CrossLocationQueries.getRooms(location=location)

        def _iterate_rooms(objIds):
            objIds = map(int, objIds)
            return (room for room in rooms if room.id in objIds)

        for obj in self._process(_iterate_rooms(idlist)):
            yield obj
        Factory.getDALManager().rollback()
        Factory.getDALManager().disconnect()

    def search(self, location, name):

        Factory.getDALManager().connect()
        rooms = CrossLocationQueries.getRooms(location=location)

        def _search_rooms(name):
            return (room for room in rooms if name.lower() in room.getFullName().lower())

        for obj in self._process(_search_rooms(name)):
            yield obj
        Factory.getDALManager().rollback()
        Factory.getDALManager().disconnect()


class RoomNameFetcher(RoomFetcher):
    DETAIL_INTERFACES = {
        'rooms': IRoomMetadataFossil
    }

class ReservationFetcher(RoomBookingFetcher):
    DETAIL_INTERFACES = {
        'reservations': IReservationMetadataFossil
    }

    def _postprocess(self, obj, fossil, iface):
        return self._addOccurrences(fossil, obj, self._fromDT, self._toDT)


    def reservation(self, locList):

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


def getResvStateFilter(queryParams):
    cancelled = get_query_parameter(queryParams, ['cxl', 'cancelled'])
    rejected = get_query_parameter(queryParams, ['rej', 'rejected'])
    confirmed = get_query_parameter(queryParams, ['confirmed'], -1)
    archival = get_query_parameter(queryParams, ['arch', 'archival'])
    repeating = get_query_parameter(queryParams, ['rec', 'recurring', 'rep', 'repeating'])
    avc = get_query_parameter(queryParams, ['avc'])
    avcSupport = get_query_parameter(queryParams, ['avcs', 'avcsupport'])
    startupSupport = get_query_parameter(queryParams, ['sts', 'startupsupport'])
    bookedFor = get_query_parameter(queryParams, ['bf', 'bookedfor'])
    if not any((cancelled, rejected, confirmed != -1, archival, repeating, avc, avcSupport, startupSupport, bookedFor)):
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
    if startupSupport is not None:
        startupSupport = (startupSupport == 'yes')
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
        if startupSupport is not None and obj.needsAssistance != startupSupport:
            return False
        if bookedFor and not fnmatch.fnmatch(obj.bookedForName.lower(), bookedFor.lower()):
            return False
        return True
    return _filter
