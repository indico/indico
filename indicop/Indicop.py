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


class Indicop(object):
    #path to this current file
    setupDir = os.path.dirname(__file__)
    
    def writeReport(self, filename, content):
        f = open(os.path.join(self.setupDir, 'report', filename + ".txt"), 'w')
        f.write(content)
        f.close()

    def main(self, specify, coverage, jsSpecify, jsCoverage, testsToRun):
        
        #define the set of tests
        testsDict = {'unit': Unit(),
                     'functional': Functional(),
                     'pylint': Pylint(),
                     'jsunit': Jsunit(jsSpecify, jsCoverage),
                     'jslint': Jslint()}
        
        returnString = "\n\n=============== ~INDICOP SAYS~ ===============\n\n"
        
        if coverage:
            figleaf.start()
            
        
        #specified test can either be unit or functional.
        #It makes more sense to run it here.
        if specify:
            #running directly the test here and ouputing in the console
            result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir, 
                                                         'python', specify)])
            if result:
                returnString += "Specified Test - Succeeded\n"
            else:
                returnString += "[FAIL] Specified Test - \
                                    read output from console\n"
        else:
            for test in testsToRun:
                try:
                    returnString += testsDict[test].run()
                except KeyError:
                    returnString += ("[ERR] Test %s does not exist. "
                      "It has to be added in the testsDict variable\n") % test
        
        
        if coverage:
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
            returnString += ("PY Unit Test - Report generated in "
                             "report/pycoverage/index.html\n")
            
        
        return returnString


class Unit(Indicop):
    def run(self):
        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr
        
        result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                        'python', 'unit', 'MaKaC_tests')])
        
        #restoring the stderr
        sys.stderr = sys.__stderr__
        
        s = outerr.getvalue()
        self.writeReport("pyunit", s)
        
        if result:
            return "PY Unit tests succeeded\n"
        else:
            return "[FAIL] Unit tests - report in indicop/report/pyunit.txt\n"

class Functional(Indicop):
    def run(self):
        try:
            #Starting Selenium server
            child = subprocess.Popen(["javae", "-jar",
                                      os.path.join(self.setupDir,'python',
                                                   'functional',
                                                   'selenium-server.jar')],
                                      stdout=subprocess.PIPE)
        except OSError:
            return ("[ERR] Could not start selenium server - command \"java\""
                    " needs to be in your PATH.")
            
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
                print 'Selenium has not started yet. Attempt #%s' % (i+1)
                time.sleep(5)
        else:
            return ('[ERR] Could not start functional tests because selenium'
                    ' server cannot be started.')
            
        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr
        
        result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                     'python', 'functional')])
        
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
            
        #Stopping Selenium Server
        child.kill()
        
        return report
    
class Pylint(Indicop):
    def run(self):
        statusOutput = commands.getstatusoutput("pylint --rcfile=%s %s" % 
                       (os.path.join(self.setupDir, 'python', 'pylint',
                                                        'pylint.conf'),
                       os.path.join(self.setupDir, '..', 'indico', 'MaKaC')))
        if statusOutput[1].find("pylint: not found") > -1:
            return ("[ERR] Could not start Source Analysis - "
                    "command \"pylint\" needs to be in your PATH.")
        else:
            self.writeReport("pylint", statusOutput[1])
            return "PY Lint - report in indicop/report/pylint.txt\n"
        
class Jsunit(Indicop):
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
                if jsDryRun[1].startswith(("No browsers were captured, "
                                           "nothing to run...")):
                    print ("Js-test-driver server has not started yet. "
                           "Attempt #%s") % (i+1)
                    time.sleep(5)
                else:
                    #server is ready
                    break
            else:
                return ('[ERR] Could not start js unit tests because '
                        'js-test-driver server cannot be started.')
                
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
                    "\"java\" needs to be in your PATH.")
            
        #stopping the server
        server.kill()
        return coverageReport + report
    
class Jslint(Indicop):
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
                    "\"rhino\" needs to be in your PATH.")
        
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
    