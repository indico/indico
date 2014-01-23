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

"""
Tests for `indico.modules.scheduler.queue` module
"""

import unittest

from indico.core.db import DBMgr
from indico.util.struct.queue import PersistentWaitingQueue, DuplicateElementException


class TestPersistentWaitingQueue(unittest.TestCase):

    def setUp(self):
        self._q = PersistentWaitingQueue()

    def _enqueueSomeElements(self):

        self._q.enqueue(1, 0)
        self._q.enqueue(1, 1)
        self._q.enqueue(2, 2)
        self._q.enqueue(3, 'a')
        self._q.enqueue(2, 4)


    def testEnqueueOperation(self):
        """
        Check that enqueue() works
        """

        self._enqueueSomeElements()

        self.assertEqual(len(self._q), 5)
        self.assertEqual(self._q.nbins(), 3)

    def testGetItemOperation(self):
        """
        Check __getitem__()
        """

        self._q.enqueue(1, 1)
        self._q.enqueue(1, 2)

        self.assertEqual(list(self._q[1]), [1,2])

    def testPopOperation(self):
        """
        Check pop()
        """
        self._enqueueSomeElements()

        self.assertEqual(self._q.pop(), (1, 0))
        self.assertEqual(self._q.pop(), (1, 1))
        self.assertEqual(self._q.pop(), (2, 2))
        self.assertEqual(self._q.pop(), (2, 4))
        self.assertEqual(self._q.pop(), (3, 'a'))

        self.assertEqual(len(self._q), 0)
        self.assertEqual(self._q.nbins(), 0)

    def testPeekOperation(self):
        """
        Check peek()
        """
        self._enqueueSomeElements()

        self.assertEqual(self._q.peek(), (1, 0))

        self.assertEqual(len(self._q), 5)
        self.assertEqual(self._q.nbins(), 3)


    def testDequeueOperation(self):
        """
        Check that dequeue() works
        """

        self._enqueueSomeElements()
        self._q.dequeue(3,'a')

        self.assertEqual(len(self._q), 4)
        self.assertEqual(self._q.nbins(), 2)

    def testIteration(self):
        """
        Iterate over a queue
        """

        self._enqueueSomeElements()

        l = []

        for e in self._q:
            l.append(e)

        self.assertEqual(l, [(1,0), (1,1), (2,2), (2,4), (3,'a')])

    def testDuplicateInsert(self):
        """
        Insert the same element twice
        """

        self._q.enqueue(1,1)

        self.assertRaises(DuplicateElementException, self._q.enqueue, 1, 1)
