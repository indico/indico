# -*- coding: utf-8 -*-
##
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


from babel.support import Translations, LazyProxy as _LazyProxy
from babel.core import Locale
from gettext import NullTranslations

from indico.util.contextManager import ContextManager


# Store the locale in a thread-local object
nullTranslations = NullTranslations()


class LazyProxy(_LazyProxy):
    """
    Stateless version of Babel's LazyProxy
    """
    def value(self):
        # just return
        return  self._func(*self._args, **self._kwargs)
    value = property(value)


class IndicoLocale(Locale):
    """
    Extends the Babel Locale class with some utility methods
    """
    def weekday(self, daynum, short=True):
        """
        Returns the week day given the index
        """
        return self.days['format']['abbreviated' if short else 'wide'][daynum].encode('utf-8')


def _tr_eval(func, *args, **kwargs):
    # ok, eval time... is there a translation?

    if 'translation' in ContextManager.get():
        # yes? good, let's do it
        tr = ContextManager.get('translation')
    else:
        # no? too bad, just don't translate anything
        tr = nullTranslations
    res = getattr(tr, func)(*args, **kwargs).encode('utf-8')
    return res


class LazyTranslations(Translations):
    """
    Defers translation in case there is still no translation available
    It will be then done when the value is finally used
    """

    def __init__(self, forceLazy=False):
        self.force = forceLazy
        super(LazyTranslations, self).__init__()

    def _wrapper(self, func, *args, **kwargs):
        # if there is a locale already defined, use it
        # (unless we have forced "lazy mode")
        if 'translation' in ContextManager.get() and not self.force:
            # straight translation
            translation = ContextManager.get('translation')
            return getattr(translation, func)(*args, **kwargs)
        else:
            # otherwise, defer translation to eval time
            return LazyProxy(_tr_eval, func, *args, **kwargs)

    def gettext(self, text):
        return self._wrapper('gettext', text)

    def ngettext(self, singular, plural, n):
        return self._wrapper('ngettext', singular, plural, n)


lazyTranslations = LazyTranslations()
forceLazyTranslations = LazyTranslations(forceLazy=True)
lazyTranslations.install(unicode=False)
