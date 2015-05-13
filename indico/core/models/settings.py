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

from collections import defaultdict
from functools import wraps, partial, update_wrapper

from enum import Enum
from flask import g, has_request_context
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.util.models import merge_table_args
from indico.core.models.principals import PrincipalMixin, PrincipalType
from indico.util.decorators import classproperty
from indico.util.string import return_ascii
from indico.util.user import iter_acl


_default = object()
_not_in_db = object()


def _coerce_value(value):
    if isinstance(value, Enum):
        return value.value
    return value


class SettingsBase(object):
    """Base class for any kind of setting tables"""

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

    @classproperty
    @staticmethod
    def __table_args__():
        # not using declared_attr here since reading such an attribute manually from a non-model triggers a warning
        return (db.CheckConstraint('module = lower(module)', 'lowercase_module'),
                db.CheckConstraint('name = lower(name)', 'lowercase_name'))

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


class JSONSettingsBase(SettingsBase):
    """Base class for setting tables with a JSON value"""

    __tablename__ = 'settings'

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
        setting.value = _coerce_value(value)
        db.session.flush()

    @classmethod
    def set_multi(cls, module, items, **kwargs):
        existing = cls.get_all_settings(module, **kwargs)
        for name in items.viewkeys() - existing.viewkeys():
            setting = cls(module=module, name=name, value=_coerce_value(items[name]), **kwargs)
            db.session.add(setting)
        for name in items.viewkeys() & existing.viewkeys():
            existing[name].value = _coerce_value(items[name])
        db.session.flush()


class PrincipalSettingsBase(PrincipalMixin, SettingsBase):
    """Base class for principal setting tables"""

    __tablename__ = 'settings_principals'
    # Additional columns used to identitfy a setting (e.g. user/event id)
    extra_key_cols = ()

    @classmethod
    def get_all_acls(cls, module, **kwargs):
        rv = defaultdict(set)
        for setting in cls.find(module=module, **kwargs):
            rv[setting.name].add(setting.principal)
        return rv

    @classmethod
    def get_acl(cls, module, name, raw=False, **kwargs):
        return {x if raw else x.principal for x in cls.find(module=module, name=name, **kwargs)}

    @classmethod
    def set_acl(cls, module, name, acl, **kwargs):
        existing = cls.get_acl(module, name, raw=True, **kwargs)
        existing_principals = {x.principal for x in existing}
        for principal in acl - existing_principals:
            db.session.add(cls(module=module, name=name, principal=principal, **kwargs))
        for setting in existing:
            if setting.principal not in acl:
                db.session.delete(setting)
        db.session.flush()

    @classmethod
    def set_acl_multi(cls, module, items, **kwargs):
        for name, acl in items.iteritems():
            cls.set_acl(module, name, acl, **kwargs)

    @classmethod
    def is_in_acl(cls, module, name, user, **kwargs):
        # TODO: This could be improved to actually query using the user
        # and his groups instead of getting the whole ACL!
        return any(user in principal for principal in iter_acl(cls.get_acl(module, name, **kwargs)))

    @classmethod
    def add_principal(cls, module, name, principal, **kwargs):
        if principal not in cls.get_acl(module, name):
            db.session.add(cls(module=module, name=name, principal=principal, **kwargs))
            db.session.flush()

    @classmethod
    def remove_principal(cls, module, name, principal, **kwargs):
        for setting in cls.get_acl(module, name, raw=True, **kwargs):
            if setting.principal == principal:
                db.session.delete(setting)
                db.session.flush()

    @classmethod
    def merge_users(cls, module, target, source):
        settings = [(setting.module, setting.name, {x: getattr(setting, x) for x in cls.extra_key_cols})
                    for setting in cls.find(module=module, type=PrincipalType.user, user=source)]
        for module, name, extra in settings:
            cls.remove_principal(module, name, source, **extra)
            cls.add_principal(module, name, target, **extra)
        db.session.flush()


class CoreSettingsMixin(object):
    @classproperty
    @staticmethod
    def __table_args__():
        # not using declared_attr here since reading such an attribute manually from a non-model triggers a warning
        return (db.Index(None, 'module', 'name'),
                {'schema': 'indico'})


class Setting(JSONSettingsBase, CoreSettingsMixin, db.Model):
    @declared_attr
    def __table_args__(cls):
        local_args = db.UniqueConstraint('module', 'name'),
        return merge_table_args(JSONSettingsBase, CoreSettingsMixin, local_args)

    @return_ascii
    def __repr__(self):
        return '<Setting({}, {}, {!r})>'.format(self.module, self.name, self.value)


