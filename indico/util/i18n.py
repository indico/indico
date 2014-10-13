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

import ast
import re

from babel.core import Locale
from babel.support import Translations
from babel import negotiate_locale
from flask import session, request, has_request_context, current_app
from flask_babelex import Babel, lazy_gettext, get_domain

from MaKaC.common.info import HelperMaKaCInfo


RE_TR_FUNCTION = re.compile(r"_\(\"([^\"]*)\"\)|_\('([^']*)'\)", re.DOTALL | re.MULTILINE)

babel = Babel()


def smart_func(func_name):
    def _wrap(*args, **kwargs):
        """
        Returns either a translated string or a lazy-translatable object,
        depending on whether there is a session language or not (respectively)
        """

        if (has_request_context() and session.lang) or func_name != 'ugettext':
            # straight translation
            translations = get_domain().get_translations()
            return getattr(translations, func_name)(*args, **kwargs).encode('utf-8')
        else:
            # otherwise, defer translation to eval time
            return lazy_gettext(*args, **kwargs)
    return _wrap


# Shortcuts
_ = gettext = smart_func('ugettext')
ngettext = smart_func('ungettext')
L_ = lazy_gettext

# Just a marker for message extraction
N_ = lambda text: text


class IndicoLocale(Locale):
    """
    Extends the Babel Locale class with some utility methods
    """
    def weekday(self, daynum, short=True):
        """
        Returns the week day given the index
        """
        return self.days['format']['abbreviated' if short else 'wide'][daynum].encode('utf-8')


class IndicoTranslations(Translations):
    """
    Routes translations through the 'smart' translators defined above
    """

    def ugettext(self, message):
        return gettext(message)

    def ungettext(self, msgid1, msgid2, n):
        return ngettext(msgid1, msgid2, n)


IndicoTranslations().install(unicode=True)


@babel.localeselector
def set_best_lang():
    """
    Get the best language/locale for the current user. This means that first
    the session will be checked, and then in the absence of an explicitly-set
    language, we will try to guess it from the browser settings and only
    after that fall back to the server's default.
    """

    if not has_request_context():
        return 'en_GB' if current_app.config['TESTING'] else HelperMaKaCInfo.getMaKaCInfoInstance().getLang()
    elif session.lang is not None:
        return session.lang

    # try to use browser language
    preferred = [x.replace('-', '_') for x in request.accept_languages.values()]
    resolved_lang = negotiate_locale(preferred, get_all_locales())

    if not resolved_lang:
        # fall back to server default
        minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
        resolved_lang = minfo.getLang()

    session.lang = resolved_lang
    return resolved_lang


def get_current_locale():
    return IndicoLocale.parse(set_best_lang())


def get_all_locales():
    """
    List all available locales/names e.g. ('pt_PT', 'Portuguese')
    """
    if babel.app is None:
        return {}
    else:
        return {str(t): t.language_name for t in babel.list_translations()}


def set_session_lang(lang):
    """
    Set the current language in the current request context
    """
    session.lang = lang


def parse_locale(locale):
    """
    Get a Locale object from a locale id
    """
    return IndicoLocale.parse(locale)


def i18nformat(text):
    """
    ATTENTION: only used for backward-compatibility
    Parses old '_() inside strings hack', translating as needed
    """

    # this is a bit of a dirty hack, but cannot risk emitting lazy proxies here
    if not session.lang:
        set_best_lang()

    return RE_TR_FUNCTION.sub(lambda x: _(next(y for y in x.groups() if y is not None)), text)


def extract(fileobj, keywords, commentTags, options):
    """
    Babel mini-extractor for old-style _() inside strings
    """
    astree = ast.parse(fileobj.read())
    return extract_node(astree, keywords, commentTags, options)


def extract_node(node, keywords, commentTags, options, parents=[None]):
    if isinstance(node, ast.Str) and isinstance(parents[-1], (ast.Assign, ast.Call)):
        matches = RE_TR_FUNCTION.findall(node.s)
        for m in matches:
            line = m[0] or m[1]
            yield (node.lineno, '', line.split('\n'), ['old style recursive strings'])
    else:
        for cnode in ast.iter_child_nodes(node):
            for rslt in extract_node(cnode, keywords, commentTags, options, parents=(parents + [node])):
                yield rslt
