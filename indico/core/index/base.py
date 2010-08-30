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
from BTrees.OOBTree import OOBTree, OOTreeSet, union
from persistent import Persistent

import logging
import zope.interface


class IUniqueIdProvider(zope.interface.Interface):

    def getUniqueId(self):
        """
        Returns a unique, application-centered ID
        """


class NonIndexableException(Exception):
    """
    Thrown when it is impossible to index an object
    """


class ElementNotFoundException(Exception):
    """
    Thrown when an element is not found in the index
    """


class InconsistentIndexException(Exception):
    """
    Thrown when the index seems inconsistent
    """

class ElementAlreadyInIndexException(Exception):
    """
    Thrown when the element is inserted a second time in the index
    """


class IOIndex(Persistent):
    """
    Maps integer values to objects
    int -> set(obj, ...)

    int is obtained by means of an adapter

    objects need to implement IUniqueIdProvider as well, as an id is needed for
    the backward-index (OOBTrees don't accept persisten objects as keys)
    """

    def __init__(self, adapter):
        self._fwd_index = IOBTree()
        self._rev_index = OOBTree()
        self._num_objs = Length(0)
        self._adapter = adapter

    def _gc_entry(self, v):
        """
        'Garbage collect' empty set entries
        """
        if len(self._fwd_index[v]) == 0:
            del self._fwd_index[v]

    def index_obj(self, obj):

        if not IUniqueIdProvider.providedBy(obj):
            raise NonIndexableException("Object %r doesn't provide IUniqueIdProvider" %
                                        obj)
        elif not self._adapter.providedBy(obj):
            raise NonIndexableException(
                "Object %r doesn't provide %r as required" % (obj, self._adapter))

        uid = obj.getUniqueId()
        value = self._adapter(obj)

        if uid not in self._rev_index:
            ts = IOTreeSet()
            self._rev_index[uid]  = ts

        if value in self._rev_index[uid]:
            raise ElementAlreadyInIndexException()
        else:
            self._rev_index[uid].add(value)

        vset = self._fwd_index.get(value)
        if vset is None:
            vset = OOTreeSet()
            self._fwd_index[value] = vset

        if obj in vset:
            raise InconsistentIndexException("%s already in fwd[%s]", (obj, value))
        else:
            vset.insert(obj)
            self._num_objs.change(1)

        return (uid, value)

    def unindex_obj(self, obj):

        uid = obj.getUniqueId()

        if uid in self._rev_index:
            values = self._rev_index[uid]
            del self._rev_index[uid]

            for v in values:
                if v in self._fwd_index:
                    vset = self._fwd_index[v]
                    if obj in vset:
                        vset.remove(obj)
                        self._gc_entry(v)
                    else:
                        raise InconsistentIndexException("%s not in fwd[%s]",
                                                         (obj, v))
                else:
                    raise InconsistentIndexException("%s not in fwd index" % v)
        else:
            raise ElementNotFoundException(uid)

        self._num_objs.change(-1)

    def values(self, *args):
        res = OOTreeSet()
        for s in self._fwd_index.itervalues(*args):
            res = union(res, s)
        return res

    def itervalues(self, *args):
        for s in self._fwd_index.itervalues(*args):
            for t in s:
                yield t

    def iteritems(self):
        for ts, s in self._fwd_index.iteritems():
            for t in s:
                yield ts, t

    def minKey(self):
        return self._fwd_index.minKey()

    def maxKey(self):
        return self._fwd_index.maxKey()

    def __len__(self):
        return self._num_objs()

    def __getitem__(self, item):
        return self._fwd_index[item]

    def get(self, item):
        return self._fwd_index[item]

class IIIndex(FieldIndex):

    """
    Maps integers to sets of integers

    Since we're dealing with ids, no adaptation is done.
    We take advantage of multiunion, which is quite fast.
    """

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
