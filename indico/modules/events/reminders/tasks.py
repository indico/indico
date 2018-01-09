# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

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
