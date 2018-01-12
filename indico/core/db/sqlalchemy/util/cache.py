# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import random
from functools import wraps

from indico.util.caching import make_hashable
from indico.util.decorators import cached_writable_property


def versioned_cache(cache, primary_key_attr='id'):
    """Mixin to add a cache version number, bumped on each commit.

    This class MUST come before db.Model in the superclass list::

        class SomeModel(versioned_cache(my_cache), db.Model, ...):
            pass

    :param cache: A :class:`GenericCache` instance
    :param primary_key_attr: The attribute containing the an unique identifier for the object
    """
    def _get_key(obj):
        return 'version:{}[{}]'.format(type(obj).__name__, getattr(obj, primary_key_attr))

    class _CacheVersionMixin(object):
        def __committed__(self, change):
            super(_CacheVersionMixin, self).__committed__(change)
            if change == 'delete':
                cache.delete(_get_key(self))
            else:
                self.cache_version += 1

        @cached_writable_property('_cache_version')
        def cache_version(self):
            return cache.get(_get_key(self), 0)

        @cache_version.setter
        def cache_version(self, value):
            cache.set(_get_key(self), value)

    return _CacheVersionMixin


def cached(cache, primary_key_attr='id', base_ttl=86400*31):
    """Caches the decorated function's result in redis.

    This decorator is meant to be be used for properties::

        @property
        @cached(my_cache)
        def expensive_function(self):
            return self.do_expensive_stuff()

    It is usually a good idea to expunge cache entries when the object is modified.
    To do so, make the model inherit from the mixin created by :func:`versioned_cache`.

    :param cache: A :class:`GenericCache` instance
    :param primary_key_attr: The attribute containing the an unique identifier for the object
    :param base_ttl: The time after which a cached property expires
    """
    _not_cached = object()

    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            primary_key = getattr(self, primary_key_attr)
            if hasattr(self, 'cache_version'):
                key = u'{}[{}.{}].{}'.format(type(self).__name__, primary_key, self.cache_version, f.__name__)
            else:
                key = u'{}[{}].{}'.format(type(self).__name__, primary_key, f.__name__)

            args_key = u', '.join(map(repr, map(make_hashable, args)) +
                                  [u'{}={}'.format(k, make_hashable(v)) for k, v in sorted(kwargs.viewitems())])
            if args_key:
                key = '{}({})'.format(key, args_key)

            result = cache.get(key, _not_cached)
            if result is _not_cached:
                result = f(self, *args, **kwargs)
                # Cache the value with a somewhat random expiry so we don't end up with all keys
                # expiring at the same time if there hasn't been an update for some time
                cache.set(key, result, base_ttl + 300 * random.randint(0, 200))
            return result

        return wrapper

    return decorator
