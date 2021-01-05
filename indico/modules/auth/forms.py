# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import PasswordField, SelectField, StringField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from indico.modules.auth import Identity
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, SyncedInputsMixin
from indico.web.forms.validators import ConfirmPassword, used_if_not_synced
from indico.web.forms.widgets import SyncedInputWidget


def _tolower(s):
    return s.lower() if s else s


def _check_existing_email(form, field):
    if User.query.filter(~User.is_deleted, ~User.is_pending, User.all_emails == field.data).has_rows():
        raise ValidationError(_('This email address is already in use.'))


def _check_existing_username(form, field):
    if Identity.query.filter_by(provider='indico', identifier=field.data).has_rows():
        raise ValidationError(_('This username is already in use.'))


class LocalLoginForm(IndicoForm):
    identifier = StringField(_('Username'), [DataRequired()], filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired()])


class AddLocalIdentityForm(IndicoForm):
    username = StringField(_('Username'), [DataRequired(), _check_existing_username], filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired(), Length(min=5)])
    confirm_password = PasswordField(_('Confirm password'), [DataRequired(), ConfirmPassword('password')])


class EditLocalIdentityForm(IndicoForm):
    username = StringField(_('Username'), [DataRequired()], filters=[_tolower])
    password = PasswordField(_('Current password'), [DataRequired()])
    new_password = PasswordField(_('New password'), [Optional(), Length(min=5)])
    confirm_new_password = PasswordField(_('Confirm password'), [ConfirmPassword('new_password')])

    def __init__(self, *args, **kwargs):
        self.identity = kwargs.pop('identity', None)
        super(EditLocalIdentityForm, self).__init__(*args, **kwargs)

    def validate_password(self, field):
        if field.data != self.identity.password:
            raise ValidationError(_("Wrong current password"))

    def validate_username(self, field):
        query = Identity.query.filter(Identity.provider == 'indico',
                                      Identity.identifier == field.data,
                                      Identity.identifier != self.identity.identifier)
        if query.has_rows():
            raise ValidationError(_('This username is already in use.'))


class SelectEmailForm(IndicoForm):
    email = SelectField(_('Email address'), [DataRequired()],
                        description=_('Choose the email address you want to verify.'))


class RegistrationEmailForm(IndicoForm):
    email = EmailField(_('Email address'), [DataRequired(), Email(), _check_existing_email], filters=[_tolower])


class RegistrationForm(IndicoForm):
    first_name = StringField(_('First name'), [DataRequired()])
    last_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'))


class MultipassRegistrationForm(SyncedInputsMixin, IndicoForm):
    first_name = StringField(_('First Name'), [used_if_not_synced, DataRequired()], widget=SyncedInputWidget())
    last_name = StringField(_('Family name'), [used_if_not_synced, DataRequired()], widget=SyncedInputWidget())
    affiliation = StringField(_('Affiliation'), widget=SyncedInputWidget())
    email = SelectField(_('Email address'), [DataRequired(), _check_existing_email])
    address = StringField(_('Address'), widget=SyncedInputWidget(textarea=True))
    phone = StringField(_('Phone number'), widget=SyncedInputWidget())
    comment = TextAreaField(_('Comment'), description=_("You can provide additional information or a comment for the "
                                                        "administrators who will review your registration."))


class LocalRegistrationForm(RegistrationForm):
    email = EmailField(_('Email address'), [Email(), _check_existing_email])
    username = StringField(_('Username'), [DataRequired(), _check_existing_username], filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired(), Length(min=5)])
    confirm_password = PasswordField(_('Confirm password'), [DataRequired(), ConfirmPassword('password')])
    comment = TextAreaField(_('Comment'), description=_("You can provide additional information or a comment for the "
                                                        "administrators who will review your registration."))

    @property
    def data(self):
        data = super(LocalRegistrationForm, self).data
        data.pop('confirm_password', None)
        return data


class ResetPasswordEmailForm(IndicoForm):
    email = EmailField(_('Email address'), [DataRequired(), Email()], filters=[_tolower])

    def validate_email(self, field):
        user = self.user
        if user is None:
            raise ValidationError(_('There is no profile with this email address.'))
        elif not user.local_identities:
            # XXX: Should we allow creating a new identity instead? Would be user-friendly for sure!
            raise ValidationError(_('This profile has no local account.'))

    @property
    def user(self):
        if not self.is_submitted() or not self.email.data:
            return None
        return (User.query
                .filter(~User.is_deleted, ~User.is_blocked, ~User.is_pending, User.all_emails == self.email.data)
                .first())


class ResetPasswordForm(IndicoForm):
    username = StringField(_('Username'))
    password = PasswordField(_('New password'), [DataRequired(), Length(min=5)])
    confirm_password = PasswordField(_('Confirm password'), [DataRequired(), ConfirmPassword('password')])
