# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import os
import posixpath
import re

from flask import session
from flask.helpers import get_root_path
from mako import exceptions
from mako.lookup import TemplateLookup

from indico.legacy.common.utils import formatDate, formatDuration, formatTime


# The main template directory
FILTER_IMPORTS = [
    'from indico.util.string import encode_if_unicode',
    'from indico.util.string import render_markdown_utf8 as m',
    'from indico.util.i18n import _'
]


class IndicoTemplateLookup(TemplateLookup):
    def get_template(self, uri):
        """Return a :class:`.Template` object corresponding to the given
        URL.

        Note the "relativeto" argument is not supported here at the moment.
        """
        try:
            if self.filesystem_checks:
                return self._check(uri, self._collection[uri])
            else:
                return self._collection[uri]
        except KeyError:
            if uri[0] == "/" and os.path.isfile(uri):
                return self._load(uri, uri)

            u = re.sub(r'^/+', '', uri)
            for dir_ in self.directories:
                srcfile = posixpath.normpath(posixpath.join(dir_, u))
                if os.path.isfile(srcfile):
                    return self._load(srcfile, uri)
            else:
                # We did not find anything, so we raise an exception
                raise exceptions.TopLevelLookupException('Can\'t locate template for uri {0!r}'.format(uri))


def _define_lookup():
    tpl_dir = os.path.join(get_root_path('indico'), 'legacy/webinterface/tpls')
    return IndicoTemplateLookup(directories=[tpl_dir],
                                disable_unicode=True,
                                input_encoding='utf-8',
                                default_filters=['encode_if_unicode', 'str'],
                                filesystem_checks=True,
                                imports=FILTER_IMPORTS,
                                cache_enabled=True)


mako = _define_lookup()


def render(tplPath, params={}):
    """Render the template."""
    template = mako.get_template(tplPath)
    registerHelpers(params)
    return template.render(**params)


def mako_call_template_hook(*name, **kwargs):
    from indico.web.flask.templating import call_template_hook

    kwargs = {k: unicode(v, 'utf-8') if isinstance(v, str) else v for k, v in kwargs.iteritems()}
    result = call_template_hook(*name, **kwargs)
    return result.encode('utf-8')


def registerHelpers(objDict):
    """
    Adds helper methods to the dictionary.
    Does it only if symbol does not exist - backward compatibility.
    """
    from indico.util.mdx_latex import latex_escape
    objDict.setdefault('formatTime', formatTime)
    objDict.setdefault('formatDate', formatDate)
    objDict.setdefault('latex_escape', latex_escape)
    objDict.setdefault('formatDuration', formatDuration)
    objDict.setdefault('_session', session)
