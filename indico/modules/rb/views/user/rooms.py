# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from flask import request, session

from indico.legacy.common.cache import GenericCache
from indico.legacy.webinterface.wcomponents import WTemplated
from indico.modules.rb import rb_settings
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import RepeatFrequency, RepeatMapping
from indico.modules.rb.util import rb_is_admin
from indico.modules.rb.views import WPRoomBookingBase, WPRoomBookingLegacyBase
from indico.modules.rb.views.calendar import RoomBookingCalendarWidget
from indico.util.i18n import _
from indico.util.string import crc32
from indico.web.flask.util import url_for
from indico.web.views import WPNotDecorated


class WPRoomBookingMapOfRooms(WPRoomBookingBase):
    sidemenu_option = 'map'


class WPRoomBookingMapOfRoomsWidget(WPNotDecorated):
    sidemenu_option = 'map'
    cache = GenericCache('MapOfRooms')

    def getCSSFiles(self):
        return WPNotDecorated.getCSSFiles(self) + ['css/mapofrooms.css']

    def getJSFiles(self):
        return WPNotDecorated.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _get_widget_params(self):
        default_location = Location.default_location
        return {'aspects': [a.to_serializable() for a in default_location.aspects],
                'buildings': default_location.get_buildings(),
                'default_repeat': '{}|0'.format(int(RepeatFrequency.NEVER)),
                'default_start_dt': datetime.combine(date.today(), Location.working_time_start),
                'default_end_dt': datetime.combine(date.today(), Location.working_time_end),
                'repeat_mapping': RepeatMapping.mapping}

    def _getBody(self, params):
        api_key = rb_settings.get('google_maps_api_key')
        cache_key = str(sorted(dict(request.args, lang=session.lang).items())) + str(crc32(api_key))
        html = self.cache.get(cache_key)
        if html is None:
            params.update(self._get_widget_params())
            params['api_key'] = api_key
            html = WTemplated('RoomBookingMapOfRoomsWidget').getHTML(params)
            self.cache.set(cache_key, html, 3600)
        return html


class WPRoomBookingSearchRooms(WPRoomBookingLegacyBase):
    sidemenu_option = 'search_rooms'

    def _getPageContent(self, params):
        params['startDT'] = datetime.combine(date.today(), Location.working_time_start)
        params['endDT'] = datetime.combine(date.today(), Location.working_time_end)
        params['startT'] = params['startDT'].strftime('%H:%M')
        params['endT'] = params['endDT'].strftime('%H:%M')
        return WTemplated('RoomBookingSearchRooms').getHTML(params)


class WPRoomBookingSearchRoomsResults(WPRoomBookingLegacyBase):
    def __init__(self, rh, menu_item, **kwargs):
        self.sidemenu_option = menu_item
        WPRoomBookingLegacyBase.__init__(self, rh, **kwargs)

    def _getPageContent(self, params):
        return WTemplated('RoomBookingSearchRoomsResults').getHTML(params)


class WPRoomBookingRoomDetails(WPRoomBookingLegacyBase):
    endpoints = {
        'room_book': 'rooms.room_book'
    }

    def _getPageContent(self, params):
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
        wvars['stats_url'] = url_for('rooms.roomBooking-roomStats', room)
        wvars['delete_room_url'] = url_for('rooms_admin.delete_room', room)
        wvars['modify_room_url'] = url_for('rooms_admin.modify_room', room)

        wvars['show_on_map'] = room.map_url if room.map_url else url_for('rooms.roomBooking-mapOfRooms', room)
        return wvars


class WPRoomBookingRoomStats(WPRoomBookingLegacyBase):
    def _getPageContent(self, params):
        params['period_options'] = [
            ('pastmonth', _('Last 30 days')),
            (params['last_month'], _('Previous month')),
            ('thisyear', _('This year')),
            (params['last_year'], _('Previous year')),
            ('sinceever', _('Since ever'))
        ]
        return WTemplated('RoomBookingRoomStats').getHTML(params)
