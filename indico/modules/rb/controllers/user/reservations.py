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

from flask import request, session
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from werkzeug.datastructures import MultiDict
from indico.core.db import db

from indico.core.errors import IndicoError, FormValuesError
from indico.modules.rb.models.blockings import Blocking
from indico.util.date_time import server_to_utc, get_datetime_from_request
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.controllers.forms import (BookingSearchForm, NewBookingCriteriaForm, NewBookingPeriodForm,
                                                 FormDefaults, NewBookingConfirmForm)
from indico.modules.rb.models.reservations import Reservation, RepeatMapping
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.utils import getRoomBookingOption
from indico.modules.rb.views.user import reservations as reservation_views
from indico.modules.rb.views.user.reservations import (WPRoomBookingSearchBookings, WPRoomBookingSearchBookingsResults,
                                                       WPRoomBookingCalendar, WPRoomBookingNewBookingSelectRoom,
                                                       WPRoomBookingNewBookingSelectPeriod,
                                                       WPRoomBookingNewBookingConfirm)
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


class RHRoomBookingNewBooking(RHRoomBookingBase):
    def _checkParams(self):
        try:
            self._step = int(request.form.get('step', 1))
        except ValueError:
            self._step = 1

    def _make_select_room_form(self):
        # Step 1
        self._rooms = sorted(Room.find_all(is_active=True), key=lambda r: natural_sort_key(r.getFullName()))
        form = NewBookingCriteriaForm()
        form.room_ids.choices = [(r.id, None) for r in self._rooms]
        return form

    def _make_select_period_form(self, defaults=None):
        # Step 2
        # If we come from a successful step 1 submission we use the default values provided by that step.
        if self._step == 1:
            return NewBookingPeriodForm(formdata=MultiDict(), obj=defaults)
        else:
            return NewBookingPeriodForm()

    def _make_confirm_form(self, room, defaults=None):
        # Step 3
        # If we come from a successful step 2 we take default values from that step once again
        if self._step == 2:
            defaults.equipments = []  # wtforms bug; avoid `foo in None` check
            form = NewBookingConfirmForm(formdata=MultiDict(), obj=defaults)
        else:
            form = NewBookingConfirmForm()

        form.equipments.query = room.find_available_video_conference()
        return form

    def _process_select_room(self):
        # Step 1: Room(s), dates, repetition selection
        form = self._make_select_room_form()
        if form.validate_on_submit():
            flexible_days = form.flexible_dates_range.data
            day_start_dt = datetime.combine(form.start_date.data.date(), time())
            day_end_dt = datetime.combine(form.end_date.data.date(), time(23, 59))

            occurrences = ReservationOccurrence.find_all(
                Reservation.room_id.in_(form.room_ids.data),
                ReservationOccurrence.start >= server_to_utc(day_start_dt) - timedelta(days=flexible_days),
                ReservationOccurrence.end <= server_to_utc(day_end_dt) + timedelta(days=flexible_days),
                ~ReservationOccurrence.is_cancelled,
                _join=Reservation,
                _eager=ReservationOccurrence.reservation
            )

            candidates = {}
            for days in xrange(-flexible_days, flexible_days + 1):
                offset = timedelta(days=days)
                series_start = server_to_utc(form.start_date.data) + offset
                series_end = server_to_utc(form.end_date.data) + offset
                candidates[series_start, series_end] = ReservationOccurrence.create_series(series_start, series_end,
                                                                                           (form.repeat_unit.data,
                                                                                            form.repeat_step.data))

            selected_rooms = [r for r in self._rooms if r.id in form.room_ids.data]
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
        return WPRoomBookingNewBookingSelectRoom(self, errors=form.error_list, rooms=self._rooms,
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
            return self._show_confirm(room, form, confirm_form_defaults)

    def _show_confirm(self, room, form, defaults=None):
        # form can be PeriodForm or Confirmform depending on the step we come from
        if self._step == 2:
            confirm_form = self._make_confirm_form(room, defaults)
        else:
            # Step3 => Step3 due to an error in the form
            confirm_form = form

        repeat_msg = RepeatMapping.getMessage(form.repeat_unit.data, form.repeat_step.data)
        prebook_only = not room.can_be_booked(session.user) and room.can_be_prebooked(session.user)
        return WPRoomBookingNewBookingConfirm(self, form=confirm_form, room=room, start_dt=form.start_date.data,
                                              end_dt=form.end_date.data, repeat_unit=form.repeat_unit.data,
                                              repeat_step=form.repeat_step.data, repeat_msg=repeat_msg,
                                              prebook_only=prebook_only,
                                              errors=confirm_form.error_list).display()

    def _process_confirm(self):
        # The form needs the room to create the equipment list, so we need to get it "manually"...
        room = Room.get(int(request.form['room_id']))
        form = self._make_confirm_form(room)
        if form.validate_on_submit():
            booking = self._create_booking(form, room)
            url = url_for('rooms.roomBooking-bookingDetails', booking)
            self._redirect(url)
            return
        # There was an error in the form
        return self._show_confirm(room, form)

    def _create_booking(self, form, room):
        reservation = Reservation.create_from_form(room, form, session.user)
        db.session.add(reservation)
        db.session.flush()
        return reservation

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
    def _checkParams(self):
        self._form = ReservationForm(prefix='reservation')
        self._room = Room.getRoomById(int(request.values.get('roomID')))
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

        start_dt = server_to_utc(self._form.start_date.data)
        end_dt = server_to_utc(self._form.end_date.data)

        day_start_dt = server_to_utc(datetime.combine(self._form.start_date.data.date(), time()))
        day_end_dt = server_to_utc(datetime.combine(self._form.end_date.data.date(), time(23, 59)))

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
                ReservationOccurrence.start >= server_to_utc(self.start_dt),
                ReservationOccurrence.end <= server_to_utc(self.end_dt),
                ~ReservationOccurrence.is_cancelled,
                _join=Reservation,
                _eager=ReservationOccurrence.reservation
            )

        return WPRoomBookingCalendar(self, rooms=rooms, occurrences=occurrences, start_dt=self.start_dt,
                                     end_dt=self.end_dt, overload=self._overload, max_days=self.MAX_DAYS).display()


