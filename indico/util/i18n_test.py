# -*- coding: utf-8 -*-
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import pytest
from babel.support import Translations
from flask import session
from flask_babelex import get_domain
from speaklater import _LazyString

from indico.util.i18n import _, ngettext


class MockTranslations(Translations):

    def __init__(self):
        super(MockTranslations, self).__init__()

        self._catalog = {
            'Fetch the cow': u'Fetchez la vache',
            'The wheels': u'Les wheels',
            ('{} cow', 0): u'{} vache',
            ('{} cow', 1): u'{} vaches'
        }


@pytest.fixture(autouse=True)
def mock_translations(monkeypatch, request_context):
    domain = get_domain()
    monkeypatch.setattr(domain, 'get_translations', MockTranslations)


def test_straight_translation():
    session.lang = 'fr_MP'  # 'Monty Python' French

    a = _(u'Fetch the cow')
    b = _(u'The wheels')

    assert isinstance(a, unicode)
    assert isinstance(b, unicode)


def test_lazy_translation():
    a = _(u'Fetch the cow')
    b = _(u'The wheels')

    assert isinstance(a, _LazyString)
    assert isinstance(b, _LazyString)

    session.lang = 'fr_MP'

    assert unicode(a) == u'Fetchez la vache'
    assert unicode(b) == u'Les wheels'


def test_ngettext():
    session.lang = 'fr_MP'

    assert ngettext(u'{} cow', u'{} cows', 1).format(1) == u'1 vache'
    assert ngettext(u'{} cow', u'{} cows', 42).format(42) == u'42 vaches'


def test_translate_bytes():
    session.lang = 'fr_MP'

    assert _(u'Fetch the cow') == u'Fetchez la vache'
    assert _('The wheels') == 'Les wheels'
