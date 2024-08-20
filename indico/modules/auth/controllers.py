# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, jsonify, redirect, render_template, request, session
from itsdangerous import BadData, BadSignature
from markupsafe import Markup
from marshmallow import RAISE, ValidationError, post_load, pre_load, validate, validates, validates_schema
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.auth import login_rate_limiter, multipass, signup_rate_limiter
from indico.core.config import config
from indico.core.db import db
from indico.core.marshmallow import mm
from indico.core.notifications import make_email, send_email
from indico.modules.admin import RHAdminBase
from indico.modules.auth import Identity, logger, login_user
from indico.modules.auth.forms import (AddLocalIdentityForm, EditLocalIdentityForm, RegistrationEmailForm,
                                       ResetPasswordEmailForm, ResetPasswordForm, SelectEmailForm)
from indico.modules.auth.models.registration_requests import RegistrationRequest
from indico.modules.auth.util import (impersonate_user, load_identity_info, register_user, undo_impersonate_user,
                                      url_for_logout)
from indico.modules.auth.views import WPAuth, WPAuthUser, WPSignup
from indico.modules.legal import legal_settings
from indico.modules.users import User, user_management_settings
from indico.modules.users.controllers import RHUserBase
from indico.modules.users.models.affiliations import Affiliation
from indico.util.date_time import format_human_timedelta, now_utc
from indico.util.i18n import _, force_locale
from indico.util.marshmallow import LowercaseString, ModelField, not_empty
from indico.util.passwords import validate_secure_password
from indico.util.signing import secure_serializer
from indico.util.string import crc32
from indico.web.args import parser, use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults, IndicoForm
from indico.web.rh import RH
from indico.web.util import url_for_index


def _get_provider(name, external):
    try:
        provider = multipass.auth_providers[name]
    except KeyError:
        raise NotFound('Provider does not exist')
    if provider.is_external != external:
        raise NotFound('Invalid provider')
    return provider


class RHLogin(RH):
    """The login page."""

    # Disable global CSRF check. The form might not be an IndicoForm
    # but a normal WTForm from Flask-WTF which does not use the same
    # CSRF token as Indico forms use. But since the form has its own
    # CSRF check anyway disabling the global check is perfectly fine.
    CSRF_ENABLED = False

    @use_kwargs({'force': fields.Bool(load_default=False)}, location='query')
    def _process(self, force):
        login_reason = session.pop('login_reason', None)

        # User is already logged in
        if session.user is not None and not force:
            multipass.set_next_url()
            return multipass.redirect_success()

        # Some clients attempt to incorrectly resolve redirections internally.
        # See https://github.com/indico/indico/issues/4720 for details
        user_agent = request.headers.get('User-Agent', '')
        sso_redirect = not any(s in user_agent for s in ('ms-office', 'Microsoft Office'))

        # If we have only one provider, and this provider is external, we go there immediately
        # However, after a failed login we need to show the page to avoid a redirect loop
        if not session.pop('_multipass_auth_failed', False) and 'provider' not in request.view_args and sso_redirect:
            single_auth_provider = multipass.single_auth_provider
            if single_auth_provider and single_auth_provider.is_external:
                multipass.set_next_url()
                return redirect(url_for('.login', provider=single_auth_provider.name))

        # Save the 'next' url to go to after login
        multipass.set_next_url()

        # If there's a provider in the URL we start the external login process
        if 'provider' in request.view_args:
            provider = _get_provider(request.view_args['provider'], True)
            return provider.initiate_external_login()

        # If we have a POST request we submitted a login form for a local provider
        rate_limit_exceeded = False
        if request.method == 'POST':
            active_provider = provider = _get_provider(request.form['_provider'], False)
            form = provider.login_form()
            rate_limit_exceeded = not login_rate_limiter.test()
            if not rate_limit_exceeded and form.validate_on_submit():
                response = multipass.handle_login_form(provider, form.data)
                if response:
                    return response
                # re-check since a failed login may have triggered the rate limit
                rate_limit_exceeded = not login_rate_limiter.test()
        # Otherwise we show the form for the default provider
        else:
            active_provider = multipass.default_local_auth_provider
            form = active_provider.login_form() if active_provider else None

        providers = list(multipass.auth_providers.values())
        retry_in = login_rate_limiter.get_reset_delay() if rate_limit_exceeded else None
        return render_template('auth/login_page.html', form=form, providers=providers, active_provider=active_provider,
                               login_reason=login_reason, retry_in=retry_in, force=(force or None))


