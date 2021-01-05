# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.util.i18n import orig_string


def connect_log_signals():
    signals.event.registration_checkin_updated.connect(log_registration_check_in)
    signals.event.registration_state_updated.connect(log_registration_updated)


def log_registration_check_in(registration, **kwargs):
    """Log a registration check-in action to the event log."""
    if registration.checked_in:
        log_text = '"{}" has been checked in'.format(registration.full_name)
    else:
        log_text = '"{}" check-in has been reset'
    registration.log(EventLogRealm.participants, EventLogKind.change, 'Registration',
                     log_text.format(registration.full_name), session.user)


def log_registration_updated(registration, previous_state, **kwargs):
    """Log the registration status change to the event log."""
    if not previous_state:
        return
    previous_state_title = orig_string(previous_state.title)
    if (previous_state == RegistrationState.pending
            and registration.state in (RegistrationState.complete, RegistrationState.unpaid)):
        log_text = 'Registration for "{}" has been approved'
        kind = EventLogKind.positive
    elif previous_state == RegistrationState.pending and registration.state == RegistrationState.rejected:
        log_text = 'Registration for "{}" has been rejected'
        kind = EventLogKind.negative
    elif previous_state == RegistrationState.unpaid and registration.state == RegistrationState.complete:
        log_text = 'Registration for "{}" has been paid'
        kind = EventLogKind.positive
    elif previous_state == RegistrationState.complete and registration.state == RegistrationState.unpaid:
        log_text = 'Registration for "{}" has been marked as not paid'
        kind = EventLogKind.negative
    elif registration.state == RegistrationState.withdrawn:
        log_text = 'Registration for "{}" has been withdrawn'
        kind = EventLogKind.negative
    else:
        state_title = orig_string(registration.state.title).lower()
        log_text = 'Registration for "{{}}" has been changed from {} to {}'.format(previous_state_title.lower(),
                                                                                   state_title)
        kind = EventLogKind.change
    registration.log(EventLogRealm.participants, kind, 'Registration', log_text.format(registration.full_name),
                     session.user, data={'Previous state': previous_state_title})
