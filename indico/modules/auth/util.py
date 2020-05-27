# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import redirect, request, session
from werkzeug.datastructures import MultiDict

from indico.core.config import config
from indico.modules.auth import Identity
from indico.modules.users.operations import create_user
from indico.util.signing import secure_serializer
from indico.util.string import to_unicode
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


def impersonate_user(user):
    """Impersonate another user as an admin"""
    from indico.modules.auth import login_user, logger

    current_user = session.user
    # We don't overwrite a previous entry - the original (admin) user should be kept there
    # XXX: Don't change this to setdefault - building `session_data` pops stuff from the session
    if 'login_as_orig_user' not in session:
        session['login_as_orig_user'] = {
            'session_data': {k: session.pop(k) for k in session.keys() if k[0] != '_' or k in ('_timezone', '_lang')},
            'user_id': session.user.id,
            'user_name': session.user.get_full_name(last_name_first=False, last_name_upper=False)
        }
    login_user(user, admin_impersonation=True)
    logger.info('Admin %r is impersonating user %r', current_user, user)


def undo_impersonate_user():
    """Undo an admin impersonation login and revert to the old user"""
    from indico.modules.auth import logger
    from indico.modules.users import User

    try:
        entry = session.pop('login_as_orig_user')
    except KeyError:
        # The user probably already switched back from another tab
        return
    user = User.get_or_404(entry['user_id'])
    logger.info('Admin %r stopped impersonating user %r', user, session.user)
    session.user = user
    session.update(entry['session_data'])


def redirect_to_login(next_url=None, reason=None):
    """Redirects to the login page.

    :param next_url: URL to be redirected upon successful login. If not
                     specified, it will be set to ``request.relative_url``.
    :param reason: Why the user is redirected to a login page.
    """
    if not next_url:
        next_url = request.relative_url
    if reason:
        session['login_reason'] = to_unicode(reason)
    return redirect(url_for_login(next_url))


def url_for_login(next_url=None):
    if next_url == '/':
        next_url = None
    return url_for('auth.login', next=next_url, _external=True)


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
    if config.LOCAL_IDENTITIES:
        token = secure_serializer.dumps(email, salt='register-email-prevalidated') if email else None
        return url_for('auth.register', token=token, next=next_url, _external=True)

    external_url = config.EXTERNAL_REGISTRATION_URL
    return external_url or url_for_login()
