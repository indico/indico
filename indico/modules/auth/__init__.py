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

from flask import session, redirect, request
from flask_multipass import Multipass, MultipassException
from werkzeug.exceptions import NotFound

# from indico.core.auth import multipass
from indico.core.db import db
from indico.core.logger import Logger
from indico.modules.auth.models.identities import Identity
from indico.modules.auth.util import save_identity_info
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.common.timezoneUtils import SessionTZ
# from MaKaC.webinterface.rh.base import RHSimple


logger = Logger.get('auth')


class IndicoMultipass(Multipass):
    # @RHSimple.wrap_function
    # def render_template(self, template_key, **kwargs):
    #     return super(IndicoMultipass, self).render_template(template_key, **kwargs)

    def process_submit(self):
        if request.method == 'POST' and request.form['provider']:
            return self.process_login(provider=request.form['provider'])
        return self.process_login()

    def process_login(self, provider=None):
        if self.login_check_callback and self.login_check_callback():
            self._set_next_url()
            return self.redirect_success()

        if provider is None:
            return self._login_page()

        try:
            provider = self.auth_providers[provider]
        except KeyError:
            raise NotFound('Provider does not exist')

        if provider.is_external:
            return self._login_external(provider)
        else:
            return self._login_page(provider)

    def _login_page(self, provider=None):
        """Renders the login page"""
        providers = self.auth_providers
        next_url = request.args.get('next')
        auth_failed = session.pop('_multipass_auth_failed', False)
        login_endpoint = 'auth.login'
        if provider:
            form = provider.login_form()
            if not form.is_submitted():
                self._set_next_url()
            if form.validate_on_submit():
                try:
                    response = provider.process_local_login(form.data)
                except MultipassException as e:
                    self.handle_auth_error(e)
                else:
                    return response
        else:
            form = self.default_auth_provider.login_form()
        if not auth_failed and len(providers) == 1:
            provider = providers.values()[0]
            return redirect(url_for(login_endpoint, provider=provider.name, next=next_url))
        else:
            if request.form.get('provider'):
                default_provider = self.auth_providers[request.form.get('provider')]
            else:
                default_provider = self.default_auth_provider
            return self.render_template('LOGIN_PAGE', providers=self.auth_providers.values(), next=next_url,
                                        auth_failed=auth_failed, login_endpoint=login_endpoint,
                                        default_provider=default_provider, form=form)

    def login_form(self, provider):
        """Generates the HTML of a provider's login form

        Used to update the login form with AJAX when the
        authentication provider is changed by the user
        """
        try:
            provider = self.auth_providers[provider]
        except KeyError:
            raise NotFound('Provider does not exist')
        form = provider.login_form()
        return self.render_template('LOGIN_FORM', form=form, provider=provider)

multipass = IndicoMultipass()


@multipass.identity_handler
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
    elif identity.user.is_deleted:
        raise MultipassException(_('Your Indico account has been deleted.'))
    else:
        user = identity.user
        logger.info('Found existing identity {} for user {}'.format(identity, user))
    # Update the identity with the latest information
    if identity.multipass_data != identity_info.multipass_data:
        logger.info('Updated multipass data'.format(identity, user))
        identity.multipass_data = identity_info.multipass_data
    if identity.data != identity_info.data:
        logger.info('Updated data'.format(identity, user))
        identity.data = identity_info.data
    if user.is_blocked:
        raise MultipassException(_('Your Indico account has been blocked.'))
    login_user(user, identity)


@multipass.login_check
def is_logged_in():
    return session.user is not None


def login_user(user, identity=None):
    """Sets the session user and performs on-login logic

    When specifying `identity`, the provider/identitifer information
    is saved in the session so the identity management page can prevent
    the user from removing the identity he used to login.

    :param user: The :class:`~indico.modules.users.User` to log in to.
    :param identity: The :class:`Identity` instance used to log in.
    """
    avatar = user.as_avatar
    session.timezone = SessionTZ(avatar).getSessionTZ()
    session.user = user
    session.lang = user.settings.get('lang')
    if identity:
        identity.register_login(request.remote_addr)
        session['login_identity'] = identity.id
    else:
        session.pop('login_identity', None)
