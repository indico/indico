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
This module defines the TestRunners that are included by default by indico.tests:

 * UnitTestRunner
 * FunctionalTestRunner
 * GridTestRunner
 * PylintTestRunner
 * JSLintTestRunner
 * JSUnitTestRunner

"""

# System modules
import commands, os, socket, subprocess, tempfile, threading

# Python stdlib
import time, urllib2

# Test modules
import nose, figleaf, figleaf.annotate_html
from selenium import selenium

from indico.tests.config import TestConfig
from indico.tests.base import BaseTestRunner, Option
from indico.tests.util import openBrowser, relpathto

__all__ = [
    'UnitTestRunner',
    'FunctionalTestRunner',
    'GridTestRunner',
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





class UnitTestRunner(BaseTestRunner):
    """
    Python Unit Tests

    Using nosetest
    """

    _runnerOptions = {'silent': Option,
                      'coverage': CoveragePythonTestOption,
                      'specify': Option}

    def _run(self):
        #coverage = CoverageTestRunner.getInstance()

        #if coverage:
        #    coverage.start()

        #retrieving tests from tests folder
        args = ['nose', '--nologcapture',  '--logging-clear-handlers', \
                '--with-id', '-v', '-s']

        specific = self.options.valueOf('specify')

        if specific:
            args.append("indico.tests.python.unit.%s" % specific)
        else:
            args.append(os.path.join(self.setupDir, 'python', 'unit'))
            # retrieving tests from plugins folder
            for folder in BaseTestRunner.walkThroughFolders(
                os.path.join(self.setupDir, '..', 'MaKaC', 'plugins'),
                "/tests/python/unit"):
                args.append(folder)

        result = nose.run(argv = args)

        #if coverage:
        #    coverage.stop()

        return result

    def walkThroughPluginsFolders(self):
        """
        Goes throught the plugin directories, and adds
        existing unit test dirs
        """
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'MaKaC',
                                       'plugins')
        foldersArray = []

        for root, __, ___ in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/unit") > 0:
                foldersArray.append(root)

        return foldersArray


class FunctionalTestRunner(BaseTestRunner):
    """
    Functional Tests

    Using selenium
    """

    _runnerOptions = {'silent': Option,
                      'record': Option,
                      'specify': Option}


    def __init__(self, **kwargs):
        BaseTestRunner.__init__(self, **kwargs)
        self.child = None

    def _runSeleniumCycle(self):
        """
        Run selenium over the existing test suite (or a specific test)
        """

        try:
            if not self._startSeleniumServer():
                return ('[ERR] Could not start functional tests because selenium'
                        ' server cannot be started.\n')

            args = ['nose', '--nologcapture', '--logging-clear-handlers',
                    '-v']

            specific = self.options.valueOf('specify')

            # if a particular test was specified
            if specific:
                args.append("indico.tests.python.functional.%s" % specific)
            else:
                args.append(os.path.join(self.setupDir, 'python', 'functional'))
                # retrieving tests from plugins folder
                for folder in BaseTestRunner.walkThroughFolders(
                    os.path.join(self.setupDir, '..', 'MaKaC', 'plugins'),
                    "/tests/python/functional"):
                    args.append(folder)

            result = nose.run(argv = args)

        except Exception, e:
            raise e
        finally:
            self._stopSeleniumServer()

        return result

    def _run(self):

        if self.options.valueOf('record'):
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

    def _startSeleniumServer(self):
        """
        starts the selenium server
        """
        started = True

        self._info("Starting Selenium Server")

        try:
            self.child = subprocess.Popen(["java", "-jar",
                                      os.path.join(self.setupDir,
                                                   'python',
                                                   'functional',
                                                   TestConfig.getInstance().
                                                   getSeleniumFilename())],
                                      stdout=None)

        except OSError, e:
            return ("[ERR] Could not start selenium server - command \"java\""
                    " needs to be in your PATH. (%s)\n" % e)
        except KeyError:
            return "[ERR] Please specify a SeleniumFilename in tests.conf\n"

        self._info("Starting Selenium RC")

        sel = selenium("localhost", 4444, "*firefox", "http://www.cern.ch/")
        for i in range(5):
            try:
                #testing if the selenium server has started
                time.sleep(1)
                sel.start()
                sel.stop()

                #server has started
                break
            except socket.error:
                print 'Selenium has not started yet. Attempt #%s\n' % (i+1)
                time.sleep(5)
        else:
            started = False

        return started

    def _stopSeleniumServer(self):
        """
        stops the selenium server
        """
        self.child.kill()


class GridEnvironmentRunner(threading.Thread):
    """
    Rspresents a specific grid environment (FF Linux, IE Windows, etc...)
    """

    def __init__(self, gridData, setupDir, resultEntry):
        threading.Thread.__init__(self)
        self.setupDir = setupDir
        self.gridData = gridData
        self.result = None
        self.resultEntry = resultEntry

    def run(self):

        self.result = nose.run(argv=['nose', '--nologcapture', '--nocapture',
                                     '--logging-clear-handlers', '-v',
                                     os.path.join(self.setupDir, 'python',
                                                  'functional')])

        self.resultEntry['success'] = self.result

    def stop(self):
        """
        Stop the GridEnvironmentRunner, by joining its thread
        """

        self.join()

        if self.result:
            return True
        else:
            return False

    @classmethod
    def getGridData(cls):
        """
        returns the data that is stored by the thread, if any
        """

        thread = threading.currentThread()

        if hasattr(thread, 'gridData'):
            return thread.gridData
        else:
            return None

class GridTestRunner(BaseTestRunner):
    """
    Selenium Grid Tests
    """

    _runnerOptions = {'silent': Option,
                      'parallel': Option,
                      'specify': Option }

    def __init__(self, **kwargs):

        BaseTestRunner.__init__(self, **kwargs)

        try:
            testConf = TestConfig.getInstance()
            self.hubEnv = testConf.getHubEnv()
            self.configExists = True
        except KeyError:
            self.configExists = False

        self.gridData = None
        specifiedEnv = self.options.valueOf('specify')

        if specifiedEnv:
            self.hubEnv = [specifiedEnv]

    def _runSerial(self, resultDict, testConf):
        """
        Run the tests one after the other
        """

        for envName in self.hubEnv:
            envRunner = self._runEnv(envName, resultDict, testConf)
            envRunner.stop()


    def _runParallel(self, resultDict, testConf):
        """
        Run all the tests at the same time
        """

        # launch every environment
        for envName in self.hubEnv:
            self._runEnv(envName, resultDict, testConf)

        # give it some time to start up
        time.sleep(1)

        # wait so that there are no more runner threads executing
        while(len(list(thread for thread in threading.enumerate()
                       if isinstance(thread, GridEnvironmentRunner))) > 0):
            time.sleep(1)


    def _runEnv(self, envName, resultDict, testConf):
        """
        Run a specific test environment, spawning a GridEnvironmentRunner
        """
        self._info("Starting env %s" % envName)

        self.gridData = GridData(testConf.getHubURL(),
                                 testConf.getHubPort(),
                                 envName,
                                 active = True)

        resultEntry = resultDict[envName] = {}

        envRunner = GridEnvironmentRunner(self.gridData, self.setupDir, resultEntry)
        envRunner.start()

        return envRunner


    def _run(self):

        resultDict = {}
        result = True

        if not self.configExists:
            return "[ERR] Grid - Please specify hub configuration in tests.conf\n"

        try:
            testConf = TestConfig.getInstance()

            # Ping server, just to know it is alive
            urllib2.urlopen("http://%s:%s/heartbeat" % (testConf.getHubURL(),
                                                        testConf.getHubPort()))

            if self.options.valueOf('parallel'):
                self._runParallel(resultDict, testConf)
            else:
                self._runSerial(resultDict, testConf)

            for name, resultEntry in resultDict.iteritems():
                if resultEntry['success']:
                    resultStr = 'OK'
                else:
                    resultStr = 'FAIL'
                    result = False
                print "%s\t %s" % (name, resultStr)

        except socket.error:
            self._error("[ERR] Selenium Grid - Connection refused, check your "
                        "hub's settings (%s:%s)" % \
                        (testConf.getHubURL(), testConf.getHubPort()))
            return False
        except urllib2.URLError, e:
            self._error("[ERR] Selenium Grid - Hub is probably down " \
                        "(%s:%s) (%s)\n" % \
                        (testConf.getHubURL(), testConf.getHubPort(), e))
            return False
        except Exception, e:
            self._error(e)
            return False

        return result

class GridData(object):
    """
    Provides informations for selenium grid, data are set from Class Grid
    and are used by seleniumTestCase.py.
    Because nosetest cannot forward the arguments to selenium grid.
    """

    def __init__(self, host, port, env, active = False):
        self.active = active
        self.host = host
        self.port = port
        self.env = env


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

            print jsTest

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
        import sets
        blackList = sets.Set(['pack', 'Loader.js', 'Common', 'i18n'])

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

