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

from collections import OrderedDict

import pytest

from indico.core import signals
from indico.util.rules import Condition, get_missing_conditions, check_rule, get_conditions


class TestCondition(Condition):
    @classmethod
    def is_none(cls, **kwargs):
        return False


class ActionCondition(TestCondition):
    name = 'action'
    description = "The action performed"
    required = True

    @classmethod
    def get_available_values(cls, **kwargs):
        return OrderedDict([('add', 'added'), ('del', 'deleted')])

    @classmethod
    def check(cls, values, action, **kwargs):
        return action in values


class FooCondition(TestCondition):
    name = 'foo'
    description = "The foo value"
    required = False

    @classmethod
    def get_available_values(cls, **kwargs):
        return OrderedDict([(1, '1'), (2, '2'), (3, '3')])

    @classmethod
    def check(cls, values, foo, **kwargs):
        return foo in values

    @classmethod
    def is_none(cls, foo, **kwargs):
        return foo == 42


class BarCondition(TestCondition):
    name = 'bar'
    description = "The bar value"
    required = False

    @classmethod
    def get_available_values(cls, **kwargs):
        return {'a': 'a', 'b': 'b', 'c': 'c'}

    @classmethod
    def check(cls, values, bar, **kwargs):
        return bar in values


def _get_test_conditions(sender, **kwargs):
    yield ActionCondition
    yield FooCondition
    yield BarCondition


@pytest.yield_fixture(autouse=True)
def _register_test_rules():
    with signals.get_conditions.connected_to(_get_test_conditions, sender='test'):
        yield


def test_get_rule():
    assert get_conditions('test') == {'action': ActionCondition, 'foo': FooCondition, 'bar': BarCondition}


def test_get_missing_rules():
    assert get_missing_conditions('test', {'action': ['test']}) == set()
    assert get_missing_conditions('test', {'action': None}) == {'action'}
    assert get_missing_conditions('test', {}) == {'action'}


@pytest.mark.parametrize(('rule', 'kwargs', 'expected'), (
    # required rule missing
    ({}, {'action': 'add', 'foo': 1, 'bar': 'a'}, False),
    # match "any" value
    ({'action': ['add']}, {'action': 'add', 'foo': 1}, True),
    # match "none" value
    ({'action': ['add'], 'foo': []}, {'action': 'add', 'foo': 42}, True),
    ({'action': ['add'], 'foo': []}, {'action': 'add', 'foo': 1}, False),
    # no match
    ({'action': ['del']}, {'action': 'add', 'foo': 1, 'bar': 'a'}, False),
    # invalid value
    ({'action': ['add'], 'foo': [4]}, {'action': 'add', 'foo': 4, 'bar': 'a'}, False),
    # invalid + valid value
    ({'action': ['add'], 'foo': [2]}, {'action': 'add', 'foo': 3, 'bar': 'a'}, False),
    # valid value
    ({'action': ['add'], 'foo': [3]}, {'action': 'add', 'foo': 3, 'bar': 'a'}, True),
    # valid values
    ({'action': ['add'], 'foo': [2, 3]}, {'action': 'add', 'foo': 3, 'bar': 'a'}, True),
))
def test_check_rules(rule, kwargs, expected):
    assert check_rule('test', rule, **kwargs) == expected
