# -*- coding: utf-8 -*-
##
## $Id$
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
This module defines some utility classes for the testing framework,
such as a wrapper for ZEOServer that allows a "test" server to be created
"""

import os
from StringIO import StringIO

from ZEO.runzeo import ZEOOptions, ZEOServer


class TestZEOServer:
    """
    Creates a standalone ZEO server for tests
    """
    def __init__(self, port, fd):
        self.options = ZEOOptions()
        self.options.realize(['-f', fd, '-a', 'localhost:%d' % port])
        self.server = ZEOServer(self.options)

    def start(self):
        """
        Actually starts the server
        """
        print "spawning server on PID %s" % os.getpid()
        self.server.main()


class TeeStringIO(StringIO):
    """
    Wrapper for StringIO that writes to an output stream as well
    """
    def __init__(self, out):
        self.__outStream =  out
        StringIO.__init__(self)

    def write(self, string):
        self.__outStream.write(string)
        StringIO.write(self, string)

    def read(self, n=-1):
        self.seek(0)
        self.__outStream.write(StringIO.read(self, n=n))

# pylint: disable-msg=W0611

try:
    from termcolor import colored
except ImportError:
    def colored(text, *__, **___):
        """
        just a dummy function that returns the same string
        (in case termcolor is not available)
        """
        return text
