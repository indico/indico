# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import MagicMock

import pytest

from indico.util.signals import named_objects_from_signal, values_from_signal


def _make_signal_response(objects):
    return [(None, obj) for obj in objects]


def _make_gen(*values):
    yield from values


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
    assert values_from_signal(signal_response, return_plugins=True) == set(list(zip([None] * 3, vals)) + [('foo', 'd')])
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
