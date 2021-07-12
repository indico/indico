# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from flask import render_template_string
from flask_pluginengine import current_plugin
from jinja2 import UndefinedError
from markupsafe import Markup

from indico.core import signals
from indico.core.plugins import IndicoPlugin
from indico.web.flask.templating import (TemplateSnippet, call_template_hook, dedent, get_overridable_template_name,
                                         markdown, register_template_hook, underline)


def test_underline():
    assert underline('foo') == 'foo\n---'
    assert underline('foobar', '=') == 'foobar\n======'


@pytest.mark.parametrize(('md', 'html'), (
    # basic markdown
    ('**hi**', '<p><strong>hi</strong></p>'),
    # nl2br extension
    ('hello\nworld', '<p>hello<br>\nworld</p>'),
    # unicode
    ('m\xf6p', '<p>m\xf6p</p>'),
))
def test_markdown(md, html):
    assert markdown(md) == html


def test_dedent():
    s = '''
        foo foo

            bar
            foobar
    test
    '''
    assert dedent(s) == '\nfoo foo\n\nbar\nfoobar\ntest\n'


@pytest.mark.parametrize(('core_prefix', 'plugin_prefix'), (
    ('',      ''),
    ('core/', ''),
    ('',      'plugin/'),
    ('core/', 'plugin/'),
))
def test_get_overridable_template_name(core_prefix, plugin_prefix):
    plugin = MagicMock(name='dummy')
    name = 'test.html'
    tpl = get_overridable_template_name(name, None, core_prefix=core_prefix, plugin_prefix=plugin_prefix)
    assert tpl == core_prefix + name
    tpl = get_overridable_template_name(name, plugin, core_prefix=core_prefix, plugin_prefix=plugin_prefix)
    assert tpl == [f'{plugin.name}:{plugin_prefix}{name}', core_prefix + name]


@pytest.mark.parametrize('template', (
    '{{ foo }}',
    '{{ d.foo.bar }}',
    '{{ d.foo["bar"] }}',
    '{{ d.foo() }}',
    '{{ d["foo"]["bar"] }}',
    '{{ d["foo"].bar }}',
    '{{ d["foo"]() }}',
    '{{ d.foo + "x" }}',
    '{{ d["foo"] + "x" }}',
))
def test_undefined_raising(template):
    with pytest.raises(UndefinedError):
        render_template_string(template, d={})


@pytest.mark.parametrize('template', (
    '{{ foo|default("ok") }}',
    '{{ "ok" if not d.foo }}',
    '{{ "ok" if not d.bar.b }}',
    '{{ "ok" if not d["foo"] }}',
    '{{ "fail" if d.foo == "bar" else "ok" }}',
    '{{ "fail" if d["foo"] == "bar" else "ok" }}',
    '{{ "ok" if d.foo != "bar" else "fail" }}',
    '{{ "ok" if d["foo"] != "bar" else "fail" }}',
))
def test_undefined_silent(template):
    assert render_template_string(template, d={'bar': {}}) == 'ok'


@contextmanager
def _register_template_hook_cleanup(name, *args, **kwargs):
    old_recvs = set(signals.plugin.template_hook.receivers_for(name))
    register_template_hook(name, *args, **kwargs)
    try:
        yield
    finally:
        for recv in signals.plugin.template_hook.receivers_for(name):
            if recv not in old_recvs:
                signals.plugin.template_hook.disconnect(recv)


class _DummyPlugin(IndicoPlugin):
    name = 'dummy'

    def __init__(self):
        pass


def test_template_hooks_markup():
    def _make_tpl_hook(name=''):
        return lambda: (f'&test{name}@{current_plugin.name}' if current_plugin else f'&test{name}')

    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2), markup=False),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(3), plugin=_DummyPlugin()),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(4), plugin=_DummyPlugin(), markup=False),
    ):
        rv = call_template_hook('test-hook')
        assert isinstance(rv, Markup)
        assert rv == ('&test1\n&amp;test2\n&test3@dummy\n&amp;test4@dummy')


