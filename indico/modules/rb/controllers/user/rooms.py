# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, timedelta

from flask import request, session

from MaKaC.common.cache import GenericCache
from MaKaC.webinterface.locators import WebLocator

from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.mixins import AttributeSetterMixin
from indico.modules.rb.models.location_attribute_keys import LocationAttributeKey
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.room_attribute_keys import RoomAttributeKey
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.views.user import rooms as room_views


class RHRoomBookingMapOfRooms(RHRoomBookingBase):

    def _checkParams(self):
        super(RHRoomBookingMapOfRooms, self)._checkParams(self, request.args)
        self._roomID = request.args.get('roomID')

    def _process(self):
        params = {}
        if self._roomID:
            params['roomID'] = self._roomID
        return room_views.WPRoomBookingMapOfRooms(self, **params).display()


class RHRoomBookingMapOfRoomsWidget(RHRoomBookingBase):

    def __init__(self, *args, **kwargs):
        super(RHRoomBookingMapOfRoomsWidget, self).__init__(*args, **kwargs)
        self._cache = GenericCache('MapOfRooms')

    def _setGeneralDefaultsInSession(self):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 0, 0)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 0, 0)

    def _checkParams(self):
        self._setGeneralDefaultsInSession()
        super(RHRoomBookingMapOfRoomsWidget, self)._checkParams(request.args)
        self._roomID = request.args.get('roomID')

    def _businessLogic(self):
        defaultLocation = Location.getDefaultLocation()
        self._defaultLocation = defaultLocation.name
        self._aspects = defaultLocation.getAllAspectsAsDict()
        self._buildings = defaultLocation.getAllBuildings()

        # specialization for a video conference, CERN-specific
        possibleEquipments = LocationAttributeKey.getAllAttributeKeys()
        # possibleEquipments = defaultLocation.factory.getEquipmentManager().getPossibleEquipment()
        self._forVideoConference = ('Video conference' in possibleEquipments) and (request.args.get('avc') == 'y')

    def _process(self):
        params = request.args  # dict(self._getRequestParams())
        params['lang'] = session.lang
        params['user'] = session.user.getId()
        key = str(sorted(params.iteritems()))
        html = self._cache.get(key)
        if not html:
            self._businessLogic()
            page = room_views.WPRoomBookingMapOfRoomsWidget(
                self,
                self._aspects,
                self._buildings,
                self._defaultLocation,
                self._forVideoConference,
                self._roomID
            )
            html = page.display()
            self._cache.set(key, html, 300)
        return html


# TODO
class RHRoomBookingRoomList(AttributeSetterMixin, RHRoomBookingBase):

    def _checkParams(self):

        params = request.args if request.method == 'GET' else request.form  # else is POST

        self.setParam('_roomLocation', params, paramName='roomLocation')
        self.setParam('_freeSearch', params, paramName='freeSearch', callback=lambda e: e.replace(',', ''))
        self.setParam('_capacity', params, paramName='capacity', callback=int)
        self.setParam('_availability', params, paramName='availability', default="Don't care")

        if self._availability != "Don't care":
            self._checkParamsRepeatingPeriod(params)

        self._includePrebookings = params.get('includePrebookings') == 'on'
        self._includePendingBlockings = params.get('includePendingBlockings') == 'on'

        # The end of "avail/don't care"

        # Equipment
        self._equipment = []
        for k, v in params.iteritems():
            if k[0:4] == "equ_" and v == "on":
                self._equipment.append(k[4:100])

        # Special
        self._isReservable = self._ownedBy = self._isAutoConfirmed = None
        if params.get('isReservable') == 'on': self._isReservable = True
        if params.get('isAutoConfirmed') == 'on': self._isAutoConfirmed = True

        # only admins can choose to consult non-active rooms
        self._isActive = True
        if self._getUser() and self._getUser().isRBAdmin() and params.get('isActive', default=None) != 'on':
            self._isActive = None

        self._onlyMy = params.get('onlyMy') == 'on'

    def _businessLogic(self):
        if self._onlyMy: # Can't be done in checkParams since it must be after checkProtection
            self._title = "My rooms"
            self._ownedBy = self._getUser()

        # r = RoomBase()
        # r.capacity = self._capacity
        # r.isActive = self._isActive
        # # r.responsibleId = self._responsibleId
        # if self._isAutoConfirmed:
        #     r.resvsNeedConfirmation = False
        # for eq in self._equipment:
        #     r.insertEquipment( eq )

        if self._onlyMy:
            rooms = self._ownedBy.getRooms()
        elif self._availability == "Don't care":
            pass
            # TODO
            # rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
            #                                       freeText=self._freeSearch,
            #                                       ownedBy=self._ownedBy,
            #                                       roomExample=r,
            #                                       pendingBlockings=self._includePendingBlockings,
            #                                       onlyPublic=self._isReservable)
            # Special care for capacity (20% => greater than)
            if not rooms:
                pass
                # rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
                #                                       freeText=self._freeSearch,
                #                                       ownedBy=self._ownedBy,
                #                                       roomExample=r,
                #                                       minCapacity=True,
                #                                       pendingBlockings=self._includePendingBlockings,
                #                                       onlyPublic=self._isReservable)
        else:
            # Period specification
            # p = ReservationBase()
            # p.startDT = self._startDT
            # p.endDT = self._endDT
            # p.repeatability = self._repeatability
            # if self._includePrebookings:
            #     p.isConfirmed = None   # because it defaults to True

            # # Set default values for later booking form
            # session["rbDefaultStartDT"] = p.startDT
            # session["rbDefaultEndDT"] = p.endDT
            # session["rbDefaultRepeatability"] = p.repeatability

            available = (self._availability == "Available")

            # rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
            #                                       freeText=self._freeSearch,
            #                                       ownedBy=self._ownedBy,
            #                                       roomExample=r,
            #                                       resvExample=p,
            #                                       available=available,
            #                                       pendingBlockings=self._includePendingBlockings)
            # Special care for capacity (20% => greater than)
            if not rooms:
                pass
                # rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
                #                                       freeText=self._freeSearch,
                #                                       ownedBy=self._ownedBy,
                #                                       roomExample=r,
                #                                       resvExample=p,
                #                                       available=available,
                #                                       minCapacity=True,
                #                                       pendingBlockings=self._includePendingBlockings)

        # TODO: model should return sorted
        rooms.sort()
        self._rooms = rooms
        self._mapAvailable = Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable()

    def _process(self):
        self._businessLogic()
        return room_views.WPRoomBookingRoomList(self, self._onlyMy).display()


