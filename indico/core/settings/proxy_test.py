# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta

import pytest
import pytz

from indico.core.settings import PrefixSettingsProxy, SettingsProxy
from indico.core.settings.converters import DatetimeConverter, EnumConverter, TimedeltaConverter
from indico.modules.events.settings import EventSettingsProxy
from indico.modules.users import User
from indico.util.enum import IndicoIntEnum


def test_proxy_strict_nodefaults():
    with pytest.raises(ValueError):
        SettingsProxy('test', {})


@pytest.mark.usefixtures('db')
def test_proxy_strict_off():
    proxy = SettingsProxy('test', {}, False)
    assert proxy.get('foo') is None
    assert proxy.get('foo', 'bar') == 'bar'
    proxy.set('foo', 'foobar')
    assert proxy.get('foo') == 'foobar'


@pytest.mark.usefixtures('db')
def test_proxy_strict():
    proxy = SettingsProxy('test', {'hello': 'world'})
    with pytest.raises(ValueError):
        proxy.get('foo')
    with pytest.raises(ValueError):
        proxy.get('foo', 'bar')
    with pytest.raises(ValueError):
        proxy.set('foo', 'foobar')
    with pytest.raises(ValueError):
        proxy.set_multi({'hello': 'world', 'foo': 'foobar'})
    with pytest.raises(ValueError):
        proxy.delete('hello', 'foo')
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
        assert proxy.get('bar') == 'test'
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
    with pytest.raises(ValueError):
        proxy.get('acl')
    with pytest.raises(ValueError):
        proxy.set('acl', 'foo')
    with pytest.raises(ValueError):
        proxy.acls.get('reg')
    with pytest.raises(ValueError):
        proxy.acls.set('reg', {user})
    with pytest.raises(ValueError):
        proxy.acls.contains_user('reg', user)
    with pytest.raises(ValueError):
        proxy.acls.add_principal('reg', user)
    with pytest.raises(ValueError):
        proxy.acls.remove_principal('reg', user)


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
    Setting = mocker.patch('indico.core.settings.proxy.Setting')  # noqa: N806
    SettingPrincipal = mocker.patch('indico.core.settings.proxy.SettingPrincipal')  # noqa: N806
    proxy = SettingsProxy('foo', {'reg': None}, acls={'acl'})
    proxy.delete('reg', 'acl')
    Setting.delete.assert_called_once_with('foo', 'reg')
    SettingPrincipal.delete.assert_called_with('foo', 'acl')


def test_set_multi_propagate(mocker):
    Setting = mocker.patch('indico.core.settings.proxy.Setting')  # noqa: N806
    SettingPrincipal = mocker.patch('indico.core.settings.proxy.SettingPrincipal')  # noqa: N806
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
    with pytest.raises(ValueError):
        proxy.get('x')
    with pytest.raises(ValueError):
        proxy.get('x_y')
    with pytest.raises(ValueError):
        proxy.set('x', 'test')
    with pytest.raises(ValueError):
        proxy.set('x_y', 'test')


@pytest.mark.parametrize('with_arg', (True, False))
@pytest.mark.usefixtures('db')
def test_prefix_settings(dummy_event, with_arg):
    kw = {'arg': dummy_event} if with_arg else {'arg': None}
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


def test_bound_settings(dummy_event, dummy_user):
    class TestEnum(IndicoIntEnum):
        foo = 123
        bar = 456

    proxy = EventSettingsProxy(
        'test',
        {'a': 1, 'b': 2, 'e': TestEnum.foo},
        acls={'acl'},
        converters={'e': EnumConverter(TestEnum)}
    )
    proxy.set(dummy_event, 'a', 111)
    proxy.set(dummy_event, 'e', TestEnum.bar)
    proxy.acls.set(dummy_event, 'acl', {dummy_user})
    bound = proxy.bind(dummy_event)
    assert bound.converters == proxy.converters
    assert bound.get('a') == 111
    assert bound.get('b') == 2
    assert bound.acls.contains_user('acl', dummy_user)
    assert bound.acls.get('acl') == {dummy_user}
    assert bound.get('e') == TestEnum.bar
    assert isinstance(bound.get('e'), TestEnum)
