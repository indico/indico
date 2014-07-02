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

import os

from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.wcomponents import BasicSideMenu, SideMenuItem, SideMenuSection
from indico.util.i18n import _
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.locations import Location
from indico.web.flask.util import url_for


class WPRoomBookingBase(WPMainBase):
    def _getTitle(self):
        return '{} - {}'.format(WPMainBase._getTitle(self), _('Room Booking'))

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage(['Management', 'RoomBooking'])

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + self._asset_env['roombooking_sass'].urls()

    def _getHeadContent(self):
        """
        !!!! WARNING
        If you update the following, you will need to do
        the same update in:
        roomBooking.py / WPRoomBookingBase0  AND
        conferences.py / WPConfModifRoomBookingBase

        For complex reasons, these two inheritance chains
        should not have common root, so this duplication is
        necessary evil. (In general, one chain is for standalone
        room booking and second is for conference-context room
        booking.)
        """
        baseurl = self._getBaseURL()
        return """
        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js?%d"></script>
        """ % (baseurl, os.stat(__file__).st_mtime)

    def _getSideMenu(self):
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()

        self._leftMenu = BasicSideMenu(self._getAW().getUser() is not None)

        self._showResponsible = False

        if minfo.getRoomBookingModuleActive():
            self._showResponsible = ((self._getAW().getUser() is not None)
                                     and (Room.isAvatarResponsibleForRooms(self._getAW().getUser())
                                          or self._getAW().getUser().isAdmin()
                                          or self._getAW().getUser().isRBAdmin()))

        self._roomsBookingOpt = SideMenuSection(currentPage=url_for('rooms.book'))

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

        self._myPendingBookingListOpt = SideMenuItem(
            _('My Pre-bookings'),
            url_for('rooms.my_pending_bookings'),
            enabled=True
        )

        self._usersBookingsOpt = SideMenuItem(
            _('Bookings in my rooms'),
            url_for('rooms.bookings_my_rooms'),
            enabled=self._showResponsible
        )

        self._usersPendingBookingsOpt = SideMenuItem(
            _('Pre-bookings in my rooms'),
            url_for('rooms.pending_bookings_my_rooms'),
            enabled=self._showResponsible
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
            enabled=self._showResponsible
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
            enabled=self._showResponsible
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

        if self._rh._getUser().isRBAdmin():
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
        if Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable():
            self._roomsBookingOpt.addItem(self._roomMapOpt)
        self._roomsBookingOpt.addItem(self._bookingListCalendarOpt)

        self._leftMenu.addSection(self._bookingsOpt)
        self._bookingsOpt.addItem(self._myBookingListOpt)
        self._bookingsOpt.addItem(self._myPendingBookingListOpt)
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
        if self._rh._getUser().isRBAdmin():
            self._leftMenu.addSection(self._adminSect)
            self._adminSect.addItem(self._adminOpt)
        return self._leftMenu

    def _isRoomBooking(self):
        return True
