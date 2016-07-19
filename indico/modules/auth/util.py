# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session, redirect, request
from werkzeug.datastructures import MultiDict

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.modules.auth import Identity
from indico.modules.users import User
from indico.modules.users.operations import create_user
from indico.util.signing import secure_serializer
from indico.web.flask.util import url_for


def save_identity_info(identity_info, user):
    """Saves information from IdentityInfo in the session"""
    trusted_email = identity_info.provider.settings.get('trusted_email', False)
    session['login_identity_info'] = {
        'provider': identity_info.provider.name,
        'provider_title': identity_info.provider.title,
        'identifier': identity_info.identifier,
        'multipass_data': identity_info.multipass_data,
        'data': dict(identity_info.data.lists()),
        'indico_user_id': user.id if user else None,
        'email_verified': bool(identity_info.data.get('email') and trusted_email),
        'moderated': identity_info.provider.settings.get('moderated', False)
    }


def load_identity_info():
    """Retrieves identity information from the session"""
    try:
        info = session['login_identity_info'].copy()
    except KeyError:
        return None
    # Restoring a multidict is quite ugly...
    data = info.pop('data')
    info['data'] = MultiDict()
    info['data'].update(data)
    return info


def register_user(email, extra_emails, user_data, identity_data, settings, from_moderation=False):
    """
    Create a user based on the registration data provided during te
    user registration process (via `RHRegister` and `RegistrationHandler`).

    This method is not meant to be used for generic user creation, the
    only reason why this is here is that approving a registration request
    is handled by the `users` module.
    """
    identity = Identity(**identity_data)
    user = create_user(email, user_data, identity=identity, settings=settings, other_emails=extra_emails,
                       from_moderation=from_moderation)
    return user, identity


def redirect_to_login(next_url=None, reason=None):
    """Redirects to the login page.

    :param next_url: URL to be redirected upon successful login. If not
                     specified, it will be set to ``request.relative_url``.
    :param reason: Why the user is redirected to a login page.
    """
    if not next_url:
        next_url = request.relative_url
    if reason:
        session['login_reason'] = unicode(reason)
    return redirect(url_for_login(next_url))


def url_for_login(next_url=None):
    return url_for('auth.login', next=next_url, _external=True, _secure=True)


def url_for_logout(next_url=None):
    return url_for('auth.logout', next=next_url)


def url_for_register(next_url=None, email=None):
    """Returns the URL to register

    :param next_url: The URL to redirect to afterwards.
    :param email: A pre-validated email address to use when creating
                  a new local account.  Use this argument ONLY when
                  sending the link in an email or if the email address
                  has already been validated using some other way.

    """
    if Config.getInstance().getLocalIdentities():
        token = secure_serializer.dumps(email, salt='register-email-prevalidated') if email else None
        return url_for('auth.register', token=token, next=next_url, _external=True, _secure=True)

    external_url = Config.getInstance().getExternalRegistrationURL()
    return external_url or url_for_login()
