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

from datetime import timedelta

from flask import session, request
from wtforms.fields import StringField, BooleanField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired

from indico.modules.events.sessions.util import get_colors
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoPalettePickerField, TimeDeltaField, JSONField
from indico.web.forms.widgets import SwitchWidget, CKEditorWidget


class SessionForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_('Title of the session'))
    code = StringField(_('Session code'), description=_('Code of the session'))
    description = StringField(_('Description'), description=_('Text describing the session'))
    default_contribution_duration = TimeDeltaField(_('Default contribution duration'), units=('minutes', 'hours'),
                                                   description=_('Specify the default duration of contributions '
                                                                 'within the session'),
                                                   default=timedelta(minutes=20))
    colors = IndicoPalettePickerField(_('Colours'), color_list=get_colors(),
                                      description=_('Specify text and background colours for the session.'))
    is_poster = BooleanField(_('Poster session'), widget=SwitchWidget(),
                             description=_('Whether the session is a poster session.'))


class EmailSessionPersonsForm(IndicoForm):
    from_address = SelectField(_('From'), [DataRequired()], choices=[(1, 1)])
    subject = StringField(_('Subject'), [DataRequired()])
    body = TextAreaField(_('Email body'), [DataRequired()], widget=CKEditorWidget(simple=True))
    event_persons = JSONField(_('Event Persons'), default=[])
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        super(EmailSessionPersonsForm, self).__init__(*args, **kwargs)
        from_addresses = ['{} <{}>'.format(session.user.full_name, email)
                          for email in sorted(session.user.all_emails, key=lambda x: x != session.user.email)]
        self.from_address.choices = zip(from_addresses, from_addresses)

    def is_submitted(self):
        return super(EmailSessionPersonsForm, self).is_submitted() and 'submitted' in request.form
