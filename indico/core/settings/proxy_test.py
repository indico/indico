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

from datetime import datetime, timedelta

import pytest
import pytz

from indico.core.settings import SettingsProxy
from indico.core.settings.converters import DatetimeConverter, TimedeltaConverter
from indico.core.settings.proxy import PrefixSettingsProxy
from indico.modules.events.settings import EventSettingsProxy
from indico.modules.users import User


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
def test_proxy_converters_all():
    epoch_dt = datetime(1970, 1, 1, tzinfo=pytz.utc)
    xmas_dt = datetime(2016, 12, 24, 20, tzinfo=pytz.utc)
    newyear_dt = datetime(2017, 1, 2, tzinfo=pytz.utc)
    duration = timedelta(days=2)
    defaults = {'epoch': epoch_dt, 'xmas': None, 'newyear': None, 'duration': None}
    converters = {name: DatetimeConverter if name != 'duration' else TimedeltaConverter for name in defaults}
    proxy = SettingsProxy('test', defaults, converters=converters)
    proxy.set('xmas', xmas_dt)
    proxy.set_multi({'newyear': newyear_dt, 'duration': duration})
    assert proxy.get_all() == {'epoch': epoch_dt, 'xmas': xmas_dt, 'newyear': newyear_dt, 'duration': duration}


@pytest.mark.usefixtures('db', 'request_context')  # use req ctx so the cache is active
def test_proxy_preload(count_queries):
    defaults = {'hello': 'world', 'foo': None, 'bar': None}
    proxy = SettingsProxy('test', defaults)
    proxy.set('bar', 'test')
    with count_queries() as cnt:
        # this one preloads
        assert proxy.get('hello') == 'world'
    assert cnt() == 1
    with count_queries() as cnt:
        # this one has no value in the db
        assert proxy.get('foo') is None
        assert proxy.get('foo', 'bar') == 'bar'
    assert cnt() == 0
    with count_queries() as cnt:
        assert proxy.get('bar') is 'test'
    assert cnt() == 0


@pytest.mark.usefixtures('db', 'request_context')  # use req ctx so the cache is active
def test_proxy_cache_mutable():
    proxy = SettingsProxy('test', {'foo': []})
    foo = proxy.get('foo')
    assert foo is not proxy.defaults['foo']
    foo.append('test')
    assert not proxy.get('foo')


@pytest.mark.usefixtures('db')
def test_acls_invalid():
    user = User()
    proxy = SettingsProxy('foo', {'reg': None}, acls={'acl'})
    pytest.raises(ValueError, proxy.get, 'acl')
    pytest.raises(ValueError, proxy.set, 'acl', 'foo')
    pytest.raises(ValueError, proxy.acls.get, 'reg')
    pytest.raises(ValueError, proxy.acls.set, 'reg', {user})
    pytest.raises(ValueError, proxy.acls.contains_user, 'reg', user)
    pytest.raises(ValueError, proxy.acls.add_principal, 'reg', user)
    pytest.raises(ValueError, proxy.acls.remove_principal, 'reg', user)


@pytest.mark.usefixtures('db')
def test_get_all_acls():
    proxy = SettingsProxy('foo', {'reg': None}, acls={'acl'})
    assert proxy.get_all() == {'reg': None, 'acl': set()}


@pytest.mark.usefixtures('db')
def test_acls(dummy_user, create_user):
    other_user = create_user(123)
    proxy = SettingsProxy('foo', acls={'acl'})
    assert proxy.acls.get('acl') == set()
    proxy.acls.set('acl', {dummy_user})
    assert proxy.acls.get('acl') == {dummy_user}
    assert proxy.acls.contains_user('acl', dummy_user)
    assert not proxy.acls.contains_user('acl', other_user)
    proxy.acls.add_principal('acl', other_user)
    assert proxy.acls.contains_user('acl', other_user)
    assert proxy.acls.get('acl') == {dummy_user, other_user}
    proxy.acls.remove_principal('acl', dummy_user)
    assert proxy.acls.get('acl') == {other_user}


def test_delete_propagate(mocker):
    Setting = mocker.patch('indico.core.settings.core.Setting')
    SettingPrincipal = mocker.patch('indico.core.settings.core.SettingPrincipal')
    proxy = SettingsProxy('foo', {'reg': None}, acls={'acl'})
    proxy.delete('reg', 'acl')
    Setting.delete.assert_called_once_with('foo', 'reg')
    SettingPrincipal.delete.assert_called_with('foo', 'acl')


def test_set_multi_propagate(mocker):
    Setting = mocker.patch('indico.core.settings.core.Setting')
    SettingPrincipal = mocker.patch('indico.core.settings.core.SettingPrincipal')
    proxy = SettingsProxy('foo', {'reg': None}, acls={'acl'})
    proxy.set_multi({
        'reg': 'bar',
        'acl': {'u'}
    })
    Setting.set_multi.assert_called_once_with('foo', {'reg': 'bar'})
    SettingPrincipal.set_acl_multi.assert_called_with('foo', {'acl': {'u'}})


def test_prefix_settings_invalid():
    foo_proxy = SettingsProxy('foo', {'a': 1, 'b': 2})
    bar_proxy = SettingsProxy('bar', {'x': 3, 'y': 4})
    proxy = PrefixSettingsProxy({'foo': foo_proxy, 'bar': bar_proxy})
    pytest.raises(ValueError, proxy.get, 'x')
    pytest.raises(ValueError, proxy.get, 'x_y')
    pytest.raises(ValueError, proxy.set, 'x', 'test')
    pytest.raises(ValueError, proxy.set, 'x_y', 'test')


@pytest.mark.parametrize('with_arg', (True, False))
@pytest.mark.usefixtures('db')
def test_prefix_settings(dummy_event_new, with_arg):
    kw = {'arg': dummy_event_new} if with_arg else {'arg': None}
    cls = EventSettingsProxy if with_arg else SettingsProxy
    foo_proxy = cls('foo', {'a': 1, 'b': 2})
    bar_proxy = cls('bar', {'x': None, 'y': 4})
    proxy = PrefixSettingsProxy({'foo': foo_proxy, 'bar': bar_proxy}, has_arg=with_arg)
    proxy.set('bar_x', 3, **kw)
    assert proxy.get_all(**kw) == {'foo_a': 1, 'foo_b': 2, 'bar_x': 3, 'bar_y': 4}
    assert proxy.get_all(no_defaults=True, **kw) == {'bar_x': 3}
    assert proxy.get('foo_a', **kw) == 1
    assert proxy.get('bar_y', 'test', **kw) == 'test'
    proxy.set_multi({'foo_a': 11, 'bar_x': 33}, **kw)
    assert proxy.get('foo_a', **kw) == 11
    assert proxy.get('bar_x', **kw) == 33
    proxy.delete('foo_a', 'bar_x', **kw)
    assert proxy.get('foo_a', **kw) == 1
    assert proxy.get('bar_x', **kw) is None
    proxy.set_multi({'foo_a': 11, 'bar_x': 33}, **kw)
    proxy.delete_all(**kw)
    assert proxy.get_all(no_defaults=True, **kw) == {}
