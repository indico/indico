# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps
from inspect import getcallargs

from flask import current_app, g, has_request_context


_notset = object()


def make_hashable(obj):
    if isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in obj.iteritems())
    elif hasattr(obj, 'getId') and obj.getId.__self__ is not None:
        # getId of AvatarUserWrapper would access a cached property, we can't have that here
        id_ = obj.getId() if obj.__class__.__name__ != 'AvatarUserWrapper' else obj.id
        return obj.__class__.__name__, id_
    return obj


# http://wiki.python.org/moin/PythonDecoratorLibrary#Alternate_memoize_as_nested_functions
# Not thread-safe. Don't use it in places where thread-safety is important!
def memoize(obj):
    cache = {}

    @wraps(obj)
    def memoizer(*args, **kwargs):
        key = (make_hashable(args), make_hashable(kwargs))
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoizer


def memoize_request(f):
    """Memoize a function during the current request."""
    @wraps(f)
    def memoizer(*args, **kwargs):
        if not has_request_context() or current_app.config['TESTING'] or current_app.config.get('REPL'):
            # No memoization outside request context
            return f(*args, **kwargs)

        try:
            cache = g.memoize_cache
        except AttributeError:
            g.memoize_cache = cache = {}

        key = (f.__module__, f.__name__, make_hashable(getcallargs(f, *args, **kwargs)))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]

    return memoizer


def memoize_redis(ttl):
    """Memoize a function in redis.

    The cached value can be cleared by calling the method
    ``clear_cached()`` of the decorated function with the same
    arguments that were used during the function call.  To check
    whether a value has been cached call ``is_cached()`` in the
    same way.

    :param ttl: How long the result should be cached.  May be a
                timedelta or a number (seconds).
    """
    from indico.legacy.common.cache import GenericCache
    cache = GenericCache('memoize')

    def decorator(f):
        def _get_key(args, kwargs):
            return f.__module__, f.__name__, make_hashable(getcallargs(f, *args, **kwargs))

        def _clear_cached(*args, **kwargs):
            cache.delete(_get_key(args, kwargs))

        def _is_cached(*args, **kwargs):
            return cache.get(_get_key(args, kwargs), _notset) is not _notset

        @wraps(f)
        def memoizer(*args, **kwargs):
            if current_app.config['TESTING'] or current_app.config.get('REPL'):
                # No memoization during tests or in the shell
                return f(*args, **kwargs)

            key = _get_key(args, kwargs)
            value = cache.get(key, _notset)
            if value is _notset:
                value = f(*args, **kwargs)
                cache.set(key, value, ttl)
            return value

        memoizer.clear_cached = _clear_cached
        memoizer.is_cached = _is_cached
        return memoizer

    return decorator
