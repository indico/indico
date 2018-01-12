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
    import indico.modules.events.reminders.tasks


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
        return self._find_reminders().has_rows()

    def _find_reminders(self):
        return self.old_event.reminders.filter(db.m.EventReminder.is_relative)

    def run(self, new_event, cloners, shared_data):
        attrs = get_simple_column_attrs(db.m.EventReminder) - {'created_dt', 'scheduled_dt', 'is_sent'}
        attrs |= {'creator_id'}
        for old_reminder in self._find_reminders():
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
