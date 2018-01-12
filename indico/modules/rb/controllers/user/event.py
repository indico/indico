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

from __future__ import unicode_literals

from operator import attrgetter

from flask import flash, redirect, request

from indico.core.db import db
from indico.core.errors import NoReportError
from indico.modules.events.contributions import Contribution
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.user.reservations import (RHRoomBookingAcceptBooking, RHRoomBookingBookingDetails,
                                                             RHRoomBookingCancelBooking,
                                                             RHRoomBookingCancelBookingOccurrence,
                                                             RHRoomBookingCloneBooking, RHRoomBookingModifyBooking,
                                                             RHRoomBookingNewBooking, RHRoomBookingNewBookingSimple,
                                                             RHRoomBookingRejectBooking,
                                                             RHRoomBookingRejectBookingOccurrence)
from indico.modules.rb.controllers.user.rooms import RHRoomBookingRoomDetails
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.views.user.event import (WPRoomBookingEventBookingDetails, WPRoomBookingEventBookingList,
                                                WPRoomBookingEventChooseEvent, WPRoomBookingEventModifyBooking,
                                                WPRoomBookingEventNewBookingConfirm,
                                                WPRoomBookingEventNewBookingSelectPeriod,
                                                WPRoomBookingEventNewBookingSelectRoom,
                                                WPRoomBookingEventNewBookingSimple, WPRoomBookingEventRoomDetails)
from indico.util.i18n import _
from indico.web.flask.util import url_for


def _get_object_type(obj):
    if isinstance(obj, db.m.Event):
        return u'Event'
    elif isinstance(obj, db.m.Session):
        return u'Session'
    elif isinstance(obj, db.m.Contribution):
        return u'Contribution'
    else:
        raise TypeError('Invalid type: {}'.format(type(obj)))


def _get_defaults_from_object(obj):
    defaults = {'start_dt': obj.start_dt.astimezone(obj.event.tzinfo).replace(tzinfo=None),
                'end_dt': obj.end_dt.astimezone(obj.event.tzinfo).replace(tzinfo=None),
                'booking_reason': u"{} '{}'".format(_get_object_type(obj), obj.title)}
    if defaults['end_dt'].date() != defaults['start_dt'].date():
        defaults['repeat_frequency'] = RepeatFrequency.DAY
        defaults['repeat_interval'] = 1
    if obj.room:
        defaults['room_ids'] = [obj.room.id]
    return defaults


def _assign_room(obj, room, flash_message=True):
    if flash_message:
        flash(_(u"Room of {0} '{1}' set to '{2}'").format(_get_object_type(obj).lower(), obj.title, room.full_name),
              'info')
    obj.inherit_location = False
    obj.room = room


class RHRoomBookingEventBase(RHManageEventBase, RHRoomBookingBase):
    def _check_access(self):
        RHManageEventBase._check_access(self)
        RHRoomBookingBase._check_access(self)


class RHRoomBookingEventBookingList(RHRoomBookingEventBase):
    def _process(self):
        reservations = self.event.reservations.all()
        if not reservations:
            return redirect(url_for('event_mgmt.rooms_choose_event', self.event))
        return WPRoomBookingEventBookingList(self, self.event, reservations=reservations).display()


class RHRoomBookingEventChooseEvent(RHRoomBookingEventBase):
    def _process(self):
        contribs = (Contribution.query
                    .with_parent(self.event)
                    .join(TimetableEntry)  # implies is_scheduled
                    .order_by(TimetableEntry.start_dt)
                    .all())
        sessions = sorted([s for s in self.event.sessions if s.start_dt is not None], key=attrgetter('start_dt'))
        return WPRoomBookingEventChooseEvent(self, self.event).display(contribs=contribs, sessions=sessions)


