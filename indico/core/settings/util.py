# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from copy import copy


_not_in_db = object()


def _get_cache_key(proxy, name, kwargs):
    return type(proxy), proxy.module, name, frozenset(kwargs.items())


def _preload_settings(cls, proxy, cache, **kwargs):
    settings = cls.get_all(proxy.module, **kwargs)
    for name, value in settings.items():
        cache_key = _get_cache_key(proxy, name, kwargs)
        cache[cache_key] = value
    # cache missing entries as not in db
    for name in proxy.defaults.keys() - settings.keys():
        cache_key = _get_cache_key(proxy, name, kwargs)
        cache[cache_key] = _not_in_db
    return settings


def get_all_settings(cls, acl_cls, proxy, no_defaults, **kwargs):
    """Helper function for SettingsProxy.get_all."""
    if no_defaults:
        rv = cls.get_all(proxy.module, **kwargs)
        if acl_cls and proxy.acl_names:
            rv.update(acl_cls.get_all_acls(proxy.module, **kwargs))
        return {k: proxy._convert_to_python(k, v) for k, v in rv.items()}
    settings = dict(proxy.defaults)
    if acl_cls and proxy.acl_names:
        settings.update({name: set() for name in proxy.acl_names})
    settings.update({k: proxy._convert_to_python(k, v)
                     for k, v in cls.get_all(proxy.module, **kwargs).items()
                     if not proxy.strict or k in proxy.defaults})
    if acl_cls and proxy.acl_names:
        settings.update(acl_cls.get_all_acls(proxy.module, **kwargs))
    return settings


def get_setting(cls, proxy, name, default, cache, **kwargs):
    """Helper function for SettingsProxy.get."""
    from indico.core.settings import SettingsProxyBase

    cache_key = _get_cache_key(proxy, name, kwargs)
    try:
        value = cache[cache_key]
        if value is not _not_in_db:
            return proxy._convert_to_python(name, value)
    except KeyError:
        setting = _preload_settings(cls, proxy, cache, **kwargs).get(name, _not_in_db)
        cache[cache_key] = setting
        if setting is not _not_in_db:
            return proxy._convert_to_python(name, setting)
    # value is not_in_db, so use the default
    # we always copy the proxy's default in case it's something mutable
    return copy(proxy.defaults.get(name)) if default is SettingsProxyBase.default_sentinel else default


def get_setting_acl(cls, proxy, name, cache, **kwargs):
    """Helper function for ACLProxy.get."""
    cache_key = _get_cache_key(proxy, name, kwargs)
    try:
        return cache[cache_key]
    except KeyError:
        cache[cache_key] = acl = cls.get_acl(proxy.module, name, **kwargs)
        return acl
