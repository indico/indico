# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import ast
import re
import textwrap
import traceback
import warnings
from contextlib import contextmanager

from babel import negotiate_locale
from babel.core import LOCALE_ALIASES, Locale
from babel.messages.pofile import read_po
from babel.support import NullTranslations, Translations
from flask import current_app, g, has_app_context, has_request_context, request, session
from flask_babelex import Babel, Domain, get_domain
from flask_pluginengine import current_plugin
from speaklater import is_lazy_string, make_lazy_string
from werkzeug.utils import cached_property

from indico.core.config import config
from indico.util.caching import memoize_request


LOCALE_ALIASES = dict(LOCALE_ALIASES, en='en_GB')
RE_TR_FUNCTION = re.compile(r'''_\("([^"]*)"\)|_\('([^']*)'\)''', re.DOTALL | re.MULTILINE)

babel = Babel()
_use_context = object()


def get_translation_domain(plugin_name=_use_context):
    """Get the translation domain for the given plugin.

    If `plugin_name` is omitted, the plugin will be taken from current_plugin.
    If `plugin_name` is None, the core translation domain ('indico') will be used.
    """
    if plugin_name is None:
        return get_domain()
    else:
        plugin = None
        if has_app_context():
            from indico.core.plugins import plugin_engine
            plugin = plugin_engine.get_plugin(plugin_name) if plugin_name is not _use_context else current_plugin
        if plugin:
            return plugin.translation_domain
        else:
            return get_domain()


def gettext_unicode(*args, **kwargs):
    from indico.util.string import inject_unicode_debug
    func_name = kwargs.pop('func_name', 'ugettext')
    plugin_name = kwargs.pop('plugin_name', None)
    force_unicode = kwargs.pop('force_unicode', False)

    if not isinstance(args[0], unicode):
        args = [(text.decode('utf-8') if isinstance(text, str) else text) for text in args]
        using_unicode = force_unicode
    else:
        using_unicode = True

    translations = get_translation_domain(plugin_name).get_translations()
    res = getattr(translations, func_name)(*args, **kwargs)
    res = inject_unicode_debug(res)
    if not using_unicode:
        res = res.encode('utf-8')
    return res


def lazy_gettext(string, plugin_name=None):
    if is_lazy_string(string):
        return string
    return make_lazy_string(gettext_unicode, string, plugin_name=plugin_name)


def orig_string(lazy_string):
    """Get the original string from a lazy string."""
    return lazy_string._args[0] if is_lazy_string(lazy_string) else lazy_string


def smart_func(func_name, plugin_name=None, force_unicode=False):
    def _wrap(*args, **kwargs):
        """
        Returns either a translated string or a lazy-translatable object,
        depending on whether there is a session language or not (respectively)
        """

        if has_request_context() or func_name != 'ugettext':
            # straight translation
            return gettext_unicode(*args, func_name=func_name, plugin_name=plugin_name, force_unicode=force_unicode,
                                   **kwargs)
        else:
            # otherwise, defer translation to eval time
            return lazy_gettext(*args, plugin_name=plugin_name)
    if plugin_name is _use_context:
        _wrap.__name__ = '<smart {}>'.format(func_name)
    else:
        _wrap.__name__ = '<smart {} bound to {}>'.format(func_name, plugin_name or 'indico')
    return _wrap


def make_bound_gettext(plugin_name, force_unicode=False):
    """
    Create a smart gettext callable bound to the domain of the specified plugin.
    """
    return smart_func('ugettext', plugin_name=plugin_name, force_unicode=force_unicode)


def make_bound_ngettext(plugin_name, force_unicode=False):
    """
    Create a smart ngettext callable bound to the domain of the specified plugin.
    """
    return smart_func('ungettext', plugin_name=plugin_name, force_unicode=force_unicode)


# Shortcuts
_ = ugettext = gettext = make_bound_gettext(None)
ungettext = ngettext = make_bound_ngettext(None)
L_ = lazy_gettext

# Plugin-context-sensitive gettext for templates
# They always return unicode even when passed a bytestring
gettext_context = make_bound_gettext(_use_context, force_unicode=True)
ngettext_context = make_bound_ngettext(_use_context, force_unicode=True)

# Just a marker for message extraction
N_ = lambda text: text  # noqa


