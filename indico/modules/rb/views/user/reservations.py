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
from datetime import datetime, time, timedelta
from itertools import izip

from flask import session
from pytz import timezone

from MaKaC.common import Config
from MaKaC.common import info
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.wcomponents import WTemplated
from indico.util.i18n import _
from indico.util.date_time import iterdays
from indico.util.struct.iterables import group_list
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.reservations import Reservation, RepeatMapping
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.utils import get_overlap
from indico.modules.rb.views import WPRoomBookingBase
from indico.modules.rb.views.utils import Bar, BlockingDetailsForBars, DayBar, RoomDetailsForBars, getNewDictOnlyWith


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
    def __init__(self, rh):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh

    def _setCurrentMenuItem(self):
        self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingDetails(self._rh).getHTML(params)


class WRoomBookingDetails(WTemplated):
    def __init__(self, rh, conference=None):
        self._rh = rh
        self._resv = rh._resv
        self._conf = conference
        self._standalone = (conference is None)

    def getVars(self):
        wvars = WTemplated.getVars(self)
        wvars['standalone'] = self._standalone
        wvars['reservation'] = self._reservation
        wvars['collisions'] = self._rh._collisions
        wvars['config'] = Config.getInstance()
        wvars['actionSucceeded'] = self._rh._afterActionSucceeded
        if self._rh._afterActionSucceeded:
            wvars['title'] = self._rh._title
            wvars['description'] = self._rh._description

        if self._standalone:
            wvars['roomDetailsUH'] = UH.UHRoomBookingRoomDetails
            wvars['modifyBookingUH'] = UH.UHRoomBookingModifyBookingForm
            wvars['cloneURL'] = UH.UHRoomBookingCloneBooking.getURL(self._resv)
        else:
            wvars['roomDetailsUH'] = UH.UHConfModifRoomBookingRoomDetails
            wvars['modifyBookingUH'] = UH.UHConfModifRoomBookingModifyBookingForm
            wvars['cloneURL'] = UH.UHConfModifRoomBookingCloneBooking.getURL(self._resv)

        wvars['isPreBooking'] = not self._reservation.is_confirmed
        wvars['bookMessage'] = _('PRE-Booking') if wvars['isPreBooking'] else _('Booking')

        wvars['canBeRejectedBy'] = None
        wvars['canBeCancelledBy'] = None

        return wvars


class WPRoomBookingBookingList(WPRoomBookingBase):
    def __init__(self, rh):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _getTitle(self):
        base_title = '{} - '.format(WPRoomBookingBase._getTitle(self))

        if self._rh._form.is_today.data:
            return base_title + _('Calendar')
        elif self._rh._form.is_only_mine.data and self._rh._form.is_only_pre_bookings.data:
            return base_title + _('My PRE-bookings')
        elif self._rh._form.is_only_mine.data:
            return base_title + _('My bookings')
        elif self._rh._form.is_only_my_rooms.data and self._rh._form.is_only_pre_bookings.data:
            return base_title + _('PRE-bookings in my rooms')
        elif self._rh._form.is_only_my_rooms.data:
            return base_title + _('Bookings in my rooms')
        else:
            return base_title + _('Found bookings')

    def _setCurrentMenuItem(self):
        if self._rh._form.is_today.data or self._rh._form.is_all_rooms:
            self._bookingListCalendarOpt.setActive(True)
        elif self._rh._form.is_only_mine.data and self._rh._form.is_only_pre_bookings.data:
            self._myPreBookingListOpt.setActive(True)
        elif self._rh._form.is_only_mine.data:
            self._myBookingListOpt.setActive(True)
        elif self._rh._form.is_only_my_rooms.data and self._rh._form.is_only_pre_bookings.data:
            self._usersPrebookings.setActive(True)
        elif self._rh._form.is_only_my_rooms.data:
            self._usersBookings.setActive(True)
        else:
            self._bookRoomNewOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingBookingList(self._rh).getHTML(params)


