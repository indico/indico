# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from datetime import timedelta
from functools import wraps
from pathlib import Path

import yaml
from flask.helpers import get_root_path

from indico.core import signals
from indico.core.settings import ACLProxyBase, SettingProperty, SettingsProxyBase
from indico.core.settings.converters import DatetimeConverter, TimedeltaConverter
from indico.core.settings.proxy import SettingsProxy
from indico.core.settings.util import get_all_settings, get_setting, get_setting_acl
from indico.modules.events.models.settings import EventSetting, EventSettingPrincipal
from indico.util.caching import memoize
from indico.util.signals import values_from_signal
from indico.util.user import iter_acl


def event_or_id(f):
    @wraps(f)
    def wrapper(self, event, *args, **kwargs):
        from indico.modules.events import Event
        if isinstance(event, Event):
            event = event.id
        return f(self, int(event), *args, **kwargs)

    return wrapper


class EventACLProxy(ACLProxyBase):
    """Proxy class for event-specific ACL settings."""

    @event_or_id
    def get(self, event, name):
        """Retrieve an ACL setting.

        :param event: Event (or its ID)
        :param name: Setting name
        """
        self._check_name(name)
        return get_setting_acl(EventSettingPrincipal, self, name, self._cache, event_id=event)

    @event_or_id
    def set(self, event, name, acl):
        """Replace an ACL with a new one.

        :param event: Event (or its ID)
        :param name: Setting name
        :param acl: A set containing principals (users/groups)
        """
        self._check_name(name)
        EventSettingPrincipal.set_acl(self.module, name, acl, event_id=event)
        self._flush_cache()

    @event_or_id
    def contains_user(self, event, name, user):
        """Check if a user is in an ACL.

        To pass this check, the user can either be in the ACL itself
        or in a group in the ACL.

        :param event: Event (or its ID)
        :param name: Setting name
        :param user: A :class:`.User`
        """
        # we need to use the original `get` method in case this acl proxy is bound to an event,
        # in which case calling `self.get()` with an explicitly provided event argument would fail
        acl_entries = EventACLProxy.get(self, event, name)
        return any(user in principal for principal in iter_acl(acl_entries))

    @event_or_id
    def add_principal(self, event, name, principal):
        """Add a principal to an ACL.

        :param event: Event (or its ID)
        :param name: Setting name
        :param principal: A :class:`.User` or a :class:`.GroupProxy`
        """
        self._check_name(name)
        EventSettingPrincipal.add_principal(self.module, name, principal, event_id=event)
        self._flush_cache()

    @event_or_id
    def remove_principal(self, event, name, principal):
        """Remove a principal from an ACL.

        :param event: Event (or its ID)
        :param name: Setting name
        :param principal: A :class:`.User` or a :class:`.GroupProxy`
        """
        self._check_name(name)
        EventSettingPrincipal.remove_principal(self.module, name, principal, event_id=event)
        self._flush_cache()

    def merge_users(self, target, source):
        """Replace all ACL user entries for `source` with `target`."""
        EventSettingPrincipal.merge_users(self.module, target, source)
        self._flush_cache()


