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

import pytest
from flask import render_template_string
from mock import MagicMock

from indico.web.flask.templating import underline, markdown, get_overridable_template_name, dedent


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


def _render(template, raises=None):
    val = u'm\xf6p'
    utfval = val.encode('utf-8')
    func = lambda x: x.encode('utf-8').decode('utf-8')
    if raises:
        with pytest.raises(raises):
            render_template_string(template, val=utfval, func=func)
    else:
        assert (render_template_string(template, val=val, func=func)
                == render_template_string(template, val=utfval, func=func))


def test_ensure_unicode_simple_vars():
    """Test simple variables"""
    _render('{{ val }}')


def test_ensure_unicode_func_args():
    """Test function arguments (no automated unicode conversion!)"""
    _render('{{ func(val | ensure_unicode) }}')
    _render('{{ func(val) }}', UnicodeDecodeError)


def test_ensure_unicode_filter_vars():
    """Test variables with filters"""
    _render('{{ val | ensure_unicode }}')  # Redundant but needs to work nonetheless
    _render('{{ val | safe }}')


def test_ensure_unicode_inline_if():
    """Test variables with inline if"""
    _render('x {{ val if true else val }} x {{ val if false else val }} x')
    _render('x {{ val|safe if true else val|safe }} x {{ val|safe if false else val|safe }} x')


def test_ensure_unicode_trans():
    """Test trans tag which need explicit unicode conversion"""
    _render('{% trans x=val | ensure_unicode %}{{ x }}}{% endtrans %}')
    _render('{% trans x=val %}{{ x }}}{% endtrans %}', UnicodeDecodeError)
