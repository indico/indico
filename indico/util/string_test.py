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

from indico.util.string import seems_html, to_unicode, make_unique_token, slugify


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
