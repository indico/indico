# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from itertools import count

import pytest
from enum import Enum

from indico.util.string import (seems_html, to_unicode, make_unique_token, slugify, text_to_repr, format_repr, snakify,
                                camelize, camelize_keys, snakify_keys, crc32, normalize_phone_number)


def test_seems_html():
    assert seems_html('<b>test')
    assert seems_html('a <b> c')
    assert not seems_html('test')
    assert not seems_html('a < b > c')


@pytest.mark.parametrize(('input', 'output'), (
    (b'foo', u'foo'),            # ascii
    (u'foo', u'foo'),            # unicode
    (b'm\xc3\xb6p', u'm\xf6p'),  # utf8
    (b'm\xf6p', u'm\xf6p'),      # latin1
    (b'm\xc3\xb6p m\xf6p',       # mixed...
     u'm\xc3\xb6p m\xf6p'),      # ...decoded as latin1
))
def test_to_unicode(input, output):
    assert to_unicode(input) == output


def test_make_unique_token(monkeypatch):
    monkeypatch.setattr('indico.util.string.uuid4', lambda _counter=count(): str(next(_counter)))
    tokens = {'1', '3'}

    def _get_token():
        token = make_unique_token(lambda t: t not in tokens)
        tokens.add(token)
        return token

    assert _get_token() == '0'
    assert _get_token() == '2'
    assert _get_token() == '4'
    assert _get_token() == '5'


@pytest.mark.parametrize(('input', 'output'), (
    (b'this is a    test',    'this-is-a-test'),
    (u'this is \xe4    test', 'this-is-ae-test'),
    (u'12345!xxx   ',         '12345xxx'),
))
def test_slugify(input, output):
    assert slugify(input) == output


@pytest.mark.parametrize(('input', 'lower', 'output'), (
    ('Test', True, 'test'),
    ('Test', False, 'Test'),
    (u'm\xd6p', False, 'mOep'),
    (u'm\xd6p', True, 'moep')
))
def test_slugify_lower(input, lower, output):
    assert slugify(input, lower=lower) == output


@pytest.mark.parametrize(('input', 'html', 'max_length', 'output'), (
    ('Hello\n  \tWorld',  False, None, 'Hello World'),
    ('Hello<b>World</b>', False, None, 'Hello<b>World</b>'),
    ('Hello<b>World</b>', True,  None, 'HelloWorld'),
    ('Hi <b>a</b> <br>',  True,  None, 'Hi a'),
    ('x' * 60,            False, None, 'x' * 60),
    ('x' * 60,            False, 50,   'x' * 50 + '...'),
    ('x' * 50,            False, 50,   'x' * 50)
))
def test_text_to_repr(input, html, max_length, output):
    assert text_to_repr(input, html=html, max_length=max_length) == output


@pytest.mark.parametrize(('args', 'kwargs', 'output'), (
    ((), {}, '<Foo()>'),
    (('id', 'hello', 'dct'), {}, "<Foo(1, world, {'a': 'b'})>"),
    (('id',), {}, '<Foo(1)>'),
    (('id', 'enum'), {}, '<Foo(1, foo)>'),
    (('id',), {'flag1': True, 'flag0': False}, '<Foo(1)>'),
    (('id',), {'flag1': False, 'flag0': False}, '<Foo(1, flag1=True)>'),
    (('id',), {'flag1': False, 'flag0': True}, '<Foo(1, flag0=False, flag1=True)>'),
    (('id',), {'flag1': False, 'flag0': True, '_text': u'moo'}, '<Foo(1, flag0=False, flag1=True): "moo">')

))
def test_format_repr(args, kwargs, output):
    class Foo(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class MyEnum(Enum):
        foo = 'bar'

    obj = Foo(id=1, enum=MyEnum.foo, hello='world', dct={'a': 'b'}, flag1=True, flag0=False)
    assert format_repr(obj, *args, **kwargs) == output


@pytest.mark.parametrize(('input', 'output'), (
    ('',       ''),
    ('FooBar', 'foo_bar'),
    ('fooBar', 'foo_bar'),
    ('fooBAR', 'foo_bar'),
    ('bar',    'bar'),
    ('Bar',    'bar'),
    ('aaBbCc', 'aa_bb_cc'),
))
def test_snakify(input, output):
    assert snakify(input) == output


@pytest.mark.parametrize(('input', 'output'), (
    ('_',        '_'),
    ('_foo_bar', '_fooBar'),
    ('foo',      'foo'),
    ('fooBar',   'fooBar'),
    ('foo_bar',  'fooBar'),
    ('aa_bb_cC', 'aaBbCc'),
))
def test_camelize(input, output):
    assert camelize(input) == output


def test_camelize_keys():
    d = {'fooBar': 'foo', 'bar_foo': 123, 'moo_bar': {'hello_world': 'test'},
         'nested': [{'is_dict': True}, 'foo', ({'a_b': 'c'},)]}
    orig = d.copy()
    d2 = camelize_keys(d)
    assert d == orig  # original dict not modified
    assert d2 == {'fooBar': 'foo', 'barFoo': 123, 'mooBar': {'helloWorld': 'test'},
                  'nested': [{'isDict': True}, 'foo', ({'aB': 'c'},)]}


def test_snakify_keys():
    d = {'sn_case': 2, 'shouldBeSnakeCase': 3, 'snake': 4, 'snake-case': 5, 'inner': {'innerDict': 2}}
    orig = d.copy()
    d2 = snakify_keys(d)
    assert d == orig
    assert d2 == {'sn_case': 2, 'should_be_snake_case': 3, 'snake': 4, 'snake-case': 5, 'inner': {'inner_dict': 2}}


def test_crc32():
    assert crc32(u'm\xf6p') == 2575016153
    assert crc32(u'm\xf6p'.encode('utf-8')) == 2575016153
    assert crc32(b'') == 0
    assert crc32(b'hello world\0\1\2\3\4') == 140159631


@pytest.mark.parametrize(('input', 'output'), (
    ('',                ''),
    ('+41785324567',    '+41785324567'),
    ('++454545455',     '+454545455'),
    ('123-456-789',     '123456789'),
    ('0123456x0+',      '0123456x0'),
    ('+48 785 326 691', '+48785326691'),
    ('0048785326691',   '0048785326691'),
    ('123-456-xxxx',    '123456xxxx')
))
def test_normalize_phone_number(input, output):
    assert normalize_phone_number(input) == output
