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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask import session

from indico.modules.rb.controllers.utils import getRoomBookingOption
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservations import RepeatMapping
from indico.modules.rb.views import WPRoomBookingBase
from indico.modules.rb.views.calendar import RoomBookingCalendarWidget
from indico.util.i18n import _
from MaKaC.common import Config
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.wcomponents import WTemplated


class WPRoomBookingBookingDetails(WPRoomBookingBase):

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingDetails(self._rh).getHTML(params)


class WRoomBookingDetails(WTemplated):

    def __init__(self, rh, conference=None):
        self._rh = rh
        self._reservation = rh._reservation
        self._conf = conference
        self._standalone = conference is None

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['standalone'] = self._standalone
        wvars['reservation'] = self._reservation
        #wvars['collisions'] = self._rh._collisions
        wvars['config'] = Config.getInstance()
        # wvars['actionSucceeded'] = self._rh._afterActionSucceeded
        # if self._rh._afterActionSucceeded:
        #     wvars['title'] = self._rh._title
        #     wvars['description'] = self._rh._description

        if self._standalone:
            wvars['roomDetailsUH'] = UH.UHRoomBookingRoomDetails
            wvars['modifyBookingUH'] = UH.UHRoomBookingModifyBookingForm
            wvars['cloneURL'] = UH.UHRoomBookingCloneBooking.getURL(self._reservation)
        else:
            wvars['roomDetailsUH'] = UH.UHConfModifRoomBookingRoomDetails
            wvars['modifyBookingUH'] = UH.UHConfModifRoomBookingModifyBookingForm
            wvars['cloneURL'] = UH.UHConfModifRoomBookingCloneBooking.getURL(self._reservation)

        wvars['isPreBooking'] = not self._reservation.is_confirmed
        wvars['bookMessage'] = _('PRE-Booking') if wvars['isPreBooking'] else _('Booking')

        wvars['can_be_rejected'] = self._reservation.can_be_rejected(session.user)
        wvars['can_be_cancelled'] = self._reservation.can_be_cancelled(session.user)
        wvars['repetition'] = RepeatMapping.getMessage(self._reservation.repeat_unit, self._reservation.repeat_step)
        wvars['vc_equipment'] = ', '.join(eq.name for eq in self._reservation.get_vc_equipment())
        wvars['assistence_emails'] = getRoomBookingOption('assistanceNotificationEmails')
        wvars['edit_logs'] = self._reservation.edit_logs.order_by(ReservationEditLog.timestamp.desc()).all()
        wvars['excluded_days'] = self._reservation.find_excluded_days().all()
        return wvars


class WPRoomBookingCalendar(WPRoomBookingBase):
    def _setCurrentMenuItem(self):
        self._bookingListCalendarOpt.setActive(True)

    def _getBody(self, params):
        params['calendar'] = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                                       rooms=params['rooms']).render()
        return WTemplated('RoomBookingCalendar').getHTML(params)


class WPRoomBookingSearchBookings(WPRoomBookingBase):
    def _setCurrentMenuItem(self):
        self._bookingListSearchOpt.setActive(True)

    def _getBody(self, params):
        return WTemplated('RoomBookingSearchBookings').getHTML(params)


class WPRoomBookingSearchBookingsResults(WPRoomBookingBase):
    mapping = {
    #    x - only for my rooms
    #    |  x - only pending bookings
    #    |  |  x - only confirmed bookings
    #    |  |  |  x - only created by myself
    #    |  |  |  |
        (0, 0, 0, 0): _('Bookings'),
        (0, 1, 0, 0): _('Pending bookings'),
        (0, 0, 1, 0): _('Confirmed bookings'),
        (0, 0, 0, 1): _('My bookings'),
        (0, 1, 0, 1): _('My pending bookings'),
        (0, 0, 1, 1): _('My confirmed bookings'),
        (1, 0, 0, 0): _('Bookings for my rooms'),
        (1, 1, 0, 0): _('Pending bookings for my rooms'),
        (1, 0, 1, 0): _('Confirmed bookings for my rooms'),
        (1, 0, 0, 1): _('My bookings for my rooms'),
        (1, 1, 0, 1): _('My pending bookings for my rooms'),
        (1, 0, 1, 1): _('My confirmed bookings for my rooms'),
    }

    def __init__(self, rh, menu_item, **kwargs):
        self._menu_item = menu_item
        WPRoomBookingBase.__init__(self, rh, **kwargs)

    def _setCurrentMenuItem(self):
        getattr(self, '_{}Opt'.format(self._menu_item)).setActive(True)

    def _get_criteria_summary(self, params):
        form = params['form']
        only_my_rooms = form.is_only_my_rooms.data
        only_pending_bookings = form.is_only_pending_bookings.data
        only_confirmed_bookings = form.is_only_confirmed_bookings.data
        only_my_bookings = form.is_only_mine.data
        if only_pending_bookings and only_confirmed_bookings:
            # Both selected = show all
            only_pending_bookings = only_confirmed_bookings = False

        return self.mapping.get((only_my_rooms, only_pending_bookings, only_confirmed_bookings, only_my_bookings),
                                _('{} occurrences found').format(len(params['occurrences'])))

    def _getBody(self, params):
        params['summary'] = self._get_criteria_summary(params)
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             rooms=params['rooms'], show_blockings=params['show_blockings'])
        params['calendar'] = calendar.render(form_data=params['form_data'])
        return WTemplated('RoomBookingSearchBookingsResults').getHTML(params)


class WPRoomBookingNewBookingBase(WPRoomBookingBase):
    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)


class WPRoomBookingNewBookingSelectRoom(WPRoomBookingNewBookingBase):
    def _getBody(self, params):
        return WTemplated('RoomBookingNewBookingSelectRoom').getHTML(params)


class WPRoomBookingNewBookingSelectPeriod(WPRoomBookingNewBookingBase):
    def _getBody(self, params):
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             candidates=params['candidates'], rooms=params['rooms'],
                                             repeat_unit=params['repeat_unit'], repeat_step=params['repeat_step'],
                                             flexible_days=params['flexible_days'])
        params['calendar'] = calendar.render(show_summary=False, can_navigate=False)
        return WTemplated('RoomBookingNewBookingSelectPeriod').getHTML(params)


class WPRoomBookingNewBookingConfirm(WPRoomBookingNewBookingBase):
    def _getBody(self, params):
        return WTemplated('RoomBookingNewBookingConfirm').getHTML(params)


class WPRoomBookingNewBookingSimple(WPRoomBookingNewBookingBase):
    def _getBody(self, params):
        if params['start_dt'] and params['end_dt']:
            calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                                 candidates=params['candidates'],
                                                 specific_room=params['room'], repeat_unit=params['repeat_unit'],
                                                 repeat_step=params['repeat_step'])
            params['calendar'] = calendar.render(show_navbar=False)
        else:
            params['calendar'] = ''
        return WTemplated('RoomBookingBookingForm').getHTML(params)


class WPRoomBookingModifyBooking(WPRoomBookingBase):
    def _getBody(self, params):
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             candidates=params['candidates'], specific_room=params['room'],
                                             repeat_unit=params['repeat_unit'], repeat_step=params['repeat_step'])
        params['calendar'] = calendar.render(show_navbar=False)
        return WTemplated('RoomBookingBookingForm').getHTML(params)


class WPRoomBookingStatement(WPRoomBookingBase):
    def _getBody(self, params):
        return WRoomBookingStatement(self._rh).getHTML(params)


class WRoomBookingStatement(WTemplated):
    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['title'] = self._rh._title
        wvars['description'] = self._rh._description
        return wvars
