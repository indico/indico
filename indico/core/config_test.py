# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.core import config as config_module
from indico.core.config import IndicoConfig, load_config


class _FakePlugin:
    def __init__(self, name, defaults):
        self.name = name
        self.plugin_config_defaults = defaults


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


def _pending(data):
    return data['PLUGIN_CONFIG']['pending']


def _resolved(data):
    return data['PLUGIN_CONFIG']['resolved']


def test_plugin_keys_are_deferred_not_top_level(write_config, recwarn):
    write_config("PLUGINS = {'demo'}\nPLUGIN_DEMO_API_KEY = 'secret'\n")
    data = load_config()
    # Plugin keys are held aside without importing the plugin and without a warning.
    assert 'PLUGIN_DEMO_API_KEY' not in data
    assert _pending(data) == {'PLUGIN_DEMO_API_KEY': 'secret'}
    assert _resolved(data) == {}
    assert not any('PLUGIN_DEMO_API_KEY' in str(w.message) for w in recwarn.list)


def test_register_plugin_config_resolves_value_and_default(write_config):
    write_config("PLUGINS = {'demo'}\nPLUGIN_DEMO_API_KEY = 'secret'\n")
    cfg = IndicoConfig(load_config())
    cfg.register_plugin_config(_FakePlugin('demo', {'API_KEY': None, 'TIMEOUT': 30}))
    assert _resolved(cfg.data) == {'PLUGIN_DEMO_API_KEY': 'secret', 'PLUGIN_DEMO_TIMEOUT': 30}
    # Claimed keys are consumed from the pending set.
    assert _pending(cfg.data) == {}


def test_register_plugin_config_applies_default_when_absent(write_config):
    write_config("PLUGINS = {'demo'}\n")
    cfg = IndicoConfig(load_config())
    cfg.register_plugin_config(_FakePlugin('demo', {'TIMEOUT': 30}))
    assert _resolved(cfg.data)['PLUGIN_DEMO_TIMEOUT'] == 30


def test_plugin_key_precedence_override_wins(write_config):
    write_config("PLUGINS = {'demo'}\nPLUGIN_DEMO_API_KEY = 'fromfile'\n")
    data = load_config(override={'PLUGIN_DEMO_API_KEY': 'fromoverride'})
    assert _pending(data)['PLUGIN_DEMO_API_KEY'] == 'fromoverride'


def test_env_override_carries_plugin_key(write_config, monkeypatch):
    write_config("PLUGINS = {'demo'}\n")
    monkeypatch.setenv('INDICO_CONF_OVERRIDE', "{'PLUGIN_DEMO_API_KEY': 'fromenv'}")
    data = load_config()
    assert _pending(data)['PLUGIN_DEMO_API_KEY'] == 'fromenv'


def test_only_defaults_override_carries_plugin_key():
    data = load_config(only_defaults=True, override={
        'BASE_URL': 'https://example.test',
        'PLUGINS': {'demo'},
        'PLUGIN_DEMO_API_KEY': 'x',
    })
    assert _pending(data) == {'PLUGIN_DEMO_API_KEY': 'x'}
    assert _resolved(data) == {}


def test_unknown_non_plugin_key_warns_at_load(write_config):
    write_config('TOTALLY_BOGUS = 1\n')
    with pytest.warns(UserWarning, match='TOTALLY_BOGUS'):
        data = load_config()
    assert 'TOTALLY_BOGUS' not in data


def test_unclaimed_plugin_key_warns(write_config):
    write_config("PLUGINS = {'demo'}\nPLUGIN_DEMO_BOGUS = 'x'\n")
    data = load_config()
    with pytest.warns(UserWarning, match='PLUGIN_DEMO_BOGUS'):
        config_module._warn_unclaimed_plugin_config(data)


def test_claimed_plugin_key_not_warned(write_config, recwarn):
    write_config("PLUGINS = {'demo'}\nPLUGIN_DEMO_API_KEY = 'secret'\n")
    cfg = IndicoConfig(load_config())
    cfg.register_plugin_config(_FakePlugin('demo', {'API_KEY': None}))
    config_module._warn_unclaimed_plugin_config(cfg.data)
    assert not any('PLUGIN_DEMO_API_KEY' in str(w.message) for w in recwarn.list)


def test_register_core_collision_warns_and_is_ignored(write_config, monkeypatch):
    # Inject a fake PLUGIN_* core default to exercise the safety branch (no real core key uses the
    # PLUGIN_ prefix, but the check stays as defense-in-depth against future drift).
    monkeypatch.setitem(config_module.DEFAULTS, 'PLUGIN_DEMO_API_KEY', 'core-default')
    write_config("PLUGINS = {'demo'}\n")
    cfg = IndicoConfig(load_config())
    with pytest.warns(UserWarning, match='PLUGIN_DEMO_API_KEY'):
        cfg.register_plugin_config(_FakePlugin('demo', {'API_KEY': 'plugin-default'}))
    assert 'PLUGIN_DEMO_API_KEY' not in _resolved(cfg.data)


def test_register_cross_plugin_collision_raises(write_config):
    # Plugin 'a' declaring 'B_C' and plugin 'a_b' declaring 'C' both resolve to PLUGIN_A_B_C.
    write_config("PLUGINS = {'a', 'a_b'}\n")
    cfg = IndicoConfig(load_config())
    cfg.register_plugin_config(_FakePlugin('a', {'B_C': 'first'}))
    with pytest.raises(RuntimeError, match='PLUGIN_A_B_C'):
        cfg.register_plugin_config(_FakePlugin('a_b', {'C': 'second'}))


def test_plugin_config_proxy_reads_resolved(write_config):
    from indico.core.plugins import PluginConfigProxy
    write_config("PLUGINS = {'demo'}\nPLUGIN_DEMO_API_KEY = 'secret'\n")
    cfg = IndicoConfig(load_config())
    cfg.register_plugin_config(_FakePlugin('demo', {'API_KEY': None}))
    proxy = PluginConfigProxy(cfg, 'PLUGIN_DEMO')
    assert proxy.API_KEY == 'secret'


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
