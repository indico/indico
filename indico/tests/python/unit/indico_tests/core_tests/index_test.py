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
Tests for `indico.core.index` module
"""

import unittest, zope.interface

from indico.core.index.base import IIIndex, IOIndex, IUniqueIdProvider, \
     ElementNotFoundException, ElementAlreadyInIndexException


from indico.core.db import DBMgr

from persistent import Persistent


class TestIIIndex(unittest.TestCase):

    def setUp(self):
        self._idx = IIIndex()

    def testIndexOperation(self):
        """
        Check that index_doc works
        """

        self._idx.index_doc(1, 2000)
        self._idx.index_doc(2, 3000)
        self._idx.index_doc(3, 1500)

        self.assertEqual(self._idx.wordCount(), 3)
        self.assertEqual(self._idx.documentCount(), 3)

    def testUnindexOperation(self):
        """
        Check that unindex_doc works
        """

        self.testIndexOperation()

        self._idx.unindex_doc(3)

        self.assertEqual(self._idx.wordCount(), 2)
        self.assertEqual(self._idx.documentCount(), 2)

        self._idx.unindex_doc(2)
        self._idx.unindex_doc(1)

        self.assertEqual(self._idx.wordCount(), 0)
        self.assertEqual(self._idx.documentCount(), 0)

    def testIndexCollisionOperation(self):
        """
        Check that index_doc works when there are key collisions
        """

        self.testIndexOperation()
        self._idx.index_doc(4, 1500)
        self._idx.index_doc(5, 1500)

        self.assertEqual(self._idx.wordCount(), 3)
        self.assertEqual(self._idx.documentCount(), 5)

    def testQueryOperation(self):
        """
        Check that queries over the index work
        """
        self.testIndexCollisionOperation()
        self.assertEqual(list(self._idx.apply((1500, 3000))), [1, 2, 3, 4, 5])
        self.assertEqual(list(self._idx.apply((1500, 1500))), [3, 4, 5])
        self.assertEqual(list(self._idx.apply((4000, 5000))), [])

    def testFaultyUnindex(self):
        """
        Unindex of non-existing value
        """

        # the operation won't fail (silently ignored), but
        # the document count won't change either

        self._idx.unindex_doc(1)

        self.assertEqual(self._idx.documentCount(), 0)

        self._idx.index_doc(1, 4000)
        self._idx.unindex_doc(3)

        self.assertEqual(self._idx.documentCount(), 1)

class IDummyAdapter(zope.interface.Interface):
    pass

class DummyObject(object):

    zope.interface.implements(IUniqueIdProvider,
                              IDummyAdapter)

    def __init__(self, oid):
        self._id = oid

    def getUniqueId(self):
        return self._id

    def __cmp__(self, obj):
        return cmp(self._id, obj._id)

    def __conform__(self, proto):
        if proto == IDummyAdapter:
            # 10, 11, 12 ... -> 1 / 20, 21, 22 ... -> 2 ...
            return self._id / 10


class TestIOIndex(unittest.TestCase):

    def setUp(self):
        self._idx = IOIndex(IDummyAdapter)

    def _indexSomeElements(self):
        objs = []
        for i in range(0, 200):
            obj = DummyObject(i)
            objs.append(obj)
            self._idx.index_obj(obj)

        return objs

    def testIndexing(self):
        objs = self._indexSomeElements()

        self.assertEqual(list(self._idx[1]), objs[10:20])
        self.assertEqual(len(self._idx), 200)

    def testFwdIndex(self):
        objs = self._indexSomeElements()
        for i in range(0, 200):
            self.assertTrue(objs[i] in self._idx._fwd_index[i/10])

    def testRevIndex(self):
        self._indexSomeElements()
        for i in range(0, 200):
            self.assertEqual(list(self._idx._rev_index[i]), [i/10])

    def testUnindexing(self):
        objs = self._indexSomeElements()

        for obj in objs:
            self._idx.unindex_obj(obj)

        self.assertEqual(len(self._idx), 0)

        for i in range(0, 20):
            self.assertEqual(self._idx.get(i), None)

    def testUnindexingNonExisting(self):
        self.assertRaises(ElementNotFoundException,
                          self._idx.unindex_obj,
                          DummyObject(1))

    def testIndexingTwice(self):
        obj = DummyObject(1)
        self._idx.index_obj(obj)
        self.assertRaises(ElementAlreadyInIndexException,
                          self._idx.index_obj,
                          obj)
