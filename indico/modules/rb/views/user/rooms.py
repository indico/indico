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

from datetime import datetime, time

from dateutil.relativedelta import relativedelta
from flask import session

from MaKaC.roomMapping import RoomMapperHolder
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.wcomponents import WTemplated
from indico.modules.rb.models.utils import next_work_day
from indico.modules.rb.views import WPRoomBookingBase
from indico.modules.rb.views.calendar import RoomBookingCalendarWidget
from indico.util.i18n import _
from indico.web.flask.util import url_for


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
    def getCSSFiles(self):
        return WPNotDecorated.getCSSFiles(self) + ['css/mapofrooms.css']

    def getJSFiles(self):
        return WPNotDecorated.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return '{} - {}'.format(WPNotDecorated._getTitle(self), _('Map of rooms'))

    def _setCurrentMenuItem(self):
        self._roomMapOpt.setActive(True)

    def _getBody(self, params):
        return WTemplated('RoomBookingMapOfRoomsWidget').getHTML(params)


class WPRoomBookingSearchRooms(WPRoomBookingBase):
    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Search for rooms'))

    def _setCurrentMenuItem(self):
        self._roomSearchOpt.setActive(True)

    def _getBody(self, params):
        today = next_work_day()
        params['startDT'] = datetime.combine(today.date(), time(8, 30))
        params['endDT'] = datetime.combine(today.date(), time(17, 30))
        params['startT'] = params['startDT'].strftime('%H:%M')
        params['endT'] = params['endDT'].strftime('%H:%M')
        return WTemplated('RoomBookingSearchRooms').getHTML(params)


class WPRoomBookingSearchRoomsResults(WPRoomBookingBase):
    def __init__(self, rh, menu_item, **kwargs):
        self._menu_item = menu_item
        WPRoomBookingBase.__init__(self, rh, **kwargs)

    def _setCurrentMenuItem(self):
        getattr(self, '_{}Opt'.format(self._menu_item)).setActive(True)

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Search results'))

    def _getBody(self, params):
        return WTemplated('RoomBookingSearchRoomsResults').getHTML(params)


class WPRoomBookingRoomDetails(WPRoomBookingBase):
    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Room Details'))

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getBody(self, params):
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             specific_room=params['room'])
        params['calendar'] = calendar.render(show_navbar=False, can_navigate=False)
        return WRoomBookingRoomDetails(self._rh, standalone=True).getHTML(params)


class WRoomBookingRoomDetails(WTemplated):
    DEFAULT_CALENDAR_RANGE = relativedelta(month=3)

    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._standalone = standalone

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['standalone'] = self._standalone
        room = wvars['room']

        wvars['attrs'] = {attr.attribute.name: attr for attr in room.attributes}

        wvars['actionSucceeded'] = self._rh._afterActionSucceeded
        wvars['deletionFailed'] = self._rh._afterDeletionFailed

        wvars['owner_name'] = room.getResponsibleName()

        wvars['bookable_times'] = room.bookable_times.all()
        wvars['nonbookable_dates'] = room.nonbookable_dates.all()

        # URLs
        wvars['stats_url'] = UH.UHRoomBookingRoomStats.getURL(room)
        if self._standalone:
            wvars['booking_details_url'] = UH.UHRoomBookingBookingDetails.getURL()
            wvars['booking_form_url'] = UH.UHRoomBookingBookingForm.getURL()
            wvars['delete_room_url'] = url_for('rooms_admin.delete_room', room)
            wvars['modify_room_url'] = url_for('rooms_admin.modify_room', room)
        else:
            wvars['booking_form_url'] = UH.UHConfModifRoomBookingBookingForm.getURL()
            wvars['booking_details_url'] = UH.UHConfModifRoomBookingDetails.getURL()
            wvars['conference'] = self._rh._conf
            wvars['delete_room_url'] = url_for('rooms_admin.delete_room', room)
            wvars['modify_room_url'] = url_for('rooms_admin.modify_room', room)



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
        wvars["kpiAverageOccupation"] = '{0:.02f}%'.format(self._rh._kpiAverageOccupation * 100)
        # Bookings
        wvars["kbiTotalBookings"] = self._rh._totalBookings
        # Next 9 KPIs
        wvars["stats"] = self._rh._booking_stats
        wvars["statsURL"] = UH.UHRoomBookingRoomStats.getURL(self._rh._room)
        return wvars
