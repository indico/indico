# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.models.reminders import EventReminder
from indico.util.date_time import now_utc


@celery.periodic_task(name='event_reminders', run_every=crontab(minute='*/5'))
def send_event_reminders():
    reminders = (EventReminder.query
                 .filter(~EventReminder.is_sent,
                         ~Event.is_deleted,
                         ~Event.label.has(EventLabel.is_event_not_happening),
                         EventReminder.scheduled_dt <= now_utc())
                 .join(EventReminder.event)
                 .all())
    for reminder in reminders:
        logger.info('Sending event reminder: %s', reminder)
        reminder.send()
    db.session.commit()
