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

from flask import session, redirect, request, flash
from itsdangerous import BadData
from markupsafe import Markup
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core.config import Config
from indico.core.db import db
from indico.core.notifications import make_email
from indico.modules.auth import multiauth, logger, Identity, login_user
from indico.modules.auth.forms import (SelectEmailForm, MultiAuthRegistrationForm, LocalRegistrationForm,
                                       RegistrationEmailForm)
from indico.modules.auth.util import load_identity_info
from indico.modules.auth.views import WPAuth
from indico.modules.users import User
from indico.util.i18n import _
from indico.util.signing import secure_serializer
from indico.web.flask.util import url_for
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults, IndicoForm

from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.rh.base import RH


class RHLogout(RH):
    """Logs the user out"""

    def _process(self):
        session.clear()
        url = request.args.get('next') or url_for('misc.index')
        return redirect(url)
        # return multiauth.logout(url) or redirect(url)


def _send_confirmation(email, salt, endpoint, template, template_args=None, url_args=None):
    template_args = template_args or {}
    url_args = url_args or {}
    token = secure_serializer.dumps(email, salt=salt)
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
            return multiauth.redirect_success()
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
            return redirect(url_for('.associate_identity'))

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
                            multiauth_data=self.identity_info['multiauth_data'])
        logger.info('Created new identity for {}: {}'.format(self.user, identity))
        del session['login_identity_info']
        login_user(self.user)
        return multiauth.redirect_success()

    def _send_confirmation(self, email):
        session['login_identity_info']['verification_email_sent'] = True
        session['login_identity_info']['data']['email'] = email  # throw away other emails
        return _send_confirmation(email, 'associate-identity-email', '.associate_identity',
                                  'auth/emails/associate_identity_verify_email.txt', {'user': self.user})


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
        handler = MultiAuthRegistrationHandler(self) if self.identity_info else LocalRegistrationHandler(self)
        verified_email = self._get_verified_email()
        if verified_email is not None:
            handler.email_verified(verified_email)
            flash(_('You have successfully validated your email address and can now proceeed with the registration.'),
                  'success')
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
        user = User(first_name=data['first_name'], last_name=data['last_name'], email=data['email'],
                    phone=data.get('phone', ''), affiliation=data['affiliation'])
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
        login_user(user, (identity.provider, identity.identifier))
        msg = _('You have sucessfully registered your Indico account. '
                'Check <a href="{url}">your profile</a> for further account details and settings.')
        flash(Markup(msg).format(url=url_for('users.user_profile')), 'success')
        return handler.redirect_success()


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


class MultiAuthRegistrationHandler(RegistrationHandler):
    form = MultiAuthRegistrationForm

    def __init__(self, rh):
        self.identity_info = rh.identity_info

    def email_verified(self, email):
        session['login_identity_info']['data']['email'] = email
        session['login_identity_info']['email_verified'] = True
        session.modified = True

    def get_form_defaults(self):
        return FormDefaults(self.identity_info['data'])

    def create_form(self):
        form = super(MultiAuthRegistrationHandler, self).create_form()
        # We only want the phone field if the provider gave us a phone number
        if 'phone' in form and not self.identity_info['data']['phone']:
            del form.phone
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
                        data=self.identity_info['data'], multiauth_data=self.identity_info['multiauth_data'])

    def redirect_success(self):
        return multiauth.redirect_success()


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
        return FormDefaults(email=session.get('register_verified_email'))

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
