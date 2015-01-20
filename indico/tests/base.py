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
This module provides a skeleton of a test runner (BaseTestRunner) that all the
other TestRunners should inherit from.
"""

# System modules
import os, sys
from threading import Thread

# Python stdlib
import StringIO
import pkg_resources
from smtpd import SMTPServer
import asyncore
import logging

# Indico
from indico.util.console import colored
from indico.tests.util import TeeStringIO
from indico.tests.config import TestConfig


class TestOptionException(Exception):
    """
    Raised when a particular runner doesn't support an option
    """

class IOMixin(object):
    """
    Mixin class that provides some simple utility functions
    for error/info messages in the console
    """

    @classmethod
    def _info(cls, message):
        """
        Prints an info message
        """
        print colored("** %s" % message, 'blue')

    @classmethod
    def _success(cls, message):
        """
        Prints an info message
        """
        print colored("** %s" % message, 'green')

    @classmethod
    def _error(cls, message):
        """
        Prints an error message
        """
        print colored("** %s" % message, 'red')


class OptionProxy(object):
    """
    Encapsulates all the options present in a TestRunner,
    providing a common access point, and controlling some
    "hot spots" as well
    """

    def __init__(self, allowedOptions):
        self._optionTable = allowedOptions
        self._options = {}

    def call(self, runner, event, *args):
        """
        Invoked from a code hot spot, so that the option can
        perform operations
        """

        for option in self._options.values():
            if hasattr(option, event) and option.shouldExecute():
                getattr(option, event)(runner, *args)

    def configure(self, **kwargs):
        """
        Initializes the options based on command line parameters
        """
        for optName, optClass  in self._optionTable.iteritems():
            if optName in kwargs:
                self._options[optName] = optClass(kwargs[optName])
            else:
                self._options[optName] = optClass(None)

        for optName in kwargs:
            if optName not in self._optionTable:
                raise TestOptionException("Option '%s' not allowed here!" %
                                          optName)

    def valueOf(self, optName, default=None):
        """
        Returns the direct value of an option
        """
        if optName in self._options and \
                self._options[optName].value is not None:
            return self._options[optName].value
        else:
            return default


class Option(IOMixin):
    """
    Represents an option for a TestRunner
    """

    def __init__(self, value):
        self.value = value

    def shouldExecute(self):
        """
        Determines if the Option should be taken into account (hot spots),
        depending on the context
        """
        return True


class BaseTestRunner(IOMixin):
    """
    Base class for all other TestRunners.
    A TestRunner runs a specific kind of test (i.e. UnitTestRunner)
    """

    # overloaded for each runner, contains allowed options for each runner

    # for this case:
    #   * silent - True if the output shouldn't be redirected to the console

    _runnerOptions = {'silent': Option}

    # path to this current file
    setupDir = os.path.dirname(__file__)

    def __init__(self, **kwargs):
        """
        Options can be passed as kwargs, currently the following is supported:

        """

        self.err = None
        self.out = None

        # make a TestConfig instance available everywhere
        self.config = TestConfig.getInstance()

        # initialize allowed options
        self.options = OptionProxy(self._runnerOptions)
        self.options.configure(**kwargs)
        self._logger = logging.getLogger('test')

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

        self._startIOCapture()

        self._info("Running %s" % description)

        self._callOptions('pre_run')
        result = self._run()
        self._callOptions('post_run')

        if result:
            self._success("%s successful!" % description)
        else:
            self._error("%s failed!" % description)

        # ask the option handlers to compute a final message
        self._callOptions('final_message')
        self._writeReport(self.__class__.__name__,
                          self._finishIOCapture())

        return result

    def _startIOCapture(self):
        """
        Start capturing stdout and stderr to StringIOs
        If options['verbose'] has been set, the data will be output to the
        stdout/stderr as well
        """

        if self.options.valueOf('silent'):
            # just capture it
            self.err = StringIO.StringIO()
            self.out = self.err
        else:
            # capture I/O but display it as well
            self.out = TeeStringIO(sys.stdout)
            self.err = TeeStringIO(sys.stderr, targetStream = self.out)
        sys.stderr = self.err
        sys.stdout = self.out



    def _finishIOCapture(self):
        """
        Restore stdout/stderr and return the captured data
        """
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__

        return self.out.getvalue()

    @staticmethod
    def findPlugins():
        """
        Goes throught the plugin directories, and adds
        existing unit test dirs
        """
        dirs = []

        for epoint in pkg_resources.iter_entry_points('indico.ext_types'):
            dirs.append(os.path.dirname(epoint.load().__file__))

        for epoint in pkg_resources.iter_entry_points('indico.ext'):
            dirs.append(os.path.dirname(epoint.load().__file__))

        return dirs

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

    def _writeReport(self, filename, content):
        """
        Write the test report, using the filename and content that are passed
        """
        filePath = os.path.join(self.setupDir, 'report', filename + ".txt")
        try:
            f = open(filePath, 'w')
            f.write(content)
            f.close()
        except IOError:
            return "Unable to write in %s, check your file permissions." % \
                    os.path.join(self.setupDir, 'report', filename + ".txt")

        self._info("report in %s" % filePath)

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

    def _callOptions(self, method, *args):
        """
        Invokes the option proxy, providing the hot spot with name 'method',
        that options should have extended
        """

        # invoke the option proxy
        self.options.call(self, method, *args)


# Some utils

class FakeMailServer(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data):
         logging.getLogger('indico.test.fake_smtp').info("mail from %s" % mailfrom)


class FakeMailThread(Thread):
    def __init__(self, addr):
        super(FakeMailThread, self).__init__()
        self.addr = addr
        self.server = FakeMailServer(self.addr, '')

    def run(self):
        asyncore.loop()

    def close(self):
        if self.server:
            self.server.close()

    def get_addr(self):
        return self.server.socket.getsockname()
