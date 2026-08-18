# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

from indico.modules.email_templates.models.email_templates import EmailTemplateType, RegistrationNotificationType
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.validators import HiddenUnless, NoRelativeURLs
from indico.web.forms.widgets import SwitchWidget, TinyMCEWidget


class CreateEmailTemplatesForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired(), Length(max=100)])
    subject = StringField(_('Subject'), [DataRequired(), Length(max=75)])
    body = TextAreaField(_('Email body'), [DataRequired(), NoRelativeURLs()],
                         widget=TinyMCEWidget(absolute_urls=True, images=True))
    notification_type = IndicoEnumSelectField(_('Email Notification type'), enum=RegistrationNotificationType, none='')
    status = IndicoEnumSelectField(_('Status'),
                                   [HiddenUnless('notification_type',
                                                 value=RegistrationNotificationType.registration_state_update),
                                    DataRequired()],
                                   enum=RegistrationState,
                                   titles=[None, _('Approved'), _('Pending'), _('Rejected'), _('Withdrawn'),
                                           _('Awaiting payment')])
    is_active = BooleanField(_('Is Active'), widget=SwitchWidget(), default=True,
                             description=_('Allow users to disable some email templates, '
                                           'system template will be used as default.'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = kwargs['target']
        self.email_template_type = kwargs['email_template_type']
        if self.email_template_type == EmailTemplateType.registration:
            self.body.description = render_placeholder_info('registration-email', regform=None, registration=None)
        else:
            self.body.description = render_placeholder_info('registration-invitation-email', invitation=None)
            del self.notification_type
            del self.status
            del self.is_active

    def validate_is_active(self, field):
        if not field.data:
            return
        if self.email_template_type != EmailTemplateType.registration:
            return
        email_templates = [email_tpl for email_tpl in self.target.email_templates
                           if email_tpl.notification_type == self.notification_type.data]
        if status := self.status.data:
            email_templates = [email_tpl for email_tpl in email_templates
                               if email_tpl.rules and email_tpl.rules.get('status') == status.name]
        if any(tpl.is_active for tpl in email_templates):
            email_tpl = email_templates.pop()
            raise ValidationError(_("There's already an active {} template with same notification rule")
                                  .format(email_tpl.title))

    @generated_data
    def type(self):
        return self.email_template_type


class EditEmailTemplatesForm(CreateEmailTemplatesForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