class RHLoginForm(RH):
    """Retrieve a login form (json)."""

    def _process(self):
        provider = _get_provider(request.view_args['provider'], False)
        form = provider.login_form()
        template_module = get_template_module('auth/_login_form.html')
        return jsonify(success=True, html=template_module.login_form(provider, form))


class RHLogout(RH):
    """Log the user out."""

    def _process(self):
        next_url = request.args.get('next')
        if not next_url or not multipass.validate_next_url(next_url):
            next_url = url_for_index()
        return multipass.logout(next_url, clear_session=True)


def _send_confirmation(email, salt, endpoint, template, template_args=None, url_args=None, data=None):
    template_args = template_args or {}
    url_args = url_args or {}
    token = secure_serializer.dumps(data or email, salt=salt)
    url = url_for(endpoint, token=token, _external=True, **url_args)
    with force_locale(None) if 'user' not in template_args else template_args['user'].force_user_locale():
        template_module = get_template_module(template, email=email, url=url, **template_args)
        send_email(make_email(email, template=template_module))
    flash(_('We have sent you a verification email. Please check your mailbox within the next hour and open '
            'the link in that email.'))
    return redirect(url_for(endpoint, **url_args))


class RHLinkAccount(RH):
    """Link a new identity with an existing user.

    This RH is only used if the identity information contains an
    email address and an existing user was found.
    """

    def _process_args(self):
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
            email = secure_serializer.loads(request.args['token'], max_age=3600, salt='link-identity-email')
            if email not in self.emails:
                raise BadData('Emails do not match')
            session['login_identity_info']['email_verified'] = True
            session.modified = True
            flash(_('You have successfully validated your email address and can now proceed with the login.'),
                  'success')
            return redirect(url_for('.link_account', provider=self.identity_info['provider']))

        if self.must_choose_email:
            form = SelectEmailForm()
            form.email.choices = list(zip(self.emails, self.emails, strict=True))
        else:
            form = IndicoForm()

        if form.validate_on_submit():
            if self.email_verified:
                return self._create_identity()
            elif not self.verification_email_sent:
                return self._send_confirmation(form.email.data if self.must_choose_email else self.emails[0])
            else:
                flash(_('The validation email has already been sent.'), 'warning')

        return WPAuth.render_template('link_identity.html', identity_info=self.identity_info, user=self.user,
                                      email_sent=self.verification_email_sent, emails=' / '.join(self.emails),
                                      form=form, must_choose_email=self.must_choose_email)

    def _create_identity(self):
        identity = Identity(user=self.user, provider=self.identity_info['provider'],
                            identifier=self.identity_info['identifier'], data=self.identity_info['data'],
                            multipass_data=self.identity_info['multipass_data'])
        logger.info('Created new identity for %s: %s', self.user, identity)
        del session['login_identity_info']
        db.session.flush()
        login_user(self.user, identity)
        return multipass.redirect_success()

    def _send_confirmation(self, email):
        session['login_identity_info']['verification_email_sent'] = True
        session['login_identity_info']['data']['email'] = email  # throw away other emails
        return _send_confirmation(email, 'link-identity-email', '.link_account',
                                  'auth/emails/link_identity_verify_email.txt', {'user': self.user},
                                  url_args={'provider': self.identity_info['provider']})


