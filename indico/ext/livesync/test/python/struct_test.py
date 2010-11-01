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

from indico.ext.livesync.struct import ListMultiPointerTrack, SetMultiPointerTrack
from indico.tests.python.unit.db import TestMemStorage

import transaction
from ZODB.POSException import ConflictError


class TestMultiPointerTrack(unittest.TestCase):

    def setUp(self):
        self._mpt = ListMultiPointerTrack()

    def _addSome(self):
        self._mpt.add(1, 'a')
        self._mpt.add(2, 'b')
        self._mpt.add(1, 'c')
        self._mpt.add(1, 'a')
        self._mpt.add(2, 'a')
        self._mpt.add(3, 'c')

    def testAdd(self):
        """
        adding several elements and checking the result
        """
        self._addSome()
        self.assertEqual(list(self._mpt[1]), ['a', 'c', 'a'])
        self.assertEqual(list(self._mpt[2]), ['b', 'a'])
        self.assertEqual(list(self._mpt[3]), ['c'])

    def testSlice(self):
        """
        adding several elements and checking the result
        """
        self._addSome()
        self.assertEqual(list(self._mpt[1:2]), [['a', 'c', 'a'], ['b', 'a']])
        self.assertEqual(list(self._mpt[:]), [['a', 'c', 'a'], ['b', 'a'], ['c']])

    def testDel(self):
        """
        adding several elements and checking the result
        """

        self._mpt.add(1, 'a')
        self._mpt.add(2, 'b')
        self._mpt.add(1, 'c')
        del self._mpt[1]
        self.assertEqual(len(self._mpt), 1)
        del self._mpt[2]
        self.assertEqual(len(self._mpt), 0)

    def testLen(self):
        """
        adding/removing several elements and checking len()
        """
        self.assertEqual(len(self._mpt), 0)
        self._mpt.add(1, 'a')
        self.assertEqual(len(self._mpt), 1)
        self._mpt.add(2, 'b')
        self._mpt.add(1, 'c')
        self.assertEqual(len(self._mpt), 2)
        del self._mpt[1]
        self.assertEqual(len(self._mpt), 1)

    def testMovePointer(self):
        """
        moving the pointer
        """
        self._addSome()
        self._mpt.addPointer('p1')
        self._mpt.addPointer('p2')
        self._mpt.movePointer('p2', 1)
        self._mpt.movePointer('p1', 1)
        self.assertEqual(list(self._mpt.pointerIterItems('p1')),
                         ['b', 'a', 'c'])
        self._mpt.movePointer('p1', 2)
        self.assertEqual(list(self._mpt.pointerIterItems('p2')),
                         ['b', 'a', 'c'])
        self.assertEqual(list(self._mpt.pointerIterItems('p1')), ['c'])
        self._mpt.movePointer('p1', 1)

    def testAddPointerStartPos(self):
        """
        adding a pointer at a start position
        """
        self._addSome()

        # should be the minimum key
        self._mpt.addPointer('p1')
        self.assertEqual(self._mpt.getPointerTimestamp('p1'), None)

        self._mpt.addPointer('p2', 3)
        self.assertEqual(self._mpt.getPointerTimestamp('p2'), 3)


    def testMovePointerErrors(self):
        """
        exceptions thrown by movePointer()
        """

        # pointer doesn't exist
        self.assertRaises(KeyError, self._mpt.movePointer, 'a', 1)

        self._addSome()

        self._mpt.addPointer('a', 1)

        # lower bound
        self.assertRaises(ValueError, self._mpt.movePointer, 'a', 0)

        # higher bound
        self.assertRaises(ValueError, self._mpt.movePointer, 'a', 4)


class TestSetMultiPointerTrack(unittest.TestCase):

    def setUp(self):
        self._mpt = SetMultiPointerTrack()

    def _addSome(self):
        self._mpt.add(1, (1,'a'))
        self._mpt.add(2, (1,'b'))
        self._mpt.add(1, (1,'c'))
        self._mpt.add(1, (2,'d'))
        self._mpt.add(2, (2,'e'))
        self._mpt.add(3, (4,'f'))


    def testOrdering(self):
        self._addSome()

        self.assertEqual(
            list(e[1] for e in self._mpt),
            ['a', 'c', 'd', 'b', 'e', 'f'])

    def testPointerIterator(self):
        self._addSome()

        self._mpt.addPointer("foo")
        self._mpt.addPointer("bar", 2)

        self.assertEqual(list(self._mpt.pointerIterValues("foo")),
                         [(1, 'a'), (1, 'c'), (2, 'd'), (1, 'b'), (2, 'e'), (4, 'f')])

        self.assertEqual(list(self._mpt.pointerIterValues("bar")),
                         [(4, 'f')])


class TestSetMultiPointerTrackDB(unittest.TestCase):


    def setUp(self):

        from ZODB import DB
        db = DB(TestMemStorage('test'))

        self._tm1 = transaction.TransactionManager()
        self._tm2 = transaction.TransactionManager()

        self._c1 = db.open(transaction_manager=self._tm1)

        self._r1 = self._c1.root()
        self._qmpt1 = self._r1["queue"] =  SetMultiPointerTrack()
        self._tm1.commit()

        self._c2 = db.open(transaction_manager=self._tm2)
        self._r2 = self._c2.root()
        self._qmpt2 = self._r2["queue"]

    def testConcurrentAdditionsConflict(self):
        """
        Concurrent addition in same TS (creation) creates conflict
        """
        self._qmpt1.add(8, 'a')
        self._qmpt2.add(8, 'b')
        self._tm1.commit()
        self.assertRaises(ConflictError, self._tm2.commit)
        # BOOM!

    def testConcurrentAdditionsOK(self):
        """
        Concurrent addition in different timestamps works OK
        """
        self._qmpt1.add(8, 'a')
        self._qmpt2.add(9, 'b')
        self._tm1.commit()
        self._tm2.commit()
        # NO BOOM :)
        self.assertEqual(True, True)

    def testConcurrentAdditionPrepared(self):
        """
        Concurrent addition in same TS (prepared) works OK
        """
        self._qmpt1.prepareEntry(8)
        self._tm1.commit()
        self._c2.sync()

        self._qmpt1.add(8, 'a')
        self._qmpt2.add(8, 'b')
        self._tm1.commit()
        self._tm2.commit()
        # NO BOOM :)
        self.assertEqual(True, True)

    def testConcurrentAdditionSameConflict(self):
        """
        Concurrent addition in same TS (prepared) raises conflict for same element
        """
        self._qmpt1.add(8, 'a')
        self._tm1.commit()
        self._c2.sync()

        self._qmpt1.add(8, 'b')
        self._qmpt2.add(8, 'b')
        self._tm1.commit()
        # BOOM!
        self.assertRaises(ConflictError, self._tm2.commit)
