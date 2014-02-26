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

from datetime import datetime, time, timedelta

from dateutil.relativedelta import relativedelta
from flask import session

from MaKaC.roomMapping import RoomMapperHolder
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.wcomponents import WTemplated

from ...models.locations import Location
from ...models.reservations import RepeatMapping, RepeatUnit
from ...models.rooms import Room
from ...models.utils import next_work_day
from ...views import WPRoomBookingBase
from ...views.utils import makePercentageString

from indico.util.i18n import _


class WPRoomBookingMapOfRooms(WPRoomBookingBase):

    def __init__(self, rh, **params):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh
        self._params = params

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Map of rooms'))

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingMapOfRooms(**self._params).getHTML(params)


class WRoomBookingMapOfRooms(WTemplated):

    def __init__(self, **params):
        WTemplated.__init__(self)
        self._params = params if params else {}

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['mapOfRoomsWidgetURL'] = UH.UHRoomBookingMapOfRoomsWidget.getURL(None, **self._params)
        return wvars


class WPRoomBookingMapOfRoomsWidget(WPNotDecorated):

    def __init__(self, rh, aspects, buildings, defaultLocation, forVideoConference, roomID):
        WPNotDecorated.__init__(self, rh)
        self._aspects = aspects
        self._buildings = buildings
        self._defaultLocation = defaultLocation
        self._forVideoConference = forVideoConference
        self._roomID = roomID

    def getCSSFiles(self):
        return WPNotDecorated.getCSSFiles(self) + ['css/mapofrooms.css']

    def getJSFiles(self):
        return WPNotDecorated.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return '{} - {}'.format(WPNotDecorated._getTitle(self), _('Map of rooms'))

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingMapOfRoomsWidget(self._aspects,
                                            self._buildings,
                                            self._defaultLocation,
                                            self._forVideoConference,
                                            self._roomID).getHTML(params)


class WRoomBookingMapOfRoomsWidget(WTemplated):

    def __init__(self, aspects, buildings, defaultLocationName, forVideoConference, roomID):
        self._aspects = aspects
        self._buildings = buildings
        self._default_location_name = defaultLocationName
        self._forVideoConference = forVideoConference
        self._roomID = roomID

    def getVars(self):
        wvars = WTemplated.getVars(self)

        wvars['aspects'] = self._aspects
        wvars['buildings'] = self._buildings
        wvars['defaultLocation'] = self._default_location_name
        wvars['forVideoConference'] = self._forVideoConference
        wvars['roomID'] = self._roomID

        wvars['roomBookingRoomListURL'] = UH.UHRoomBookingRoomList.getURL(None)
        wvars['startDT'] = session.get('_rb_default_start')
        wvars['endDT'] = session.get('_rb_default_end')
        wvars['startT'] = session.get('_rb_default_start').time().strftime('%H:%M')
        wvars['endT'] = session.get('_rb_default_end').time().strftime('%H:%M')

        wvars['repeat_mapping'] = RepeatMapping.getMapping()
        wvars['default_repeat'] = session.get('_rb_default_repeatability')

        return wvars


class WPRoomBookingRoomList(WPRoomBookingBase):

    def __init__(self, rh):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh

    def _getTitle(self):
        return '{} - {}'.format(
            WPRoomBookingBase._getTitle(self),
            _('My Rooms') if self._rh._form.is_only_my_rooms.data else _('Found rooms')
        )

    def _setCurrentMenuItem(self):
        if self._rh._form.is_only_my_rooms.data:
            self._myRoomListOpt.setActive(True)
        else:
            self._roomSearchOpt.setActive(True)


    def _getBody(self, params):
        return WRoomBookingRoomList(self._rh, standalone=True).getHTML(params)


