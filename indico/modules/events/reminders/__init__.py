# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.logger import Logger
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem

from MaKaC.conference import EventCloner


logger = Logger.get('events.reminders')


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.events.reminders.tasks


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    return SideMenuItem('reminders', _('Reminders'), url_for('event_reminders.list', event), section='organization')


@signals.event.data_changed.connect
def _event_data_changed(event, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    query = EventReminder.find(EventReminder.event_id == int(event.id),
                               EventReminder.is_relative,
                               ~EventReminder.is_sent)
    for reminder in query:
        new_dt = event.getStartDate() - reminder.event_start_delta
        if reminder.scheduled_dt != new_dt:
            logger.info('Changing start time of {} to {}'.format(reminder, new_dt))
            reminder.scheduled_dt = new_dt


@signals.event_management.clone.connect
def _get_reminder_cloner(event, **kwargs):
    return ReminderCloner(event)


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    EventReminder.find(creator_id=source.id).update({EventReminder.creator_id: target.id})


class ReminderCloner(EventCloner):
    def find_reminders(self):
        from indico.modules.events.reminders.models.reminders import EventReminder
        return EventReminder.find(EventReminder.is_relative, EventReminder.event_id == int(self.event.id))

    def get_options(self):
        enabled = bool(self.find_reminders().count())
        return {'reminders': (_('Reminders'), enabled, True)}

    def clone(self, new_event, options):
        from indico.modules.events.reminders.models.reminders import EventReminder
        if 'reminders' not in options:
            return
        attrs = get_simple_column_attrs(EventReminder) - {'created_dt', 'scheduled_dt', 'is_sent'}
        attrs |= {'creator_id'}
        for old_reminder in self.find_reminders():
            scheduled_dt = new_event.getStartDate() - old_reminder.event_start_delta
            # Skip anything that's would have been sent on a past date.
            # We ignore the time on purpose so cloning an event shortly before will
            # still trigger a reminder that's just a few hours overdue.
            if scheduled_dt.date() < now_utc().date():
                logger.info('Not cloning reminder {} which would trigger at {}'.format(old_reminder, scheduled_dt))
                continue
            reminder = EventReminder(event=new_event, **{attr: getattr(old_reminder, attr) for attr in attrs})
            reminder.scheduled_dt = scheduled_dt
            db.session.add(reminder)
            db.session.flush()
            logger.info('Added reminder during event cloning: {}'.format(reminder))
