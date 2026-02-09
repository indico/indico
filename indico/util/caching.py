# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps
from inspect import getcallargs

from flask import current_app, g, has_request_context
from werkzeug.exceptions import Conflict


_notset = object()


def make_hashable(obj):
    if isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in obj.items())
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


def memoize_redis(ttl, *, versioned=False):
    """Memoize a function in redis.

    The cached value can be cleared by calling the method
    ``clear_cached()`` of the decorated function with the same
    arguments that were used during the function call.  To check
    whether a value has been cached call ``is_cached()`` in the
    same way.

    :param ttl: How long the result should be cached.  May be a
                timedelta or a number (seconds).
    """
    from indico.core.cache import make_scoped_cache
    cache = make_scoped_cache('memoize')

    def decorator(f):
        version_key = '_version_', f.__module__, f.__name__

        def _get_key(args, kwargs):
            version_parts = ()
            if versioned:
                version_parts = (cache.get(version_key, 0),)
            return *version_parts, f.__module__, f.__name__, make_hashable(getcallargs(f, *args, **kwargs))

        def _clear_cached(*args, **kwargs):
            cache.delete(_get_key(args, kwargs))

        def _is_cached(*args, **kwargs):
            return cache.get(_get_key(args, kwargs), _notset) is not _notset

        def _bump_version(new_version=None):
            if new_version is None:
                new_version = cache.get(version_key, 0) + 1
            cache.set(version_key, new_version)

        @wraps(f)
        def memoizer(*args, **kwargs):
            if current_app.config['TESTING'] or current_app.config.get('REPL'):
                # No memoization during tests or in the shell
                return f(*args, **kwargs)

            key = _get_key(args, kwargs)
            value = cache.get(key, _notset)
            if value is _notset:
                value = f(*args, **kwargs)
                cache.set(key, value, timeout=ttl)
            return value

        memoizer.clear_cached = _clear_cached
        memoizer.is_cached = _is_cached
        if versioned:
            memoizer.bump_version = _bump_version
        return memoizer

    return decorator


def global_lock(*, timeout, use_args=True):
    """Globally lock a function so it cannot execute in parallel.

    This is intended for expensive endpoints where it is not possible to apply more
    fine-grained rate limiting (e.g. because they do not require authentication) AND
    it does not cause disruption to users if requests can randomly fail. In particular,
    it should only be used in places where the potential DoS of someone repeatedly
    calling the endpoint does not cause notable issues for anyone else, for example by
    caching the result and only applying this lock when no cached value is available.
    """
    from indico.core.cache import make_scoped_cache
    cache = make_scoped_cache('global-lock')

    def decorator(f):
        def _get_key(args, kwargs):
            args_key = (make_hashable(getcallargs(f, *args, **kwargs)),) if use_args else ()
            return f.__module__, f.__name__, *args_key

        def _is_running(*args, **kwargs):
            return cache.get(_get_key(args, kwargs), _notset) is not _notset

        @wraps(f)
        def memoizer(*args, **kwargs):
            if current_app.config['TESTING'] or current_app.config.get('REPL'):
                # No limits during tests or in the shell
                return f(*args, **kwargs)

            key = _get_key(args, kwargs)
            if cache.get(key, _notset) is not _notset:
                raise Conflict('Please try again later')
            cache.set(key, True, timeout=timeout)
            rv = f(*args, **kwargs)
            cache.delete(key)
            return rv

        memoizer.is_running = _is_running
        return memoizer

    return decorator
