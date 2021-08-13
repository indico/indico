# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import functools

from flask import current_app, request
from flask_multipass import InvalidCredentials, Multipass, NoSuchUser
from werkzeug.local import LocalProxy

from indico.core.config import config
from indico.core.limiter import make_rate_limiter
from indico.core.logger import Logger


logger = Logger.get('auth')
login_rate_limiter = LocalProxy(functools.cache(lambda: make_rate_limiter('login', config.FAILED_LOGIN_RATE_LIMIT)))


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
        if isinstance(exc, (NoSuchUser, InvalidCredentials)):
            login_rate_limiter.hit()
            logger.warning('Invalid credentials (ip=%s, provider=%s): %s',
                           request.remote_addr, exc.provider.name if exc.provider else None, exc)
        else:
            exc_str = str(exc)
            fn = logger.error
            if exc_str.startswith('mismatching_state:'):
                fn = logger.debug
            fn('Authentication via %s failed: %s (%r)', exc.provider.name if exc.provider else None, exc_str,
               exc.details)
        return super().handle_auth_error(exc, redirect_to_login=redirect_to_login)


multipass = IndicoMultipass()
