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
'''
To add new tests simply create a new file inside tests/ or inside a subdir with a
unittest.TestCase child class and this script will automatically find it.

WARNING WARNING WARNING
If you are launching tests inside Eclipse or any other IDE make sure that sys.path 
is properly set.
'''
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
from selenium import selenium


    ##TODO check relative PATHs
class Indicop():
    
    def unit(self):
        result = nose.run(argv=['nose','-v', 'indicop/MaKaC_tests/'])
        return result
    
    def functional(self):
        #Starting Selenium server
        child = subprocess.Popen(["java", "-jar", "indicop/selenium_tests/selenium-server.jar"], stdout=subprocess.PIPE)
    
        sel = selenium("localhost", 4444, "*chrome", "http://www.cern.ch/")
        for i in range(5):
            try:
                #testing if the selenium server has started
                time.sleep(1)
                sel.start()
                sel.stop()
                
                result = nose.run(argv=['nose','-v', 'indicop/selenium_tests/'])
                break
            except socket.error:
                print 'Selenium has not started yet. Attempt #%s' % (i+1)
                time.sleep(5)
        else:
            print 'ERROR - Could not start functional tests because of Selenium server.'
            sys.exit(1)
        
        #Stopping Selenium Server
        child.kill()
        
        return result

    def main(self, testPath, coverage, unitTest, functionalTest):
    
        print "Welcome in INDICOP"
        sys.stdout.flush()
        returnString=""
        
        if coverage:
            figleaf.start()
            
        if testPath:
            #Security, getting rid of everything after a semicolon
            escapedPath = testPath.split(';')
            result = nose.run(argv=['nose','-v', 'indicop/%s' % escapedPath[0]])
        elif unitTest:
            result = self.unit()
        elif functionalTest:
            result = self.functional()
        else:
            result = self.unit() and self.functional()
        
        if coverage:
            figleaf.stop()
            coverageOutput = figleaf.get_data().gather_files()
            try:
                figleaf.annotate_html.report_as_html(coverageOutput, 'indicop/coverage/html_report', [], {})
            except Exception:
                os.mkdir('indicop/coverage/html_report')
                figleaf.annotate_html.report_as_html(coverageOutput, 'indicop/coverage/html_report', [], {})
            returnString += "Report generated in indicop/coverage/html_report\n"
        
        if result:
            returnString += "All tests succeeded!"
        else:
            returnString += "TestSuite failed!"
        
        return returnString
