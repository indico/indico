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
This module defines the TestRunners that are included by default by indico.tests:

 * UnitTestRunner
 * FunctionalTestRunner
 * GridTestRunner
 * PylintTestRunner
 * JSLintTestRunner
 * JSUnitTestRunner

"""

# System modules
import commands, os, socket, subprocess, tempfile, threading, multiprocessing

# Python stdlib
import time, urllib2

# Test modules
import figleaf
import figleaf.annotate_html
from selenium import webdriver
import nose

from indico.tests.config import TestConfig
from indico.tests.base import BaseTestRunner, Option
from indico.tests.util import openBrowser, relpathto
from indico.tests import default_actions
from indico.core.db import DBMgr

# legacy indico modules
from indico.core.config import Config

__all__ = [
    'UnitTestRunner',
    'FunctionalTestRunner',
    'PylintTestRunner',
    'JSLintTestRunner',
    'JSUnitTestRunner'
    ]

JSTEST_CFG_FILE = "builtConf.conf"


class CoverageBaseTestOption(Option):
    """
    This class can be used in order to add an
    optional code coverage analysis
    """

    def __init__(self, value):
        Option.__init__(self, value)
        self.coverageDir = None

    def final_message(self, __):
        """
        just a short message
        """
        self._info("Code coverage report generated at "
                   "%s/index.html\n" % self.coverageDir)

    def shouldExecute(self):
        return self.value


class CoveragePythonTestOption(CoverageBaseTestOption):
    """
    Python Coverage Tests
    """

    def __init__(self, value):
        CoverageBaseTestOption.__init__(self, value)

    def pre_run(self, __):
        """
        starts figleaf
        """

        figleaf.start()

    def post_run(self, runner):
        """
        stops figleaf and returns a report
        """

        figleaf.stop()
        coverageOutput = figleaf.get_data().gather_files()
        self.coverageDir = os.path.join(runner.setupDir, 'report', 'pycoverage')

        # check if there's a dir first
        if not os.path.exists(self.coverageDir):
            os.mkdir(self.coverageDir)

        figleaf.annotate_html.report_as_html(coverageOutput,
                                             self.coverageDir, [], {})

        # open a browser window with the report
        openBrowser(runner.config.getBrowserPath(), os.path.join(
            self.coverageDir, "index.html"))



class LogToConsoleTestOption(Option):
    """
    Python Coverage Tests
    """

    def __init__(self, value):
        super(LogToConsoleTestOption, self).__init__(value)

    def pre_run(self, __):
        """
        sets up logging
        """

        import logging
        h = logging.StreamHandler()
        logger = logging.getLogger('')

        logger.setLevel(getattr(logging, self.value))

        # add multiprocessing info
        multiprocessing.get_logger().addHandler(h)

        logger.addHandler(h)
        formatter = logging.Formatter("[%(process)d:%(threadName)s] %(asctime)s - %(name)s - %(levelname)s - %(message)s")
        h.setFormatter(formatter)

    def shouldExecute(self):
        # execute it as long as it is specified
        return not not self.value


class XMLOutputOption(Option):

    def use_xml_output(self, obj, fname, args):

        if self.value:
            if not os.path.exists('build'):
                os.makedirs('build')
            args += ['--with-xunit', '--xunit-file=build/%s-results.xml' % fname]
        else:
            args += ['-v']


class NoseTestRunner(BaseTestRunner):

    def _buildArgs(self):
        args = ['nose', '--nologcapture', '--logging-clear-handlers', \
                '--with-id', '-s']

        # will set args
        self._callOptions('use_xml_output', 'unit', args)

        specific = self.options.valueOf('specify')

        if specific:
            args.append(specific)
        else:
            args.append(os.path.join(self.setupDir, self._defaultPath))

        return args


class UnitTestRunner(NoseTestRunner):
    """
    Python Unit Tests

    Using nosetest
    """

    _defaultPath = os.path.join('python', 'unit')
    _runnerOptions = {'silent': Option,
                      'coverage': CoveragePythonTestOption,
                      'specify': Option,
                      'log': LogToConsoleTestOption,
                      'xml': XMLOutputOption }

    def _buildArgs(self):
        args = NoseTestRunner._buildArgs(self)

        if not self.options.valueOf('specify'):
            #TODO: Make more general for functional test.
            # add plugins
            args += BaseTestRunner.findPlugins()
        return args

    def _run(self):
        args = self._buildArgs()
        return nose.run(argv = args)


class FunctionalTestRunner(NoseTestRunner):
    """
    Functional Tests

    Using selenium
    """

    _defaultPath = os.path.join('python', 'functional')
    _runnerOptions = {'silent': Option,
                      'record': Option,
                      'browser': Option,
                      'mode': Option,
                      'server_url': Option,
                      'specify': Option,
                      'xml': XMLOutputOption}


    def __init__(self, **kwargs):
        BaseTestRunner.__init__(self, **kwargs)
        self.child = None

    def _runSeleniumCycle(self):
        """
        Run selenium over the existing test suite (or a specific test)
        """
        test_config = TestConfig.getInstance()


        mode = self.options.valueOf('mode', test_config.getRunMode())

        browser = self.options.valueOf('browser')
        if browser:
            browsers = [browser]
        elif mode == 'local':
            browsers = [test_config.getStandaloneBrowser()]
        else:
            browsers = test_config.getGridBrowsers()

        args = self._buildArgs()

        # Execute the tests
        result = True

        os.environ['INDICO_TEST_MODE'] = mode or ''
        os.environ['INDICO_TEST_URL'] = self.options.valueOf('server_url') or ''

        for browser in browsers:
            os.environ['INDICO_TEST_BROWSER'] = browser
            testResult = nose.run(argv=args)
            result = result and testResult
            self._info("%s: %s\n" % \
                       (browser, testResult and 'OK' or 'Error'))

        return result

    def _run(self):
        if self.options.valueOf('record'):
            dbi = DBMgr.getInstance()

            dbi.startRequest()
            conn = dbi.getDBConnection()

            default_actions.initialize_new_db(conn.root())
            default_actions.create_dummy_users()
            dbi.endRequest()

            raw_input("Press [ENTER] to finish recording... ")
            result = False

        else:
            result = self._runSeleniumCycle()

        return result

    def walkThroughPluginsFolders(self):
        """
        Goes throught the plugin directories, and adds
        existing functional test dirs
        """
        rootPluginsPath = os.path.join(self.setupDir, '..', 'MaKaC', 'plugins')
        foldersArray = []

        for root, __, ___ in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/functional") > 0:
                foldersArray.append(root)

        return foldersArray


class HTMLOption(Option):
    """
    Represents the option that allows HTML reports to be generated
    instead of console output
    """

    def __init__(self, value):

        Option.__init__(self, value)
        self.tmpFile = None

    def prepare_outstream(self, runner):
        """
        Forward the output to either a file or the process output
        """

        if self.value:
            __, filePath = tempfile.mkstemp()
            self.tmpFile = open(filePath, 'w+b')
            runner.outStream = self.tmpFile
        else:
            # for regular text, just use a pipe
            runner.outStream = subprocess.PIPE

    def write_report(self, runner, fileName, content):
        """
        Open the browser or write an actual report, depending on the state
        of the option
        """
        if self.value:
            self.tmpFile.close()
            # open a browser window with the report
            openBrowser(runner.config.getBrowserPath(), self.tmpFile.name)
        else:
            # for non-html output, use the normal mechanisms
            runner.writeNormalReport(fileName, content)


class PylintTestRunner(BaseTestRunner):
    """
    Pylint
    """

    _runnerOptions = {'silent': Option,
                      'html': HTMLOption}

    def __init__(self, **kwargs):

        BaseTestRunner.__init__(self, **kwargs)
        self.outStream = None

    def _run(self):

        fileList = self.config.getPylintFiles()

        try:
            # while we have MaKaC, we have to keep this extra path
            extraPath = os.path.join(self.setupDir, '..')
            os.environ['PYTHONPATH'] = "%s:%s" % (extraPath,
                                                  os.environ.get('PYTHONPATH',''))

            # Prepare the args for Pylint
            args = ["pylint", "--rcfile=%s" %
                    os.path.join(self.setupDir,
                                 'python',
                                 'pylint',
                                 'pylint.conf')
                    ] + fileList

            if self.options.valueOf('html'):
                args += ['-f', 'html']

            # will set self.outStream
            self._callOptions('prepare_outstream')

            pylintProcess = subprocess.Popen(
                args,
                stdout = self.outStream,
                stderr = subprocess.PIPE)

            # for regular aoutput, redirect the out pipe to stdout
            if not self.options.valueOf('html'):
                self._redirectPipeToStdout(pylintProcess.stdout)

            # stderr always goes to the same place
            self._redirectPipeToStdout(pylintProcess.stderr)

            # wait pylint to finish
            pylintProcess.wait()

        except OSError, e:
            self._error("[ERR] Could not start Source Analysis - "
                        "command \"pylint\" needs to be in your PATH. (%s)\n" % e)
            return False

        return True

    def _writeReport(self, fileName, content):

        # overloaded just to handle the case of HTML reports
        self._callOptions('write_report', fileName, content)

    def writeNormalReport(self, fileName, content):
        """
        Just call the parent report writing method
        (used from HTMLOption)
        """
        BaseTestRunner._writeReport(self, fileName, content)


class CoverageJSTestOption(CoverageBaseTestOption):
    """
    Python Coverage Tests
    """

    def __init__(self, value):
        CoverageBaseTestOption.__init__(self, value)

    def post_run(self, runner):
        """
        Creates a coverage report in HTML
        """

        #generate html for coverage

        reportPath = os.path.join(runner.setupDir, 'report', 'jscoverage')
        genOutput = commands.getstatusoutput(
            "genhtml -o %s %s" % (reportPath,
                                  os.path.join(reportPath,
                                               '%s-coverage.dat' %
                                               JSTEST_CFG_FILE)))

        self.coverageDir = reportPath

        if genOutput[1].find("genhtml") > -1:
            BaseTestRunner._error("JS Unit Tests - html coverage "
                                  "generation failed, genhtml needs to be "
                                  "in your PATH. (%s)\n" % genOutput[1])
        else:
            BaseTestRunner._info("JS Coverage - report generated\n")
            # open a browser window with the report
            openBrowser(runner.config.getBrowserPath(), os.path.join(
                reportPath, "index.html"))


class JSUnitTestRunner(BaseTestRunner):
    """
    JS Unit Tests

    Based on JSUnit
    """

    _runnerOptions = {'silent': Option,
                      'coverage': CoverageJSTestOption,
                      'specify': Option}

    def __init__(self, **kwargs):
        BaseTestRunner.__init__(self, **kwargs)
        self.coverage = self.options.valueOf('coverage')
        self.specify = self.options.valueOf('specify')

    def _run(self):

        #conf file used at run time

        try:
            #Starting js-test-driver server
            server = subprocess.Popen(["java", "-jar",
                                       os.path.join(self.setupDir,
                                                    'javascript',
                                                    'unit',
                                                    TestConfig.getInstance().
                                                    getJSUnitFilename()),
                                        "--port",
                                        "9876",
                                        "--browser",
                                        "firefox"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            time.sleep(2)

            #constructing conf file depending on installed plugins and
            #coverage activation

            success = self.buildConfFile(JSTEST_CFG_FILE, self.coverage)

            if success != "":
                self._error(success)
                return False

            #switching directory to run the tests
            os.chdir(os.path.join(self.setupDir, 'javascript', 'unit'))

            #check if server is ready
            for i in range(5):
                jsDryRun = commands.getstatusoutput(("java -jar "
                                             "%s"
                                             " --config "
                                             "%s"
                                             " --tests Fake.dryRun") %\
                                             (TestConfig.getInstance().
                                              getJSUnitFilename(),
                                              JSTEST_CFG_FILE))

                # Not very nice error checking, but how to do it nicely?
                if "browsers" in jsDryRun[1] or \
                    "Connection refused" in jsDryRun[1]:
                    print "Js-test-driver server has not started yet. " \
                          "Attempt #%s\n" % (i+1)
                    time.sleep(5)
                else:
                    #server is ready
                    break
            else:
                raise Exception('Could not start js unit tests because '
                                'js-test-driver server cannot be started.\n')

            #setting tests to run
            toTest = ""
            if self.specify:
                toTest = self.specify
            else:
                toTest = "all"

            command = ("java -jar %s "
                            "--config %s "
                            "--verbose "
                            "--tests %s ") % \
                            (TestConfig.getInstance().getJSUnitFilename(),
                             JSTEST_CFG_FILE,
                             toTest)

            if self.coverage:
                # path relative to the jar file
                command += "--testOutput %s" % \
                           os.path.join('..', '..', 'report', 'jscoverage')

            #running tests
            jsTest = commands.getoutput(command)


            #delete built conf file
            os.unlink(JSTEST_CFG_FILE)

            #restoring directory
            os.chdir(self.setupDir)

        except OSError, e:
            self._error("[ERR] Could not start js-test-driver server - command "
                        "\"java\" needs to be in your PATH. (%s)\n" % e)
        except KeyError:
            self._error("[ERR] Please specify a JSUnitFilename in tests.conf\n")
        except Exception, e:
            self._error(e)
        finally:
            # stopping the server
            server.kill()

        return True

    def buildConfFile(self, confFilePath, coverage):
        """
        Builds a driver config file
        """
        confTemplateDir = os.path.join(self.setupDir,
                                        'javascript',
                                        'unit')
        confTemplatePath = os.path.join(confTemplateDir, 'confTemplate.conf')

        absoluteTestsDir = os.path.join(self.setupDir,
                                           "javascript",
                                           "unit",
                                           "tests")

        absolutePluginDir = os.path.join(self.setupDir,
                                            "..",
                                            "..",
                                            "indico",
                                            "MaKaC",
                                            "plugins")

        try:
            #lines needed to activate coverage plugin
            coverageConf = """\nplugin:
  - name: \"coverage\"
    jar: \"plugins/%s\"
    module: \"com.google.jstestdriver.coverage.CoverageModule\"""" % \
        TestConfig.getInstance().getJSCoverageFilename()
        except KeyError:
            return "Please, specify a JSCoverageFilename in tests.conf\n"


        try:
            #retrieve and store the template file
            f = open(confTemplatePath)
            confTemplate = f.read()
            f.close()

            #adding tests files from tests folder
            for root, __, files in os.walk(absoluteTestsDir):
                for name in files:
                    if name.endswith(".js"):
                        absoluteFilePath = os.path.join(root, name)
                        relativeFilePath = relpathto(confTemplateDir,
                                                     absoluteFilePath)

                        confTemplate += "\n  - %s" % os.path.join(relativeFilePath)


            #adding plugins test files
            for root, __, files in os.walk(absolutePluginDir):
                for name in files:
                    if name.endswith(".js") and \
                                          root.find("/tests/javascript/unit") > 0:
                        absoluteFilePath = os.path.join(root, name)
                        relativeFilePath = relpathto(confTemplateDir,
                                                     absoluteFilePath)

                        confTemplate += "\n  - %s" % os.path.join('..',
                                                                  '..',
                                                                  relativeFilePath)

            #addind coverage if necessary
            if coverage:
                confTemplate += coverageConf

            #writing the complete configuration in a file
            confFile = open(os.path.join(self.setupDir, 'javascript', 'unit',
                                         confFilePath), 'w')
            confFile.write(confTemplate)
            confFile.close()

            return ""
        except IOError, e:
            return "JS Unit Tests - Could not open a file. (%s)" % e

