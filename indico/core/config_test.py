# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core import config as config_module
from indico.core.config import load_config


class _FakeEntryPoint:
    def __init__(self, name, plugin_class):
        self.name = name
        self._plugin_class = plugin_class

    def load(self):
        return self._plugin_class


@pytest.fixture
def fake_entry_points(monkeypatch):
    eps = {}

    def _entry_points(*, group):
        if group != 'indico.plugins':
            return []
        return list(eps.values())

    monkeypatch.setattr(config_module, 'entry_points', _entry_points)
    return eps


@pytest.fixture
def write_config(tmp_path, monkeypatch):
    def _write(body):
        path = tmp_path / 'indico.conf'
        # Required keys to keep _postprocess_config / _validate_config happy.
        baseline = "BASE_URL = 'https://example.test'\n"
        path.write_text(baseline + body)
        monkeypatch.setenv('INDICO_CONFIG', str(path))
        return str(path)
    return _write


def _make_plugin(defaults):
    class Plugin:
        plugin_config_defaults = defaults
    return Plugin


def test_plugin_config_default_loaded(fake_entry_points, write_config):
    fake_entry_points['demo'] = _FakeEntryPoint('demo', _make_plugin({'API_KEY': None, 'TIMEOUT': 30}))
    write_config("PLUGINS = {'demo'}\n")
    data = load_config()
    assert data['DEMO_API_KEY'] is None
    assert data['DEMO_TIMEOUT'] == 30


def test_plugin_config_user_value_overrides_default(fake_entry_points, write_config):
    fake_entry_points['demo'] = _FakeEntryPoint('demo', _make_plugin({'API_KEY': None, 'TIMEOUT': 30}))
    write_config("PLUGINS = {'demo'}\nDEMO_API_KEY = 'secret'\nDEMO_TIMEOUT = 5\n")
    data = load_config()
    assert data['DEMO_API_KEY'] == 'secret'
    assert data['DEMO_TIMEOUT'] == 5


def test_plugin_config_unknown_key_warns(fake_entry_points, write_config):
    fake_entry_points['demo'] = _FakeEntryPoint('demo', _make_plugin({'API_KEY': None}))
    write_config("PLUGINS = {'demo'}\nDEMO_BOGUS = 'x'\n")
    with pytest.warns(UserWarning, match='DEMO_BOGUS'):
        data = load_config()
    assert 'DEMO_BOGUS' not in data


def test_only_defaults_with_plugin_override_carries_keys(fake_entry_points):
    fake_entry_points['demo'] = _FakeEntryPoint('demo', _make_plugin({'API_KEY': None}))
    data = load_config(only_defaults=True, override={
        'BASE_URL': 'https://example.test',
        'PLUGINS': {'demo'},
        'DEMO_API_KEY': 'x',
    })
    assert data['DEMO_API_KEY'] == 'x'


def test_plugin_config_collision_with_core_key_warns_and_is_ignored(fake_entry_points, write_config):
    # Plugin 'external' declaring 'REGISTRATION_URL' would shadow the core EXTERNAL_REGISTRATION_URL
    # default. The user's indico.conf does not set this key, so the plugin default would otherwise win.
    fake_entry_points['external'] = _FakeEntryPoint(
        'external', _make_plugin({'REGISTRATION_URL': 'plugin-default'}))
    write_config("PLUGINS = {'external'}\n")
    with pytest.warns(UserWarning, match='EXTERNAL_REGISTRATION_URL'):
        data = load_config()
    # Core default wins; the plugin's value is dropped.
    assert data['EXTERNAL_REGISTRATION_URL'] is None


def test_plugin_config_collision_between_plugins_warns_and_latter_wins(fake_entry_points, write_config):
    # Plugin 'a' declaring 'B_C' and plugin 'a_b' declaring 'C' both resolve to A_B_C.
    fake_entry_points['a'] = _FakeEntryPoint('a', _make_plugin({'B_C': 'first'}))
    fake_entry_points['a_b'] = _FakeEntryPoint('a_b', _make_plugin({'C': 'second'}))
    write_config("PLUGINS = {'a', 'a_b'}\n")
    with pytest.warns(UserWarning, match='A_B_C'):
        data = load_config()
    assert data['A_B_C'] == 'second'


def test_indico_conf_override_env_passes_plugin_key(fake_entry_points, write_config, monkeypatch):
    fake_entry_points['demo'] = _FakeEntryPoint('demo', _make_plugin({'API_KEY': None}))
    write_config("PLUGINS = {'demo'}\n")
    monkeypatch.setenv('INDICO_CONF_OVERRIDE', "{'DEMO_API_KEY': 'fromenv'}")
    data = load_config()
    assert data['DEMO_API_KEY'] == 'fromenv'


def test_missing_entry_point_graceful(fake_entry_points, write_config):
    # 'ghost' has no registered entry-point; should not crash, key absent from result.
    write_config("PLUGINS = {'ghost'}\n")
    data = load_config()
    assert 'GHOST_ANYTHING' not in data


def test_plugin_config_proxy_reads_prefixed():
    from indico.core.plugins import PluginConfigProxy

    class FakeConfig:
        UN_MFA_ENABLED = True
        UN_TIMEOUT = 5

    proxy = PluginConfigProxy(FakeConfig(), prefix='UN')
    assert proxy.MFA_ENABLED is True
    assert proxy.TIMEOUT == 5


def test_plugin_config_proxy_missing_attr_raises():
    from indico.core.plugins import PluginConfigProxy

    class FakeConfig:
        pass

    proxy = PluginConfigProxy(FakeConfig(), prefix='UN')
    with pytest.raises(AttributeError):
        proxy.NOPE  # noqa: B018
