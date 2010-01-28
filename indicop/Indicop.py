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


import os
import sys
import nose
import figleaf
import figleaf.annotate_html
import subprocess
import socket
import time
import commands
import StringIO
import signal
from BaseTest import BaseTest
from selenium import selenium
from MaKaC.common.db import DBMgr
from MaKaC import user
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common import indexes
from util import TestZEOServer
import ZODB
from ZODB import FileStorage, DB
import transaction


class Unit(BaseTest):
    def run(self):
        returnString = ""
        self.startMessage("Starting Python unit tests")

        result = False

        try:
            coverage = Coverage.getInstance()
            if coverage != False:
                coverage.start()

            self.createDummyUser()

            #capturing the stderr
            outerr = StringIO.StringIO()
            sys.stderr = outerr


            #retrieving tests from Indicop folder
            args = ['nose', '--nologcapture', '--logging-clear-handlers', '-v', os.path.join(self.setupDir, 'python', 'unit')]
            #retrieving tests from plugins folder
            for folder in self.walkThroughFolders(os.path.join(self.setupDir,
                                                               '..',
                                                               'indico',
                                                               'MaKaC',
                                                               'plugins'),
                                                  "/tests/python/unit"):
                args.append(folder)

            result = nose.run(argv = args)

            #restoring the stderr
            sys.stderr = sys.__stderr__

            if coverage:
                returnString += coverage.stop()

            s = outerr.getvalue()
            returnString += self.writeReport("pyunit", s)
        finally:
            self.deleteDummyUser()

        if result:
            return returnString + "PY Unit tests succeeded\n"
        else:
            return returnString + \
                "[FAIL] Unit tests - report in indicop/report/pyunit.txt\n"

    def walkThroughPluginsFolders(self):
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'indico',
                                       'MaKaC',
                                       'plugins')
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/unit") > 0:
                foldersArray.append(root)

        return foldersArray

