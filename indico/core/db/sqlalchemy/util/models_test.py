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
