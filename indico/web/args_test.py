# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

import pytest
from flask.ctx import _AppCtxGlobals
from marshmallow import EXCLUDE, INCLUDE, RAISE
from webargs import fields
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import UnprocessableEntity

from indico.core import signals
from indico.core.marshmallow import mm
from indico.web.args import use_args, use_kwargs, use_rh_args, use_rh_kwargs


class MockRequest:
    def __init__(self, form=None, args=None, json=None, view_args=None, cookies=None, headers=None):
        self.form = ImmutableMultiDict(form or {})
        self.args = ImmutableMultiDict(args or {})
        self.json = json
        self.is_json = json is not None
        self.view_args = view_args or {}
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.mimetype = 'application/x-www-form-urlencoded' if json is None else 'application/json'

    def get_data(self, cache=True):
        return json.dumps(self.json)


class ContextData(fields.String):
    def __init__(self, key, **kwargs):
        self.key = key
        super().__init__(**kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        return value + self.context[self.key]


def make_decorated_func(decorator, schema, req_or_form, **decorator_kwargs):
    req = MockRequest(req_or_form) if not isinstance(req_or_form, MockRequest) else req_or_form

    @decorator(schema, req=req, **decorator_kwargs)
    def fn(args=None, **kwargs):
        if decorator in (use_kwargs, use_rh_kwargs):
            assert args is None
            return kwargs
        else:
            assert not kwargs
            return args

    return fn


@pytest.mark.parametrize('location', ('query', 'form', 'json', 'json_or_form'))
def test_stripping_whitespace(location):
    args = {
        'a': ' 1337 ',
        'b': '\ttest\n',
        'c': ['  12 ', ' foo\t']
    }
    req = {
        'query': MockRequest(args=args),
        'form': MockRequest(form=args),
        'json': MockRequest(json=args),
        'json_or_form': MockRequest(form=args)
    }[location]
    fn = make_decorated_func(use_kwargs, {
        'a': fields.Integer(),
        'b': fields.String(),
        'c': fields.List(fields.String()),
    }, req, location=location)
    assert fn() == {'a': 1337, 'b': 'test', 'c': ['12', 'foo']}


@pytest.mark.parametrize('location', ('query', 'form', 'json', 'json_or_form'))
def test_mutability(location):
    def _schema_pre_load(sender, data, **kwargs):
        data['foo'] = 'bar'

    with signals.plugin.schema_pre_load.connected_to(_schema_pre_load):
        args = {
            'a': '1337',
            'b': 'test',
        }
        req = {
            'query': MockRequest(args=args),
            'form': MockRequest(form=args),
            'json': MockRequest(json=args),
            'json_or_form': MockRequest(form=args)
        }[location]
        fn = make_decorated_func(use_kwargs, {
            'a': fields.Integer(),
            'b': fields.String(),
            'foo': fields.String(),
        }, req, location=location)
        assert fn() == {'a': 1337, 'b': 'test', 'foo': 'bar'}


@pytest.mark.parametrize('location', ('query', 'form', 'json', 'json_or_form'))
@pytest.mark.parametrize('unknown', (None, INCLUDE, EXCLUDE, RAISE))
def test_unknown(location, unknown):
    args = {
        'a': '1337',
        'b': 'test',
        'foo': 'bar',
    }
    req = {
        'query': MockRequest(args=args),
        'form': MockRequest(form=args),
        'json': MockRequest(json=args),
        'json_or_form': MockRequest(form=args)
    }[location]
    # not setting unknown here will use our default of EXCLUDE
    unknown_kw = {'unknown': unknown} if unknown is not None else {}
    fn = make_decorated_func(use_kwargs, {
        'a': fields.Integer(),
        'b': fields.String(),
    }, req, location=location, **unknown_kw)
    if unknown == RAISE:
        with pytest.raises(UnprocessableEntity) as exc_info:
            fn()
        assert exc_info.value.data['messages'] == {'foo': ['Unknown field.']}
    else:
        expected = {'a': 1337, 'b': 'test'}
        if unknown == INCLUDE:
            expected['foo'] = 'bar'
        assert fn() == expected


@pytest.mark.parametrize('location', ('query', 'form', 'json', 'json_or_form'))
@pytest.mark.parametrize('unknown', (None, INCLUDE, EXCLUDE, RAISE))
def test_unknown_schema(location, unknown):
    class TestSchema(mm.Schema):
        # not setting unknown here will use the schema-level default of RAISE
        if unknown is not None:
            Meta = type('Meta', (), {'unknown': unknown})
        a = fields.Integer()
        b = fields.String()

    args = {
        'a': '1337',
        'b': 'test',
        'foo': 'bar',
    }
    req = {
        'query': MockRequest(args=args),
        'form': MockRequest(form=args),
        'json': MockRequest(json=args),
        'json_or_form': MockRequest(form=args)
    }[location]
    fn = make_decorated_func(use_kwargs, TestSchema, req, location=location, unknown=None)
    if unknown == RAISE or unknown is None:
        with pytest.raises(UnprocessableEntity) as exc_info:
            fn()
        assert exc_info.value.data['messages'] == {'foo': ['Unknown field.']}
    else:
        expected = {'a': 1337, 'b': 'test'}
        if unknown == INCLUDE:
            expected['foo'] = 'bar'
        assert fn() == expected


@pytest.mark.parametrize('location', ('query', 'form', 'json'))
def test_lists(location):
    req = {
        'query': MockRequest(args={'single': '123', 'multi': ['456', '789']}),
        'form': MockRequest(form={'single': '123', 'multi': ['456', '789']}),
        'json': MockRequest(json={'single': 123, 'multi': [456, 789]}),
    }[location]
    fn = make_decorated_func(use_kwargs, {
        'single': fields.Integer(),
        'multi': fields.List(fields.Integer()),
    }, req, location=location)
    assert fn() == {'single': 123, 'multi': [456, 789]}


@pytest.mark.parametrize('location', ('query', 'form', 'json'))
def test_meta_location(location):
    req = {
        'query': MockRequest(args={'single': '123', 'multi': ['456', '789']}),
        'form': MockRequest(form={'single': '123', 'multi': ['456', '789']}),
        'json': MockRequest(json={'single': 123, 'multi': [456, 789]}),
    }[location]
    fn = make_decorated_func(use_kwargs, {
        'single': fields.Integer(),
        'multi': fields.List(fields.Integer()),
    }, req)
    if location == 'query':
        assert fn() == {}
    else:
        assert fn() == {'single': 123, 'multi': [456, 789]}


@pytest.mark.parametrize('decorator', (use_kwargs, use_args))
@pytest.mark.parametrize(('partial', 'args', 'result'), (
    # regular
    (False, {'a': '1'}, {'a': 1, 'b': 'no-b'}),
    (False, {'a': '1', 'b': '2'}, {'a': 1, 'b': '2'}),
    (False, {'a': '1', 'c': '3'}, {'a': 1, 'b': 'no-b', 'c': '3'}),
    (False, {'a': '1', 'xxx': 'wtf'}, {'a': 1, 'b': 'no-b'}),
    # partial
    (True, {}, {}),
    (True, {'a': '1'}, {'a': 1}),
    (True, {'b': '1'}, {'b': '1'}),
    (True, {'b': '1', 'c': '3'}, {'b': '1', 'c': '3'}),
    (True, {'a': '1', 'b': '2'}, {'a': 1, 'b': '2'}),
    (True, {'a': '1', 'xxx': 'wtf'}, {'a': 1}),
    # errors
    (False, {}, {'a'}),
    (False, {'c': '3'}, {'a'}),
))
def test_use_args_kwargs(decorator, partial, args, result):
    fn = make_decorated_func(decorator, {
        'a': fields.Integer(required=True),
        'b': fields.String(missing='no-b'),
        'c': fields.String(),
    }, args, partial=partial)

    if isinstance(result, dict):
        assert fn() == result
    else:
        with pytest.raises(UnprocessableEntity) as exc_info:
            fn()
        assert result == exc_info.value.data['messages'].keys()


context_test_params = pytest.mark.parametrize(('partial', 'args', 'result'), (
    # regular
    (False, {'a': '1', 'd': '4'}, {'a': 1, 'b': 'no-b', 'd': '4x'}),
    (False, {'a': '1', 'b': '2'}, {'a': 1, 'b': '2'}),
    (False, {'a': '1', 'xxx': 'wtf'}, {'a': 1, 'b': 'no-b'}),
    # partial
    (True, {}, {}),
    (True, {'d': '4'}, {'d': '4x'}),
    (True, {'d': '4', 'xxx': 'wtf'}, {'d': '4x'}),
))


@pytest.mark.parametrize('decorator', (use_kwargs, use_args))
@context_test_params
def test_use_args_kwargs_context(decorator, partial, args, result):
    fn = make_decorated_func(decorator, {
        'a': fields.Integer(required=True),
        'b': fields.String(missing='no-b'),
        'c': fields.String(),
        'd': ContextData('data'),
    }, args, partial=partial, context={'data': 'x'})
    assert fn() == result


@pytest.mark.parametrize('decorator', (use_rh_kwargs, use_rh_args))
@context_test_params
def test_use_args_kwargs_rh_context(monkeypatch, decorator, partial, args, result):
    fake_g = _AppCtxGlobals()
    fake_g.rh = type('RH', (), {'data': 'x'})
    monkeypatch.setattr('indico.web.args.g', fake_g)
    fn = make_decorated_func(decorator, {
        'a': fields.Integer(required=True),
        'b': fields.String(missing='no-b'),
        'c': fields.String(),
        'd': ContextData('data'),
    }, args, partial=partial, rh_context=('data',))
    assert fn() == result


class TestContextSchema(mm.Schema):
    class Meta:
        rh_context = ('data',)

    a = fields.Integer(required=True)
    b = fields.String(missing='no-b')
    c = fields.String()
    d = ContextData('data')


@pytest.mark.parametrize('decorator', (use_rh_kwargs, use_rh_args))
@context_test_params
def test_use_args_kwargs_rh_context_schema(monkeypatch, decorator, partial, args, result):
    fake_g = _AppCtxGlobals()
    fake_g.rh = type('RH', (), {'data': 'x'})
    monkeypatch.setattr('indico.web.args.g', fake_g)

    fn = make_decorated_func(decorator, TestContextSchema, args, partial=partial)
    assert fn() == result


@pytest.mark.parametrize('decorator', (use_kwargs, use_args, use_rh_kwargs, use_rh_args))
def test_use_args_kwargs_schema_no_instance(decorator):
    with pytest.raises(TypeError) as exc_info:
        make_decorated_func(decorator, TestContextSchema(), {})
    assert str(exc_info.value).startswith('Pass a schema or an argmap')


@pytest.mark.parametrize('decorator', (use_rh_kwargs, use_rh_args))
def test_use_args_kwargs_rh_context_schema_no_kwarg(decorator):
    with pytest.raises(TypeError) as exc_info:
        make_decorated_func(decorator, TestContextSchema, {}, rh_context=('data',))
    assert str(exc_info.value) == 'The `rh_context` kwarg is only supported when passing an argmap'


def test_unknown_locations():
    req = MockRequest(
        form={'f': '1', 'xxx': 'wtf'},
        args={'q': '2', 'xxx': 'wtf'},
        json={'j': '3', 'xxx': 'wtf'},
        view_args={'v': '4', 'xxx': 'wtf'},
        headers={'h': '5', 'xxx': 'wtf'},
        cookies={'c': '6', 'xxx': 'wtf'},
    )

    @use_kwargs({'f': fields.String()}, req=req, location='form')
    @use_kwargs({'q': fields.String()}, req=req, location='query')
    @use_kwargs({'j': fields.String()}, req=req, location='json')
    @use_kwargs({'v': fields.String()}, req=req, location='view_args')
    @use_kwargs({'h': fields.String()}, req=req, location='headers')
    @use_kwargs({'c': fields.String()}, req=req, location='cookies')
    def fn(**kwargs):
        return kwargs

    assert fn() == {
        'f': '1',
        'q': '2',
        'j': '3',
        'v': '4',
        'h': '5',
        'c': '6'
    }
