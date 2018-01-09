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

import os

import pytest
from babel.messages import Catalog
from babel.messages.mofile import write_mo
from babel.support import Translations
from flask import has_request_context, request, session
from flask_babelex import get_domain
from speaklater import _LazyString
from werkzeug.http import LanguageAccept

from indico.core.plugins import IndicoPlugin, plugin_engine
from indico.util.i18n import _, babel, gettext_context, make_bound_gettext, ngettext, session_language, ungettext


DICTIONARIES = {
    'fr_FR': {
        'This is not a string': u"Ceci n'est pas une cha\u00cene"
    },

    'fr_MP': {
        'Fetch the cow': u'Fetchez la vache',
        'The wheels': u'Les wheels',
        ('{} cow', 0): u'{} vache',
        ('{} cow', 1): u'{} vaches',
    },

    'en_PI': {
        'I need a drink.': u"I be needin' a bottle of rhum!"
    }
}


class MockTranslations(Translations):
    """
    Mock `Translations` class - returns a mock dictionary
    based on the selected locale
    """

    def __init__(self):
        super(MockTranslations, self).__init__()
        self._catalog = DICTIONARIES[babel.locale_selector_func()]


class MockPlugin(IndicoPlugin):
    def init(self):
        pass


@pytest.fixture
def mock_translations(monkeypatch, request_context):
    domain = get_domain()
    locales = {'fr_FR': 'French',
               'en_GB': 'English'}
    monkeypatch.setattr('indico.util.i18n.get_all_locales', lambda: locales)
    monkeypatch.setattr(domain, 'get_translations', MockTranslations)


@pytest.mark.usefixtures('mock_translations')
def test_straight_translation():
    session.lang = 'fr_MP'  # 'Monty Python' French

    a = _(u'Fetch the cow')
    b = _(u'The wheels')

    assert isinstance(a, unicode)
    assert isinstance(b, unicode)


@pytest.mark.usefixtures('mock_translations')
def test_lazy_translation(monkeypatch):
    monkeypatch.setattr('indico.util.i18n.has_request_context', lambda: False)
    a = _(u'Fetch the cow')
    b = _(u'The wheels')
    monkeypatch.setattr('indico.util.i18n.has_request_context', lambda: True)

    assert isinstance(a, _LazyString)
    assert isinstance(b, _LazyString)

    session.lang = 'fr_MP'

    assert unicode(a) == u'Fetchez la vache'
    assert unicode(b) == u'Les wheels'


@pytest.mark.usefixtures('mock_translations')
def test_ngettext():
    session.lang = 'fr_MP'

    assert ngettext(u'{} cow', u'{} cows', 1).format(1) == u'1 vache'
    assert ungettext(u'{} cow', u'{} cows', 42).format(42) == u'42 vaches'


@pytest.mark.usefixtures('mock_translations')
def test_translate_bytes():
    session.lang = 'fr_MP'

    assert _(u'Fetch the cow') == u'Fetchez la vache'
    assert _('The wheels') == 'Les wheels'


@pytest.mark.usefixtures('mock_translations')
def test_context_manager():
    session.lang = 'fr_MP'
    with session_language('en_PI'):
        assert session.lang == 'en_PI'
        assert _(u'I need a drink.') == u"I be needin' a bottle of rhum!"

    assert session.lang == 'fr_MP'


def test_set_best_lang_no_request():
    assert not has_request_context()
    assert babel.locale_selector_func() == 'en_GB'


@pytest.mark.usefixtures('mock_translations')
def test_set_best_lang_request():
    with session_language('en_PI'):
        assert babel.locale_selector_func() == 'en_PI'


@pytest.mark.usefixtures('mock_translations')
def test_set_best_lang_no_session_lang():
    request.accept_languages = LanguageAccept([('en-PI', 1), ('fr_FR', 0.7)])
    assert babel.locale_selector_func() == 'fr_FR'

    request.accept_languages = LanguageAccept([('fr-FR', 1)])
    assert babel.locale_selector_func() == 'fr_FR'


@pytest.mark.usefixtures('mock_translations')
def test_translation_plugins(app, tmpdir):
    session.lang = 'fr_FR'
    plugin = MockPlugin(plugin_engine, app)
    app.extensions['pluginengine'].plugins['dummy'] = plugin
    plugin.root_path = tmpdir.strpath
    french_core_str = DICTIONARIES['fr_FR']['This is not a string']
    french_plugin_str = "This is not le french string"

    trans_dir = os.path.join(plugin.root_path, 'translations', 'fr_FR', 'LC_MESSAGES')
    os.makedirs(trans_dir)

    # Create proper *.mo file for plugin translation
    with open(os.path.join(trans_dir, 'messages.mo'), 'wb') as f:
        catalog = Catalog(locale='fr_FR', domain='plugin')
        catalog.add("This is not a string", "This is not le french string")
        write_mo(f, catalog)

    gettext_plugin = make_bound_gettext('dummy')

    assert _(u'This is not a string') == french_core_str
    assert gettext_context(u"This is not a string") == french_core_str
    assert isinstance(gettext_context(b"This is not a string"), unicode)
    assert isinstance(gettext_context(u"This is not a string"), unicode)
    assert gettext_plugin(u"This is not a string") == french_plugin_str

    with plugin.plugin_context():
        assert _(u'This is not a string') == french_core_str
        assert gettext_context(u"This is not a string") == french_plugin_str
        assert gettext_plugin(u"This is not a string") == french_plugin_str
