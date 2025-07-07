# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import functools

from flask import current_app, request
from flask_multipass import InvalidCredentials, Multipass, NoSuchUser
from werkzeug.local import LocalProxy

from indico.core import signals
from indico.core.config import config
from indico.core.limiter import make_rate_limiter
from indico.core.logger import Logger
from indico.util.signals import values_from_signal


logger = Logger.get('auth')
login_rate_limiter = LocalProxy(
    functools.cache(lambda: make_rate_limiter('login', config.FAILED_LOGIN_RATE_LIMIT))
)
login_rate_limiter_user = LocalProxy(
    functools.cache(lambda: make_rate_limiter('login-user', config.FAILED_LOGIN_RATE_LIMIT_USER))
)
signup_rate_limiter = LocalProxy(
    functools.cache(lambda: make_rate_limiter('signup', config.SIGNUP_RATE_LIMIT))
)
signup_rate_limiter_email = LocalProxy(
    functools.cache(lambda: make_rate_limiter('signup-email', config.SIGNUP_RATE_LIMIT_EMAIL))
)


class IndicoMultipass(Multipass):
    @property
    def default_local_auth_provider(self):
        """The default form-based auth provider."""
        return next((p for p in self.auth_providers.values() if not p.is_external and p.settings.get('default')),
                    None)

    @property
    def sync_provider(self):
        """The synchronization provider.

        This is the identity provider used to sync user data.
        """
        return next((p for p in self.identity_providers.values() if p.settings.get('synced_fields')), None)

    @property
    def has_moderated_providers(self):
        return (
            config.LOCAL_MODERATION or
            any(p for p in self.identity_providers.values() if p.settings.get('moderated'))
        )

    @property
    def synced_fields(self):
        """The keys to be synchronized.

        This is the set of keys to be synced to user data.
        The ``email`` can never be synchronized.
        """
        provider = self.sync_provider
        if provider is None:
            return set()
        synced_fields = set(provider.settings.get('synced_fields'))
        synced_fields &= set(current_app.config['MULTIPASS_IDENTITY_INFO_KEYS'])
        return synced_fields

    @property
    def locked_fields(self):
        """The keys that cannot be desynchronized.

        This is a subset of the keys listed in ``synced_fields`` that cannot be
        desynchronized by a non-admin user.
        """
        provider = self.sync_provider
        if provider is None:
            return set()
        return (set(provider.settings.get('locked_fields', ())) & self.synced_fields) - {'email'}

    @property
    def locked_field_message(self):
        provider = self.sync_provider
        if provider is None:
            return ''
        return provider.settings.get('locked_field_message', '')

    def init_app(self, app):
        super().init_app(app)
        with app.app_context():
            self._check_default_provider()

    def _check_default_provider(self):
        # Ensure that there is maximum one sync provider
        sync_providers = [p for p in self.identity_providers.values() if p.settings.get('synced_fields')]
        if len(sync_providers) > 1:
            raise ValueError('There can only be one sync provider.')
        # Ensure that there is exactly one form-based default auth provider
        auth_providers = list(self.auth_providers.values())
        external_providers = [p for p in auth_providers if p.is_external]
        local_providers = [p for p in auth_providers if not p.is_external]
        if any(p.settings.get('default') for p in external_providers):
            raise ValueError('The default provider cannot be external')
        if all(p.is_external for p in auth_providers):
            return
        default_providers = [p for p in auth_providers if p.settings.get('default')]
        if len(default_providers) > 1:
            raise ValueError('There can only be one default auth provider')
        elif not default_providers:
            if len(local_providers) == 1:
                local_providers[0].settings['default'] = True
            else:
                raise ValueError('There is no default auth provider')

    def handle_auth_error(self, exc, redirect_to_login=False):
        if isinstance(exc, NoSuchUser):
            if not getattr(exc, '_indico_no_rate_limit', False):
                login_rate_limiter.hit()
                login_rate_limiter_user.hit(exc.identifier)
            logger.warning('Invalid credentials (ip=%s, provider=%s): %s',
                           request.remote_addr, exc.provider.name if exc.provider else None, exc)
        elif isinstance(exc, InvalidCredentials):
            login_rate_limiter.hit()
            login_rate_limiter_user.hit(exc.identifier)
            logger.warning('Invalid credentials (ip=%s, provider=%s, identifier=%s): %s',
                           request.remote_addr, exc.provider.name if exc.provider else None, exc.identifier, exc)
        else:
            exc_str = str(exc)
            fn = logger.error
            if exc_str.startswith('mismatching_state:'):
                fn = logger.debug
            fn('Authentication via %s failed: %s (%r)', exc.provider.name if exc.provider else None, exc_str,
               exc.details)
        return super().handle_auth_error(exc, redirect_to_login=redirect_to_login)

    def handle_login_form(self, provider, data):
        signal_res = signals.users.check_login_data.send(type(provider), provider=provider, data=data)
        if errors := values_from_signal(signal_res, as_list=True):
            identifier = provider.get_identifier(data)
            self.handle_auth_error(InvalidCredentials(errors[0], provider=provider, identifier=identifier))
            return
        return super().handle_login_form(provider, data)


def get_exceeded_login_rate_limiter(identifier=None):
    """Return the rate limiter that has been exceeded for login."""
    if login_rate_limiter.test():
        return None
    elif not login_rate_limiter_user.limits or not identifier:
        return login_rate_limiter
    elif login_rate_limiter_user.test(identifier):
        return None
    else:
        return login_rate_limiter_user


def get_exceeded_signup_rate_limiter(email=None):
    """Return the rate limiter that has been exceeded for signup."""
    if signup_rate_limiter.test():
        return None
    elif not signup_rate_limiter_email.limits or not email:
        return signup_rate_limiter
    elif signup_rate_limiter_email.test(email):
        return None
    else:
        return signup_rate_limiter_email


multipass = IndicoMultipass()
