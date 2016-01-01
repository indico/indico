# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import request, flash

from indico.core.errors import NoReportError
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.user.reservations import (RHRoomBookingBookingDetails, RHRoomBookingModifyBooking,
                                                             RHRoomBookingCloneBooking, RHRoomBookingNewBookingSimple,
                                                             RHRoomBookingNewBooking, RHRoomBookingCancelBooking,
                                                             RHRoomBookingRejectBooking, RHRoomBookingAcceptBooking,
                                                             RHRoomBookingCancelBookingOccurrence,
                                                             RHRoomBookingRejectBookingOccurrence)
from indico.modules.rb.controllers.user.rooms import RHRoomBookingRoomDetails
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.views.user.event import (WPRoomBookingEventRoomDetails, WPRoomBookingEventBookingList,
                                                WPRoomBookingEventBookingDetails, WPRoomBookingEventModifyBooking,
                                                WPRoomBookingEventNewBookingSimple, WPRoomBookingEventChooseEvent,
                                                WPRoomBookingEventNewBookingSelectRoom,
                                                WPRoomBookingEventNewBookingSelectPeriod,
                                                WPRoomBookingEventNewBookingConfirm)
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.conference import CustomRoom, CustomLocation, Session
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _get_defaults_from_object(obj):
    defaults = {'start_dt': obj.getAdjustedStartDate().replace(tzinfo=None),
                'end_dt': obj.getAdjustedEndDate().replace(tzinfo=None),
                'booking_reason': "{} '{}'".format(obj.getVerboseType(), obj.getTitle())}
    if defaults['end_dt'].date() != defaults['start_dt'].date():
        defaults['repeat_frequency'] = RepeatFrequency.DAY
        defaults['repeat_interval'] = 1
    if obj.getLocation() and obj.getRoom():
        room = Room.find_first(Room.name == obj.getRoom().getName(), Location.name == obj.getLocation().getName(),
                               _join=Room.location)
        if room:
            defaults['room_ids'] = [room.id]
    return defaults


def _assign_room(obj, room, flash_message=True):
    if flash_message:
        flash(_(u"Room of {0} '{1}' set to '{2}'").format(obj.getVerboseType().lower(), obj.getTitle().decode('utf-8'),
                                                          room.full_name), 'info')
    if isinstance(obj, Session):
        for slot in obj.getSlotList():
            _assign_room(slot, room, False)
        return
    custom_location = CustomLocation()
    custom_location.setName(room.location_name)
    custom_room = CustomRoom()
    custom_room.setName(room.name)
    custom_room.setFullName(room.full_name)
    obj.setRoom(custom_room)
    obj.setLocation(custom_location)


class RHRoomBookingEventBase(RHConferenceModifBase, RHRoomBookingBase):
    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        RHRoomBookingBase._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf
        self.event_id = int(self.event.getId())


class RHRoomBookingEventBookingList(RHRoomBookingEventBase):
    def _process(self):
        reservations = self.event_new.reservations.all()
        if not reservations:
            self._redirect(url_for('event_mgmt.rooms_choose_event', self.event))
            return
        return WPRoomBookingEventBookingList(self, self.event, reservations=reservations).display()


class RHRoomBookingEventChooseEvent(RHRoomBookingEventBase):
    def _process(self):
        return WPRoomBookingEventChooseEvent(self, self.event).display()


class RHRoomBookingEventRoomDetails(RHRoomBookingEventBase, RHRoomBookingRoomDetails):
    def __init__(self):
        RHRoomBookingRoomDetails.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingRoomDetails._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventRoomDetails(self, self.event, **kwargs)

    def _process(self):
        return RHRoomBookingRoomDetails._process(self)


class RHRoomBookingEventBookingDetails(RHRoomBookingEventBase, RHRoomBookingBookingDetails):
    def __init__(self):
        RHRoomBookingBookingDetails.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingBookingDetails._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventBookingDetails(self, self.event, **kwargs)

    def _process(self):
        return RHRoomBookingBookingDetails._process(self)


class RHRoomBookingEventBookingModifyBooking(RHRoomBookingEventBase, RHRoomBookingModifyBooking):
    def __init__(self):
        RHRoomBookingModifyBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingModifyBooking._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventModifyBooking(self, self.event, **kwargs)

    def _get_success_url(self):
        return url_for('event_mgmt.rooms_booking_details', self.event, self._reservation)

    def _process(self):
        return RHRoomBookingModifyBooking._process(self)


class RHRoomBookingEventBookingCloneBooking(RHRoomBookingEventBase, RHRoomBookingCloneBooking):
    def __init__(self):
        RHRoomBookingCloneBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingCloneBooking._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventNewBookingSimple(self, self.event, cloning=True, **kwargs)

    def _get_success_url(self, booking):
        return url_for('event_mgmt.rooms_booking_details', self.event, booking)

    def _create_booking(self, form, room):
        booking = RHRoomBookingCloneBooking._create_booking(self, form, room)
        booking.event_id = self.event_id
        return booking

    def _process(self):
        return RHRoomBookingCloneBooking._process(self)