class WRoomBookingBookingList(WTemplated):
    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = WTemplated.getVars(self)

        f = self._rh._form

        wvars['title'] = self._rh._title

        wvars['bookingURL'] = UH.UHRoomBookingBookRoom.getURL()

        wvars['finishDate'] = f.finish_date.data
        wvars['search'] = f.is_search.data

        wvars['showRejectAllButton'] = True  # rh._showRejectAllButton
        wvars['prebookingsRejected'] = True  # rh._prebookingsRejected

        wvars['subtitle'] = ''  # rh._subtitle
        wvars['description'] = ''  # rh._description

        yesterday = datetime.utcnow() - timedelta(1)
        wvars['yesterday'] = yesterday

        wvars['attributes'] = {}
        wvars["withPrevNext"] = True

        timediff = f.end_date.data - f.start_date.data
        wvars['prevURL'] = UH.UHRoomBookingBookingList.getURL(
            **getNewDictOnlyWith(
                f.data,
                keys=['room_id_list', 'repeat_unit', 'repeat_step', 'is_search'],
                start_date=f.start_date.data - timediff - timedelta(1),
                end_date=f.end_date.data - timediff - timedelta(1)
            )
        )
        wvars['nextURL'] = UH.UHRoomBookingBookingList.getURL(
            **getNewDictOnlyWith(
                f.data,
                keys=['room_id_list', 'repeat_unit', 'repeat_step', 'is_search'],
                start_date=f.start_date.data + timediff + timedelta(1),
                end_date=f.end_date.data + timediff + timedelta(1)
            )
        )

        wvars['overload'] = True  # f._overload
        wvars['dayLimit'] = 500  # self._rh._dayLimit
        wvars['newBooking'] = f.is_new_booking.data

        # Bars

        barData, room_ids = {}, set()
        for (d, room, location_name,
             blocking_id, blocking_message, blocking_creator,
             rids, reasons, booked_for_names, is_confirmed_statuses,
             start_times, end_times) in self._rh._reservations:
            room_ids.add(room.id)

            day = datetime.strftime(d, '%Y-%m-%d')
            if day not in barData:
                barData[day] = []

            room_data = DayBar(RoomDetailsForBars(room, location_name))

            blocking_details = BlockingDetailsForBars(blocking_id, blocking_message, blocking_creator)
            if blocking_id:
                barData[day].addBar(Bar(
                    day, datetime.max.time(), datetime.min.time(),
                    Bar.BLOCKED,
                    None, None, None, None,
                    blocking_details
                ))

            occurrences = [(None, None, None, False, f.start_date.data.time(), f.end_date.data.time())] + \
                          filter(lambda e: e[0] is not None,
                                 izip(rids, reasons, booked_for_names, is_confirmed_statuses, start_times, end_times))

            for occ1 in occurrences:
                occ1_id, occ1_reason, occ1_name, occ1_is_confirmed, occ1_st, occ1_et = occ1
                room_data.addBar(Bar(
                    day, occ1_st, occ1_et,
                    Bar.get_kind(occ1_id, occ1_is_confirmed),
                    occ1_id, occ1_reason, occ1_name, location_name,
                    blocking_details
                ))
                for occ2 in occurrences:
                    if occ1 == occ2 or not occ1_id:
                        continue
                    occ2_id, occ2_reason, occ2_name, occ2_is_confirmed, occ2_st, occ2_et = occ2

                    overlap = get_overlap(occ1_st, occ1_et, occ2_st, occ2_et)
                    if overlap:
                        st, et = overlap
                        room_data.addBar(Bar(
                            day, st, et,
                            Bar.get_kind(occ1_id, occ1_is_confirmed, occ2_id, occ2_is_confirmed),
                            occ1_id, occ1_reason, occ1_name, location_name,
                            blocking_details
                        ))
            barData[day].append(room_data.to_serializable())

        wvars['barsFossil'] = barData
        wvars['numOfRooms'] = len(room_ids)
        wvars['manyRooms'] = wvars['numOfRooms'] > 0
        wvars['periodName'] = 'day' if f.start_date.data == f.end_date.data else 'period'
        wvars['startD'] = f.start_date.data.date().strftime('%d/%m/%Y')
        wvars['endD'] = f.end_date.data.date().strftime('%d/%m/%Y')
        wvars['repeatability'] = RepeatMapping.getOldMapping(f.repeat_unit.data, f.repeat_step.data)

        wvars['conflictsNumber'] = 0
        wvars['thereAreConflicts'] = False

        wvars['flexibleDatesRange'] = f.flexible_dates_range.data
        wvars['ofMyRooms'] = f.is_only_my_rooms.data
        wvars['calendarFormUrl'] = UH.UHRoomBookingBookingList.getURL(
            room_id_list=-1,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow()
        )

        wvars['dayAttrs'] = {}
        wvars["calendarParams"] = {}
        return wvars


