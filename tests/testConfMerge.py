# -*- coding: utf-8 -*-
##
## $Id:
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
import unittest
from setup import confmerge

class TestConfMerge(unittest.TestCase):
    def testShouldFillMissingValueWithNewDefaultValue(self):
        newConf = confmerge({'htdocsDir': ''}, {'htdocsDir': 'auto'})
        self.assertEqual('auto', newConf['htdocsDir'])

    def testShouldPreserveExistingValue(self):
        newConf = confmerge({'htdocsDir': '/opt/indico'}, {'htdocsDir': 'auto'})
        self.assertEqual('/opt/indico', newConf['htdocsDir'])

    def testShouldIgnoreValuesNotPresentInNewConfig(self):
        newConf = confmerge({'alarmState': '1'}, {})
        assert('alarmState' not in newConf.keys())

    def testShouldAddNewKeys(self):
        newConf = confmerge({}, {'htdocsDir': 'auto'})
        assert('htdocsDir' in newConf.keys())
        self.assertEqual('auto', newConf['htdocsDir'])

    def testShouldPreserveExistingListValue(self):
        newConf = confmerge({'someList': ('host0', 'port0')}, {'someList': ('host', 'port')})
        self.assertEqual(('host0', 'port0'), newConf['someList'])

    def testShouldPreserveClassIfList(self):
        newConf = confmerge({'someList': []}, {'someList': ['one']})
        self.assertEqual(1, len(newConf['someList']))
        self.assertEqual(list, newConf['someList'].__class__)


    def testShouldReturnUniques(self):
        newConf = confmerge({'someList': ['one']}, {'someList': ['one', 'two']})
        self.assertEqual(2, len(newConf['someList']))
        for k in ('one', 'two'):
            assert k in newConf['someList']

    def testShouldAppendNewValuesToExistingListValue(self):
        newConf = confmerge({'someList': ['three']}, {'someList': ['one', 'two']})
        self.assertEqual(3, len(newConf['someList']))
        for k in ('one', 'two', 'three'):
            assert k in newConf['someList']
