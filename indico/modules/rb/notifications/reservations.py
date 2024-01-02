# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy import and_
from sqlalchemy.orm import load_only

from indico.core.notifications import email_sender, make_email
from indico.modules.rb.settings import RoomEmailMode, rb_user_settings
from indico.modules.users import User, UserSetting
from indico.util.date_time import format_datetime
from indico.util.i18n import force_locale
from indico.web.flask.templating import get_template_module


def get_manager_emails(room):
    emails = set(room.notification_emails)
    if (rb_user_settings.get(room.owner, 'email_mode') in (RoomEmailMode.owned, RoomEmailMode.all)
            and room not in rb_user_settings.get(room.owner, 'email_blacklist')):
        emails.add(room.owner.email)
    # skip people who don't want manager emails
    email_mode_filter = and_(
        UserSetting.name == 'email_mode',
        UserSetting.value[()].astext.in_([RoomEmailMode.none.name, RoomEmailMode.owned.name])
    )
    # skip people who don't want emails for the room
    room_blacklist_filter = and_(
        UserSetting.name == 'email_blacklist',
        UserSetting.value.contains(str(room.id))
    )
    query = (User.query
             .join(UserSetting)
             .options(load_only('id'))
             .filter(UserSetting.module == 'roombooking',
                     email_mode_filter | room_blacklist_filter))
    disabled_emails = {u.email for u in query}
    emails |= room.get_manager_emails() - disabled_emails
    return emails


class ReservationNotification:
    def __init__(self, reservation):
        self.reservation = reservation
        self.start_dt = format_datetime(reservation.start_dt)

    def _make_template(self, mail_params, **body_params):
        from indico.modules.rb.models.reservations import RepeatFrequency, RepeatMapping
        template_params = mail_params | body_params
        template_params['RepeatFrequency'] = RepeatFrequency
        template_params['RepeatMapping'] = RepeatMapping
        return get_template_module('rb/emails/reservations/{}.txt'.format(mail_params['template_name']),
                                   **template_params)

    def compose_email_to_user(self, **mail_params):
        creator = self.reservation.created_by_user
        to_list = {creator.email}
        if self.reservation.contact_email:
            to_list.add(self.reservation.contact_email)
        with force_locale(None):
            template = self._make_template(mail_params, reservation=self.reservation)
            return make_email(to_list=to_list, template=template)

    def compose_email_to_manager(self, **mail_params):
        room = self.reservation.room
        with force_locale(None):  # No event, and managers are sent in one mail together
            template = self._make_template(mail_params, reservation=self.reservation)
            return make_email(to_list=get_manager_emails(room), template=template)


@email_sender
def notify_reset_approval(reservation):
    notification = ReservationNotification(reservation)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='change_state_email_to_user'),
        notification.compose_email_to_manager(template_name='change_state_email_to_manager')
    ] if _f]


@email_sender
def notify_cancellation(reservation):
    if not reservation.is_cancelled:
        raise ValueError('Reservation is not cancelled')
    notification = ReservationNotification(reservation)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='cancellation_email_to_user'),
        notification.compose_email_to_manager(template_name='cancellation_email_to_manager'),
    ] if _f]


@email_sender
def notify_confirmation(reservation, reason=None):
    if not reservation.is_accepted:
        raise ValueError('Reservation is not confirmed')
    notification = ReservationNotification(reservation)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='confirmation_email_to_user', reason=reason),
        notification.compose_email_to_manager(template_name='confirmation_email_to_manager', reason=reason),
    ] if _f]


@email_sender
def notify_creation(reservation):
    notification = ReservationNotification(reservation)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='creation_email_to_user'),
        notification.compose_email_to_manager(template_name='creation_email_to_manager'),
    ] if _f]


@email_sender
def notify_rejection(reservation):
    if not reservation.is_rejected:
        raise ValueError('Reservation is not rejected')
    notification = ReservationNotification(reservation)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='rejection_email_to_user'),
        notification.compose_email_to_manager(template_name='rejection_email_to_manager')
    ] if _f]


@email_sender
def notify_modification(reservation, changes):
    notification = ReservationNotification(reservation)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='modification_email_to_user'),
        notification.compose_email_to_manager(template_name='modification_email_to_manager'),
    ] if _f]


@email_sender
def notify_about_finishing_bookings(user, reservations):
    with user.force_user_locale():
        tpl = get_template_module('rb/emails/reservations/reminders/finishing_bookings.html',
                                  reservations=reservations, user=user)
        return make_email(to_list={user.email}, template=tpl, html=True)
