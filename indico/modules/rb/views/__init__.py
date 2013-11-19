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
from MaKaC.webinterface.wcomponents import (
    BasicSideMenu,
    SideMenuItem,
    SideMenuSection
)

from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.locations import Location


class WPRoomBookingBase(WPMainBase):

    def _getTitle(self):
        return (super(WPRoomBookingBase, self)._getTitle() +
                " - " + _("Room Booking"))

    def getJSFiles(self):
        return (super(WPRoomBookingBase, self).getJSFiles(self) +
                self._includeJSPackage('Management'))

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

        self._leftMenu = BasicSideMenu(self._getAW().getUser() != None)

        self._showResponsible = False


        if minfo.getRoomBookingModuleActive():  # and CrossLocationDB.isConnected():
            self._showResponsible = ((self._getAW().getUser() != None)
                                     and (Room.isAvatarResponsibleForRooms(self._getAW().getUser())
                                     or self._getAW().getUser().isAdmin()
                                     or self._getAW().getUser().isRBAdmin()))

        self._roomsBookingOpt = SideMenuSection(currentPage=urlHandlers.UHRoomBookingBookRoom.getURL())

        self._bookRoomNewOpt = SideMenuItem(
            _("Book a Room"),
            urlHandlers.UHRoomBookingBookRoom.getURL(),
            enabled=True
        )

        self._roomMapOpt = SideMenuItem(
            _("Map of rooms"),
            urlHandlers.UHRoomBookingMapOfRooms.getURL(),
            enabled=True
        )

        self._bookingListCalendarOpt = SideMenuItem(
            _("Calendar"),
            urlHandlers.UHRoomBookingBookingList.getURL(today=True, allRooms=True),
            enabled=True
        )

        self._bookingsOpt = SideMenuSection(
            _("View My Bookings"),
            urlHandlers.UHRoomBookingSearch4Bookings.getURL()
        )

        self._bookARoomOpt = SideMenuItem(
            _("Book a Room (Old)"),
            urlHandlers.UHRoomBookingSearch4Rooms.getURL(forNewBooking=True),
            enabled=True
        )
        self._bookARoomOpt.setVisible(False)

        self._myBookingListOpt = SideMenuItem(
            _("My bookings"),
            urlHandlers.UHRoomBookingBookingList.getURL(onlyMy=True,autoCriteria=True),
            enabled=True
        )

        self._myPreBookingListOpt = SideMenuItem(
            _("My PRE-bookings"),
            urlHandlers.UHRoomBookingBookingList.getURL(onlyMy=True, onlyPrebookings=True, autoCriteria=True),
            enabled=True
        )

        self._usersBookings = SideMenuItem(
            _("Bookings in my rooms"),
            urlHandlers.UHRoomBookingBookingList.getURL(ofMyRooms=True, autoCriteria=True),
            enabled=self._showResponsible
        )

        self._usersPrebookings = SideMenuItem(
            _("PRE-bookings in my rooms"),
            urlHandlers.UHRoomBookingBookingList.getURL(ofMyRooms=True, onlyPrebookings=True, autoCriteria=True),
            enabled=self._showResponsible
        )

        self._bookingListSearchOpt = SideMenuItem(
            _("Search bookings"),
            urlHandlers.UHRoomBookingSearch4Bookings.getURL(),
            enabled=True
        )

        self._blockingsOpt = SideMenuSection(_("Room Blocking"))

        self._usersBlockings = SideMenuItem(
            _("Blockings for my rooms"),
            urlHandlers.UHRoomBookingBlockingsMyRooms.getURL(filterState='pending'),
            enabled=self._showResponsible
        )

        self._roomsOpt = SideMenuSection(
            _("View Rooms"),
            urlHandlers.UHRoomBookingSearch4Rooms.getURL()
        )

        self._roomSearchOpt = SideMenuItem(
            _("Search rooms"),
            urlHandlers.UHRoomBookingSearch4Rooms.getURL(),
            enabled=True
        )

        self._myRoomListOpt = SideMenuItem(
            _("My rooms"),
            urlHandlers.UHRoomBookingRoomList.getURL(onlyMy=True),
            enabled=self._showResponsible
        )

        if self._showResponsible:
            self._myBlockingListOpt = SideMenuItem(
                _("My blockings"),
                urlHandlers.UHRoomBookingBlockingList.getURL(onlyMine=True, onlyRecent=True),
                enabled=True
            )
        else:
            self._myBlockingListOpt = SideMenuItem(
                _("Blockings"),
                urlHandlers.UHRoomBookingBlockingList.getURL(onlyRecent=True),
                enabled=True
            )

        self._blockRooms = SideMenuItem(
            _("Block rooms"),
            urlHandlers.UHRoomBookingBlockingForm.getURL(),
            enabled=self._showResponsible
        )


        if self._rh._getUser().isRBAdmin():
            self._adminSect = SideMenuSection(
                _("Administration"),
                urlHandlers.UHRoomBookingAdmin.getURL()
            )

            self._adminOpt = SideMenuItem(
                _("Administration"),
                urlHandlers.UHRoomBookingAdmin.getURL()
            )

        self._leftMenu.addSection(self._roomsBookingOpt)
        self._roomsBookingOpt.addItem(self._bookRoomNewOpt)
        if Location.getDefaultLocation() and Location.getDefaultLocation().isMapAvailable():
            self._roomsBookingOpt.addItem(self._roomMapOpt)
        self._roomsBookingOpt.addItem(self._bookingListCalendarOpt)

        self._leftMenu.addSection(self._bookingsOpt)
        self._bookingsOpt.addItem(self._bookARoomOpt)
        self._bookingsOpt.addItem(self._myBookingListOpt)
        self._bookingsOpt.addItem(self._myPreBookingListOpt)
        self._bookingsOpt.addItem(self._usersBookings)
        self._bookingsOpt.addItem(self._usersPrebookings)
        self._bookingsOpt.addItem(self._bookingListSearchOpt)
        self._leftMenu.addSection(self._blockingsOpt)
        self._blockingsOpt.addItem(self._blockRooms)
        self._blockingsOpt.addItem(self._myBlockingListOpt)
        self._blockingsOpt.addItem(self._usersBlockings)
        self._leftMenu.addSection(self._roomsOpt)
        self._roomsOpt.addItem(self._roomSearchOpt)
        self._roomsOpt.addItem(self._myRoomListOpt)
        if self._rh._getUser().isRBAdmin():
            self._leftMenu.addSection(self._adminSect)
            self._adminSect.addItem(self._adminOpt)
        return self._leftMenu

    def _isRoomBooking(self):
        return True