class WPRoomBookingSearch4Bookings(WPRoomBookingBase):
    def __init__(self, rh):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh

    def _getTitle(self):
        return '{} - {}'.format(WPRoomBookingBase._getTitle(self),
                                _('Search for bookings'))

    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def _setCurrentMenuItem(self):
        self._bookingListSearchOpt.setActive(True)

    def _getBody(self, params):
        return WRoomBookingSearch4Bookings(self._rh).getHTML(params)


class WRoomBookingSearch4Bookings(WTemplated):
    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = WTemplated.getVars(self)

        wvars['today'] = datetime.utcnow()
        wvars['weekLater'] = datetime.utcnow() + timedelta(7)
        wvars['Location'] = Location
        wvars['rooms'] = [r['room'].to_serializable('__public_exhaustive__') for r in self._rh._rooms]
        wvars['repeatability'] = None
        wvars['isResponsibleForRooms'] = Room.isAvatarResponsibleForRooms(self._rh.getAW().getUser())
        wvars['roomBookingBookingListURL'] = UH.UHRoomBookingBookingList.getURL()

        return wvars


class WPRoomBookingBookingForm(WPRoomBookingBase):
    def getJSFiles(self):
        return WPRoomBookingBase.getJSFiles(self) + self._includeJSPackage('RoomBooking')

    def __init__(self, rh):
        WPRoomBookingBase.__init__(self, rh)
        self._rh = rh

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

        wvars['user'] = session.user
        wvars['form'] = self._form
        wvars['config'] = Config.getInstance()
        wvars['isModif'] = self._rh._isModif
        wvars['allow_past'] = 'true' if self._rh._isModif else 'false'
        wvars['standalone'] = self._standalone
        wvars['infoBookingMode'] = self._rh._infoBookingMode

        wvars['showErrors'] = self._rh._showErrors
        wvars['errors'] = self._rh._errors
        wvars['thereAreConflicts'] = self._rh._thereAreConflicts
        wvars['skipConflicting'] = self._rh._skipConflicting

        wvars['room'] = self._room
        wvars['rooms'] = self._rh._rooms
        wvars['startDT'] = self._form.start_date.data
        wvars['endDT'] = self._form.end_date.data
        wvars['startT'] = self._form.start_date.data.strftime('%H:%M')
        wvars['endT'] = self._form.end_date.data.strftime('%H:%M')

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
        if self._room.canBePreBookedBy(session.user) and not self._room.canBeBookedBy(session.user):
            wvars['bookingMessage'] = 'PRE-Book'
        else:
            wvars['bookingMessage'] = 'Book'

        bText = _('Save') if self._rh._isModif else wvars['bookingMessage']
        wvars["room_calendar"] = WRoomBookingRoomCalendar(self._rh, self._standalone, button_text=bText).getHTML({})

        return wvars


