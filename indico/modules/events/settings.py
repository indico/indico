# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from functools import wraps

import yaml

from indico.core.settings import SettingsProxyBase, ACLProxyBase
from indico.core.settings.util import get_setting, get_all_settings, get_setting_acl
from indico.modules.events import Event
from indico.modules.events.models.settings import EventSettingPrincipal, EventSetting
from indico.util.caching import memoize
from indico.util.user import iter_acl


def event_or_id(f):
    @wraps(f)
    def wrapper(self, event, *args, **kwargs):
        from MaKaC.conference import Conference
        if isinstance(event, (Conference, Event)):
            event = event.id
        return f(self, int(event), *args, **kwargs)

    return wrapper


class EventACLProxy(ACLProxyBase):
    """Proxy class for event-specific ACL settings"""

    @event_or_id
    def get(self, event, name):
        """Retrieves an ACL setting

        :param event: Event (or its ID)
        :param name: Setting name
        """
        self._check_name(name)
        return get_setting_acl(EventSettingPrincipal, self, name, self._cache, event_id=event)

    @event_or_id
    def set(self, event, name, acl):
        """Replaces an ACL with a new one

        :param event: Event (or its ID)
        :param name: Setting name
        :param acl: A set containing principals (users/groups)
        """
        self._check_name(name)
        EventSettingPrincipal.set_acl(self.module, name, acl, event_id=event)
        self._flush_cache()

    @event_or_id
    def contains_user(self, event, name, user):
        """Checks if a user is in an ACL.

        To pass this check, the user can either be in the ACL itself
        or in a group in the ACL.

        :param event: Event (or its ID)
        :param name: Setting name
        :param user: A :class:`.User`
        """
        return any(user in principal for principal in iter_acl(self.get(event, name)))

    @event_or_id
    def add_principal(self, event, name, principal):
        """Adds a principal to an ACL

        :param event: Event (or its ID)
        :param name: Setting name
        :param principal: A :class:`.User` or a :class:`.GroupProxy`
        """
        self._check_name(name)
        EventSettingPrincipal.add_principal(self.module, name, principal, event_id=event)
        self._flush_cache()

    @event_or_id
    def remove_principal(self, event, name, principal):
        """Removes a principal from an ACL

        :param event: Event (or its ID)
        :param name: Setting name
        :param principal: A :class:`.User` or a :class:`.GroupProxy`
        """
        self._check_name(name)
        EventSettingPrincipal.remove_principal(self.module, name, principal, event_id=event)
        self._flush_cache()

    def merge_users(self, target, source):
        """Replaces all ACL user entries for `source` with `target`"""
        EventSettingPrincipal.merge_users(self.module, target, source)
        self._flush_cache()


class EventSettingsProxy(SettingsProxyBase):
    """Proxy class to access event-specific settings for a certain module"""

    acl_proxy_class = EventACLProxy

    @property
    def query(self):
        """Returns a query object filtering by the proxy's module."""
        return EventSetting.find(module=self.module)

    @event_or_id
    def get_all(self, event, no_defaults=False):
        """Retrieves all settings

        :param event: Event (or its ID)
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return get_all_settings(EventSetting, EventSettingPrincipal, self, no_defaults, event_id=event)

    @event_or_id
    def get(self, event, name, default=SettingsProxyBase.default_sentinel):
        """Retrieves the value of a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return get_setting(EventSetting, self, name, default, self._cache, event_id=event)

    @event_or_id
    def set(self, event, name, value):
        """Sets a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_name(name)
        EventSetting.set(self.module, name, value, event_id=event)
        self._flush_cache()

    @event_or_id
    def set_multi(self, event, items):
        """Sets multiple settings at once.

        :param event: Event (or its ID)
        :param items: Dict containing the new settings
        """
        self._split_call(items,
                         lambda x: EventSetting.set_multi(self.module, x, event_id=event),
                         lambda x: EventSettingPrincipal.set_acl_multi(self.module, x, event_id=event))
        self._flush_cache()

    @event_or_id
    def delete(self, event, *names):
        """Deletes settings.

        :param event: Event (or its ID)
        :param names: One or more names of settings to delete
        """
        self._split_call(names,
                         lambda name: EventSetting.delete(self.module, *name, event_id=event),
                         lambda name: EventSettingPrincipal.delete(self.module, *name, event_id=event))
        self._flush_cache()

    @event_or_id
    def delete_all(self, event):
        """Deletes all settings.

        :param event: Event (or its ID)
        """
        EventSetting.delete_all(self.module, event_id=event)
        EventSettingPrincipal.delete_all(self.module, event_id=event)
        self._flush_cache()


class ThemeSettingsProxy(object):

    def __init__(self, settings_file):
        settings = self._load_settings(settings_file)
        self.themes = settings['definitions']
        self.defaults = settings['defaults']

    @staticmethod
    @memoize
    def _load_settings(settings_file):
        with open(settings_file) as f:
            return yaml.load(f)

    @memoize
    def get_themes_for(self, event_type):
        return {theme_id: theme_data for theme_id, theme_data in self.themes.viewitems()
                if event_type in theme_data['event_types']}

    @property
    @memoize
    def xml_themes(self):
        return {theme_id: theme_data for theme_id, theme_data in self.themes.viewitems()
                if theme_data.get('is_xml')}