class RHRegister(RH):
    """Create a new indico user.

    This handles two cases:
    - creation of a new user with a locally stored username and password
    - creation of a new user based on information from an identity provider
    """

    def _process_args(self):
        self.identity_info = None
        self.provider_name = request.view_args['provider']
        if self.provider_name is not None:
            self.identity_info = info = load_identity_info()
            if not info:
                return redirect(url_for('.login'))
            elif info['indico_user_id'] is not None or info['provider'] != self.provider_name:
                # If we have a matching user id, we shouldn't be on the registration page
                # If the provider doesn't match it would't be a big deal but the request doesn't make sense
                raise BadRequest
        elif not config.LOCAL_IDENTITIES:
            raise Forbidden('Local identities are disabled')
        elif not config.LOCAL_REGISTRATION:
            raise Forbidden('Local registration is disabled')

    def _get_verified_email(self):
        """Check if there is an email verification token."""
        try:
            token = request.args['token']
        except KeyError:
            return None, None
        try:
            return secure_serializer.loads(token, max_age=3600, salt='register-email'), False
        except BadSignature:
            return secure_serializer.loads(token, max_age=86400 * 31, salt='register-email-prevalidated'), True

    def _process(self):
        if session.user:
            return redirect(url_for_index())

        handler = MultipassRegistrationHandler(self) if self.identity_info else LocalRegistrationHandler(self)
        verified_email, prevalidated = self._get_verified_email()
        if verified_email is not None:
            handler.email_verified(verified_email)
            if prevalidated:
                flash(_('You may change your email address after finishing the registration process.'), 'info')
            else:
                flash(_('You have successfully validated your email address and can now proceed with the '
                        'registration.'), 'success')
            return redirect(url_for('.register', provider=self.provider_name))

        if handler.must_verify_email:
            return self._process_verify(handler)

        signup_config = handler.get_signup_config()
        if request.method == 'POST':
            if 'is_email_verification' not in request.form:
                return self._process_post(handler)
            elif request.form.get('email') != session.get('register_verified_email'):
                # User somehow succeeded to trigger again the request to send verification email
                # while the session is pending to a previously validated email
                flash(_('Please finish or cancel your pending registration before attempting to register with '
                        'another email address.'), 'warning')
        return WPSignup.render_template('register.html', signup_config=signup_config)

    def _process_verify(self, handler):
        email_sent = session.pop('register_verification_email_sent', False)
        form = handler.create_verify_email_form()
        rate_limit_exceeded = not signup_rate_limiter.test()
        if not email_sent and rate_limit_exceeded:
            # tell users that they exceeded the rate limit, but NOT if they just
            # used their last attempt successfully
            retry_in = login_rate_limiter.get_reset_delay()
            delay = format_human_timedelta(retry_in, 'minutes')
            flash(_('Too many signup attempts. Please wait {}').format(delay), 'error')
        if not rate_limit_exceeded and form.validate_on_submit():
            signup_rate_limiter.hit()
            return self._send_confirmation(form.email.data)
        return WPSignup.render_template('register_verify.html', form=form, email_sent=email_sent)

    def _process_post(self, handler):
        data = handler.parse_request()
        if handler.moderate_registrations:
            rv = self._create_registration_request(data, handler)
        else:
            rv = self._create_user(data, handler)
        return jsonify(redirect=rv.headers['Location'])

    def _send_confirmation(self, email):
        session['register_verification_email_sent'] = True
        return _send_confirmation(email, 'register-email', '.register', 'auth/emails/register_verify_email.txt',
                                  url_args={'provider': self.provider_name})

    def _prepare_registration_data(self, data, handler):
        email = data['email']
        extra_emails = handler.get_all_emails(data) - {email}
        user_data = {k: v for k, v in data.items()
                     if k in {'first_name', 'last_name', 'affiliation', 'affiliation_link', 'address', 'phone'}}
        user_data.update(handler.get_extra_user_data(data))
        if data.pop('accept_terms', False):
            user_data['accepted_terms_dt'] = now_utc()
        identity_data = handler.get_identity_data(data)
        settings = {
            'timezone': config.DEFAULT_TIMEZONE if session.timezone == 'LOCAL' else session.timezone,
            'lang': session.lang or config.DEFAULT_LOCALE
        }
        return {'email': email, 'extra_emails': extra_emails, 'user_data': user_data, 'identity_data': identity_data,
                'settings': settings}

    def _create_registration_request(self, data, handler):
        registration_data = self._prepare_registration_data(data, handler)
        email = registration_data['email']
        req = RegistrationRequest.query.filter_by(email=email).first() or RegistrationRequest(email=email)
        req.comment = data['comment']
        if accepted_terms_dt := registration_data['user_data'].pop('accepted_terms_dt', None):
            registration_data['user_data']['accepted_terms_dt'] = accepted_terms_dt.isoformat()
        if aff_link := registration_data['user_data'].pop('affiliation_link', None):
            db.session.add(aff_link)  # in case it's newly created
            db.session.flush()
            registration_data['user_data']['affiliation_id'] = aff_link.id
        req.populate_from_dict(registration_data)
        db.session.add(req)
        db.session.flush()
        signals.users.registration_requested.send(req)
        flash(_('Your registration request has been received. We will send you an email once it has been processed.'),
              'success')
        return handler.redirect_success()

    def _create_user(self, data, handler):
        user, identity = register_user(**self._prepare_registration_data(data, handler))
        login_user(user, identity)
        msg = _('You have sucessfully registered your Indico profile. '
                'Check <a href="{url}">your profile</a> for further details and settings.')
        flash(Markup(msg).format(url=url_for('users.user_profile')), 'success')
        db.session.flush()
        return handler.redirect_success()


