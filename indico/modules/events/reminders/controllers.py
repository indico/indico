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

from babel.dates import get_timezone
from flask import request, session, redirect, flash, jsonify, render_template

from indico.core.db import db
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.forms import ReminderForm
from indico.modules.events.reminders.models.reminders import EventReminder
from indico.modules.events.reminders.util import make_reminder_email
from indico.modules.events.reminders.views import WPReminders
from indico.util.date_time import format_datetime
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHRemindersBase(RHConferenceModifBase):
    ALLOW_LEGACY_IDS = False
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.event = self._conf


class RHSpecificReminderBase(RHRemindersBase):
    """Base class for pages related to a specific reminder"""

    def _checkParams(self, params):
        RHRemindersBase._checkParams(self, params)
        self.reminder = EventReminder.find_one(id=request.view_args['id'], event_id=int(self.event.id))


class RHListReminders(RHRemindersBase):
    """Shows the list of event reminders"""

    def _process(self):
        reminders = EventReminder.find(event_id=self.event.id).order_by(EventReminder.scheduled_dt.desc()).all()
        tz = get_timezone(DisplayTZ(conf=self.event).getDisplayTZ())
        return WPReminders.render_template('reminders.html', self.event, event=self.event, reminders=reminders,
                                           timezone=tz)


class RHDeleteReminder(RHSpecificReminderBase):
    """Deletes a reminder"""

    def _process(self):
        if self.reminder.is_sent:
            flash(_('Sent reminders cannot be deleted.'), 'error')
        else:
            db.session.delete(self.reminder)
            logger.info('Reminder deleted by {}: {}'.format(session.user, self.reminder))
            flash(_("The reminder at {} has been deleted.").format(format_datetime(self.reminder.scheduled_dt)),
                  'success')
        return redirect(url_for('.list', self.event))


def _send_reminder(reminder):
    """Send reminder immediately"""
    reminder.send()
    logger.info('Reminder sent by {}: {}'.format(session.user, reminder))
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
            tz = get_timezone(DisplayTZ(conf=self.event).getDisplayTZ())
            dt = reminder.scheduled_dt.astimezone(tz)
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
                logger.info('Reminder modified by {}: {}'.format(session.user, reminder))
                flash(_("The reminder at {} has been modified.").format(format_datetime(reminder.scheduled_dt)),
                      'success')
            return redirect(url_for('.list', self.event))

        widget_attrs = ({field.short_name: {'disabled': True} for field in form}
                        if reminder.is_sent
                        else form.default_widget_attrs)
        return WPReminders.render_template('edit_reminder.html', self.event, event=self.event, reminder=reminder,
                                           form=form, widget_attrs=widget_attrs)


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
                logger.info('Reminder created by {}: {}'.format(session.user, reminder))
                flash(_("A reminder at {} has been created.").format(format_datetime(reminder.scheduled_dt)), 'success')
            return redirect(url_for('.list', self.event))

        return WPReminders.render_template('edit_reminder.html', self.event, event=self.event, reminder=None, form=form,
                                           widget_attrs=form.default_widget_attrs)


class RHPreviewReminder(RHRemindersBase):
    """Previews the email for a reminder"""

    def _process(self):
        tpl = make_reminder_email(self.event, request.form.get('include_summary') == '1', request.form.get('message'))
        html = render_template('events/reminders/preview.html', subject=tpl.get_subject(), body=tpl.get_body())
        return jsonify(html=html)
