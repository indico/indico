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

    to_list = []
    reservation_user = occurrence.reservation.booked_for_user
    if reservation_user is not None:
        to_list.append(reservation_user.email)

    cc_list = []
    room = occurrence.reservation.room
    if room.notification_for_responsible:
        cc_list.append(room.owner.email)

    if not to_list and not cc_list:
        return

    subject = 'Reservation reminder'
    text = render_template('rb/emails/reservations/reminders/upcoming_occurrence.txt',
                           occurrence=occurrence,
                           owner=reservation_user,
                           RepeatFrequency=RepeatFrequency)
    return make_email(to_list=to_list, cc_list=cc_list, subject=subject, body=text)
