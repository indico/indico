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

from collections import defaultdict
from datetime import datetime, timedelta, time
from operator import attrgetter

from itertools import groupby
from flask import session

from MaKaC.common import Config
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.wcomponents import WTemplated
from indico.modules.rb.controllers.utils import getRoomBookingOption
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatMapping
from indico.util.i18n import _
from indico.util.date_time import iterdays
from indico.util.string import natural_sort_key
from indico.util.struct.iterables import group_list
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.views import WPRoomBookingBase
from indico.modules.rb.views.utils import Bar


class RoomBookingCalendarWidget(object):
    def __init__(self, occurrences, start_dt, end_dt, candidates=None, rooms=None, specific_room=None,
                 repeat_unit=None, repeat_step=None, flexible_days=None):
        self.occurrences = occurrences
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.candidates = candidates
        self.rooms = rooms
        self.specific_room = specific_room
        self.repeat_unit = repeat_unit
        self.repeat_step = repeat_step
        self.flexible_days = flexible_days

        self.conflicts = 0
        self.bars = []

        if self.specific_room and self.rooms:
            raise ValueError('specific_room and rooms are mutually exclusive')

        if self.specific_room:
            self.rooms = [self.specific_room]
        elif self.rooms is None:
            self.rooms = Room.find_all(is_active=True)
        self.rooms = sorted(self.rooms, key=lambda x: natural_sort_key(x.getFullName()))

        self._produce_bars()

    def render(self, show_empty_rooms=True, show_empty_days=True, form_data=None, show_summary=True, show_navbar=True,
               can_navigate=True):
        bars = self.build_bars_data(show_empty_rooms, show_empty_days)
        days = self.build_days_attrs() if self.specific_room and bars else {}

        period = self.end_dt.date() - self.start_dt.date() + timedelta(days=1)

        return WTemplated('RoomBookingCalendarWidget').getHTML({
            'form_data': form_data,
            'bars': bars,
            'days': days,
            'start_dt': self.start_dt,
            'end_dt': self.end_dt,
            'period_name': _('day') if period.days == 1 else _('period'),
            'specific_room': bool(self.specific_room),
            'show_summary': show_summary,
            'show_navbar': show_navbar,
            'can_navigate': show_navbar and can_navigate,
            'repeat_unit': self.repeat_unit,
            'flexible_days': self.flexible_days
        })

    def iter_days(self):
        if self.repeat_unit is None and self.repeat_step is None and self.flexible_days is None:
            for dt in iterdays(self.start_dt, self.end_dt):
                yield dt.date()
        else:
            for dt in ReservationOccurrence.iter_start_time(self.start_dt, self.end_dt,
                                                            (self.repeat_unit, self.repeat_step)):
                for offset in xrange(-self.flexible_days, self.flexible_days + 1):
                    yield (dt + timedelta(days=offset)).date()

    def build_bars_data(self, show_empty_rooms=True, show_empty_days=True):
        bars_data = defaultdict(list)
        day_bars = group_list(self.bars, key=lambda b: b.date)

        for day in self.iter_days():
            bars = day_bars.get(day, [])
            if not bars and not show_empty_days:
                continue

            room_bars = group_list(bars, key=attrgetter('room_id'), sort_by=attrgetter('importance'))
            for room in self.rooms:
                bars = room_bars.get(room.id, [])
                if not bars and not show_empty_rooms:
                    continue
                room_dict = {
                    'room': room.to_serializable('__calendar_public__'),
                    'bars': [bar.to_serializable() for bar in bars]
                }
                bars_data[str(day)].append(room_dict)

        return bars_data

    def build_days_attrs(self):
        days_data = {}

        for day in self.iter_days():
            attrs = {'tooltip': '', 'className': ''}

            # TODO waiting for blockings
            # blocking = self._room.getBlockedDay(day)
            blocking = False

            if blocking:
                block = blocking.block

                if block.canOverride(session.user, explicitOnly=True):
                    attrs['className'] = 'blocked_permitted'
                    attrs['tooltip'] = _(
                        'Blocked by {0}:\n{1}\n\n<b>You are permitted to '
                        'override the blocking.</b>'.format(block.createdByUser.getFullName(), block.message))
                elif blocking.active is True:
                    if block.canOverride(session.user, self._room):
                        attrs['className'] = 'blocked_override'
                        attrs['tooltip'] = _(
                            'Blocked by {0}:\n{1}\n\n<b>You own this room or are an administrator '
                            'and are thus permitted to override the blocking. Please use this '
                            'privilege with care!</b>'.format(block.createdByUser.getFullName(), block.message))
                    else:
                        attrs['className'] = 'blocked'
                        attrs['tooltip'] = _('Blocked by {0}:\n{1}'.format(block.createdByUser.getFullName(), block.message))
                elif blocking.active is None:
                    attrs['className'] = 'preblocked'
                    attrs['tooltip'] = _(
                        'Blocking requested by {0}:\n{1}\n\n'
                        '<b>If this blocking is approved, any colliding bookings will be rejected!</b>'.format(block.createdByUser.getFullName(), block.message))
            days_data[str(day)] = attrs

        return days_data

    def _produce_bars(self):
        self._produce_reservation_bars()
        self._produce_prereservation_overlap_bars()
        if self.candidates is not None:
            self._produce_candidate_bars()
            self._produce_conflict_bars()
        self._produce_blocking_bars()

    def _produce_reservation_bars(self):
        self.bars += map(Bar.from_occurrence, self.occurrences)

    def _produce_candidate_bars(self):
        for room in self.rooms:
            for (start_dt, end_dt), candidates in self.candidates.iteritems():
                self.bars.extend(Bar.from_candidate(cand, room.id, start_dt, end_dt) for cand in candidates)

    def _produce_prereservation_overlap_bars(self):
        for _, occurrences in groupby((o for o in self.occurrences if not o.reservation.is_confirmed),
                                      key=lambda o: o.reservation.room_id):
            occurrences = list(occurrences)
            for idx, o1 in enumerate(occurrences):
                for o2 in occurrences[idx+1:]:
                    if o1.overlaps(o2, skip_self=True):
                        start, end = o1.get_overlap(o2)
                        self.bars.append(Bar(start, end, overlapping=True, reservation=o2.reservation,
                                             kind=Bar.PRECONCURRENT))

    def _produce_conflict_bars(self):
        for candidates in self.candidates.itervalues():
            for candidate in candidates:
                for occurrence in self.occurrences:
                    if not occurrence.reservation.is_confirmed:
                        continue
                    if candidate.overlaps(occurrence, skip_self=True):
                        start, end = candidate.get_overlap(occurrence)
                        self.conflicts += occurrence.reservation.is_confirmed
                        self.bars.append(Bar(start, end, overlapping=True, reservation=occurrence.reservation))

    def _produce_blocking_bars(self):
        blocked_rooms = BlockedRoom.find_with_filters({'room_ids': [r.id for r in self.rooms],
                                                       'state': BlockedRoom.State.accepted,
                                                       'start_date': self.start_dt.date(),
                                                       'end_date': self.end_dt.date()})

        for blocked_room in blocked_rooms:
            blocking = blocked_room.blocking
            self.bars.extend(Bar.from_blocked_room(blocked_room, day)
                             for day in self.iter_days()
                             if blocking.start_date <= day <= blocking.end_date)


