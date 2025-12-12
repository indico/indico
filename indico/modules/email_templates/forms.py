# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import BooleanField, StringField, TextAreaField
from wtforms.fields.choices import SelectField
from wtforms.validators import DataRequired, Length, ValidationError

from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import HiddenUnless, NoRelativeURLs
from indico.web.forms.widgets import SwitchWidget, TinyMCEWidget


class CreateEmailTemplatesForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired(), Length(max=100)])
    subject = StringField(_('Subject'), [DataRequired(), Length(max=75)])
    body = TextAreaField(_('Email body'), [DataRequired(), NoRelativeURLs()],
                         widget=TinyMCEWidget(absolute_urls=True, images=True))
    type = SelectField(_('Email Notification type'), [DataRequired()],
                       choices=[('registration_creation', _('Registration Creation')),
                                ('registration_state_update', _('Registration State Update')),
                                ('registration_modification', _('Registration Modification')),
                                ('registration_receipt_creation', _('Registration Receipt Creation'))])
    status = SelectField(_('Status'), [DataRequired(), HiddenUnless('type', value='registration_state_update')],
                         choices=[('pending', _('Pending')), ('complete', _('Approved')), ('rejected', _('Rejected'))])
    is_active = BooleanField(_('Is Active'), widget=SwitchWidget(), default=True,
                             description=_('Allow users to disable some email templates, '
                                           'system template will be used as default.'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = kwargs['target']
        self.body.description = (render_placeholder_info('registration-email', regform=None, registration=None))

    def validate_is_active(self, field):
        if not field.data:
            return
        email_templates = [email_tpl for email_tpl in self.target.email_templates if email_tpl.type == self.type.data]
        if status := self.status.data:
            email_templates = [email_tpl for email_tpl in email_templates
                               if email_tpl.rules and email_tpl.rules.get('status') == status]
        if any(tpl.is_active for tpl in email_templates):
            email_tpl = email_templates.pop()
            raise ValidationError(_("There's already an active {} template with same notification rule")
                                  .format(email_tpl.title))


class EditEmailTemplatesForm(CreateEmailTemplatesForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
