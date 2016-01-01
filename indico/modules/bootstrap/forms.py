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

from operator import itemgetter

from wtforms import validators, TextField, SelectField, BooleanField
from wtforms.fields.html5 import EmailField

from indico.modules.auth.forms import LocalRegistrationForm
from indico.util.i18n import _, get_all_locales
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget


class BootstrapForm(LocalRegistrationForm):
    first_name = TextField('First Name', [validators.Required()])
    last_name = TextField('Last Name', [validators.Required()])
    email = EmailField(_('Email address'), [validators.Required()])
    language = SelectField('Language', [validators.Required()])
    affiliation = TextField('Affiliation', [validators.Required()])
    enable_tracking = BooleanField('Join the community', widget=SwitchWidget())
    contact_name = TextField('Contact Name',
                             [UsedIfChecked('enable_tracking'), validators.Required()])
    contact_email = EmailField('Contact Email Address',
                               [UsedIfChecked('enable_tracking'), validators.Required(), validators.Email()])

    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        self.language.choices = sorted(get_all_locales().items(), key=itemgetter(1))
