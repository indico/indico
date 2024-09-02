# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from collections import Counter

from babel import negotiate_locale
from babel.core import LOCALE_ALIASES, Locale
from babel.messages.pofile import read_po
from babel.support import NullTranslations
from flask import current_app, g, has_app_context, has_request_context, request, session
from flask_babel import Babel, Domain
from flask_babel import force_locale as _force_locale
from flask_babel import get_domain, get_locale
from flask_pluginengine import current_plugin
from speaklater import is_lazy_string, make_lazy_string
from werkzeug.utils import cached_property

from indico.core.config import config
from indico.util.caching import memoize_request


LOCALE_ALIASES = dict(LOCALE_ALIASES, en='en_GB')

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


def _indico_gettext(*args, **kwargs):
    func_name = kwargs.pop('func_name', 'gettext')
    plugin_name = kwargs.pop('plugin_name', None)

    translations = get_translation_domain(plugin_name).get_translations()
    return getattr(translations, func_name)(*args, **kwargs)


def lazy_gettext(string, plugin_name=None):
    if is_lazy_string(string):
        return string
    return make_lazy_string(_indico_gettext, string, plugin_name=plugin_name)


def orig_string(lazy_string):
    """Get the original string from a lazy string."""
    return lazy_string._args[0] if is_lazy_string(lazy_string) else lazy_string


def smart_func(func_name, plugin_name=None):
    def _wrap(*args, **kwargs):
        """
        Return either a translated string or a lazy-translatable object,
        depending on whether there is a session language or not (respectively).
        """
        if has_request_context() or func_name != 'gettext':
            # straight translation
            return _indico_gettext(*args, func_name=func_name, plugin_name=plugin_name, **kwargs)
        else:
            # otherwise, defer translation to eval time
            return lazy_gettext(*args, plugin_name=plugin_name)

    if plugin_name is _use_context:
        _wrap.__name__ = f'<smart {func_name}>'
    else:
        _wrap.__name__ = '<smart {} bound to {}>'.format(func_name, plugin_name or 'indico')
    return _wrap


def make_bound_gettext(plugin_name):
    """Create a smart gettext callable bound to the domain of the specified plugin."""
    return smart_func('gettext', plugin_name=plugin_name)


def make_bound_ngettext(plugin_name):
    """Create a smart ngettext callable bound to the domain of the specified plugin."""
    return smart_func('ngettext', plugin_name=plugin_name)


def make_bound_pgettext(plugin_name):
    """Create a smart pgettext callable bound to the domain of the specified plugin."""
    return smart_func('pgettext', plugin_name=plugin_name)


def make_bound_npgettext(plugin_name):
    """Create a smart npgettext callable bound to the domain of the specified plugin."""
    return smart_func('npgettext', plugin_name=plugin_name)


# Shortcuts
_ = gettext = make_bound_gettext(None)
ngettext = make_bound_ngettext(None)
pgettext = make_bound_pgettext(None)
npgettext = make_bound_npgettext(None)
L_ = lazy_gettext

# Plugin-context-sensitive gettext for templates
gettext_context = make_bound_gettext(_use_context)
ngettext_context = make_bound_ngettext(_use_context)
pgettext_context = make_bound_pgettext(_use_context)
npgettext_context = make_bound_npgettext(_use_context)


class NullDomain(Domain):
    """A `Domain` that doesn't contain any translations."""

    def __init__(self):
        super().__init__()
        self.null = NullTranslations()

    def get_translations(self):
        return self.null


class IndicoLocale(Locale):
    """Extend the Babel Locale class with some utility methods."""

    def weekday(self, daynum, short=True):
        """Return the week day given the index."""
        return self.days['format']['abbreviated' if short else 'wide'][daynum]

    @property
    def html_locale(self):
        """Return locale in HTML-compatible way (e.g., en-US instead of en_US)."""
        return f'{self.language}-{self.territory}'

    @cached_property
    def time_formats(self):
        formats = super().time_formats
        for v in formats.values():
            v.format = v.format.replace(':%(ss)s', '')
        return formats


def _remove_locale_script(locale):
    parts = locale.split('_')  # e.g. `en_GB` or `zh_Hans_CN`
    return f'{parts[0]}_{parts[-1]}'


def force_locale(locale, *, default=True):
    """Temporarily override the locale.

    Use this as a context manager in a ``with`` block.
    `locale` can be set to ``None`` to avoid translation and thus
    use the hardcoded string which is en_US.

    :param locale: The locale to force
    :param default: Whether to use the server default instead of en_US
                    if no locale is specified. Should be disabled only
                    for cases where an english string is always preferred,
                    e.g. when generating log messages that include stuff
                    like enum titles or dates
    """
    if default and not locale:
        locale = config.DEFAULT_LOCALE
    return _force_locale(locale or 'en_US')


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
                           lambda m: f'{m.group(1).lower()}_{m.group(2).upper()}',
                           resolved_lang)

    # As soon as we looked up a language, cache it during the request.
    # This will be returned when accessing `session.lang` since there's code
    # which reads the language from there and might fail (e.g. by returning
    # lazy strings) if it's not set.
    g.lang = resolved_lang
    return resolved_lang


def get_current_locale():
    return _get_current_locale(str(get_locale()))


@memoize_request
def _get_current_locale(locale):
    return IndicoLocale.parse(locale)


def get_all_locales():
    """List all available locales/names e.g. ``{'pt_PT': ('Portuguese', 'Portugal', True)}``."""
    if not has_app_context():
        return {}
    else:
        missing = object()
        languages = {str(t): config.CUSTOM_LANGUAGES.get(str(t), (t.language_name.title(), t.territory_name))
                     for t in babel.list_translations()
                     if config.CUSTOM_LANGUAGES.get(str(t), missing) is not None}
        counts = Counter(x[0] for x in languages.values())
        return {code: (name, territory or '', counts[name] > 1) for code, (name, territory) in languages.items()}


def set_session_lang(lang):
    """Set the current language in the current request context."""
    session.lang = lang


def parse_locale(locale):
    """Get a Locale object from a locale id."""
    return IndicoLocale.parse(locale)


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
