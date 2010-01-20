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
from selenium import selenium
from MaKaC.common.db import DBMgr
from MaKaC import user
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common import indexes

class BaseTest(object):
    #path to this current file
    setupDir = os.path.dirname(__file__)
    
    def __init__(self):
        self.al = None
        self.ah = None
        self.avatar = None
        self.ih = None
    
    def writeReport(self, filename, content):
        f = open(os.path.join(self.setupDir, 'report', filename + ".txt"), 'w')
        f.write(content)
        f.close()
        
    def createDummyUser(self):
        DBMgr.getInstance().startRequest()
        
        #filling info to new user
        self.avatar = user.Avatar()
        self.avatar.setName( "fake" )
        self.avatar.setSurName( "fake" )
        self.avatar.setOrganisation( "fake" )
        self.avatar.setLang( "en_US" )
        self.avatar.setEmail( "fake@fake.fake" )
        
        #registering user
        self.ah = user.AvatarHolder()
        self.ah.add(self.avatar)
        
        #setting up the login info
        li = user.LoginInfo( "dummyuser", "dummyuser" )
        self.ih = AuthenticatorMgr()
        userid = self.ih.createIdentity( li, self.avatar, "Local" )
        self.ih.add( userid )
        
        #activate the account
        self.avatar.activateAccount()
        
        #since the DB is empty, we have to add dummy user as admin
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        self.al = minfo.getAdminList()
        self.al.grant( self.avatar )
        
        DBMgr.getInstance().endRequest()
        
    def deleteDummyUser(self):
        DBMgr.getInstance().startRequest()
        
        #removing user from admin list
        self.al.revoke( self.avatar )
        
        #remove the login info
        userid = self.avatar.getIdentityList()[0]
        self.ih.removeIdentity(userid)
        
        #unregistering the user info
        index = indexes.IndexesHolder().getById("email")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("name")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("surName")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("organisation")
        index.unindexUser(self.avatar)
        index = indexes.IndexesHolder().getById("status")
        index.unindexUser(self.avatar)
        
        #removing user from list
        la = self.ih.getById("Local")
        la.remove(userid)
        self.ah.remove(self.avatar)
        
        DBMgr.getInstance().endRequest()
        
        
class Unit(BaseTest):
    def run(self):
        
        self.createDummyUser()
        result = None
        
        try:
            #capturing the stderr
            outerr = StringIO.StringIO()
            sys.stderr = outerr
            
            result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                               'python',
                                                               'unit',
                                                               'MaKaC_tests')])
            
            #restoring the stderr
            sys.stderr = sys.__stderr__
            
            
            s = outerr.getvalue()
            self.writeReport("pyunit", s)
        finally:
            self.deleteDummyUser()
        
        if result:
            return "PY Unit tests succeeded\n"
        else:
            return "[FAIL] Unit tests - report in indicop/report/pyunit.txt\n"

class Functional(BaseTest):
    def __init__(self):
        self.child = None
        
    def run(self):
        if not self.startSeleniumServer():
            return ('[ERR] Could not start functional tests because selenium'
                    ' server cannot be started.\n')
            
        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr
        
        result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                           'python',
                                                           'functional')])
        
        self.stopSeleniumServer()
        
        #restoring the stderr
        sys.stderr = sys.__stderr__
        
        s = outerr.getvalue()
        self.writeReport("pyfunctional", s)
        
        report = ""
        if result:
            report = "PY Functional tests succeeded\n"
        else:
            report = ("[FAIL] Functional tests - report in "
                    " indicop/report/pyfunctional.txt\n")
        return report
    
    def startSeleniumServer(self):
        started = True
        try:
            self.child = subprocess.Popen(["java", "-jar",
                                      os.path.join(self.setupDir,
                                                   'python',
                                                   'functional',
                                                   'selenium-server.jar')],
                                      stdout=subprocess.PIPE)
        except OSError:
            return ("[ERR] Could not start selenium server - command \"java\""
                    " needs to be in your PATH.\n")
            
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
        self.gridData.setActive(True)
        
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
        self.writeReport("pygrid", s)
        
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
    
class Pylint(BaseTest):
    def run(self):
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
                    "command \"pylint\" needs to be in your PATH.\n")
        else:
            self.writeReport("pylint", statusOutput[1])
            return "PY Lint - report in indicop/report/pylint.txt\n"
        
