from flask import render_template, session

from indico.core.config import Config
from indico.modules.rb.notifications.util import email_sender
from indico.util.date_time import format_datetime


class ReservationNotification(object):
    def __init__(self, reservation):
        self.reservation = reservation
        self.start_date = format_datetime(reservation.start_date)

    def _get_email_subject(self, **mail_params):
        return '{prefix}[{room}] {subject} {date} {suffix}'.format(
            prefix=mail_params.get('subject_prefix', ''),
            room=self.reservation.room.getFullName(),
            subject=mail_params.get('subject', ''),
            date=self.start_date,
            suffix=mail_params.get('subject_suffix', '')
        ).strip()

    def _make_body(self, mail_params, **body_params):
        return render_template('rb/emails/{}.txt'.format(mail_params['template_name']), **dict(mail_params, **body_params))

    def _make_email(self, to_list, subject=None, body=None):
        return {
            'fromAddr': Config.getInstance().getNoReplyEmail(),
            'toList': to_list,
            'subject': subject,
            'body': body
        }

    def compose_email_to_creator_and_contact(self, **mail_params):
        creator = self.reservation.created_by_user
        to_list = set([creator.getEmail()] + self.reservation.getContactEmailList())
        subject = self._get_email_subject(**mail_params)
        body = self._make_body(mail_params, reservation=self.reservation)
        return self._make_email(to_list, subject, body)

    def compose_email_to_owner(self, **mail_params):
        to_list = set([self.reservation.room.getResponsible().getEmail()] + self.reservation.getNotificationEmailList())
        subject = self._get_email_subject(**mail_params)
        body = self._make_body(mail_params, reservation=self.reservation)
        return self._make_email(to_list, subject, body)

    def compose_email_to_avc_support(self, **mail_params):
        if self.reservation.is_confirmed and self.reservation.uses_video_conference:
            to_list = self.reservation.room.location.getSupportEmails()
            if to_list:
                subject = self._get_email_subject(**mail_params)
                body = self._make_body(mail_params, reservation=self.reservation)
                return self._make_email(to_list, subject, body)

    def compose_email_to_assistance(self, **mail_params):
        if self.reservation.room.notification_for_assistance:
            if self.reservation.needs_general_assistance or mail_params.get('assistance_cancelled'):
                from indico.modules.rb.controllers.utils import getRoomBookingOption
                to_list = getRoomBookingOption('assistanceNotificationEmails')
                if to_list:
                    subject = self._get_email_subject(**mail_params)
                    body = self._make_body(mail_params, reservation=self.reservation)
                    return self._make_email(to_list, subject, body)


@email_sender
def notify_cancellation(reservation):
    if not reservation.is_cancelled:
        raise ValueError('Reservation is not cancelled')
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_creator_and_contact(
            subject='Booking cancelled on',
            template_name='cancellation_email_to_user'
        ),
        notification.compose_email_to_owner(
            subject='Booking cancelled on',
            template_name='cancellation_email_to_manager'
        ),
        notification.compose_email_to_avc_support(
            subject='Booking cancelled on',
            template_name='cancellation_email_to_avc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request Cancellation]',
            subject='Request cancelled for',
            template_name='cancellation_email_to_assistance'
        )
    ])


@email_sender
def notify_confirmation(reservation):
    if not reservation.is_confirmed:
        raise ValueError('Reservation is not confirmed')
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_creator_and_contact(
            subject='Booking confirmed on',
            template_name='confirmation_email_to_user'
        ),
        notification.compose_email_to_owner(
            subject='Booking confirmed on',
            template_name='confirmation_email_to_manager'
        ),
        notification.compose_email_to_avc_support(
            subject='New Booking on',
            template_name='creation_email_to_avc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request]',
            subject='New Support on',
            template_name='creation_email_to_assistance'
        )
    ])


@email_sender
def notify_creation(reservation):
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_creator_and_contact(
            subject=('Pre-Booking awaiting acceptance', 'New Booking on')[reservation.is_confirmed],
            template_name=('creation_pre_email_to_user', 'creation_email_to_user')[reservation.is_confirmed]
        ),
        notification.compose_email_to_owner(
            subject=('New Pre-Booking on', 'New Booking on')[reservation.is_confirmed],
            booking_message=('Book', 'Pre-book')[reservation.is_confirmed],
            template_name='creation_email_to_manager'
        ),
        notification.compose_email_to_avc_support(
            subject='New Booking on',
            template_name='creation_email_to_avc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request]',
            subject='New Booking on',
            template_name='creation_email_to_assistance'
        )
    ])


@email_sender
def notify_rejection(reservation):
    if not reservation.is_rejected:
        raise ValueError('Reservation is not rejected')
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_creator_and_contact(
            subject='Booking rejected on',
            template_name='rejection_email_to_user',
        ),
        notification.compose_email_to_owner(
            subject='Booking rejected on',
            template_name='rejection_email_to_manager',
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request Cancellation]',
            subject='Request cancelled for',
            template_name='rejection_email_to_assistance',
        )
    ])


@email_sender
def notify_modification(reservation, changes):
    assistance_change = changes.get('needs_general_assistance')
    assistance_cancelled = assistance_change and assistance_change['old'] and not assistance_change['new']
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_creator_and_contact(
            subject='Booking modified on',
            template_name='modification_email_to_user'
        ),
        notification.compose_email_to_owner(
            subject='Booking modified on',
            template_name='modification_email_to_manager'
        ),
        notification.compose_email_to_avc_support(
            subject='Booking modified on',
            template_name='modification_email_to_avc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request {}]'.format(('Modification', 'Cancelled')[assistance_cancelled]),
            subject='Modified request on',
            template_name='modification_email_to_assistance',
            assistance_cancelled=assistance_cancelled
        )
    ])
