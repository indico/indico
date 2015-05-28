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
from indico.core.logger import Logger


logger = Logger.get('events.reminders')


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.events.reminders.tasks


@signals.event.data_changed.connect
def _event_data_changed(event, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    if event.has_legacy_id:
        return
    query = EventReminder.find(EventReminder.event_id == int(event.id),
                               EventReminder.is_relative,
                               ~EventReminder.is_sent)
    for reminder in query:
        new_dt = event.getStartDate() - reminder.event_start_delta
        if reminder.scheduled_dt != new_dt:
            logger.info('Changing start time of {} to {}'.format(reminder, new_dt))
            reminder.scheduled_dt = new_dt


@signals.event.deleted.connect
def _event_deleted(event, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    if event.has_legacy_id:
        return
    EventReminder.find(event_id=int(event.id)).delete()


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.reminders.models.reminders import EventReminder
    EventReminder.find(creator_id=source.id).update({EventReminder.creator_id: target.id})
