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

from flask import session, redirect, request, flash, render_template, jsonify
from itsdangerous import BadData
from markupsafe import Markup
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core.auth import multipass
from indico.core.config import Config
from indico.core.db import db
from indico.core.notifications import make_email
from indico.modules.auth import logger, Identity, login_user
from indico.modules.auth.forms import (SelectEmailForm, MultipassRegistrationForm, LocalRegistrationForm,
                                       RegistrationEmailForm, ResetPasswordEmailForm, ResetPasswordForm,
                                       LocalLoginAddForm, LocalLoginEditForm)
from indico.modules.auth.util import load_identity_info
from indico.modules.auth.views import WPAuth
from indico.modules.users import User
from indico.modules.users.controllers import RHUserBase
from indico.modules.users.views import WPUser
from indico.util.i18n import _
from indico.util.signing import secure_serializer
from indico.web.flask.util import url_for
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults, IndicoForm

from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.rh.base import RH


def _get_provider(name, external):
    try:
        provider = multipass.auth_providers[name]
    except KeyError:
        raise NotFound('Provider does not exist')
    if provider.is_external != external:
        raise NotFound('Invalid provider')
    return provider


class RHLogin(RH):
    """The login page"""

    def _process(self):
        # User is already logged in
        if session.user is not None:
            multipass.set_next_url()
            return multipass.redirect_success()

        # If we have only one provider, and this provider is external, we go there immediately
        # However, after a failed login we need to show the page to avoid a redirect loop
        if not session.pop('_multipass_auth_failed', False) and 'provider' not in request.view_args:
            single_auth_provider = multipass.single_auth_provider
            if single_auth_provider and single_auth_provider.is_external:
                return redirect(url_for('.login', provider=single_auth_provider.name))

        # Save the 'next' url to go to after login
        multipass.set_next_url()

        # If there's a provider in the URL we start the external login process
        if 'provider' in request.view_args:
            provider = _get_provider(request.view_args['provider'], True)
            return provider.initiate_external_login()

        # If we have a POST request we submitted a login form for a local provider
        if request.method == 'POST':
            active_provider = provider = _get_provider(request.form['_provider'], False)
            form = provider.login_form()
            if form.validate_on_submit():
                response = multipass.handle_login_form(provider, form.data)
                if response:
                    return response
        # Otherwise we show the form for the default provider
        else:
            active_provider = multipass.default_local_auth_provider
            form = active_provider.login_form() if active_provider else None

        providers = multipass.auth_providers.values()
        return render_template('auth/login_page.html', form=form, providers=providers, active_provider=active_provider)


class RHLoginForm(RH):
    """Retrieves a login form (json)"""

    def _process(self):
        provider = _get_provider(request.view_args['provider'], False)
        form = provider.login_form()
        template_module = get_template_module('auth/_login_form.html')
        return jsonify(success=True, html=template_module.login_form(provider, form))


class RHLogout(RH):
    """Logs the user out"""

    def _process(self):
        return multipass.logout(request.args.get('next') or url_for('misc.index'), clear_session=True)


def _send_confirmation(email, salt, endpoint, template, template_args=None, url_args=None, data=None):
    template_args = template_args or {}
    url_args = url_args or {}
    token = secure_serializer.dumps(data or email, salt=salt)
    url = url_for(endpoint, token=token, _external=True, _secure=True, **url_args)
    template_module = get_template_module(template, email=email, url=url, **template_args)
    GenericMailer.send(make_email(email, template=template_module))
    flash(_('We have sent you a verification email. Please check your mailbox within the next hour and open '
            'the link in that email.'))
    return redirect(url_for(endpoint, **url_args))