class RHAccounts(RHUserBase):
    """Display user accounts."""

    def _create_form(self):
        if self.user.local_identity:
            defaults = FormDefaults(username=self.user.local_identity.identifier)
            local_account_form = EditLocalIdentityForm(identity=self.user.local_identity, obj=defaults)
        else:
            local_account_form = AddLocalIdentityForm()
        return local_account_form

    def _handle_add_local_account(self, form):
        identity = Identity(provider='indico', identifier=form.data['username'], password=form.data['password'])
        self.user.identities.add(identity)
        logger.info('User %s added a local account (%s)', self.user, identity.identifier)
        flash(_('Local account added successfully'), 'success')

    def _handle_edit_local_account(self, form):
        self.user.local_identity.identifier = form.data['username']
        if form.data['new_password']:
            self.user.local_identity.password = form.data['new_password']
            session.pop('insecure_password_error', None)
            logger.info('User %s (%s) changed their password', self.user, self.user.local_identity.identifier)
        flash(_('Your local account credentials have been updated successfully'), 'success')

    def _process(self):
        insecure_login_password_error = session.get('insecure_password_error')

        form = self._create_form()
        if form.validate_on_submit():
            if isinstance(form, AddLocalIdentityForm):
                self._handle_add_local_account(form)
            elif isinstance(form, EditLocalIdentityForm):
                self._handle_edit_local_account(form)
            return redirect(url_for('auth.accounts'))
        provider_titles = {name: provider.title for name, provider in multipass.identity_providers.items()}
        return WPAuthUser.render_template('accounts.html', 'accounts',
                                          form=form, user=self.user, provider_titles=provider_titles,
                                          insecure_login_password_error=insecure_login_password_error)


class RHRemoveAccount(RHUserBase):
    """Remove an identity linked to a user."""

    def _process_args(self):
        RHUserBase._process_args(self)
        self.identity = Identity.get_or_404(request.view_args['identity'])
        if self.identity.user != self.user:
            raise NotFound

    def _process(self):
        if session.get('login_identity') == self.identity.id:
            raise BadRequest("The identity used to log in can't be removed")
        if self.user.local_identity == self.identity:
            raise BadRequest("The main local identity can't be removed")
        self.user.identities.remove(self.identity)
        try:
            provider_title = multipass.identity_providers[self.identity.provider].title
        except KeyError:
            provider_title = self.identity.provider.title()
        flash(_('{provider} ({identifier}) successfully removed from your accounts')
              .format(provider=provider_title, identifier=self.identity.identifier), 'success')
        return redirect(url_for('.accounts'))


