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


"""
Asynchronous request handlers for room booking
"""
from MaKaC.services.interface.rpc.common import ServiceError

import time
from datetime import datetime
from MaKaC.services.implementation.base import ServiceBase, LoggedOnlyService

from MaKaC.plugins.RoomBooking.rb_roomblocking import RoomBlockingBase
from MaKaC.rb_reservation import ReservationBase
from MaKaC.rb_location import Location, MapAspect, RoomGUID
from MaKaC.rb_location import CrossLocationQueries
import MaKaC.common.info as info
from MaKaC.common.utils import HolidaysHolder, isWeekend
from MaKaC.errors import NoReportError
from MaKaC.webinterface.rh.roomBooking import RoomBookingAvailabilityParamsMixin
import MaKaC.webinterface.linking as linking
from MaKaC.rb_factory import Factory


class RoomBookingListLocations(ServiceBase):

    def _getAnswer(self):
        """
        Calls _handle() on the derived classes, in order to make it happen. Provides
        them with self._value.
        """

        result = {}

        locationNames = map(lambda l: l.friendlyName, Location.allLocations)

        for name in locationNames:
            result[name] = name

        return result


class RoomBookingListRooms(ServiceBase):

    def _checkParams(self):

        try:
            self._location = self._params["location"]
        except:
            raise ServiceError("ERR-RB0", "Invalid location.")

    def _getAnswer(self):

        res = {}
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            if Location.parse(self._location):
                for room in CrossLocationQueries.getRooms(location=self._location):
                    res[room.name] = room.name
        return sorted(res)


class RoomBookingAvailabilitySearchRooms(ServiceBase, RoomBookingAvailabilityParamsMixin):

    def _checkParams(self):
        try:
            self._location = self._params["location"]
        except:
            raise ServiceError("ERR-RB0", "Invalid location.")

        self._checkParamsRepeatingPeriod(self._params)

    def _getAnswer(self):
        p = ReservationBase()
        p.startDT = self._startDT
        p.endDT = self._endDT
        p.repeatability = self._repeatability

        rooms = CrossLocationQueries.getRooms(location=self._location, resvExample=p, available=True)

        return [room.id for room in rooms]


class RoomBookingFullNameListRooms(RoomBookingListRooms):

    def _getAnswer(self):

        res = []
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            if Location.parse(self._location):
                for room in CrossLocationQueries.getRooms(location=self._location, allFast=True):
                        res.append((room.name, room.getFullName()))
        return res


