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

import pytest
from enum import Enum

from indico.core.models.settings import SettingsProxy, Setting


def test_proxy_strict_nodefaults():
    with pytest.raises(ValueError):
        SettingsProxy('test', {})


@pytest.mark.usefixtures('db')
def test_proxy_strict_off():
    proxy = SettingsProxy('test', {}, False)
    assert proxy.get('foo') is None
    proxy.get('foo', 'bar') == 'bar'
    proxy.set('foo', 'foobar')
    assert proxy.get('foo') == 'foobar'


@pytest.mark.usefixtures('db')
def test_proxy_strict():
    proxy = SettingsProxy('test', {'hello': 'world'})
    pytest.raises(ValueError, proxy.get, 'foo')
    pytest.raises(ValueError, proxy.get, 'foo', 'bar')
    pytest.raises(ValueError, proxy.set, 'foo', 'foobar')
    pytest.raises(ValueError, proxy.set_multi, {'hello': 'world', 'foo': 'foobar'})
    pytest.raises(ValueError, proxy.delete, 'hello', 'foo')
    assert proxy.get('hello') == 'world'


@pytest.mark.usefixtures('db', 'request_context')  # use req ctx so the cache is active
def test_proxy_defaults():
    proxy = SettingsProxy('test', {'hello': 'world', 'foo': None})
    assert proxy.get('hello') == 'world'
    assert proxy.get('foo') is None
    assert proxy.get('foo', 'bar') == 'bar'
    assert not proxy.get_all(True)
    proxy.set('foo', 'bar')
    assert proxy.get_all(True) == {'foo': 'bar'}
    assert proxy.get_all() == {'hello': 'world', 'foo': 'bar'}


@pytest.mark.usefixtures('db')
def test_proxy_delete_all():
    defaults = {'hello': 'world', 'foo': None}
    proxy = SettingsProxy('test', defaults)
    assert proxy.get_all() == defaults
    proxy.set('hello', 'test')
    assert proxy.get_all() == {'hello': 'test', 'foo': None}
    proxy.delete_all()
    assert proxy.get_all() == defaults


@pytest.mark.usefixtures('db')
def test_set_enum():
    class Useless(int, Enum):
        thing = 1337

    Setting.set_multi('foo', {'foo': Useless.thing})
    Setting.set('foo', 'bar', Useless.thing)
    for key in {'foo', 'bar'}:
        value = Setting.get('foo', key)
        assert value == Useless.thing
        assert value == Useless.thing.value
        assert not isinstance(value, Useless)  # we store it as a plain value!
