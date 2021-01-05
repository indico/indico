# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core.db.sqlalchemy.util.models import auto_table_args


@pytest.mark.parametrize(('args', 'kw', 'expected'), (
    # simple tuples
    ([('foo',), ('bar',)],
     {},
     ('foo', 'bar')),
    # simple dicts
    ([{'a': 'b'}, {'c': 'd'}],
     {},
     ({'a': 'b', 'c': 'd'})),
    # all possible types
    ([('foo',), {'a': 'b'}, ('bar', {'a': 'c', 'x': 'y'})],
     {},
     ('foo', 'bar', {'a': 'c', 'x': 'y'})),
    # all empty
    ([], {}, ()),
    ([()], {}, ()),
    # extra kwargs
    ([('foo',), ('bar',)],
     {'troll': 'fish'},
     ('foo', 'bar', {'troll': 'fish'})),
))
def test_auto_table_args(args, kw, expected):
    classes = []
    for i, arg in enumerate(args):
        name = 'Test{}'.format(i)
        classes.append(type(name, (object,), {'_{}__auto_table_args'.format(name): arg}))
    cls = type('Test', tuple(classes), {})
    assert auto_table_args(cls, **kw) == expected