class Coverage(BaseTest):
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
        return ("PY Unit Test - Report generated in "
                             "report/pycoverage/index.html\n")
        
class Jsunit(BaseTest):
    def __init__(self, jsSpecify, jsCoverage):
        self.coverage = jsCoverage
        self.specify = jsSpecify
        
    def run(self):
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
            
            #switching directory to run the tests
            os.chdir(os.path.join(self.setupDir, 'javascript', 'unit'))
            
            #check if server is ready
            for i in range(5):
                if self.coverage:
                    jsDryRun = commands.getstatusoutput(("java -jar "
                                                      "JsTestDriver-1.2.jar "
                                                      "--tests Fake.dryRun "
                                                      "--testOutput %s")
                                                      % os.path.join('..',
                                                                '..',
                                                                'report',
                                                                'jscoverage'))
                else:
                    jsDryRun = commands.getstatusoutput(("java -jar "
                                                 "JsTestDriver-1.2.jar"
                                                 " --config "
                                                 "jsTestDriverNoCoverage.conf"
                                                 " --tests Fake.dryRun"))
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
            

            coverageReport = ""
            if self.coverage:
                jsTest = commands.getstatusoutput(("java -jar "
                                                   "JsTestDriver-1.2.jar "
                                                   "--tests %s "
                                                   "--testOutput %s") % 
                                                   (toTest, os.path.join(
                                                               '..',
                                                               '..',
                                                               'report',
                                                               'jscoverage')))
                
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
                                           'jsTestDriver.conf-coverage.dat')))
                
                if genOutput[1].find("genhtml") > -1:
                    coverageReport = ("[ERR] JS Unit Tests - html coverage "
                                      "generation failed, genhtml needs to be "
                                      "in your PATH.\n")
                else:
                    coverageReport = ("JS Unit Tests - coverage generated in "
                                     "indicop/report/jscoverage/index.html\n")
                
            else:
                jsTest = commands.getstatusoutput(("java -jar "
                                                 "JsTestDriver-1.2.jar "
                                                 "--config "
                                                 "jsTestDriverNoCoverage.conf"
                                                 " --tests %s") % toTest)
            
            #restoring directory
            os.chdir(self.setupDir)
            
            report = ""
            if self.specify:
                #ouputing directly in the console
                print jsTest[1]
                report = "JS Unit Tests - Output in console\n"
            else:
                self.writeReport("jsunit", jsTest[1])
                report = ("JS Unit Tests - report in "
                          "indicop/report/jsunit.txt\n")
        except OSError:
            return ("[ERR] Could not start js-test-driver server - command "
                    "\"java\" needs to be in your PATH.\n")
            
        #stopping the server
        server.kill()
        return coverageReport + report
    
class Jslint(BaseTest):
    def run(self):
        #Folders which are going to be scanned.
        #Files are going to be find recursively in these folders
        folderNames = ['Admin', 'Collaboration', 'Core', 'Display', 'Legacy',
                       'Management', 'MaterialEditor', 'Timetable']
        
        outputString = ""
        
        #checking if rhino is accessible
        statusOutput = commands.getstatusoutput("rhino -?")
        if statusOutput[1].find("rhino: not found") > -1:
            return ("[ERR] Could not start JS Source Analysis - command "
                    "\"rhino\" needs to be in your PATH.\n")
        
        for folderName in folderNames:
            for root, dirs, files in os.walk(os.path.join(self.setupDir,
                                                          '..',
                                                          'indico',
                                                          'htdocs',
                                                          'js',
                                                          'indico',
                                                          folderName)):
                for name in files:
                    filename = os.path.join(root, name)
                    outputString += ("\n================== Scanning %s "
                                     "==================\n") % filename
                    output = commands.getstatusoutput("rhino %s %s" %
                                                      (os.path.join(
                                                                self.setupDir,
                                                                'javascript',
                                                                'jslint',
                                                                'jslint.js'),
                                                                filename))
                    outputString += output[1]

        self.writeReport("jslint", outputString)
        return "JS Lint - report in indicop/report/jslint.txt\n"


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
        
        coverageTest = Coverage()
        if coverage:
            coverageTest.start()
            
        
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
        
        
        if coverage:
            returnString += coverageTest.stop()
        
        return returnString
