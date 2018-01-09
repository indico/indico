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

from indico.legacy.webinterface.wcomponents import WTemplated
from indico.modules.rb import Room, rb_settings
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservations import RepeatMapping
from indico.modules.rb.views import WPRoomBookingLegacyBase
from indico.modules.rb.views.calendar import RoomBookingCalendarWidget
from indico.util.caching import memoize_redis
from indico.util.i18n import _


class WPRoomBookingBookingDetails(WPRoomBookingLegacyBase):
    endpoints = {
        'room_details': 'rooms.roomBooking-roomDetails',
        'booking_details': 'rooms.roomBooking-bookingDetails',
        'booking_modify': 'rooms.roomBooking-modifyBookingForm',
        'booking_clone': 'rooms.roomBooking-cloneBooking',
        'booking_accept': 'rooms.roomBooking-acceptBooking',
        'booking_cancel': 'rooms.roomBooking-cancelBooking',
        'booking_reject': 'rooms.roomBooking-rejectBooking',
        'booking_occurrence_cancel': 'rooms.roomBooking-cancelBookingOccurrence',
        'booking_occurrence_reject': 'rooms.roomBooking-rejectBookingOccurrence'
    }

    def _getPageContent(self, params):
        reservation = params['reservation']
        params['endpoints'] = self.endpoints
        params['assistance_emails'] = rb_settings.get('assistance_emails')
        params['vc_equipment'] = ', '.join(eq.name for eq in reservation.get_vc_equipment())
        params['repetition'] = RepeatMapping.get_message(*reservation.repetition)
        params['edit_logs'] = reservation.edit_logs.order_by(ReservationEditLog.timestamp.desc()).all()
        params['excluded_days'] = reservation.find_excluded_days().all()
        return WTemplated('RoomBookingDetails').getHTML(params)


class WPRoomBookingCalendar(WPRoomBookingLegacyBase):
    sidemenu_option = 'calendar'

    def _getPageContent(self, params):
        params['calendar'] = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                                       rooms=params['rooms']).render()
        return WTemplated('RoomBookingCalendar').getHTML(params)


class WPRoomBookingSearchBookings(WPRoomBookingLegacyBase):
    sidemenu_option = 'search_bookings'

    def _getPageContent(self, params):
        return WTemplated('RoomBookingSearchBookings').getHTML(params)


class WPRoomBookingSearchBookingsResults(WPRoomBookingLegacyBase):
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
        self.sidemenu_option = menu_item
        WPRoomBookingLegacyBase.__init__(self, rh, **kwargs)

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

    def _getPageContent(self, params):
        params['summary'] = self._get_criteria_summary(params)
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             rooms=params['rooms'], show_blockings=params['show_blockings'])
        params['calendar'] = calendar.render(form_data=params['form_data'])
        return WTemplated('RoomBookingSearchBookingsResults').getHTML(params)


class WPRoomBookingNewBookingBase(WPRoomBookingLegacyBase):
    sidemenu_option = 'book_room'


@memoize_redis(3600)
def _get_serializable_rooms(room_ids):
    # all the rooms are already in sqlalchemy's identity cache so they won't be queried again
    return [Room.get(r).to_serializable('__public_exhaustive__') for r in room_ids]


class WPRoomBookingNewBookingSelectRoom(WPRoomBookingNewBookingBase):
    def _getPageContent(self, params):
        params['serializable_rooms'] = _get_serializable_rooms([r.id for r in params['rooms']])
        params['booking_limit'] = rb_settings.get('booking_limit')
        return WTemplated('RoomBookingNewBookingSelectRoom').getHTML(params)


class WPRoomBookingNewBookingSelectPeriod(WPRoomBookingNewBookingBase):
    def _getPageContent(self, params):
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             candidates=params['candidates'], rooms=params['rooms'],
                                             repeat_frequency=params['repeat_frequency'],
                                             repeat_interval=params['repeat_interval'],
                                             flexible_days=params['flexible_days'])
        params['calendar'] = calendar.render(show_summary=False, can_navigate=False, details_in_new_tab=True)
        return WTemplated('RoomBookingNewBookingSelectPeriod').getHTML(params)


class WPRoomBookingNewBookingConfirm(WPRoomBookingNewBookingBase):
    endpoints = {
        'room_details': 'rooms.roomBooking-roomDetails'
    }

    def _getPageContent(self, params):
        params['endpoints'] = self.endpoints
        return WTemplated('RoomBookingNewBookingConfirm').getHTML(params)


class WPRoomBookingNewBookingSimple(WPRoomBookingNewBookingBase):
    endpoints = {
        'room_details': 'rooms.roomBooking-roomDetails'
    }

    def _getPageContent(self, params):
        params['endpoints'] = self.endpoints
        if params['start_dt'] and params['end_dt']:
            calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                                 candidates=params['candidates'],
                                                 specific_room=params['room'],
                                                 repeat_frequency=params['repeat_frequency'],
                                                 repeat_interval=params['repeat_interval'])
            params['calendar'] = calendar.render(show_navbar=False, details_in_new_tab=True)
        else:
            params['calendar'] = ''
        params['serializable_room'] = Room.get(params['room'].id).to_serializable('__public_exhaustive__')
        params['booking_limit'] = rb_settings.get('booking_limit')
        return WTemplated('RoomBookingBookingForm').getHTML(params)


class WPRoomBookingModifyBooking(WPRoomBookingLegacyBase):
    endpoints = {
        'room_details': 'rooms.roomBooking-roomDetails'
    }

    def _getPageContent(self, params):
        params['endpoints'] = self.endpoints
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             candidates=params['candidates'], specific_room=params['room'],
                                             repeat_frequency=params['repeat_frequency'],
                                             repeat_interval=params['repeat_interval'])
        params['calendar'] = calendar.render(show_navbar=False, details_in_new_tab=True)
        params['serializable_room'] = Room.get(params['room'].id).to_serializable('__public_exhaustive__')
        params['booking_limit'] = rb_settings.get('booking_limit')
        return WTemplated('RoomBookingBookingForm').getHTML(params)