class EventSettingsProxy(SettingsProxyBase):
    """Proxy class to access event-specific settings for a certain module."""

    acl_proxy_class = EventACLProxy

    @property
    def query(self):
        """Return a query object filtering by the proxy's module."""
        return EventSetting.query.filter_by(module=self.module)

    @event_or_id
    def get_all(self, event, no_defaults=False):
        """Retrieve all settings.

        :param event: Event (or its ID)
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return get_all_settings(EventSetting, EventSettingPrincipal, self, no_defaults, event_id=event)

    @event_or_id
    def get(self, event, name, default=SettingsProxyBase.default_sentinel):
        """Retrieve the value of a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return get_setting(EventSetting, self, name, default, self._cache, event_id=event)

    @event_or_id
    def set(self, event, name, value):
        """Set a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_name(name)
        EventSetting.set(self.module, name, self._convert_from_python(name, value), event_id=event)
        self._flush_cache()

    @event_or_id
    def set_multi(self, event, items):
        """Set multiple settings at once.

        :param event: Event (or its ID)
        :param items: Dict containing the new settings
        """
        items = {k: self._convert_from_python(k, v) for k, v in items.items()}
        self._split_call(items,
                         lambda x: EventSetting.set_multi(self.module, x, event_id=event),
                         lambda x: EventSettingPrincipal.set_acl_multi(self.module, x, event_id=event))
        self._flush_cache()

    @event_or_id
    def delete(self, event, *names):
        """Delete settings.

        :param event: Event (or its ID)
        :param names: One or more names of settings to delete
        """
        self._split_call(names,
                         lambda name: EventSetting.delete(self.module, *name, event_id=event),
                         lambda name: EventSettingPrincipal.delete(self.module, *name, event_id=event))
        self._flush_cache()

    @event_or_id
    def delete_all(self, event):
        """Delete all settings.

        :param event: Event (or its ID)
        """
        EventSetting.delete_all(self.module, event_id=event)
        EventSettingPrincipal.delete_all(self.module, event_id=event)
        self._flush_cache()


class EventSettingProperty(SettingProperty):
    attr = 'event'


class ThemeSettingsProxy:
    @property
    @memoize
    def settings(self):
        core_data = Path(get_root_path('indico'), 'modules', 'events', 'themes.yaml').read_text()
        core_settings = yaml.safe_load(core_data)
        # YAML doesn't give us access to anchors so we need to include the base yaml.
        # Since duplicate keys are invalid (and may start failing in the future) we
        # rename them - this also makes it easy to throw them away after parsing the
        # file provided by a plugin.
        core_data = re.sub(r'^(\S+:)$', r'__core_\1', core_data, flags=re.MULTILINE)
        for plugin, path in values_from_signal(signals.plugin.get_event_themes_files.send(), return_plugins=True):
            data = Path(path).read_text()
            settings = {k: v
                        for k, v in yaml.safe_load(core_data + '\n' + data).items()
                        if not k.startswith('__core_')}
            # We assume there's no more than one theme plugin that provides defaults.
            # If that's not the case the last one "wins". We could reject this but it
            # is quite unlikely that people have multiple theme plugins in the first
            # place, even more so theme plugins that specify defaults.
            core_settings['defaults'].update(settings.get('defaults', {}))
            # Same for definitions - we assume plugin authors are responsible enough
            # to avoid using definition names that are likely to cause collisions.
            # Either way, if someone does this on purpose chances are good they want
            # to override a default style so let them do so...
            for name, definition in settings.get('definitions', {}).items():
                definition['plugin'] = plugin
                definition.setdefault('user_visible', False)
                core_settings['definitions'][name] = definition
        return core_settings

    @property
    @memoize
    def themes(self):
        return self.settings['definitions']

    @property
    @memoize
    def defaults(self):
        return self.settings['defaults']

    @memoize
    def get_themes_for(self, event_type):
        return {theme_id: theme_data for theme_id, theme_data in self.themes.items()
                if event_type in theme_data['event_types']}


event_core_settings = EventSettingsProxy('core', {
    'start_dt_override': None,
    'end_dt_override': None,
    'organizer_info': '',
    'additional_info': '',
    'public_regform_access': False
}, converters={
    'start_dt_override': DatetimeConverter,
    'end_dt_override': DatetimeConverter
})

event_contact_settings = EventSettingsProxy('contact', {
    'title': 'Contact',
    'emails': [],
    'phones': []
})

event_language_settings = EventSettingsProxy('language', {
    'supported_locales': [],
    'default_locale': '',
    'enforce_locale': False,
})

unlisted_events_settings = SettingsProxy('unlisted_events', {
    'enabled': False,
    'restricted': False,
}, acls={
    'authorized_creators'
})

autolinker_settings = SettingsProxy('autolinker', {
    'rules': []
})

data_retention_settings = SettingsProxy('data_retention', {
    'minimum_data_retention': timedelta(days=7),
    'maximum_data_retention': None,
}, converters={
    'minimum_data_retention': TimedeltaConverter,
    'maximum_data_retention': TimedeltaConverter
})
