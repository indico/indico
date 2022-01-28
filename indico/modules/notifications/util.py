# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps

from flask import g

from indico.core.db import db
from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.core.notifications import email_sender
from indico.modules.notifications import settings as notification_settings
from indico.modules.notifications.models.notifications import Notification
from indico.modules.notifications.tasks import send_webhook_notification


def check_notifications_enabled():
    url = notification_settings.get('webhook_url')
    return bool(url)


def make_notification(to_users, subject=None, body=None, template=None, content_type='plain_text'):
    if template is not None and (subject is not None or body is not None):
        raise ValueError('Only subject/body or template can be passed')

    if template:
        subject = template.get_subject()
        body = template.get_body()

    return {
        'to': set(to_users),
        'subject': subject,
        'body': body,
        'content_type': content_type
    }


def process_notification(notification_data):
    for receiver in notification_data['to']:
        notification = Notification(
            user=receiver,
            subject=notification_data['subject'],
            body=notification_data['body'],
            render_mode=RenderMode[notification_data.get('content_type', 'plain_text')]
        )
        db.session.add(notification)
        # flush so that we get the id of the notification (useful for logging, etc...)
        db.session.flush()

        # enqueue notification task in global queue (sent when request succeeds)
        if 'webhook_queue' in g:
            g.webhook_queue.add(notification)
        else:
            send_webhook_notification.delay(notification)


def notification_to_email(notification):
    content_type = notification.pop('content_type')
    assert content_type in {'html', 'plain_text'}
    notification['html'] = content_type == 'html'
    return notification


def notification_sender(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        notifications_enabled = check_notifications_enabled()
        notification = fn(*args, **kwargs)
        if notifications_enabled:
            process_notification(notification)
        else:
            # send regular e-mails
            email_sender(fn)(notification_to_email(notification))
    return wrapper
