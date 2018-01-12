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

from collections import defaultdict
from datetime import date, datetime, time, timedelta

import dateutil
from flask import flash, jsonify, redirect, request, session
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.core.errors import IndicoError, NoReportError
from indico.modules.rb import rb_settings
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.forms.reservations import (BookingSearchForm, ModifyBookingForm, NewBookingConfirmForm,
                                                  NewBookingCriteriaForm, NewBookingPeriodForm, NewBookingSimpleForm)
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import RepeatMapping, Reservation
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.util import get_default_booking_interval, rb_is_admin
from indico.modules.rb.views.user.reservations import (WPRoomBookingBookingDetails, WPRoomBookingCalendar,
                                                       WPRoomBookingModifyBooking, WPRoomBookingNewBookingConfirm,
                                                       WPRoomBookingNewBookingSelectPeriod,
                                                       WPRoomBookingNewBookingSelectRoom, WPRoomBookingNewBookingSimple,
                                                       WPRoomBookingSearchBookings, WPRoomBookingSearchBookingsResults)
from indico.util.date_time import get_datetime_from_request, round_up_to_minutes
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHRoomBookingBookingMixin:
    """Mixin that retrieves the booking or fails if there is none."""
    def _process_args(self):
        self._reservation = Reservation.get_one(request.view_args['resvID'])


class RHRoomBookingBookingDetails(RHRoomBookingBookingMixin, RHRoomBookingBase):
    def _get_view(self, **kwargs):
        return WPRoomBookingBookingDetails(self, **kwargs)

    def _process(self):
        return self._get_view(reservation=self._reservation).display()


class _SuccessUrlDetailsMixin:
    def _get_success_url(self):
        return url_for('rooms.roomBooking-bookingDetails', self._reservation)


