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

from flask import request

from indico.modules.rb.controllers import RHRoomBookingBase


class RHRoomBookingMapOfRooms(RHRoomBookingBase):

    def _checkParams(self):
        super(RHRoomBookingMapOfRooms, self)._checkParams(self, request.args)
        self._roomID = request.args.get('roomID')

    def _process(self):
        params = {}
        if self._roomID:
            params['roomID'] = self._roomID
        page = roomBooking_wp.WPRoomBookingMapOfRooms(self, **params)
        return page.display()


class RHRoomBookingMapOfRoomsWidget(RHRoomBookingBase):

    def __init__(self, *args, **kwargs):
        RHRoomBookingBase.__init__(self, *args, **kwargs)
        self._cache = GenericCache('MapOfRooms')

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta( 7 - now.weekday() )

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 0, 0)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 0, 0)

    def _checkParams(self, params):
        self._setGeneralDefaultsInSession()
        RHRoomBookingBase._checkParams(self, params)
        self._roomID = params.get('roomID')

    def _businessLogic(self):
        # get all rooms
        defaultLocation = Location.getDefaultLocation()
        rooms = RoomBase.getRooms(location=defaultLocation.friendlyName)
        aspects = [aspect.toDictionary() for aspect in defaultLocation.getAspects()]

        # specialization for a video conference, CERN-specific
        possibleEquipment = defaultLocation.factory.getEquipmentManager().getPossibleEquipment()
        possibleVideoConference = 'Video conference' in possibleEquipment
        self._forVideoConference = possibleVideoConference and self._getRequestParams().get("avc") == 'y'

        # break-down the rooms by buildings
        buildings = {}
        for room in rooms:
            if room.building:

                # if it's the first room in that building, initialize the building
                building = buildings.get(room.building, None)
                if building is None:
                    title = _("Building") + " %s" % room.building
                    building = {'has_coordinates':False, 'number':room.building, 'title':title, 'rooms':[]}
                    buildings[room.building] = building

                # if the room has coordinates, set the building coordinates
                if room.latitude and room.longitude:
                    building['has_coordinates'] = True
                    building['latitude'] = room.latitude
                    building['longitude'] = room.longitude

                # add the room to its building
                if not self._forVideoConference or room.needsAVCSetup:
                    building['rooms'].append(room.fossilize())

        # filter the buildings with rooms and coordinates and return them
        buildings_with_coords = [b for b in buildings.values() if b['rooms'] and b['has_coordinates']]
        self._defaultLocation = defaultLocation.friendlyName
        self._aspects = aspects
        self._buildings = buildings_with_coords

    def _process(self):
        params = dict(self._getRequestParams())
        params["lang"] = session.lang
        params["user"] = self._aw.getSession().getUser().getId()
        key = str(sorted(params.iteritems()))
        html = self._cache.get(key)
        if not html:
            self._businessLogic()
            page = roomBooking_wp.WPRoomBookingMapOfRoomsWidget(self, self._aspects, self._buildings, self._defaultLocation, self._forVideoConference, self._roomID)
            html = page.display()
            self._cache.set(key, html, 300)
        return html


class RHRoomBookingRoomList( RHRoomBookingBase ):

    def _checkParams( self, params ):

        self._roomLocation = None
        if params.get("roomLocation") and len( params["roomLocation"].strip() ) > 0:
            self._roomLocation = params["roomLocation"].strip()

        self._freeSearch = None
        if params.get("freeSearch") and len( params["freeSearch"].strip() ) > 0:
            s = params["freeSearch"].strip()
            # Remove commas
            self._freeSearch = ""
            for c in s:
                if c != ',': self._freeSearch += c

        self._capacity = None
        if params.get("capacity") and len( params["capacity"].strip() ) > 0:
            self._capacity = int( params["capacity"].strip() )

        self._availability = "Don't care"
        if params.get("availability") and len( params["availability"].strip() ) > 0:
            self._availability = params["availability"].strip()

        if self._availability != "Don't care":
            self._checkParamsRepeatingPeriod( params )

        self._includePrebookings = False
        if params.get( 'includePrebookings' ) == "on": self._includePrebookings = True

        self._includePendingBlockings = False
        if params.get( 'includePendingBlockings' ) == "on": self._includePendingBlockings = True

        # The end of "avail/don't care"

        # Equipment
        self._equipment = []
        for k, v in params.iteritems():
            if k[0:4] == "equ_" and v == "on":
                self._equipment.append( k[4:100] )

        # Special
        self._isReservable = self._ownedBy = self._isAutoConfirmed = None
        self._isActive = True

        if params.get( 'isReservable' ) == "on": self._isReservable = True
        if params.get( 'isAutoConfirmed' ) == "on": self._isAutoConfirmed = True

        # only admins can choose to consult non-active rooms
        if self._getUser() and self._getUser().isRBAdmin() and params.get( 'isActive', None ) != "on":
            self._isActive = None

        self._onlyMy = params.get( 'onlyMy' ) == "on"

    def _businessLogic( self ):
        if self._onlyMy: # Can't be done in checkParams since it must be after checkProtection
            self._title = "My rooms"
            self._ownedBy = self._getUser()

        r = RoomBase()
        r.capacity = self._capacity
        r.isActive = self._isActive
        #r.responsibleId = self._responsibleId
        if self._isAutoConfirmed:
            r.resvsNeedConfirmation = False
        for eq in self._equipment:
            r.insertEquipment( eq )

        if self._onlyMy:
            rooms = self._ownedBy.getRooms()
        elif self._availability == "Don't care":
            rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
                                                  freeText=self._freeSearch,
                                                  ownedBy=self._ownedBy,
                                                  roomExample=r,
                                                  pendingBlockings=self._includePendingBlockings,
                                                  onlyPublic=self._isReservable)
            # Special care for capacity (20% => greater than)
            if len (rooms) == 0:
                rooms = CrossLocationQueries.getRooms(location=self._roomLocation,
                                                      freeText=self._freeSearch,
                                                      ownedBy=self._ownedBy,
                                                      roomExample=r,
                                                      minCapacity=True,
                                                      pendingBlockings=self._includePendingBlockings,
                                                      onlyPublic=self._isReservable)
        else:
            # Period specification
            p = ReservationBase()
            p.startDT = self._startDT
            p.endDT = self._endDT
            p.repeatability = self._repeatability
            if self._includePrebookings:
                p.isConfirmed = None   # because it defaults to True

            # Set default values for later booking form
            session["rbDefaultStartDT"] = p.startDT
            session["rbDefaultEndDT"] = p.endDT
            session["rbDefaultRepeatability"] = p.repeatability

            available = ( self._availability == "Available" )

            rooms = CrossLocationQueries.getRooms( \
                location = self._roomLocation,
                freeText = self._freeSearch,
                ownedBy = self._ownedBy,
                roomExample = r,
                resvExample = p,
                available = available,
                pendingBlockings = self._includePendingBlockings )
            # Special care for capacity (20% => greater than)
            if len ( rooms ) == 0:
                rooms = CrossLocationQueries.getRooms( \
                    location = self._roomLocation,
                    freeText = self._freeSearch,
                    ownedBy = self._ownedBy,
                    roomExample = r,
                    resvExample = p,
                    available = available,
                    minCapacity = True,
                    pendingBlockings = self._includePendingBlockings )

        rooms.sort()

        self._rooms = rooms

        self._mapAvailable = Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomList( self, self._onlyMy )
        return p.display()


