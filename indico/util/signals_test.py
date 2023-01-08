# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import MagicMock

import pytest

from indico.core import signals
from indico.util.signals import interceptable_sender, make_interceptable, named_objects_from_signal, values_from_signal


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


def test_interceptable():
    def foo(a, /, b, c=1, *, d=123, **kw):
        return f'{a=} {b=} {c=} {d=} {kw=}'

    def _handler(sender, func, args, ctx, **kwargs):
        args.apply_defaults()
        args.arguments['c'] = 'ccc'
        args.arguments['kw'].setdefault('lol', 'funny')
        if ctx:
            return {'return': 'value', 'orig': func(*args.args, **args.kwargs)}

    foo = make_interceptable(foo)
    foo2 = make_interceptable(foo, ctx=True)
    with signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(foo)):
        assert foo(1, 2) == "a=1 b=2 c='ccc' d=123 kw={'lol': 'funny'}"
        assert foo(1, 2, lol='test') == "a=1 b=2 c='ccc' d=123 kw={'lol': 'test'}"
        assert foo2(3, 4) == {'return': 'value', 'orig': "a=3 b=4 c='ccc' d=123 kw={'lol': 'funny'}"}


def test_interceptable_method():
    class Foo:
        def __init__(self, x):
            self.x = x

        def bar(self, a):
            return f'{self.x=} {a=}'

    def _handler(sender, func, args, ctx, **kwargs):
        args.arguments['a'] = 'x'

    foo = Foo(1)
    bar = make_interceptable(foo.bar)
    with signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(Foo.bar)):
        assert bar(2) == "self.x=1 a='x'"


def test_interceptable_method_decorated():
    class Foo:
        def __init__(self, x):
            self.x = x

        @make_interceptable
        def bar(self, a):
            return f'{self.x=} {a=}'

    def _handler(sender, func, args, ctx, **kwargs):
        args.arguments['a'] = 'x'

    with signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(Foo.bar)):
        assert Foo(1).bar(2) == "self.x=1 a='x'"


def test_interceptable_starargs():
    def foo(a, *va, **kw):
        return f'{a=} {va=} {kw=}'

    def _handler(sender, func, args, **kwargs):
        args.apply_defaults()
        assert args.arguments == {'a': 1, 'va': (2, 3), 'kw': {'x': 4}}
        args.arguments['va'] = (*args.arguments['va'], 33)
        args.arguments['kw'] = {**args.arguments['kw'], 'y': 5}

    foo = make_interceptable(foo, 'test')
    with signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(foo, 'test')):
        assert foo(1, 2, 3, x=4) == "a=1 va=(2, 3, 33) kw={'x': 4, 'y': 5}"


@pytest.mark.parametrize(('caller_key', 'receiver_key'), (
    (None, None),
    (None, 'test'),
    ('test', None),
    ('test', 'test'),
    ('foo', 'bar'),
))
def test_interceptable_key(caller_key, receiver_key):
    called = False

    def _handler(sender, func, args, **kwargs):
        nonlocal called
        called = True

    foo = make_interceptable(lambda a: f'{a=}', caller_key)
    with signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(foo, receiver_key)):
        assert foo(1) == 'a=1'
    assert called == (caller_key == receiver_key)


def test_interceptable_override_multi():
    foo = make_interceptable(lambda a: f'{a=}')
    with (
        signals.plugin.interceptable_function.connected_to(lambda *a, **kw: 'x', interceptable_sender(foo)),
        signals.plugin.interceptable_function.connected_to(lambda *a, **kw: 'y', interceptable_sender(foo)),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            foo(1)
        assert str(exc_info.value) == f'Multiple results returned for interceptable {interceptable_sender(foo)}'


def test_interceptable_override_none():
    foo = make_interceptable(lambda: 'nope')
    with signals.plugin.interceptable_function.connected_to(lambda *a, **kw: None, interceptable_sender(foo)):
        # simply returning None won't work
        assert foo() == 'nope'
    with signals.plugin.interceptable_function.connected_to(lambda *a, RETURN_NONE, **kw: RETURN_NONE,
                                                            interceptable_sender(foo)):
        assert foo() is None


def test_interceptable_multi():
    def _handler(sender, func, args, **kwargs):
        args.arguments['a'] *= 2

    def _handler2(sender, func, args, **kwargs):
        args.arguments['a'] *= 3

    foo = make_interceptable(lambda a: a)
    with signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(foo)):
        assert foo(1) == 2
    with (
        signals.plugin.interceptable_function.connected_to(_handler, interceptable_sender(foo)),
        signals.plugin.interceptable_function.connected_to(_handler2, interceptable_sender(foo)),
    ):
        assert foo(1) == 6
