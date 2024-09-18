# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events import logger
from indico.modules.logs import EventLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.signals import make_interceptable


def _log_registration_form_update(regform, changes, extra_log_fields):
    log_fields = {
        'title': {'title': 'Title', 'type': 'string'},
        'introduction': 'Introduction',
        'contact_info': 'Contact info',
        'moderation_enabled': 'Moderated',
        'private': 'Private',
        'require_login': 'Only logged-in users',
        'require_user': 'Registrant must have account',
        'require_captcha': 'Require CAPTCHA',
        'registration_limit': 'Maximum number of registrations',
        'modification_mode': 'Modification allowed',
        'publish_registration_count': 'Publish number of registrations',
        'publish_checkin_enabled': 'Publish check-in status',
        'notification_sender_address': 'Notification sender address',
        'message_pending': 'Message for pending registrations',
        'message_unpaid': 'Message for unpaid registrations',
        'message_complete': 'Message for complete registrations',
        'attach_ical': 'Attach iCalendar file',
        'manager_notifications_enabled': 'Notify managers about registration creation',
        'manager_notification_recipients': 'Registration creation notification emails',
        **(extra_log_fields or {})
    }
    if changes:
        regform.event.log(EventLogRealm.management, LogKind.change, 'Registration Form',
                          f'Data updated for "{regform.title}"', session.user,
                          data={'Changes': make_diff_log(changes, log_fields)})


@make_interceptable
def update_registration_form_settings(regform, data, *, skip=(), _extra_log_fields=None):
    changes = regform.populate_from_dict(data, skip=skip)
    db.session.flush()
    signals.event.registration_form_edited.send(regform)
    logger.info('Registration form %r updated with %r by %r', regform, data, session.user)
    _log_registration_form_update(regform, changes, _extra_log_fields)
