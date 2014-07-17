# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

import os

from indico.modules.rb.views.user.reservations import WPRoomBookingBookingDetails
from indico.web.flask.util import url_for
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.webinterface.wcomponents import TabControl, WTabControl, WTemplated


class WPRoomBookingEventBase(WPConferenceModifBase):
    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + self._asset_env['roombooking_sass'].urls()

    def _getHeadContent(self):
        return """
        <!-- Our libs -->
        <script type="text/javascript" src="%s/js/indico/Legacy/validation.js?%d"></script>

        """ % (self._getBaseURL(), os.stat(__file__).st_mtime)

    def _setActiveSideMenuItem(self):
        self._roomBookingMenuItem.setActive()

    def _createTabCtrl(self):
        self._tabCtrl = TabControl()
        self._tabExistBookings = self._tabCtrl.newTab('existing', 'Existing Bookings',
                                                      url_for('event_mgmt.rooms_booking_list', self._conf))
        self._tabNewBooking = self._tabCtrl.newTab('new', 'New Booking',
                                                   urlHandlers.UHConfModifRoomBookingChooseEvent.getURL(self._conf))
        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()
        params['event'] = self._conf
        return WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))

    def _getTabContent(self, params):
        raise NotImplementedError


class WPRoomBookingEventBookingList(WPRoomBookingEventBase):
    def _setActiveTab(self):
        self._tabExistBookings.setActive()

    def _getTabContent(self, params):
        return WTemplated('RoomBookingEventBookingList').getHTML(params)


class WPRoomBookingEventBookingDetails(WPRoomBookingEventBase, WPRoomBookingBookingDetails):
    def _setActiveTab(self):
        self._tabExistBookings.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingBookingDetails._getBody(self, params)
