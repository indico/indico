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

from flask import request

from copy import copy
from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import izip

from MaKaC.common import Config
from MaKaC.webinterface import urlHandlers as UH
from MaKaC.webinterface.wcomponents import WTemplated

from indico.util.i18n import _

from .. import WPRoomBookingBase
from ...models.locations import Location
from ...models.rooms import Room
from ...models.reservations import RepeatMapping
from ...models.utils import get_overlap
from ..utils import (
    Bar,
    BlockingDetailsForBars,
    DayBar,
    RoomDetailsForBars,
    getNewDictOnlyWith,
    updateOldDateStyle
)


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
        wvars['rooms'] = [r.to_serializable() for r in self._rh._rooms]

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
                start_date=f.start_date.data-timediff-timedelta(1),
                end_date=f.end_date.data-timediff-timedelta(1)
            )
        )
        wvars['nextURL'] = UH.UHRoomBookingBookingList.getURL(
            **getNewDictOnlyWith(
                f.data,
                keys=['room_id_list', 'repeat_unit', 'repeat_step', 'is_search'],
                start_date=f.start_date.data+timediff+timedelta(1),
                end_date=f.end_date.data+timediff+timedelta(1)
            )
        )

        wvars['overload'] = True  # f._overload
        wvars['dayLimit'] = 500   # self._rh._dayLimit
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

            occurrences = [
                (None, None, None, False,
                 f.start_date.data.time(), f.end_date.data.time())
            ] + filter(lambda e: e[0] != None, izip(
                rids, reasons, booked_for_names,
                is_confirmed_statuses, start_times, end_times
            ))

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
        wvars['rooms'] = self._rh._rooms
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
        self._candResv = rh._candResv
        self._standalone = standalone

    def getVars(self):
        wvars = WTemplated.getVars(self)

        wvars['standalone'] = self._standalone
        wvars['config'] = Config.getInstance()

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

        wvars['candResv'] = self._candResv
        wvars['startDT'] = self._candResv.startDT
        wvars['endDT'] = self._candResv.endDT
        wvars['startT'] = ''
        wvars['endT'] = ''
        if any((self._candResv.startDT.hour,
                self._candResv.startDT.minute,
                self._candResv.endDT.hour,
                self._candResv.endDT.minute)):
            wvars["startT"] = '%02d:%02d' % (self._candResv.startDT.hour, self._candResv.startDT.minute)
            wvars["endT"] = '%02d:%02d' % (self._candResv.endDT.hour, self._candResv.endDT.minute)

        wvars['showErrors'] = self._rh._showErrors
        wvars['errors'] = self._rh._errors
        wvars['thereAreConflicts'] = self._rh._thereAreConflicts
        wvars['skipConflicting'] = self._rh._skipConflicting

        if self._rh._formMode == FormMode.MODIF:
            wvars["allowPast"] = "true"
        else:
            wvars["allowPast"] = "false"
        wvars["formMode"] = self._rh._formMode
        wvars["FormMode"] = FormMode

        # [Book] or [PRE-Book] ?
        bookingMessage = "Book"
        room = self._candResv.room
        user = self._rh._getUser()
        if room.canPrebook(user) and not room.canBook(user):
            bookingMessage = "PRE-Book"
        wvars["bookingMessage"] = bookingMessage
        wvars["user"] = user

        if self._rh._formMode != FormMode.MODIF:
            bText = bookingMessage
        else:
            bText = "Save"

        wvars["roomBookingRoomCalendar"] = WRoomBookingRoomCalendar(self._rh, self._standalone, buttonText=bText).getHTML({})
        wvars["rooms"] = self._rh._rooms
        wvars["infoBookingMode"] = self._rh._infoBookingMode

        return wvars


