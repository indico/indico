# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from datetime import datetime

import pytest
from babel.messages import Catalog
from babel.messages.mofile import write_mo
from babel.support import Translations
from flask import has_request_context, request, session
from flask_babel import get_domain, get_locale
from speaklater import _LazyString
from werkzeug.datastructures import LanguageAccept

from indico.core.plugins import IndicoPlugin, plugin_engine
from indico.util.date_time import format_datetime
from indico.util.i18n import _, force_locale, gettext_context, make_bound_gettext, ngettext, pgettext


def _to_msgid(context, message):
    return f'{context}\x04{message}'


DICTIONARIES = {
    'fr_FR': {
        'This is not a string': "Ceci n'est pas une cha\u00cene"
    },

    'fr_CH': {  # monty python french (some of it), but babel doesn't like fr_MP :(
        'Fetch the cow': 'Fetchez la vache',
        'The wheels': 'Les wheels',
        ('{} cow', 0): '{} vache',
        ('{} cow', 1): '{} vaches',
        'I need a drink.': 'Booze, svp.',
    },

    'en_AU': {  # pirate english, but babel doesn't like en_PI :(
        'I need a drink.': "I be needin' a bottle of rhum!"
    },

    'pl_PL': {
        ('Convener', 0): 'Lider',
        ('Convener', 1): 'Liderzy',
        (_to_msgid('Dummy context', 'Convener'), 0): 'Lider (Context)',
        (_to_msgid('Dummy context', 'Convener'), 1): 'Liderzy (Context)',
    },
}


class MockTranslations(Translations):
    """
    Mock `Translations` class - returns a mock dictionary
    based on the selected locale
    """

    def __init__(self):
        super().__init__()
        self._catalog = DICTIONARIES[str(get_locale())]


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
    session.lang = 'fr_CH'  # 'Monty Python' French

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

    session.lang = 'fr_CH'

    assert str(a) == 'Fetchez la vache'
    assert str(b) == 'Les wheels'


@pytest.mark.usefixtures('mock_translations')
def test_ngettext():
    session.lang = 'fr_CH'

    assert ngettext('{} cow', '{} cows', 1).format(1) == '1 vache'
    assert ngettext('{} cow', '{} cows', 42).format(42) == '42 vaches'


@pytest.mark.usefixtures('mock_translations')
def test_translate_bytes():
    session.lang = 'fr_CH'

    assert _('Fetch the cow') == 'Fetchez la vache'
    assert _('The wheels') == 'Les wheels'


@pytest.mark.usefixtures('mock_translations')
def test_force_locale():
    session.lang = 'en_AU'
    dt = datetime(2022, 8, 29, 13, 37)

    assert format_datetime(dt, timezone='UTC') == '29 Aug 2022, 1:37 pm'
    assert _('I need a drink.') == "I be needin' a bottle of rhum!"

    with force_locale('fr_CH'):
        assert format_datetime(dt, timezone='UTC') == '29 août 2022, 13:37'
        assert _('I need a drink.') == 'Booze, svp.'

    assert format_datetime(dt, timezone='UTC') == '29 Aug 2022, 1:37 pm'
    assert _('I need a drink.') == "I be needin' a bottle of rhum!"

    assert session.lang == 'en_AU'


def test_set_best_lang_no_request():
    assert not has_request_context()
    assert str(get_locale()) == 'en_GB'


@pytest.mark.usefixtures('mock_translations')
def test_set_best_lang_request():
    with force_locale('en_AU'):
        assert str(get_locale()) == 'en_AU'


@pytest.mark.usefixtures('mock_translations')
def test_set_best_lang_no_session_lang():
    request.accept_languages = LanguageAccept([('en-PI', 1), ('fr_FR', 0.7)])
    assert str(get_locale()) == 'fr_FR'

    request.accept_languages = LanguageAccept([('fr-FR', 1)])
    assert str(get_locale()) == 'fr_FR'


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


@pytest.mark.usefixtures('mock_translations')
def test_gettext_plurals():
    session.lang = 'pl_PL'  # Polish

    assert _('Convener') == 'Lider'
    assert _('User') == 'User'


@pytest.mark.usefixtures('mock_translations')
def test_pgettext_plurals():
    session.lang = 'pl_PL'  # Polish

    assert pgettext('Dummy context', 'Convener') == 'Lider (Context)'
    assert pgettext('Dummy context', 'User') == 'User'


@pytest.mark.usefixtures('mock_translations')
def test_force_user_locale(dummy_user):
    session.lang = 'en_AU'
    dt = datetime(2022, 8, 29, 13, 37)

    assert format_datetime(dt, timezone='UTC') == '29 Aug 2022, 1:37 pm'
    assert _('I need a drink.') == "I be needin' a bottle of rhum!"

    dummy_user.settings.set('lang', 'fr_CH')
    with dummy_user.force_user_locale():
        assert format_datetime(dt, timezone='UTC') == '29 août 2022, 13:37'
        assert _('I need a drink.') == 'Booze, svp.'

    assert format_datetime(dt, timezone='UTC') == '29 Aug 2022, 1:37 pm'
    assert _('I need a drink.') == "I be needin' a bottle of rhum!"

    assert session.lang == 'en_AU'
