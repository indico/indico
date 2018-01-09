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

import pytest

from indico.util.locators import get_locator, locator_property


def test_get_locator_none():
    with pytest.raises(TypeError):
        get_locator(object())
    with pytest.raises(TypeError):
        get_locator(None)


def test_get_locator():
    class _Prop(object):
        @property
        def locator(self):
            return {'foo': 'bar'}

    class _Locator(object):
        @locator_property
        def locator(self):
            return {'foo': 'bar'}

    assert get_locator(_Prop()) == {'foo': 'bar'}
    assert get_locator(_Locator()) == {'foo': 'bar'}
    assert get_locator({'foo': 'bar'}) == {'foo': 'bar'}


def test_locator_property():
    class _Test(object):
        @locator_property
        def locator(self):
            return {'foo': 'bar'}

        @locator.fancy
        def locator(self):
            return dict(self.locator, awesome='magic')

    assert isinstance(_Test.locator, locator_property)
    t = _Test()
    assert get_locator(t) == {'foo': 'bar'}
    assert get_locator(t.locator) == {'foo': 'bar'}
    assert get_locator(t.locator.fancy) == {'foo': 'bar', 'awesome': 'magic'}
    with pytest.raises(AttributeError):
        t.locator.invalid


def test_locator_property_lazy():
    class _Test(object):
        @locator_property
        def locator(self):
            accessed.append('locator')
            return {'foo': 'bar'}

        @locator.fancy
        def locator(self):
            accessed.append('fancy')
            return {'awesome': 'magic'}

    accessed = []
    # creating the object or accessing the locator itself doesn't
    # call the underlying function
    t = _Test()
    t.locator
    assert not accessed

    # accessing the locator in any way that needs to access its data
    # obviously triggers a call to the accessor
    assert t.locator == {'foo': 'bar'}
    assert accessed == ['locator']

    # accessing a special locator only triggers that locator's accessor
    # but not the one of the default locator
    accessed = []
    t.locator.fancy
    assert accessed == ['fancy']


def test_locator_property_nested():
    with pytest.raises(AttributeError):
        class _Test(object):
            @locator_property
            def locator(self):
                pass

            @locator.x
            def locator(self):
                pass

            @locator.x.y
            def locator(self):
                pass