# TODO
class RHRoomBookingSearch4Rooms(RHRoomBookingBase):

    def _cleanDefaultsFromSession(self):
        session.pop("rbDefaultStartDT", None)
        session.pop("rbDefaultEndDT", None)
        session.pop("rbDefaultRepeatability", None)
        session.pop("rbDefaultBookedForId", None)
        session.pop("rbDefaultBookedForName", None)
        session.pop("rbDefaultReason", None)
        session.pop("rbAssign2Session", None)
        session.pop("rbAssign2Contribution", None)

    def _setGeneralDefaultsInSession(self):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 8, 30)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 17, 30)

    def _checkParams(self):
        params = request.args if request.method == 'GET' else request.form
        self._cleanDefaultsFromSession()
        self._setGeneralDefaultsInSession()
        self._eventRoomName = None
        self._forNewBooking = params.get('forNewBooking', type=bool)  # == True

    def _businessLogic(self):
        self._rooms = Room.getAllRooms()
        # self._rooms = CrossLocationQueries.getRooms(allFast=True)
        # self._rooms.sort()
        self._equipment = RoomAttributeKey.getAllAttributeKeys()
        # self._equipment = CrossLocationQueries.getPossibleEquipment()

    def _process(self):
        self._businessLogic()
        return room_views.WPRoomBookingSearch4Rooms(self, self._forNewBooking).display()


# TODO
class RHRoomBookingRoomDetails(RHRoomBookingBase):

    def _setGeneralDefaultsInSession(self):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 0, 0)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 0, 0)

    def _checkParams(self):
        locator = WebLocator()
        locator.setRoom(request.args)
        self._setGeneralDefaultsInSession()
        self._room = self._target = locator.getObject()

        self._afterActionSucceeded = session.get('rbActionSucceeded')
        self._afterDeletionFailed = session.get('rbDeletionFailed')
        self._formMode = session.get('rbFormMode')

        self._searchingStartDT = self._searchingEndDT = None
        if not request.args.get('calendarMonths'):
            self._searchingStartDT = session.get("rbDefaultStartDT")
            self._searchingEndDT = session.get("rbDefaultEndDT")

        self._clearSessionState()

    def _process(self):
        return room_views.WPRoomBookingRoomDetails(self).display()


# TODO
class RHRoomBookingRoomStats(RHRoomBookingBase):

    def _checkParams(self):
        params = request.args if request.method == 'GET' else request.form
        locator = WebLocator()
        locator.setRoom(params)
        self._period = params.get('period', default='pastmonth')
        self._room = self._target = locator.getObject()

    def _businessLogic(self):
        pass
        # self._kpiAverageOccupation = self._room.getMyAverageOccupation(self._period)
        # self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms()
        # self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms()
        # self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity()
        # # Bookings
        # st = ReservationBase.getRoomReservationStats(self._room)
        # self._booking_stats = st
        # self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

    def _process(self):
        self._businessLogic()
        return room_views.WPRoomBookingRoomStats(self).display()
