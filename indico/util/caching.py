# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from functools import wraps
from inspect import getcallargs

from flask import has_request_context, g, current_app


_notset = object()


def make_hashable(obj):
    if isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in obj.iteritems())
    elif hasattr(obj, 'getId') and obj.getId.__self__ is not None:
        # getId of AvatarUserWrapper would access a cached property, we can't have that here
        # don't call Conference.getId() so we get the getId() access warning for other places
        id_ = obj.getId() if obj.__class__.__name__ not in ('AvatarUserWrapper', 'Conference') else obj.id
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
    """Memoize a function during the current request"""
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
    """Memoize a function in redis

    The cached value can be cleared by calling the method
    ``clear_cached()`` of the decorated function with the same
    arguments that were used during the function call.  To check
    whether a value has been cached call ``is_cached()`` in the
    same way.

    :param ttl: How long the result should be cached.  May be a
                timedelta or a number (seconds).
    """
    from MaKaC.common.cache import GenericCache
    cache = GenericCache('memoize')

    def decorator(f):
        def _get_key(args, kwargs):
            return f.__name__, make_hashable(getcallargs(f, *args, **kwargs))

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
