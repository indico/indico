# -*- coding: utf-8 -*-
##
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


from babel.support import Translations, LazyProxy
from babel.core import Locale
from gettext import NullTranslations

from indico.util.contextManager import ContextManager


# Store the locale in a thread-local object
nullTranslations = NullTranslations()



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

    def ungettext(self, singular, plural, n):
        return self._wrapper('ungettext', singular, plural, n)


lazyTranslations = LazyTranslations()
lazyTranslations.install(unicode=True)