class RHAssociateIdentity(RH):
    """Associates a new identity with an existing user.

    This RH is only used if the identity information contains an
    email address and an existing user was found.
    """

    def _checkParams(self):
        self.identity_info = load_identity_info()
        if not self.identity_info or self.identity_info['indico_user_id'] is None:
            # Just redirect to the front page or whereever we wanted to go.
            # Probably someone simply used his browser's back button.
            flash('There is no pending login.', 'warning')
            return multipass.redirect_success()
        self.user = User.get(self.identity_info['indico_user_id'])
        self.emails = sorted(self.user.all_emails & set(self.identity_info['data'].getlist('email')))
        self.verification_email_sent = self.identity_info.get('verification_email_sent', False)
        self.email_verified = self.identity_info['email_verified']
        self.must_choose_email = len(self.emails) != 1 and not self.email_verified

    def _process(self):
        if self.verification_email_sent and 'token' in request.args:
            email = secure_serializer.loads(request.args['token'], max_age=3600, salt='associate-identity-email')
            if email not in self.emails:
                raise BadData('Emails do not match')
            session['login_identity_info']['email_verified'] = True
            session.modified = True
            flash(_('You have successfully validated your email address and can now proceeed with the login.'),
                  'success')
            return redirect(url_for('.associate_identity', provider=self.identity_info['provider']))

        if self.must_choose_email:
            form = SelectEmailForm()
            form.email.choices = zip(self.emails, self.emails)
        else:
            form = IndicoForm()

        if form.validate_on_submit():
            if self.email_verified:
                return self._create_identity()
            elif not self.verification_email_sent:
                return self._send_confirmation(form.email.data if self.must_choose_email else self.emails[0])
            else:
                flash(_('The validation email has already been sent.'), 'warning')

        return WPAuth.render_template('associate_identity.html', identity_info=self.identity_info, user=self.user,
                                      email_sent=self.verification_email_sent, emails=' / '.join(self.emails),
                                      form=form, must_choose_email=self.must_choose_email)

    def _create_identity(self):
        identity = Identity(user=self.user, provider=self.identity_info['provider'],
                            identifier=self.identity_info['identifier'], data=self.identity_info['data'],
                            multipass_data=self.identity_info['multipass_data'])
        logger.info('Created new identity for {}: {}'.format(self.user, identity))
        del session['login_identity_info']
        db.session.flush()
        login_user(self.user, identity)
        return multipass.redirect_success()

    def _send_confirmation(self, email):
        session['login_identity_info']['verification_email_sent'] = True
        session['login_identity_info']['data']['email'] = email  # throw away other emails
        return _send_confirmation(email, 'associate-identity-email', '.associate_identity',
                                  'auth/emails/associate_identity_verify_email.txt', {'user': self.user},
                                  url_args={'provider': self.identity_info['provider']})


class RHRegister(RH):
    """Creates a new indico user.

    This handles two cases:
    - creation of a new account with a locally stored username and password
    - creation of a new account based on information from an identity provider
    """

    def _checkParams(self):
        self.identity_info = None
        self.provider_name = request.view_args['provider']
        if self.provider_name is not None:
            self.identity_info = info = load_identity_info()
            if not info:
                return redirect(url_for('.login', provider=self.provider_name))
            elif info['indico_user_id'] is not None or info['provider'] != self.provider_name:
                # If we have a matching user id, we shouldn't be on the registration page
                # If the provider doesn't match it would't be a big deal but the request doesn't make sense
                raise BadRequest
        elif not Config.getInstance().getLocalIdentities():
            raise Forbidden('Local identities are disabled')

    def _get_verified_email(self):
        """Checks if there is an email verification token."""
        if 'token' not in request.args:
            return None
        return secure_serializer.loads(request.args['token'], max_age=3600, salt='register-email')

    def _process(self):
        if session.user:
            return redirect(url_for('misc.index'))
        handler = MultipassRegistrationHandler(self) if self.identity_info else LocalRegistrationHandler(self)
        verified_email = self._get_verified_email()
        if verified_email is not None:
            handler.email_verified(verified_email)
            flash(_('You have successfully validated your email address and can now proceeed with the registration.'),
                  'success')

            # Check whether there is already an existing pending user with this e-mail
            pending = User.find_first(User.all_emails.contains(verified_email), is_pending=True)

            if pending:
                session['register_pending_user'] = pending.id
                flash(_("There is already some information in Indico that concerns you. "
                        "We are going to link it automatically."), 'info')

            return redirect(url_for('.register', provider=self.provider_name))

        form = handler.create_form()
        if form.validate_on_submit():
            if handler.must_verify_email:
                return self._send_confirmation(form.email.data)
            else:
                return self._create_user(form.data, handler)
        return WPAuth.render_template('register.html', form=form, local=(not self.identity_info),
                                      must_verify_email=handler.must_verify_email, widget_attrs=handler.widget_attrs,
                                      email_sent=session.pop('register_verification_email_sent', False))

    def _send_confirmation(self, email):
        session['register_verification_email_sent'] = True
        return _send_confirmation(email, 'register-email', '.register', 'auth/emails/register_verify_email.txt',
                                  url_args={'provider': self.provider_name})

    def _create_user(self, data, handler):
        existing_user_id = session.get('register_pending_user')
        if existing_user_id:
            # Get pending user and set her as non-pending
            user = User.get(existing_user_id)
            user.is_pending = False
        else:
            user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'],
                        address=data.get('address', ''), phone=data.get('phone', ''), affiliation=data['affiliation'])

        identity = handler.create_identity(data)
        user.identities.add(identity)
        user.secondary_emails = handler.extra_emails - {user.email}
        user.favorite_users.add(user)
        db.session.add(user)
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        timezone = session.timezone
        if timezone == 'LOCAL':
            timezone = minfo.getTimezone()
        user.settings.set('timezone', timezone)
        user.settings.set('lang', session.lang or minfo.getLang())
        db.session.flush()
        login_user(user, identity)
        msg = _('You have sucessfully registered your Indico account. '
                'Check <a href="{url}">your profile</a> for further account details and settings.')
        flash(Markup(msg).format(url=url_for('users.user_profile')), 'success')
        return handler.redirect_success()


