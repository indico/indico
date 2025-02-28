# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from fnmatch import fnmatch

from flask import session
from wtforms import HiddenField
from wtforms.fields import EmailField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Email, Optional, ValidationError

from indico.core import signals
from indico.core.config import config
from indico.modules.auth import Identity
from indico.modules.core.captcha import WTFCaptchaField
from indico.modules.users import User, user_management_settings
from indico.util.i18n import _
from indico.util.signals import values_from_signal
from indico.util.string import validate_email
from indico.web.forms.base import IndicoForm
from indico.web.forms.validators import ConfirmPassword, SecurePassword


def _tolower(s):
    return s.lower() if s else s


def _check_existing_email(form, field):
    if User.query.filter(~User.is_deleted, ~User.is_pending, User.all_emails == field.data).has_rows():
        raise ValidationError(_('This email address is already in use.'))


def _check_existing_username(form, field):
    if Identity.query.filter_by(provider='indico', identifier=field.data).has_rows():
        raise ValidationError(_('This username is already in use.'))


def _check_not_blacklisted(form, field):
    blacklist = user_management_settings.get('email_blacklist')
    email_address = field.data
    error_msg = _('This email address is blacklisted.')

    for pattern in blacklist:
        pattern = pattern.strip()
        if fnmatch(email_address, pattern):
            raise ValidationError(error_msg)


def _check_not_email_address(form, field):
    if validate_email(field.data, check_dns=False):
        raise ValidationError(_('Your username cannot be an email address.'))


def _check_signup(form, field):
    if errors := values_from_signal(signals.users.check_signup_email.send(field.data), as_list=True):
        raise ValidationError(errors[0])


class LocalLoginForm(IndicoForm):
    identifier = StringField(_('Username or email'), [DataRequired()], filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not config.LOCAL_USERNAMES:
            self.identifier.label.text = _('Email')


class AddLocalIdentityForm(IndicoForm):
    username = StringField(_('Username'), [DataRequired(), _check_existing_username, _check_not_email_address],
                           filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired(), SecurePassword('set-user-password',
                                                                            username_field='username',
                                                                            emails=lambda form: form.user_emails)],
                             render_kw={'autocomplete': 'new-password'})
    confirm_password = PasswordField(_('Confirm password'), [DataRequired(), ConfirmPassword('password')],
                                     render_kw={'autocomplete': 'new-password'})

    def __init__(self, *args, user_emails, **kwargs):
        self.user_emails = user_emails
        super().__init__(*args, **kwargs)
        if not config.LOCAL_USERNAMES:
            del self.username


class EditLocalIdentityForm(IndicoForm):
    username = StringField(_('Username'), [DataRequired()], filters=[_tolower])
    password = PasswordField(_('Current password'), [DataRequired()],
                             render_kw={'autocomplete': 'current-password'})
    new_password = PasswordField(_('New password'), [Optional(), SecurePassword('set-user-password',
                                                                                username_field='username',
                                                                                emails=lambda form: form.user_emails)],
                                 render_kw={'autocomplete': 'new-password'})
    confirm_new_password = PasswordField(_('Confirm password'), [ConfirmPassword('new_password')],
                                         render_kw={'autocomplete': 'new-password'})

    def __init__(self, *args, identity=None, **kwargs):
        self.identity = identity
        self.user_emails = identity.user.all_emails
        super().__init__(*args, **kwargs)
        if not config.LOCAL_USERNAMES:
            del self.username
        if session.user.is_admin and session.user != self.identity.user:
            del self.password

    def validate_password(self, field):
        if field.data != self.identity.password:
            raise ValidationError(_('Wrong current password'))

    def validate_username(self, field):
        if validate_email(field.data, check_dns=False) and field.data != self.identity.identifier:
            raise ValidationError(_('Your username cannot be an email address.'))
        query = Identity.query.filter(Identity.provider == 'indico',
                                      Identity.identifier == field.data,
                                      Identity.identifier != self.identity.identifier)
        if query.has_rows():
            raise ValidationError(_('This username is already in use.'))


class SelectEmailForm(IndicoForm):
    email = SelectField(_('Email address'), [DataRequired()],
                        description=_('Choose the email address you want to verify.'))


class RegistrationEmailForm(IndicoForm):
    email = EmailField(_('Email address'),
                       [DataRequired(), Email(), _check_not_blacklisted, _check_existing_email, _check_signup],
                       filters=[_tolower])
    captcha = WTFCaptchaField()
    is_email_verification = HiddenField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not config.SIGNUP_CAPTCHA:
            del self.captcha


# only used on bootstrap+admin pages
class LocalRegistrationForm(IndicoForm):
    first_name = StringField(_('First name'), [DataRequired()])
    last_name = StringField(_('Family name'), [DataRequired()])
    affiliation = StringField(_('Affiliation'))
    email = EmailField(_('Email address'), [Email(), _check_existing_email])
    username = StringField(_('Username'), [DataRequired(), _check_existing_username], filters=[_tolower])
    password = PasswordField(_('Password'), [DataRequired(), SecurePassword('set-user-password',
                                                                            username_field='username',
                                                                            emails=lambda form: {form.email.data})],
                             render_kw={'autocomplete': 'new-password'})
    confirm_password = PasswordField(_('Confirm password'), [DataRequired(), ConfirmPassword('password')],
                                     render_kw={'autocomplete': 'new-password'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not config.LOCAL_USERNAMES:
            del self.username

    @property
    def data(self):
        data = super().data
        data.pop('confirm_password', None)
        return data

    def validate_username(self, field):
        if validate_email(field.data, check_dns=False):
            raise ValidationError(_('Your username cannot be an email address.'))


class ResetPasswordEmailForm(IndicoForm):
    email = EmailField(_('Email address'), [DataRequired(), Email()], filters=[_tolower])

    def validate_email(self, field):
        user = self.user
        if user is None:
            raise ValidationError(_('There is no profile with this email address.'))

    @property
    def user(self):
        if not self.is_submitted() or not self.email.data:
            return None
        return (User.query
                .filter(~User.is_deleted, ~User.is_blocked, ~User.is_pending, User.all_emails == self.email.data)
                .first())


class ResetPasswordForm(IndicoForm):
    username = StringField(_('Username'))
    password = PasswordField(_('New password'), [DataRequired(), SecurePassword('set-user-password',
                                                                                username_field='username',
                                                                                emails=lambda form: form.user_emails)],
                             render_kw={'autocomplete': 'new-password'})
    confirm_password = PasswordField(_('Confirm password'), [DataRequired(), ConfirmPassword('password')],
                                     render_kw={'autocomplete': 'new-password'})

    def __init__(self, *args, user_emails, **kwargs):
        self.user_emails = user_emails
        super().__init__(*args, **kwargs)
        if not config.LOCAL_USERNAMES:
            del self.username
