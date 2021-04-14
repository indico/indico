# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict
from enum import Enum

from flask import g, has_request_context
from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalMixin, PrincipalType
from indico.util.decorators import strict_classproperty


def _coerce_value(value):
    if isinstance(value, Enum):
        return value.value
    return value


class SettingsBase:
    """Base class for any kind of setting tables."""

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

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (db.CheckConstraint('module = lower(module)', 'lowercase_module'),
                db.CheckConstraint('name = lower(name)', 'lowercase_name'))

    @classmethod
    def delete(cls, module, *names, **kwargs):
        if not names:
            return
        (cls.query
         .filter(cls.name.in_(names), cls.module == module)
         .filter_by(**kwargs)
         .delete(synchronize_session='fetch'))
        db.session.flush()
        cls._clear_cache()

    @classmethod
    def delete_all(cls, module, **kwargs):
        cls.query.filter_by(module=module, **kwargs).delete()
        db.session.flush()
        cls._clear_cache()

    @classmethod
    def _get_cache(cls, kwargs):
        if not has_request_context():
            # disable the cache by always returning an empty one
            return defaultdict(dict), False
        key = (cls, frozenset(kwargs.items()))
        try:
            return g.global_settings_cache[key], True
        except AttributeError:
            # no cache at all
            g.global_settings_cache = cache = dict()
            cache[key] = rv = defaultdict(dict)
            return rv, False
        except KeyError:
            # no cache for this settings class / kwargs
            return g.global_settings_cache.setdefault(key, defaultdict(dict)), False

    @staticmethod
    def _clear_cache():
        if has_request_context():
            g.pop('global_settings_cache', None)


class JSONSettingsBase(SettingsBase):
    """Base class for setting tables with a JSON value."""

    __tablename__ = 'settings'

    value = db.Column(
        JSONB,
        nullable=False
    )

    @classmethod
    def get_setting(cls, module, name, **kwargs):
        return cls.query.filter_by(module=module, name=name, **kwargs).first()

    @classmethod
    def get_all_settings(cls, module, **kwargs):
        return {s.name: s for s in cls.query.filter_by(module=module, **kwargs)}

    @classmethod
    def get_all(cls, module, **kwargs):
        cache, hit = cls._get_cache(kwargs)
        if hit:
            return cache[module]
        else:
            for s in cls.query.filter_by(**kwargs):
                cache[s.module][s.name] = s.value
            return cache[module]

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
        cls._clear_cache()

    @classmethod
    def set_multi(cls, module, items, **kwargs):
        existing = cls.get_all_settings(module, **kwargs)
        for name in items.keys() - existing.keys():
            setting = cls(module=module, name=name, value=_coerce_value(items[name]), **kwargs)
            db.session.add(setting)
        for name in items.keys() & existing.keys():
            existing[name].value = _coerce_value(items[name])
        db.session.flush()
        cls._clear_cache()


class PrincipalSettingsBase(PrincipalMixin, SettingsBase):
    """Base class for principal setting tables."""

    __tablename__ = 'settings_principals'
    # Additional columns used to identitfy a setting (e.g. user/event id)
    extra_key_cols = ()

    @strict_classproperty
    @classmethod
    def unique_columns(cls):
        return ('module', 'name') + cls.extra_key_cols

    @classmethod
    def get_all_acls(cls, module, **kwargs):
        rv = defaultdict(set)
        for setting in cls.query.filter_by(module=module, **kwargs):
            rv[setting.name].add(setting.principal)
        return rv

    @classmethod
    def get_acl(cls, module, name, raw=False, **kwargs):
        return {x if raw else x.principal for x in cls.query.filter_by(module=module, name=name, **kwargs)}

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
        for name, acl in items.items():
            cls.set_acl(module, name, acl, **kwargs)

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
                    for setting in cls.query.filter_by(module=module, type=PrincipalType.user, user=source)]
        for module, name, extra in settings:
            cls.remove_principal(module, name, source, **extra)
            cls.add_principal(module, name, target, **extra)
        db.session.flush()