class RHRoomBookingSaveBooking(RHRoomBookingBase):
    """
    Performs physical INSERT or UPDATE.
    When succeeded redirects to booking details, otherwise returns to booking
    form.
    """

    def _checkParams(self, params):

        self._roomLocation = params.get("roomLocation")
        self._roomID = params.get("roomID")
        self._resvID = params.get("resvID")
        if self._resvID == 'None':
            self._resvID = None

        # if the user is not logged in it will be redirected
        # to the login page by the _checkProtection, so we don't
        # need to store info in the session or process the other params
        if not self._getUser():
            return

        self._answer = params.get("answer", None)

        self._skipConflicting = False

        # forceAddition is set by the confirmation dialog, so that
        # prebookings that conflict with other prebookings are
        # silently added

        self._forceAddition = params.get("forceAddition", "False")
        if self._forceAddition == 'True':
            self._forceAddition = True
        else:
            self._forceAddition = False

        candResv = None
        if self._resvID:
            self._formMode = FormMode.MODIF
            self._resvID = int(self._resvID)
            _candResv = CrossLocationQueries.getReservations(resvID=self._resvID, location=self._roomLocation)
            self._orig_candResv = _candResv

            # Creates a "snapshot" of the reservation's attributes before modification
            self._resvAttrsBefore = self._orig_candResv.createSnapshot()

            import copy

            candResv = copy.copy(_candResv)

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession(candResv, params)
            else:
                self._loadResvCandidateFromParams(candResv, params)

            # Creates a "snapshot" of the reservation's attributes after modification
            self._resvAttrsAfter = candResv.createSnapshot()

        else:
            self._formMode = FormMode.NEW
            candResv = Location.parse(self._roomLocation).factory.newReservation()
            candResv.createdDT = datetime.now()
            candResv.createdBy = str(self._getUser().id)
            candResv.isRejected = False
            candResv.isCancelled = False

            if self._forceAddition:
                # booking data comes from session if confirmation was required
                self._loadResvCandidateFromSession(candResv, params)
            else:
                self._loadResvCandidateFromParams(candResv, params)

            self._resvID = None

        user = self._getUser()
        self._candResv = candResv

        if not (user.isAdmin() or user.isRBAdmin()):
            for nbd in self._candResv.room.getNonBookableDates():
                if nbd.doesPeriodOverlap(self._candResv.startDT, self._candResv.endDT):
                    raise FormValuesError(_("You cannot book this room during the following periods: %s") % ("; ".join(
                        map(lambda x: "from %s to %s" % (
                            x.getStartDate().strftime("%d/%m/%Y (%H:%M)"), x.getEndDate().strftime("%d/%m/%Y (%H:%M)")),
                            self._candResv.room.getNonBookableDates()))))

            if self._candResv.room.getDailyBookablePeriods():
                for nbp in self._candResv.room.getDailyBookablePeriods():
                    if nbp.doesPeriodFit(self._candResv.startDT.time(), self._candResv.endDT.time()):
                        break
                else:
                    raise FormValuesError(_("You must book this room in one of the following time periods: %s") % (
                        ", ".join(map(lambda x: "from %s to %s" % (x.getStartTime(), x.getEndTime()),
                                      self._candResv.room.getDailyBookablePeriods()))))

        days = self._candResv.room.maxAdvanceDays
        if not (user.isRBAdmin() or user.getId() == self._candResv.room.responsibleId) and days > 0:
            if dateAdvanceAllowed(self._candResv.endDT, days):
                raise FormValuesError(_("You cannot book this room more than %s days in advance.") % days)

        self._params = params
        self._clearSessionState()

    def _checkProtection(self):
        # If the user is not logged in, we redirect the same reservation page
        if not self._getUser():
            self._redirect(urlHandlers.UHSignIn.getURL(
                returnURL=urlHandlers.UHRoomBookingBookingForm.getURL(
                    roomID=self._roomID,
                    resvID=self._resvID,
                    roomLocation=self._roomLocation)))
            self._doProcess = False
        else:
            RHRoomBookingBase._checkProtection(self)
            if not self._candResv.room.isActive and not self._getUser().isRBAdmin():
                raise MaKaCError("You are not authorized to book this room.")

            if self._formMode == FormMode.MODIF:
                if not self._orig_candResv.canModify(self.getAW()):
                    raise MaKaCError("You are not authorized to take this action.")

    def _businessLogic(self):

        candResv = self._candResv
        emailsToBeSent = []
        self._confirmAdditionFirst = False

        # Set confirmation status
        candResv.isConfirmed = True
        user = self._getUser()
        if not candResv.room.canBook(user):
            candResv.isConfirmed = False

        errors = self._getErrorsOfResvCandidate(candResv)

        if not errors and self._answer != 'No':

            isConfirmed = candResv.isConfirmed
            candResv.isConfirmed = None
            # find pre-booking collisions
            self._collisions = candResv.getCollisions(sansID=candResv.id)
            candResv.isConfirmed = isConfirmed

            if not self._forceAddition and self._collisions:
                # save the reservation to the session
                self._saveResvCandidateToSession(candResv)
                # ask for confirmation about the pre-booking
                self._confirmAdditionFirst = True


            # approved pre-booking or booking
            if not self._confirmAdditionFirst:

                # Form is OK and (no conflicts or skip conflicts)
                if self._formMode == FormMode.NEW:
                    candResv.insert()
                    emailsToBeSent += candResv.notifyAboutNewReservation()
                    if candResv.isConfirmed:
                        session['rbTitle'] = _('You have successfully made a booking.')
                        session['rbDescription'] = _(
                            'NOTE: Your booking is complete. However, be <b>aware</b> that in special cases the person responsible for a room may reject your booking. In that case you would be instantly notified by e-mail.')
                    else:
                        session['rbTitle'] = _(
                            'You have successfully made a <span style="color: Red;">PRE</span>-booking.')
                        session['rbDescription'] = _(
                            'NOTE: PRE-bookings are subject to acceptance or rejection. Expect an e-mail with acceptance/rejection information.')
                elif self._formMode == FormMode.MODIF:
                    self._orig_candResv.unindexDayReservations()
                    self._orig_candResv.clearCalendarCache()
                    if self._forceAddition:
                        self._loadResvCandidateFromSession(self._orig_candResv, self._params)
                    else:
                        self._loadResvCandidateFromParams(self._orig_candResv, self._params)
                    self._orig_candResv.update()
                    self._orig_candResv.indexDayReservations()
                    emailsToBeSent += self._orig_candResv.notifyAboutUpdate(self._resvAttrsBefore)

                    # Add entry to the log
                    info = []
                    self._orig_candResv.getResvHistory().getResvModifInfo(info, self._resvAttrsBefore,
                                                                          self._resvAttrsAfter)

                    # If no modification was observed ("Save" was pressed but no field
                    # was changed) no entry is added to the log
                    if len(info) > 1:
                        histEntry = ResvHistoryEntry(self._getUser(), info, emailsToBeSent)
                        self._orig_candResv.getResvHistory().addHistoryEntry(histEntry)

                    session['rbTitle'] = _('Booking updated.')
                    session['rbDescription'] = _('Please review details below.')

                session['rbActionSucceeded'] = True

                # Booking - reject all colliding PRE-Bookings
                if candResv.isConfirmed and self._collisions:
                    rejectionReason = "Conflict with booking: %s" % urlHandlers.UHRoomBookingBookingDetails.getURL(
                        candResv)
                    for coll in self._collisions:
                        collResv = coll.withReservation
                        if collResv.repeatability is None:  # not repeatable -> reject whole booking. easy :)
                            collResv.rejectionReason = rejectionReason
                            collResv.reject()  # Just sets isRejected = True
                            collResv.update()
                            emails = collResv.notifyAboutRejection()
                            emailsToBeSent += emails

                            # Add entry to the booking history
                            info = []
                            info.append("Booking rejected")
                            info.append("Reason: '%s'" % collResv.rejectionReason)
                            histEntry = ResvHistoryEntry(self._getUser(), info, emails)
                            collResv.getResvHistory().addHistoryEntry(histEntry)
                        else:  # repeatable -> only reject the specific days
                            rejectDate = coll.startDT.date()
                            collResv.excludeDay(rejectDate, unindex=True)
                            collResv.update()
                            emails = collResv.notifyAboutRejection(date=rejectDate, reason=rejectionReason)
                            emailsToBeSent += emails

                            # Add entry to the booking history
                            info = []
                            info.append("Booking occurence of the %s rejected" % rejectDate.strftime("%d %b %Y"))
                            info.append("Reason: '%s'" % rejectionReason)
                            histEntry = ResvHistoryEntry(self._getUser(), info, emails)
                            collResv.getResvHistory().addHistoryEntry(histEntry)

        else:
            session['rbCandDataInSession'] = True
            session['rbErrors'] = errors

            if self._answer == 'No':
                session['rbActionSucceeded'] = True
            else:
                session['rbActionSucceeded'] = False
                session['rbShowErrors'] = True
                session['rbThereAreConflicts'] = self._thereAreConflicts

            self._saveResvCandidateToSession(candResv)

        # Form is not properly filled OR there are conflicts
        self._errors = errors

        for notification in emailsToBeSent:
            GenericMailer.send(notification)

    def _process(self):

        self._businessLogic()

        if self._errors or self._answer == 'No':
            url = urlHandlers.UHRoomBookingBookingForm.getURL(self._candResv.room, resvID=self._resvID,
                                                              infoBookingMode=True)
        elif self._confirmAdditionFirst:
            p = roomBooking_wp.WPRoomBookingConfirmBooking(self)
            return p.display()
        else:
            url = urlHandlers.UHRoomBookingBookingDetails.getURL(self._candResv)

        self._redirect(url)


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


class RHRoomBookingRejectALlConflicting(RHRoomBookingBase):
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
