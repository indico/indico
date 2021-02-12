# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from flask_caching import Cache
from flask_caching.backends.rediscache import RedisCache
from flask_caching.backends.simplecache import SimpleCache
from redis import RedisError

from indico.core.logger import Logger


_logger = Logger.get('cache')


class CachedNone:
    __slots__ = ()

    @classmethod
    def wrap(cls, value):
        return cls() if value is None else value

    @classmethod
    def unwrap(cls, value, default=None):
        if value is None:
            return default
        elif isinstance(value, cls):
            return None
        else:
            return value


class IndicoCacheMixin:
    def get(self, key, default=None):
        return CachedNone.unwrap(super().get(key), default)

    def get_many(self, *keys, default=None):
        return [CachedNone.unwrap(val, default) for val in super().get_many(*keys)]

    def get_dict(self, *keys, default=None):
        return dict(zip(keys, self.get_many(*keys, default=default)))


class IndicoRedisCache(IndicoCacheMixin, RedisCache):
    """
    This is similar to the original RedisCache from Flask-Caching, but it
    allows specifying a default value when retrieving cache data and
    distinguishing between a cached ``None`` value and a cache miss.
    """

    def dump_object(self, value):
        # We are not overriding the `load_object` counterpart to this method o
        # purpose because we need to have access to the wrapped value in `get`
        # and `get_many`.
        return super().dump_object(CachedNone.wrap(value))


class IndicoSimpleCache(IndicoCacheMixin, SimpleCache):
    """
    This is similar to the original SimpleCache from Flask-Caching, but it
    allows specifying a default value when retrieving cache data and
    distinguishing between a cached ``None`` value and a cache miss.
    """

    def set(self, key, value, timeout=None):
        return super().set(key, CachedNone.wrap(value), timeout=timeout)

    def add(self, key, value, timeout=None):
        return super().add(key, CachedNone.wrap(value), timeout=timeout)


def make_indico_simple_cache(app, config, args, kwargs):
    return IndicoSimpleCache(*args, **kwargs)


def make_indico_redis_cache(app, config, args, kwargs):
    from redis import from_url as redis_from_url
    key_prefix = config.get('CACHE_KEY_PREFIX')
    if key_prefix:
        kwargs['key_prefix'] = key_prefix
    kwargs['host'] = redis_from_url(config['CACHE_REDIS_URL'], socket_timeout=1)
    return IndicoRedisCache(*args, **kwargs)


class ScopedCache:
    def __init__(self, cache, scope):
        self.cache = cache
        self.scope = scope

    def _scoped(self, key):
        return f'{self.scope}/{key}'

    def get(self, key, default=None):
        return self.cache.get(self._scoped(key), default=default)

    def set(self, key, value, timeout=None):
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        self.cache.set(self._scoped(key), value, timeout=timeout)

    def add(self, key, value, timeout=None):
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        self.cache.add(self._scoped(key), value, timeout=timeout)

    def delete(self, key):
        self.cache.delete(self._scoped(key))

    def delete_many(self, *keys):
        keys = [self._scoped(key) for key in keys]
        self.cache.delete_many(*keys)

    def clear(self):
        raise NotImplementedError('Clearing scoped caches is not supported')

    def get_dict(self, *keys, default=None):
        return dict(zip(keys, self.get_many(*keys, default=default)))

    def get_many(self, *keys, default=None):
        keys = [self._scoped(key) for key in keys]
        return self.cache.get_many(*keys, default=default)

    def set_many(self, mapping, timeout=None):
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        mapping = {self._scoped(key): value for key, value in mapping.items()}
        self.cache.set_many(mapping, timeout=timeout)

    def __repr__(self):
        return f'<ScopedCache: {self.scope}>'


class IndicoCache(Cache):
    """
    This is basicaly the Cache class from Flask-Caching but it silences all
    exceptions that happen during a cache operation since cache failures should
    not take down the whole page.

    While this cache can in principle support many different backends, we only
    consider redis and (for unittests) a simple dict-based cache. This allows
    us to be more specific in catching exceptions since the Redis cache has
    exactly one base exception.
    """

    def get(self, key, default=None):
        try:
            return super().get(key, default)
        except RedisError:
            _logger.exception('get(%r) failed', key)
            return default

    def set(self, key, value, timeout=None):
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        try:
            super().set(key, value, timeout=timeout)
        except RedisError:
            _logger.exception('set(%r) failed', key)

    def add(self, key, value, timeout=None):
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        try:
            super().add(key, value, timeout=timeout)
        except RedisError:
            _logger.exception('add(%r) failed', key)

    def delete(self, key):
        try:
            super().delete(key)
        except RedisError:
            _logger.exception('delete(%r) failed', key)

    def delete_many(self, *keys):
        try:
            super().delete_many(*keys)
        except RedisError:
            _logger.exception('delete_many(%s) failed', ', '.join(map(repr, keys)))

    def clear(self):
        try:
            super().clear()
        except RedisError:
            _logger.exception('clear() failed')

    def get_many(self, *keys, default=None):
        try:
            return super().get_many(*keys, default=default)
        except RedisError:
            logkeys = ', '.join(map(repr, keys))
            _logger.exception('get_many(%s) failed', logkeys)
            return [default] * len(keys)

    def set_many(self, mapping, timeout=None):
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        try:
            super().set_many(mapping, timeout=timeout)
        except RedisError:
            _logger.exception('set_many(%r) failed', mapping)

    def get_dict(self, *keys, default=None):
        try:
            return super().get_dict(*keys, default=default)
        except RedisError:
            logkeys = ', '.join(map(repr, keys))
            _logger.exception('get_dict(%s) failed', logkeys)
            return dict(zip(keys, [default] * len(keys)))


def make_scoped_cache(scope):
    """Create a new scoped cache.

    In most cases the global cache should not be used directly but rather
    with a scope depending on the module a cache is used for. This is
    especially important when passing user-provided data as the cache key
    to prevent reading other unrelated cache keys.
    """
    return ScopedCache(cache, scope)


cache = IndicoCache()