class JSLintTestRunner(BaseTestRunner):
    """
    JSLint
    """

    def _run(self):

        # Folders which are not going to be scanned.
        # Files are going to be find recursively in the other folders
        blackList = set(['pack', 'Loader.js', 'Common', 'i18n'])

        #checking if rhino is accessible
        statusOutput = commands.getstatusoutput("rhino -?")
        if statusOutput[1].find("rhino: not found") > -1:
            return ("[ERR] Could not start JS Source Analysis - command "
                    "\"rhino\" needs to be in your PATH. (%s)\n" % statusOutput[1])

        #constructing a list of folders to scan
        folderNames = []

        indicoDir = os.path.join(self.setupDir, '..', '..', 'indico')

        fileList  = os.listdir(os.path.join(indicoDir,
                                            'htdocs',
                                            'js',
                                            'indico'))
        for name in fileList:
            if not (name in blackList):
                folderNames.append(name)

        #Scanning Indico core
        for folderName in folderNames:
            self.runJSLint(
                os.path.join(indicoDir, 'htdocs', 'js', 'indico'),
                folderName)

        #Scanning plugins js files
        return self.runJSLint(
            os.path.join(indicoDir, 'MaKaC', 'plugins'))


    def runJSLint(self, path, folderRestriction=''):
        """
        runs the actual JSLint command
        """

        for root, __, files in os.walk(os.path.join(self.setupDir,
                                                    path,
                                                    folderRestriction)):
            for name in files:
                if name.endswith(".js"):
                    filename = os.path.join(root, name)
                    self._info("Scanning %s" % filename)
                    output = commands.getstatusoutput("rhino %s %s" %
                                                      (os.path.join(
                                                                self.setupDir,
                                                                'javascript',
                                                                'jslint',
                                                                'jslint.js'),
                                                       filename))
                    print output[1]

                    if output[0] != 0:
                        return False
        return True

