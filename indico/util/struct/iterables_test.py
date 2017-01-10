# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from indico.util.struct.iterables import grouper


def test_grouper():
    assert list(grouper([], 3)) == []
    assert list(grouper(xrange(6), 3)) == [(0, 1, 2), (3, 4, 5)]
    assert list(grouper(xrange(7), 3)) == [(0, 1, 2), (3, 4, 5), (6, None, None)]
    assert list(grouper(xrange(7), 3, fillvalue='x')) == [(0, 1, 2), (3, 4, 5), (6, 'x', 'x')]
    assert list(grouper(xrange(7), 3, skip_missing=True)) == [(0, 1, 2), (3, 4, 5), (6,)]
