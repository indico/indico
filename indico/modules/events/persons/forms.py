# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request
from wtforms.fields import BooleanField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import HiddenFieldList, IndicoEmailRecipientsField
from indico.web.forms.widgets import CKEditorWidget, SwitchWidget


class EmailEventPersonsForm(IndicoForm):
    from_address = SelectField(_('From'), [DataRequired()])
    subject = StringField(_('Subject'), [DataRequired()])
    body = TextAreaField(_('Email body'), [DataRequired()], widget=CKEditorWidget())
    recipients = IndicoEmailRecipientsField(_('Recipients'))
    copy_for_sender = BooleanField(_('Send copy to me'), widget=SwitchWidget(),
                                   description=_('Send copy of each email to my mailbox'))
    person_id = HiddenFieldList()
    user_id = HiddenFieldList()
    role_id = HiddenFieldList()
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        register_link = kwargs.pop('register_link')
        event = kwargs.pop('event')
        super().__init__(*args, **kwargs)
        self.from_address.choices = list(event.get_allowed_sender_emails().items())
        self.body.description = render_placeholder_info('event-persons-email', event=None, person=None,
                                                        register_link=register_link)

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form
