# -*- coding: utf-8 -*-
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# system lib imports
import os
import re

# stdlib imports
from distutils.cmd import Command
from gettext import NullTranslations
import ast

# external lib imports
from babel.support import Translations, LazyProxy
from babel.core import Locale
import pkg_resources

# indico imports
import indico.locale

# legacy indico imports
from MaKaC.common.contextManager import ContextManager


LOCALE_DIR = os.path.dirname(indico.locale.__file__)
LOCALE_DOMAIN = 'messages'

RE_TR_FUNCTION = re.compile(r"_\(\"([^\"]*)\"\)|_\('([^']*)'\)", re.DOTALL | re.MULTILINE)

# Store the locale in a thread-local object
nullTranslations = NullTranslations()


def _tr_eval(func, *args, **kwargs):
    # ok, eval time... is there a translation?
    if 'translation' in ContextManager.get():
        # yes? good, let's do it
        tr = ContextManager.get('translation')
    else:
        # no? too bad, just don't transate anything
        tr = nullTranslations
    return getattr(tr, func)(*args, **kwargs).encode('utf-8')


class LazyTranslations(Translations):
    """
    Defers translation in case there is still no translation available
    It will be then done when the value is finally used
    """
    def _wrapper(self, func, *args, **kwargs):
        # if there is a locale already defined
        if 'translation' in ContextManager.get():
            # straight translation
            translation = ContextManager.get('translation')
            return getattr(translation, func)(*args, **kwargs).encode('utf-8')
        else:
            # otherwise, defer translation to eval time
            return LazyProxy(_tr_eval, func, *args, **kwargs)

    def ugettext(self, text):
        return self._wrapper('ugettext', text)

    def ngettext(self, text):
        return self._wrapper('ngettext', text)


lazyTranslations = LazyTranslations()
lazyTranslations.install(unicode=True)

_ = ugettext = gettext = lazyTranslations.ugettext
ngettext = ungettext = lazyTranslations.ungettext

defaultLocale = 'en_US'


class IndicoLocale(Locale):
    """
    Extends the Babel Locale class with some utility methods
    """
    def weekday(self, daynum, short=True):
        """
        Returns the week day given the index
        """
        return self.days['format']['abbreviated' if short else 'wide'][daynum].encode('utf-8')


def setLocale(locale):
    """
    Set the current locale in the current thread context
    """
    ContextManager.set('locale', locale)
    ContextManager.set('translation', Translations.load(LOCALE_DIR, locale, LOCALE_DOMAIN))


def currentLocale():
    return IndicoLocale.parse(ContextManager.get('locale', defaultLocale))


def getAllLocales():
    """
    List all available locales/translations
    """
    return [loc for loc in pkg_resources.resource_listdir('indico.locale', '') if '.' not in loc]


availableLocales = getAllLocales()


def getLocaleDisplayNames(using=None):
    """
    List of (locale_id, locale_name) tuples
    """
    locales = [loc for loc in availableLocales if loc != using]
    if using:
        locales.insert(0, userLoc)
    return list((loc, IndicoLocale.parse(loc).get_display_name(using).encode('utf-8')) for loc in locales)


def parseLocale(locale):
    """
    Just a shortcut to babel
    """
    return Locale.parse(locale)


def i18nformat(text):
    """
    ATTENTION: only used for backward-compatibility
    Parses old '_() inside strings hack', translating as needed
    """
    return RE_TR_FUNCTION.sub(lambda x: _(filter(lambda y: y != None, x.groups())[0]), text)


class generate_messages_js(Command):
    """
    Translates *.po files to a JSON dict, with a little help of pojson
    """

    description = "generates JSON from po"
    user_options = [('input-dir=', None, 'input dir'),
                    ('output-dir=', None, 'output dir'),
                    ('domain=', None, 'domain')]
    boolean_options = []

    def initialize_options(self):
        self.input_dir = None
        self.output_dir = None
        self.domain = None

    def finalize_options(self):
        pass

    def run(self):
        try:
            pkg_resources.require('pojson')
        except pkg_resources.DistributionNotFound:
            print """
            pojson not found! JSTools is needed for JS i18n file generation, if you're building Indico from source. Please install it.
            i.e. try 'easy_install pojson'"""
            sys.exit(-1)

        from pojson import convert

        localeDirs = [name for name in os.listdir(self.input_dir) if os.path.isdir(os.path.join(self.input_dir, name))]

        for locale in localeDirs:
            result = convert(self.domain, os.path.join(
                self.input_dir, locale, "LC_MESSAGES", 'messages-js.po'), js=True, pretty_print=True)
            fname = os.path.join(self.output_dir, '%s.js' % locale)
            with open(fname, 'w') as f:
                f.write(result)
            print 'wrote %s' % fname


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
            yield (node.lineno, '', m[1].split('\n'), ['old style recursive strings'])
    else:
        for cnode in ast.iter_child_nodes(node):
            for rslt in  extract_node(cnode, keywords, commentTags, options, parents=(parents + [node])):
                yield rslt
