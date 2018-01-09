# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from enum import Enum
from itertools import count

import pytest

from indico.util.string import (camelize, camelize_keys, crc32, format_repr, make_unique_token, normalize_phone_number,
                                render_markdown, sanitize_email, seems_html, slugify, snakify, snakify_keys, strip_tags,
                                text_to_repr, to_unicode)


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


def test_slugify_maxlen():
    assert slugify('foo bar', maxlen=5) == 'foo-b'


def test_slugify_args():
    assert slugify('foo', 123, 'bar') == 'foo-123-bar'
    assert slugify(u'm\xf6p'.encode('utf-8'), 123, u'b\xe4r') == 'moep-123-baer'


@pytest.mark.parametrize(('input', 'lower', 'output'), (
    ('Test', True, 'test'),
    ('Test', False, 'Test'),
    (u'm\xd6p', False, 'mOep'),
    (u'm\xd6p', True, 'moep')
))
def test_slugify_lower(input, lower, output):
    assert slugify(input, lower=lower) == output


@pytest.mark.parametrize(('input', 'output'), (
    (b'foo <strong>bar</strong>', b'foo bar'),
    (u'foo <strong>bar</strong>', u'foo bar'),
))
def test_strip_tags(input, output):
    assert strip_tags(input) == output
    assert type(input) is type(output)


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


@pytest.mark.parametrize(('input', 'output'), (
    ('', ''),
    ('foo', 'foo'),
    ('foo@bar.fb', 'foo@bar.fb'),
    ('<foo@bar.fb>', 'foo@bar.fb'),
    ('foobar <foo@bar.fb> asdf', 'foo@bar.fb'),
    ('foobar <foo@bar.fb> <test@test.com>', 'foo@bar.fb')
))
def test_sanitize_email(input, output):
    assert sanitize_email(input) == output


@pytest.mark.parametrize(('input', 'output'), (
    ('*coconut*', '<p><em>coconut</em></p>'),
    ('**swallow**', '<p><strong>swallow</strong></p>'),
    ('<span>Blabla **strong text**</span>', '<p>&lt;span&gt;Blabla <strong>strong text</strong>&lt;/span&gt;</p>'),
    ('[Python](http://www.google.com/search?q=holy+grail&ln=fr)',
     '<p><a href="http://www.google.com/search?q=holy+grail&amp;ln=fr">Python</a></p>'),
    ("<script>alert('I'm evil!')</script>", "&lt;script&gt;alert('I'm evil!')&lt;/script&gt;"),
    ("Name|Colour\n---|---\nLancelot|Blue",
     '<table>\n<thead>\n<tr>\n<th>Name</th>\n<th>Colour</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n<td>Lancelot</td>\n'
     '<td>Blue</td>\n</tr>\n</tbody>\n</table>'),
    ("**$2 * 2 * 2 > 7$**", "<p><strong>$2 * 2 * 2 > 7$</strong></p>"),
    ("Escaping works just fine! $ *a* $", "<p>Escaping works just fine! $ *a* $</p>"),
    ('![Just a cat](http://myserver.example.com/cat.png)', '<p><img alt="Just a cat" '
     'src="http://myserver.example.com/cat.png"></p>'),
    ("<https://getindico.io>", '<p><a href="https://getindico.io">https://getindico.io</a></p>')
))
def test_markdown(input, output):
    assert render_markdown(input,  extensions=('tables',)) == output
