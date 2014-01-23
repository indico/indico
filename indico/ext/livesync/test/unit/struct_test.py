# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import unittest

from indico.ext.livesync.struct import ListMultiPointerTrack, SetMultiPointerTrack, \
     timestamp
from indico.tests.python.unit.db import TestMemStorage

import transaction
from ZODB.POSException import ConflictError


class DummyType(object):
    def __init__(self, value):
        self._value = value

    def __timestamp__(self):
        return timestamp(self._value)

    def __str__(self):
        return "<DT %s>" % self._value

    def __cmp__(self, obj):
        val = cmp(self._value, obj._value)
        if val == 0:
            return cmp(id(self), id(obj))
        else:
            return val


class TestMultiPointerTrack(unittest.TestCase):

    def setUp(self):
        self._mpt = ListMultiPointerTrack()
        self._a = DummyType(1)
        self._b = DummyType(2)
        self._c = DummyType(3)

    def _addSome(self):
        self._mpt.add(1, self._a)
        self._mpt.add(2, self._b)
        self._mpt.add(1, self._c)
        self._mpt.add(1, self._a)
        self._mpt.add(2, self._a)
        self._mpt.add(3, self._c)

    def testAdd(self):
        """
        adding several elements and checking the result
        """
        self._addSome()
        self.assertEqual(list(self._mpt[1]), [self._a, self._c, self._a])
        self.assertEqual(list(self._mpt[2]), [self._b, self._a])
        self.assertEqual(list(self._mpt[3]), [self._c])

    def testSlice(self):
        """
        adding several elements and checking the result
        """
        self._addSome()
        self.assertEqual(list(self._mpt[2:1]), [[self._b, self._a],
                                                [self._a, self._c, self._a]])
        self.assertEqual(list(self._mpt[:]),
                         [[self._c], [self._b, self._a], [self._a, self._c, self._a]])

    def testDel(self):
        """
        adding/deleting several elements and checking the result
        """

        self._mpt.add(1, self._a)
        self._mpt.add(2, self._b)
        self._mpt.add(1, self._c)
        del self._mpt[1]
        self.assertEqual(len(self._mpt), 1)
        del self._mpt[2]
        self.assertEqual(len(self._mpt), 0)

    def testLen(self):
        """
        adding/removing several elements and checking len()
        """
        self.assertEqual(len(self._mpt), 0)
        self._mpt.add(1, self._a)
        self.assertEqual(len(self._mpt), 1)
        self._mpt.add(2, self._b)
        self._mpt.add(1, self._c)
        self.assertEqual(len(self._mpt), 2)
        del self._mpt[1]
        self.assertEqual(len(self._mpt), 1)

    def test_track_empty(self):
        """
        checking that track is empty
        """
        self.assertEqual(self._mpt.is_empty(), True)
        self._addSome()
        self.assertEqual(self._mpt.is_empty(), False)

    def testMovePointer(self):
        """
        moving the pointer
        """
        self._addSome()
        self._mpt.addPointer('p1')
        self._mpt.addPointer('p2')
        self._mpt.movePointer('p2', 1)
        self._mpt.movePointer('p1', 1)
        self.assertEqual(list(self._mpt.pointerIterValues('p1')),
                         [self._c, self._b, self._a])

        self._mpt.movePointer('p1', 2)
        self.assertEqual(list(self._mpt.pointerIterValues('p2')),
                         [self._c, self._b, self._a])

        self.assertEqual(list(self._mpt.pointerIterValues('p1')), [self._c])

    def testAddPointerStartPos(self):
        """
        adding a pointer at a start position
        """
        self._addSome()

        # should be the minimum key
        self._mpt.addPointer('p1')
        self.assertEqual(self._mpt.getPointerTimestamp('p1'), None)

        self._mpt.addPointer('p2', 3 )
        self.assertEqual(self._mpt.getPointerTimestamp('p2'), 3 )

    def testMovePointerError(self):
        """
        exception thrown by movePointer()
        """

        # pointer doesn't exist
        self.assertRaises(KeyError, self._mpt.movePointer, self._a, 1 )


class TestSetMultiPointerTrack(unittest.TestCase):

    def _val(self, iter):
        return list(e._value for e in iter)

    def setUp(self):
        self._mpt = SetMultiPointerTrack()
        self._a = DummyType(1  + 2)
        self._b = DummyType(2  + 2)
        self._c = DummyType(1  + 2)
        self._d = DummyType(1  + 1)
        self._e = DummyType(2  + 1)
        self._f = DummyType(3  + 4)

    def _addSome(self):
        self._mpt.add(1, self._a)
        self._mpt.add(2, self._b)
        self._mpt.add(1, self._c)
        self._mpt.add(1, self._d)
        self._mpt.add(2, self._e)
        self._mpt.add(3, self._f)

    def testOrdering(self):
        self._addSome()

        self.assertEqual(
            list(e._value for ts, e in self._mpt),
            [7, 3, 4, 2, 3, 3])

    def testPointerIterator(self):
        self._addSome()

        self._mpt.addPointer("foo")
        self._mpt.addPointer("bar", 2)

        self.assertEqual(self._val(self._mpt.pointerIterValues("foo")),
                         [7, 3, 4, 2, 3, 3])

        self.assertEqual(self._val(self._mpt.pointerIterValues("bar")),
                         [7])

    def testPointerIteratorTill(self):
        """
        Iterate till a certain timestamp
        """
        self._addSome()

        self._mpt.addPointer("foo")

        self.assertEqual(self._val(self._mpt.pointerIterValues("foo", till=2 )),
                         [3, 4, 2, 3, 3])


class TestSetMultiPointerTrackDB(unittest.TestCase):

    def setUp(self):

        from ZODB import DB
        db = DB(TestMemStorage('test'))

        self._tm1 = transaction.TransactionManager()
        self._tm2 = transaction.TransactionManager()

        self._c1 = db.open(transaction_manager=self._tm1)

        self._r1 = self._c1.root()
        self._qmpt1 = self._r1["queue"] = SetMultiPointerTrack()
        self._tm1.commit()

        self._c2 = db.open(transaction_manager=self._tm2)
        self._r2 = self._c2.root()
        self._qmpt2 = self._r2["queue"]

        self._a = DummyType(1)
        self._b = DummyType(2)
        self._c = DummyType(3)

    def testConcurrentAdditionsConflict(self):
        """
        Concurrent addition in same TS (creation) creates conflict
        """
        self._qmpt1.add(8, self._a)
        self._qmpt2.add(8, self._b)
        self._tm1.commit()
        self.assertRaises(ConflictError, self._tm2.commit)
        # BOOM!

    def testConcurrentAdditionsOK(self):
        """
        Concurrent addition in different timestamps works OK
        """
        self._qmpt1.add(8, self._a)
        self._qmpt2.add(18, self._b)
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

        self._qmpt1.add(8, self._a)
        self._qmpt2.add(8, self._b)
        self._tm1.commit()
        self._tm2.commit()
        # NO BOOM :)
        self.assertEqual(True, True)

    def testConcurrentAdditionSameConflict(self):
        """
        Concurrent addition in same TS (prepared) raises conflict for same element
        """
        self._qmpt1.add(8, self._a)
        self._tm1.commit()
        self._c2.sync()

        self._qmpt1.add(8, self._b)
        self._qmpt2.add(8, self._b)
        self._tm1.commit()
        # BOOM!
        self.assertRaises(ConflictError, self._tm2.commit)
