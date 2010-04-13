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

class TestInitializedContextManager(unittest.TestCase):

    def setUp(self):
        ContextManager.create()

    def testGetDefaultWorks(self):
        self.assertEquals(ContextManager.getdefault('test', '42'), '42')

    def testGetWorks(self):
        ContextManager.set('test', 123)
        self.assertEquals(ContextManager.get('test'), 123)

    def testThrowsKeyError(self):
        self.assertEquals(ContextManager.get('test').__class__, ContextManager.DummyContext)

    def testDoubleSetWorks(self):
        ContextManager.set('test2', 65)
        ContextManager.set('test2', 66)
        self.assertEquals(ContextManager.get('test2'), 66)

    def thread1(self):
        ContextManager.create()
        ContextManager.set('samevariable', 'a')
        time.sleep(2)
        self.assertEquals(ContextManager.get('samevariable'), 'a')

    def thread2(self):
        ContextManager.create()
        time.sleep(1)
        ContextManager.set('samevariable', 'b')
        self.assertEquals(ContextManager.get('samevariable'), 'b')

    def testWithThreads(self):
        t1 = threading.Thread(target=self.thread1)
        t2 = threading.Thread(target=self.thread2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.assertEquals(ContextManager.get('samevariable').__class__, ContextManager.DummyContext)

if __name__ == '__main__':
    unittest.main()
