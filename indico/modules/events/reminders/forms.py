# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.modules.events.models.events import EventType
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import EmailListField, IndicoDateTimeField, IndicoRadioField, TimeDeltaField
from indico.web.forms.validators import DateTimeRange, HiddenUnless


class ReminderForm(IndicoForm):
    recipient_fields = {'recipients', 'send_to_participants'}
    schedule_fields = {'schedule_type', 'absolute_dt', 'relative_delta'}
    schedule_recipient_fields = recipient_fields | schedule_fields

    # Schedule
    schedule_type = IndicoRadioField(_('Type'), [DataRequired()],
                                     choices=[('relative', _("Relative to the event start time")),
                                              ('absolute', _("Fixed date/time")),
                                              ('now', _('Send immediately'))])
    relative_delta = TimeDeltaField(_('Offset'), [HiddenUnless('schedule_type', 'relative'), DataRequired()])
    absolute_dt = IndicoDateTimeField(_('Date'), [HiddenUnless('schedule_type', 'absolute'), DataRequired(),
                                                  DateTimeRange()])
    # Recipients
    recipients = EmailListField(_('Email addresses'), description=_('One email address per line.'))
    send_to_participants = BooleanField(_('Participants'),
                                        description=_('Send the reminder to all participants/registrants '
                                                      'of the event.'))
    # Misc
    reply_to_address = SelectField(_('Sender'), [DataRequired()],
                                   description=_('The email address that will show up as the sender.'))
    message = TextAreaField(_('Note'), description=_('A custom message to include in the email.'))
    include_summary = BooleanField(_('Include agenda'),
                                   description=_("Includes a simple text version of the event's agenda in the email."))
    include_description = BooleanField(_('Include description'),
                                       description=_("Includes the event's description in the email."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.timezone = self.event.timezone
        super(ReminderForm, self).__init__(*args, **kwargs)
        self.reply_to_address.choices = (self.event
                                         .get_allowed_sender_emails(extra=self.reply_to_address.object_data)
                                         .items())
        if self.event.type_ == EventType.lecture:
            del self.include_summary

    def validate_recipients(self, field):
        if not field.data and not self.send_to_participants.data:
            raise ValidationError(_('If participants are not included you need to specify recipients.'))

    def validate_send_to_participants(self, field):
        if not field.data and not self.recipients.data:
            raise ValidationError(_('If no recipients are specified you need to include participants.'))

    def validate_schedule_type(self, field):
        # Be graceful and allow a reminder that's in the past but on the same day.
        # It will be sent immediately but that way we are a little bit more user-friendly
        if field.data == 'now':
            return
        scheduled_dt = self.scheduled_dt.data
        if scheduled_dt is not None and scheduled_dt.date() < now_utc().date():
            raise ValidationError(_('The specified date is in the past'))

    @generated_data
    def scheduled_dt(self):
        if self.schedule_type.data == 'absolute':
            if self.absolute_dt.data is None:
                return None
            return self.absolute_dt.data
        elif self.schedule_type.data == 'relative':
            if self.relative_delta.data is None:
                return None
            return self.event.start_dt - self.relative_delta.data
        elif self.schedule_type.data == 'now':
            return now_utc()

    @generated_data
    def event_start_delta(self):
        return self.relative_delta.data if self.schedule_type.data == 'relative' else None
