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

"""
Tests for `indico.core.index` module
"""

import unittest, zope.interface

from indico.core.index.base import IIIndex, IOIndex, IUniqueIdProvider

from MaKaC.common import DBMgr

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
        self.assertEqual(list(self._idx.apply((1500,3000))), [1, 2, 3, 4, 5])
        self.assertEqual(list(self._idx.apply((1500,1500))), [3, 4, 5])
        self.assertEqual(list(self._idx.apply((4000,5000))), [])

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

class DummyObject(Persistent):

    zope.interface.implements(IUniqueIdProvider,
                              IDummyAdapter)

    def __init__(self, oid):
        self._id = oid

    def getUniqueId(self):
        return self._id

    def __conform__(self, proto):
        if proto == IDummyAdapter:
            return 1


class TestIOIndex(unittest.TestCase):

    def setUp(self):
        self._idx = IOIndex(IDummyAdapter)

    def testIndexing(self):
        for i in range(0, 200):
            obj = DummyObject(i)
            self._idx.index_obj(obj)

        # ... finish this ...