class SettingPrincipal(PrincipalSettingsBase, CoreSettingsMixin, db.Model):
    principal_backref_name = 'in_settings_acls'

    @declared_attr
    def __table_args__(cls):
        return merge_table_args(PrincipalSettingsBase, CoreSettingsMixin)

    @return_ascii
    def __repr__(self):
        return '<SettingPrincipal({}, {}, {!r})>'.format(self.module, self.name, self.principal)


class EventSettingsMixin(object):
    @classproperty
    @staticmethod
    def __table_args__():
        # not using declared_attr here since reading such an attribute manually from a non-model triggers a warning
        return (db.Index(None, 'event_id', 'module', 'name'),
                db.Index(None, 'event_id', 'module'),
                {'schema': 'events'})

    event_id = db.Column(
        db.String,
        index=True,
        nullable=False
    )

    @classmethod
    def delete_event(cls, event_id):
        cls.find(event_id=event_id).delete(synchronize_session='fetch')


class EventSetting(JSONSettingsBase, EventSettingsMixin, db.Model):
    @declared_attr
    def __table_args__(cls):
        local_args = db.UniqueConstraint('event_id', 'module', 'name'),
        return merge_table_args(EventSettingsMixin, local_args)

    @return_ascii
    def __repr__(self):
        return '<EventSetting({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.value)


class EventSettingPrincipal(PrincipalSettingsBase, EventSettingsMixin, db.Model):
    principal_backref_name = 'in_event_settings_acls'
    extra_key_cols = ('event_id',)

    @declared_attr
    def __table_args__(cls):
        return merge_table_args(PrincipalSettingsBase, EventSettingsMixin)

    @return_ascii
    def __repr__(self):
        return '<EventSettingPrincipal({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.principal)


def _get_all(cls, acl_cls, proxy, no_defaults, **kwargs):
    """Helper function for SettingsProxy.get_all"""
    if no_defaults:
        rv = cls.get_all(proxy.module, **kwargs)
        if acl_cls:
            rv.update(acl_cls.get_all_acls(proxy.module, **kwargs))
        return rv
    settings = dict(proxy.defaults)
    if acl_cls:
        settings.update({name: set() for name in proxy.acl_names})
    settings.update(cls.get_all(proxy.module, **kwargs))
    if acl_cls:
        settings.update(acl_cls.get_all_acls(proxy.module, **kwargs))
    return settings


def _get(cls, proxy, name, default, cache, **kwargs):
    """Helper function for SettingsProxy.get"""
    cache_key = proxy.module, name, frozenset(kwargs.viewitems())
    try:
        return cache[cache_key]
    except KeyError:
        setting = cls.get(proxy.module, name, _not_in_db, **kwargs)
        if setting is _not_in_db:
            # we never cache a default value - it would have to be included in the cache key and we
            # cannot do that because of mutable values (lists/dicts). of course we could convert
            # them to tuples and frozen sets and then do include them in the key, but since most
            # settings are actually set in the db that's overkill.
            return proxy.defaults.get(name) if default is _default else default
        else:
            cache[cache_key] = setting
            return setting


def _get_acl(cls, proxy, name, cache, cached_only=False, **kwargs):
    """Helper function for SettingsProxy.get_acl"""
    cache_key = proxy.module, name, frozenset(kwargs.viewitems())
    try:
        return cache[cache_key]
    except KeyError:
        if cached_only:
            return None
        cache[cache_key] = acl = cls.get_acl(proxy.module, name, **kwargs)
        return acl


class ACLProxyBase(object):
    """Base Proxy class for ACL settings"""

    def __init__(self, proxy):
        self.proxy = proxy
        self.module = self.proxy.module

    @property
    def _cache(self):
        return self.proxy._cache

    def _check_name(self, name):
        self.proxy._check_name(name, True)

    def _flush_cache(self):
        self.proxy._flush_cache()


