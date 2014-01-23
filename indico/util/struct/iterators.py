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
Special iterators.
"""

class SortedDictIterator:
    """Iterator for looping a dictionary in sorted order."""

    def __init__(self, data, reverse=False):
        # TODO Python 3 doesn't support iteritems(), use items() instead.
        # items() in Python 2 returns a list and in Python 3 an iterator.
        self.it = iter(sorted(data.iteritems(), reverse=reverse))

    def __iter__(self):
        return self.it

    def next(self):
        return self.it.next()
