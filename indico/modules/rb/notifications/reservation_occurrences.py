# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from datetime import date

from flask import render_template

from indico.core.notifications import email_sender, make_email
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.notifications.reservations import ReservationNotification
from indico.util.date_time import format_datetime


class ReservationOccurrenceNotification(ReservationNotification):
    def __init__(self, occurrence):
        super(ReservationOccurrenceNotification, self).__init__(occurrence.reservation)
        self.occurrence = occurrence
        self.start_dt = format_datetime(occurrence.start_dt)

    def _get_email_subject(self, **mail_params):
        mail_params = dict(mail_params, **{'subject_suffix': '(SINGLE OCCURRENCE)'})
        return super(ReservationOccurrenceNotification, self)._get_email_subject(**mail_params)

    def _make_body(self, mail_params, **body_params):
        body_params['occurrence'] = self.occurrence
        return super(ReservationOccurrenceNotification, self)._make_body(mail_params, **body_params)


@email_sender
def notify_cancellation(occurrence):
    if not occurrence.is_cancelled:
        raise ValueError('Occurrence is not cancelled')
    notification = ReservationOccurrenceNotification(occurrence)
    return filter(None, [
        notification.compose_email_to_user(
            subject='Booking cancelled on',
            template_name='occurrence_cancellation_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='Booking cancelled on',
            template_name='occurrence_cancellation_email_to_manager'
        ),
        notification.compose_email_to_vc_support(
            subject='Booking cancelled on',
            template_name='occurrence_cancellation_email_to_vc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request Cancellation]',
            subject='Request cancelled for',
            template_name='occurrence_cancellation_email_to_assistance'
        )
    ])


@email_sender
def notify_rejection(occurrence):
    if not occurrence.is_rejected:
        raise ValueError('Occurrence is not rejected')
    notification = ReservationOccurrenceNotification(occurrence)
    return filter(None, [
        notification.compose_email_to_user(
            subject='Booking rejected on',
            template_name='occurrence_rejection_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='Booking rejected on',
            template_name='occurrence_rejection_email_to_manager'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request Cancellation]',
            subject='Request cancelled for',
            template_name='occurrence_rejection_email_to_assistance'
        )
    ])


@email_sender
def notify_upcoming_occurrence(occurrence):
    if occurrence.start_dt.date() < date.today():
        raise ValueError("This reservation occurrence started in the past")

    reservation_user = occurrence.reservation.booked_for_user
    subject = 'Reservation reminder'
    text = render_template('rb/emails/reservations/reminders/upcoming_occurrence.txt',
                           occurrence=occurrence,
                           owner=reservation_user,
                           RepeatFrequency=RepeatFrequency)
    return make_email(to_list={reservation_user.email}, subject=subject, body=text)
