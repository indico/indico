# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import session, redirect
from flask_multiauth import MultiAuth, MultiAuthException

from indico.core.db import db
from indico.core.logger import Logger
from indico.modules.auth.models.identities import Identity
from indico.modules.auth.util import save_identity_info
from indico.modules.auth.views import WPAuth
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.common.timezoneUtils import SessionTZ
from MaKaC.webinterface.rh.base import RHSimple


logger = Logger.get('auth')


class IndicoMultiAuth(MultiAuth):
    @RHSimple.wrap_function
    def render_template(self, template_key, **kwargs):
        rv = super(IndicoMultiAuth, self).render_template(template_key, **kwargs)
        return WPAuth.render_string(rv)


multiauth = IndicoMultiAuth()


@multiauth.identity_handler
@RHSimple.wrap_function
def process_identity(identity_info):
    logger.info('Received identity info: {}'.format(identity_info))
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
            elif len(users) > 2:
                # TODO: handle this case somehow.. let the user select which user to log in to?
                raise NotImplementedError('Multiple emails matching multiple users')
        save_identity_info(identity_info, user)
        if user is None:
            logger.info('Email search did not find an existing user')
            return redirect(url_for('auth.register', provider=identity_info.provider.name))
        else:
            logger.info('Found user with matching email: {}'.format(user))
            return redirect(url_for('auth.associate_identity'))
    else:
        user = identity.user
        logger.info('Found existing identity {} for user {}'.format(identity, user))
    # Update the identity with the latest information
    if identity.multiauth_data != identity_info.multiauth_data:
        logger.info('Updated multiauth data'.format(identity, user))
        identity.multiauth_data = identity_info.multiauth_data
    if identity.data != identity_info.data:
        logger.info('Updated data'.format(identity, user))
        identity.data = identity_info.data
    if user.is_blocked:
        raise MultiAuthException(_('Your Indico account has been blocked.'))
    login_user(user)


@multiauth.login_check
def is_logged_in():
    return session.user is not None


def login_user(user, logged_in_with=None):
    """Sets the session user and performs on-login logic

    When specifying `logged_in_with`, this information is saved in the
    session so the identity management page can prevent the user from
    removing the identity he used to login.

    :param user: The :class:`~indico.modules.users.User` to log in to.
    :param logged_in_with: A ``provider_name, identifier`` tuple
    """
    avatar = user.as_avatar
    session.timezone = SessionTZ(avatar).getSessionTZ()
    session.user = user
    session.lang = user.settings.get('lang')
    if logged_in_with:
        session['logged_in_with'] = logged_in_with
    else:
        session.pop('logged_in_with', None)