class RHRoomBookingAcceptBooking(_SuccessUrlDetailsMixin, RHRoomBookingBookingMixin, RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self._reservation.can_be_accepted(session.user):
            raise Forbidden("You are not authorized to perform this action")

    def _process(self):
        if self._reservation.find_overlapping().filter(Reservation.is_accepted).count():
            raise IndicoError(_(u"This reservation couldn't be accepted due to conflicts with other reservations"))
        if self._reservation.is_pending:
            self._reservation.accept(session.user)
            flash(_(u'Booking accepted'), 'success')
        return redirect(self._get_success_url())


class RHRoomBookingCancelBooking(_SuccessUrlDetailsMixin, RHRoomBookingBookingMixin, RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self._reservation.can_be_cancelled(session.user):
            raise Forbidden("You are not authorized to perform this action")

    def _process(self):
        if not self._reservation.is_cancelled and not self._reservation.is_rejected:
            self._reservation.cancel(session.user)
            flash(_(u'Booking cancelled'), 'success')
        return redirect(self._get_success_url())


class RHRoomBookingRejectBooking(_SuccessUrlDetailsMixin, RHRoomBookingBookingMixin, RHRoomBookingBase):
    def _process_args(self):
        RHRoomBookingBookingMixin._process_args(self)
        self._reason = request.form.get('reason', u'')

    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self._reservation.can_be_rejected(session.user):
            raise Forbidden("You are not authorized to perform this action")

    def _process(self):
        if not self._reservation.is_cancelled and not self._reservation.is_rejected:
            self._reservation.reject(session.user, self._reason)
            flash(_(u'Booking rejected'), 'success')
        return redirect(self._get_success_url())


class RHRoomBookingCancelBookingOccurrence(_SuccessUrlDetailsMixin, RHRoomBookingBookingMixin, RHRoomBookingBase):
    def _process_args(self):
        RHRoomBookingBookingMixin._process_args(self)
        occ_date = dateutil.parser.parse(request.view_args['date'], yearfirst=True).date()
        self._occurrence = self._reservation.occurrences.filter(ReservationOccurrence.date == occ_date).one()

    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self._reservation.can_be_cancelled(session.user):
            raise Forbidden("You are not authorized to perform this action")

    def _process(self):
        if self._occurrence.is_valid:
            self._occurrence.cancel(session.user)
            flash(_(u'Booking occurrence cancelled'), 'success')
        return redirect(self._get_success_url())


class RHRoomBookingRejectBookingOccurrence(_SuccessUrlDetailsMixin, RHRoomBookingBookingMixin, RHRoomBookingBase):
    def _process_args(self):
        RHRoomBookingBookingMixin._process_args(self)
        occ_date = dateutil.parser.parse(request.view_args['date'], yearfirst=True).date()
        self._reason = request.form.get('reason', u'')
        self._occurrence = self._reservation.occurrences.filter(ReservationOccurrence.date == occ_date).one()

    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self._reservation.can_be_rejected(session.user):
            raise Forbidden("You are not authorized to perform this action")

    def _process(self):
        if self._occurrence.is_valid:
            self._occurrence.reject(session.user, self._reason)
            flash(_(u'Booking occurrence rejected'), 'success')
        return redirect(self._get_success_url())


class RHRoomBookingSearchBookings(RHRoomBookingBase):
    menu_item = 'search_bookings'
    show_blockings = True
    CSRF_ENABLED = False

    def _get_form_data(self):
        return request.form

    def _filter_displayed_rooms(self, rooms, occurrences):
        return rooms

    def _process_args(self):
        self._rooms = sorted(Room.find_all(is_active=True), key=lambda r: natural_sort_key(r.full_name))
        self._form_data = self._get_form_data()
        self._form = BookingSearchForm(self._form_data, csrf_enabled=False)
        self._form.room_ids.choices = [(r.id, None) for r in self._rooms]

    def _is_submitted(self):
        return self._form.is_submitted()

    def _process(self):
        form = self._form
        if self._is_submitted() and form.validate():
            if form.data.get('is_only_my_rooms'):
                form.room_ids.data = [room.id for room in Room.find_all() if room.is_owned_by(session.user)]

            occurrences = ReservationOccurrence.find_with_filters(form.data, session.user).all()
            rooms = self._filter_displayed_rooms([r for r in self._rooms if r.id in set(form.room_ids.data)],
                                                 occurrences)
            return WPRoomBookingSearchBookingsResults(self, rooms=rooms, occurrences=occurrences,
                                                      show_blockings=self.show_blockings,
                                                      start_dt=form.start_dt.data, end_dt=form.end_dt.data,
                                                      form=form, form_data=self._form_data,
                                                      menu_item=self.menu_item).display()

        my_rooms = [r.id for r in Room.get_owned_by(session.user)]
        return WPRoomBookingSearchBookings(self, errors=form.error_list, rooms=self._rooms, my_rooms=my_rooms,
                                           form=form).display()


class RHRoomBookingSearchBookingsShortcutBase(RHRoomBookingSearchBookings):
    """Base class for searches with predefined criteria"""
    search_criteria = {}
    show_blockings = False

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


class _RoomsWithBookingsMixin:
    def _filter_displayed_rooms(self, rooms, occurrences):
        booked_rooms = {occ.reservation.room_id for occ in occurrences}
        return [r for r in rooms if r.id in booked_rooms]


class _MyRoomsMixin:
    def _filter_displayed_rooms(self, rooms, occurrences):
        return [r for r in rooms if r.is_owned_by(session.user)]


class RHRoomBookingSearchMyBookings(_RoomsWithBookingsMixin, RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'my_bookings'
    search_criteria = {
        'is_only_mine': True
    }


class RHRoomBookingSearchBookingsMyRooms(_MyRoomsMixin, RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'bookings_in_my_rooms'
    search_criteria = {
        'is_only_my_rooms': True
    }


class RHRoomBookingSearchPendingBookingsMyRooms(_MyRoomsMixin, RHRoomBookingSearchBookingsShortcutBase):
    menu_item = 'prebookings_in_my_rooms'
    search_criteria = {
        'is_only_my_rooms': True,
        'is_only_pending_bookings': True
    }


class RHRoomBookingNewBookingBase(RHRoomBookingBase):
    DEFAULT_START_TIME_PRECISION = 15  # minutes
    DEFAULT_BOOKING_DURATION = 90  # minutes

    def _make_confirm_form(self, room, step=None, defaults=None, form_class=NewBookingConfirmForm):
        # Note: ALWAYS pass defaults as a kwargs! For-Event room booking depends on it!
        # Step 3
        # If we come from a successful step 2 we take default values from that step once again
        if step == 2:
            defaults.used_equipment = []  # wtforms bug; avoid `foo in None` check
            form = form_class(formdata=MultiDict(), obj=defaults)
        else:
            form = form_class(obj=defaults)

        if not room.notification_for_assistance:
            del form.needs_assistance

        can_book = room.can_be_booked(session.user)
        can_prebook = room.can_be_prebooked(session.user)
        if room.is_auto_confirm or (not can_prebook or (can_book and room.can_be_booked(session.user, True))):
            # The user has actually the permission to book (not just because he's an admin)
            # Or he simply can't even prebook the room
            del form.submit_prebook
        if not can_book:
            # User can only prebook
            del form.submit_book

        form.used_equipment.query = room.find_available_vc_equipment()
        return form

    def _get_all_conflicts(self, room, form, reservation_id=None):
        conflicts = defaultdict(list)
        pre_conflicts = defaultdict(list)

        candidates = ReservationOccurrence.create_series(form.start_dt.data, form.end_dt.data,
                                                         (form.repeat_frequency.data, form.repeat_interval.data))
        occurrences = ReservationOccurrence.find_overlapping_with(room, candidates, reservation_id).all()

        for cand in candidates:
            for occ in occurrences:
                if cand.overlaps(occ):
                    if occ.reservation.is_accepted:
                        conflicts[cand].append(occ)
                    else:
                        pre_conflicts[cand].append(occ)

        return conflicts, pre_conflicts

    def _get_all_occurrences(self, room_ids, form, flexible_days=0, reservation_id=None):
        start_dt = form.start_dt.data
        end_dt = form.end_dt.data
        repeat_frequency = form.repeat_frequency.data
        repeat_interval = form.repeat_interval.data
        day_start_dt = datetime.combine(start_dt.date(), time())
        day_end_dt = datetime.combine(end_dt.date(), time(23, 59))
        flexible_start_dt = day_start_dt - timedelta(days=flexible_days)
        flexible_end_dt = day_end_dt + timedelta(days=flexible_days)

        occurrences = ReservationOccurrence.find(
            Reservation.room_id.in_(room_ids),
            Reservation.id != reservation_id,
            ReservationOccurrence.start_dt >= flexible_start_dt,
            ReservationOccurrence.end_dt <= flexible_end_dt,
            ReservationOccurrence.is_valid,
            _join=ReservationOccurrence.reservation,
            _eager=ReservationOccurrence.reservation
        ).options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY).all()

        candidates = {}
        for days in xrange(-flexible_days, flexible_days + 1):
            offset = timedelta(days=days)
            series_start = start_dt + offset
            series_end = end_dt + offset
            if series_start < flexible_start_dt:
                continue
            candidates[series_start, series_end] = ReservationOccurrence.create_series(series_start, series_end,
                                                                                       (repeat_frequency,
                                                                                        repeat_interval))
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

    def _get_success_url(self, booking):
        return url_for('rooms.roomBooking-bookingDetails', booking)

    def _create_booking_response(self, form, room):
        """Creates the booking and returns a JSON response."""
        try:
            booking = self._create_booking(form, room)
        except NoReportError as e:
            db.session.rollback()
            return jsonify(success=False, msg=unicode(e))
        flash(_(u'Pre-Booking created') if booking.is_pending else _(u'Booking created'), 'success')
        return jsonify(success=True, url=self._get_success_url(booking))

    def _validate_room_booking_limit(self, form, booking_limit_days):
        day_start_dt = datetime.combine(form.start_dt.data.date(), time())
        day_end_dt = datetime.combine(form.end_dt.data.date(), time(23, 59))
        selected_period_days = (day_end_dt - day_start_dt).days
        return selected_period_days <= booking_limit_days


class RHRoomBookingNewBookingSimple(RHRoomBookingNewBookingBase):
    def _process_args(self):
        self._room = Room.get(int(request.view_args['roomID']))
        if self._room is None:
            raise NotFound(u'This room does not exist')

    def _make_form(self):
        start_date = None
        force_today = False
        if 'start_date' in request.args:
            force_today = True
            try:
                start_date = datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
            else:
                if not self._room.check_advance_days(start_date, user=session.user, quiet=True):
                    start_date = date.today()
                    flash(_(u"This room cannot be booked at the desired date, using today's date instead."), 'warning')

        self.past_date = start_date is not None and start_date < date.today()
        if start_date is None or start_date <= date.today():
            start_dt, end_dt, self.date_changed = get_default_booking_interval(
                duration=self.DEFAULT_BOOKING_DURATION,
                precision=self.DEFAULT_START_TIME_PRECISION,
                force_today=force_today
            )
            self.date_changed = self.date_changed and not self.past_date
        else:
            start_dt = datetime.combine(start_date, Location.working_time_start)
            end_dt = datetime.combine(start_date, Location.working_time_end)
            self.date_changed = False
        defaults = FormDefaults(room_id=self._room.id,
                                start_dt=start_dt,
                                end_dt=end_dt)
        return self._make_confirm_form(self._room, defaults=defaults, form_class=NewBookingSimpleForm)

    def _get_view(self, **kwargs):
        return WPRoomBookingNewBookingSimple(self, **kwargs)

    def _process(self):
        room = self._room
        rooms = Room.find_all()
        form = self._make_form()

        if form.is_submitted() and not form.validate():
            occurrences = {}
            candidates = {}
            conflicts = {}
            pre_conflicts = {}
            only_conflicts = False
        else:
            occurrences, candidates = self._get_all_occurrences([self._room.id], form)
            conflicts, pre_conflicts = self._get_all_conflicts(self._room, form)
            candidate_days = {occ.date for candidate in candidates.itervalues() for occ in candidate}
            conflicting_days = {occ.date for occ in conflicts.iterkeys()}
            only_conflicts = candidate_days <= conflicting_days

        if form.validate_on_submit() and not form.submit_check.data:
            booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
            if not self._validate_room_booking_limit(form, booking_limit_days):
                msg = (_(u'Bookings for the room "{}" may not be longer than {} days')
                       .format(room.name, booking_limit_days))
                return jsonify(success=False, url=url_for('rooms.room_book', room), msg=msg)
            return self._create_booking_response(form, room)

        can_override = room.can_be_overridden(session.user)
        return self._get_view(form=form,
                              room=room,
                              rooms=rooms,
                              occurrences=occurrences,
                              candidates=candidates,
                              conflicts=conflicts,
                              only_conflicts=only_conflicts,
                              pre_conflicts=pre_conflicts,
                              start_dt=form.start_dt.data,
                              end_dt=form.end_dt.data,
                              repeat_frequency=form.repeat_frequency.data,
                              repeat_interval=form.repeat_interval.data,
                              can_override=can_override,
                              past_date=not form.is_submitted() and self.past_date,
                              date_changed=not form.is_submitted() and self.date_changed).display()


class RHRoomBookingCloneBooking(RHRoomBookingBookingMixin, RHRoomBookingNewBookingSimple):
    def _process_args(self):
        RHRoomBookingBookingMixin._process_args(self)

        # use 'room' if passed through GET
        room_id = request.args.get('room', None)

        if room_id is None:
            # otherwise default to reservation's
            self._room = self._reservation.room
        else:
            self._room = Room.get(int(room_id))

        if self._room is None:
            raise NotFound(u'This room does not exist')

    def _get_view(self, **kwargs):
        return RHRoomBookingNewBookingSimple._get_view(self, clone_booking=self._reservation, **kwargs)

    def _update_datetime(self):
        """Make necessary changes to reservation's start and end datetime.

        Move the start date to the current day, adjust the end date
        accordingly and if the start datetime is still in the past, change the
        start and end time to the current (rounded up) time.

        :return: A dict with the new start and end datetime
        """
        reservation_duration = self._reservation.end_dt - self._reservation.start_dt
        date_delta = date.today() - self._reservation.start_dt.date()
        start_dt = self._reservation.start_dt + date_delta
        end_dt = start_dt + reservation_duration
        if start_dt < datetime.now():
            new_start_dt = round_up_to_minutes(datetime.now(), 15) + timedelta(minutes=15)
            time_delta = new_start_dt - start_dt
            start_dt = new_start_dt
            end_dt = end_dt + time_delta
        return {'start_dt': start_dt, 'end_dt': end_dt}

    def _make_form(self):
        self.past_date = self.date_changed = False
        changes = {'room_id': self._room.id}
        changes.update(self._update_datetime())

        if self._reservation.created_by_user != session.user:
            # if the user is cloning someone else's booking, set him/her as booked_for
            changes.update(booked_for_user=session.user,
                           booked_for_name=session.user.full_name,
                           contact_email=session.user.email,
                           contact_phone=session.user.phone)

        defaults = FormDefaults(self._reservation,
                                skip_attrs=set(changes),
                                **changes)

        return self._make_confirm_form(self._room, defaults=defaults, form_class=NewBookingSimpleForm)


class RHRoomBookingNewBooking(RHRoomBookingNewBookingBase):
    def _process_args(self):
        try:
            self._step = int(request.form.get('step', 1))
        except ValueError:
            self._step = 1

    def _get_view(self, view, **kwargs):
        views = {'select_room': WPRoomBookingNewBookingSelectRoom,
                 'select_period': WPRoomBookingNewBookingSelectPeriod,
                 'confirm': WPRoomBookingNewBookingConfirm}
        return views[view](self, **kwargs)

    def _get_select_room_form_defaults(self):
        start_dt, end_dt, date_changed = get_default_booking_interval(duration=self.DEFAULT_BOOKING_DURATION,
                                                                      precision=self.DEFAULT_START_TIME_PRECISION,
                                                                      force_today=False)
        return FormDefaults(start_dt=start_dt, end_dt=end_dt), date_changed

    def _make_select_room_form(self):
        # Step 1
        self._rooms = sorted(Room.find_all(is_active=True), key=lambda r: natural_sort_key(r.full_name))
        form_obj, self.date_changed = self._get_select_room_form_defaults()
        form = NewBookingCriteriaForm(obj=form_obj)
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
            confirm_form = self._make_confirm_form(room, step, defaults=defaults)
        else:
            # Step3 => Step3 due to an error in the form
            confirm_form = form

        conflicts, pre_conflicts = self._get_all_conflicts(room, form)
        repeat_msg = RepeatMapping.get_message(form.repeat_frequency.data, form.repeat_interval.data)
        return self._get_view('confirm', form=confirm_form, room=room, start_dt=form.start_dt.data,
                              end_dt=form.end_dt.data, repeat_frequency=form.repeat_frequency.data,
                              repeat_interval=form.repeat_interval.data, repeat_msg=repeat_msg, conflicts=conflicts,
                              pre_conflicts=pre_conflicts, errors=confirm_form.error_list).display()

    def _process_select_room(self):
        # Step 1: Room(s), dates, repetition selection
        form = self._make_select_room_form()
        if form.validate_on_submit():
            flexible_days = form.flexible_dates_range.data
            day_start_dt = datetime.combine(form.start_dt.data.date(), time())
            day_end_dt = datetime.combine(form.end_dt.data.date(), time(23, 59))
            selected_rooms = [r for r in self._rooms if r.id in form.room_ids.data]
            selected_period_days = (day_end_dt - day_start_dt).days
            for room in selected_rooms:
                booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
                if selected_period_days > booking_limit_days:
                    flash(_(u'Bookings for the room "{}" may not be longer than {} days')
                          .format(room.name, booking_limit_days), 'error')
                    return redirect(url_for('rooms.book'))
            occurrences, candidates = self._get_all_occurrences(form.room_ids.data, form, flexible_days)
            period_form_defaults = FormDefaults(repeat_interval=form.repeat_interval.data,
                                                repeat_frequency=form.repeat_frequency.data)
            period_form = self._make_select_period_form(period_form_defaults)

            # Show step 2 page
            return self._get_view('select_period', rooms=selected_rooms, occurrences=occurrences, candidates=candidates,
                                  start_dt=day_start_dt, end_dt=day_end_dt, period_form=period_form, form=form,
                                  repeat_frequency=form.repeat_frequency.data,
                                  repeat_interval=form.repeat_interval.data, flexible_days=flexible_days).display()

        # GET or form errors => show step 1 page
        return self._get_view('select_room', errors=form.error_list, rooms=self._rooms, form=form,
                              my_rooms=[r.id for r in Room.get_owned_by(session.user)],
                              max_room_capacity=Room.max_capacity, can_override=rb_is_admin(session.user),
                              date_changed=not form.is_submitted() and self.date_changed, ).display()

    def _process_select_period(self):
        form = self._make_select_period_form()
        if form.is_submitted():
            # Errors in here are only caused by users messing with the submitted data so it's not
            # worth making the code more complex to show the errors nicely on the originating page.
            # Doing so would be very hard anyway as we don't keep all data necessary to show step 2
            # when it's not a step 1 form submission.
            if not form.validate():
                raise IndicoError(u'<br>'.join(form.error_list))
            room = Room.get(form.room_id.data)
            if not room:
                raise IndicoError(u'Invalid room')
            # Show step 3 page
            confirm_form_defaults = FormDefaults(form.data)
            return self._show_confirm(room, form, self._step, confirm_form_defaults)

    def _process_confirm(self):
        # The form needs the room to create the equipment list, so we need to get it "manually"...
        room = Room.get(int(request.form['room_id']))
        form = self._make_confirm_form(room)
        if not room.can_be_booked(session.user) and not room.can_be_prebooked(session.user):
            raise Forbidden('You cannot book this room')
        if form.validate_on_submit():
            return self._create_booking_response(form, room)
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
            return redirect(url_for('rooms.book'))


class RHRoomBookingModifyBooking(RHRoomBookingBookingMixin, RHRoomBookingNewBookingBase):
    def _check_access(self):
        if not self._reservation.can_be_modified(session.user):
            raise Forbidden

    def _get_view(self, **kwargs):
        return WPRoomBookingModifyBooking(self, **kwargs)

    def _get_success_url(self):
        return url_for('rooms.roomBooking-bookingDetails', self._reservation)

    def _process(self):
        room = self._reservation.room
        form = ModifyBookingForm(obj=self._reservation,
                                 old_start_dt=self._reservation.start_dt, old_end_dt=self._reservation.end_dt)
        form.used_equipment.query = room.find_available_vc_equipment()

        if not room.notification_for_assistance and not self._reservation.needs_assistance:
            del form.needs_assistance

        invalid_form = form.is_submitted() and not form.validate()
        if invalid_form:
            occurrences = {}
            candidates = {}
            conflicts = {}
            pre_conflicts = {}
        else:
            occurrences, candidates = self._get_all_occurrences([room.id], form, reservation_id=self._reservation.id)
            conflicts, pre_conflicts = self._get_all_conflicts(room, form, self._reservation.id)

        if form.validate_on_submit() and not form.submit_check.data:
            try:
                booking_limit_days = room.booking_limit_days or rb_settings.get('booking_limit')
                if not self._validate_room_booking_limit(form, booking_limit_days):
                    msg = (_(u'Bookings for the room "{}" may not be longer than {} days')
                           .format(room.name, booking_limit_days))
                    return jsonify(success=False, url=url_for('rooms.roomBooking-modifyBookingForm', self._reservation),
                                   msg=msg)
                self._reservation.modify(form.data, session.user)
                flash(_(u'Booking updated'), 'success')
            except NoReportError as e:
                db.session.rollback()
                return jsonify(success=False, msg=unicode(e))
            return jsonify(success=True, url=self._get_success_url())

        elif invalid_form and not form.submit_check.data and request.is_xhr:
            return jsonify(success=False, msg='\n'.join(form.error_list))

        return self._get_view(form=form, room=room, rooms=Room.find_all(), occurrences=occurrences,
                              candidates=candidates, conflicts=conflicts, pre_conflicts=pre_conflicts,
                              start_dt=form.start_dt.data, end_dt=form.end_dt.data, only_conflicts=False,
                              repeat_frequency=form.repeat_frequency.data, repeat_interval=form.repeat_interval.data,
                              reservation=self._reservation,
                              can_override=room.can_be_overridden(session.user)).display()


class RHRoomBookingCalendar(RHRoomBookingBase):
    MAX_DAYS = 365 * 2

    def _process_args(self):
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
            occurrences = (ReservationOccurrence
                           .find(Reservation.room_id.in_(room.id for room in rooms),
                                 ReservationOccurrence.start_dt >= self.start_dt,
                                 ReservationOccurrence.end_dt <= self.end_dt,
                                 ReservationOccurrence.is_valid,
                                 _join=ReservationOccurrence.reservation,
                                 _eager=ReservationOccurrence.reservation)
                           .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY)
                           .all())

        return WPRoomBookingCalendar(self, rooms=rooms, occurrences=occurrences, start_dt=self.start_dt,
                                     end_dt=self.end_dt, overload=self._overload, max_days=self.MAX_DAYS).display()