class WPRoomBookingBookRoom(WPRoomBookingBase):
    def __init__(self, rh):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self), _('Book a Room'))

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBookRoom(self._rh).getHTML(params)


class WRoomBookingBookRoom(WTemplated):
    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['today'] = datetime.utcnow()
        wvars['rooms'] = [r['room'].to_serializable('__public_exhaustive__') for r in self._rh._rooms]
        wvars['maxRoomCapacity'] = self._rh._max_capacity
        wvars['roomBookingBookingListURL'] = UH.UHRoomBookingBookingListForBooking.getURL()
        wvars['formerBookingInterfaceURL'] = UH.UHRoomBookingSearch4Rooms.getURL(is_new_booking=True)
        return wvars


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
        self._standalone = (conference is None)

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
        wvars['edit_logs'] = self._reservation.edit_logs.order_by(ReservationEditLog.timestamp.asc()).all()
        wvars['excluded_days'] = self._reservation.find_excluded_days().all()

        return wvars


class WPRoomBookingCalendar(WPRoomBookingBase):
    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _setCurrentMenuItem(self):
        self._bookingListCalendarOpt.setActive(True)

    def _getBody(self, params):
        params['calendar'] = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                                       rooms=params['rooms']).render()
        return WTemplated('RoomBookingCalendar').getHTML(params)


