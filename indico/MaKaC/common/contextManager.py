# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Defines the ContextManager, which provides a global access namespace for
storing runtime information
"""

import threading

class ContextManager(object):
    """
    A context manager provides a global access namespace (singleton) for storing
    run-time information.
    """

    def __init__(self):
        pass

    class NoContextException(Exception):
        """
        Thrown where there is no Context currently defined
        """
        pass


    class DummyContext(object):
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
            return "<DummyContext>"


    @classmethod
    def _getContextDict(cls):
        """
        Retrieve the corresponding dictionary for the current
        context
        """
        if not hasattr(cls, 'contextDict'):
            cls.contextDict = {}
        return cls.contextDict

    @classmethod
    def _getThreadContext(cls, forceCleanup=False):
        """
        * forceCleanup - forces the context to be reset
        """

        tid = threading._get_ident()
        contextDict = cls._getContextDict()

        if forceCleanup:
            contextDict[tid] = {}

        if tid in contextDict:
            return contextDict[tid]
        else:
            raise cls.NoContextException(tid)

    @classmethod
    def destroy(cls):
        """
        destroy the context
        """
        tid = threading._get_ident()
        del cls._getContextDict()[tid]

    @classmethod
    def create(cls):
        """
        create the context
        """
        cls._getThreadContext(forceCleanup=True)

    @classmethod
    def get(cls, name):
        """
        If no set has been done over the variable before,
        a dummy context will be returned.
        """
        try:
            return cls._getThreadContext()[name]
        except (cls.NoContextException, KeyError):
            return cls.DummyContext()

    @classmethod
    def has(cls, name):
        """
        If no set has been done over the variable before,
        an exception will be thrown.
        """
        try:
            return name in cls._getThreadContext()
        except cls.NoContextException:
            return False

    @classmethod
    def getdefault(cls, name, default):
        """
        If no set has been done over the variable before,
        a default value is *set* and *returned*
        """
        try:
            return cls._getThreadContext().setdefault(name, default)
        except cls.NoContextException:
            return cls.DummyContext()

    @classmethod
    def set(cls, name, value):
        """
        Set the 'name' entry to 'value'
        """
        try:
            cls._getThreadContext()[name] = value
        except cls.NoContextException:
            return cls.DummyContext()
