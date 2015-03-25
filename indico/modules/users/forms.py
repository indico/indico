# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from wtforms.fields.core import SelectField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.fields.simple import StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.util.i18n import _, get_all_locales
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget

from operator import itemgetter
from pytz import all_timezones


_title_choices = [('', ''),
                  ('Mrs.', _('Mrs.')),
                  ('Ms.', _('Ms.')),
                  ('Mr.', _('Mr.')),
                  ('Dr.', _('Dr.')),
                  ('Prof.', _('Prof.'))]

_display_timezones = [('event', 'Event Timezone'),
                      ('user', 'My Timezone')]


class UserDetailsForm(IndicoForm):
    title = SelectField(_('Title'), [DataRequired()], choices=_title_choices)
    first_name = StringField(_('First name'), [DataRequired()])
    family_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'), [DataRequired()])
    address = TextAreaField(_('Address'))
    phone = StringField(_('Phone number'))


class UserPreferencesForm(IndicoForm):
    language = SelectField(_('Language'))
    timezone = SelectField(_('Timezone'))
    display_tz = SelectField(_('Display timezone'), choices=_display_timezones)
    show_past = BooleanField(_('Show past events'),
                             widget=SwitchWidget(),
                             description='Show past events by default.')

    def __init__(self, *args, **kwargs):
        super(UserPreferencesForm, self).__init__(*args, **kwargs)
        self.language.choices = sorted(get_all_locales().items(), key=itemgetter(1))
        self.timezone.choices = zip(all_timezones, all_timezones)


class UserEmailsForm(IndicoForm):
    email = EmailField(_('Add new email address'))
