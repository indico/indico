# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import time

from markupsafe import escape
from wtforms.fields import BooleanField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional

from indico.core.db import db
from indico.modules.events.surveys.models.surveys import Survey
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import EmailListField, FileField, IndicoDateTimeField
from indico.web.forms.validators import HiddenUnless, LinkedDateTime, UsedIf, ValidationError
from indico.web.forms.widgets import SwitchWidget


class SurveyForm(IndicoForm):
    _notification_fields = ('notifications_enabled', 'notify_participants', 'start_notification_emails',
                            'new_submission_emails')

    title = StringField(_('Title'), [DataRequired()], description=_('The title of the survey'))
    introduction = TextAreaField(_('Introduction'), description=_('An introduction to be displayed before the survey'))
    anonymous = BooleanField(_('Anonymous submissions'), widget=SwitchWidget(),
                             description=_('User information will not be attached to submissions'))
    require_user = BooleanField(_('Only logged-in users'), [HiddenUnless('anonymous')], widget=SwitchWidget(),
                                description=_('Require users to be logged in for submitting the survey'))
    limit_submissions = BooleanField(_('Limit submissions'), widget=SwitchWidget(),
                                     description=_('Whether there is a submission cap'))
    submission_limit = IntegerField(_('Capacity'),
                                    [HiddenUnless('limit_submissions'), DataRequired(), NumberRange(min=1)],
                                    description=_('Maximum number of submissions accepted'))
    private = BooleanField(_('Private survey'), widget=SwitchWidget(),
                           description=_('Only selected people can answer the survey.'))
    partial_completion = BooleanField(_('Partial completion'), widget=SwitchWidget(),
                                      description=_('Allow to save answers without submitting the survey.'))
    notifications_enabled = BooleanField(_('Enabled'), widget=SwitchWidget(),
                                         description=_('Send email notifications for specific events related to the '
                                                       'survey.'))
    notify_participants = BooleanField(_('Participants'), [HiddenUnless('notifications_enabled', preserve_data=True)],
                                       widget=SwitchWidget(),
                                       description=_('Notify participants of the event when this survey starts.'))
    start_notification_emails = EmailListField(_('Start notification recipients'),
                                               [HiddenUnless('notifications_enabled', preserve_data=True)],
                                               description=_('Email addresses to notify about the start of the survey'))
    new_submission_emails = EmailListField(_('New submission notification recipients'),
                                           [HiddenUnless('notifications_enabled', preserve_data=True)],
                                           description=_('Email addresses to notify when a new submission is made'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)

    def validate_title(self, field):
        query = (Survey.query.with_parent(self.event)
                 .filter(db.func.lower(Survey.title) == field.data.lower(),
                         Survey.title != field.object_data,
                         ~Survey.is_deleted))
        if query.count():
            raise ValidationError(_('There is already a survey named "{}" on this event').format(escape(field.data)))

    def post_validate(self):
        if not self.anonymous.data:
            self.require_user.data = True


class ScheduleSurveyForm(IndicoForm):
    start_dt = IndicoDateTimeField(_('Start'), [UsedIf(lambda form, field: form.allow_reschedule_start), Optional()],
                                   default_time=time(0, 0),
                                   description=_('Moment when the survey will open for submissions'))
    end_dt = IndicoDateTimeField(_('End'), [Optional(), LinkedDateTime('start_dt')],
                                 default_time=time(23, 59),
                                 description=_('Moment when the survey will close'))
    resend_start_notification = BooleanField(_('Resend start notification'), widget=SwitchWidget(),
                                             description=_('Resend the survey start notification.'))

    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey')
        self.allow_reschedule_start = kwargs.pop('allow_reschedule_start')
        self.timezone = survey.event.timezone
        super().__init__(*args, **kwargs)
        if not survey.start_notification_sent or not self.allow_reschedule_start:
            del self.resend_start_notification


class SectionForm(IndicoForm):
    display_as_section = BooleanField(_('Display as section'), widget=SwitchWidget(), default=True,
                                      description=_('Whether this is going to be displayed as a section or standalone'))
    title = StringField(_('Title'), [HiddenUnless('display_as_section', preserve_data=True), DataRequired()],
                        description=_('The title of the section.'))
    description = TextAreaField(_('Description'), [HiddenUnless('display_as_section', preserve_data=True)],
                                description=_('You may use Markdown for formatting.'))


class TextForm(IndicoForm):
    description = TextAreaField(_('Text'),
                                description=_('The text that should be displayed.'))


class ImportQuestionnaireForm(IndicoForm):
    json_file = FileField(_('File'), [DataRequired(_('You need to upload a JSON file.'))],
                          accepted_file_types='application/json,.json',
                          description=_('Choose a previously exported survey content to import. '
                                        'Existing sections will be preserved.'))