def test_template_hooks():
    def _make_tpl_hook(name=''):
        return lambda: f'test{name}@{current_plugin.name}' if current_plugin else f'test{name}'

    # single receiver
    with _register_template_hook_cleanup('test-hook', _make_tpl_hook()):
        assert call_template_hook('test-hook') == 'test'

    # single receiver - plugin
    with _register_template_hook_cleanup('test-hook', _make_tpl_hook(), plugin=_DummyPlugin()):
        assert call_template_hook('test-hook') == 'test@dummy'

    # multiple receivers
    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2)),
    ):
        assert call_template_hook('test-hook') == 'test1\ntest2'
        assert call_template_hook('test-hook', as_list=True) == ['test1', 'test2']

    # multiple receivers - plugin
    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1), plugin=_DummyPlugin()),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2), plugin=_DummyPlugin()),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(3)),
    ):
        assert call_template_hook('test-hook') == 'test1@dummy\ntest2@dummy\ntest3'
        assert call_template_hook('test-hook', as_list=True) == ['test1@dummy', 'test2@dummy', 'test3']

    # custom priority
    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1), plugin=_DummyPlugin(), priority=60),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(3), priority=30),
    ):
        assert call_template_hook('test-hook') == 'test3\ntest2\ntest1@dummy'


def test_template_hooks_yielding():
    def _make_tpl_hook(name='', yielding=False):
        if yielding:
            def _hook():
                yield f'test{name}@{current_plugin.name}' if current_plugin else f'test{name}'
                yield f'test{name}@{current_plugin.name}' if current_plugin else f'test{name}'
            return _hook
        else:
            return lambda: f'test{name}@{current_plugin.name}' if current_plugin else f'test{name}'

    # single receiver
    with _register_template_hook_cleanup('test-hook', _make_tpl_hook(yielding=True)):
        assert call_template_hook('test-hook') == 'test\ntest'

    # single receiver - plugin
    with _register_template_hook_cleanup('test-hook', _make_tpl_hook(yielding=True), plugin=_DummyPlugin()):
        assert call_template_hook('test-hook') == 'test@dummy\ntest@dummy'

    # multiple receivers
    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2, yielding=True)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(3, yielding=True)),
    ):
        assert call_template_hook('test-hook') == 'test1\ntest2\ntest2\ntest3\ntest3'
        assert call_template_hook('test-hook', as_list=True) == ['test1', 'test2', 'test2', 'test3', 'test3']

    # multiple receivers - plugin
    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1), plugin=_DummyPlugin()),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2, yielding=True), plugin=_DummyPlugin()),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(3)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(4, yielding=True)),
    ):
        assert call_template_hook('test-hook') == 'test1@dummy\ntest2@dummy\ntest2@dummy\ntest3\ntest4\ntest4'
        assert call_template_hook('test-hook', as_list=True) == [
            'test1@dummy', 'test2@dummy', 'test2@dummy', 'test3', 'test4', 'test4'
        ]


def test_template_hooks_snippets():
    def _make_tpl_hook(name='', yielding=False, snippet=None):
        if yielding:
            def _hook():
                text = f'&test{name}@{current_plugin.name}' if current_plugin else f'&test{name}'
                if snippet:
                    yield TemplateSnippet(text, **snippet)
                    yield TemplateSnippet(text, **snippet)
                else:
                    yield text
                    yield text
            return _hook
        elif snippet:
            return lambda: TemplateSnippet(f'&test{name}@{current_plugin.name}' if current_plugin else f'&test{name}',
                                           **snippet)
        else:
            return lambda: f'&test{name}@{current_plugin.name}' if current_plugin else f'&test{name}'

    with (
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(1)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(2, snippet={'markup': False, 'priority': 60})),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(3, snippet={'markup': False, 'priority': 30},
                                                                    yielding=True)),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(4, snippet={'priority': 70}),
                                        plugin=_DummyPlugin()),
        _register_template_hook_cleanup('test-hook', _make_tpl_hook(5, snippet={'priority': 10}, yielding=True),
                                        plugin=_DummyPlugin()),
    ):
        assert call_template_hook('test-hook') == '\n'.join([
            '&test5@dummy', '&test5@dummy',
            '&amp;test3', '&amp;test3',
            '&test1',
            '&amp;test2',
            '&test4@dummy',
        ])
        assert call_template_hook('test-hook', as_list=True) == [
            Markup('&test5@dummy'), Markup('&test5@dummy'),
            '&test3', '&test3',
            Markup('&test1'),
            '&test2',
            Markup('&test4@dummy'),
        ]
