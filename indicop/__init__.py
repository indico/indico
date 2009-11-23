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
import os.path
import unittest
import sys
import glob
import re
import nose

def main():
    sys.path = ['/home/jeremy/cds-indico/indico'] + sys.path

    print "Welcome in INDICOP"
    sys.stdout.flush()
#    result = nose.run(argv=['nose', '--verbose', 'indicop/MaKaC_tests'])
    result = nose.run(argv=['nose','-v', 'indicop/MaKaC_tests/'])
    
    return result

if __name__ == '__main__':
    main()