class Coverage(BaseTest):
    """This class is a singleton instantiate by Indicop class and
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
                             "report/pycoverage/index.html\n")

    def getInstance(cls):
        if cls.__instance == None:
            return False
        return cls.__instance
    getInstance = classmethod( getInstance )

    def instantiate(cls):
        cls.__instance = Coverage()
    instantiate = classmethod( instantiate )

class Functional(BaseTest):
    def __init__(self):
        self.child = None

    def run(self):
        returnString = ""
        self.startMessage("Starting Python functional tests")

        if not self.startSeleniumServer():
            return ('[ERR] Could not start functional tests because selenium'
                    ' server cannot be started.\n')

        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr

        #retrieving tests from Indicop folder
        args = ['nose', '--nologcapture', '--logging-clear-handlers', '-v', os.path.join(self.setupDir, 'python', 'functional')]
        #retrieving tests from plugins folder
        for folder in self.walkThroughFolders(os.path.join(self.setupDir,
                                                           '..',
                                                           'indico',
                                                           'MaKaC',
                                                           'plugins'),
                                              "/tests/python/functional"):
            args.append(folder)

        result = nose.run(argv = args)

        self.stopSeleniumServer()

        #restoring the stderr
        sys.stderr = sys.__stderr__

        s = outerr.getvalue()
        returnString += self.writeReport("pyfunctional", s)

        report = ""
        if result:
            report = returnString + "PY Functional tests succeeded\n"
        else:
            report = returnString + ("[FAIL] Functional tests - report in"
                    " indicop/report/pyfunctional.txt\n")
        return report

    def walkThroughPluginsFolders(self):
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'indico',
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
                                                   'selenium-server.jar')],
                                      stdout=subprocess.PIPE)
        except OSError, e:
            return ("[ERR] Could not start selenium server - command \"java\""
                    " needs to be in your PATH. (%s)\n" % e)

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

class Specify(Functional):
    def __init__(self, specifyArg):
        self.specify = specifyArg

    def run(self):
        self.startMessage("Starting Python specified tests")

        #Just in case we're dealing with functional tests
        if not self.startSeleniumServer():
            return ('[ERR] Could not start functional tests because selenium'
                    ' server cannot be started.\n')

        #running dthe test and ouputing in the console
        result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                           'python',
                                                           self.specify)])

        self.stopSeleniumServer()

        if result:
            return "Specified Test - Succeeded\n"
        else:
            return "[FAIL] Specified Test - read output from console\n"

class Grid(BaseTest):
    def __init__(self, hubUrl, hubPort, hubEnv):
        self.hubEnv = hubEnv
        self.gridData = GridData.getInstance()
        self.gridData.setUrl(hubUrl)
        self.gridData.setPort(hubPort)
        self.gridData.setActive(False)

    def run(self):
        self.startMessage("Starting grid tests")

        self.gridData.setActive(True)

        #Checking if hub is online
        sel = selenium(self.gridData.getUrl(), self.gridData.getPort(),
                       self.hubEnv[0], "http://www.cern.ch/")
        selTimeout = TimeoutFunction(sel.start, 10)
        try:
            selTimeout()
        except TimeoutFunctionException:
            return "[FAIL] Selenium Grid - Hub is probably down (%s:%s)" % \
                    (self.gridData.getUrl(), self.gridData.getPort())
        else:
            print "Hub is UP, continue with grid tests"


        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr

        returnString = ""
        for env in self.hubEnv:
            self.gridData.setEnv(env)
            sys.stderr.write('\n~ %s ~\n' % env)
            result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                               'python',
                                                               'functional')])
            if result:
                returnString += "PY Functional (%s) tests succeeded\n" % env
            else:
                returnString += ("[FAIL] Functional (%s) tests - report in "
                        " indicop/report/pygrid.txt\n") % env

        #restoring the stderr
        sys.stderr = sys.__stderr__

        s = outerr.getvalue()
        returnString += self.writeReport("pygrid", s)

        return returnString


class GridData(BaseTest):
    """Provide informations for selenium grid, data are set from Class Grid
    and are used by seleniumTestCase.py.
    Because nosetest cannot forward the arguments to selenium grid."""

    __instance = None
    def __init__(self):
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

    def getInstance(cls):
        if cls.__instance == None:
            cls.__instance = GridData()
        return cls.__instance

    getInstance = classmethod( getInstance )


class TimeoutFunctionException(Exception):
    """Exception to raise on a timeout"""
    pass

class TimeoutFunction:

    def __init__(self, function, timeout):
        self.timeout = timeout
        self.function = function

    def handle_timeout(self, signum, frame):
        raise TimeoutFunctionException()

    def __call__(self, *args):
        old = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        try:
            result = self.function(*args)
        finally:
            signal.signal(signal.SIGALRM, old)
        signal.alarm(0)
        return result


class Pylint(BaseTest):
    def run(self):
        returnString = ""
        self.startMessage("Starting pylint tests")

        statusOutput = commands.getstatusoutput("pylint --rcfile=%s %s" %
                                                (os.path.join(self.setupDir,
                                                              'python',
                                                              'pylint',
                                                              'pylint.conf'),
                                                os.path.join(self.setupDir,
                                                             '..',
                                                             'indico',
                                                             'MaKaC', 'conference.py')))
        if statusOutput[1].find("pylint: not found") > -1:
            return ("[ERR] Could not start Source Analysis - "
                    "command \"pylint\" needs to be in your PATH. (%s)\n" %
                                                                statusOutput[1])
        else:
            returnString += self.writeReport("pylint", statusOutput[1])
            return returnString + "PY Lint - report in indicop/report/pylint.txt\n"


class Jsunit(BaseTest):
    def __init__(self, jsSpecify, jsCoverage):
        self.coverage = jsCoverage
        self.specify = jsSpecify

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
                                                    'JsTestDriver-1.2.jar'),
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
                                             "JsTestDriver-1.2.jar"
                                             " --config "
                                             "%s"
                                             " --tests Fake.dryRun") % confFile)
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


            #running tests
            jsTest = commands.getstatusoutput(("java -jar "
                                             "JsTestDriver-1.2.jar "
                                             "--config "
                                             "%s "
                                             "--tests %s "
                                             "--testOutput %s") %
                                             (confFile, toTest, coveragePath))

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
                                     "indicop/report/jscoverage/index.html\n")

            #delete built conf file
            os.unlink(confFile)

            #restoring directory
            os.chdir(self.setupDir)

            report = ""
            if self.specify:
                #ouputing directly in the console
                print jsTest[1]
                report = "JS Unit Tests - Output in console\n"
            else:
                report += self.writeReport("jsunit", jsTest[1])
                report += ("JS Unit Tests - report in "
                          "indicop/report/jsunit.txt\n")
        except OSError, e:
            return ("[ERR] Could not start js-test-driver server - command "
                    "\"java\" needs to be in your PATH. (%s)\n" % e)

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

        #lines needed to activate coverage plugin
        coverageConf = """\nplugin:
  - name: \"coverage\"
    jar: \"plugins/coverage-1.2.jar\"
    module: \"com.google.jstestdriver.coverage.CoverageModule\""""


        try:
            #retrieve and store the template file
            f = open(confTemplatePath)
            confTemplate = f.read()
            f.close()

            #adding tests files from Indicop folder
            for root, dirs, files in os.walk(absoluteTestsFolder):
                for name in files:
                    if name.endswith(".js"):
                        absoluteFilePath = os.path.join(root, name)
                        splitPath = absoluteFilePath.split(relativeTestsFolder)
                        relativeFilePath = relativeTestsFolder + splitPath[1]

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

