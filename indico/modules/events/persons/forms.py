# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session, request
from wtforms.fields import StringField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired

from indico.modules.users.models.users import UserTitle
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoStaticTextField, HiddenFieldList, IndicoEnumSelectField
from indico.web.forms.widgets import CKEditorWidget


class EmailEventPersonsForm(IndicoForm):
    from_address = SelectField(_('From'), [DataRequired()])
    subject = StringField(_('Subject'), [DataRequired()])
    body = TextAreaField(_('Email body'), [DataRequired()], widget=CKEditorWidget(simple=True))
    recipients = IndicoStaticTextField(_('Recipients'))
    person_id = HiddenFieldList()
    user_id = HiddenFieldList()
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        super(EmailEventPersonsForm, self).__init__(*args, **kwargs)
        from_addresses = ['{} <{}>'.format(session.user.full_name, email)
                          for email in sorted(session.user.all_emails, key=lambda x: x != session.user.email)]
        self.from_address.choices = zip(from_addresses, from_addresses)

    def is_submitted(self):
        return super(EmailEventPersonsForm, self).is_submitted() and 'submitted' in request.form


class EventPersonForm(IndicoForm):
    title = IndicoEnumSelectField(_('Title'), enum=UserTitle)
    first_name = StringField(_('First name'), [DataRequired()])
    last_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'))
    address = TextAreaField(_('Address'))
    phone = StringField(_('Phone number'))
