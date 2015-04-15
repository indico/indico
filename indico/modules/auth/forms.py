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

from wtforms.fields import StringField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Length

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoPasswordField


class SelectEmailForm(IndicoForm):
    email = SelectField(_('Email address'), [DataRequired()],
                        description=_('Choose the email address you want to verify.'))


class RegistrationEmailForm(IndicoForm):
    email = EmailField(_('Email address'), [DataRequired()], filters=[lambda x: x.lower() if x else x])


class RegistrationForm(IndicoForm):
    first_name = StringField(_('First name'), [DataRequired()])
    last_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'), [DataRequired()])


class MultiAuthRegistrationForm(RegistrationForm):
    email = SelectField(_('Email address'), [DataRequired()])
    phone = StringField(_('Phone number'))


class LocalRegistrationForm(RegistrationForm):
    email = EmailField(_('Email address'), [DataRequired()])
    username = StringField(_('Username'), [DataRequired()])
    password = IndicoPasswordField(_('Password'), [DataRequired(), Length(min=5)], toggle=True)
    confirm_password = IndicoPasswordField(_('Confirm password'),
                                           [DataRequired(), EqualTo('password',
                                                                    message=_('The passwords do not match.'))])
