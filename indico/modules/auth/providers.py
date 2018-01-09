# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
