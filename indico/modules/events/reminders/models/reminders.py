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

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.util import make_reminder_email
from indico.util.date_time import now_utc
from indico.util.string import format_repr, return_ascii


class EventReminder(db.Model):
    """Email reminders for events"""
    __tablename__ = 'reminders'
    __table_args__ = (db.Index(None, 'scheduled_dt', postgresql_where=db.text('not is_sent')),
                      {'schema': 'events'})

    #: The ID of the reminder
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The ID of the user who created the reminder
    creator_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    #: The date/time when the reminder was created
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: The date/time when the reminder should be sent
    scheduled_dt = db.Column(
        UTCDateTime,
        nullable=False
    )
    #: If the reminder has been sent
    is_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: How long before the event start the reminder should be sent
    #: This is needed to update the `scheduled_dt` when changing the
    #: start  time of the event.
    event_start_delta = db.Column(
        db.Interval,
        nullable=True
    )
    #: The recipients of the notification
    recipients = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    #: If the notification should also be sent to all event participants
    send_to_participants = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: If the notification should include a summary of the event's schedule.
    include_summary = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: If the notification should include the event's description.
    include_description = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The address to use as Reply-To in the notification email.
    reply_to_address = db.Column(
        db.String,
        nullable=False
    )
    #: Custom message to include in the email
    message = db.Column(
        db.String,
        nullable=False,
        default=''
    )

    #: The user who created the reminder
    creator = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'event_reminders',
            lazy='dynamic'
        )
    )
    #: The Event this reminder is associated with
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'reminders',
            lazy='dynamic'
        )
    )

    @property
    def locator(self):
        return dict(self.event.locator, reminder_id=self.id)

    @property
    def all_recipients(self):
        """Returns all recipients of the notifications.

        This includes both explicit recipients and, if enabled,
        participants of the event.
        """
        recipients = set(self.recipients)
        if self.send_to_participants:
            recipients.update(reg.email for reg in Registration.get_all_for_event(self.event))
        recipients.discard('')  # just in case there was an empty email address somewhere
        return recipients

    @hybrid_property
    def is_relative(self):
        """Returns if the reminder is relative to the event time"""
        return self.event_start_delta is not None

    @is_relative.expression
    def is_relative(self):
        return self.event_start_delta != None  # NOQA

    @property
    def is_overdue(self):
        return not self.is_sent and self.scheduled_dt <= now_utc()

    def send(self):
        """Sends the reminder to its recipients."""
        self.is_sent = True
        recipients = self.all_recipients
        if not recipients:
            logger.info('Notification %s has no recipients; not sending anything', self)
            return
        email_tpl = make_reminder_email(self.event, self.include_summary, self.include_description, self.message)
        email = make_email(bcc_list=recipients, from_address=self.reply_to_address, template=email_tpl)
        send_email(email, self.event, 'Reminder', self.creator)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'scheduled_dt', is_sent=False)