class WRoomBookingRoomCalendar(WTemplated):
    def __init__(self, rh, standalone=False, button_text=''):
        self._rh = rh
        self._form = rh._form
        self._room = rh._room
        self._standalone = standalone
        self._button_text = button_text

    def getVars(self):
        wvars = WTemplated.getVars(self)
        form = self._form
        room = self._room

        if form.start_date is not None and form.end_date is not None:
            self.start = datetime.combine(form.start_date.data, time())
            self.end = datetime.combine(form.end_date.data, time(23, 59))
        else:
            self.start = datetime.combine(datetime.now(), time())
            self.end = self.start + timedelta(3 * 31, 50, 0, 0, 59, 23)

        tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        self.start = timezone(tz).localize(self.start)
        self.end = timezone(tz).localize(self.end)

        self.occurrences = ReservationOccurrence.find_all(
            Reservation.room_id == room.id,
            ReservationOccurrence.start >= self.start,
            ReservationOccurrence.end <= self.end,
            _join=Reservation
        )

        # TODO: retrieve occurrence if it's a modification
        self.candidates = ReservationOccurrence.create_series(
            self.start, self.end,
            (form.repeat_unit.data, form.repeat_step.data)
        )

        # Produce bars
        self.bars = []
        self.conflicts = 0
        self._produce_reservation_bars()
        self._produce_candidate_bars()
        self._produce_prereservation_overlap_bars()
        self._produce_conflict_bars()

        # TODO ???
        # if not self._standalone:
        #     for dt in bars.iterkeys():
        #         for bar in bars[dt]:
        #             # bar.forReservation.setOwner(self._rh._conf)
        #             bar.reservation.created_by = self._rh._getUser().id

        wvars['bars'] = self._get_bars_json()
        wvars['day_attrs'] = self._get_day_attrs()
        wvars["conflicts"] = self.conflicts if not form.is_rejected and not form.is_cancelled else None

        # TODO retrieve conflict state with blockings
        # wvars["blockConflicts"] = form.getBlockingConflictState(self._rh._aw.getUser())

        wvars['Bar'] = Bar
        wvars['room'] = room
        wvars['button_text'] = self._button_text
        wvars['with_conflicts'] = True
        wvars['booking_details_url'] = room.details_url if self._standalone else room.booking_url

        return wvars

    def _get_bars_json(self, show_empty_rooms=True, show_empty_days=True):
        json_dict = defaultdict(list)
        day_bars = group_list(self.bars, key=lambda b: b.date)

        for day in (d.date() for d in iterdays(self.start, self.end)):
            bars = day_bars.get(day, [])
            room_bars = group_list(bars, key=lambda b: b.reservation.room if b.reservation else self._room, sort_by=lambda b: b.importance)
            for room, bars in room_bars.iteritems():
                # TODO show_empty == False
                room_dict = {
                    'room': room.to_serializable('__calendar_public__'),
                    'bars': [bar.to_serializable() for bar in bars]
                }
                json_dict[str(day)].append(room_dict)

        # TODO
        # if showEmptyRooms:
        #     dayRoomBarsList = getRoomBarsList(rooms)  # copy.copy(cleanRoomBarsList)

        #     for roomBar in dayRoomBarsList:
        #         roomBar.bars = roomBarsDic.get(roomBar.room, [])
        # else:
        #     dayRoomBarsList = []
        #     for room in roomBarsDic.keys():
        #         dayRoomBarsList.append(RoomBars(room, roomBarsDic[room]))

        # if showEmptyDays or len(dayBars) > 0:
        #     newDayBarsDic[day.date()] = dayRoomBarsList

        return json_dict

    def _get_day_attrs(self):
        json_dict = {}

        for day in (d.date() for d in iterdays(self.start, self.end)):
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
            json_dict[str(day)] = attrs

        return json_dict


    def _produce_candidate_bars(self):
        for c in self.candidates:
            self.bars.append(Bar.from_occurrence(c))

    def _produce_reservation_bars(self):
        for o in self.occurrences:
            self.bars.append(Bar.from_occurrence(o))

    def _produce_prereservation_overlap_bars(self):
        prebookings = [o for o in self.occurrences if not o.reservation.is_confirmed]
        for idx, o1 in enumerate(prebookings):
            for o2 in prebookings[idx+1:]:
                if o1.overlaps(o2, skip_self=True):
                    start, end = o1.get_overlap(o2)
                    self.bars.append(start, end, overlapping=True, reservation=o2.reservation, kind=Bar.PRECONCURRENT)

    def _produce_conflict_bars(self):
        for c in self.candidates:
            for o in [o for o in self.occurrences if o.reservation.is_confirmed]:
                if c.overlaps(o, skip_self=True):
                    start, end = c.get_overlap(o)
                    self.conflicts += 1 if o.reservation.is_confirmed else 0
                    self.bars.append(Bar(start, end, overlapping=True, reservation=o.reservation))


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
