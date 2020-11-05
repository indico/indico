# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest
from mock import MagicMock

from indico.web.flask.templating import dedent, get_overridable_template_name, markdown, underline


def test_underline():
    assert underline('foo') == 'foo\n---'
    assert underline('foobar', '=') == 'foobar\n======'


def test_markdown():
    # basic markdown
    assert markdown('**hi**') == u'<p><strong>hi</strong></p>'
    # nl2br extension
    assert markdown('hello\nworld') == u'<p>hello<br>\nworld</p>'
    # unicode
    val = u'm\xf6p'
    utfval = val.encode('utf-8')
    assert markdown(utfval) == u'<p>{}</p>'.format(val)
    assert markdown(val) == u'<p>{}</p>'.format(val)


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
    assert tpl == ['{}:{}{}'.format(plugin.name, plugin_prefix, name), core_prefix + name]
