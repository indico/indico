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
from BTrees.OOBTree import OOBTree, OOTreeSet, OOSet, union
from persistent import Persistent

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


class Index(Persistent):
    pass


class SIndex(Index):

    _fwd_class = None
    _fwd_set_class = None

    def __init__(self, adapter):
        self._adapter = adapter
        self._fwd_index = self._fwd_class()
        self._num_objs = Length(0)

    def _gc_entry(self, v):
        """
        'Garbage collect' empty set entries
        """
        if len(self._fwd_index[v]) == 0:
            del self._fwd_index[v]

    def index_obj(self, obj):

        value = self._adapter(obj)
        vset = self._fwd_index.get(value, self._fwd_set_class())

        if obj in vset:
            raise InconsistentIndexException("%s already in fwd[%s]", (obj, value))
        else:
            vset.insert(obj)
            self._num_objs.change(1)

        self._fwd_index[value] = vset

    def _unindex_obj_from_key(self, key, obj):
        if key in self._fwd_index:
            vset = self._fwd_index[key]
            if obj in vset:
                vset.remove(obj)
                self._fwd_index[key] = vset
                self._gc_entry(key)
            else:
                raise InconsistentIndexException("'%s' not in fwd[%s]",
                                                 (obj, key))
        else:
            raise InconsistentIndexException("'%s' not in fwd index" % key)

    def unindex_obj(self, obj):
        """
        Slightly dumber than the one in DIndex, takes the indexation value (key)
        instead of looking it up in the reverse index
        """
        key = self._adapter(obj)
        self._unindex_obj_from_key(key, obj)
        self._num_objs.change(-1)


    def values(self, *args):
        res = self._fwd_set_class()
        for s in self._fwd_index.itervalues(*args):
            res = union(res, s)
        return res

    def itervalues(self, *args):
        for s in self._fwd_index.itervalues(*args):
            for t in s:
                yield t

    def iteritems(self, *args):
        for ts, s in self._fwd_index.iteritems(*args):
            for t in s:
                yield ts, t

    def minKey(self):
        return self._fwd_index.minKey()

    def maxKey(self):
        return self._fwd_index.maxKey()

    def __iter__(self):
        return iter(self._fwd_index)

    def __len__(self):
        return self._num_objs()

    def __getitem__(self, item):
        return self._fwd_index[item]

    def get(self, item, default=None):
        return self._fwd_index.get(item, default)


class DIndex(SIndex):
    """
    Bidirectional Index Class

    objects need to implement IUniqueIdProvider as well, as an id is needed for
    the backward-index (OOBTrees don't accept persisten objects as keys)
    """

    _rev_class = None
    _rev_set_class = None

    def __init__(self, adapter):
        super(DIndex, self).__init__(adapter)
        self._rev_index = self._rev_class()

    def has_obj(self, obj):
        return obj.getUniqueId() in self._rev_index

    def index_obj(self, obj):

        if not IUniqueIdProvider.providedBy(obj):
            raise NonIndexableException("Object %r doesn't provide IUniqueIdProvider" %
                                        obj)
        elif not self._adapter.providedBy(obj):
            raise NonIndexableException(
                "Object %r doesn't provide %r as required" % (obj, self._adapter))

        uid = obj.getUniqueId()
        value = self._adapter(obj)

        ts = self._rev_index.get(uid, self._rev_set_class())

        if value in ts:
            raise ElementAlreadyInIndexException((value, obj))
        else:
            ts.index(value)

        self._rev_index[uid] = ts

        super(DIndex, self).index_obj(obj)

        return (uid, value)

    def unindex_obj(self, obj):

        uid = obj.getUniqueId()

        if uid in self._rev_index:
            keys = self._rev_index[uid]
            del self._rev_index[uid]

            for key in keys:
                self._unindex_obj_from_key(key, obj)
        else:
            raise ElementNotFoundException(uid)

        self._num_objs.change(-1)

    def _check(self, dbi=None):
        """
        Simple sanity check
        """
        i = 0
        # check that the elements in fwd index are also in rev index
        cls = self.__class__.__name__
        for ts, eset in self._fwd_index.iteritems():
            if not eset:
                yield "[%s] Element set at '%s' is empty" % ts
            for elem in eset:
                uid = elem.getUniqueId()
                key = self._adapter(elem)
                if uid not in self._rev_index:
                    yield "[%s] An entry for '%s'(%s) should exist in _rev_index" \
                          % (cls, uid, ts)
                elif key not in self._rev_index[uid]:
                    yield "[%s] Element '%s'(%s) should be in _rev_index['%s']" \
                          % (cls, uid, ts, key)
            if dbi and i % 1000 == 999:
                dbi.abort()
            i += 1

        # now the opposite
        for uid, kset in self._rev_index.iteritems():
            for key in kset:
                if key not in self._fwd_index:
                    yield "[%s] Key '%s' not found in _fwd_index" % (cls, key)
                elif uid not in map(lambda x:x.getUniqueId(), self._fwd_index[key]):
                    yield "[%s] Object '%s' not in _fwd_index[%s]" % (cls, uid, key)
            if dbi and i % 1000 == 999:
                dbi.abort()
            i += 1


class SIOIndex(DIndex):
    """
    Maps integer keys to objects
    int -> set(obj)
    """
    _fwd_class = IOBTree
    _fwd_set_class = OOTreeSet


class IOIndex(DIndex):
    """
    Maps integer keys to objects
    int -> set(obj)
    uid(obj) -> set(int)
    """
    _fwd_class = IOBTree
    _rev_class = OOBTree
    _fwd_set_class = OOTreeSet
    _rev_set_class = IOTreeSet


class OOIndex(DIndex):
    """
    Maps object keys to objects
    obj -> set(obj)
    uid(obj) -> set(obj)
    """
    _fwd_class = OOBTree
    _rev_class = OOBTree
    _fwd_set_class = OOSet
    _rev_set_class = OOSet


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