class RHUserAccounts(RHUserBase):
    """Displays user accounts"""

    def _create_form(self):
        if self.user.local_identity:
            defaults = FormDefaults(username=self.user.local_identity.identifier)
            local_account_form = LocalLoginEditForm(identity=self.user.local_identity, obj=defaults)
        else:
            local_account_form = LocalLoginAddForm()
        return local_account_form

    def _handle_add_local_account(self, form):
        identity = Identity(provider='indico', identifier=form.data['username'], password=form.data['password'])
        self.user.identities.add(identity)
        flash(_("Local account added successfully"), 'success')

    def _handle_edit_local_account(self, form):
        self.user.local_identity.identifier = form.data['username']
        if form.data['new_password']:
            self.user.local_identity.password = form.data['new_password']
        flash(_("Your local account credentials have been updated successfully"), 'success')

    def _process(self):
        form = self._create_form()
        if form.validate_on_submit():
            if isinstance(form, LocalLoginAddForm):
                self._handle_add_local_account(form)
            elif isinstance(form, LocalLoginEditForm):
                self._handle_edit_local_account(form)
            return redirect(url_for('auth.accounts'))
        provider_titles = {name: provider.title for name, provider in multipass.auth_providers.iteritems()}
        return WPUser.render_template('accounts.html', form=form, user=self.user, provider_titles=provider_titles)


class RHUserAccountsRemove(RHUserBase):
    """Removes an account"""

    def _checkParams(self):
        RHUserBase._checkParams(self)
        self.identity = Identity.get_one(request.view_args['identity'])
        if self.identity.user != self.user:
            raise NotFound()

    def _process(self):
        if session['login_identity'] == self.identity.id:
            raise BadRequest("The identity used to log in can't be removed")
        if self.user.local_identity == self.identity:
            raise BadRequest("The main local identity can't be removed")
        self.user.identities.remove(self.identity)
        provider_title = multipass.identity_providers[self.identity.provider].title
        flash(_("{} ({}) successfully removed from your accounts"
              .format(provider_title, self.identity.identifier)), 'success')
        return redirect(url_for('.accounts'))


class RegistrationHandler(object):
    form = None

    def __init__(self, rh):
        pass

    def email_verified(self, email):
        raise NotImplementedError

    def get_form_defaults(self):
        raise NotImplementedError

    def create_form(self):
        defaults = self.get_form_defaults()
        if self.must_verify_email:
            # We don't bother with multiple emails here. The case that the provider sends more
            # than one email AND those emails are untrusted is so low it's simply not worth it.
            # The only drawback in that situation would be not showing the extra emails to the
            # user...
            return RegistrationEmailForm(obj=defaults)
        else:
            return self.form(obj=defaults)

    @property
    def widget_attrs(self):
        return {}

    @property
    def must_verify_email(self):
        raise NotImplementedError

    @property
    def extra_emails(self):
        # Extra emails that user should get as secondary emails.
        # To make this easier to use in some cases, the set may contain the primary email, too.
        return set()

    def create_identity(self, data):
        raise NotImplementedError

    def redirect_success(self):
        raise NotImplementedError


