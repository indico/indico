# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.config import config
from indico.core.notifications import make_email, send_email
from indico.modules.core.settings import core_settings
from indico.modules.events.ical import MIMECalendar, event_to_ical
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.util.placeholders import replace_placeholders
from indico.util.signals import make_interceptable, values_from_signal
from indico.web.flask.templating import get_template_module


def notify_invitation(invitation, email_subject, email_body, from_address):
    """Send a notification about a new registration invitation."""
    email_body = replace_placeholders('registration-invitation-email', email_body, invitation=invitation)
    email_subject = replace_placeholders('registration-invitation-email', email_subject, invitation=invitation)
    template = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
    email = make_email(invitation.email, from_address=from_address, template=template, html=True)
    user = session.user if session else None
    send_email(email, invitation.registration_form.event, 'Registration', user)


@make_interceptable
def _notify_registration(registration, template_name, to_managers=False, attach_rejection_reason=False,
                         diff=None, old_price=None):
    from indico.modules.events.registration.util import get_ticket_attachments
    attachments = []
    regform = registration.registration_form
    tickets_handled = values_from_signal(signals.event.is_ticketing_handled.send(regform), single_value=True)
    if (not to_managers and
            regform.tickets_enabled and
            regform.ticket_on_email and
            not any(tickets_handled) and
            registration.state == RegistrationState.complete):
        attachments += get_ticket_attachments(registration)
    if not to_managers and registration.registration_form.attach_ical:
        event_ical = event_to_ical(registration.event, method='REQUEST', skip_access_check=True,
                                   organizer=(core_settings.get('site_title'), config.NO_REPLY_EMAIL))
        attachments.append(MIMECalendar('event.ics', event_ical))
    to_list = (
        registration.email if not to_managers else registration.registration_form.manager_notification_recipients
    )
    from_address = registration.registration_form.notification_sender_address if not to_managers else None
    with registration.event.force_event_locale(registration.user if not to_managers else None):
        tpl = get_template_module(f'events/registration/emails/{template_name}', registration=registration,
                                  attach_rejection_reason=attach_rejection_reason, diff=diff, old_price=old_price)
        mail = make_email(to_list=to_list, template=tpl, html=True, from_address=from_address, attachments=attachments)
    user = session.user if session else None
    signals.core.before_notification_send.send('notify-registration', email=mail, registration=registration,
                                               template_name=template_name, to_managers=to_managers,
                                               attach_rejection_reason=attach_rejection_reason)
    send_email(mail, event=registration.registration_form.event, module='Registration', user=user,
               log_metadata={'registration_id': registration.id})


def notify_registration_creation(registration, notify_user=True):
    if notify_user:
        _notify_registration(registration, 'registration_creation_to_registrant.html')
    if registration.registration_form.manager_notifications_enabled:
        _notify_registration(registration, 'registration_creation_to_managers.html', to_managers=True)


def notify_registration_modification(registration, notify_user=True, diff=None, old_price=None):
    if notify_user:
        _notify_registration(registration, 'registration_modification_to_registrant.html',
                             diff=diff, old_price=old_price)
    if registration.registration_form.manager_notifications_enabled:
        _notify_registration(registration, 'registration_modification_to_managers.html', to_managers=True,
                             diff=diff, old_price=old_price)


def notify_registration_state_update(registration, attach_rejection_reason=False):
    _notify_registration(registration, 'registration_state_update_to_registrant.html',
                         attach_rejection_reason=attach_rejection_reason)
    if registration.registration_form.manager_notifications_enabled:
        _notify_registration(registration, 'registration_state_update_to_managers.html', to_managers=True)