class WRoomBookingRoomCalendar(WTemplated):

    def __init__(self, rh, standalone=False, buttonText =''):
        self._rh = rh
        self._candResv = rh._candResv
        self._standalone = standalone
        self._buttonText = buttonText

    def getVars(self):
        wvars = super(WRoomBookingRoomCalendar, self).getVars()

        candResv = self._candResv
        room = candResv.room

        if self._standalone:
            wvars["bookingDetailsUH"] = urlHandlers.UHRoomBookingBookingDetails
        else:
            wvars["bookingDetailsUH"] = urlHandlers.UHConfModifRoomBookingDetails

        # Calendar range
        now = datetime.now()
        if candResv != None: #.startDT != None and candResv.endDT != None:
            calendarStartDT = datetime(
                candResv.startDT.year,
                candResv.startDT.month,
                candResv.startDT.day,
                0, 0, 1
            )  # Potential performance problem
            calendarEndDT =  datetime(
                candResv.endDT.year,
                candResv.endDT.month,
                candResv.endDT.day,
                23, 59
            )  # with very long reservation periods
        else:
            calendarStartDT = datetime(now.year, now.month, now.day, 0, 0, 1)
            calendarEndDT = calendarStartDT + timedelta(3 * 31, 50, 0, 0, 59, 23)

        # example resv. to ask for other reservations
        resvEx = CrossLocationFactory.newReservation(location =room.locationName)
        resvEx.startDT = calendarStartDT
        resvEx.endDT = calendarEndDT
        resvEx.repeatability = RepeatabilityEnum.daily
        resvEx.room = room
        resvEx.isConfirmed = None # To include both confirmed and not confirmed

        # Bars: Existing reservations
        collisionsOfResvs = resvEx.getCollisions()
        bars = []
        for c in collisionsOfResvs:
            if c.withReservation.isConfirmed:
                bars.append(Bar(c, Bar.UNAVAILABLE))
            else:
                bars.append(Bar(c, Bar.PREBOOKED))

        # Bars: Candidate reservation
        periodsOfCandResv = candResv.splitToPeriods()
        for p in periodsOfCandResv:
            bars.append(Bar(Collision((p.startDT, p.endDT), candResv), Bar.CANDIDATE))

        # Bars: Conflicts all vs candidate
        candResvIsConfirmed = candResv.isConfirmed;
        candResv.isConfirmed = None
        allCollisions = candResv.getCollisions()
        candResv.isConfirmed = candResvIsConfirmed
        if candResv.id:
            # Exclude candidate vs self pseudo-conflicts (Booking modification)
            allCollisions = filter(lambda c: c.withReservation.id != candResv.id, allCollisions)

        collisions = [] # only with confirmed resvs
        for c in allCollisions:
            if c.withReservation.isConfirmed:
                bars.append(Bar(c, Bar.CONFLICT))
                collisions.append(c)
            else:
                bars.append(Bar(c, Bar.PRECONFLICT))

        if not candResv.isRejected and not candResv.isCancelled:
            wvars["thereAreConflicts"] = len(collisions) > 0
        else:
            wvars["thereAreConflicts"] = False
        wvars["conflictsNumber"] = len(collisions)

        bars = barsList2Dictionary(bars)
        bars = addOverlappingPrebookings(bars)
        bars = sortBarsByImportance(bars, calendarStartDT, calendarEndDT)

        if not self._standalone:
            for dt in bars.iterkeys():
                for bar in bars[dt]:
                    bar.forReservation.setOwner(self._rh._conf)

        wvars["blockConflicts"] = candResv.getBlockingConflictState(self._rh._aw.getUser())

        wvars["calendarStartDT"] = calendarStartDT
        wvars["calendarEndDT"] = calendarEndDT
        bars = introduceRooms([room], bars, calendarStartDT, calendarEndDT, user=self._rh._aw.getUser())
        fossilizedBars = {}
        for key in bars:
            fossilizedBars[str(key)] = [fossilize(bar, IRoomBarFossil) for bar in bars[key]]
        wvars["barsFossil"] = fossilizedBars
        wvars["dayAttrs"] = fossilize(dict((day.strftime("%Y-%m-%d"), getDayAttrsForRoom(day, room))
                                           for day in bars.iterkeys()))
        wvars["bars"] = bars
        wvars["iterdays"] = iterdays
        wvars["day_name"] = day_name
        wvars["Bar"] = Bar
        wvars["room"] = room
        wvars["buttonText"] = self._buttonText
        wvars["currentUser"] = self._rh._aw.getUser()
        wvars["withConflicts"] = True
        return wvars


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

    def __init__(self, rh):
        self._rh = rh
        super(WPRoomBookingStatement, self).__init__(rh)

    def _getBody(self, params):
        return WRoomBookingStatement(self._rh).getHTML(params)


class WRoomBookingStatement(WTemplated):

    def __init__(self, rh):
        self._rh = rh

    def getVars(self):
        wvars = super(WRoomBookingStatement, self).getVars()
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

