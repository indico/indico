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

from indico.modules.events.models.events import EventType
from indico.web.flask.templating import get_template_module


def make_reminder_email(event, with_agenda, with_description, note):
    """Returns the template module for the reminder email.

    :param event: The event
    :param with_agenda: If the event's agenda should be included
    :param note: A custom message to include in the email
    """
    if event.type_ == EventType.lecture:
        with_agenda = False
    agenda = event.timetable_entries.filter_by(parent_id=None).all() if with_agenda else None
    return get_template_module('events/reminders/emails/event_reminder.txt', event=event,
                               url=event.short_external_url, note=note, with_agenda=with_agenda,
                               with_description=with_description, agenda=agenda)
