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
import os, commands, subprocess, sys

# Python stdlib
import time, re

# Test modules
import nose, figleaf, figleaf.annotate_html
from selenium import selenium

from indico.tests.config import TestConfig
from indico.tests.base import BaseTestRunner

class UnitTestRunner(BaseTestRunner):

    def run(self):
        returnString = ""
        self.startMessage("Starting Python unit tests")

        result = False

        coverage = CoverageTestRunner.getInstance()
        if coverage != False:
            coverage.start()

        self._startIOCapture()

        #retrieving tests from tests folder
        args = ['nose', '--nologcapture',  '--logging-clear-handlers', \
                '--with-id', '-v', '-s', os.path.join(self.setupDir, 'python', 'unit')]
        #retrieving tests from plugins folder
        for folder in self.walkThroughFolders(os.path.join(self.setupDir,
                                                           '..',
                                                           'MaKaC',
                                                           'plugins'),
                                              "/tests/python/unit"):
            args.append(folder)

        result = nose.run(argv = args)

        if not self.options['verbose']:
            # restoring the stderr
            s = self._finishIOCapture()[1]
            returnString += self.writeReport("pyunit", s)

        if coverage:
            returnString += coverage.stop()

        if result:
            return returnString + "PY Unit tests succeeded\n"
        else:
            return returnString + \
                "[FAIL] Unit tests - report in indico/tests/report/pyunit.txt\n"

    def walkThroughPluginsFolders(self):
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'MaKaC',
                                       'plugins')
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/unit") > 0:
                foldersArray.append(root)

        return foldersArray

class CoverageTestRunner(BaseTestRunner):
    """This class is a singleton instantiate by TestRunner class and
    used by Python Unit tests.
    """
    __instance = None

    def start(self):
        figleaf.start()

    def stop(self):
        figleaf.stop()
        coverageOutput = figleaf.get_data().gather_files()
        coverageDir = os.path.join(self.setupDir, 'report', 'pycoverage')
        try:
            figleaf.annotate_html.report_as_html(coverageOutput,
                                                 coverageDir, [], {})
        except IOError:
            os.mkdir(coverageDir)
            figleaf.annotate_html.report_as_html(coverageOutput,
                                                 coverageDir, [], {})
        return ("PY Coverage - Report generated in "
                             "tests/report/pycoverage/index.html\n")

    def getInstance(cls):
        if cls.__instance == None:
            return False
        return cls.__instance
    getInstance = classmethod( getInstance )

    def instantiate(cls):
        cls.__instance = Coverage()
    instantiate = classmethod( instantiate )


class FunctionalTestRunner(BaseTestRunner):

    def __init__(self, **kwargs):
        BaseTestRunner.__init__(self, **kwargs)
        self.child = None

    def run(self):
        returnString = ""
        self.startMessage("Starting Python functional tests")

        try:
            if not self.startSeleniumServer():
                return ('[ERR] Could not start functional tests because selenium'
                        ' server cannot be started.\n')

            self._startIOCapture()

            #retrieving tests from tests folder
            args = ['nose', '--nologcapture', '--logging-clear-handlers', '-v',
                    os.path.join(self.setupDir, 'python', 'functional')]
            #retrieving tests from plugins folder
            for folder in self.walkThroughFolders(os.path.join(self.setupDir,
                                                               '..',
                                                               'MaKaC',
                                                               'plugins'),
                                                  "/tests/python/functional"):
                args.append(folder)

            result = nose.run(argv = args)

        finally:
            self.stopSeleniumServer()

            #restoring the stderr
            sys.stderr = sys.__stderr__

        s = self._finishIOCapture()[1]
        returnString += self.writeReport("pyfunctional", s)

        report = ""
        if result:
            report = returnString + "PY Functional tests succeeded\n"
        else:
            report = returnString + ("[FAIL] Functional tests - report in"
                    " tests/report/pyfunctional.txt\n")
        return report

    def walkThroughPluginsFolders(self):
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'MaKaC',
                                       'plugins')
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/functional") > 0:
                foldersArray.append(root)

        return foldersArray

    def startSeleniumServer(self):
        started = True
        try:
            self.child = subprocess.Popen(["java", "-jar",
                                      os.path.join(self.setupDir,
                                                   'python',
                                                   'functional',
                                                   TestsConfig.getInstance().
                                                   getSeleniumFilename())],
                                      stdout=subprocess.PIPE)
        except OSError, e:
            return ("[ERR] Could not start selenium server - command \"java\""
                    " needs to be in your PATH. (%s)\n" % e)
        except KeyError:
            return "[ERR] Please specify a SeleniumFilename in tests.conf\n"

        sel = selenium("localhost", 4444, "*chrome", "http://www.cern.ch/")
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

    def stopSeleniumServer(self):
        self.child.kill()


