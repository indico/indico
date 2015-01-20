from datetime import date

from flask import render_template

from indico.core.config import Config
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.notifications.reservations import ReservationNotification
from indico.modules.rb.notifications.util import email_sender
from indico.util.date_time import format_datetime, get_month_end, get_month_start


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
        to_list.append(reservation_user.getEmail())

    cc_list = []
    room = occurrence.reservation.room
    if room.notification_for_responsible:
        cc_list.append(room.owner.getEmail())

    if not to_list and not cc_list:
        return

    from_addr = Config.getInstance().getNoReplyEmail()
    subject = 'Reservation reminder'
    text = render_template('rb/emails/reservations/reminders/upcoming_occurrence.txt',
                           occurrence=occurrence,
                           owner=reservation_user,
                           RepeatFrequency=RepeatFrequency)

    return {
        'fromAddr': from_addr,
        'toList': to_list,
        'ccList': cc_list,
        'subject': subject,
        'body': text
    }


@email_sender
def notify_reservation_digest(reservation, occurrences):
    if not occurrences:
        return
    if reservation.end_dt.date() < date.today():
        raise ValueError("This reservation has already ended")
    if reservation.repeat_frequency != RepeatFrequency.WEEK:
        raise ValueError("This reservation is not weekly")
    if any(occ.reservation != reservation for occ in occurrences):
        raise ValueError("Some occurrences don't belong to the reservation")
    if any(occurrences[0].start_dt.month != occ.start_dt.month for occ in occurrences):
        raise ValueError("Occurrences happening in different months")

    to_list = []
    reservation_user = reservation.booked_for_user
    if reservation_user is not None:
        to_list.append(reservation_user.getEmail())

    cc_list = []
    room = reservation.room
    if room.notification_for_responsible:
        cc_list.append(room.owner.getEmail())

    if not to_list and not cc_list:
        return

    from_addr = Config.getInstance().getNoReplyEmail()
    subject = 'Reservation reminder digest'
    text = render_template('rb/emails/reservations/reminders/reservation_digest.txt',
                           reservation=reservation,
                           occurrences=occurrences,
                           owner=reservation_user)

    return {
        'fromAddr': from_addr,
        'toList': to_list,
        'ccList': cc_list,
        'subject': subject,
        'body': text
    }
