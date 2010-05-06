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

# System modules
import os, sys

# Python stdlib
import StringIO

# Indico
from indico.tests.util import TeeStringIO, colored


class BaseTestRunner(object):
    """
    Base class for all other TestRunners.
    A TestRunner runs a specific kind of test (i.e. UnitTestRunner)
    """

    # path to this current file
    setupDir = os.path.dirname(__file__)

    def __init__(self, **kwargs):
        self.options = kwargs
        self.err = None
        self.out = None

    def run(self):
        # get the description from the first lines
        # of the docstring
        description =  self.__doc__.strip().split('\n')[0]

        print colored("** Running %s" % description, 'yellow', attrs = ['bold'])

        return self._run()

    def _startIOCapture(self):

        if self.options['verbose']:
            # capture I/O but display it as well
            self.err = TeeStringIO(sys.stderr)
            self.out = TeeStringIO(sys.stdout)
        else:
            # just capture it
            self.err = StringIO.StringIO()
            self.out = StringIO.StringIO()
        sys.stderr = self.err
        sys.stdout = self.out


    def _finishIOCapture(self):
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__

        return (self.out.getvalue(),
                self.err.getvalue())

    @staticmethod
    def _redirectPipeToStdout(pipe):
        while True:
            data = pipe.readline()
            if not data:
                break
            print data,

    def writeReport(self, filename, content):
        try:
            f = open(os.path.join(self.setupDir, 'report', filename + ".txt"), 'w')
            f.write(content)
            f.close()
            return ""
        except IOError:
            return "Unable to write in %s, check your file permissions." % \
                    os.path.join(self.setupDir, 'report', filename + ".txt")

    @staticmethod
    def walkThroughFolders(rootPath, foldersPattern):
        """scan a directory and return folders which match the pattern"""

        rootPluginsPath = os.path.join(rootPath)
        foldersArray = []

        for root, __, __ in os.walk(rootPluginsPath):
            if root.endswith(foldersPattern) > 0:
                foldersArray.append(root)

        return foldersArray
