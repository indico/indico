# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from flask_multipass import MultipassException

from indico.core import signals
from indico.core.auth import multipass
from indico.core.db import db
from indico.core.logger import Logger
from indico.modules.auth.models.identities import Identity
from indico.modules.auth.models.registration_requests import RegistrationRequest
from indico.modules.auth.util import save_identity_info
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem
from indico.legacy.common.timezoneUtils import SessionTZ


logger = Logger.get('auth')


@multipass.identity_handler
def process_identity(identity_info):
    logger.info('Received identity info: %s', identity_info)
    identity = Identity.query.filter_by(provider=identity_info.provider.name,
                                        identifier=identity_info.identifier).first()
    if identity is None:
        logger.info('Identity does not exist in the database yet')
        user = None
        emails = {email.lower() for email in identity_info.data.getlist('email') if email}
        if emails:
            identity_info.data.setlist('email', emails)
            users = User.query.filter(~User.is_deleted, User.all_emails.contains(db.func.any(list(emails)))).all()
            if len(users) == 1:
                user = users[0]
            elif len(users) > 1:
                # TODO: handle this case somehow.. let the user select which user to log in to?
                raise NotImplementedError('Multiple emails matching multiple users')
        save_identity_info(identity_info, user if user and not user.is_pending else None)
        if not user or user.is_pending:
            if user and user.is_pending:
                logger.info('Found pending user with matching email: %s', user)
            else:
                logger.info('Email search did not find an existing user')
            return redirect(url_for('auth.register', provider=identity_info.provider.name))
        else:
            logger.info('Found user with matching email: %s', user)
            return redirect(url_for('auth.link_account', provider=identity_info.provider.name))
    elif identity.user.is_deleted:
        raise MultipassException(_('Your Indico profile has been deleted.'))
    else:
        user = identity.user
        if user.is_pending:
            # This should never happen!
            raise ValueError('Got identity for pending user')
        logger.info('Found existing identity %s for user %s', identity, user)
    # Update the identity with the latest information
    if identity.multipass_data != identity_info.multipass_data:
        logger.info('Updated multipass data of identity %s for user %s', identity, user)
        identity.multipass_data = identity_info.multipass_data
    if identity.data != identity_info.data:
        logger.info('Updated data of identity %s for user %s', identity, user)
        identity.data = identity_info.data
    if user.is_blocked:
        raise MultipassException(_('Your Indico profile has been blocked.'))
    login_user(user, identity)


def login_user(user, identity=None, admin_impersonation=False):
    """Set the session user and performs on-login logic

    When specifying `identity`, the provider/identitifer information
    is saved in the session so the identity management page can prevent
    the user from removing the identity he used to login.

    :param user: The :class:`~indico.modules.users.User` to log in to.
    :param identity: The :class:`Identity` instance used to log in.
    :param admin_impersonation: Whether the login is an admin
                                impersonating the user and thus should not
                                be considered a login by the user.
    """
    avatar = user.as_avatar
    session.timezone = SessionTZ(avatar).getSessionTZ()
    session.user = user
    session.lang = user.settings.get('lang')
    if not admin_impersonation:
        if identity:
            identity.register_login(request.remote_addr)
            session['login_identity'] = identity.id
        else:
            session.pop('login_identity', None)
        user.synchronize_data()


@signals.menu.items.connect_via('user-profile-sidemenu')
def _extend_profile_sidemenu(sender, user, **kwargs):
    yield SideMenuItem('accounts', _('Accounts'), url_for('auth.accounts'), 50, disabled=user.is_system)


@signals.users.registered.connect
def _delete_requests(user, **kwargs):
    for req in RegistrationRequest.find(RegistrationRequest.email.in_(user.all_emails)):
        logger.info('Deleting registration request %r due to registration of %r', req, user)
        db.session.delete(req)
    db.session.flush()