class WPRoomBookingSearchBookings(WPRoomBookingBase):
    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

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

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

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
                                _('{} occurences found').format(len(params['occurrences'])))

    def _getBody(self, params):
        params['summary'] = self._get_criteria_summary(params)
        calendar = RoomBookingCalendarWidget(params['occurrences'], params['start_dt'], params['end_dt'],
                                             rooms=params['rooms'])
        params['calendar'] = calendar.render(form_data=params['form_data'])
        return WTemplated('RoomBookingSearchBookingsResults').getHTML(params)


class WPRoomBookingNewBookingBase(WPRoomBookingBase):
    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

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


class WPRoomBookingBookingForm(WPRoomBookingBase):
    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBookingForm(self._rh, standalone=True).getHTML(params)


class WRoomBookingBookingForm(WTemplated):
    def __init__(self, rh, standalone=False):
        self._rh = rh
        self._form = rh._form
        self._room = rh._room
        self._standalone = standalone

    def getVars(self):
        wvars = WTemplated.getVars(self)
        room = self._room
        form = self._form

        wvars['user'] = session.user
        wvars['form'] = form
        wvars['config'] = Config.getInstance()
        wvars['isModif'] = self._rh._isModif
        wvars['allow_past'] = self._rh._isModif
        wvars['standalone'] = self._standalone
        wvars['infoBookingMode'] = self._rh._infoBookingMode

        wvars['showErrors'] = self._rh._showErrors
        wvars['errors'] = self._rh._errors
        wvars['thereAreConflicts'] = self._rh._thereAreConflicts
        wvars['skipConflicting'] = self._rh._skipConflicting

        wvars['room'] = room
        wvars['rooms'] = self._rh._rooms
        wvars['startDT'] = form.start_date.data
        wvars['endDT'] = form.end_date.data
        wvars['startT'] = form.start_date.data.strftime('%H:%M')
        wvars['endT'] = form.end_date.data.strftime('%H:%M')

        if self._standalone:
            wvars['conf'] = None
            wvars['saveBookingUH'] = UH.UHRoomBookingSaveBooking.getURL(None)
            wvars['roomDetailsUH'] = UH.UHRoomBookingRoomDetails.getURL(None)
            wvars['bookingFormURL'] = UH.UHRoomBookingBookingForm.getURL(None)
        else:
            wvars['conf'] = self._rh._conf
            wvars['saveBookingUH'] = UH.UHConfModifRoomBookingSaveBooking.getURL(wvars['conf'])
            wvars['roomDetailsUH'] = UH.UHConfModifRoomBookingRoomDetails.getURL(wvars['conf'])
            wvars['bookingFormURL'] = UH.UHConfModifRoomBookingBookingForm.getURL(wvars['conf'])

        # [Book] or [PRE-Book] ?
        if room.canBePreBookedBy(session.user) and not room.canBeBookedBy(session.user):
            wvars['bookingMessage'] = 'PRE-Book'
        else:
            wvars['bookingMessage'] = 'Book'

        start_dt = datetime.combine(form.start_date.data.date(), time())
        end_dt = datetime.combine(form.start_date.data.date(), time(23, 59))

        wvars["room_calendar"] = RoomBookingCalendarWidget(wvars['occurrences'], start_dt, end_dt,
                                                           candidates=wvars['candidates'],
                                                           specific_room=room).render(show_navbar=False)
        return wvars


