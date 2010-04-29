# -*- coding: utf-8 -*-
##
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
import os.path
import unittest
import sys
import glob
import re
import sys

try:
    import xmlrunner
except:
    pass

# The following tests are outdated and need to be fixed before they can be run  
INVALID_TESTS = ('__init__', 'test', 'testCategories', 'testCFA', 'testConferences', 'testContributions', 'testFileSubmission', 'testSchedule', 'testSciProgramme', 'testSessions', 'testWebInterface', 'rpc', 'jslint')
    
def suite():
    '''Scans tests/ for TestCase based tests and returns a suite containing all the tests'''
    testcases = []
    
    for root, dirs, files in os.walk('tests/'):
        for f in files:
            if f[-3:] == '.py' and not f.replace('.py', '') in INVALID_TESTS:
                testcases.append(os.path.join(root, f)[6:].replace('/', '.')[:-3])
    
    modules = map(__import__, testcases)
    load = unittest.defaultTestLoader.loadTestsFromModule
    return unittest.TestSuite([load(sys.modules[k]) for k in testcases])


if __name__ == '__main__':
    sys.path = ['.', os.path.join('indico'), os.path.join('..', 'indico')] + sys.path
    try:
        xmlrunner.XMLTestRunner(output='test-reports').run(suite())
    except:
        print 'No unittest-xml-reporting package detected, using TextTestRunner..'
        unittest.TextTestRunner(verbosity=2).run(suite())