class Specify(FunctionalTestRunner):
    def __init__(self, specifyArg):
        self.specify = specifyArg

    def run(self):
        self.startMessage("Starting Python specified tests")

        #if specified path does not contained unit, we are probably dealing
        #with functional tests
        if self.specify.find('unit/') < 0:
            if not self.startSeleniumServer():
                return ('[ERR] Could not start functional tests because selenium'
                        ' server cannot be started.\n')
            try:
                #running the test and ouputing in the console
                result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                                   '..',
                                                                   self.specify)])
            finally:
                self.stopSeleniumServer()
        else:
            #running the test and ouputing in the console
            result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                           '..',
                                                           self.specify)])

        if result:
            return "Specified Test - Succeeded\n"
        else:
            return "[FAIL] Specified Test - read output from console\n"

class TimeoutException(Exception):
    """SIGALARM was sent to the process"""
    pass

def raise_timeout(signum, frame):
    raise TimeoutException("15sec Timeout")


class GridTestRunner(BaseTestRunner):

    def __init__(self, **kwargs):

        BaseTestRunner.__init__(self, **kwargs)

        try:
            self.hubEnv = TestsConfig.getInstance().getHubEnv()
            self.gridData = GridData.getInstance()
            self.gridData.setUrl(TestsConfig.getInstance().getHubURL())
            self.gridData.setPort(TestsConfig.getInstance().getHubPort())
            self.gridData.setActive(False)
            self.configExists = True
        except KeyError:
            self.configExists = False

    def run(self):
        self.startMessage("Starting grid tests")

        if not self.configExists:
            return "[ERR] Grid - Please specify hub configuration in tests.conf\n"

        try:
            try:
                self.gridData.setActive(True)

                #Checking if hub is online
                sel = selenium(self.gridData.getUrl(), self.gridData.getPort(),
                               self.hubEnv[0], "http://www.cern.ch/")

                signal.signal(signal.SIGALRM, raise_timeout)
                signal.alarm(15)
                sel.start()
                sel.open("/")
                sel.stop()
                #disable the alarm signal
                signal.alarm(0)

                self._startIOCapture()

                returnString = ""
                for env in self.hubEnv:
                    self.gridData.setEnv(env)
                    sys.stderr.write('\n~ %s ~\n' % env)
                    result = nose.run(argv=['nose', '--nologcapture',
                                            '--logging-clear-handlers', '-v',
                                            os.path.join(self.setupDir,
                                                         'python',
                                                         'functional')])
                    if result:
                        returnString += "PY Functional (%s) tests succeeded\n" % env
                    else:
                        returnString += ("[FAIL] Functional (%s) tests - report in"
                                " tests/report/pygrid.txt\n") % env

                s = self._finishIOCapture()[1]

                returnString += self.writeReport("pygrid", s)
            except socket.error:
                return ("[ERR] Selenium Grid - Connection refused, check your "
                        "hub's settings (%s:%s)") % \
                        (self.gridData.getUrl(), self.gridData.getPort())
            except TimeoutException, e:
                return "[ERR] Selenium Grid - Hub is probably down (%s:%s) (%s)\n" % \
                        (self.gridData.getUrl(), self.gridData.getPort(), e)
        finally:
            #disable alarm
            signal.alarm(0)

        return returnString

class GridDataTestRunner(BaseTestRunner):
    """Provide informations for selenium grid, data are set from Class Grid
    and are used by seleniumTestCase.py.
    Because nosetest cannot forward the arguments to selenium grid."""

    __instance = None
    def __init__(self, **kwargs):
        BaseTestRunner.__init__(self, **kwargs)
        self.active = None
        self.url = None
        self.port = None
        self.active = None
        self.currentEnv = None

    def isActive(self):
        return self.active
    def getUrl(self):
        return self.url
    def getPort(self):
        return self.port
    def getEnv(self):
        return self.currentEnv

    def setActive(self, active):
        self.active = active
    def setUrl(self, url):
        self.url = url
    def setPort(self, port):
        self.port = port
    def setEnv(self, env):
        self.currentEnv = env

    @classmethod
    def getInstance(cls):
        if cls.__instance == None:
            cls.__instance = GridData()
        return cls.__instance


