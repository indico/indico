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

from wtforms.fields import StringField, SelectField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from indico.modules.auth import Identity
from indico.modules.users.models.emails import UserEmail
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm


def _tolower(s):
    return s.lower() if s else s


def _check_existing_email(form, field):
    if UserEmail.find(email=field.data, is_user_deleted=False).count():
        raise ValidationError(_('This email address is already in use.'))


class SelectEmailForm(IndicoForm):
    email = SelectField(_('Email address'), [DataRequired()],
                        description=_('Choose the email address you want to verify.'))


class RegistrationEmailForm(IndicoForm):
    email = EmailField(_('Email address'), [DataRequired(), _check_existing_email], filters=[_tolower])


class RegistrationForm(IndicoForm):
    first_name = StringField(_('First name'), [DataRequired()])
    last_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'), [DataRequired()])


class MultiAuthRegistrationForm(RegistrationForm):
    email = SelectField(_('Email address'), [DataRequired(), _check_existing_email])
    phone = StringField(_('Phone number'))


class LocalRegistrationForm(RegistrationForm):
    email = EmailField(_('Email address'))
    username = StringField(_('Username'), [DataRequired()], filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired(), Length(min=5)])
    confirm_password = PasswordField(_('Confirm password'),
                                     [DataRequired(), EqualTo('password', message=_('The passwords do not match.'))])

    def validate_username(self, field):
        if Identity.find(provider='indico', identifier=field.data).count():
            raise ValidationError(_('This username is already in use.'))
