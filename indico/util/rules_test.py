# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core import signals
from indico.util.rules import Rule, get_missing_rules, check_rules, get_rules


class ActionRule(Rule):
    name = 'action'
    description = "The action performed"
    required = True

    @classmethod
    def get_available_values(cls, **kwargs):
        return {'add': 'added', 'del': 'deleted'}

    @classmethod
    def check(cls, values, action, foo, bar):
        return action in values


class FooRule(Rule):
    name = 'foo'
    description = "The foo value"
    required = False

    @classmethod
    def get_available_values(cls, **kwargs):
        return {1: '1', 2: '2', 3: '3'}

    @classmethod
    def check(cls, values, action, foo, bar):
        return foo in values


class BarRule(Rule):
    name = 'bar'
    description = "The bar value"
    required = False

    @classmethod
    def get_available_values(cls, **kwargs):
        return {'a': 'a', 'b': 'b', 'c': 'c'}

    @classmethod
    def check(cls, values, action, foo, bar):
        return bar in values


def _get_test_rules(sender, **kwargs):
    yield ActionRule
    yield FooRule
    yield BarRule


@pytest.yield_fixture(autouse=True)
def _register_test_rules():
    with signals.get_rules.connected_to(_get_test_rules, sender='test'):
        yield


def test_get_rules():
    assert get_rules('test') == {'action': ActionRule, 'foo': FooRule, 'bar': BarRule}


def test_get_missing_rules():
    assert get_missing_rules('test', {'action': ['test']}) == set()
    assert get_missing_rules('test', {'action': None}) == {'action'}
    assert get_missing_rules('test', {}) == {'action'}


@pytest.mark.parametrize(('ruleset', 'kwargs', 'expected'), (
    # required rule missing
    ({}, {'action': 'add', 'foo': 1, 'bar': 'a'}, False),
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
def test_check_rules(ruleset, kwargs, expected):
    assert check_rules('test', ruleset, **kwargs) == expected
