# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request
from wtforms.fields import BooleanField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.modules.users.models.users import UserTitle
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import HiddenFieldList, IndicoEmailRecipientsField, IndicoEnumSelectField
from indico.web.forms.widgets import CKEditorWidget, SwitchWidget


class EmailEventPersonsForm(IndicoForm):
    from_address = SelectField(_('From'), [DataRequired()])
    subject = StringField(_('Subject'), [DataRequired()])
    body = TextAreaField(_('Email body'), [DataRequired()], widget=CKEditorWidget(simple=True))
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
        super(EmailEventPersonsForm, self).__init__(*args, **kwargs)
        self.from_address.choices = event.get_allowed_sender_emails().items()
        self.body.description = render_placeholder_info('event-persons-email', event=None, person=None,
                                                        register_link=register_link)

    def is_submitted(self):
        return super(EmailEventPersonsForm, self).is_submitted() and 'submitted' in request.form


class EventPersonForm(IndicoForm):
    title = IndicoEnumSelectField(_('Title'), enum=UserTitle, sorted=True)
    first_name = StringField(_('First name'), [DataRequired()])
    last_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'))
    address = TextAreaField(_('Address'))
    phone = StringField(_('Phone number'))
