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

from flask import session

from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.wcomponents import WTemplated

from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.views import WPRoomBookingBase


class WPRoomBookingMapOfRooms(WPRoomBookingBase):

    def __init__(self, rh, **params):
        self._rh = rh
        self._params = params
        WPRoomBookingBase.__init__(self, rh)

    def _getTitle(self):
        return super(WPRoomBookingMapOfRooms, self)._getTitle() + " - " + _("Map of rooms")

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingMapOfRooms(**self._params).getHTML(params)


class WRoomBookingMapOfRooms(WTemplated):

    def __init__(self, **params):
        if params:
            self._params = params
        else:
            self._params = {}
        super(WRoomBookingMapOfRooms, self).__init__()

    def getVars(self):
        wvars = super(WRoomBookingMapOfRooms, self).getVars()
        wvars["mapOfRoomsWidgetURL"] = urlHandlers.UHRoomBookingMapOfRoomsWidget.getURL(None, **self._params)

        return wvars


class WPRoomBookingMapOfRoomsWidget(WPNotDecorated):

    def __init__(self, rh, aspects, buildings, defaultLocation, forVideoConference, roomID):
        super(WPRoomBookingMapOfRoomsWidget, self).__init__(rh)
        self._aspects = aspects
        self._buildings = buildings
        self._defaultLocation = defaultLocation
        self._forVideoConference = forVideoConference
        self._roomID = roomID

    def getCSSFiles(self):
        return (super(WPRoomBookingMapOfRoomsWidget, self).getCSSFiles() +
                ['css/mapofrooms.css'])

    def getJSFiles(self):
        return (super(WPRoomBookingMapOfRoomsWidget, self).getJSFiles() +
                self._includeJSPackage('RoomBooking'))

    def _getTitle(self):
        return (super(WPRoomBookingMapOfRoomsWidget, self)._getTitle() +
                " - " + _("Map of rooms"))

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingMapOfRoomsWidget(self._aspects, self._buildings,
                                            self._defaultLocation, self._forVideoConference,
                                            self._roomID).getHTML(params)


class WRoomBookingMapOfRoomsWidget(WTemplated):

    def __init__(self, aspects, buildings, defaultLocation, forVideoConference, roomID):
        self._aspects = aspects
        self._buildings = buildings
        self._defaultLocation = defaultLocation
        self._forVideoConference = forVideoConference
        self._roomID = roomID

    def getVars(self):
        wvars = super(WRoomBookingMapOfRoomsWidget, self).getVars()

        wvars["aspects"] = self._aspects
        wvars["buildings"] = self._buildings
        wvars["defaultLocation"] = self._defaultLocation
        wvars["forVideoConference"] = self._forVideoConference
        wvars["roomID"] = self._roomID

        wvars["roomBookingRoomListURL"] = urlHandlers.UHRoomBookingRoomList.getURL(None)
        wvars["startDT"] = session.get("rbDefaultStartDT")
        wvars["endDT"] = session.get("rbDefaultEndDT")
        wvars["startT"] = session.get("rbDefaultStartDT").time().strftime("%H:%M")
        wvars["endT"] = session.get("rbDefaultEndDT").time().strftime("%H:%M")
        wvars["repeatability"] = session.get("rbDefaultRepeatability")

        return wvars


class WPRoomBookingRoomList(WPRoomBookingBase):

    def __init__(self, rh, onlyMy=False):
        self._rh = rh
        self._onlyMy = onlyMy
        super(WPRoomBookingRoomList, self).__init__(rh)

    def _getTitle(self):
        return (super(WPRoomBookingRoomList, self)._getTitle() + ' - ' +
                (_("My Rooms") if self._onlyMy else _("Found rooms")))

    def _setCurrentMenuItem(self):
        if self._onlyMy:
            self._myRoomListOpt.setActive(True)
        else:
            self._roomSearchOpt.setActive(True)


    def _getBody(self, params):
        return WRoomBookingRoomList(self._rh, standalone=True, onlyMy=self._onlyMy).getHTML(params)


