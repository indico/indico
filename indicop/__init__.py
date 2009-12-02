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


def main(testPath, coverage):

    print "Welcome in INDICOP"
    sys.stdout.flush()
    returnString=""
    
    if coverage:
        figleaf.start()
        
    #Starting Selenium server
    child = subprocess.Popen(["java", "-jar", "indicop/selenium_tests/selenium-server.jar"], stdout=subprocess.PIPE)
    
    #This is a cheap trick to make sure that selenium has fully
    #started before launching the tests.
    #Selenium (1.0.1) displays 5 lines in the shell before being ready
    counter = 0
    while counter < 5:
        child_output = child.stdout.readline()
        #print "Selenium debug %s: %s" % (counter, child_output)
        counter += 1
    
    if testPath:
        result = nose.run(argv=['nose','-v', 'indicop/MaKaC_tests/%s' % testPath])
    else:
        #result = nose.run(argv=['nose','-v', 'indicop/MaKaC_tests/'])
        result = nose.run(argv=['nose','-v', 'indicop/selenium_tests/create_delete_lecture_test.py:Selenium_test.test_create_delete_lecture'])
    
    #Stopping Selenium Server
    child.kill()
    
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

if __name__ == '__main__':
    main()