# class WRoomBookingRoomCalendar(WRoomBookingCalendar):
#     def __init__(self, rh, room, form, standalone=False):
#         WRoomBookingCalendar.__init__(self, rh, room, form)
#         self._rh = rh
#         self._form = rh._form
#         self._room = rh._room
#         self._standalone = standalone
#
#     def getVars(self):
#         wvars = WRoomBookingCalendar.getVars(self, reservations=True, preresevations=True)
#         form = self._form
#         room = self._room
#
#         # TODO ???
#         # if not self._standalone:
#         #     for dt in bars.iterkeys():
#         #         for bar in bars[dt]:
#         #             # bar.forReservation.setOwner(self._rh._conf)
#         #             bar.reservation.created_by = self._rh._getUser().id
#
#         # TODO retrieve conflict state with blockings
#         # wvars["blockConflicts"] = form.getBlockingConflictState(self._rh._aw.getUser())
#
#         wvars['Bar'] = Bar
#         wvars['room'] = room
#         wvars['with_conflicts'] = True
#         wvars['booking_details_url'] = room.details_url if self._standalone else room.booking_url
#
#         return wvars


class WPRoomBookingConfirmBooking(WPRoomBookingBase):
    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingConfirmBooking, self).__init__(rh)

    def _getBody(self, params):
        return WRoomBookingConfirmBooking(self._rh, standalone=True).getHTML(params)


class WRoomBookingConfirmBooking(WRoomBookingBookingForm):
    def getVars(self):
        wvars = super(WRoomBookingConfirmBooking, self).getVars()

        wvars["candResv"] = self._candResv

        wvars["standalone"] = self._standalone
        wvars["formMode"] = self._rh._formMode
        wvars["FormMode"] = FormMode
        wvars["collisions"] = self._rh._collisions

        # If we are here, we are either in booking mode and trying to overwrite PRE-Bookings...
        bookingMessage = "Book"
        bookingMessageOther = "PRE-Book"
        wvars["rejectOthers"] = True
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook(user) and not room.canBook(user):
            # ...or we are in PRE-booking mode and conflicting with another PRE-Booking
            bookingMessage = "PRE-Book"
            bookingMessageOther = "PRE-Book"
            wvars["rejectOthers"] = False
        wvars["bookingMessage"] = bookingMessage
        wvars["bookingMessageOther"] = bookingMessageOther

        if self._standalone:
            wvars["conf"] = None
            wvars["saveBookingUH"] = urlHandlers.UHRoomBookingSaveBooking
            wvars["roomDetailsUH"] = urlHandlers.UHRoomBookingRoomDetails
        else:
            wvars["conf"] = self._rh._conf
            wvars["saveBookingUH"] = urlHandlers.UHConfModifRoomBookingSaveBooking
            wvars["roomDetailsUH"] = urlHandlers.UHConfModifRoomBookingRoomDetails
        return wvars


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


class WRoomBookingList(WTemplated):
    def __init__(self, rh, standalone=False):
        self._standalone = standalone
        self._rh = rh
        if not standalone:
            self._conf = rh._conf

    def getVars(self):
        wvars = super(WRoomBookingList, self).getVars()

        wvars["reservations"] = self._rh._resvs
        wvars["standalone"] = self._standalone
        wvars["yesterday"] = datetime.now() - timedelta(1)

        if self._standalone:
            wvars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            wvars["conference"] = self._conf
            wvars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails

        return wvars