class Jslint(BaseTest):
    def run(self):
        returnString = ""
        self.startMessage("Starting jslint tests")

        #Folders which are going to be scanned.
        #Files are going to be find recursively in these folders
        folderNames = ['Admin', 'Collaboration', 'Core', 'Display', 'Legacy',
                       'Management', 'MaterialEditor', 'Timetable']

        outputString = ""

        #checking if rhino is accessible
        statusOutput = commands.getstatusoutput("rhino -?")
        if statusOutput[1].find("rhino: not found") > -1:
            return ("[ERR] Could not start JS Source Analysis - command "
                    "\"rhino\" needs to be in your PATH. (%s)\n" % statusOutput[1])

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
        return returnString + "JS Lint - report in indicop/report/jslint.txt\n"

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


class Indicop(object):

    def __init__(self, jsspecify, jscoverage):

        #MODIFY ACCORDINGLY TO YOUR SELENIUM GRID INSTALLATION
        self.gridUrl = "macuds01.cern.ch"
        self.gridPort = 4444
        self.gridEnv = ["Firefox on OS X",
                        "Safari on OS X"]

        #variables for jsunit
        self.jsSpecify = jsspecify
        self.jsCoverage = jscoverage

        #define the set of tests
        self.testsDict = {'unit': Unit(),
                 'functional': Functional(),
                 'pylint': Pylint(),
                 'jsunit': Jsunit(self.jsSpecify, self.jsCoverage),
                 'jslint': Jslint(),
                 'grid': Grid(self.gridUrl, self.gridPort, self.gridEnv)}


    def main(self, specify, coverage, testsToRun):

        returnString = "\n\n=============== ~INDICOP SAYS~ ===============\n\n"

        self.startDB()

        if coverage:
            Coverage.instantiate()

        #specified test can either be unit or functional.
        if specify:
            returnString += Specify(specify).run()
        else:
            for test in testsToRun:
                try:
                    returnString += self.testsDict[test].run()
                except KeyError:
                    returnString += ("[ERR] Test %s does not exist. "
                      "It has to be added in the testsDict variable\n") % test

        self.stopDB()

        return returnString


    def startDB(self):
        zeoPort = 9686
        self.createNewDBFile()
        self.zeoServer = self.createDBServer("/tmp/indicop/Data.fs", zeoPort)
        print ("zodb server started on pid: " + str(self.zeoServer) + " .")
        print ("Creating a CustomDBMgr on port " + str(zeoPort))
        self.cdbmgr = DBMgr.getInstance(hostname="localhost", port=zeoPort)
        print ("Starting a request ...")
        self.cdbmgr.startRequest()
        print ("Request started successfully.")
        self.cdbmgr.endRequest(True)
        print ("Request ended successfully.")

    def stopDB(self):
        try:
            print ("Sending kill signal to ZEO Server at pid " + str(self.zeoServer) + " ...")
            os.kill(self.zeoServer, signal.SIGTERM)
            print ("Signal sent")
        except Exception, e:
            print ("Problem sending kill signal: " + str(e))

        try:
            print ("Waiting for ZEO Server to finish ...")
            os.wait()
            print ("Zodb server finished.")
        except Exception, e:
            print ("Problem waiting for ZEO Server: " + str(e))

        self.removeDBFile()

    def createNewDBFile(self):
        savedDir = os.getcwd()
        try:
            os.mkdir("/tmp/indicop")
        except OSError:
            pass
        os.chdir("/tmp/indicop/")
        print "DONE"
        storage = FileStorage.FileStorage("Data.fs")
        print "DONE"
        db = DB(storage)
        print "DONE"
        connection = db.open()
        print "DONE"
        dbroot = connection.root()
        print "DONE"

        transaction.commit()

        connection.close()
        print "DONE"
        db.close()
        print "DONE"
        storage.close()
        print "DONE"
        os.chdir(savedDir)

    def removeDBFile(self):
        savedDir = os.getcwd()
        os.chdir("/tmp/indicop/")

        os.unlink("Data.fs")
        os.unlink("Data.fs.index")
        os.unlink("Data.fs.lock")
        os.unlink("Data.fs.tmp")

        os.chdir(savedDir)

    def createDBServer(self, file, port):
        pid = os.fork()
        if pid:
            return pid
        else:
            server = TestZEOServer(port, file)
            server.start()