class SettingsProxyBase(object):
    """Base proxy class to access settings for a certain module

    :param module: the module to use
    :param defaults: default values to use if there's nothing in the db
    :param strict: in strict mode any key that's not in `defaults` or
                   `acls` is illegal and triggers a `ValueError`
    :param acls: setting names which are referencing ACLs in a
                 separate table
    """

    acl_proxy_class = None

    def __init__(self, module, defaults=None, strict=True, acls=None):
        self.module = module
        self.defaults = defaults or {}
        self.strict = strict
        self.acl_names = set(acls or ())
        self.acls = self.acl_proxy_class(self) if self.acl_proxy_class else None
        self._bound_args = None
        if strict and not defaults and not acls:
            raise ValueError('cannot use strict mode with no defaults')
        if acls and not self.acl_proxy_class:
            raise ValueError('this proxy does not support acl settings')
        if acls and self.acl_names & self.defaults.viewkeys():
            raise ValueError('acl settings cannot have a default value')

    @return_ascii
    def __repr__(self):
        if self._bound_args:
            return '<{}({}, {})>'.format(type(self).__name__, self.module, self._bound_args)
        else:
            return '<{}({})>'.format(type(self).__name__, self.module)

    def bind(self, *args):
        """Returns a version of this proxy that is bound to some arguments.

        This is useful for specialized versions of the proxy such as
        EventSettingsProxy where one might want to provide an easy-to-use
        version that does not require the event to be specified in each
        method.

        :param args: The positional argument that are prepended to each
                     function call.
        """

        self_type = type(self)
        bound = self_type(self.module, self.defaults, self.strict)
        bound._bound_args = args

        for name in dir(self_type):
            if name[0] == '_' or name == 'bind' or not callable(getattr(self_type, name)):
                continue
            func = getattr(bound, name)
            func = update_wrapper(partial(func, *args), func)
            setattr(bound, name, func)
        return bound

    def _check_name(self, name, acl=False):
        strict = self.strict or acl  # acl settings always use strict mode
        collection = self.acl_names if acl else self.defaults
        if strict and name not in collection:
            raise ValueError('invalid setting: {}.{}'.format(self.module, name))

    def _split_names(self, names):
        # Returns a ``(regular_names, acl_names)`` tuple
        return {x for x in names if x not in self.acl_names}, {x for x in names if x in self.acl_names}

    def _split_call(self, value, regular_func, acl_func):
        # Util to call different functions depending if the name is an acl or regular setting
        regular_names, acl_names = self._split_names(value)
        for name in regular_names:
            self._check_name(name)
        for name in acl_names:
            self._check_name(name, True)
        if isinstance(value, dict):
            regular_items = {name: value[name] for name in regular_names}
            acl_items = {name: value[name] for name in acl_names}
            if regular_items:
                regular_func(regular_items)
            if acl_items:
                acl_func(acl_items)
        else:
            if regular_names:
                regular_func(regular_names)
            if acl_names:
                acl_func(acl_names)

    def _flush_cache(self):
        if has_request_context():
            g.get('settings_cache', {}).clear()

    @property
    def _cache(self):
        if not has_request_context():
            return {}  # new dict everytime, this effectively disables the cache
        try:
            return g.settings_cache
        except AttributeError:
            g.settings_cache = rv = {}
            return rv


class ACLProxy(ACLProxyBase):
    """Proxy class for core ACL settings"""

    def get(self, name):
        """Retrieves an ACL setting

        :param name: Setting name
        """
        self._check_name(name)
        return _get_acl(SettingPrincipal, self, name, self._cache)

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
        self._check_name(name)
        # If we've already cached the whole ACL, check it directly
        acl = _get_acl(SettingPrincipal, self, name, self._cache, cached_only=True)
        if acl is not None:
            return any(user in principal for principal in iter_acl(acl))
        return SettingPrincipal.is_in_acl(self.module, name, user)

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
        return _get_all(Setting, SettingPrincipal, self, no_defaults)

    def get(self, name, default=_default):
        """Retrieves the value of a single setting.

        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return _get(Setting, self, name, default, self._cache)

    def set(self, name, value):
        """Sets a single setting.

        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_name(name)
        Setting.set(self.module, name, value)
        self._flush_cache()

    def set_multi(self, items):
        """Sets multiple settings at once.

        :param items: Dict containing the new settings
        """
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


def event_or_id(f):
    @wraps(f)
    def wrapper(self, event, *args, **kwargs):
        from MaKaC.conference import Conference
        if isinstance(event, Conference):
            event = event.id
        return f(self, unicode(event), *args, **kwargs)

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
        return _get_acl(EventSettingPrincipal, self, name, self._cache, event_id=event)

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
        self._check_name(name)
        return EventSettingPrincipal.is_in_acl(self.module, name, user, event_id=event)

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

    @event_or_id
    def get_all(self, event, no_defaults=False):
        """Retrieves all settings

        :param event: Event (or its ID)
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return _get_all(EventSetting, EventSettingPrincipal, self, no_defaults, event_id=event)

    @event_or_id
    def get(self, event, name, default=_default):
        """Retrieves the value of a single setting.

        :param event: Event (or its ID)
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return _get(EventSetting, self, name, default, self._cache, event_id=event)

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
