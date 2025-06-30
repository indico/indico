# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.models.events import EventType
from indico.web.flask.templating import get_template_module


def make_reminder_email(event, with_agenda, with_description, note):
    """Return template modules for reminder email in both text/plain and text/html format.

    :param event: The event
    :param with_agenda: If the event's agenda should be included
    :param note: A custom message to include in the email

    :return: tuple of templates for text/plain and text/html representation
    """
    if event.type_ == EventType.lecture:
        with_agenda = False
    agenda = event.timetable_entries.filter_by(parent_id=None).all() if with_agenda else None
    text_tpl = get_template_module('events/reminders/emails/event_reminder.txt', event=event,
                                    url=event.short_external_url, note=note, with_agenda=with_agenda,
                                    with_description=with_description, agenda=agenda)
    html_tpl = get_template_module('events/reminders/emails/event_reminder.html', event=event,
                                    url=event.short_external_url, note=note, with_agenda=with_agenda,
                                    with_description=with_description, agenda=agenda)
    return text_tpl, html_tpl