class PylintTestRunner(BaseTestRunner):
    def run(self):
        returnString = ""
        self.startMessage("Starting pylint tests")

        self._startIOCapture()

        baseDir = os.path.join(self.setupDir, '..')

        filePaths = map(lambda s: s.replace('.', os.sep)+".py",
                        TestConfig.getInstance().getPylintFiles())

        fileList = list(os.path.join(baseDir, f) for f in filePaths)

        try:
            pylintProcess = subprocess.Popen(
                ["pylint", "--rcfile=%s" % os.path.join(self.setupDir,
                                                         'python',
                                                         'pylint',
                                                         'pylint.conf'),
                ] + fileList,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT)

            self._redirectPipeToStdout(pylintProcess.stdout)
        except OSError, e:
            self._finishIOCapture()
            return ("[ERR] Could not start Source Analysis - "
                    "command \"pylint\" needs to be in your PATH. (%s)\n" % e)

        statusOutput = self._finishIOCapture()

        returnString += self.writeReport("pylint", statusOutput[0])
        return returnString + "PY Lint - report in indico/tests/report/pylint.txt\n"


class JSUnitTestRunner(BaseTestRunner):

    def __init__(self, **kwargs):
        BaseTestRunner.__init__(self, **kwargs)
        self.coverage = self.options['coverage']
        self.specify = self.options['specify']

    def run(self):
        self.startMessage("Starting Javascript unit tests")

        #conf file used at run time
        confFile = ("builtConf.conf")
        #path relative to the jar file
        coveragePath = os.path.join('..', '..', 'report', 'jscoverage')

        try:
            #Starting js-test-driver server
            server = subprocess.Popen(["java", "-jar",
                                       os.path.join(self.setupDir,
                                                    'javascript',
                                                    'unit',
                                                    TestsConfig.getInstance().
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
            success = self.buildConfFile(confFile, self.coverage)
            if not (success == ""):
                return success

            #switching directory to run the tests
            os.chdir(os.path.join(self.setupDir, 'javascript', 'unit'))

            #check if server is ready
            for i in range(5):
                jsDryRun = commands.getstatusoutput(("java -jar "
                                             "%s"
                                             " --config "
                                             "%s"
                                             " --tests Fake.dryRun") %\
                                             (TestsConfig.getInstance().
                                              getJSUnitFilename(),
                                              confFile))
                if jsDryRun[1].startswith("No browsers were captured"):
                    print ("Js-test-driver server has not started yet. "
                           "Attempt #%s\n") % (i+1)
                    time.sleep(5)
                else:
                    #server is ready
                    break
            else:
                return ('[ERR] Could not start js unit tests because '
                        'js-test-driver server cannot be started.\n')

            #setting tests to run
            toTest = ""
            if self.specify:
                toTest = self.specify
            else:
                toTest = "all"

            command = ("java -jar %s "
                            "--config %s "
                            "--tests %s ") % \
                            (TestsConfig.getInstance().getJSUnitFilename(),
                             confFile,
                             toTest)
            if self.coverage:
                command += "--testOutput %s" % coveragePath

            #running tests
            jsTest = commands.getoutput(command)

            coverageReport = ""
            if self.coverage:
                #generate html for coverage
                genOutput = commands.getstatusoutput("genhtml -o %s %s" %
                                                    (os.path.join('..',
                                                                '..',
                                                                'report',
                                                                'jscoverage'),
                                                    os.path.join('..',
                                                                 '..',
                                                                 'report',
                                                                 'jscoverage',
                                           '%s-coverage.dat' % confFile)))

                if genOutput[1].find("genhtml") > -1:
                    coverageReport = ("[ERR] JS Unit Tests - html coverage "
                                      "generation failed, genhtml needs to be "
                                      "in your PATH. (%s)\n" % genOutput[1])
                else:
                    coverageReport = ("JS Coverage - generated in "
                                     "tests/report/jscoverage/index.html\n")

            #delete built conf file
            os.unlink(confFile)

            #restoring directory
            os.chdir(self.setupDir)

            report = ""
            if self.specify:
                #ouputing directly in the console
                print jsTest
                report = "JS Unit Tests - Output in console\n"
            else:
                report += self.writeReport("jsunit", jsTest)

                #check if all tests succedded
                successRegexp = re.compile('(.|\n)*\nTotal\s[0-9]+\stests\s\(Passed:\s[0-9]+;\sFails:\s0;\sErrors:\s0\).*\n(.|\n)*')
                success = successRegexp.match(jsTest)
                if not success:
                    report += ("[FAIL] JS Unit Tests - report in "
                          "tests/report/jsunit.txt\n")
                else:
                    report += ("JS Unit tests succeeded\n")
        except OSError, e:
            return ("[ERR] Could not start js-test-driver server - command "
                    "\"java\" needs to be in your PATH. (%s)\n" % e)
        except KeyError:
            return "[ERR] Please specify a JSUnitFilename in tests.conf\n"

        #stopping the server
        server.kill()
        return coverageReport + report

    def buildConfFile(self, confFilePath, coverage):
        confTemplatePath = os.path.join(self.setupDir,
                                        'javascript',
                                        'unit',
                                        'confTemplate.conf')

        relativeTestsFolder = os.path.join("tests")
        absoluteTestsFolder = os.path.join(self.setupDir,
                                           "javascript",
                                           "unit",
                                           "tests")

        relativePluginsFolder = os.path.join("..", "indico", "MaKaC", "plugins")
        absolutePluginsFolder = os.path.join(self.setupDir,
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
        TestsConfig.getInstance().getJscoverageFilename()
        except KeyError:
            return "[ERR] Please, specify a JscoverageFilename in tests.conf\n"


        try:
            #retrieve and store the template file
            f = open(confTemplatePath)
            confTemplate = f.read()
            f.close()

            #adding tests files from tests folder
            for root, dirs, files in os.walk(absoluteTestsFolder):
                for name in files:
                    if name.endswith(".js"):
                        absoluteFilePath = os.path.join(root, name)
                        splitPath = absoluteFilePath.split(relativeTestsFolder)
                        relativeFilePath = relativeTestsFolder + splitPath[2]

                        confTemplate += "\n  - %s" % os.path.join(relativeFilePath)


            #adding plugins test files
            for root, dirs, files in os.walk(absolutePluginsFolder):
                for name in files:
                    if name.endswith(".js") and \
                                          root.find("/tests/javascript/unit") > 0:
                        absoluteFilePath = os.path.join(root, name)
                        splitPath = absoluteFilePath.split(relativePluginsFolder)
                        relativeFilePath = relativePluginsFolder + splitPath[1]

                        confTemplate += "\n  - %s" % os.path.join('..',
                                                                  '..',
                                                                  relativeFilePath)

            #addind coverage if necessary
            if coverage:
                confTemplate += coverageConf

            #writing the compelete configuration in a file
            confFile = open(os.path.join(self.setupDir, 'javascript', 'unit',
                                         confFilePath), 'w')
            confFile.write(confTemplate)
            confFile.close()

            return ""
        except IOError, e:
            return "[ERR] JS Unit Tests - Could not open a file. (%s)" % e

class JSLintTestRunner(BaseTestRunner):

    def run(self):
        returnString = ""
        self.startMessage("Starting jslint tests")

        #Folders which are not going to be scanned.
        #Files are going to be find recursively in the other folders
        import sets
        blackList = sets.Set(['pack', 'Loader.js', 'Common', 'i18n'])

        outputString = ""

        #checking if rhino is accessible
        statusOutput = commands.getstatusoutput("rhino -?")
        if statusOutput[1].find("rhino: not found") > -1:
            return ("[ERR] Could not start JS Source Analysis - command "
                    "\"rhino\" needs to be in your PATH. (%s)\n" % statusOutput[1])

        #constructing a list of folders to scan
        folderNames = []
        list  = os.listdir(os.path.join(self.setupDir,
                                        '..',
                                        'indico',
                                        'htdocs',
                                        'js',
                                        'indico'))
        for name in list:
            if not (name in blackList):
                folderNames.append(name)

        #Scanning Indico core
        for folderName in folderNames:
            outputString += self.walkThroughFolders(os.path.join(
                                                          self.setupDir,
                                                          '..',
                                                          'indico',
                                                          'htdocs',
                                                          'js',
                                                          'indico'),
                                                    folderName)

        #Scanning plugins js files
        outputString += self.walkThroughFolders(os.path.join(
                                                          self.setupDir,
                                                          '..',
                                                          'indico',
                                                          'MaKaC',
                                                          'plugins'))

        returnString += self.writeReport("jslint", outputString)
        return returnString + "JS Lint - report in tests/report/jslint.txt\n"

    def walkThroughFolders(self, path, folderRestriction=''):
        returnString = ""
        for root, dirs, files in os.walk(os.path.join(self.setupDir,
                                                      path,
                                                      folderRestriction)):
            for name in files:
                if name.endswith(".js"):
                    filename = os.path.join(root, name)
                    returnString += ("\n================== Scanning %s "
                                     "==================\n") % filename
                    output = commands.getstatusoutput("rhino %s %s" %
                                                      (os.path.join(
                                                                self.setupDir,
                                                                'javascript',
                                                                'jslint',
                                                                'jslint.js'),
                                                                filename))
                    returnString += output[1]
        return returnString
