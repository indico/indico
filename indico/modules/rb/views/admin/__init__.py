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
from MaKaC.webinterface.pages.admins import WPAdminsBase
from MaKaC.webinterface.wcomponents import TabControl, WSimpleNavigationDrawer, WTabControl

from indico.util.i18n import _


class WPRoomsBase(WPAdminsBase):
    def _setActiveSideMenuItem(self):
        self._roomsMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = TabControl()

        if session.user.isAdmin():
            self._subTabRoomBooking = self._tabCtrl.newTab(
                'booking',
                _('Room Booking'),
                urlHandlers.UHRoomBookingPluginAdmin.getURL()
            )

            self._subTabMain = self._subTabRoomBooking.newSubTab(
                'settings',
                _('Settings'),
                urlHandlers.UHRoomBookingPluginAdmin.getURL()
            )
        else:
            self._subTabRoomBooking = self._tabCtrl.newTab(
                'booking',
                _('Room Booking'),
                urlHandlers.UHRoomBookingAdmin.getURL()
            )

        self._subTabConfig = self._subTabRoomBooking.newSubTab(
            'management',
            _('Management'),
            urlHandlers.UHRoomBookingAdmin.getURL()
        )
        self._subTabRoomMappers = self._tabCtrl.newTab(
            'mappers',
            _('Room Mappers'),
            urlHandlers.UHRoomMappers.getURL()
        )

    def _getNavigationDrawer(self):
        if self._rh._getUser().isAdmin():
            return WSimpleNavigationDrawer(
                _('Room Booking Admin'),
                urlHandlers.UHRoomBookingPluginAdmin.getURL,
                bgColor='white'
            )

        return WSimpleNavigationDrawer(_('Room Booking Admin'),
                                       urlHandlers.UHRoomBookingAdmin.getURL,
                                       bgColor="white")

    def _getPageContent(self, params):
        return WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))


class WPRoomBookingPluginAdminBase(WPRoomsBase):
    def getJSFiles(self):
        return WPRoomsBase.getJSFiles(self) + self._includeJSPackage('Management')

    def _setActiveTab(self):
        self._subTabRoomBooking.setActive()

    def _getSiteArea(self):
        return 'Room Booking Administration'
