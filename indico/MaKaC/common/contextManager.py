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

class ContextManager:

    class NoContextException(Exception):
        pass


    class DummyContext:

        def _dummyMethod(*args, **kwargs):
            return None

        def __getattr__(self, name):
            return self._dummyMethod

        def __setattr__(self, name, value):
            return None


    @classmethod
    def _getContextDict(cls):
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
        tid = threading._get_ident()
        del cls._getContextDict()[tid]

    @classmethod
    def create(cls):
        cls._getThreadContext(forceCleanup=True)

    @classmethod
    def get(cls, name):
        """
        If no set has been done over the variable before,
        an exception will be thrown.
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
        try:
            cls._getThreadContext()[name] = value
        except cls.NoContextException:
            return cls.DummyContext()

