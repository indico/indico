# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from flask_multipass.providers.sqlalchemy import SQLAlchemyAuthProviderBase, SQLAlchemyIdentityProviderBase

from indico.modules.auth import Identity, logger
from indico.modules.auth.forms import LocalLoginForm
from indico.modules.users import User
from indico.util.passwords import validate_secure_password


class IndicoAuthProvider(SQLAlchemyAuthProviderBase):
    login_form = LocalLoginForm
    identity_model = Identity
    provider_column = Identity.provider
    identifier_column = Identity.identifier
    multi_instance = False

    def check_password(self, identity, password):
        # No, the passwords are not stored in plaintext. Magic is happening here!
        if identity.password != password:
            return False
        if error := validate_secure_password('login', password, username=identity.identifier, fast=True):
            logger.warning('Account %s logged in with an insecure password: %s', identity.identifier, error)
            session['insecure_password_error'] = error
        return True


class IndicoIdentityProvider(SQLAlchemyIdentityProviderBase):
    user_model = User
    identity_user_relationship = 'user'
    multi_instance = False
