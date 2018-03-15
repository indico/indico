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

from indico.legacy.webinterface.wcomponents import TabControl, WTabControl, WTemplated
from indico.modules.events.management.views import WPEventManagementLegacy
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.views.user.reservations import (WPRoomBookingBookingDetails, WPRoomBookingModifyBooking,
                                                       WPRoomBookingNewBookingConfirm,
                                                       WPRoomBookingNewBookingSelectPeriod,
                                                       WPRoomBookingNewBookingSelectRoom, WPRoomBookingNewBookingSimple)
from indico.modules.rb.views.user.rooms import WPRoomBookingRoomDetails
from indico.web.flask.util import url_for


class WPRoomBookingEventBase(WPEventManagementLegacy):
    sidemenu_option = 'room_booking'
    bundles = ('module_rb.js',)

    def _createTabCtrl(self):
        self._tabCtrl = TabControl()
        self._tabExistBookings = self._tabCtrl.newTab('existing', 'Existing Bookings',
                                                      url_for('event_mgmt.rooms_booking_list', self.event))
        self._tabNewBooking = self._tabCtrl.newTab('new', 'New Booking',
                                                   url_for('event_mgmt.rooms_choose_event', self.event))
        if not Reservation.query.with_parent(self.event).has_rows():
            self._tabExistBookings.setEnabled(False)
        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()
        params['event'] = self.event
        return WTabControl(self._tabCtrl).getHTML(self._getTabContent(params))

    def _getTabContent(self, params):
        raise NotImplementedError


class WPRoomBookingEventRoomDetails(WPRoomBookingEventBase, WPRoomBookingRoomDetails):
    endpoints = {
        'room_book': 'event_mgmt.rooms_room_book'
    }

    def _setActiveTab(self):
        self._tabNewBooking.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingRoomDetails._getPageContent(self, params)


class WPRoomBookingEventBookingList(WPRoomBookingEventBase):
    def _setActiveTab(self):
        self._tabExistBookings.setActive()

    def _getTabContent(self, params):
        return WTemplated('RoomBookingEventBookingList').getHTML(params)


class WPRoomBookingEventChooseEvent(WPRoomBookingEventBase):
    def _setActiveTab(self):
        self._tabNewBooking.setActive()

    def _getTabContent(self, params):
        return WTemplated('RoomBookingEventChooseEvent').getHTML(params)


class WPRoomBookingEventBookingDetails(WPRoomBookingEventBase, WPRoomBookingBookingDetails):
    endpoints = {
        'room_details': 'event_mgmt.rooms_room_details',
        'booking_modify': 'event_mgmt.rooms_booking_modify',
        'booking_clone': 'event_mgmt.rooms_booking_clone',
        'booking_accept': 'event_mgmt.rooms_booking_accept',
        'booking_cancel': 'event_mgmt.rooms_booking_cancel',
        'booking_reject': 'event_mgmt.rooms_booking_reject',
        'booking_occurrence_cancel': 'event_mgmt.rooms_booking_occurrence_cancel',
        'booking_occurrence_reject': 'event_mgmt.rooms_booking_occurrence_reject'
    }

    def _setActiveTab(self):
        self._tabExistBookings.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingBookingDetails._getPageContent(self, params)


class WPRoomBookingEventModifyBooking(WPRoomBookingEventBase, WPRoomBookingModifyBooking):
    endpoints = {
        'room_details': 'event_mgmt.rooms_room_details'
    }

    def _setActiveTab(self):
        self._tabExistBookings.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingModifyBooking._getPageContent(self, params)


class WPRoomBookingEventNewBookingSimple(WPRoomBookingEventBase, WPRoomBookingNewBookingSimple):
    endpoints = {
        'room_details': 'event_mgmt.rooms_room_details'
    }

    def _setActiveTab(self):
        self._tabNewBooking.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingNewBookingSimple._getPageContent(self, params)


class WPRoomBookingEventNewBookingSelectRoom(WPRoomBookingEventBase, WPRoomBookingNewBookingSelectRoom):
    def _setActiveTab(self):
        self._tabNewBooking.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingNewBookingSelectRoom._getPageContent(self, params)


class WPRoomBookingEventNewBookingSelectPeriod(WPRoomBookingEventBase, WPRoomBookingNewBookingSelectPeriod):
    def _setActiveTab(self):
        self._tabNewBooking.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingNewBookingSelectPeriod._getPageContent(self, params)


class WPRoomBookingEventNewBookingConfirm(WPRoomBookingEventBase, WPRoomBookingNewBookingConfirm):
    def _setActiveTab(self):
        self._tabNewBooking.setActive()

    def _getTabContent(self, params):
        return WPRoomBookingNewBookingConfirm._getPageContent(self, params)
