# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.models.reminders import EventReminder
from indico.util.date_time import now_utc


@celery.periodic_task(name='event_reminders', run_every=crontab(minute='*/5'))
def send_event_reminders():
    reminders = EventReminder.find_all(~EventReminder.is_sent, ~Event.is_deleted,
                                       EventReminder.scheduled_dt <= now_utc(),
                                       _join=EventReminder.event)
    for reminder in reminders:
        logger.info('Sending event reminder: %s', reminder)
        reminder.send()
    db.session.commit()
