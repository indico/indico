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

"""
Defines the ContextManager, which provides a global access namespace for
storing runtime information
"""

import threading


class DummyDict(object):
    """
    A context that doesn't react, much like a Null Object
    """

    def __init__(self):
        pass

    def _dummyMethod(*args, **__):
        """
        this method just does nothing, accepting
        whatever arguments are passed to it
        """
        return None

    def __getattr__(self, name):
        return self._dummyMethod

    def __setattr__(self, name, value):
        return None

    def __str__(self):
        return "<DummyDict>"


class Context(threading.local):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __contains__(self, elem):
        return elem in self.__dict__

    def __getitem__(self, elem):
        return self.get(elem)

    def get(self, elem, default=DummyDict()):
        if elem in self.__dict__:
            return self.__dict__[elem]
        else:
            return default

    def __setitem__(self, elem, value):
        self.__dict__[elem] = value

    def __delitem__(self, elem):
        del self.__dict__[elem]

    def clear(self):
        self.__dict__.clear()

    def setdefault(self, name, default):
        return self.__dict__.setdefault(name, default)


class ContextManager(object):
    """
    A context manager provides a global access namespace (singleton) for storing
    run-time information.
    """

    _context = Context()

    def __init__(self):
        pass

    @classmethod
    def destroy(cls):
        """
        destroy the context
        """
        cls._context.clear()

    @classmethod
    def get(cls, elem=None, default=DummyDict()):
        """
        If no set has been done over the variable before,
        a dummy context will be returned.
        """
        if elem is None:
            return cls._context
        else:
            return cls._context.get(elem, default)

    @classmethod
    def set(cls, elem, value):
        cls._context[elem] = value
        return cls.get(elem)

    @classmethod
    def setdefault(cls, name, default):
        """
        If no set has been done over the variable before,
        a default value is *set* and *returned*
        """
        return cls._context.setdefault(name, default)

    @classmethod
    def delete(cls, name, silent=False):
        try:
            del cls._context[name]
        except KeyError:
            if not silent:
                raise
