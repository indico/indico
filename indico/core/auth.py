# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from warnings import warn

from flask import current_app, request
from flask_multipass import InvalidCredentials, Multipass, NoSuchUser
from flask_multipass.providers.oauth import OAuthInvalidSessionState

from indico.core.logger import Logger


logger = Logger.get('auth')


class IndicoMultipass(Multipass):
    @property
    def default_local_auth_provider(self):
        """The default form-based auth provider."""
        return next((p for p in self.auth_providers.itervalues() if not p.is_external and p.settings.get('default')),
                    None)

    @property
    def default_group_provider(self):
        """The default group provider.

        This is an identity provider which supports groups and which
        is used in places where only a group name can be specified,
        such as legacy data or room ACLs.
        """
        return next((p for p in self.identity_providers.itervalues()
                     if p.supports_groups and p.settings.get('default_group_provider')), None)

    @property
    def sync_provider(self):
        """The synchronization provider.

        This is the identity provider used to sync user data.
        """
        return next((p for p in self.identity_providers.itervalues()
                     if p.supports_refresh and p.settings.get('synced_fields')), None)

    @property
    def synced_fields(self):
        """The keys to be synchronized

        This is the set of keys to be synced to user data.
        The ``email`` can never be synchronized.
        """
        provider = self.sync_provider
        if provider is None:
            return set()
        synced_fields = set(provider.settings.get('synced_fields'))
        synced_fields &= set(current_app.config['MULTIPASS_IDENTITY_INFO_KEYS'])
        synced_fields.discard('email')
        return synced_fields

    def init_app(self, app):
        super(IndicoMultipass, self).init_app(app)
        with app.app_context():
            self._check_default_provider()

    def _check_default_provider(self):
        # Warn if there is no default group provider
        if not self.default_group_provider and any(p.supports_groups for p in self.identity_providers.itervalues()):
            warn('There is no default group provider but you have providers with group support. '
                 'This will break legacy ACLs referencing external groups and room ACLs will use local group IDs.')
        # Ensure that there is maximum one sync provider
        sync_providers = [p for p in self.identity_providers.itervalues()
                          if p.supports_refresh and p.settings.get('synced_fields')]
        if len(sync_providers) > 1:
            raise ValueError('There can only be one sync provider.')
        # Ensure that there is exactly one form-based default auth provider
        auth_providers = self.auth_providers.values()
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
            logger.warning('Invalid credentials (ip=%s, provider=%s): %s',
                           request.remote_addr, exc.provider.name if exc.provider else None, exc)
        else:
            fn = logger.debug if isinstance(exc, OAuthInvalidSessionState) else logger.error
            fn('Authentication via %s failed: %s (%r)', exc.provider.name if exc.provider else None, exc, exc.details)
        return super(IndicoMultipass, self).handle_auth_error(exc, redirect_to_login=redirect_to_login)


multipass = IndicoMultipass()
