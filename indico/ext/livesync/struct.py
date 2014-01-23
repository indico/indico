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

# ZODB related imports
from persistent import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOSet
from ZODB.PersistentMapping import PersistentMapping


class timestamp(int):
    """
    This class is used to reverse the order of the index
    """

    def __eq__(self, num):
        if isinstance(num, timestamp):
            return self.__cmp__(num) == 0
        else:
            return False

    def __ne__(self, num):
        return not self.__eq__(num)

    def __cmp__(self, num):
        return - int.__cmp__(self, int(num))

    def _assertType(self, obj):
        """
        Make sure this is a timestamp
        """
        if not isinstance(obj, timestamp):
            raise TypeError('timestamp object expected')

    def __sub__(self, num):
        self._assertType(num)
        return timestamp(int.__sub__(self, num))

    def __add__(self, num):
        self._assertType(num)
        return timestamp(int.__add__(self, num))

    def __repr__(self):
        return "^%s" % (int.__repr__(self))

    @classmethod
    def fromObject(cls, obj):
        return obj.__timestamp__()


class EmptyTrackException(Exception):
    pass


class MultiPointerTrack(Persistent):
    """
    A MultiPointerTrack is a kind of structure that is based on an IOBTree,
    where each entry contains an ordered set (or list, depending on the
    implementation) of elements. Then, several "pointers" can be created,
    which point to different positions of the track (very much like runners
    in a race track).
    This class is abstract, implementations should be derived.
    """

    def __init__(self, elemContainer):
        self._container = OOBTree()
        self._pointers = PersistentMapping()
        self._elemContainer = elemContainer

        # initialize first entry
        #self._container[timestamp(0)] = elemContainer()

    def addPointer(self, pid, startPos=None):
        """
        Registers a new pointer
        """
        self._pointers[pid] = None
        if startPos:
            self.movePointer(pid, startPos)

    def removePointer(self, pid):
        """
        Removes a pointer from the list
        """
        del self._pointers[pid]

    def prepareEntry(self, ts):
        """
        Creates an empty sub-structure (elemContainer) for a given timestamp
        """
        self._container[timestamp(ts)] = self._elemContainer()

    def getCurrentPosition(self, pid):
        """
        Returns the current entry (set/list) for a given pointer id
        """
        currentPos = self._pointers[pid]
        # TODO: assertion? check?
        return self._container[timestamp(currentPos)]

    def getPointerTimestamp(self, pid):
        """
        Gets the current 'position' of a pointer (id)
        """
        return self._pointers[pid]

    def __getitem__(self, ts):
        """
        Implements __getitem__, so that mpt[timestamp] works
        """
        if isinstance(ts, slice):
            return self._getSlice(ts)
        else:
            return self._container[timestamp(ts)]

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

        fargs = []

        for a in args:
            if a == None:
                fargs.append(None)
            else:
                fargs.append(timestamp(a))

        return self._container.values(*fargs)

    def _append(self, ts, val):
        """
        Should be overloaded.
        """
        raise Exception("Unimplemented method")

    def add(self, intTS, value):
        """
        Adds a value to the container corresponding to a specific timestamp
        """
        ts = timestamp(intTS)
        if ts not in self._container:
            self.prepareEntry(intTS)

        self._append(ts, value)

    def _pointerIterator(self, pid, func, till=None):
        """
        Iterates over the positions that are left (till the end of the track)
        for a given pointer (id). Takes a function that is applied to yielded
        values
        """

        return self.iterate(self._pointers[pid], till, func)

    def iterate(self, fromPos=None, till=None, func=(lambda x: x)):
        """
        Generator that iterates through the data structure
        """
        if till != None:
            till = timestamp(till)
            # negative numbers mean "last but one", "last but two", etc...
            if till == timestamp(-1):
                # most common case
                till = self._container.maxKey() - timestamp(1)

        if fromPos != None:
            fromPos = timestamp(fromPos)

        for ts, entry in self._container.iteritems(till, fromPos):
            if fromPos and ts == fromPos:
                # stop immediately if we're past fromPos
                raise StopIteration

            for elem in entry:
                yield func((int(ts), elem))

    def mostRecentTS(self, maximum=None):
        """
        Returns most recent timestamp in track (minimum key)
        If 'maximum' is provided, return it if less recent
        """

        # check that the tree has something
        if len(self._container) == 0:
            raise EmptyTrackException()

        mr = self._container.minKey()

        if maximum:
            maximum = timestamp(maximum)
            # in timestamp logic, max() returns the oldest
            return max(mr, maximum)
        else:
            return mr

    def oldestTS(self):
        """
        Returns least recent timestamp in track (maximum key)
        """

        # check that the tree has something
        if len(self._container) == 0:
            raise EmptyTrackException()

        return self._container.maxKey()

    def pointerIterValues(self, pid, till=None):
        """
        Iterates over the positions that are left (till the end of the track)
        for a given pointer (id) - iterates over values
        """
        return self._pointerIterator(pid, lambda x: x[1], till=till)

    def pointerIterItems(self, pid, till=None):
        """
        Iterates over the positions that are left (till the end of the track)
        for a given pointer (id) - iterates over key-value pairs (iteritems)
        """

        return self._pointerIterator(pid, lambda x: x, till=till)

    def is_empty(self):
        for __, ___ in self._container.iteritems():
            return False
        return True

    def movePointer(self, pid, pos):
        """
        Moves a given pointer (id) to a given timestamp
        """
        if pid not in self._pointers:
            raise KeyError("Pointer '%s' doesn't seem to exist!" % pid)

        # check that the tree has something
        if self.is_empty():
            raise EmptyTrackException()

        self._pointers[pid] = pos

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
        Iterates over the whole structure, element by elements
        (goes inside containers)
        """
        return self.iterate()

    def __contains__(self, ts):
        return timestamp(ts) in self._container


class SetMultiPointerTrack(MultiPointerTrack):
    """
    OOSet-based MultiPointerTrack implementation. As OOSets are ordered, order
    is not lost. Order will depend on the __cmp__ method implemented by the
    contained objects.
    """

    def __init__(self):
        super(SetMultiPointerTrack, self).__init__(OOSet)

    def _append(self, ts, val):
        self._container[ts].add(val)


class ListMultiPointerTrack(MultiPointerTrack):
    """
    List-based MultiPointerTrack implementation
    """

    def __init__(self):
        super(ListMultiPointerTrack, self).__init__(list)

    def _append(self, ts, val):
        self._container[ts].append(val)