class RHRoomBookingEventRoomDetails(RHRoomBookingEventBase, RHRoomBookingRoomDetails):
    def __init__(self):
        RHRoomBookingRoomDetails.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingRoomDetails._process_args(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventRoomDetails(self, self.event, **kwargs)

    def _process(self):
        return RHRoomBookingRoomDetails._process(self)


class RHRoomBookingEventBookingDetails(RHRoomBookingEventBase, RHRoomBookingBookingDetails):
    def __init__(self):
        RHRoomBookingBookingDetails.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingBookingDetails._process_args(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventBookingDetails(self, self.event, **kwargs)

    def _process(self):
        return RHRoomBookingBookingDetails._process(self)


class RHRoomBookingEventBookingModifyBooking(RHRoomBookingEventBase, RHRoomBookingModifyBooking):
    def __init__(self):
        RHRoomBookingModifyBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingModifyBooking._process_args(self)

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

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingCloneBooking._process_args(self)

    def _get_view(self, **kwargs):
        return WPRoomBookingEventNewBookingSimple(self, self.event, cloning=True, **kwargs)

    def _get_success_url(self, booking):
        return url_for('event_mgmt.rooms_booking_details', self.event, booking)

    def _create_booking(self, form, room):
        booking = RHRoomBookingCloneBooking._create_booking(self, form, room)
        booking.event = self.event
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

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingAcceptBooking._process_args(self)

    def _process(self):
        return RHRoomBookingAcceptBooking._process(self)


class RHRoomBookingEventCancelBooking(_SuccessUrlDetailsMixin, RHRoomBookingEventBase, RHRoomBookingCancelBooking):
    def __init__(self):
        RHRoomBookingCancelBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingCancelBooking._process_args(self)

    def _process(self):
        return RHRoomBookingCancelBooking._process(self)


class RHRoomBookingEventRejectBooking(_SuccessUrlDetailsMixin, RHRoomBookingEventBase, RHRoomBookingRejectBooking):
    def __init__(self):
        RHRoomBookingRejectBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingRejectBooking._process_args(self)

    def _process(self):
        return RHRoomBookingRejectBooking._process(self)


class RHRoomBookingEventCancelBookingOccurrence(_SuccessUrlDetailsMixin, RHRoomBookingEventBase,
                                                RHRoomBookingCancelBookingOccurrence):
    def __init__(self):
        RHRoomBookingCancelBookingOccurrence.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingCancelBookingOccurrence._process_args(self)

    def _process(self):
        return RHRoomBookingCancelBookingOccurrence._process(self)


class RHRoomBookingEventRejectBookingOccurrence(_SuccessUrlDetailsMixin, RHRoomBookingEventBase,
                                                RHRoomBookingRejectBookingOccurrence):
    def __init__(self):
        RHRoomBookingRejectBookingOccurrence.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingRejectBookingOccurrence._process_args(self)

    def _process(self):
        return RHRoomBookingRejectBookingOccurrence._process(self)


class RHRoomBookingEventNewBookingSimple(RHRoomBookingEventBase, RHRoomBookingNewBookingSimple):
    def __init__(self):
        RHRoomBookingNewBookingSimple.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingNewBookingSimple._process_args(self)

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
        booking.event = self.event
        return booking

    def _process(self):
        return RHRoomBookingNewBookingSimple._process(self)


class RHRoomBookingEventNewBooking(RHRoomBookingEventBase, RHRoomBookingNewBooking):
    def __init__(self):
        RHRoomBookingNewBooking.__init__(self)
        RHRoomBookingEventBase.__init__(self)

    def _process_args(self):
        RHRoomBookingEventBase._process_args(self)
        RHRoomBookingNewBooking._process_args(self)
        assign = request.args.get('assign')
        if not assign or assign == 'nothing':
            self._assign_to = None
        elif assign == 'event':
            self._assign_to = self.event
        else:
            element, _, element_id = assign.partition('-')
            if element == 'session':
                self._assign_to = self.event.get_session(element_id)
            elif element == 'contribution':
                self._assign_to = self.event.get_contribution(element_id)
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
        booking.event = self.event
        if self._assign_to:
            _assign_room(self._assign_to, room)

        return booking

    def _process(self):
        return RHRoomBookingNewBooking._process(self)
