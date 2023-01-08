# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core import signals
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
        name = f'Test{i}'
        classes.append(type(name, (object,), {f'_{name}__auto_table_args': arg}))
    cls = type('Test', tuple(classes), {})
    assert auto_table_args(cls, **kw) == expected


@pytest.mark.usefixtures('db')
def test_signal_query(dummy_user, create_event):
    from indico.modules.events.models.events import Event

    def _fn(sender, query, **kwargs):
        assert sender == 'test'
        return query.filter(Event.title != 'evt2')

    with signals.core.db_query.connected_to(_fn, sender='test'):
        assert not dummy_user.created_events.signal_query('test').has_rows()
        assert not dummy_user.created_events.has_rows()
        create_event(title='evt1')
        create_event(title='evt2')
        assert dummy_user.created_events.count() == 2
        assert dummy_user.created_events.signal_query('test').count() == 1
        assert Event.query.count() == 2
        assert Event.query.signal_query('test').count() == 1
    # signal no longer bound -> no modification applied
    assert dummy_user.created_events.signal_query('test').count() == 2
    assert Event.query.signal_query('test').count() == 2