class NullDomain(Domain):
    """A `Domain` that doesn't contain any translations."""

    def __init__(self):
        super(NullDomain, self).__init__()
        self.null = NullTranslations()

    def get_translations(self):
        return self.null


class IndicoLocale(Locale):
    """Extend the Babel Locale class with some utility methods."""

    def weekday(self, daynum, short=True):
        """Return the week day given the index."""
        return self.days['format']['abbreviated' if short else 'wide'][daynum].encode('utf-8')

    @cached_property
    def time_formats(self):
        formats = super(IndicoLocale, self).time_formats
        for k, v in formats.items():
            v.format = v.format.replace(':%(ss)s', '')
        return formats


class IndicoTranslations(Translations):
    """
    Route translations through the 'smart' translators defined above.
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
        if 'indico/legacy/' in frame[0]:
            # legacy code gets off with a warning
            warnings.warn(msg, RuntimeWarning)
        else:
            raise RuntimeError(msg)

    def ugettext(self, message):
        from indico.core.config import config
        if config.DEBUG:
            self._check_stack()
        return gettext(message)

    def ungettext(self, msgid1, msgid2, n):
        from indico.core.config import config
        if config.DEBUG:
            self._check_stack()
        return ngettext(msgid1, msgid2, n)


IndicoTranslations().install(unicode=True)


def _remove_locale_script(locale):
    parts = locale.split('_')  # e.g. `en_GB` or `zh_Hans_CN`
    return '{}_{}'.format(parts[0], parts[-1])


@babel.localeselector
def set_best_lang(check_session=True):
    """Get the best language/locale for the current user.

    This means that first the session will be checked, and then in the
    absence of an explicitly-set language, we will try to guess it from
    the browser settings and only after that fall back to
    the server's default.
    """
    from indico.core.config import config

    if not has_request_context():
        return 'en_GB' if current_app.config['TESTING'] else config.DEFAULT_LOCALE
    elif 'lang' in g:
        return g.lang
    elif check_session and session.lang is not None:
        return session.lang

    # chinese uses `zh-Hans-CN`, but browsers send `zh-CN`
    all_locales = {_remove_locale_script(loc).lower(): loc for loc in get_all_locales()}

    # try to use browser language
    preferred = [x.replace('-', '_') for x in request.accept_languages.values()]
    resolved_lang = negotiate_locale(preferred, list(all_locales), aliases=LOCALE_ALIASES)

    if not resolved_lang:
        if current_app.config['TESTING']:
            return 'en_GB'

        # fall back to server default
        resolved_lang = config.DEFAULT_LOCALE

    # restore script information if necessary
    try:
        resolved_lang = all_locales[resolved_lang.lower()]
    except KeyError:
        # this happens if we have e.g. a development setup with no built languages.
        # in this case `get_all_locales()` only contains `en_EN`
        return 'en_GB'

    # normalize to xx_YY capitalization
    resolved_lang = re.sub(r'^([a-zA-Z]+)_([a-zA-Z]+)$',
                           lambda m: '{}_{}'.format(m.group(1).lower(), m.group(2).upper()),
                           resolved_lang)

    # As soon as we looked up a language, cache it during the request.
    # This will be returned when accessing `session.lang` since there's code
    # which reads the language from there and might fail (e.g. by returning
    # lazy strings) if it's not set.
    g.lang = resolved_lang
    return resolved_lang


@memoize_request
def get_current_locale():
    return IndicoLocale.parse(set_best_lang())


def get_all_locales():
    """
    List all available locales/names e.g. ``{'pt_PT': ('Portuguese', 'Portugal)}``.
    """
    if babel.app is None:
        return {}
    else:
        missing = object()
        return {str(t): config.CUSTOM_LANGUAGES.get(str(t), (t.language_name.title(), t.territory_name))
                for t in babel.list_translations()
                if config.CUSTOM_LANGUAGES.get(str(t), missing) is not None}


def set_session_lang(lang):
    """Set the current language in the current request context."""
    session.lang = lang


@contextmanager
def session_language(lang):
    """Context manager that temporarily sets session language."""
    old_lang = session.lang

    set_session_lang(lang)
    yield
    set_session_lang(old_lang)


def parse_locale(locale):
    """Get a Locale object from a locale id."""
    return IndicoLocale.parse(locale)


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
    """Convert *.po file to a json-like data structure."""
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
