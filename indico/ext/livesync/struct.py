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

import random

# ZODB related imports
from persistent import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOTreeSet, OOSet
from ZODB.PersistentMapping import PersistentMapping


class MultiPointerTrack(Persistent):
    """
    A MultiPointerTrack is a kind of structure that is based on an IOBTree, where
    each entry contains an ordered set (or list, depending on the implementation)
    of elements. Then, several "pointers" can be created, which point to different
    positions of the track (very much like runners in a race track).
    This class is abstract, implementations should be derived.
    """

    def __init__(self, elemContainer):
        self._container = IOBTree()
        self._pointers = PersistentMapping()
        self._elemContainer = elemContainer

    def addPointer(self, pid, startPos = None):
        """
        Registers a new pointer
        """
        self._pointers[pid] = None
        if startPos:
            self.movePointer(pid, startPos)

    def prepareEntry(self, timestamp):
        """
        Creates an empty sub-structure (elemContainer) for a given timestamp
        """
        self._container[timestamp] = self._elemContainer()

    def getCurrentPosition(self, pid):
        """
        Returns the current entry (set/list) for a given pointer id
        """
        currentPos = self._pointers[pid]
        # TODO: assertion? check?
        return self._container[currentPos]

    def getPointerTimestamp(self, pid):
        """
        Gets the current 'position' of a pointer (id)
        """
        return self._pointers[pid]

    def __getitem__(self, timestamp):
        """
        Implements __getitem__, so that mpt[timestamp] works
        """
        if isinstance(timestamp, slice):
            return self._getSlice(timestamp)
        else:
            return self._container[timestamp]

    def _getSlice(self, s):
        """
        Calculates a slice of the structure (timestamp-wise)
        """
        if s.step != None:
            raise TypeError('Extended slices are not accepted here')
        return self._container.values(s.start, s.stop)

    def values(self, *args):
        """
        Return values or ranges (timestamps) of the structure
        """
        return self._container.values(*args)

    def add(self, timestamp, value):
        """
        Adds a value to the container corresponding to a specific timestamp
        """
        if timestamp not in self._container:
            self.prepareEntry(timestamp)

        self._append(timestamp, value)

    def _pointerIterator(self, pid, func):
        """
        Iterates over the positions that are left (till the end of the track) for
        a given pointer (id). Takes a function that is applied to yielded values
        """
        ptrPos = self._pointers[pid]

        it = self._container.iteritems(ptrPos)
            # consume a single position
        if ptrPos != None:
            it.next()

        for entry in it:
            for elem in entry[1]:
                yield elem

    def pointerIterValues(self, pid):
        """
        Iterates over the positions that are left (till the end of the track) for
        a given pointer (id) - iterates over values
        """
        return self._pointerIterator(pid, lambda x: x[1])

    def pointerIterItems(self, pid):
        """
        Iterates over the positions that are left (till the end of the track) for
        a given pointer (id) - iterates over key-value pairs (iteritems)
        """

        return self._pointerIterator(pid, lambda x: x)

    def movePointer(self, pid, timestamp):
        """
        Moves a given pointer (id) to a given timestamp
        """
        if pid not in self._pointers:
            raise KeyError("Pointer '%s' doesn't seem to exist!" % pid)
        if timestamp < self._container.minKey() or \
               timestamp > self._container.maxKey():
            raise ValueError("timestamp outside bounds")
        else:
            self._pointers[pid] = timestamp

    def __len__(self):
        """
        Returns the number of timestamp entries
        """
        return len(self._container)

    def __delitem__(self, item):
        """
        Deletes a given timestamp entry (or range)
        """
        self._container.__delitem__(item)

    def __iter__(self):
        """
        Iterates over the whole structure, element by element (goes inside containers)
        """
        for entry in self._container.itervalues():
            for elem in entry:
                yield elem


class SetMultiPointerTrack(MultiPointerTrack):
    """
    OOSet-based MultiPointerTrack implementation. As OOSets are ordered, order is not
    lost. Order will depend on the __cmp__ method implemented by the contained objects.
    """

    def __init__(self):
        super(SetMultiPointerTrack, self).__init__(OOSet)

    def _append(self, timestamp, val):
        self._container[timestamp].add(val)


class ListMultiPointerTrack(MultiPointerTrack):
    """
    List-based MultiPointerTrack implementation
    """

    def __init__(self):
        super(ListMultiPointerTrack, self).__init__(list)

    def _append(self, timestamp, val):
        self._container[timestamp].append(val)
