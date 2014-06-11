# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
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

from ast import literal_eval
from datetime import datetime, time, timedelta, date
from collections import defaultdict

from flask import request, session
from werkzeug.datastructures import MultiDict

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.util.date_time import get_datetime_from_request
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.forms import (BookingSearchForm, NewBookingCriteriaForm, NewBookingPeriodForm,
                                                 FormDefaults, NewBookingConfirmForm, NewBookingSimpleForm)
from indico.modules.rb.models.reservations import Reservation, RepeatMapping
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.utils import getRoomBookingOption
from indico.modules.rb.views.user import reservations as reservation_views
from indico.modules.rb.views.user.reservations import (WPRoomBookingSearchBookings, WPRoomBookingSearchBookingsResults,
                                                       WPRoomBookingCalendar, WPRoomBookingNewBookingSelectRoom,
                                                       WPRoomBookingNewBookingSelectPeriod,
                                                       WPRoomBookingNewBookingConfirm,
                                                       WPRoomBookingNewBookingSimple)
from indico.web.flask.util import url_for


class RHRoomBookingBookRoom(RHRoomBookingBase):
    def _process(self):
        self._rooms = sorted(Room.getRoomsWithData('equipment'),
                             key=lambda x: natural_sort_key(x['room'].getFullName()))
        self._max_capacity = Room.getMaxCapacity()
        return reservation_views.WPRoomBookingBookRoom(self).display()


class RHRoomBookingBookingDetails(RHRoomBookingBase):
    def _checkParams(self):
        resv_id = request.view_args.get('resvID')
        self._reservation = Reservation.get(request.view_args['resvID'])
        if not self._reservation:
            raise IndicoError('No booking with id: {}'.format(resv_id))

    def _process(self):
        return reservation_views.WPRoomBookingBookingDetails(self).display()


class RHRoomBookingSearchBookings(RHRoomBookingBase):
    menu_item = 'bookingListSearch'

    def _get_form_data(self):
        return request.form

    def _checkParams(self):
        self._rooms = sorted(Room.find_all(is_active=True), key=lambda r: natural_sort_key(r.getFullName()))
        self._form_data = self._get_form_data()
        self._form = BookingSearchForm(self._form_data)
        self._form.room_ids.choices = [(r.id, None) for r in self._rooms]

    def _is_submitted(self):
        return self._form.is_submitted()

    def _process(self):
        form = self._form
        if self._is_submitted() and form.validate():
            occurrences = ReservationOccurrence.find_with_filters(form.data, session.user).all()
            rooms = [r for r in self._rooms if r.id in set(form.room_ids.data)]
            return WPRoomBookingSearchBookingsResults(self, rooms=rooms, occurrences=occurrences,
                                                      start_dt=form.start_dt.data, end_dt=form.end_dt.data,
                                                      form=form, form_data=self._form_data,
                                                      menu_item=self.menu_item).display()

        return WPRoomBookingSearchBookings(self, errors=form.error_list, rooms=self._rooms,
                                           user_has_rooms=session.user.has_rooms).display()


class RHRoomBookingSearchBookingsShortcutBase(RHRoomBookingSearchBookings):
    """Base class for searches with predefined criteria"""
    search_criteria = {}

    def _is_submitted(self):
        return True

    def _get_form_data(self):
        if request.method == 'POST':
            # Actual form submission (when using the period selector widget)
            return RHRoomBookingSearchBookings._get_form_data(self)

        # Class-specific criteria + default times
        data = MultiDict(self.search_criteria)
        data['start_time'] = '00:00'
        data['end_time'] = '23:59'
        data['start_date'] = date.today().strftime('%d/%m/%Y')
        data['end_date'] = (date.today() + timedelta(weeks=1)).strftime('%d/%m/%Y')
        data.setlist('room_ids', [r.id for r in self._rooms])
        return data