class RegistrationHandler:
    def __init__(self, rh):
        pass

    def create_verify_email_form(self):
        return RegistrationEmailForm()

    def email_verified(self, email):
        raise NotImplementedError

    def get_pending_initial_data(self, emails):
        pending = User.query.filter(~User.is_deleted, User.is_pending, User.all_emails.in_(emails)).first()
        if not pending:
            return {}
        data = {
            'first_name': pending.first_name,
            'last_name': pending.last_name,
            'affiliation': pending.affiliation,
            'affiliation_data': {'id': pending.affiliation_id, 'text': pending.affiliation},
        }
        if pending.phone:
            data['phone'] = pending.phone
        if pending.address:
            data['address'] = pending.address
        return data

    def get_signup_config(self):
        effective_date = legal_settings.get('terms_effective_date')

        return {
            'cancelURL': url_for_logout(),
            'moderated': self.moderate_registrations,
            'hasPredefinedAffiliations': Affiliation.query.has_rows(),
            'mandatoryFields': user_management_settings.get('mandatory_fields_account_request'),
            'tosUrl': legal_settings.get('tos_url'),
            'tos': legal_settings.get('tos'),
            'privacyPolicyUrl': legal_settings.get('privacy_policy_url'),
            'privacyPolicy': legal_settings.get('privacy_policy'),
            'termsRequireAccept': legal_settings.get('terms_require_accept'),
            'termsEffectiveDate': effective_date.isoformat() if effective_date else None,
        }

    def create_schema(self):
        emails = self.get_all_emails()
        mandatory_fields = user_management_settings.get('mandatory_fields_account_request')

        class SignupSchema(mm.Schema):
            class Meta:
                unknown = RAISE

            email = fields.String(required=True, validate=validate.OneOf(emails))
            first_name = fields.String(required=True)
            last_name = fields.String(required=True)
            address = fields.String(load_default='')
            if self.moderate_registrations and 'affiliation' in mandatory_fields:
                affiliation = fields.String(required=True, validate=not_empty)
            else:
                affiliation = fields.String(load_default='')
            phone = fields.String(load_default='')
            affiliation_link = ModelField(Affiliation, data_key='affiliation_id', load_default=None)

            if legal_settings.get('terms_require_accept'):
                accept_terms = fields.Bool(required=True, validate=not_empty)

            if self.moderate_registrations:
                if 'comment' in mandatory_fields:
                    comment = fields.String(required=True, validate=not_empty)
                else:
                    comment = fields.String(load_default='')

            @post_load
            def ensure_affiliation_text(self, data, **kwargs):
                if affiliation_link := data.get('affiliation_link'):
                    data['affiliation'] = affiliation_link.name
                elif 'affiliation' in data:
                    data['affiliation_link'] = None
                return data

            @validates('email')
            def check_email_unique(self, email, **kwargs):
                if User.query.filter(~User.is_deleted, ~User.is_pending, User.all_emails == email).has_rows():
                    raise ValidationError('Email already in use')

        return SignupSchema

    def parse_request(self):
        return parser.parse(self.create_schema())

    @property
    def must_verify_email(self):
        raise NotImplementedError

    @property
    def moderate_registrations(self):
        return False

    def get_all_emails(self, data=None):
        # All (verified!) emails that should be set on the user.
        # This MUST include the primary email from the form if available.
        # Any additional emails will be set as secondary emails
        # The emails returned here are used to check for pending users
        return {data['email']} if data and data.get('email') else set()

    def get_identity_data(self, data):
        raise NotImplementedError

    def get_extra_user_data(self, data):
        return {}

    def redirect_success(self):
        raise NotImplementedError


