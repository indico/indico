# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.modules.events import EventLogRealm
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.logs import LogKind
from indico.util.i18n import orig_string


def connect_log_signals():
    signals.event.registration_checkin_updated.connect(log_registration_check_in)
    signals.event.registration_state_updated.connect(log_registration_updated)


def log_registration_check_in(registration, **kwargs):
    """Log a registration check-in action to the event log."""
    if registration.checked_in:
        log_text = f'"{registration.full_name}" has been checked in'
    else:
        log_text = '"{}" check-in has been reset'
    registration.log(EventLogRealm.participants, LogKind.change, 'Registration',
                     log_text.format(registration.full_name), session.user)


def log_registration_updated(registration, previous_state, silent=False, **kwargs):
    """Log the registration status change to the event log."""
    if not previous_state or silent:
        return
    previous_state_title = orig_string(previous_state.title)
    data = {'Previous state': previous_state_title}
    if (previous_state == RegistrationState.pending
            and registration.state in (RegistrationState.complete, RegistrationState.unpaid)):
        log_text = 'Registration for "{}" has been approved'
        kind = LogKind.positive
    elif previous_state == RegistrationState.pending and registration.state == RegistrationState.rejected:
        log_text = 'Registration for "{}" has been rejected'
        kind = LogKind.negative
        if registration.rejection_reason:
            data['Reason'] = registration.rejection_reason
    elif previous_state == RegistrationState.unpaid and registration.state == RegistrationState.complete:
        log_text = 'Registration for "{}" has been paid'
        kind = LogKind.positive
    elif previous_state == RegistrationState.complete and registration.state == RegistrationState.unpaid:
        log_text = 'Registration for "{}" has been marked as not paid'
        kind = LogKind.negative
    elif registration.state == RegistrationState.withdrawn:
        log_text = 'Registration for "{}" has been withdrawn'
        kind = LogKind.negative
    else:
        state_title = orig_string(registration.state.title).lower()
        log_text = f'Registration for "{{}}" has been changed from {previous_state_title.lower()} to {state_title}'
        kind = LogKind.change
    registration.log(EventLogRealm.participants, kind, 'Registration', log_text.format(registration.full_name),
                     session.user, data=data)
