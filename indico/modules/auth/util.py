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

from flask import session, redirect, request, flash
from werkzeug.datastructures import MultiDict

from indico.core.config import Config
from indico.core.notifications import make_email, send_email
from indico.modules.users.models.users import User
from indico.util.i18n import _
from indico.util.signing import secure_serializer
from indico.web.flask.util import url_for
from indico.web.flask.templating import get_template_module


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
        'email_verified': bool(identity_info.data.get('email') and trusted_email)
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


def send_confirmation(email, salt, endpoint, template, template_args=None, url_args=None, data=None,
                      redirect_endpoint=None):
    template_args = template_args or {}
    url_args = url_args or {}
    token = secure_serializer.dumps(data or email, salt=salt)
    url = url_for(endpoint, token=token, _external=True, _secure=True, **url_args)
    template_module = get_template_module(template, email=email, url=url, **template_args)
    send_email(make_email(email, template=template_module))

    flash(_('We have sent you a verification email. Please check your mailbox within the next hour and open '
            'the link in that email.'))

    if redirect_endpoint:
        return redirect(url_for(redirect_endpoint, **url_args))
    else:
        return redirect(url_for(endpoint, **url_args))


def send_verification_email(email, template, salt, endpoint, data=None, url_args=None):
    token = secure_serializer.dumps(data or email, salt=salt)
    url = url_for(endpoint, email=email, token=token, _external=True, _secure=True)
    template = get_template_module(template, email=email, url=url)
    send_email(make_email(email, template=template))


def notify_of_registration_request_approval(user, endpoint):
    template = get_template_module('auth/emails/registration_request_approved.txt', recipient=user)
    send_email(make_email(user.email, template=template))


def send_notification_to_admins(template):
    for admin in User.find(is_admin=True):
        send_email(make_email(admin.email, template=template))
