# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

import requests
from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.notifications import logger
from indico.modules.notifications import settings as notification_settings
from indico.modules.notifications.models.notifications import Notification
from indico.util.date_time import now_utc


def _get_config_data():
    url = notification_settings.get('webhook_url')
    token = notification_settings.get('secret_token')
    channel_id = notification_settings.get('channel_id')

    if not url:
        raise ValueError('Webhook URL not set!')

    return url, token, channel_id


def _send_notifications(notifications):
    """Send a set of notifications to the webhook.

    :param notifications: an iterable of notification dicts
    """
    url, token, channel_id = _get_config_data()
    sent_items = set()
    try:
        for notification in notifications:
            data = {
                'notification': {
                    'target': channel_id,
                    'summary': notification.subject,
                    'body': notification.body,
                    'targetUsers': [{'email': notification.user.email}]
                }
            }
            resp = requests.post(url, json=data, headers={'Authorization': 'Bearer ' + token})
            resp.raise_for_status()
            sent_items.add(notification)
    finally:
        for notification in sent_items:
            notification.sent_dt = now_utc()
        if sent_items:
            db.session.commit()
            logger.info('Sent %d notification(s) using webhook', len(sent_items))


@celery.task(name='send_webhook_notification')
def send_webhook_notification(notification):
    """Send immediately a notification."""
    _send_notifications((notification,))


@celery.periodic_task(name='send_pending_webhook_notifications', run_every=crontab(minute='*/5'))
def send_pending_webhook_notifications():
    """Send notifications that for some reason were not sent immediately."""
    # get all notifications that are older than 5 minutes but weren't sent yet
    _send_notifications(Notification.query.filter(
        Notification.sent_dt.is_(None),
        (now_utc() - timedelta(minutes=5)) > Notification.created_dt
    ))
