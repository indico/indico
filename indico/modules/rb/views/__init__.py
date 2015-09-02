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

import os

from flask import session

from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import BasicSideMenu, SideMenuItem, SideMenuSection
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import rb_is_admin
from indico.util.i18n import _
from indico.web.flask.util import url_for


class WPRoomBookingHeadContentMixin:
    def _getHeadContent(self):
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        return """
        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js?%d"></script>
        """ % (self._getBaseURL(), timestamp)


class WPRoomBookingBase(WPRoomBookingHeadContentMixin, WPMainBase):
    def _getTitle(self):
        return '{} - {}'.format(WPMainBase._getTitle(self), _('Room Booking'))

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage(['Management', 'RoomBooking'])

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + self._asset_env['roombooking_sass'].urls()

    def _getSideMenu(self):
        self._leftMenu = BasicSideMenu(session.user is not None)
        user_has_rooms = session.user is not None and Room.user_owns_rooms(session.user)
        user_is_admin = session.user is not None and rb_is_admin(session.user)

        self._roomsBookingOpt = SideMenuSection()

        self._bookRoomNewOpt = SideMenuItem(
            _('Book a Room'),
            url_for('rooms.book'),
            enabled=True
        )

        self._roomMapOpt = SideMenuItem(
            _('Map of rooms'),
            urlHandlers.UHRoomBookingMapOfRooms.getURL(),
            enabled=True
        )

        self._bookingListCalendarOpt = SideMenuItem(
            _('Calendar'),
            url_for('rooms.calendar'),
            enabled=True
        )

        self._bookingsOpt = SideMenuSection(
            _('View My Bookings'),
            urlHandlers.UHRoomBookingSearch4Bookings.getURL()
        )

        self._myBookingListOpt = SideMenuItem(
            _('My bookings'),
            url_for('rooms.my_bookings'),
            enabled=True
        )

        self._usersBookingsOpt = SideMenuItem(
            _('Bookings in my rooms'),
            url_for('rooms.bookings_my_rooms'),
            enabled=user_has_rooms
        )

        self._usersPendingBookingsOpt = SideMenuItem(
            _('Pre-bookings in my rooms'),
            url_for('rooms.pending_bookings_my_rooms'),
            enabled=user_has_rooms
        )

        self._bookingListSearchOpt = SideMenuItem(
            _('Search bookings'),
            urlHandlers.UHRoomBookingSearch4Bookings.getURL(),
            enabled=True
        )

        self._blockingsOpt = SideMenuSection(_('Room Blocking'))

        self._usersBlockingsOpt = SideMenuItem(
            _('Blockings for my rooms'),
            url_for('rooms.blocking_my_rooms', state='pending'),
            enabled=user_has_rooms
        )

        self._roomsOpt = SideMenuSection(_('View Rooms'))

        self._roomSearchOpt = SideMenuItem(
            _('Search rooms'),
            url_for('rooms.search_rooms'),
            enabled=True
        )

        self._myRoomListOpt = SideMenuItem(
            _('My rooms'),
            url_for('rooms.search_my_rooms'),
            enabled=user_has_rooms
        )

        self._blockingListOpt = SideMenuItem(
            _('Blockings'),
            url_for('rooms.blocking_list', only_mine=True, timeframe='recent'),
            enabled=True
        )

        self._blockRoomsOpt = SideMenuItem(
            _('Block rooms'),
            url_for('rooms.create_blocking')
        )

        if user_is_admin:
            self._adminSect = SideMenuSection(
                _('Administration'),
                urlHandlers.UHRoomBookingAdmin.getURL()
            )

            self._adminOpt = SideMenuItem(
                _('Administration'),
                urlHandlers.UHRoomBookingAdmin.getURL()
            )

        self._leftMenu.addSection(self._roomsBookingOpt)
        self._roomsBookingOpt.addItem(self._bookRoomNewOpt)
        default_location = Location.default_location
        if default_location and default_location.is_map_available:
            self._roomsBookingOpt.addItem(self._roomMapOpt)
        self._roomsBookingOpt.addItem(self._bookingListCalendarOpt)

        self._leftMenu.addSection(self._bookingsOpt)
        self._bookingsOpt.addItem(self._myBookingListOpt)
        self._bookingsOpt.addItem(self._usersBookingsOpt)
        self._bookingsOpt.addItem(self._usersPendingBookingsOpt)
        self._bookingsOpt.addItem(self._bookingListSearchOpt)
        self._leftMenu.addSection(self._blockingsOpt)
        self._blockingsOpt.addItem(self._blockRoomsOpt)
        self._blockingsOpt.addItem(self._blockingListOpt)
        self._blockingsOpt.addItem(self._usersBlockingsOpt)
        self._leftMenu.addSection(self._roomsOpt)
        self._roomsOpt.addItem(self._roomSearchOpt)
        self._roomsOpt.addItem(self._myRoomListOpt)
        if user_is_admin:
            self._leftMenu.addSection(self._adminSect)
            self._adminSect.addItem(self._adminOpt)
        return self._leftMenu

    def _isRoomBooking(self):
        return True
