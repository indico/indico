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

from warnings import warn

from flask_multipass import Multipass


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

    def init_app(self, app):
        super(IndicoMultipass, self).init_app(app)
        with app.app_context():
            self._check_default_provider()

    def _check_default_provider(self):
        # Warn if there is no default group provider
        if not self.default_group_provider and any(p.supports_groups for p in self.identity_providers.itervalues()):
            warn('There is no default group provider but you have providers with group support. '
                 'This will break legacy ACLs referencing external groups and room ACLs will use local group IDs.')
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


multipass = IndicoMultipass()
