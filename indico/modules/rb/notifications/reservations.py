# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template

from indico.core.notifications import email_sender, make_email
from indico.util.date_time import format_datetime
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module


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
        to_list = {creator.email}
        if self.reservation.contact_email:
            to_list.add(self.reservation.contact_email)
        subject = self._get_email_subject(**mail_params)
        body = self._make_body(mail_params, reservation=self.reservation)
        return make_email(to_list=to_list, subject=subject, body=body)

    def compose_email_to_manager(self, **mail_params):
        room = self.reservation.room
        to_list = {room.owner.email} | room.get_manager_emails() | set(room.notification_emails)
        subject = self._get_email_subject(**mail_params)
        body = self._make_body(mail_params, reservation=self.reservation)
        return make_email(to_list=to_list, subject=subject, body=body)


@email_sender
def notify_reset_approval(reservation):
    notification = ReservationNotification(reservation)
    return filter(None, [
        notification.compose_email_to_user(
            subject='Booking approval changed state on',
            template_name='change_state_email_to_user'
        ),
        notification.compose_email_to_manager(
            subject='Booking approval changed state on',
            template_name='change_state_email_to_manager'
        )
    ])


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
        )
    ])


@email_sender
def notify_modification(reservation, changes):
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
    ])


@email_sender
def notify_about_finishing_bookings(user, reservations):
    tpl = get_template_module('rb/emails/reservations/reminders/finishing_bookings.html',
                              reservations=reservations, user=user)
    return make_email(to_list={user.email}, template=tpl, html=True)
