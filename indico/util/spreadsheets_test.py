# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import textwrap

import pytest

from indico.util.spreadsheets import generate_csv


def test_generate_csv():
    headers = ['foo', 'bar']
    rows = [
        {'foo': 'hello', 'bar': ''},
        {'foo': 'hello', 'bar': ['3', '1', '2']},
        {'foo': 'hello', 'bar': ('3', '1', '2')},
        {'foo': 'hello', 'bar': {'3', '1', '2'}},
        {'foo': 'hello', 'bar': True},
        {'foo': 'hello', 'bar': False},
        {'foo': 'hello', 'bar': None},
        {'foo': 'hello', 'bar': 'hello\nworld'},
    ]
    csv = generate_csv(headers, rows).read().decode('utf-8-sig').strip().splitlines()
    assert csv == textwrap.dedent('''
        foo,bar
        hello,
        hello,3; 1; 2
        hello,3; 1; 2
        hello,1; 2; 3
        hello,Yes
        hello,No
        hello,
        hello,hello    world
    ''').strip().splitlines()


@pytest.mark.parametrize(('value', 'expected'), (
    ('=foo', 'foo'),
    ('+foo', 'foo'),
    ('-foo', 'foo'),
    ('@foo', 'foo'),
    ('=+-@foo', 'foo'),
    ('++foo', 'foo'),
))
def test_generate_csv_malicious(value, expected):
    headers = ['foo', 'bar']
    rows = [{'foo': value, 'bar': ''}]
    csv = generate_csv(headers, rows).read().decode('utf-8-sig').strip().splitlines()
    assert csv == ['foo,bar', '{},'.format(expected)]