class RHRoomBookingSearchMyBookings(RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'myBookingList'
    search_criteria = {
        'is_only_mine': True
    }


class RHRoomBookingSearchMyPendingBookings(RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'myPendingBookingList'
    search_criteria = {
        'is_only_mine': True,
        'is_only_pending_bookings': True
    }


class RHRoomBookingSearchBookingsMyRooms(RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'usersBookings'
    search_criteria = {
        'is_only_my_rooms': True
    }


class RHRoomBookingSearchPendingBookingsMyRooms(RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'usersPendingBookings'
    search_criteria = {
        'is_only_my_rooms': True,
        'is_only_pending_bookings': True
    }


class RHRoomBookingNewBookingBase(RHRoomBookingBase):
    def _make_confirm_form(self, room, step=None, defaults=None, form_class=NewBookingConfirmForm):
        # Step 3
        # If we come from a successful step 2 we take default values from that step once again
        if step == 2:
            defaults.equipments = []  # wtforms bug; avoid `foo in None` check
            form = form_class(formdata=MultiDict(), obj=defaults)
        else:
            form = form_class(obj=defaults)

        can_book = room.can_be_booked(session.user)
        can_prebook = room.can_be_prebooked(session.user)
        if not can_prebook or (can_book and room.can_be_booked(session.user, True)):
            # The user has actually the permission to book (not just because he's an admin)
            # Or he simply can't even prebook the room
            del form.submit_prebook
        if not can_book:
            # User can only prebook
            del form.submit_book

        form.equipments.query = room.find_available_video_conference()
        return form

    def _get_all_conflicts(self, room, form):
        conflicts = defaultdict(list)
        pre_conflicts = defaultdict(list)

        candidates = ReservationOccurrence.create_series(form.start_date.data, form.end_date.data,
                                                         (form.repeat_step.data, form.repeat_step.data))
        occurences = ReservationOccurrence.find_overlapping_with(room, candidates).all()

        for cand in candidates:
            for occ in occurences:
                if cand.overlaps(occ):
                    if occ.reservation.is_confirmed:
                        conflicts[cand].append(occ)
                    else:
                        pre_conflicts[cand].append(occ)

        return conflicts, pre_conflicts

    def _get_all_occurrences(self, room_ids, form, flexible_days=0):
        start_dt = form.start_date.data
        end_dt = form.end_date.data
        repeat_unit = form.repeat_unit.data
        repeat_step = form.repeat_step.data
        day_start_dt = datetime.combine(start_dt.date(), time())
        day_end_dt = datetime.combine(end_dt.date(), time(23, 59))
        today_start_dt = datetime.combine(date.today(), time())
        flexible_start_dt = day_start_dt - timedelta(days=flexible_days)
        if not session.user.isAdmin():
            flexible_start_dt = max(today_start_dt, flexible_start_dt)
        flexible_end_dt = day_end_dt + timedelta(days=flexible_days)

        occurrences = ReservationOccurrence.find_all(
            Reservation.room_id.in_(room_ids),
            ReservationOccurrence.start >= flexible_start_dt,
            ReservationOccurrence.end <= flexible_end_dt,
            ReservationOccurrence.is_valid,
            _join=Reservation,
            _eager=ReservationOccurrence.reservation
        )

        candidates = {}
        for days in xrange(-flexible_days, flexible_days + 1):
            offset = timedelta(days=days)
            series_start = start_dt + offset
            series_end = end_dt + offset
            if series_start < flexible_start_dt:
                    continue
            candidates[series_start, series_end] = ReservationOccurrence.create_series(series_start, series_end,
                                                                                       (repeat_unit, repeat_step))
        return occurrences, candidates

    def _create_booking(self, form, room):
        if 'submit_book' in form and 'submit_prebook' in form:
            # Admins have the choice
            prebook = form.submit_prebook.data
        else:
            # Otherwise the existence of the book submit button means the user can book
            prebook = 'submit_book' not in form
        reservation = Reservation.create_from_data(room, form.data, session.user, prebook)
        db.session.add(reservation)
        db.session.flush()
        return reservation


class RHRoomBookingNewBookingSimple(RHRoomBookingNewBookingBase):
    def _checkParams(self):
        self._room = Room.get(int(request.view_args['roomID']))

    def _make_form(self):
        if 'start_date' in request.args:
            start_date = datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        else:
            start_date = date.today()
        defaults = FormDefaults(room_id=self._room.id,
                                start_date=datetime.combine(start_date, time(8, 30)),
                                end_date=datetime.combine(start_date, time(17, 30)),
                                booked_for_id=session.user.id,
                                booked_for_name=session.user.getStraightFullName().decode('utf-8'),
                                contact_email=session.user.getEmail().decode('utf-8'),
                                contact_phone=session.user.getPhone().decode('utf-8'))

        return self._make_confirm_form(self._room, defaults=defaults, form_class=NewBookingSimpleForm)

    def _process(self):
        room = self._room
        rooms = Room.find_all()
        form = self._make_form()

        if form.is_submitted() and not form.validate():
            occurrences = {}
            candidates = {}
            conflicts = {}
            pre_conflicts = {}
        else:
            occurrences, candidates = self._get_all_occurrences([self._room.id], form)
            conflicts, pre_conflicts = self._get_all_conflicts(self._room, form)

        if form.validate_on_submit() and not form.submit_check.data:
            booking = self._create_booking(form, room)
            self._redirect(url_for('rooms.roomBooking-bookingDetails', booking))
            return

        can_override = room.can_be_overriden(session.user)
        return WPRoomBookingNewBookingSimple(self, form=form, room=room, rooms=rooms,
                                             occurrences=occurrences,
                                             candidates=candidates,
                                             conflicts=conflicts,
                                             pre_conflicts=pre_conflicts,
                                             start_dt=form.start_date.data,
                                             end_dt=form.end_date.data,
                                             repeat_unit=form.repeat_unit.data,
                                             repeat_step=form.repeat_step.data,
                                             can_override=can_override).display()


class RHRoomBookingNewBooking(RHRoomBookingNewBookingBase):
    def _checkParams(self):
        try:
            self._step = int(request.form.get('step', 1))
        except ValueError:
            self._step = 1

    def _make_select_room_form(self):
        # Step 1
        self._rooms = sorted(Room.find_all(is_active=True), key=lambda r: natural_sort_key(r.getFullName()))

        defaults = FormDefaults(start_date=datetime.combine(date.today(), time(8, 30)),
                                end_date=datetime.combine(date.today(), time(17, 30)))

        form = NewBookingCriteriaForm(obj=defaults)
        form.room_ids.choices = [(r.id, None) for r in self._rooms]
        return form

    def _make_select_period_form(self, defaults=None):
        # Step 2
        # If we come from a successful step 1 submission we use the default values provided by that step.
        if self._step == 1:
            return NewBookingPeriodForm(formdata=MultiDict(), obj=defaults)
        else:
            return NewBookingPeriodForm()

    def _show_confirm(self, room, form, step=None, defaults=None):
        # form can be PeriodForm or Confirmform depending on the step we come from
        if step == 2:
            confirm_form = self._make_confirm_form(room, step, defaults)
        else:
            # Step3 => Step3 due to an error in the form
            confirm_form = form

        conflicts, pre_conflicts = self._get_all_conflicts(room, form)
        repeat_msg = RepeatMapping.getMessage(form.repeat_unit.data, form.repeat_step.data)
        return WPRoomBookingNewBookingConfirm(self, form=confirm_form, room=room,
                                              start_dt=form.start_date.data,
                                              end_dt=form.end_date.data,
                                              repeat_unit=form.repeat_unit.data,
                                              repeat_step=form.repeat_step.data,
                                              repeat_msg=repeat_msg,
                                              conflicts=conflicts,
                                              pre_conflicts=pre_conflicts,
                                              errors=confirm_form.error_list).display()

    def _process_select_room(self):
        # Step 1: Room(s), dates, repetition selection
        form = self._make_select_room_form()
        if form.validate_on_submit():
            flexible_days = form.flexible_dates_range.data
            day_start_dt = datetime.combine(form.start_date.data.date(), time())
            day_end_dt = datetime.combine(form.end_date.data.date(), time(23, 59))

            selected_rooms = [r for r in self._rooms if r.id in form.room_ids.data]
            occurrences, candidates = self._get_all_occurrences(form.room_ids.data, form, flexible_days)

            period_form_defaults = FormDefaults(repeat_step=form.repeat_step.data, repeat_unit=form.repeat_unit.data)
            period_form = self._make_select_period_form(period_form_defaults)

            # Show step 2 page
            return WPRoomBookingNewBookingSelectPeriod(self, rooms=selected_rooms, occurrences=occurrences,
                                                       candidates=candidates, start_dt=day_start_dt,
                                                       end_dt=day_end_dt, period_form=period_form, form=form,
                                                       repeat_unit=form.repeat_unit.data,
                                                       repeat_step=form.repeat_step.data,
                                                       flexible_days=flexible_days).display()

        # GET or form errors => show step 1 page
        return WPRoomBookingNewBookingSelectRoom(self, errors=form.error_list, rooms=self._rooms, form=form,
                                                 max_room_capacity=Room.getMaxCapacity()).display()

    def _process_select_period(self):
        form = self._make_select_period_form()
        if form.is_submitted():
            # Errors in here are only caused by users messing with the submitted data so it's not
            # worth making the code more complex to show the errors nicely on the originating page.
            # Doing so would be very hard anyway as we don't keep all data necessary to show step 2
            # when it's not a step 1 form submission.
            if not form.validate():
                raise IndicoError('<br>'.join(form.error_list))
            room = Room.get(form.room_id.data)
            if not room:
                raise IndicoError('Invalid room')
            # Show step 3 page
            confirm_form_defaults = FormDefaults(form.data,
                                                 booked_for_id=session.user.id,
                                                 booked_for_name=session.user.getStraightFullName().decode('utf-8'),
                                                 contact_email=session.user.getEmail().decode('utf-8'),
                                                 contact_phone=session.user.getPhone().decode('utf-8'))
            return self._show_confirm(room, form, self._step, confirm_form_defaults)

    def _process_confirm(self):
        # The form needs the room to create the equipment list, so we need to get it "manually"...
        room = Room.get(int(request.form['room_id']))
        form = self._make_confirm_form(room)
        if not room.can_be_booked(session.user) and not room.can_be_prebooked(session.user):
            raise IndicoError('You cannot book this room')
        if form.validate_on_submit():
            booking = self._create_booking(form, room)
            url = url_for('rooms.roomBooking-bookingDetails', booking)
            self._redirect(url)
            return
        # There was an error in the form
        return self._show_confirm(room, form)

    def _process(self):
        if self._step == 1:
            return self._process_select_room()
        elif self._step == 2:
            return self._process_select_period()
        elif self._step == 3:
            return self._process_confirm()
        else:
            self._redirect(url_for('rooms.book'))


class RHRoomBookingBookingForm(RHRoomBookingBase):
    # This class is unused and should be removed soon!
    def _checkParams(self):
        self._form = ReservationForm(prefix='reservation')
        self._room = Room.get(int(request.values.get('roomID')))
        self._infoBookingMode = 'infoBookingMode' in request.values
        self._isAssistenceEmailSetup = getRoomBookingOption('assistanceNotificationEmails')
        self._requireRealUsers = getRoomBookingOption('bookingsForRealUsers')
        self._skipConflicting = request.values.get('skipConflicting') == 'on'
        self._isModif = False

        if not self._form.is_submitted():
            self.__populate_form(request)
        else:
            if 'resvID' in request.view_args:  # modification
                self._isModif = True
                if self._form.validate_on_submit():
                    self._reservation = Reservation()
                    self._form.populate_obj(self._reservation)

        self._thereAreConflicts = session.get('rbThereAreConflicts')
        self._showErrors = session.get('rbShowErrors')
        self._errors = session.get('rbErrors') if self._showErrors else None

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # if self._doProcess:
        #     if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
        #         raise FormValuesError('You are not authorized to book this room.')

        #     if not self._candResv.room.canBook(self._getUser()) and not self._candResv.room.canPrebook(self._getUser()):
        #         raise NoReportError('You are not authorized to book this room.')

        #     if self._formMode == FormMode.MODIF:
        #         if not self._candResv.canModify(self.getAW()):
        #             raise IndicoError('You are not authorized to take this action.')

    def _process(self):
        self._rooms = Room.find_all()

        start_dt = self._form.start_date.data
        end_dt = self._form.end_date.data

        day_start_dt = datetime.combine(self._form.start_date.data.date(), time())
        day_end_dt = datetime.combine(self._form.end_date.data.date(), time(23, 59))

        occurrences = ReservationOccurrence.find_all(
            Reservation.room_id == self._room.id,
            ReservationOccurrence.start >= day_start_dt,
            ReservationOccurrence.end <= day_end_dt,
            ~ReservationOccurrence.is_cancelled,
            _join=Reservation,
            _eager=ReservationOccurrence.reservation
        )

        candidates = ReservationOccurrence.create_series(
            start_dt, end_dt,
            (self._form.repeat_unit.data, self._form.repeat_step.data)
        )

        return reservation_views.WPRoomBookingBookingForm(self, occurrences=occurrences,
                                                          candidates=candidates).display()

    def __populate_form(self, request):
        sDT = {
            'day': request.values.get('day', datetime.now().day),
            'month': request.values.get('month', datetime.now().month),
            'year': request.values.get('year', datetime.now().year)}
        eDT = {
            'day': request.values.get('dayEnd', datetime.now().day),
            'month': request.values.get('monthEnd', datetime.now().month),
            'year': request.values.get('yearEnd', datetime.now().year)}
        sTime = {
            'hour': request.values.get('hour', 8),
            'minute': request.values.get('minute', 30)}
        eTime = {
            'hour': request.values.get('hourEnd', 17),
            'minute': request.values.get('minuteEnd', 30)}
        repeatability = request.values.get('repeatability')

        self._form.booked_for_id.data = session.user.getId()
        self._form.booked_for_name.data = session.user.getFullName().decode('utf-8')
        self._form.contact_email.data = session.user.getEmail().decode('utf-8')
        self._form.contact_phone.data = session.user.getPhone().decode('utf-8')

        for data in [sDT, sTime, eDT, eTime]:
            for k, v in data.iteritems():
                data[k] = int(v) if v is not None else v

        self._form.start_date.data = datetime(sDT['year'], sDT['month'], sDT['day'], sTime['hour'], sTime['minute'])
        self._form.end_date.data = datetime(eDT['year'], eDT['month'], eDT['day'], eTime['hour'], eTime['minute'])

        try:
            repeatability = literal_eval(repeatability)
            if len(repeatability) == 2:
                self._form.repeat_unit.data = int(repeatability[0])
                self._form.repeat_step.data = int(repeatability[1])
            else:
                raise ValueError('Wrong repeatition, expecting (interval, frequency)')
        except ValueError:
            self._form.repeat_unit.data = 0
            self._form.repeat_step.data = 0


class RHRoomBookingCalendar(RHRoomBookingBase):
    MAX_DAYS = 365 * 2

    def _checkParams(self):
        today = datetime.now().date()
        self.start_dt = get_datetime_from_request('start_', default=datetime.combine(today, time(0, 0)))
        self.end_dt = get_datetime_from_request('end_', default=datetime.combine(self.start_dt.date(), time(23, 59)))
        period = self.end_dt.date() - self.start_dt.date() + timedelta(days=1)
        self._overload = period.days > self.MAX_DAYS

    def _process(self):
        if self._overload:
            rooms = []
            occurrences = []
        else:
            rooms = Room.find_all(is_active=True)
            occurrences = ReservationOccurrence.find_all(
                Reservation.room_id.in_(room.id for room in rooms),
                ReservationOccurrence.start >= self.start_dt,
                ReservationOccurrence.end <= self.end_dt,
                ~ReservationOccurrence.is_cancelled,
                _join=Reservation,
                _eager=ReservationOccurrence.reservation
            )

        return WPRoomBookingCalendar(self, rooms=rooms, occurrences=occurrences, start_dt=self.start_dt,
                                     end_dt=self.end_dt, overload=self._overload, max_days=self.MAX_DAYS).display()


# TODO remove with legacy MaKaC code
class RHRoomBookingSaveBooking(RHRoomBookingBase):

    def __init__(self):
        raise NotImplementedError


class RHRoomBookingStatement(RHRoomBookingBase):
    def _checkParams(self):
        self._title = session.pop('rbTitle', None)
        self._description = session.pop('rbDescription', None)

    def _process(self):
        return reservation_views.WPRoomBookingStatement(self).display()


class RHRoomBookingAcceptBooking(RHRoomBookingBase):
    def _checkParams(self):
        resvID = int(params.get("resvID"))
        roomLocation = params.get("roomLocation")
        self._resv = CrossLocationQueries.getReservations(resvID=resvID, location=roomLocation)
        self._target = self._resv

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)

        # only do the remaining checks the rest if the basic ones were successful
        # (i.e. user is logged in)
        if self._doProcess:
            user = self._getUser()
            # Only responsible and admin can ACCEPT
            if not self._resv.room.isOwnedBy(user) and not self._getUser().isRBAdmin():
                raise MaKaCError("You are not authorized to take this action.")

    def _process(self):
        emailsToBeSent = []
        if len(self._resv.getCollisions(sansID=self._resv.id)) == 0:
            # No conflicts
            self._resv.isConfirmed = True
            self._resv.update()
            emailsToBeSent += self._resv.notifyAboutConfirmation()

            # Add entry to the booking history
            info = []
            info.append("Booking accepted")
            histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
            self._resv.getResvHistory().addHistoryEntry(histEntry)

            session['rbActionSucceeded'] = True
            session['rbTitle'] = _("Booking has been accepted.")
            session['rbDescription'] = _("NOTE: confirmation e-mail has been sent to the user.")
            url = urlHandlers.UHRoomBookingBookingDetails.getURL(self._resv)
            self._redirect(url)  # Redirect to booking details
        else:
            errors = ["PRE-Booking conflicts with other (confirmed) bookings."]
            session['rbActionSucceeded'] = False
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors
            session['rbShowErrors'] = True
            session['rbThereAreConflicts'] = True

            session['rbTitle'] = _("PRE-Booking conflicts with other (confirmed) bookings.")
            session['rbDescription'] = ""

            self._formMode = FormMode.MODIF
            self._saveResvCandidateToSession(self._resv)
            url = urlHandlers.UHRoomBookingBookingForm.getURL(self._resv.room)
            self._redirect(url)  # Redirect to booking details

        for notification in emailsToBeSent:
            GenericMailer.send(notification)


class RHRoomBookingCancelBooking(RHRoomBookingBase):
    def _checkParams(self, params):
        resvID = int(params.get("resvID"))
        roomLocation = params.get("roomLocation")
        self._resv = CrossLocationQueries.getReservations(resvID=resvID, location=roomLocation)
        self._target = self._resv

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only owner (the one who created), the requestor(booked for) and admin can CANCEL
        # (Responsible can not cancel a booking!)
        if not self._resv.canCancel(user):
            raise MaKaCError("You are not authorized to take this action.")

    def _process(self):
        # Booking deletion is always possible - just delete
        self._resv.cancel()  # Just sets isCancel = True
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutCancellation()

        # Add entry to the booking history
        info = []
        info.append("Booking cancelled")
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Booking has been cancelled.")
        session['rbDescription'] = _("You have successfully cancelled the booking.")
        url = urlHandlers.UHRoomBookingBookingDetails.getURL(self._resv)
        self._redirect(url)  # Redirect to booking details


class RHRoomBookingRejectBooking(RHRoomBookingBase):
    def _checkParams(self, params):
        resvID = int(params.get("resvID"))
        roomLocation = params.get("roomLocation")
        reason = params.get("reason")

        self._resv = CrossLocationQueries.getReservations(resvID=resvID, location=roomLocation)
        self._resv.rejectionReason = reason
        self._target = self._resv

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if not self._resv.room.isOwnedBy(user) and not self._getUser().isRBAdmin():
            raise MaKaCError("You are not authorized to take this action.")

    def _process(self):
        self._resv.reject()  # Just sets isRejected = True
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutRejection()

        # Add entry to the booking history
        info = []
        info.append("Booking rejected")
        info.append("Reason : '%s'" % self._resv.rejectionReason)
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Booking has been rejected.")
        session['rbDescription'] = _(
            "NOTE: rejection e-mail has been sent to the user. However, it's advisable to <strong>inform</strong> the user directly. Note that users often don't read e-mails.")
        url = urlHandlers.UHRoomBookingBookingDetails.getURL(self._resv)
        self._redirect(url)  # Redirect to booking details


class RHRoomBookingCloneBooking(RHRoomBookingBase):
    """
    Performs open a new booking form with the data of an already existing booking.
    """

    def _checkParams(self, params):
        # DATA FROM
        session['rbCandDataInSession'] = True

        self._formMode = FormMode.NEW

        # Reservation ID
        resvID = int(params.get("resvID"))

        # CREATE CANDIDATE OBJECT
        candResv = CrossLocationQueries.getReservations(resvID=resvID)
        if type(candResv) == list:
            candResv = candResv[0]
        self._saveResvCandidateToSession(candResv)
        self._room = candResv.room

    def _process(self):
        self._redirect(urlHandlers.UHRoomBookingBookingForm.getURL(self._room))


class RHRoomBookingCancelBookingOccurrence(RHRoomBookingBase):
    def _checkParams(self, params):
        resvID = int(params.get("resvID"))
        roomLocation = params.get("roomLocation")
        date = params.get("date")

        self._resv = CrossLocationQueries.getReservations(resvID=resvID, location=roomLocation)
        self._date = parse_date(date)
        self._target = self._resv

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only owner (the one who created), the requestor(booked for) and admin can CANCEL
        # (Owner can not reject his own booking, he should cancel instead)
        if not self._resv.canCancel(user):
            raise MaKaCError("You are not authorized to take this action.")

    def _process(self):
        self._resv.excludeDay(self._date, unindex=True)
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutCancellation(date=self._date)

        # Add entry to the booking history
        info = []
        info.append("Booking occurence of the %s cancelled" % self._date.strftime("%d %b %Y"))
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Selected occurrence has been cancelled.")
        session['rbDescription'] = _("You have successfully cancelled an occurrence of this booking.")
        url = urlHandlers.UHRoomBookingBookingDetails.getURL(self._resv)
        self._redirect(url)  # Redirect to booking details


class RHRoomBookingRejectBookingOccurrence(RHRoomBookingBase):
    def _checkParams(self, params):
        resvID = int(params.get("resvID"))
        roomLocation = params.get("roomLocation")
        reason = params.get("reason")
        date = params.get("date")

        self._resv = CrossLocationQueries.getReservations(resvID=resvID, location=roomLocation)
        self._rejectionReason = reason
        self._date = parse_date(date)
        self._target = self._resv

    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if not self._resv.room.isOwnedBy(user) and not self._getUser().isRBAdmin():
            raise MaKaCError("You are not authorized to take this action.")

    def _process(self):
        self._resv.excludeDay(self._date, unindex=True)
        self._resv.update()
        emailsToBeSent = self._resv.notifyAboutRejection(date=self._date, reason=self._rejectionReason)

        # Add entry to the booking history
        info = []
        info.append("Booking occurence of the %s rejected" % self._date.strftime("%d %b %Y"))
        info.append("Reason : '%s'" % self._rejectionReason)
        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
        self._resv.getResvHistory().addHistoryEntry(histEntry)

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

        session['rbActionSucceeded'] = True
        session['rbTitle'] = _("Selected occurrence of this booking has been rejected.")
        session['rbDescription'] = _("NOTE: rejection e-mail has been sent to the user.")
        url = urlHandlers.UHRoomBookingBookingDetails.getURL(self._resv)
        self._redirect(url)  # Redirect to booking details


class RHRoomBookingRejectAllConflicting(RHRoomBookingBase):
    def _checkProtection(self):
        RHRoomBookingBase._checkProtection(self)
        user = self._getUser()
        # Only responsible and admin can REJECT
        # (Owner can not reject his own booking, he should cancel instead)
        if not user.getRooms() and not self._getUser().isRBAdmin():
            raise MaKaCError("You are not authorized to take this action.")

    def _process(self):
        userRooms = self._getUser().getRooms()
        emailsToBeSent = []

        resvEx = ReservationBase()
        resvEx.isConfirmed = False
        resvEx.isRejected = False
        resvEx.isCancelled = False

        resvs = CrossLocationQueries.getReservations(resvExample=resvEx, rooms=userRooms)

        counter = 0
        for resv in resvs:
            # There's a big difference between 'isConfirmed' being None and False. This value needs to be
            # changed to None and after the search reverted to the previous value. For further information,
            # please take a look at the comment in rb_reservation.py::ReservationBase.getCollisions method
            tmpConfirmed = resv.isConfirmed
            resv.isConfirmed = None
            if resv.getCollisions(sansID=resv.id, boolResult=True):
                resv.rejectionReason = "Your PRE-booking conflicted with exiting booking. (Please note it IS possible even if you were the first one to PRE-book the room)."
                resv.reject()  # Just sets isRejected = True
                resv.update()
                emailsToBeSent += resv.notifyAboutRejection()
                counter += 1
                # Add entry to the history of the rejected reservation
                info = []
                info.append("Booking rejected due to conflict with existing booking")
                histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
                resv.getResvHistory().addHistoryEntry(histEntry)
            resv.isConfirmed = tmpConfirmed
        session['rbPrebookingsRejected'] = True
        if counter > 0:
            session['rbTitle'] = _("%d conflicting PRE-bookings have been rejected.") % counter
            session['rbDescription'] = _(
                "Rejection e-mails have been sent to the users, with explanation that their PRE-bookings conflicted with the present confirmed bookings.")
        else:
            session['rbTitle'] = _("There are no conflicting PRE-bookings for your rooms.")
            session['rbDescription'] = ""
        for notification in emailsToBeSent:
            GenericMailer.send(notification)
        url = urlHandlers.UHRoomBookingBookingList.getURL(ofMyRooms=True, onlyPrebookings=True, autoCriteria=True)
        self._redirect(url)  # Redirect to booking details
