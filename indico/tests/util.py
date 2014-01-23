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
This module defines some utility classes for the testing framework,
such as a wrapper for ZEOServer that allows a "test" server to be created
"""

import os, time, logging
from multiprocessing import Process
from StringIO import StringIO

from ZEO.runzeo import ZEOOptions, ZEOServer


class SilentZEOServer(ZEOServer):
    """
    A ZEO Server that doesn't write on the console
    """
    def setup_default_logging(self):
        # do nothing, just use whatever handler is available
        pass


class TestZEOServer(Process):
    """
    Creates a standalone ZEO server for tests
    """
    def __init__(self, port, fd, hostname="localhost"):
        Process.__init__(self)
        self.addr = (hostname, port)
        self.fd = fd

    def run(self):
        """
        Actually starts the server
        """
        options = ZEOOptions()
        options.realize(['-f', self.fd, '-a', '%s:%d' % self.addr])
        self.server = SilentZEOServer(options)
        self.server.main()

    def shutdown(self, killself=False):
        """
        This is basically a 'blocking' terminate()
        """

        self.terminate()

        if killself:
            # Do not wait for shutdown if we are going to kill ourselves
            return

        # wait till i'm dead
        while self.is_alive():
            time.sleep(1)


class TeeStringIO(StringIO):
    """
    Wrapper for StringIO that writes to an output stream as well
    """
    def __init__(self, out, targetStream = None):
        self.__outStream =  out
        self.__targetStream = targetStream
        StringIO.__init__(self)

    def write(self, string, echo=True):

        if echo:
            self.__outStream.write(string)
        if self.__targetStream:
            self.__targetStream.write(string, echo=False)
        else:
            StringIO.write(self, string)

    def read(self, n=-1):
        self.seek(0)
        self.__outStream.write(StringIO.read(self.__targetStream or self, n=n))


def openBrowser(browserPath, filePath):
    """
    Open a browser window with an HTML document
    """
    os.system("%s %s" % (browserPath, filePath))


###
# path manipulation functions
# adapted from path.py (Jason Orendorff <jason at jorendorff com>)
#
# (Public Domain code)
###

def splitall(loc):
    """
    Return a list of the path components in this path.

    The first item in the list will be a path.  Its value will be
    either os.curdir, os.pardir, empty, or the root directory of
    this path (for example, '/' or 'C:\\').  The other items in
    the list will be strings.

    path.path.joinpath(*result) will yield the original path.
    """

    parts = []
    while loc != os.curdir and loc != os.pardir:
        prev = loc
        loc, child = os.path.split(prev)
        if loc == prev:
            break
        parts.append(child)
    parts.append(loc)
    parts.reverse()
    return parts


def relpathto(origin, dest):
    """
    Return a relative path from self to dest.

    If there is no relative path from self to dest, for example if
    they reside on different drives in Windows, then this returns
    dest.abspath().
    """

    orig_list = splitall(os.path.normcase(origin))
    # Don't normcase dest!  We want to preserve the case.
    dest_list = splitall(dest)

    if orig_list[0] != os.path.normcase(dest_list[0]):
        # Can't get here from there.
        return dest

    # Find the location where the two paths start to differ.
    i = 0
    for start_seg, dest_seg in zip(orig_list, dest_list):
        if start_seg != os.path.normcase(dest_seg):
            break
        i += 1

    # Now i is the point where the two paths diverge.
    # Need a certain number of "os.pardir"s to work up
    # from the origin to the point of divergence.
    segments = [os.pardir] * (len(orig_list) - i)
    # Need to add the diverging part of dest_list.
    segments += dest_list[i:]
    if len(segments) == 0:
        # If they happen to be identical, use os.curdir.
        relpath = os.curdir
    else:
        relpath = os.path.join(*segments)
    return relpath

### END ###
