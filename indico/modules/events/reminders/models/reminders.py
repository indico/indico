# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.notifications import make_email, send_email
from indico.modules.core.settings import core_settings
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.ical import MIMECalendar, event_to_ical
from indico.modules.events.models.events import EventType
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.reminders import logger
from indico.modules.events.reminders.util import make_reminder_email
from indico.util.date_time import now_utc
from indico.util.signals import values_from_signal
from indico.util.string import format_repr


class EventReminder(db.Model):
    """Email reminders for events."""

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
    #: If the notification should also be sent to all event speakers
    send_to_speakers = db.Column(
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
    #: If the notification should include the event's iCalendar file.
    attach_ical = db.Column(
        db.Boolean,
        nullable=False,
        default=True
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
        """Return all recipients of the notifications.

        This includes both explicit recipients and, if enabled,
        participants/speakers of the event.
        """
        recipients = set(self.recipients)
        if self.send_to_participants:
            recipients.update(reg.email for reg in Registration.get_all_for_event(self.event))

        if self.send_to_speakers:
            recipients.update(person_link.email for person_link in self.event.person_links)

            # contribution/sub-contribution speakers are present only in meetings and conferences
            if self.event.type != EventType.lecture:
                contrib_speakers = (
                    ContributionPersonLink.query
                    .filter(
                        ContributionPersonLink.is_speaker,
                        ContributionPersonLink.contribution.has(is_deleted=False, event=self.event)
                    )
                    .all()
                )

                subcontrib_speakers = (
                    SubContributionPersonLink.query
                    .filter(
                        SubContributionPersonLink.is_speaker,
                        SubContributionPersonLink.subcontribution.has(
                            db.and_(
                                ~SubContribution.is_deleted,
                                SubContribution.contribution.has(is_deleted=False, event=self.event)
                            )
                        )
                    )
                    .all()
                )

                recipients.update(speaker.email for speaker in contrib_speakers)
                recipients.update(speaker.email for speaker in subcontrib_speakers)

        recipients.discard('')  # just in case there was an empty email address somewhere
        return recipients

    @hybrid_property
    def is_relative(self):
        """Return if the reminder is relative to the event time."""
        return self.event_start_delta is not None

    @is_relative.expression
    def is_relative(cls):
        return cls.event_start_delta.isnot(None)

    @property
    def is_overdue(self):
        return not self.is_sent and self.scheduled_dt <= now_utc()

    def _make_email(self, recipient, template, attachments):
        email_params = {
            'to_list': recipient,
            'from_address': self.reply_to_address,
            'template': template,
            'attachments': attachments
        }
        extra_params = signals.event.reminder.before_reminder_make_email.send(self, **email_params)
        for param in values_from_signal(extra_params, as_list=True):
            email_params.update(param)
        return make_email(**email_params)

    def send(self):
        """Send the reminder to its recipients."""
        self.is_sent = True
        recipients = self.all_recipients
        if not recipients:
            logger.info('Notification %s has no recipients; not sending anything', self)
            return
        with self.event.force_event_locale():
            email_tpl = make_reminder_email(self.event, self.include_summary, self.include_description, self.message)
        attachments = []
        if self.attach_ical:
            event_ical = event_to_ical(self.event, skip_access_check=True, method='REQUEST',
                                       organizer=(core_settings.get('site_title'), config.NO_REPLY_EMAIL))
            attachments.append(MIMECalendar('event.ics', event_ical))

        for recipient in recipients:
            with self.event.force_event_locale():
                email = self._make_email(recipient, email_tpl, attachments)
            send_email(email, self.event, 'Reminder', self.creator, log_metadata={'reminder_id': self.id})

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'scheduled_dt', is_sent=False)
