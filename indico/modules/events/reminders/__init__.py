# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.logger import Logger
from indico.modules.events import Event
from indico.modules.events.cloning import EventCloner
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.reminders')


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.events.reminders.tasks  # noqa: F401


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user):
        return
    return SideMenuItem('reminders', _('Reminders'), url_for('event_reminders.list', event), section='organization')


@signals.event.times_changed.connect_via(Event)
def _event_times_changed(sender, obj, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    event = obj
    for reminder in event.reminders.filter(EventReminder.is_relative, ~EventReminder.is_sent):
        new_dt = event.start_dt - reminder.event_start_delta
        if reminder.scheduled_dt != new_dt:
            logger.info('Changing start time of %s to %s', reminder, new_dt)
            reminder.scheduled_dt = new_dt


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    EventReminder.find(creator_id=source.id).update({EventReminder.creator_id: target.id})


@signals.event_management.get_cloners.connect
def _get_reminder_cloner(sender, **kwargs):
    return ReminderCloner


class ReminderCloner(EventCloner):
    name = 'reminders'
    friendly_name = _('Reminders')
    is_default = True

    @property
    def is_available(self):
        return self._find_reminders(self.old_event).has_rows()

    def has_conflicts(self, target_event):
        return self._find_reminders(target_event).has_rows()

    def _find_reminders(self, event):
        return event.reminders.filter(db.m.EventReminder.is_relative)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        attrs = get_simple_column_attrs(db.m.EventReminder) - {'created_dt', 'scheduled_dt', 'is_sent'}
        attrs |= {'creator_id'}
        for old_reminder in self._find_reminders(self.old_event):
            scheduled_dt = new_event.start_dt - old_reminder.event_start_delta
            # Skip anything that's would have been sent on a past date.
            # We ignore the time on purpose so cloning an event shortly before will
            # still trigger a reminder that's just a few hours overdue.
            if scheduled_dt.date() < now_utc().date():
                logger.info('Not cloning reminder %s which would trigger at %s', old_reminder, scheduled_dt)
                continue
            reminder = db.m.EventReminder(**{attr: getattr(old_reminder, attr) for attr in attrs})
            reminder.scheduled_dt = scheduled_dt
            new_event.reminders.append(reminder)
            db.session.flush()
            logger.info('Added reminder during event cloning: %s', reminder)
