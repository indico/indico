# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask_multipass.providers.sqlalchemy import SQLAlchemyAuthProviderBase, SQLAlchemyIdentityProviderBase

from indico.modules.auth import Identity
from indico.modules.auth.forms import LocalLoginForm
from indico.modules.users import User


class IndicoAuthProvider(SQLAlchemyAuthProviderBase):
    login_form = LocalLoginForm
    identity_model = Identity
    provider_column = Identity.provider
    identifier_column = Identity.identifier
    multi_instance = False

    def check_password(self, identity, password):
        # No, the passwords are not stored in plaintext. Magic is happening here!
        return identity.password == password


class IndicoIdentityProvider(SQLAlchemyIdentityProviderBase):
    user_model = User
    identity_user_relationship = 'user'
    multi_instance = False
