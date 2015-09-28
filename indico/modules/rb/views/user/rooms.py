# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from flask import session

from MaKaC.roomMapping import RoomMapperHolder
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.wcomponents import WTemplated
from indico.modules.rb.models.locations import Location
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb.views import WPRoomBookingBase
from indico.modules.rb.views.calendar import RoomBookingCalendarWidget
from indico.util.i18n import _
from indico.web.flask.util import url_for


class WPRoomBookingMapOfRooms(WPRoomBookingBase):

    sidemenu_option = 'map'

    def __init__(self, rh, **params):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh
        self._params = params

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Map of rooms'))

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
    sidemenu_option = 'map'

    def getCSSFiles(self):
        return WPNotDecorated.getCSSFiles(self) + ['css/mapofrooms.css']

    def getJSFiles(self):
        return WPNotDecorated.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return '{} - {}'.format(WPNotDecorated._getTitle(self), _('Map of rooms'))

    def _getBody(self, params):
        return WTemplated('RoomBookingMapOfRoomsWidget').getHTML(params)


class WPRoomBookingSearchRooms(WPRoomBookingBase):
    sidemenu_option = 'search_rooms'

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Search for rooms'))

    def _getBody(self, params):
        params['startDT'] = datetime.combine(date.today(), Location.working_time_start)
        params['endDT'] = datetime.combine(date.today(), Location.working_time_end)
        params['startT'] = params['startDT'].strftime('%H:%M')
        params['endT'] = params['endDT'].strftime('%H:%M')
        return WTemplated('RoomBookingSearchRooms').getHTML(params)


class WPRoomBookingSearchRoomsResults(WPRoomBookingBase):
    def __init__(self, rh, menu_item, **kwargs):
        self.sidemenu_option = menu_item
        WPRoomBookingBase.__init__(self, rh, **kwargs)

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Search results'))

    def _getBody(self, params):
        return WTemplated('RoomBookingSearchRoomsResults').getHTML(params)


class WPRoomBookingRoomDetails(WPRoomBookingBase):
    endpoints = {
        'room_book': 'rooms.room_book'
    }

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Room Details'))

    def _getBody(self, params):
        params['endpoints'] = self.endpoints
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

        wvars['attrs'] = {attr.attribute.name: attr for attr in room.attributes
                          if not attr.attribute.is_hidden or rb_is_admin(session.user)}

        wvars['owner_name'] = room.owner.full_name

        wvars['bookable_hours'] = room.bookable_hours.all()
        wvars['nonbookable_periods'] = room.nonbookable_periods.all()

        # URLs
        wvars['stats_url'] = UH.UHRoomBookingRoomStats.getURL(room)
        wvars['delete_room_url'] = url_for('rooms_admin.delete_room', room)
        wvars['modify_room_url'] = url_for('rooms_admin.modify_room', room)
        if not self._standalone:
            wvars['conference'] = self._rh._conf

        room_mapper = RoomMapperHolder().match({'placeName': self._rh._location.name}, exact=True)
        if room_mapper:
            wvars['show_on_map'] = room_mapper[0].getMapURL(self._rh._room.name)
        else:
            wvars['show_on_map'] = UH.UHRoomBookingMapOfRooms.getURL(roomID=self._rh._room.id)

        return wvars


class WPRoomBookingRoomStats(WPRoomBookingBase):
    def _getBody(self, params):
        params['period_options'] = [
            ('pastmonth', _('Past month')),
            ('thisyear', _('This year')),
            ('sinceever', _('Since ever'))
        ]
        return WTemplated('RoomBookingRoomStats').getHTML(params)