class RHRoomBookingSearch4Rooms( RHRoomBookingBase ):

    def _cleanDefaultsFromSession( self ):
        session.pop("rbDefaultStartDT", None)
        session.pop("rbDefaultEndDT", None)
        session.pop("rbDefaultRepeatability", None)
        session.pop("rbDefaultBookedForId", None)
        session.pop("rbDefaultBookedForName", None)
        session.pop("rbDefaultReason", None)
        session.pop("rbAssign2Session", None)
        session.pop("rbAssign2Contribution", None)

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 8, 30)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 17, 30)

    def _checkParams( self, params ):
        self._cleanDefaultsFromSession()
        self._setGeneralDefaultsInSession()
        self._forNewBooking = False
        self._eventRoomName = None
        if params.get( 'forNewBooking' ):
            self._forNewBooking = params.get( 'forNewBooking' ) == 'True'

    def _businessLogic( self ):
        self._rooms = CrossLocationQueries.getRooms(allFast = True)
        self._rooms.sort()
        self._equipment = CrossLocationQueries.getPossibleEquipment()

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingSearch4Rooms( self, self._forNewBooking )
        return p.display()


class RHRoomBookingRoomDetails( RHRoomBookingBase ):

    def _setGeneralDefaultsInSession( self ):
        now = datetime.now()

        # if it's saturday or sunday, postpone for monday as a default
        if now.weekday() in [5,6]:
            now = now + timedelta(7 - now.weekday())

        session["rbDefaultStartDT"] = datetime(now.year, now.month, now.day, 0, 0)
        session["rbDefaultEndDT"] = datetime(now.year, now.month, now.day, 0, 0)

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._setGeneralDefaultsInSession()
        self._room = self._target = locator.getObject()

        self._afterActionSucceeded = session.get('rbActionSucceeded')
        self._afterDeletionFailed = session.get('rbDeletionFailed')
        self._formMode = session.get('rbFormMode')

        self._searchingStartDT = self._searchingEndDT = None
        if not params.get('calendarMonths'):
            self._searchingStartDT = session.get("rbDefaultStartDT")
            self._searchingEndDT = session.get("rbDefaultEndDT")

        self._clearSessionState()

    def _businessLogic( self ):
        pass

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomDetails( self )
        return p.display()


class RHRoomBookingRoomStats( RHRoomBookingBase ):

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setRoom( params )
        self._period = params.get("period","pastmonth")
        self._room = self._target = locator.getObject()

    def _businessLogic( self ):
        self._kpiAverageOccupation = self._room.getMyAverageOccupation(self._period)
        self._kpiActiveRooms = RoomBase.getNumberOfActiveRooms()
        self._kpiReservableRooms = RoomBase.getNumberOfReservableRooms()
        self._kpiReservableCapacity, self._kpiReservableSurface = RoomBase.getTotalSurfaceAndCapacity()
        # Bookings
        st = ReservationBase.getRoomReservationStats(self._room)
        self._booking_stats = st
        self._totalBookings = st['liveValid'] + st['liveCancelled'] + st['liveRejected'] + st['archivalValid'] + st['archivalCancelled'] + st['archivalRejected']

    def _process( self ):
        self._businessLogic()
        p = roomBooking_wp.WPRoomBookingRoomStats( self )
        return p.display()
