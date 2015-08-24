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

from wtforms import validators, TextField, BooleanField
from wtforms.fields.html5 import EmailField

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import UsedIfChecked
from indico.web.forms.widgets import SwitchWidget


class CephalopodForm(IndicoForm):
    joined = BooleanField('Join the community', widget=SwitchWidget())
    contact_name = TextField('Contact Name', [UsedIfChecked('enable_tracking'), validators.Required()],
                             description=_('Name of the person responsible for your Indico server.'))
    contact_email = EmailField('Contact Email',
                               [UsedIfChecked('enable_tracking'), validators.Required(), validators.Email()],
                               description=_('Email address of the person responsible for your Indico server.'))