class MultipassRegistrationHandler(RegistrationHandler):
    form = MultipassRegistrationForm

    def __init__(self, rh):
        self.identity_info = rh.identity_info

    def email_verified(self, email):
        session['login_identity_info']['data']['email'] = email
        session['login_identity_info']['email_verified'] = True
        session.modified = True

    def get_form_defaults(self):
        return FormDefaults(self.identity_info['data'])

    def create_form(self):
        form = super(MultipassRegistrationHandler, self).create_form()
        # We only want the phone/address fields if the provider gave us data for it
        for field in {'address', 'phone'}:
            if field in form and not self.identity_info['data'][field]:
                delattr(form, field)
        emails = self.identity_info['data'].getlist('email')
        form.email.choices = zip(emails, emails)
        return form

    @property
    def must_verify_email(self):
        return not self.identity_info['email_verified']

    @property
    def extra_emails(self):
        return set(self.identity_info['data'].getlist('email'))

    def create_identity(self, data):
        del session['login_identity_info']
        return Identity(provider=self.identity_info['provider'], identifier=self.identity_info['identifier'],
                        data=self.identity_info['data'], multipass_data=self.identity_info['multipass_data'])

    def redirect_success(self):
        return multipass.redirect_success()


class LocalRegistrationHandler(RegistrationHandler):
    form = LocalRegistrationForm

    def __init__(self, rh):
        if 'next' in request.args:
            session['register_next_url'] = request.args['next']

    @property
    def widget_attrs(self):
        return {'email': {'disabled': not self.must_verify_email}}

    @property
    def must_verify_email(self):
        return 'register_verified_email' not in session

    def email_verified(self, email):
        session['register_verified_email'] = email

    def get_form_defaults(self):
        email = session.get('register_verified_email')
        existing_user_id = session.get('register_pending_user')
        existing_user = User.get(existing_user_id) if existing_user_id else None
        data = {'email': email}

        if existing_user:
            data.update(first_name=existing_user.first_name,
                        last_name=existing_user.last_name,
                        affiliation=existing_user.affiliation)

        return FormDefaults(**data)

    def create_form(self):
        form = super(LocalRegistrationHandler, self).create_form()
        if not self.must_verify_email:
            form.email.data = session['register_verified_email']
        return form

    def create_identity(self, data):
        del session['register_verified_email']
        return Identity(provider='indico', identifier=data['username'], password=data['password'])

    def redirect_success(self):
        return redirect(session.pop('register_next_url', url_for('misc.index')))


class RHResetPassword(RH):
    """Resets the password for a local identity."""

    def _checkParams(self):
        if not Config.getInstance().getLocalIdentities():
            raise Forbidden('Local identities are disabled')

    def _process(self):
        if 'token' in request.args:
            identity_id = secure_serializer.loads(request.args['token'], max_age=3600, salt='reset-password')
            identity = Identity.get(identity_id)
            if not identity:
                raise BadData('Identity does not exist')
            return self._reset_password(identity)
        else:
            return self._request_token()

    def _request_token(self):
        form = ResetPasswordEmailForm()
        if form.validate_on_submit():
            user = form.user
            # The only case where someone would have more than one identity is after a merge.
            # And the worst case that can happen here is that we send the user a different
            # username than the one he expects. But he still gets back into his account.
            # Showing a list of usernames would be a little bit more user-friendly but less
            # secure as we'd expose valid usernames for a specific user to an untrusted person.
            identity = next(iter(user.local_identities))
            _send_confirmation(form.email.data, 'reset-password', '.resetpass', 'auth/emails/reset_password.txt',
                               {'user': user, 'username': identity.identifier}, data=identity.id)
            session['resetpass_email_sent'] = True
            return redirect(url_for('.resetpass'))
        return WPAuth.render_template('reset_password.html', form=form, identity=None, widget_attrs={},
                                      email_sent=session.pop('resetpass_email_sent', False))

    def _reset_password(self, identity):
        form = ResetPasswordForm()
        if form.validate_on_submit():
            identity.password = form.password.data
            flash(_("Your password has been changed successfully."), 'success')
            login_user(identity.user, identity)
            # We usually come here from a multipass login page so we should have a target url
            return multipass.redirect_success()
        form.username.data = identity.identifier
        return WPAuth.render_template('reset_password.html', form=form, identity=identity,
                                      widget_attrs={'username': {'disabled': True}})
