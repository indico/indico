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
Queue-style data structures
"""

from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOTreeSet
from BTrees.Length import Length
from persistent import Persistent

class DuplicateElementException(Exception):
    """
    Tried to insert the same element twice in the queue
    """


class PersistentWaitingQueue(Persistent):
    """
    A Waiting queue, implemented using a map structure (BTree...)
    It is persistent, but very vulnerable to conflicts. This is due to the
    fact that sets are used as container, and there can happen a situation
    where two different sets are assigned to the same timestamp. This will
    for sure result in conflict.

    That said, the commits of objects like these have to be carefully
    synchronized. See `indico.modules.scheduler.controllers` for more info
    (particularly the way we use the 'spool').
    """

    def __init__(self):
        super(PersistentWaitingQueue, self).__init__()
        self._reset()

    def _reset(self):
        # this counter keeps the number of elements
        self._elem_counter = Length(0)
        self._container = IOBTree()

    def _gc_bin(self, t):
        """
        'garbage-collect' bins
        """
        if len(self._container[t]) == 0:
            del self._container[t]

    def _check_gc_consistency(self):
        """
        'check that there are no empty bins'
        """
        for t in self._container:
            if len(self._container[t]) == 0:
                return False

        return True

    def enqueue(self, t, obj):
        """
        Add an element to the queue
        """

        if t not in self._container:
            self._container[t] = OOTreeSet()

        if obj in self._container[t]:
            raise DuplicateElementException(obj)

        self._container[t].add(obj)
        self._elem_counter.change(1)

    def dequeue(self, t, obj):
        """
        Remove an element from the queue
        """
        self._container[t].remove(obj)
        self._gc_bin(t)
        self._elem_counter.change(-1)

    def _next_timestamp(self):
        """
        Return the next 'priority' to be served
        """
        i = iter(self._container)

        try:
            t = i.next()
            return t
        except StopIteration:
            return None

    def peek(self):
        """
        Return the next element
        """
        t = self._next_timestamp()
        if t:
            # just to be sure
            assert(len(self._container[t]) != 0)

            # find the next element
            i = iter(self._container[t])
            # store it
            elem = i.next()

            # return the element
            return t, elem
        else:
            return None

    def pop(self):
        """
        Remove and return the next set of elements to be processed
        """
        pair = self.peek()
        if pair:
            self.dequeue(*pair)

            # return the element
            return pair
        else:
            return None

    def nbins(self):
        """
        Return the number of 'bins' (map entries) currently used
        """
        # get 'real' len()
        return len(self._container)

    def __len__(self):
        return self._elem_counter()


    def __getitem__(self, param):
        return self._container.__getitem__(param)

    def __iter__(self):

        # tree iterator
        for tstamp in iter(self._container):
            cur_set = self._container[tstamp]
            try:
                # set iterator
                for elem in cur_set:
                    yield tstamp, elem
            except StopIteration:
                pass


