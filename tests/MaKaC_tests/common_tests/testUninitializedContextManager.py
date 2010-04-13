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

import unittest
import threading, time

from MaKaC.common.contextManager import ContextManager

class TestUninitializedContextManager(unittest.TestCase):


    def testGetDefaultSilent(self):
        self.assertEquals(ContextManager.getdefault('test', '42').__class__, ContextManager.DummyContext)

    def testGetSilent(self):
        self.assertEquals(ContextManager.get('test').__class__, ContextManager.DummyContext)

    def testSetSilent(self):
        self.assertEquals(ContextManager.set('test','foo').__class__, ContextManager.DummyContext)

    def testHasFalse(self):
        self.assertEquals(ContextManager.has('test'), False)

    def testGetIgnoresCalls(self):
        self.assertEquals(ContextManager.get('test').doSomething(), None)

    def testGetIgnoresGetItem(self):
        self.assertEquals(ContextManager.get('test')['foo'], None)

    def testGetIgnoresSetItem(self):
        ContextManager.get('test')['foo'] = 'bar'


if __name__ == '__main__':
    unittest.main()