class RoomBookingListLocationsAndRooms(ServiceBase):

    def _getAnswer(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive():
            result = {}
            locationNames = map(lambda l: l.friendlyName, Location.allLocations)
            for loc in locationNames:
                for room in CrossLocationQueries.getRooms(location=loc):
                    result[loc + ":" + room.name] = loc + ":" + room.name
            return sorted(result)
        else:
            return []


class RoomBookingListLocationsAndRoomsWithGuids(ServiceBase):

    def _checkParams(self):
        self._isActive = self._params.get('isActive', None)

    def _getAnswer(self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        result = {}
        if minfo.getRoomBookingModuleActive():
            locationNames = map(lambda l: l.friendlyName, Location.allLocations)
            for loc in locationNames:
                roomEx = Factory.newRoom()
                roomEx.isActive = self._isActive
                for room in CrossLocationQueries.getRooms(location=loc, roomExample=roomEx):
                    result[str(room.guid)] = "%s: %s" % (loc, room.getFullName())
        return result


class GetBookingBase(object):

    def _getRoomInfo(self, target):
        location = target.getOwnLocation()

        if location:
            locName = location.getName()
            locAddress = location.getAddress()
        else:
            locName = None
            locAddress = None

        room = target.getOwnRoom()

        if room:
            roomName = room.getName()
        else:
            roomName = None

        return {'location': locName,
                'room': roomName,
                'address': locAddress}

    def _getAnswer(self):
        return self._getRoomInfo(self._target)


class GetDateWarning(ServiceBase):

    def _checkParams(self):
        """
        Extracts startDT, endDT and repeatability
        from the form, if present.

        Assigns these values to self, or Nones if values
        are not present.
        """

        sDay = self._params.get("sDay")
        eDay = self._params.get("eDay")
        sMonth = self._params.get("sMonth")
        eMonth = self._params.get("eMonth")
        sYear = self._params.get("sYear")
        eYear = self._params.get("eYear")

        if sDay and len(sDay.strip()) > 0:
            sDay = int(sDay.strip())

        if eDay and len(eDay.strip()) > 0:
            eDay = int(eDay.strip())

        if sMonth and len(sMonth.strip()) > 0:
            sMonth = int(sMonth.strip())

#        if sYear and sMonth and sDay:
#            # For format checking
#            try:
#                time.strptime(sDay.strip() + "/" + sMonth.strip() + "/" + sYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The Start Date must be of the form DD/MM/YYYY and must be a valid date."))

        if eMonth and len(eMonth.strip()) > 0:
            eMonth = int(eMonth.strip())

        if sYear and len(sYear.strip()) > 0:
            sYear = int(sYear.strip())

        if eYear and len(eYear.strip()) > 0:
            eYear = int(eYear.strip())

#        if eYear and eMonth and eDay:
#            # For format checking
#            try:
#                time.strptime(eDay.strip() + "/" + eMonth.strip() + "/" + eYear.strip() , "%d/%m/%Y")
#            except ValueError:
#                raise NoReportError(_("The End Date must be of the form DD/MM/YYYY and must be a valid date."))

        sTime = self._params.get("sTime")
        if sTime and len(sTime.strip()) > 0:
            sTime = sTime.strip()
        eTime = self._params.get("eTime")
        if eTime and len(eTime.strip()) > 0:
            eTime = eTime.strip()

        # process sTime and eTime
        if sTime and eTime:

            try:
                time.strptime(sTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The Start Time must be of the form HH:MM and must be a valid time."))

            t = sTime.split(':')
            sHour = int(t[0])
            sMinute = int(t[1])

            try:
                time.strptime(eTime, "%H:%M")
            except ValueError:
                raise NoReportError(_("The End Time must be of the form HH:MM and must be a valid time."))

            t = eTime.split(':')
            eHour = int(t[0])
            eMinute = int(t[1])

        self._startDT = None
        self._endDT = None
        if sYear and sMonth and sDay and sTime and eYear and eMonth and eDay and eTime:
            # Full period specified
            self._startDT = datetime(sYear, sMonth, sDay, sHour, sMinute)
            self._endDT = datetime(eYear, eMonth, eDay, eHour, eMinute)
        elif sYear and sMonth and sDay and eYear and eMonth and eDay:
            # There are no times
            self._startDT = datetime(sYear, sMonth, sDay, 0, 0, 0)
            self._endDT = datetime(eYear, eMonth, eDay, 23, 59, 59)
        elif sTime and eTime:
            # There are no dates
            self._startDT = datetime(1990, 1, 1, sHour, sMinute)
            self._endDT = datetime(2030, 12, 31, eHour, eMinute)
        self._today = False
        if self._params.get("day", "") == "today":
            self._today = True
            self._startDT = datetime.today().replace(hour=0, minute=0, second=0)
            self._endDT = self._startDT.replace(hour=23, minute=59, second=59)

    def _getAnswer(self):
        if not self._startDT or not self._endDT:
            return ""

        if HolidaysHolder.isWorkingDay(self._startDT) and \
           HolidaysHolder.isWorkingDay(self._endDT):
            return ""

        if isWeekend(self._startDT) or isWeekend(self._endDT):
            return _("weekend chosen")

        return _("holidays chosen")


class RoomBookingMapBase(ServiceBase):
    def _param(self, parameterName):
        try:
            return self._params[parameterName]
        except:
            raise ServiceError("ERR-RB0", "Invalid %s." % parameterName)


class RoomBookingMapCreateAspect(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.parse(self._param("location"))
        self._aspect = self._param("aspect")

    def _getAnswer(self):
        aspect = MapAspect()
        aspect.updateFromDictionary(self._aspect)
        self._location.addAspect(aspect)
        return {}


class RoomBookingMapUpdateAspect(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.parse(self._param("location"))
        self._aspect = self._param("aspect")

    def _getAnswer(self):
        aspect = self._location.getAspect(self._aspect['id'])
        aspect.updateFromDictionary(self._aspect)
        return {}


class RoomBookingMapRemoveAspect(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.parse(self._param("location"))
        self._aspectId = self._param("aspectId")

    def _getAnswer(self):
        self._location.removeAspect(self._aspectId)
        return {}


class RoomBookingMapListAspects(RoomBookingMapBase):

    def _checkParams(self):
        self._location = Location.parse(self._param("location"))

    def _getAnswer(self):
        return [aspect.toDictionary() for aspect in self._location.getAspects()]


class RoomBookingLocationsAndRoomsGetLink(ServiceBase):

    def _checkParams(self):
        self._location = self._params["location"]
        self._room = self._params["room"]

    def _getAnswer(self):
        return linking.RoomLinker().getURLByName(self._room, self._location)


class RoomBookingBlockingProcessBase(ServiceBase):

    def _checkParams(self):
        self._blocking = RoomBlockingBase.getById(int(self._params["blockingId"]))
        self._room = RoomGUID.parse(self._params["room"]).getRoom()
        self._roomBlocking = self._blocking.getBlockedRoom(self._room)

    def _checkProtection(self):
        user = self._aw.getUser()
        if not user or (not user.isAdmin() and not self._room.isOwnedBy(user)):
            raise ServiceError(_('You are not permitted to modify this blocking'))


class RoomBookingBlockingApprove(RoomBookingBlockingProcessBase):

    def _getAnswer(self):
        self._roomBlocking.approve()
        return {"active": self._roomBlocking.getActiveString()}


class RoomBookingBlockingReject(RoomBookingBlockingProcessBase):

    def _checkParams(self):
        RoomBookingBlockingProcessBase._checkParams(self)
        self._reason = self._params.get('reason')
        if not self._reason:
            raise ServiceError(_('You have to specify a rejection reason'))

    def _getAnswer(self):
        self._roomBlocking.reject(self._getUser(), self._reason)
        return {"active": self._roomBlocking.getActiveString()}


class BookingPermission(LoggedOnlyService):
    def _checkParams(self):
        self._room = CrossLocationQueries.getRooms(roomID=self._params["room_id"])[0]
        blocking_id = self._params.get('blocking_id')
        self._blocking = RoomBlockingBase.getById(blocking_id) if blocking_id else None

    def _getAnswer(self):
        user = self._aw.getUser()
        return {
            'blocked': not self._blocking.canOverride(user) if self._blocking else False,
            'can_book': self._room.canBook(user) or self._room.canPrebook(user),
            'group': self._room.customAtts.get('Booking Simba List')
        }