class _SuccessUrlDetailsMixin:
    def _get_success_url(self):
        return url_for('event_mgmt.rooms_booking_details', self.event, self._reservation)


class RHRoomBookingEventAcceptBooking(_SuccessUrlDetailsMixin, RHRoomBookingEventBase, RHRoomBookingAcceptBooking):
    def __init__(self):
        RHRoomBookingAcceptBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingAcceptBooking._checkParams(self)

    def _process(self):
        return RHRoomBookingAcceptBooking._process(self)


class RHRoomBookingEventCancelBooking(_SuccessUrlDetailsMixin, RHRoomBookingEventBase, RHRoomBookingCancelBooking):
    def __init__(self):
        RHRoomBookingCancelBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingCancelBooking._checkParams(self)

    def _process(self):
        return RHRoomBookingCancelBooking._process(self)


class RHRoomBookingEventRejectBooking(_SuccessUrlDetailsMixin, RHRoomBookingEventBase, RHRoomBookingRejectBooking):
    def __init__(self):
        RHRoomBookingRejectBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingRejectBooking._checkParams(self)

    def _process(self):
        return RHRoomBookingRejectBooking._process(self)


class RHRoomBookingEventCancelBookingOccurrence(_SuccessUrlDetailsMixin, RHRoomBookingEventBase,
                                                RHRoomBookingCancelBookingOccurrence):
    def __init__(self):
        RHRoomBookingCancelBookingOccurrence.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingCancelBookingOccurrence._checkParams(self)

    def _process(self):
        return RHRoomBookingCancelBookingOccurrence._process(self)


class RHRoomBookingEventRejectBookingOccurrence(_SuccessUrlDetailsMixin, RHRoomBookingEventBase,
                                                RHRoomBookingRejectBookingOccurrence):
    def __init__(self):
        RHRoomBookingRejectBookingOccurrence.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingRejectBookingOccurrence._checkParams(self)

    def _process(self):
        return RHRoomBookingRejectBookingOccurrence._process(self)


class RHRoomBookingEventNewBookingSimple(RHRoomBookingEventBase, RHRoomBookingNewBookingSimple):
    def __init__(self):
        RHRoomBookingNewBookingSimple.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingNewBookingSimple._checkParams(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventNewBookingSimple(self, self.event, **kwargs)

    def _make_confirm_form(self, *args, **kwargs):
        defaults = kwargs['defaults']
        for key, value in _get_defaults_from_object(self.event).iteritems():
            defaults[key] = value
        return RHRoomBookingNewBookingSimple._make_confirm_form(self, *args, **kwargs)

    def _get_success_url(self, booking):
        return url_for('event_mgmt.rooms_booking_details', self.event, booking)

    def _create_booking(self, form, room):
        booking = RHRoomBookingNewBookingSimple._create_booking(self, form, room)
        booking.event_id = self.event_id
        return booking

    def _process(self):
        return RHRoomBookingNewBookingSimple._process(self)


class RHRoomBookingEventNewBooking(RHRoomBookingEventBase, RHRoomBookingNewBooking):
    def __init__(self):
        RHRoomBookingNewBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _checkParams(self, params):
        RHRoomBookingEventBase._checkParams(self, params)
        RHRoomBookingNewBooking._checkParams(self)
        assign = request.args.get('assign')
        if not assign or assign == 'nothing':
            self._assign_to = None
        elif assign == 'event':
            self._assign_to = self.event
        else:
            element, _, element_id = assign.partition('-')
            if element == 'session':
                self._assign_to = self.event.getSessionById(element_id)
            elif element == 'contribution':
                self._assign_to = self.event.getContributionById(element_id)
            else:
                raise NoReportError('Invalid assignment')
            if not self._assign_to:
                raise NoReportError('Invalid assignment')

    def _get_view(self, view, **kwargs):
        if view == 'select_room':
            kwargs['ignore_userdata'] = True
        views = {'select_room': WPRoomBookingEventNewBookingSelectRoom,
                 'select_period': WPRoomBookingEventNewBookingSelectPeriod,
                 'confirm': WPRoomBookingEventNewBookingConfirm}
        return views[view](self, self.event, **kwargs)

    def _get_select_room_form_defaults(self):
        defaults, _ = RHRoomBookingNewBooking._get_select_room_form_defaults(self)
        for key, value in _get_defaults_from_object(self._assign_to or self.event).iteritems():
            defaults[key] = value
        return defaults, False

    def _make_confirm_form(self, *args, **kwargs):
        if 'defaults' in kwargs:
            obj = self._assign_to or self.event
            kwargs['defaults'].booking_reason = _get_defaults_from_object(obj)['booking_reason']
        return RHRoomBookingNewBooking._make_confirm_form(self, *args, **kwargs)

    def _get_success_url(self, booking):
        return url_for('event_mgmt.rooms_booking_details', self.event, booking)

    def _create_booking(self, form, room):
        booking = RHRoomBookingNewBooking._create_booking(self, form, room)
        booking.event_id = self.event_id
        if self._assign_to:
            _assign_room(self._assign_to, room)

        return booking

    def _process(self):
        return RHRoomBookingNewBooking._process(self)
