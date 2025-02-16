# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, session
from flask_multipass import AuthInfo, AuthProvider, InvalidCredentials, NoSuchUser
from flask_multipass.providers.sqlalchemy import SQLAlchemyIdentityProviderBase

from indico.core.db import db
from indico.modules.auth import Identity, logger
from indico.modules.auth.forms import LocalLoginForm
from indico.modules.users import User
from indico.modules.users.models.emails import UserEmail
from indico.util.i18n import _
from indico.util.passwords import validate_secure_password


class IndicoAuthProvider(AuthProvider):
    login_form = LocalLoginForm
    multi_instance = False

    def check_password(self, identity, password):
        # No, the passwords are not stored in plaintext. Magic is happening here!
        if identity.password != password:
            return False
        if error := validate_secure_password('login', password, username=identity.identifier, fast=True):
            logger.warning('Account %s logged in with an insecure password: %s', identity.identifier, error)
            session['insecure_password_error'] = error
        return True

    def process_local_login(self, data):
        # Query identities either by (user-settable) username or by email address.
        # In some very rare edge cases we can get more than one, e.g. when a user has an old identity
        # with a username that happens to be the email address of another user (this is no longer possible,
        # but existing accounts could have it).
        identities = (
            Identity.query
            .join(User)
            .join(UserEmail)
            .filter(Identity.provider == self.name,
                    db.or_(Identity.identifier == data['identifier'],
                           UserEmail.email == data['identifier']),
                    ~User.is_pending,
                    ~UserEmail.is_user_deleted)
            .order_by(Identity.id)
            .all()
        )
        # If we have no matching identities we fail with invalid username
        # XXX This is intentional, having an account on an Indico instance is generally not considered
        # secret information, and we want to give users the benefit of more verbose error messages.
        if not identities:
            raise NoSuchUser(provider=self)
        # From all the matching identities (usually just one), get one where the password matches, or
        # fail with invalid-password if there is none.
        if not (identity := next((ide for ide in identities if self.check_password(ide, data['password'])), None)):
            raise InvalidCredentials(provider=self)
        if data['identifier'] != identity.identifier and data['identifier'] in identity.user.secondary_emails:
            flash(_('You are logging in with a secondary email address. Please note that account related '
                    'notifications will always be sent to your primary email address. Go to "My profile" to '
                    'manage your emails.'), 'warning')
        auth_info = AuthInfo(self, identity=identity)
        return self.multipass.handle_auth_success(auth_info)


class IndicoIdentityProvider(SQLAlchemyIdentityProviderBase):
    user_model = User
    identity_user_relationship = 'user'
    multi_instance = False
