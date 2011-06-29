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

# For now, disable Pylint
# pylint: disable-all


import unittest
import threading, time

from MaKaC.common.contextManager import ContextManager, DummyDict

class TestInitializedContextManager(unittest.TestCase):
    "Context Manager - Properly Initialized"

    def tearDown(self):
        ContextManager.destroy()

    def testGetWorks(self):
        "Getting the value of an existing attribute"

        ContextManager.set('test', 123)
        self.assertEquals(ContextManager.get('test'), 123)

    def testGetItemWorks(self):
        "Getting the value of an existing attribute (__getitem__)"

        ContextManager.set('test', 123)
        self.assertEquals(ContextManager.get()['test'], 123)

    def testDoubleSetWorks(self):
        "Two consecutive set() operations over the same attribute"

        ContextManager.set('test2', 65)
        ContextManager.set('test2', 66)
        self.assertEquals(ContextManager.get('test2'), 66)

    def thread1(self):
        ContextManager.set('samevariable', 'a')
        time.sleep(2)
        self.assertEquals(ContextManager.get('samevariable'), 'a')

    def thread2(self):
        time.sleep(1)
        ContextManager.set('samevariable', 'b')
        self.assertEquals(ContextManager.get('samevariable'), 'b')

    def testWithThreads(self):
        "Thread safety"

        t1 = threading.Thread(target=self.thread1)
        t2 = threading.Thread(target=self.thread2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        self.assertEquals(ContextManager.get('samevariable').__class__, DummyDict)


class TestUninitializedContextManager(unittest.TestCase):
    "Context Manager - Uninitialized"

    def testReturnsDummyDict(self):
        "Return a DummyDict in case the attribute is not defined"

        self.assertEquals(ContextManager.get('test').__class__, DummyDict)

    def testGetSilent(self):
        "get() shouldn't fail, but return a DummyDict instead"

        self.assertEquals(ContextManager.get('utest').__class__, DummyDict)

    def testGetDefault(self):
        "get() should support a default argument"

        self.assertEquals(ContextManager.get('utest', 'foo'), 'foo')

    def testContainsFalse(self):
        "__contains__ will return false"

        self.assertEquals('utest' in ContextManager.get(), False)

    def testGetIgnoresCalls(self):
        "methods called on get() should do nothing"

        self.assertEquals(ContextManager.get('utest').doSomething(), None)
