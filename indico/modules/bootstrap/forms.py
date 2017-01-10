# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from wtforms import StringField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

from indico.modules.auth.forms import LocalRegistrationForm
from indico.util.i18n import _
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget


class BootstrapForm(LocalRegistrationForm):
    first_name = StringField('First Name', [DataRequired()])
    last_name = StringField('Last Name', [DataRequired()])
    email = EmailField(_('Email address'), [DataRequired()])
    affiliation = StringField('Affiliation', [DataRequired()])
    enable_tracking = BooleanField('Join the community', widget=SwitchWidget())
    contact_name = StringField('Contact Name', [UsedIfChecked('enable_tracking'), DataRequired()])
    contact_email = EmailField('Contact Email Address',  [UsedIfChecked('enable_tracking'), DataRequired(), Email()])
