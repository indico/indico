# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.legacy.webinterface.pages.admins import WPAdminsBase
from indico.legacy.webinterface.wcomponents import TabControl, WTabControl

from indico.util.i18n import _
from indico.web.flask.util import url_for


class WPRoomsBase(WPAdminsBase):
    sidemenu_option = 'rb'

    def _createTabCtrl(self):
        self._tabCtrl = TabControl()
        if session.user.is_admin:
            self._subTabRoomBooking = self._tabCtrl.newTab(
                'booking',
                _('Room Booking'),
                url_for('rooms_admin.settings')
            )

            self._subTabMain = self._subTabRoomBooking.newSubTab(
                'settings',
                _('Settings'),
                url_for('rooms_admin.settings')
            )
        else:
            self._subTabRoomBooking = self._tabCtrl.newTab(
                'booking',
                _('Room Booking'),
                url_for('rooms_admin.roomBooking-admin')
            )

        self._subTabConfig = self._subTabRoomBooking.newSubTab(
            'management',
            _('Management'),
            url_for('rooms_admin.roomBooking-admin')
        )

    def _getPageContent(self, params):
        return WTabControl(self._tabCtrl).getHTML(self._getTabContent(params))


class WPRoomBookingAdminBase(WPRoomsBase):
    def getJSFiles(self):
        return WPRoomsBase.getJSFiles(self) + self._includeJSPackage('Management')

    def _setActiveTab(self):
        self._subTabRoomBooking.setActive()