class WRoomBookingRoomList(WTemplated):

    def __init__(self, rh, standalone=False, onlyMy=False):
        self._rh = rh
        self._standalone = standalone
        self._title = None
        self._onlyMy = onlyMy
        try: self._title = self._rh._title;
        except: pass

    def getVars(self):
        wvars = super(WRoomBookingRoomList, self).getVars()

        wvars["rooms"] = self._rh._rooms
        wvars["mapAvailable"] = self._rh._mapAvailable
        wvars["standalone"] = self._standalone
        wvars["title"] = self._title
        if self._onlyMy:
            wvars["noResultsMsg"] = _("You are not the owner of any room")
        else:
            wvars["noResultsMsg"] = _("There are no rooms with this search criteria")

        if self._standalone:
            wvars["detailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            wvars["bookingFormUH"] = urlHandlers.UHRoomBookingBookingForm
        else:
            wvars["conference"] = self._rh._conf
            wvars["detailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            wvars["bookingFormUH"] = urlHandlers.UHConfModifRoomBookingBookingForm

        return wvars


class WPRoomBookingSearch4Rooms(WPRoomBookingBase):

    def __init__(self, rh, forNewBooking=False):
        self._rh = rh
        self._forNewBooking = forNewBooking
        super(WPRoomBookingSearch4Rooms, self).__init__(rh)

    def getJSFiles(self):
        return (super(WPRoomBookingSearch4Rooms, self).getJSFiles() +
                self._includeJSPackage('RoomBooking'))

    def _getTitle(self):
        return (super(WPRoomBookingSearch4Rooms, self)._getTitle() +
                " - " + _("Search for rooms"))

    def _setCurrentMenuItem(self):
        if self._forNewBooking:
            self._bookARoomOpt.setActive(True)
        else:
            self._roomSearchOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingSearch4Rooms(self._rh, standalone=True).getHTML(params)


class WRoomBookingSearch4Rooms(WTemplated):

    def __init__(self, rh, standalone=False):
        self._standalone = standalone
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingSearch4Rooms, self).getVars()

        wvars["standalone"] = self._standalone

        wvars["Location"] = Location  # TODO: template logic should come here
        wvars["rooms"] = self._rh._rooms
        wvars["possibleEquipment"] = self._rh._equipment
        wvars["forNewBooking"] = self._rh._forNewBooking
        wvars["eventRoomName"] = self._rh._eventRoomName
        wvars["isResponsibleForRooms"] = Room.isAvatarResponsibleForRooms(self._rh.getAW().getUser())

        wvars["preview"] = False

        wvars["startDT"] = session.get("rbDefaultStartDT")
        wvars["endDT"] = session.get("rbDefaultEndDT")
        wvars["startT"] = session.get("rbDefaultStartDT").time().strftime("%H:%M")
        wvars["endT"] = session.get("rbDefaultEndDT").time().strftime("%H:%M")
        wvars["repeatability"] = session.get("rbDefaultRepeatability")

        if self._standalone:
            # URLs for standalone room booking
            wvars["roomBookingRoomListURL"] = urlHandlers.UHRoomBookingRoomList.getURL(None)
            wvars["detailsUH"] = urlHandlers.UHRoomBookingRoomDetails
            wvars["bookingFormUH"] =  urlHandlers.UHRoomBookingBookingForm
        else:
            # URLs for room booking in the event context
            wvars["roomBookingRoomListURL"] = urlHandlers.UHConfModifRoomBookingRoomList.getURL(self._rh._conf)
            wvars["detailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
            wvars["bookingFormUH"] =  urlHandlers.UHConfModifRoomBookingBookingForm

        return wvars


class WPRoomBookingRoomDetails(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingRoomDetails, self).__init__(rh)

    def _getTitle(self):
        return (super(WPRoomBookingRoomDetails, self)._getTitle() +
                " - " + _("Room Details"))

    def _setCurrentMenuItem(self):
        self._roomSearchOpt.setActive(True)

    def getJSFiles(self):
        return (super(WPRoomBookingRoomDetails, self).getJSFiles() +
                self._includeJSPackage('RoomBooking'))

    def _getBody(self, params):
        return WRoomBookingRoomDetails(self._rh, standalone=True).getHTML(params)


class WRoomBookingRoomDetails(WTemplated):

    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._standalone = standalone

    def getVars(self):
        wvars = super(WRoomBookingRoomDetails, self).getVars()
        wvars["room"] = self._rh._room
        goodFactory = Location.parse( self._rh._room.locationName ).factory
        attributes = goodFactory.getCustomAttributesManager().getAttributes(location=self._rh._room.locationName)
        wvars["attrs"] = {}
        for attribute in attributes:
            if not attribute.get("hidden", False) or self._rh._getUser().isAdmin():
                wvars["attrs"][attribute['name']] = self._rh._room.customAtts.get(attribute['name'],"")
                if attribute['name'] == 'notification email' :
                    wvars["attrs"][attribute['name']] = wvars["attrs"][attribute['name']].replace(',', ', ')
        wvars["config"] = Config.getInstance()
        wvars["standalone"] = self._standalone
        wvars["actionSucceeded"] = self._rh._afterActionSucceeded
        wvars["deletionFailed"] = self._rh._afterDeletionFailed

        wvars["roomStatsUH"] = urlHandlers.UHRoomBookingRoomStats

        if self._standalone:
            wvars["bookingFormUH"] = urlHandlers.UHRoomBookingBookingForm
            wvars["modifyRoomUH"] = urlHandlers.UHRoomBookingRoomForm
            wvars["deleteRoomUH"] = urlHandlers.UHRoomBookingDeleteRoom
            wvars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            wvars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails
            wvars["conference"] = self._rh._conf
            wvars["bookingFormUH"] = urlHandlers.UHConfModifRoomBookingBookingForm
            wvars["modifyRoomUH"] = urlHandlers.UHRoomBookingRoomForm
            wvars["deleteRoomUH"] = urlHandlers.UHRoomBookingDeleteRoom

        # Calendar range: 3 months
        if self._rh._searchingStartDT and self._rh._searchingEndDT:
            sd = self._rh._searchingStartDT
            calendarStartDT = datetime(sd.year, sd.month, sd.day, 0, 0, 1)
            ed = self._rh._searchingEndDT
            calendarEndDT = datetime(ed.year, ed.month, ed.day, 23, 59)
        else:
            now = datetime.now()
            calendarStartDT = datetime(now.year, now.month, now.day, 0, 0, 1)
            calendarEndDT = calendarStartDT + timedelta(3 * 31, 50, 0, 0, 59, 23)

        # Example resv. to ask for other reservations
        resvEx = CrossLocationFactory.newReservation(location = self._rh._room.locationName)
        resvEx.startDT = calendarStartDT
        resvEx.endDT = calendarEndDT
        resvEx.repeatability = RepeatabilityEnum.daily
        resvEx.room = self._rh._room
        resvEx.isConfirmed = None # to include not also confirmed

        # Bars: Existing reservations
        collisionsOfResvs = resvEx.getCollisions()

        bars = []
        for c in collisionsOfResvs:
            if c.withReservation.isConfirmed:
                bars.append(Bar(c, Bar.UNAVAILABLE))
            else:
                bars.append(Bar(c, Bar.PREBOOKED))

        bars = barsList2Dictionary(bars)
        bars = addOverlappingPrebookings(bars)
        bars = sortBarsByImportance(bars, calendarStartDT, calendarEndDT)

        # Set owner for all
        if not self._standalone:
            for dt in bars.iterkeys():
                for bar in bars[dt]:
                    bar.forReservation.setOwner( self._rh._conf )

        wvars["calendarStartDT"] = calendarStartDT
        wvars["calendarEndDT"] = calendarEndDT
        bars = introduceRooms([self._rh._room], bars, calendarStartDT,
                              calendarEndDT, user=self._rh._aw.getUser())
        fossilizedBars = {}
        for key in bars:
            fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
        wvars["barsFossil"] = fossilizedBars
        wvars["dayAttrs"] = fossilize(dict((day.strftime("%Y-%m-%d"),
                                           getDayAttrsForRoom(day, self._rh._room))
                                           for day in bars.iterkeys()))
        wvars["bars"] = bars
        wvars["iterdays"] = iterdays
        wvars["day_name"] = day_name
        wvars["Bar"] = Bar
        wvars["withConflicts"] = False
        wvars["currentUser"] = self._rh._aw.getUser()

        return wvars


class WPRoomBookingRoomStats(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingRoomStats, self).__init__(rh)

    def _setCurrentMenuItem(self):
        self._roomSearchOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingRoomStats(self._rh, standalone=True).getHTML(params)


class WRoomBookingRoomStats(WTemplated):

    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._standalone = standalone

    def getVars(self):
        wvars = super(WRoomBookingRoomStats, self).getVars()
        wvars["room"] = self._rh._room
        wvars["standalone"] = self._standalone
        wvars["period"] = self._rh._period
        wvars["kpiAverageOccupation"] = str(int(round(self._rh._kpiAverageOccupation * 100 ))) + "%"
        # Bookings
        wvars["kbiTotalBookings"] = self._rh._totalBookings
        # Next 9 KPIs
        wvars["stats"] = self._rh._booking_stats
        wvars["statsURL"] = urlHandlers.UHRoomBookingRoomStats.getURL(self._rh._room)
        return wvars
