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
This module provides a skeleton of a test runner (BaseTestRunner) that all the
other TestRunners should inherit from.
"""

# System modules
import os, sys

# Python stdlib
import StringIO

# Indico
from indico.tests.util import TeeStringIO, colored
from indico.tests.config import TestConfig

class BaseTestRunner(object):
    """
    Base class for all other TestRunners.
    A TestRunner runs a specific kind of test (i.e. UnitTestRunner)
    """

    # path to this current file
    setupDir = os.path.dirname(__file__)

    def __init__(self, **kwargs):
        """
        Options can be passed as kwargs, currently the following is supported:

         * verbose - if the output should be redirected to the console in
        addition to the log file;
        """

        self.options = kwargs
        self.err = None
        self.out = None

        # make a TestConfig instance available everywhere
        self.config = TestConfig.getInstance()

    def _run(self):
        """
        This method should be overloaded by inheriting classes.
        It should provide the code that executes the actual tests,
        returning output information.
        """
        pass

    def run(self):
        """
        Executes the actual test code
        """
        # get the description from the first lines
        # of the docstring
        description =  self.__doc__.strip().split('\n')[0]

        print colored("** Running %s" % description, 'yellow', attrs = ['bold'])

        return self._run()

    def _startIOCapture(self):
        """
        Start capturing stdout and stderr to StringIOs
        If options['verbose'] has been set, the data will be output to the
        stdout/stderr as well
        """

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
        """
        Restore stdout/stderr and return the captured data
        """
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__

        return (self.out.getvalue(),
                self.err.getvalue())

    @staticmethod
    def _redirectPipeToStdout(pipe):
        """
        Redirect a given pipe to stdout
        """
        while True:
            data = pipe.readline()
            if not data:
                break
            print data,

    def writeReport(self, filename, content):
        """
        Write the test report, using the filename and content that are passed
        """
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
        """
        Scan a directory and return folders which match the pattern
        """

        rootPluginsPath = os.path.join(rootPath)
        foldersArray = []

        for root, __, __ in os.walk(rootPluginsPath):
            if root.endswith(foldersPattern) > 0:
                foldersArray.append(root)

        return foldersArray
