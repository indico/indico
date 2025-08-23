# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.models.events import EventType
from indico.util.string import html_to_markdown
from indico.web.flask.templating import get_template_module


def get_reminder_email_tpl(event, reminder_type, render_mode, with_agenda, with_description, subject, message):
    """Return template modules for reminder email in both text/html abd text/plain format if applicable.

    Legacy reminder (text/plain message) -> text/plain email format only
    Standard reminder (text/html message) -> both text/html and text/plain email format
    Custom reminder (text/html message) -> text/html email format only

    :param event: The event
    :param reminder_type: standard|custom
    :param render_mode: plain_text|html
    :param with_agenda: If the event's agenda should be included
    :param subject: Subject for the custom reminder
    :param message: A custom message to include in the email (full email body for custom reminder)

    :return: tuple of templates for text/html and text/plain representation
    """
    from indico.modules.events.reminders.models.reminders import ReminderType

    if reminder_type == ReminderType.custom:
        html_tpl = get_template_module('emails/custom.html',
                                       url=event.short_external_url, subject=subject, body=message)
        return html_tpl, None

    if event.type_ == EventType.lecture:
        with_agenda = False
    agenda = event.timetable_entries.filter_by(parent_id=None).all() if with_agenda else None
    text_message = str(message)  # Legacy reminder (text/plain email only)
    if text_message and render_mode == RenderMode.html:
        # Standard reminder (text/html -> text/plain)
        text_message = html_to_markdown(text_message, inline_links=False).strip()
    text_tpl = get_template_module('events/reminders/emails/event_reminder.txt', event=event,
                                    url=event.short_external_url, note=text_message, with_agenda=with_agenda,
                                    with_description=with_description, agenda=agenda)
    html_tpl = None
    if render_mode == RenderMode.html:
        html_tpl = get_template_module('events/reminders/emails/event_reminder.html', event=event,
                                        url=event.short_external_url, note=message, with_agenda=with_agenda,
                                        with_description=with_description, agenda=agenda)

    return html_tpl, text_tpl
