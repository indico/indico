from flask import render_template

from indico.core.notifications import email_sender, make_email
from indico.util.date_time import format_datetime
from indico.util.string import to_unicode


class ReservationNotification(object):
    def __init__(self, reservation):
        self.reservation = reservation
        self.start_dt = format_datetime(reservation.start_dt)

    def _get_email_subject(self, **mail_params):
        return u'{prefix}[{room}] {subject} {date} {suffix}'.format(
            prefix=to_unicode(mail_params.get('subject_prefix', '')),
            room=self.reservation.room.full_name,
            subject=to_unicode(mail_params.get('subject', '')),
            date=to_unicode(self.start_dt),
            suffix=to_unicode(mail_params.get('subject_suffix', ''))
        ).strip()

    def _make_body(self, mail_params, **body_params):
        from indico.modules.rb.models.reservations import RepeatFrequency, RepeatMapping
        template_params = dict(mail_params, **body_params)
        template_params['RepeatFrequency'] = RepeatFrequency
        template_params['RepeatMapping'] = RepeatMapping
        return render_template('rb/emails/reservations/{}.txt'.format(mail_params['template_name']), **template_params)

    def compose_email_to_user(self, **mail_params):
        creator = self.reservation.created_by_user
        to_list = {creator.email} | self.reservation.contact_emails
        subject = self._get_email_subject(**mail_params)
        body = self._make_body(mail_params, reservation=self.reservation)
        return make_email(to_list=to_list, subject=subject, body=body)

    def compose_email_to_manager(self, **mail_params):
        to_list = {self.reservation.room.owner.email} | self.reservation.room.notification_emails
        subject = self._get_email_subject(**mail_params)
        body = self._make_body(mail_params, reservation=self.reservation)
        return make_email(to_list=to_list, subject=subject, body=body)

    def compose_email_to_vc_support(self, **mail_params):
        from indico.modules.rb import rb_settings

        if self.reservation.is_accepted and self.reservation.uses_vc:
            to_list = rb_settings.get('vc_support_emails')
            if to_list:
                subject = self._get_email_subject(**mail_params)
                body = self._make_body(mail_params, reservation=self.reservation)
                return make_email(to_list=to_list, subject=subject, body=body)

    def compose_email_to_assistance(self, **mail_params):
        from indico.modules.rb import rb_settings

        if self.reservation.room.notification_for_assistance:
            if self.reservation.needs_assistance or mail_params.get('assistance_cancelled'):
                to_list = rb_settings.get('assistance_emails')
                if to_list:
                    subject = self._get_email_subject(**mail_params)
                    body = self._make_body(mail_params, reservation=self.reservation)
                    return make_email(to_list=to_list, subject=subject, body=body)


@email_sender
def notify_cancellation(reservation):
    if not reservation.is_cancelled:
        raise ValueError('Reservation is not cancelled')
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_user(
            subject='Booking cancelled on',
            template_name='cancellation_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='Booking cancelled on',
            template_name='cancellation_email_to_manager'
        ),
        notification.compose_email_to_vc_support(
            subject='Booking cancelled on',
            template_name='cancellation_email_to_vc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request Cancellation]',
            subject='Request cancelled for',
            template_name='cancellation_email_to_assistance'
        )
    ])


@email_sender
def notify_confirmation(reservation):
    if not reservation.is_accepted:
        raise ValueError('Reservation is not confirmed')
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_user(
            subject='Booking confirmed on',
            template_name='confirmation_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='Booking confirmed on',
            template_name='confirmation_email_to_manager'
        ),
        notification.compose_email_to_vc_support(
            subject='New Booking on',
            template_name='creation_email_to_vc_support'
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
        notification.compose_email_to_user(
            subject='New Booking on' if reservation.is_accepted else 'Pre-Booking awaiting acceptance',
            template_name='creation_email_to_user' if reservation.is_accepted else 'creation_pre_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='New booking on' if reservation.is_accepted else 'New Pre-Booking on',
            template_name='creation_email_to_manager' if reservation.is_accepted else 'creation_pre_email_to_manager'
        ),
        notification.compose_email_to_vc_support(
            subject='New Booking on',
            template_name='creation_email_to_vc_support'
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
        notification.compose_email_to_user(
            subject='Booking rejected on',
            template_name='rejection_email_to_user',
        ),
        notification.compose_email_to_manager(
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
    assistance_change = changes.get('needs_assistance')
    assistance_cancelled = assistance_change and assistance_change['old'] and not assistance_change['new']
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_user(
            subject='Booking modified on',
            template_name='modification_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='Booking modified on',
            template_name='modification_email_to_manager'
        ),
        notification.compose_email_to_vc_support(
            subject='Booking modified on',
            template_name='modification_email_to_vc_support'
        ),
        notification.compose_email_to_assistance(
            subject_prefix='[Support Request {}]'.format('Cancelled' if assistance_cancelled else 'Modification'),
            subject='Modified request on',
            template_name='modification_email_to_assistance',
            assistance_cancelled=assistance_cancelled
        )
    ])
