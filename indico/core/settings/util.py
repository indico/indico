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

from indico.core.settings.proxy import SettingsProxyBase


_not_in_db = object()


def _get_cache_key(proxy, name, kwargs):
    return type(proxy), proxy.module, name, frozenset(kwargs.viewitems())


def _preload_settings(cls, proxy, cache, **kwargs):
    settings = cls.get_all(proxy.module, **kwargs)
    for name, value in settings.iteritems():
        cache_key = _get_cache_key(proxy, name, kwargs)
        cache[cache_key] = value
    # cache missing entries as not in db
    for name in proxy.defaults.viewkeys() - settings.viewkeys():
        cache_key = _get_cache_key(proxy, name, kwargs)
        cache[cache_key] = _not_in_db
    return settings


def get_all_settings(cls, acl_cls, proxy, no_defaults, **kwargs):
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


def get_setting(cls, proxy, name, default, cache, **kwargs):
    """Helper function for SettingsProxy.get"""
    cache_key = _get_cache_key(proxy, name, kwargs)
    try:
        value = cache[cache_key]
        if value is not _not_in_db:
            return value
    except KeyError:
        if proxy.preload:
            setting = _preload_settings(cls, proxy, cache, **kwargs).get(name, _not_in_db)
        else:
            setting = cls.get(proxy.module, name, _not_in_db, **kwargs)
        cache[cache_key] = setting
        if setting is not _not_in_db:
            return setting
    # value is not_in_db, so use the default
    return proxy.defaults.get(name) if default is SettingsProxyBase.default_sentinel else default


def get_setting_acl(cls, proxy, name, cache, **kwargs):
    """Helper function for ACLProxy.get"""
    cache_key = _get_cache_key(proxy, name, kwargs)
    try:
        return cache[cache_key]
    except KeyError:
        cache[cache_key] = acl = cls.get_acl(proxy.module, name, **kwargs)
        return acl
