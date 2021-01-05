# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.models.events import EventType
from indico.web.flask.templating import get_template_module


def make_reminder_email(event, with_agenda, with_description, note):
    """Return the template module for the reminder email.

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
