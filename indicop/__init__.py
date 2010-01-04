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
import unittest
import sys
import glob
import re
import nose
import figleaf
import figleaf.annotate_html
import subprocess
import socket
import time
import commands
import StringIO
from selenium import selenium

    ##TODO check relative PATHs
class Indicop():
    
    def unit(self):
        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr
        
        result = nose.run(argv=['nose','-v', 'indicop/MaKaC_tests/'])
        
        #restoring the stderr
        sys.stderr = sys.__stderr__
        
        s = outerr.getvalue()
        self.writeReport("unitTest", s)
        
        if result:
            return "All Unit tests succeeded\n"
        else:
            return "[FAIL] Unit tests - report in indicop/report/unitTest.txt\n"


    def functional(self):
        try:
            #Starting Selenium server
            child = subprocess.Popen(["java", "-jar", "indicop/selenium_tests/selenium-server.jar"], stdout=subprocess.PIPE)
        except OSError:
            print "[ERR] Could not start selenium server - command \"java\" needs to be in your PATH."
            sys.exit(1)
            
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
            print '[ERR] Could not start functional tests because selenium server cannot be started.'
            sys.exit(1)
            
        #capturing the stderr
        outerr = StringIO.StringIO()
        sys.stderr = outerr
        
        result = nose.run(argv=['nose','-v', 'indicop/selenium_tests/'])
        
        #restoring the stderr
        sys.stderr = sys.__stderr__
        
        s = outerr.getvalue()
        self.writeReport("functionalTest", s)
        
        report = ""
        if result:
            report = "All Functional tests succeeded\n"
        else:
            report = "[FAIL] Functional tests - report in indicop/report/functionalTest.txt\n"
            
        #Stopping Selenium Server
        child.kill()
        
        return report


    def pylint(self):
        statusOutput = commands.getstatusoutput("pylint --rcfile=indicop/source_analysis/pylint/pylint.conf ../cds-indico/indico/MaKaC/conference.py")
        if statusOutput[1].find("pylint: not found") > -1:
            print "[ERR] Could not start Source Analysis - command \"pylint\" needs to be in your PATH."
            sys.exit(1)
        else:
            self.writeReport("pylint", statusOutput[1])
            return "Pylint - report in indicop/report/pylint.txt\n"


    def jsUnit(self, coverage, specify):
        try:
            #Starting js-test-driver server
            server = subprocess.Popen(["java", "-jar", "indicop/javascript_tests/JsTestDriver-1.2.jar", "--port", "9876", "--browser", "firefox"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
            
            #switching directory to run the tests
            rootDir = os.getcwd()
            os.chdir("%s/indicop/javascript_tests/" % rootDir)
            
            #check if server is ready
            for i in range(5):
                jsDryRun = commands.getstatusoutput("java -jar JsTestDriver-1.2.jar --config jsTestDriverNoCoverage.conf --tests Fake.dryRun")
                if jsDryRun[1].startswith("No browsers were captured, nothing to run..."):
                    print "Js-test-driver server has not started yet. Attempt #%s" % (i+1)
                    time.sleep(5)
                else:
                    #server is ready
                    break
            
            #setting tests to run
            toTest = ""
            if specify:
                toTest = specify
            else:
                toTest = "all"
            

            coverageReport = ""
            if coverage:
                jsTest = commands.getstatusoutput("java -jar JsTestDriver-1.2.jar --tests %s --testOutput coverage" % toTest)
                
                os.chdir("%s/coverage" % os.getcwd())
                
                #generate html for coverage
                commands.getstatusoutput("genhtml jsTestDriver.conf-coverage.dat")
                
                coverageReport = "JS Unit Tests - coverage generated in indicop/javascript_tests/coverage/index.html\n"
            else:
                jsTest = commands.getstatusoutput("java -jar JsTestDriver-1.2.jar --config jsTestDriverNoCoverage.conf --tests %s --testOutput coverage" % toTest)
            
            #restoring directory
            os.chdir(rootDir)
            
            report = ""
            if specify:
                print jsTest[1]
                report = "JS Unit Tests - Ouput in console\n"
            else:
                self.writeReport("jsUnit", jsTest[1])
                report = "JS Unit Tests - report in indicop/report/jsUnit.txt\n"
        except OSError:
            print "[ERR] Could not start js-test-driver server - command \"java\" needs to be in your PATH."
            sys.exit(1)
            
        #stopping the server
        server.kill()
        return coverageReport + report


    def jsLint(self):
        #Folders which are going to be scanned.
        #Files are going to be find recursively in these folders
        folderNames=['Admin', 'Collaboration', 'Core', 'Display', 'Legacy', 'Management',
                      'MaterialEditor', 'Timetable']
        
        outputString = ""
        
        #checking if rhino is accessible
        statusOutput = commands.getstatusoutput("rhino -?")
        if statusOutput[1].find("rhino: not found") > -1:
            print "[ERR] Could not start JS Source Analysis - command \"rhino\" needs to be in your PATH."
            sys.exit(1)
        
        for folderName in folderNames:
            for root, dirs, files in os.walk("%s/indico/htdocs/js/indico/%s" % (os.getcwd(), folderName)):
                for name in files:
                    filename = os.path.join(root, name)
                    outputString += "\n================== Scanning %s ==================\n" % filename
                    output = commands.getstatusoutput("rhino indicop/source_analysis/jslint/jslint.js %s" % filename)
                    outputString += output[1]

        self.writeReport("jsLint", outputString)
        return "JS Lint - report in indicop/report/jsLint.txt\n"

    
    def writeReport(self, filename, content):
        f = open('indicop/report/%s.txt' % filename, 'w')
        f.write(content)
        f.close()

    def main(self, specify, coverage, unitTest, functionalTest, pylint, jsunit, jslint, jsCoverage, jsSpecify):
        returnString="=============== ~INDICOP SAYS~ ===============\n\n"
        
        if coverage:
            figleaf.start()
            
        if specify:
            result = nose.run(argv=['nose','-v', 'indicop/%s' % specify])
            if result:
                returnString += "Specified Test - Succeeded\n"
            else:
                returnString += "[FAIL] Specified Test - read output from console\n"
        elif pylint:
            returnString += self.pylint()
        elif unitTest:
            returnString += self.unit()
        elif functionalTest:
            returnString += self.functional()
        elif jsunit or jsSpecify:
            returnString += self.jsUnit(jsCoverage, jsSpecify)
        elif jslint:
            returnString += self.jsLint()
        else:
            returnString += self.unit()
            returnString += self.functional()
            returnString += self.pylint()
            returnString += self.jsUnit(jsCoverage, jsSpecify)
            returnString += self.jsLint()
        
        if coverage:
            figleaf.stop()
            coverageOutput = figleaf.get_data().gather_files()
            try:
                figleaf.annotate_html.report_as_html(coverageOutput, 'indicop/coverage/html_report', [], {})
            except IOError:
                os.mkdir('indicop/coverage/html_report')
                figleaf.annotate_html.report_as_html(coverageOutput, 'indicop/coverage/html_report', [], {})
            returnString += "Unit Test - Report generated in indicop/coverage/html_report/index.html\n"
        
        
        return returnString