class WRoomBookingRoomList(WTemplated):

    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._standalone = standalone

    def getVars(self):
        wvars = WTemplated.getVars(self)
        f = self._rh._form

        wvars['rooms'] = self._rh._rooms
        wvars['mapAvailable'] = self._rh._mapAvailable
        wvars['standalone'] = self._standalone
        wvars['title'] = self._rh._title
        if f.is_only_my_rooms.data:
            wvars['noResultsMsg'] = _('You are not the owner of any room')
        else:
            wvars['noResultsMsg'] = _('There are no rooms with this search criteria')

        if self._standalone:
            wvars['detailsUH'] = UH.UHRoomBookingRoomDetails
            wvars['bookingUH'] = UH.UHRoomBookingBookingForm
        else:
            wvars['conference'] = self._rh._conf
            wvars['detailsUH'] = UH.UHConfModifRoomBookingRoomDetails
            wvars['bookingUH'] = UH.UHConfModifRoomBookingBookingForm
        wvars['modificationUH'] = UH.UHRoomBookingRoomForm
        wvars['mapUH'] = UH.UHRoomBookingMapOfRooms

        return wvars


class WPRoomBookingSearch4Rooms(WPRoomBookingBase):

    def __init__(self, rh, is_new_booking=False):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh
        self._is_new_booking = is_new_booking

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Search for rooms'))

    def _setCurrentMenuItem(self):
        if self._is_new_booking:
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
        wvars = WTemplated.getVars(self)

        wvars['standalone'] = self._standalone
        wvars['forNewBooking'] = self._rh._is_new_booking
        wvars['eventRoomName'] = self._rh._event_room_name

        wvars['locations'] = self._rh._locations
        wvars['rooms'] = self._rh._rooms
        wvars['possibleEquipment'] = self._rh._equipments
        wvars['isResponsibleForRooms'] = Room.isAvatarResponsibleForRooms(self._rh.getAW().getUser())

        today = next_work_day()
        wvars['startDT'] = datetime.combine(today.date(), time(8, 30))
        wvars['endDT'] = datetime.combine(today.date(), time(17, 30))
        wvars['startT'] = wvars['startDT'].time().strftime("%H:%M")
        wvars['endT'] = wvars['endDT'].strftime("%H:%M")
        wvars['repeatability'] = RepeatMapping.getOldMapping(RepeatUnit.NEVER, 0)

        if self._standalone:
            # URLs for standalone room booking
            wvars['roomBookingRoomListURL'] = UH.UHRoomBookingRoomList.getURL(None)
            wvars['detailsUH'] = UH.UHRoomBookingRoomDetails
            wvars['bookingFormUH'] = UH.UHRoomBookingBookingForm
        else:
            # URLs for room booking in the event context
            wvars['roomBookingRoomListURL'] = UH.UHConfModifRoomBookingRoomList.getURL(self._rh._conf)
            wvars['detailsUH'] = UH.UHConfModifRoomBookingRoomDetails
            wvars['bookingFormUH'] = UH.UHConfModifRoomBookingBookingForm
        return wvars


class WPRoomBookingRoomDetails(WPRoomBookingBase):

    def __init__(self, rh):
        self._rh = rh
        WPRoomBookingBase.__init__(self, self._rh)

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Room Details'))

    def _setCurrentMenuItem(self):
        self._roomSearchOpt.setActive(True)

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getBody(self, params):
        return WRoomBookingRoomDetails(self._rh, standalone=True).getHTML(params)


