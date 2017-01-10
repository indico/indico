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
from mock import MagicMock

from indico.util.signals import values_from_signal, named_objects_from_signal


def _make_signal_response(objects):
    return [(None, obj) for obj in objects]


def _make_gen(*values):
    for value in values:
        yield value


@pytest.mark.parametrize(('retvals', 'expected'), (
    (('a', 'b', 'c'),            {'a', 'b', 'c'}),
    (('a', _make_gen('b', 'c')), {'a', 'b', 'c'}),
))
def test_values_from_signal(retvals, expected):
    signal_response = _make_signal_response(retvals)
    assert values_from_signal(signal_response) == expected


def test_values_from_signal_single_value():
    vals = ('a', _make_gen('b', 'c'))
    signal_response = _make_signal_response(vals)
    assert values_from_signal(signal_response, single_value=True) == set(vals)
    assert values_from_signal(signal_response) == {'a', 'b', 'c'}


def test_values_from_signal_skip_none():
    vals = ('a', None, 'b', 'c')
    signal_response = _make_signal_response(vals)
    assert values_from_signal(signal_response, skip_none=False) == set(vals)
    assert values_from_signal(signal_response) == set(vals) - {None}


def test_values_from_signal_as_list():
    vals = ('a', 'b', 'c')
    signal_response = _make_signal_response(vals)
    assert values_from_signal(signal_response, as_list=True) == list(vals)
    assert values_from_signal(signal_response) == set(vals)


def test_values_from_signal_multi_value_types():
    vals = ('a', ['b', 'c'])
    signal_response = _make_signal_response(vals)
    with pytest.raises(TypeError):
        # list is unhashable, can't be added to a set
        values_from_signal(signal_response)
    assert values_from_signal(signal_response, as_list=True) == list(vals)
    assert values_from_signal(signal_response, multi_value_types=list) == {'a', 'b', 'c'}


def test_values_from_signal_return_plugins():
    vals = ('a', 'b', 'c')
    signal_response = _make_signal_response(vals) + [(MagicMock(indico_plugin='foo'), 'd')]
    assert values_from_signal(signal_response, return_plugins=True) == set(zip([None] * 3, vals) + [('foo', 'd')])
    assert values_from_signal(signal_response) == set(vals + ('d',))


@pytest.mark.parametrize('name_attr', ('name', 'foobar'))
def test_named_objects_from_signal(name_attr):
    objects = [type('Dummy', (object,), {name_attr: name}) for name in ('a', 'b')]
    signal_response = _make_signal_response(objects)
    assert named_objects_from_signal(signal_response, name_attr=name_attr) == {'a': objects[0], 'b': objects[1]}


def test_named_objects_from_signal_plugin_attr():
    objects = [type('Dummy', (object,), {'name': name}) for name in ('a', 'b')]
    signal_response = _make_signal_response(objects)
    signal_response[-1] = (MagicMock(indico_plugin='foo'), signal_response[-1][1])
    rv = named_objects_from_signal(signal_response, plugin_attr='plugin')
    assert rv == {'a': objects[0], 'b': objects[1]}
    assert rv['a'].plugin is None
    assert rv['b'].plugin == 'foo'


def test_named_objects_from_signal_duplicate():
    objects = [type('Dummy', (object,), {'name': name}) for name in ('a', 'a', 'b', 'c', 'c')]
    signal_response = _make_signal_response(objects)
    with pytest.raises(RuntimeError) as exc_info:
        named_objects_from_signal(signal_response)
    assert str(exc_info.value) == 'Non-unique object names: a, c'
