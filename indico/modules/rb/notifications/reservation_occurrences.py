# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.notifications import email_sender, make_email
from indico.modules.rb.notifications.reservations import ReservationNotification
from indico.util.date_time import format_datetime
from indico.web.flask.templating import get_template_module


class ReservationOccurrenceNotification(ReservationNotification):
    def __init__(self, occurrence):
        super().__init__(occurrence.reservation)
        self.occurrence = occurrence
        self.start_dt = format_datetime(occurrence.start_dt)

    def _make_template(self, mail_params, **body_params):
        body_params['occurrence'] = self.occurrence
        return super()._make_template(mail_params, **body_params)


@email_sender
def notify_cancellation(occurrence):
    if not occurrence.is_cancelled:
        raise ValueError('Occurrence is not cancelled')
    notification = ReservationOccurrenceNotification(occurrence)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='occurrence_cancellation_email_to_user'),
        notification.compose_email_to_manager(template_name='occurrence_cancellation_email_to_manager'),
    ] if _f]


@email_sender
def notify_rejection(occurrence):
    if not occurrence.is_rejected:
        raise ValueError('Occurrence is not rejected')
    notification = ReservationOccurrenceNotification(occurrence)
    return [_f for _f in [
        notification.compose_email_to_user(template_name='occurrence_rejection_email_to_user'),
        notification.compose_email_to_manager(template_name='occurrence_rejection_email_to_manager')
    ] if _f]


@email_sender
def notify_upcoming_occurrences(user, occurrences):
    with user.force_user_locale():
        tpl = get_template_module('rb/emails/reservations/reminders/upcoming_occurrence.html',
                                  occurrences=occurrences, user=user)
        return make_email(to_list={user.email}, template=tpl, html=True)
