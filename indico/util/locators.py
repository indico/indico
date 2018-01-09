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

from __future__ import unicode_literals

from UserDict import IterableUserDict, UserDict

from werkzeug.utils import cached_property


class locator_property(object):
    """Defines a smart locator property.

    This behaves pretty much like a normal read-only property and the
    decorated function should return a dict containing the necessary
    data to build a URL for the object.

    This decorator should usually be applied to a method named
    ``locator`` as this name is required for `get_locator` to find it
    automatically when just passing the object.

    If you need more than one locator, you can define it like this::

        @locator_property
        def locator(self):
            return {...}

        @locator.other
        def locator(self):
            return {...}

    The ``other`` locator can then be accessed by passing
    ``obj.locator.other`` to the code expecting an object with
    a locator.
    """

    def __init__(self, fn):
        self.fn = fn
        self.locators = {}

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return _LocatorDict(self, obj)

    def __getattr__(self, name):
        def _fn(f):
            assert name not in self.locators
            self.locators[name] = f
            return self
        return _fn

    def __repr__(self):
        if self.locators:
            return '<locator_property with {}>'.format(', '.join(self.locators))
        else:
            return '<locator_property>'


def get_locator(obj):
    """Retrieves the locator data from an object.

    The object may be a dictionary (in case a locator is passed) or
    an object with a ``locator`` property.
    """
    # note: we use explicit hasattr checks since we don't want to end
    # up with an AttributeError raised from inside the locator method.
    # doing so would result in a hard-to-debug error since we'd assume
    # the object doesn't have a locator instead of letting the actual
    # exception bubble up.
    if isinstance(obj, (dict, UserDict)):
        return obj
    elif hasattr(obj, 'locator'):
        return obj.locator
    else:
        raise TypeError('{} does not contain a locator'.format(obj))


class _LocatorDict(IterableUserDict, object):
    def __init__(self, locator, obj):
        # call to super constructor is omitted on purpose
        self._locator = locator
        self._obj = obj

    @cached_property
    def data(self):
        try:
            return self._locator.fn(self._obj)
        except AttributeError as e:
            # an AttributeError leaving this function would result in
            # `__getattr__ ` being called which is clearly not what we
            # want here as there cannot be a 'data' locator and the
            # error raised in `__getattr__` would be very misleading
            raise Exception(e)

    def __getattr__(self, name):
        try:
            fn = self._locator.locators[name]
        except KeyError:
            raise AttributeError('No such locator: ' + name)
        return fn(self._obj)
