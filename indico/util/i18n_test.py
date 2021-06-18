# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

import pytest
from babel.messages import Catalog
from babel.messages.mofile import write_mo
from babel.support import Translations
from flask import has_request_context, request, session
from flask_babel import get_domain
from speaklater import _LazyString
from werkzeug.datastructures import LanguageAccept

from indico.core.plugins import IndicoPlugin, plugin_engine
from indico.util.i18n import _, babel, gettext_context, make_bound_gettext, ngettext, session_language


DICTIONARIES = {
    'fr_FR': {
        'This is not a string': "Ceci n'est pas une cha\u00cene"
    },

    'fr_MP': {
        'Fetch the cow': 'Fetchez la vache',
        'The wheels': 'Les wheels',
        ('{} cow', 0): '{} vache',
        ('{} cow', 1): '{} vaches',
    },

    'en_PI': {
        'I need a drink.': "I be needin' a bottle of rhum!"
    }
}


class MockTranslations(Translations):
    """
    Mock `Translations` class - returns a mock dictionary
    based on the selected locale
    """

    def __init__(self):
        super().__init__()
        self._catalog = DICTIONARIES[babel.locale_selector_func()]


class MockPlugin(IndicoPlugin):
    def init(self):
        pass


@pytest.fixture
def mock_translations(monkeypatch, request_context):
    domain = get_domain()
    locales = {'fr_FR': ('French', 'France'),
               'en_GB': ('English', 'United Kingdom')}
    monkeypatch.setattr('indico.util.i18n.get_all_locales', lambda: locales)
    monkeypatch.setattr(domain, 'get_translations', MockTranslations)


@pytest.mark.usefixtures('mock_translations')
def test_straight_translation():
    session.lang = 'fr_MP'  # 'Monty Python' French

    a = _('Fetch the cow')
    b = _('The wheels')

    assert isinstance(a, str)
    assert isinstance(b, str)


@pytest.mark.usefixtures('mock_translations')
def test_lazy_translation(monkeypatch):
    monkeypatch.setattr('indico.util.i18n.has_request_context', lambda: False)
    a = _('Fetch the cow')
    b = _('The wheels')
    monkeypatch.setattr('indico.util.i18n.has_request_context', lambda: True)

    assert isinstance(a, _LazyString)
    assert isinstance(b, _LazyString)

    session.lang = 'fr_MP'

    assert str(a) == 'Fetchez la vache'
    assert str(b) == 'Les wheels'


@pytest.mark.usefixtures('mock_translations')
def test_ngettext():
    session.lang = 'fr_MP'

    assert ngettext('{} cow', '{} cows', 1).format(1) == '1 vache'
    assert ngettext('{} cow', '{} cows', 42).format(42) == '42 vaches'


@pytest.mark.usefixtures('mock_translations')
def test_translate_bytes():
    session.lang = 'fr_MP'

    assert _('Fetch the cow') == 'Fetchez la vache'
    assert _('The wheels') == 'Les wheels'


@pytest.mark.usefixtures('mock_translations')
def test_context_manager():
    session.lang = 'fr_MP'
    with session_language('en_PI'):
        assert session.lang == 'en_PI'
        assert _('I need a drink.') == "I be needin' a bottle of rhum!"

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
    french_plugin_str = 'This is not le french string'

    trans_dir = os.path.join(plugin.root_path, 'translations', 'fr_FR', 'LC_MESSAGES')
    os.makedirs(trans_dir)

    # Create proper *.mo file for plugin translation
    with open(os.path.join(trans_dir, 'messages.mo'), 'wb') as f:
        catalog = Catalog(locale='fr_FR', domain='plugin')
        catalog.add('This is not a string', 'This is not le french string')
        write_mo(f, catalog)

    gettext_plugin = make_bound_gettext('dummy')

    assert _('This is not a string') == french_core_str
    assert gettext_context('This is not a string') == french_core_str
    assert isinstance(gettext_context('This is not a string'), str)
    assert gettext_plugin('This is not a string') == french_plugin_str

    with plugin.plugin_context():
        assert _('This is not a string') == french_core_str
        assert gettext_context('This is not a string') == french_plugin_str
        assert gettext_plugin('This is not a string') == french_plugin_str
