# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import ast
import errno
import traceback
import os
import re
import textwrap
import warnings
from contextlib import contextmanager

from babel import negotiate_locale
from babel.core import Locale
from babel.messages.pofile import read_po
from babel.support import Translations
from flask import session, request, has_request_context, current_app
from flask_babelex import Babel, get_domain
from flask_pluginengine import current_plugin
from speaklater import is_lazy_string, make_lazy_string

from indico.core.config import Config
from indico.core.db import DBMgr
from indico.core.signals import after_process

from MaKaC.common.info import HelperMaKaCInfo


RE_TR_FUNCTION = re.compile(r'''_\("([^"]*)"\)|_\('([^']*)'\)''', re.DOTALL | re.MULTILINE)

babel = Babel()
_auto = object()


def get_translation_domain(plugin_name=_auto):
    """Get the translation domain for the given plugin

    If `plugin_name` is omitted, the plugin will be taken from current_plugin.
    If `plugin_name` is None, the core translation domain ('indico') will be used.
    """
    if plugin_name is None:
        return get_domain()
    else:
        from indico.core.plugins import plugin_engine
        plugin = plugin_engine.get_plugin(plugin_name) if plugin_name is not _auto else current_plugin
        if plugin and plugin.translation_path:
            return current_plugin.translation_domain
        else:
            return get_domain()


def gettext_unicode(*args, **kwargs):
    func_name = kwargs.pop('func_name', 'ugettext')
    plugin_name = kwargs.pop('plugin_name', None)

    if not isinstance(args[0], unicode):
        args = [(text.decode('utf-8') if isinstance(text, str) else text) for text in args]
        using_unicode = False
    else:
        using_unicode = True

    translations = get_translation_domain(plugin_name).get_translations()
    res = getattr(translations, func_name)(*args, **kwargs)
    if not using_unicode:
        res = res.encode('utf-8')
    return res


def lazy_gettext(string, plugin_name=None):
    if is_lazy_string(string):
        return string
    return make_lazy_string(lambda s: gettext_unicode(s, plugin_name=plugin_name), string)


def smart_func(func_name, plugin_name=None):
    def _wrap(*args, **kwargs):
        """
        Returns either a translated string or a lazy-translatable object,
        depending on whether there is a session language or not (respectively)
        """
        if (has_request_context() and session.lang) or func_name != 'ugettext':
            # straight translation
            return gettext_unicode(*args, func_name=func_name, plugin_name=plugin_name, **kwargs)

        else:
            # otherwise, defer translation to eval time
            return lazy_gettext(*args, plugin_name=plugin_name)
    return _wrap


def make_bound_gettext(plugin_name):
    """Creates a smart gettext callable bound to the domain of the specified plugin"""
    return smart_func('ugettext', plugin_name=plugin_name)


def make_bound_ngettext(plugin_name):
    """Creates a smart ngettext callable bound to the domain of the specified plugin"""
    return smart_func('ungettext', plugin_name=plugin_name)


# Shortcuts
_ = ugettext = gettext = make_bound_gettext(None)
ungettext = ngettext = make_bound_ngettext(None)
L_ = lazy_gettext

# Plugin-context-sensitive gettext
gettext_context = make_bound_gettext(_auto)
ngettext_context = make_bound_ngettext(_auto)

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

    def _check_stack(self):
        stack = traceback.extract_stack()
        # [..., the caller we are looking for, ugettext/ungettext, this function]
        frame = stack[-3]
        frame_msg = textwrap.dedent("""
            File "{}", line {}, in {}
              {}
        """).strip().format(*frame)
        msg = ('Using the gettext function (`_`) patched into the builtins is disallowed.\n'
               'Please import it from `indico.util.i18n` instead.\n'
               'The offending code was found in this location:\n{}').format(frame_msg)
        if 'MaKaC/' in frame[0]:
            # legacy code gets off with a warning
            warnings.warn(msg, RuntimeWarning)
        else:
            raise RuntimeError(msg)

    def ugettext(self, message):
        if Config.getInstance().getDebug():
            self._check_stack()
        return gettext(message)

    def ungettext(self, msgid1, msgid2, n):
        if Config.getInstance().getDebug():
            self._check_stack()
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
        with DBMgr.getInstance().global_connection():
            # fall back to server default
            minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
            resolved_lang = minfo.getLang()

    session.lang = resolved_lang
    return resolved_lang


def get_current_locale():
    return IndicoLocale.parse(set_best_lang())


def get_all_locales():
    """
    List all available locales/names e.g. {'pt_PT': 'Portuguese'}
    """
    if babel.app is None:
        return {}
    else:
        return {str(t): t.language_name.title() for t in babel.list_translations()}


def set_session_lang(lang):
    """
    Set the current language in the current request context
    """
    session.lang = lang


@contextmanager
def session_language(lang):
    """
    Context manager that temporarily sets session language
    """
    old_lang = session.lang

    set_session_lang(lang)
    yield
    set_session_lang(old_lang)


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


def po_to_json(po_file, locale=None, domain=None):
    """
    Converts *.po file to a json-like data structure
    """
    with open(po_file, 'rb') as f:
        po_data = read_po(f, locale=locale, domain=domain)

    messages = dict((message.id[0], message.string) if message.pluralizable else (message.id, [message.string])
                    for message in po_data)

    messages[''] = {
        'domain': po_data.domain,
        'lang': str(po_data.locale),
        'plural_forms': po_data.plural_forms
    }

    return {
        (po_data.domain or ''): messages
    }


@after_process.connect
def delete_old_i18n_cache(sender, **kwargs):
    """
    deletes old i18n files on startup
    """
    config = Config.getInstance()
    for locale_name in get_all_locales():
        file_path = os.path.join(config.getXMLCacheDir(), 'assets_i18n_{}.js'.format(locale_name))
        if os.path.exists(file_path):
            # file can be deleted many times in multi-process environment
            try:
                os.unlink(file_path)
            except OSError, e:
                if e.errno != errno.ENOENT:
                    raise
