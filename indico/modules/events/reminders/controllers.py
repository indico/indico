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

from flask import flash, jsonify, redirect, render_template, request, session

from indico.core.db import db
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.forms import ReminderForm
from indico.modules.events.reminders.models.reminders import EventReminder
from indico.modules.events.reminders.util import make_reminder_email
from indico.modules.events.reminders.views import WPReminders
from indico.util.date_time import format_datetime
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


class RHRemindersBase(RHManageEventBase):
    pass


class RHSpecificReminderBase(RHRemindersBase):
    """Base class for pages related to a specific reminder"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.reminder
        }
    }

    def _process_args(self):
        RHRemindersBase._process_args(self)
        self.reminder = EventReminder.get_one(request.view_args['reminder_id'])


class RHListReminders(RHRemindersBase):
    """Shows the list of event reminders"""

    def _process(self):
        reminders = EventReminder.query.with_parent(self.event).order_by(EventReminder.scheduled_dt.desc()).all()
        return WPReminders.render_template('reminders.html', self.event, reminders=reminders)


class RHDeleteReminder(RHSpecificReminderBase):
    """Deletes a reminder"""

    def _process(self):
        if self.reminder.is_sent:
            flash(_('Sent reminders cannot be deleted.'), 'error')
        else:
            db.session.delete(self.reminder)
            logger.info('Reminder deleted by %s: %s', session.user, self.reminder)
            flash(_("The reminder at {} has been deleted.")
                  .format(to_unicode(format_datetime(self.reminder.scheduled_dt))), 'success')
        return redirect(url_for('.list', self.event))


def _send_reminder(reminder):
    """Send reminder immediately"""
    reminder.send()
    logger.info('Reminder sent by %s: %s', session.user, reminder)
    flash(_('The reminder has been sent.'), 'success')


class RHEditReminder(RHSpecificReminderBase):
    """Modifies an existing reminder"""

    def _get_defaults(self):
        reminder = self.reminder
        if reminder.is_relative:
            defaults_kwargs = {'schedule_type': 'relative',
                               'relative_delta': reminder.event_start_delta}
        else:
            # Use the user's preferred event timezone
            dt = reminder.scheduled_dt.astimezone(self.event.tzinfo)
            defaults_kwargs = {'schedule_type': 'absolute',
                               'absolute_date': dt.date(),
                               'absolute_time': dt.time()}
        return FormDefaults(reminder, **defaults_kwargs)

    def _process(self):
        reminder = self.reminder
        form = ReminderForm(obj=self._get_defaults(), event=self.event)
        if form.validate_on_submit():
            if reminder.is_sent:
                flash(_("This reminder has already been sent and cannot be modified anymore."), 'error')
                return redirect(url_for('.edit', reminder))
            form.populate_obj(reminder, existing_only=True)
            if form.schedule_type.data == 'now':
                _send_reminder(reminder)
            else:
                logger.info('Reminder modified by %s: %s', session.user, reminder)
                flash(_("The reminder at {} has been modified.")
                      .format(to_unicode(format_datetime(reminder.scheduled_dt))), 'success')
            return jsonify_data(flash=False)

        return jsonify_template('events/reminders/edit_reminder.html', event=self.event, reminder=reminder,
                                form=form)


class RHAddReminder(RHRemindersBase):
    """Adds a new reminder"""

    def _process(self):
        form = ReminderForm(event=self.event, schedule_type='relative')
        if form.validate_on_submit():
            reminder = EventReminder(creator=session.user, event=self.event)
            form.populate_obj(reminder, existing_only=True)
            db.session.add(reminder)
            db.session.flush()
            if form.schedule_type.data == 'now':
                _send_reminder(reminder)
            else:
                logger.info('Reminder created by %s: %s', session.user, reminder)
                flash(_("A reminder at {} has been created.")
                      .format(to_unicode(format_datetime(reminder.scheduled_dt))), 'success')
            return jsonify_data(flash=False)

        return jsonify_template('events/reminders/edit_reminder.html', event=self.event, reminder=None, form=form,
                                widget_attrs=form.default_widget_attrs)


class RHPreviewReminder(RHRemindersBase):
    """Previews the email for a reminder"""

    def _process(self):
        include_summary = request.form.get('include_summary') == '1'
        include_description = request.form.get('include_description') == '1'
        tpl = make_reminder_email(self.event, include_summary, include_description, request.form.get('message'))
        html = render_template('events/reminders/preview.html', subject=tpl.get_subject(), body=tpl.get_body())
        return jsonify(html=html)
