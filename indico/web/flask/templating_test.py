# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from unittest.mock import MagicMock

import pytest
from flask import render_template_string
from jinja2 import UndefinedError

from indico.web.flask.templating import dedent, get_overridable_template_name, markdown, underline


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
