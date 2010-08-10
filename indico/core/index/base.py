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

from BTrees.Length import Length
from zope.index.field import FieldIndex

from BTrees.IOBTree import IOBTree, IOTreeSet
from BTrees.OOBTree import OOBTree, OOTreeSet
from persistent import Persistent

class IOIndex(Persistent):
    """
    Maps integer values to objects
    int -> set(obj, ...)
    """

    def __init__(self):
        self._fwd_index = IOBTree()
        self._rev_index = OOBTree()
        self._num_objs = Length(0)

    def index_obj(self, obj, value):

        if obj not in self._rev_index:
            self._rev_index[obj]  = IOTreeSet()

        if value in self._rev_index[obj]:
            return
        else:
            self._rev_index[obj].add(value)

        vset = self._fwd_index.get(value)
        if vset is None:
            vset = OOTreeSet()
            self._fwd_index[value] = vset

        if obj in vset:
            raise Exception('Inconsistent Index!')
        else:
            vset.insert(obj)
            self._num_objs.change(1)



class IntFieldIndex(FieldIndex):

    def clear(self):
        """
        Initialize forward and reverse mappings.
        """

        # The forward index maps indexed values to a sequence of docids
        self._fwd_index = self.family.IO.BTree()

        # The reverse index maps a docid to its index value
        self._rev_index = self.family.II.BTree()
        self._num_docs = Length(0)

    def has_doc(self, docid):
        if type(docid) == int:
            return docid in self._rev_index
        else:
            return False

    def all(self):
        return self.family.IF.multiunion(
            self._fwd_index.values())
