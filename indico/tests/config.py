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
Here is defined a helper class that provides access to the configuration file
for the testing framework.
"""

import os

class TestConfig:
    """
    Singleton Proxy for tests.conf, that loads it and provides get* methods
    """

    __instance = None

    def __init__(self):
        """
        Initializes the proxy object, loading the configuration data
        from tests.conf
        """
        fpath = os.path.join(os.path.dirname(__file__), 'tests.conf')
        if os.path.exists(fpath):
            execfile(fpath)
        else:
            print "tests.conf not found, using sample file instead"
            execfile("%s.sample" % fpath)
        self.testsConf = locals()

    def __getattr__(self, attr):
        """
        Dynamic finder for values defined in indico.conf

        For example, if an indico.conf value is "username" this method will
        return its value for a getUsername() call.

        If you add a new pair option = value to indico.conf there is no need to
        create anything here. It will be returned automatically.

        This all means that changing the name of an indico.conf will force you
        to change all references in code to getOldOptionName to getNewOptionName
        including the reference in default_values in this file.
        """

        # The following code intercepts all method calls that start with get and are
        # not already defined (so you can still override a get method if you want)
        # and returns a closure that returns the value of the option being asked for
        if attr[0:3] == 'get':
            def configFinder(k):
                return self.testsConf[k]
            return lambda: configFinder(attr[3:])
        else:
            raise AttributeError

    @classmethod
    def getInstance(cls):
        """
        Provides a single instance for this class (singleton)
        """
        if cls.__instance == None:
            cls.__instance = cls()
        return cls.__instance