class WRoomBookingRoomDetails(WTemplated):

    DEFAULT_CALENDAR_RANGE = relativedelta(month=3)

    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._standalone = standalone

    def getVars(self):
        wvars = WTemplated.getVars(self)
        room = self._rh._room

        wvars['standalone'] = self._standalone
        wvars['room'] = room

        # goodFactory = Location.parse(self._rh._room.locationName).factory
        # attributes = goodFactory.getCustomAttributesManager().getAttributes(location=self._rh._room.locationName)
        # wvars["attrs"] = {}
        # for attribute in attributes:
        #     if not attribute.get("hidden", False) or self._rh._getUser().isAdmin():
        #         wvars["attrs"][attribute['name']] = self._rh._room.customAtts.get(attribute['name'],"")
        #         if attribute['name'] == 'notification email':
        #             wvars["attrs"][attribute['name']] = wvars["attrs"][attribute['name']].replace(',', ', ')

        wvars['attrs'] = []

        wvars['actionSucceeded'] = self._rh._afterActionSucceeded
        wvars['deletionFailed'] = self._rh._afterDeletionFailed

        wvars['owner_name'] = room.getResponsibleName()

        wvars['bookable_times'] = room.getBookableTimes()
        wvars['nonbookable_dates'] = room.getNonBookableDates()

        # URLs
        wvars['stats_url'] = UH.UHRoomBookingRoomStats.getURL(room)
        if self._standalone:
            wvars['booking_details_url'] = UH.UHRoomBookingBookingDetails.getURL()
            wvars['booking_form_url'] = UH.UHRoomBookingBookingForm.getURL()
            wvars['delete_room_url'] = UH.UHRoomBookingDeleteRoom.getURL(room)
            wvars['modify_room_url'] = UH.UHRoomBookingRoomForm.getURL(room)
        else:
            wvars['booking_form_url'] = UH.UHConfModifRoomBookingBookingForm.getURL()
            wvars['booking_details_url'] = UH.UHConfModifRoomBookingDetails.getURL()
            wvars['conference'] = self._rh._conf
            wvars['delete_room_url'] = UH.UHRoomBookingDeleteRoom.getURL(room)
            wvars['modify_room_url'] = UH.UHRoomBookingRoomForm.getURL(room)

        s, e = self._rh._searching_start, self._rh._searching_end
        if s and e:
            s = datetime.utcnow()
            e = s + self.__class__.DEFAULT_CALENDAR_RANGE
        wvars['calendar_start'], wvars['calendar_end'] = s, e

        # TODO
        # # Example resv. to ask for other reservations
        # resvEx = CrossLocationFactory.newReservation(location=self._rh._room.locationName)
        # resvEx.startDT = calendarStartDT
        # resvEx.endDT = calendarEndDT
        # resvEx.repeatability = RepeatabilityEnum.daily
        # resvEx.room = self._rh._room
        # resvEx.isConfirmed = None # to include not also confirmed

        # # Bars: Existing reservations
        # collisionsOfResvs = resvEx.getCollisions()

        # bars = []
        # for c in collisionsOfResvs:
        #     if c.withReservation.isConfirmed:
        #         bars.append(Bar(c, Bar.UNAVAILABLE))
        #     else:
        #         bars.append(Bar(c, Bar.PREBOOKED))

        # bars = barsList2Dictionary(bars)
        # bars = addOverlappingPrebookings(bars)
        # bars = sortBarsByImportance(bars, calendarStartDT, calendarEndDT)

        # # Set owner for all
        # if not self._standalone:
        #     for dt in bars.iterkeys():
        #         for bar in bars[dt]:
        #             bar.forReservation.setOwner(self._rh._conf)

        # bars = introduceRooms([self._rh._room], bars, calendarStartDT,
        #                       calendarEndDT, user=self._rh._aw.getUser())
        # fossilizedBars = {}
        # for key in bars:
        #     fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
        # wvars["barsFossil"] = fossilizedBars
        # wvars["dayAttrs"] = fossilize(dict((day.strftime("%Y-%m-%d"),
        #                                    getDayAttrsForRoom(day, self._rh._room))
        #                                    for day in bars.iterkeys()))
        # wvars["bars"] = bars
        # wvars["iterdays"] = iterdays
        # wvars["day_name"] = day_name
        # wvars["Bar"] = Bar
        wvars['withConflicts'] = False
        wvars['currentUser'] = self._rh._aw.getUser()
        wvars['barsFossil'] = None
        wvars['dayAttrs'] = None

        room_mapper = RoomMapperHolder().match({'placeName': self._rh._location.name}, exact=True)
        if room_mapper:
            wvars['show_on_map'] = room_mapper[0].getMapURL(self._rh._room.name)
        else:
            wvars['show_on_map'] = UH.UHRoomBookingMapOfRooms.getURL(roomID=self._rh._room.id)

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
        wvars['room'] = self._rh._room
        wvars["standalone"] = self._standalone
        wvars["period"] = self._rh._period
        wvars["kpiAverageOccupation"] = makePercentageString(self._rh._kpiAverageOccupation)
        # Bookings
        wvars["kbiTotalBookings"] = self._rh._totalBookings
        # Next 9 KPIs
        wvars["stats"] = self._rh._booking_stats
        wvars["statsURL"] = UH.UHRoomBookingRoomStats.getURL(self._rh._room)
        return wvars