class MultipassRegistrationHandler(RegistrationHandler):
    def __init__(self, rh):
        self.identity_info = rh.identity_info

    @property
    def from_sync_provider(self):
        # If the multipass login came from the provider that's used for synchronization
        return multipass.sync_provider and multipass.sync_provider.name == self.identity_info['provider']

    def create_verify_email_form(self):
        if email := self.identity_info['data'].get('email'):
            return RegistrationEmailForm(email=email)
        return super().create_verify_email_form()

    def email_verified(self, email):
        session['login_identity_info']['data']['email'] = email
        session['login_identity_info']['email_verified'] = True
        session.modified = True

    def get_signup_config(self):
        base_signup_config = super().get_signup_config()

        emails = sorted(set(self.identity_info['data'].getlist('email')))
        initial_values = {
            'email': emails[0] if emails else '',
            'synced_fields': [],
            'affiliation_data': {'id': None, 'text': ''}
        }
        affiliation_meta = None
        pending_data = self.get_pending_initial_data(emails)
        if self.from_sync_provider:
            synced_fields = set(multipass.synced_fields)
            synced_values = {k: v or '' for k, v in self.identity_info['data'].items() if k in synced_fields}
            required_empty_fields = {x for x in ('first_name', 'last_name') if not synced_values.get(x)}
            initial_values['synced_fields'] = sorted(multipass.synced_fields - required_empty_fields)
            initial_values.update(synced_values)
            if affiliation_data := self.identity_info['data'].get('affiliation_data'):
                affiliation_meta = affiliation_data | {'id': -1}
                initial_values['affiliation_data'] = {'id': -1, 'text': affiliation_data['name']}
                if 'affiliation' in synced_fields:
                    synced_values['affiliation_id'] = -1
            initial_values.update((k, v) for k, v in pending_data.items()
                                  if k not in synced_fields and k not in initial_values)
            locked_fields = list(multipass.locked_fields - required_empty_fields)
        else:
            synced_values = {}
            allowed_fields = {'first_name', 'last_name', 'affiliation', 'phone', 'address'}
            multipass_data = {k: v for k, v in self.identity_info['data'].items() if k in allowed_fields and v}
            initial_values.update(pending_data or multipass_data)
            locked_fields = []

        return {
            **base_signup_config,
            'initialValues': initial_values,
            'showAccountForm': False,
            'syncedValues': synced_values,
            'emails': emails,
            'affiliationMeta': affiliation_meta,
            'hasPendingUser': bool(pending_data),
            'lockedFields': locked_fields,
            'lockedFieldMessage': multipass.locked_field_message,
        }

    def create_schema(self):
        class MultipassSignupSchema(super().create_schema()):
            synced_fields = fields.List(fields.String(validate=validate.OneOf(multipass.synced_fields)), required=True)

            @pre_load
            def fix_affiliation_id(self, data, **kwargs):
                if data.get('affiliation_id') == -1:
                    self.context['use_default_affiliation_link'] = True
                    del data['affiliation_id']
                return data

            @post_load
            def pass_default_affiliation(self, data, **kwargs):
                if self.context.get('use_default_affiliation_link'):
                    data['use_default_affiliation_link'] = True
                return data

            @post_load
            def remove_synced_data(self, data, **kwargs):
                for field in data['synced_fields']:
                    if field == 'email':
                        continue
                    if field == 'affiliation':
                        del data['affiliation_link']
                    del data[field]
                return data

            @validates_schema(skip_on_field_errors=True)
            def validate_everything(self, data, **kwargs):
                if 'first_name' not in data['synced_fields'] and not data['first_name']:
                    raise ValidationError(_('This field cannot be empty.'), 'first_name')
                if 'last_name' not in data['synced_fields'] and not data['last_name']:
                    raise ValidationError(_('This field cannot be empty.'), 'last_name')

        return MultipassSignupSchema

    def parse_request(self):
        def _must_force_sync(field):
            if field not in ('first_name', 'last_name'):
                return True
            return self.identity_info['data'].get(field)
        data = super().parse_request()
        data['synced_fields'] += [f for f in multipass.locked_fields
                                  if f not in data['synced_fields'] and _must_force_sync(f)]
        for field in data['synced_fields']:
            data[field] = self.identity_info['data'][field] or ''
        if (
            data.pop('use_default_affiliation_link', False) and
            (aff_data := self.identity_info['data'].get('affiliation_data'))
        ):
            data['affiliation_link'] = Affiliation.get_or_create_from_data(aff_data)
            data['affiliation'] = data['affiliation_link'].name
        return data

    @property
    def must_verify_email(self):
        return not self.identity_info['email_verified']

    @property
    def moderate_registrations(self):
        return self.identity_info['moderated']

    def get_all_emails(self, data=None):
        emails = super().get_all_emails(data)
        return emails | set(self.identity_info['data'].getlist('email'))

    def get_identity_data(self, data):
        del session['login_identity_info']
        return {'provider': self.identity_info['provider'], 'identifier': self.identity_info['identifier'],
                'data': self.identity_info['data'], 'multipass_data': self.identity_info['multipass_data']}

    def get_extra_user_data(self, data):
        extra_data = super().get_extra_user_data(data)
        if self.from_sync_provider:
            extra_data['synced_fields'] = sorted(
                set(data.get('synced_fields', ())) | (multipass.synced_fields - set(data))
            )
        return extra_data

    def redirect_success(self):
        return multipass.redirect_success()


