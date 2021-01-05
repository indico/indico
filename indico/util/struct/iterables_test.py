# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.struct.iterables import grouper


def test_grouper():
    assert list(grouper([], 3)) == []
    assert list(grouper(xrange(6), 3)) == [(0, 1, 2), (3, 4, 5)]
    assert list(grouper(xrange(7), 3)) == [(0, 1, 2), (3, 4, 5), (6, None, None)]
    assert list(grouper(xrange(7), 3, fillvalue='x')) == [(0, 1, 2), (3, 4, 5), (6, 'x', 'x')]
    assert list(grouper(xrange(7), 3, skip_missing=True)) == [(0, 1, 2), (3, 4, 5), (6,)]
