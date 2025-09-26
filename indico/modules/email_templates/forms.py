# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import StringField, TextAreaField
from wtforms.fields.choices import SelectField
from wtforms.validators import DataRequired, Length

from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import NoRelativeURLs, HiddenUnless
from indico.web.forms.widgets import TinyMCEWidget


class CreateEmailTemplatesForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired(), Length(max=100)])
    subject = StringField(_("Subject"), [DataRequired(), Length(max=75)])
    body = TextAreaField(_("Email body"), [DataRequired(), NoRelativeURLs()],
                            widget=TinyMCEWidget(absolute_urls=True, images=True))
    type = SelectField(_("Email type"), [DataRequired()],
                       choices=[('event', _('Event')), ('registration', _('Registration')),
                                ('reminders', _('Reminders'))])
    status = SelectField(_("Status"), [HiddenUnless('type', value='registration')],
                               choices=[('pending', _('Pending')), ('approved', _('Approved')),
                                        ('rejected', _('Rejected'))])
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body.description = (render_placeholder_info('registration-email', regform=None, registration=None))