class LocalRegistrationHandler(RegistrationHandler):
    def __init__(self, rh):
        next_url = request.args.get('next')
        if next_url and multipass.validate_next_url(next_url):
            session['register_next_url'] = next_url

    def get_signup_config(self):
        base_signup_config = super().get_signup_config()
        email = session['register_verified_email']
        initial_values = {'email': email, 'affiliation_data': {'id': None, 'text': ''}}
        pending_data = self.get_pending_initial_data([email])
        initial_values.update(pending_data)
        return {
            **base_signup_config,
            'initialValues': initial_values,
            'showAccountForm': True,
            'syncedValues': {},
            'emails': [email],
            'hasPendingUser': bool(pending_data),
        }

    def create_schema(self):
        class LocalSignupSchema(super().create_schema()):
            first_name = fields.String(required=True, validate=not_empty)
            last_name = fields.String(required=True, validate=not_empty)
            username = LowercaseString(required=True, validate=not_empty)
            password = fields.String(required=True, validate=not_empty)

            @validates('username')
            def validate_username(self, username, **kwargs):
                if Identity.query.filter_by(provider='indico', identifier=username).has_rows():
                    raise ValidationError(_('This username is already in use.'))

            @validates_schema(skip_on_field_errors=False)
            def validate_password(self, data, **kwargs):
                if error := validate_secure_password('set-user-password', data['password'],
                                                     username=data.get('username', '')):
                    raise ValidationError(error, 'password')

        return LocalSignupSchema

    @property
    def must_verify_email(self):
        return 'register_verified_email' not in session

    @property
    def moderate_registrations(self):
        return config.LOCAL_MODERATION

    def get_all_emails(self, data=None):
        emails = super().get_all_emails(data)
        if not self.must_verify_email:
            emails.add(session['register_verified_email'])
        return emails

    def email_verified(self, email):
        session['register_verified_email'] = email

    def get_identity_data(self, data):
        del session['register_verified_email']
        return {'provider': 'indico', 'identifier': data['username'],
                'password_hash': Identity.password.backend.create_hash(data['password'])}

    def redirect_success(self):
        return redirect(session.pop('register_next_url', url_for_index()))


class RHResetPassword(RH):
    """Reset the password for a local identity."""

    def _process_args(self):
        if not config.LOCAL_IDENTITIES:
            raise Forbidden('Local identities are disabled')

    def _process(self):
        if 'token' in request.args:
            data = secure_serializer.loads(request.args['token'], max_age=3600, salt='reset-password')
            identity = Identity.get(data['id'])
            if not identity:
                raise BadData('Identity does not exist')
            elif crc32(identity.password_hash) != data['hash']:
                raise BadData('Password already changed')
            return self._reset_password(identity)
        else:
            return self._request_token()

    def _request_token(self):
        form = ResetPasswordEmailForm()
        if form.validate_on_submit():
            user = form.user
            # The only case where someone would have more than one identity is after a merge.
            # And the worst case that can happen here is that we send the user a different
            # username than the one he expects. But he still gets back into his profile.
            # Showing a list of usernames would be a little bit more user-friendly but less
            # secure as we'd expose valid usernames for a specific user to an untrusted person.
            identity = next(iter(user.local_identities))
            _send_confirmation(form.email.data, 'reset-password', '.resetpass', 'auth/emails/reset_password.txt',
                               {'user': user, 'username': identity.identifier},
                               data={'id': identity.id, 'hash': crc32(identity.password_hash)})
            session['resetpass_email_sent'] = True
            logger.info('Password reset requested for user %s', user)
            return redirect(url_for('.resetpass'))
        return WPAuth.render_template('reset_password.html', form=form, identity=None, widget_attrs={},
                                      email_sent=session.pop('resetpass_email_sent', False))

    def _reset_password(self, identity):
        form = ResetPasswordForm()
        if form.validate_on_submit():
            identity.password = form.password.data
            flash(_('Your password has been changed successfully.'), 'success')
            login_user(identity.user, identity)
            logger.info('Password reset confirmed for user %s', identity.user)
            # We usually come here from a multipass login page so we should have a target url
            return multipass.redirect_success()
        form.username.data = identity.identifier
        return WPAuth.render_template('reset_password.html', form=form, identity=identity, email_sent=False,
                                      widget_attrs={'username': {'disabled': True}})


class RHAdminImpersonate(RHAdminBase):
    @use_kwargs({
        'undo': fields.Bool(load_default=False),
        'user_id': fields.Int(load_default=None)
    })
    def _process_args(self, undo, user_id):
        RHAdminBase._process_args(self)
        self.user = None if undo else User.get_or_404(user_id, is_deleted=False)

    def _check_access(self):
        if self.user:
            RHAdminBase._check_access(self)

    def _process(self):
        if self.user:
            impersonate_user(self.user)
        else:
            # no user? it means it's an undo
            undo_impersonate_user()

        return jsonify()
