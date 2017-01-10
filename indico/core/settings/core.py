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

from indico.core.settings import SettingsProxyBase, ACLProxyBase
from indico.core.settings.util import get_setting, get_all_settings, get_setting_acl
from indico.core.settings.models.settings import Setting, SettingPrincipal


class ACLProxy(ACLProxyBase):
    """Proxy class for core ACL settings"""

    def get(self, name):
        """Retrieves an ACL setting

        :param name: Setting name
        """
        self._check_name(name)
        return get_setting_acl(SettingPrincipal, self, name, self._cache)

    def set(self, name, acl):
        """Replaces an ACL with a new one

        :param name: Setting name
        :param acl: A set containing principals (users/groups)
        """
        self._check_name(name)
        SettingPrincipal.set_acl(self.module, name, acl)
        self._flush_cache()

    def contains_user(self, name, user):
        """Checks if a user is in an ACL.

        To pass this check, the user can either be in the ACL itself
        or in a group in the ACL.

        :param name: Setting name
        :param user: A :class:`.User`
        """
        from indico.util.user import iter_acl
        return any(user in principal for principal in iter_acl(self.get(name)))

    def add_principal(self, name, principal):
        """Adds a principal to an ACL

        :param name: Setting name
        :param principal: A :class:`.User` or a :class:`.GroupProxy`
        """
        self._check_name(name)
        SettingPrincipal.add_principal(self.module, name, principal)
        self._flush_cache()

    def remove_principal(self, name, principal):
        """Removes a principal from an ACL

        :param name: Setting name
        :param principal: A :class:`.User` or a :class:`.GroupProxy`
        """
        self._check_name(name)
        SettingPrincipal.remove_principal(self.module, name, principal)
        self._flush_cache()

    def merge_users(self, target, source):
        """Replaces all ACL user entries for `source` with `target`"""
        SettingPrincipal.merge_users(self.module, target, source)
        self._flush_cache()


class SettingsProxy(SettingsProxyBase):
    """Proxy class to access settings for a certain module"""

    acl_proxy_class = ACLProxy

    def get_all(self, no_defaults=False):
        """Retrieves all settings, including ACLs

        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return get_all_settings(Setting, SettingPrincipal, self, no_defaults)

    def get(self, name, default=SettingsProxyBase.default_sentinel):
        """Retrieves the value of a single setting.

        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return get_setting(Setting, self, name, default, self._cache)

    def set(self, name, value):
        """Sets a single setting.

        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_name(name)
        Setting.set(self.module, name, self._convert_from_python(name, value))
        self._flush_cache()

    def set_multi(self, items):
        """Sets multiple settings at once.

        :param items: Dict containing the new settings
        """
        items = {k: self._convert_from_python(k, v) for k, v in items.iteritems()}
        self._split_call(items,
                         lambda x: Setting.set_multi(self.module, x),
                         lambda x: SettingPrincipal.set_acl_multi(self.module, x))
        self._flush_cache()

    def delete(self, *names):
        """Deletes settings.

        :param names: One or more names of settings to delete
        """
        self._split_call(names,
                         lambda name: Setting.delete(self.module, *name),
                         lambda name: SettingPrincipal.delete(self.module, *name))
        self._flush_cache()

    def delete_all(self):
        """Deletes all settings."""
        Setting.delete_all(self.module)
        SettingPrincipal.delete_all(self.module)
        self._flush_cache()
