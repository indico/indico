# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, jsonify, redirect, render_template, request, session
from markupsafe import escape
from marshmallow import fields

from indico.core.db import db
from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.forms import ReminderForm
from indico.modules.events.reminders.models.reminders import EventReminder, ReminderType
from indico.modules.events.reminders.util import get_reminder_email_tpl
from indico.modules.events.reminders.views import WPReminders
from indico.util.date_time import format_datetime
from indico.util.i18n import _
from indico.util.string import PlainText, RichMarkup
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


class RHRemindersBase(RHManageEventBase):
    pass


class RHSpecificReminderBase(RHRemindersBase):
    """Base class for pages related to a specific reminder."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.reminder
        }
    }

    def _process_args(self):
        RHRemindersBase._process_args(self)
        self.reminder = EventReminder.get_or_404(request.view_args['reminder_id'])


class RHListReminders(RHRemindersBase):
    """Show the list of event reminders."""

    def _process(self):
        reminders = EventReminder.query.with_parent(self.event).order_by(EventReminder.scheduled_dt.desc()).all()
        return WPReminders.render_template('reminders.html', self.event, reminders=reminders)


class RHDeleteReminder(RHSpecificReminderBase):
    """Delete a reminder."""

    def _process(self):
        if self.reminder.is_sent:
            flash(_('Sent reminders cannot be deleted.'), 'error')
        else:
            db.session.delete(self.reminder)
            logger.info('Reminder deleted by %s: %s', session.user, self.reminder)
            flash(_('The reminder at {} has been deleted.')
                  .format(format_datetime(self.reminder.scheduled_dt)), 'success')
        return redirect(url_for('.list', self.event))


def _send_reminder(reminder):
    """Send reminder immediately."""
    reminder.send()
    logger.info('Reminder sent by %s: %s', session.user, reminder)
    flash(_('The reminder has been sent.'), 'success')


class RHEditReminder(RHSpecificReminderBase):
    """Modify an existing reminder."""

    def _get_defaults(self):
        reminder = self.reminder
        if reminder.is_start_time_relative:
            defaults_kwargs = {'schedule_type': 'start_time_relative',
                               'relative_delta': reminder.event_start_delta}
        elif reminder.is_end_time_relative:
            defaults_kwargs = {'schedule_type': 'end_time_relative',
                               'relative_delta': reminder.event_end_delta}
        else:
            defaults_kwargs = {'schedule_type': 'absolute',
                               'absolute_dt': reminder.scheduled_dt}
        return FormDefaults(reminder, **defaults_kwargs)

    def _process(self):
        reminder = self.reminder
        form = ReminderForm(obj=self._get_defaults(), event=self.event, render_mode=self.reminder.render_mode,
                            reminder_type=self.reminder.reminder_type)
        if form.validate_on_submit():
            if reminder.is_sent:
                flash(_('This reminder has already been sent and cannot be modified anymore.'), 'error')
                return redirect(url_for('.edit', reminder))
            form.populate_obj(reminder, existing_only=True)
            if form.schedule_type.data == 'now':
                _send_reminder(reminder)
            else:
                logger.info('Reminder modified by %s: %s', session.user, reminder)
                flash(_('The reminder at {} has been modified.')
                      .format(format_datetime(reminder.scheduled_dt)), 'success')
            return jsonify_data(flash=False)

        return jsonify_template('events/reminders/edit_reminder.html', event=self.event, reminder=reminder,
                                form=form)


class RHAddReminder(RHRemindersBase):
    """Add a new reminder."""

    @use_kwargs({
        'reminder_type': fields.Enum(ReminderType, required=True)
    }, location='query')
    def _process(self, reminder_type):
        form = ReminderForm(event=self.event,
                            schedule_type='start_time_relative',
                            attach_ical=reminder_type == ReminderType.standard,
                            reminder_type=reminder_type,
                            render_mode=RenderMode.html)
        if form.validate_on_submit():
            reminder = EventReminder(creator=session.user, event=self.event)
            form.populate_obj(reminder, existing_only=True)
            db.session.add(reminder)
            db.session.flush()
            if form.schedule_type.data == 'now':
                _send_reminder(reminder)
            else:
                logger.info('Reminder created by %s: %s', session.user, reminder)
                flash(_('A reminder at {} has been created.')
                      .format(format_datetime(reminder.scheduled_dt)), 'success')
            return jsonify_data(flash=False)

        return jsonify_template('events/reminders/edit_reminder.html', event=self.event, reminder=None, form=form)


class RHPreviewReminder(RHRemindersBase):
    """Preview the email for a reminder."""

    @use_kwargs({
        'reminder_type': fields.Enum(ReminderType, required=True),
        'render_mode': fields.Enum(RenderMode, required=True),
        'include_summary': fields.Boolean(required=True),
        'include_description': fields.Boolean(required=True),
        'subject': fields.String(required=True),
        'message': fields.String(required=True),
    })
    def _process(self, reminder_type, render_mode, include_summary, include_description, subject, message):
        if render_mode == RenderMode.plain_text:  # Legacy reminder (text/plain email only)
            message = PlainText(message)
        else:
            message = RichMarkup(message)
        with self.event.force_event_locale():
            html_email_tpl, text_email_tpl = get_reminder_email_tpl(self.event, reminder_type, render_mode,
                                                                    include_summary, include_description,
                                                                    escape(subject), message)
        email_tpl = html_email_tpl or text_email_tpl
        html = render_template('events/reminders/preview.html', render_mode=render_mode.name,
                               subject=email_tpl.get_subject(), body=email_tpl.get_body())
        return jsonify(html=html)
