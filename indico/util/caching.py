# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from functools import wraps
from indico.util.contextManager import ContextManager


def request_cached(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        # if there are kwargs, skip caching
        if kwargs:
            return f(*args, **kwargs)
        else:
            # create a unique key
            k = (f, args)
            cache = ContextManager.setdefault('request_cache', {})
            if k not in cache:
                cache[k] = f(*args)
            return cache[k]
    return _wrapper


def order_dict(dict):
    """
    Very simple method that returns an sorted tuple of (k, v) tuples
    This is supposed to be used for converting shallow dicts into "hashable"
    values.
    """
    return tuple(sorted(dict.iteritems()))


# http://code.activestate.com/recipes/576563-cached-property/
# Modified to use a volatile dict so it doesn't go to the DB under any circumstances
def cached_property(f):
    """returns a cached property that is calculated by function f"""
    def get(self):
        try:
            return self._v_property_cache[f]
        except AttributeError:
            self._v_property_cache = {}
            x = self._v_property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._v_property_cache[f] = f(self)
            return x
    return property(get)


def _make_hashable(obj):
    if isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, dict):
        return frozenset((k, _make_hashable(v)) for k, v in obj.iteritems())
    return obj


# http://wiki.python.org/moin/PythonDecoratorLibrary#Alternate_memoize_as_nested_functions
# Not thread-safe. Don't use it in places where thread-safety is important!
def memoize(obj):
    cache = {}

    @wraps(obj)
    def memoizer(*args, **kwargs):
        key = (_make_hashable(args), _make_hashable(kwargs))
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    return memoizer
