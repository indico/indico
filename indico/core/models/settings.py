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

from functools import wraps

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db.sqlalchemy import db
from indico.util.string import return_ascii


_default = object()


class SettingsBase(object):
    __tablename__ = 'settings'

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    module = db.Column(
        db.String,
        index=True,
        nullable=False
    )
    name = db.Column(
        db.String,
        index=True,
        nullable=False
    )
    value = db.Column(
        JSON,
        nullable=False
    )

    @classmethod
    def get_setting(cls, module, name, **kwargs):
        return cls.find_first(module=module, name=name, **kwargs)

    @classmethod
    def get_all_settings(cls, module, **kwargs):
        return {s.name: s for s in cls.find(module=module, **kwargs)}

    @classmethod
    def get_all(cls, module, **kwargs):
        return {s.name: s.value for s in cls.find(module=module, **kwargs)}

    @classmethod
    def get(cls, module, name, default=None, **kwargs):
        setting = cls.get_setting(module, name, **kwargs)
        if setting is None:
            return default
        return setting.value

    @classmethod
    def set(cls, module, name, value, **kwargs):
        setting = cls.get_setting(module, name, **kwargs)
        if setting is None:
            setting = cls(module=module, name=name, **kwargs)
            db.session.add(setting)
        setting.value = value
        db.session.flush()

    @classmethod
    def set_multi(cls, module, items, **kwargs):
        existing = cls.get_all_settings(module, **kwargs)
        for name in items.viewkeys() - existing.viewkeys():
            setting = cls(module=module, name=name, value=items[name], **kwargs)
            db.session.add(setting)
        for name in items.viewkeys() & existing.viewkeys():
            existing[name].value = items[name]
        db.session.flush()

    @classmethod
    def delete(cls, module, *names, **kwargs):
        if not names:
            return
        cls.find(cls.name.in_(names), cls.module == module, **kwargs).delete(synchronize_session='fetch')
        db.session.flush()

    @classmethod
    def delete_all(cls, module, **kwargs):
        cls.find(module=module, **kwargs).delete()
        db.session.flush()


class Setting(SettingsBase, db.Model):
    __table_args__ = (db.Index('ix_settings_module_key', 'module', 'name'),
                      db.UniqueConstraint('module', 'name'),
                      db.CheckConstraint('module = lower(module)'),
                      db.CheckConstraint('name = lower(name)'),
                      {'schema': 'indico'})

    @return_ascii
    def __repr__(self):
        return '<Setting({}, {}, {!r})>'.format(self.module, self.name, self.value)


class EventSetting(SettingsBase, db.Model):
    __table_args__ = (db.Index('ix_settings_event_id_module_name', 'event_id', 'module', 'name'),
                      db.Index('ix_settings_event_id_module', 'event_id', 'module'),
                      db.UniqueConstraint('event_id', 'module', 'name'),
                      db.CheckConstraint('module = lower(module)'),
                      db.CheckConstraint('name = lower(name)'),
                      {'schema': 'events'})

    event_id = db.Column(
        db.String,
        index=True,
        nullable=False
    )

    @return_ascii
    def __repr__(self):
        return '<EventSetting({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.value)

    @classmethod
    def delete_event(cls, event_id):
        cls.find(event_id=event_id).delete(synchronize_session='fetch')


def _get_all(cls, proxy, no_defaults, **kwargs):
    """Helper function for SettingsProxy.get_all"""
    if no_defaults:
        return cls.get_all(proxy.module, **kwargs)
    settings = dict(proxy.defaults)
    settings.update(cls.get_all(proxy.module, **kwargs))
    return settings


def _get(cls, proxy, name, default, **kwargs):
    """Helper function for SettingsProxy.get"""
    setting = cls.get(proxy.module, name, default, **kwargs)
    if setting is _default:
        return proxy.defaults.get(name)
    return setting


class SettingsProxyBase(object):
    """Base proxy class to access settings for a certain module

    :param module: the module to use
    :param defaults: default values to use if there's nothing in the db
    :param strict: in strict mode any key that's not in defaults is illegal
                   and triggers a `ValueError`
    """

    def __init__(self, module, defaults, strict=True):
        self.module = module
        self.defaults = defaults or {}
        self.strict = strict
        if strict and not defaults:
            raise ValueError('cannot use strict mode with no defaults')

    def _check_strict(self, name):
        if self.strict and name not in self.defaults:
            raise ValueError('invalid setting: {}.{}'.format(self.module, name))


class SettingsProxy(SettingsProxyBase):
    """Proxy class to access settings for a certain module"""

    def get_all(self, no_defaults=False):
        """Retrieves all settings

        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return _get_all(Setting, self, no_defaults)

    def get(self, name, default=_default):
        """Retrieves the value of a single setting.

        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_strict(name)
        return _get(Setting, self, name, default)

    def set(self, name, value):
        """Sets a single setting.

        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_strict(name)
        return Setting.set(self.module, name, value)

    def set_multi(self, items):
        """Sets multiple settings at once.

        :param items: Dict containing the new settings
        """
        for name in items:
            self._check_strict(name)
        return Setting.set_multi(self.module, items)

    def delete(self, *names):
        """Deletes settings.

        :param names: One or more names of settings to delete
        """
        for name in names:
            self._check_strict(name)
        return Setting.delete(self.module, names)

    def delete_all(self):
        """Deletes all settings."""
        return Setting.delete_all(self.module)

    @return_ascii
    def __repr__(self):
        return u'<SettingsProxy({})>'.format(self.module)


def event_or_id(f):
    @wraps(f)
    def wrapper(self, event, *args, **kwargs):
        from MaKaC.conference import Conference
        if isinstance(event, Conference):
            event = event.id
        return f(self, unicode(event), *args, **kwargs)

    return wrapper


class EventSettingsProxy(SettingsProxyBase):
    """Proxy class to access event-specific settings for a certain module"""

    @event_or_id
    def get_all(self, event, no_defaults=False):
        """Retrieves all settings

        :param event: Event (or its ID)
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return _get_all(EventSetting, self, no_defaults, event_id=event)

    @event_or_id
    def get(self, event, name, default=_default):
        """Retrieves the value of a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_strict(name)
        return _get(EventSetting, self, name, default, event_id=event)

    @event_or_id
    def set(self, event, name, value):
        """Sets a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_strict(name)
        return EventSetting.set(self.module, name, value, event_id=event)

    @event_or_id
    def set_multi(self, event, items):
        """Sets multiple settings at once.

        :param event: Event (or its ID)
        :param items: Dict containing the new settings
        """
        for name in items:
            self._check_strict(name)
        return EventSetting.set_multi(self.module, items, event_id=event)

    @event_or_id
    def delete(self, event, *names):
        """Deletes settings.

        :param event: Event (or its ID)
        :param names: One or more names of settings to delete
        """
        for name in names:
            self._check_strict(name)
        return EventSetting.delete(self.module, names, event_id=event)

    @event_or_id
    def delete_all(self, event):
        """Deletes all settings.

        :param event: Event (or its ID)
        """
        return EventSetting.delete_all(self.module, event_id=event)

    @return_ascii
    def __repr__(self):
        return '<EventSettingsProxy({})>'.format(self.module)
