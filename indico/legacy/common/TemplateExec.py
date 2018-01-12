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
import xml.sax.saxutils

from flask import current_app as app
from flask import g, render_template, request, session
from flask.helpers import get_root_path
from mako import exceptions
from mako.lookup import TemplateLookup

from indico.core.config import config
from indico.legacy.common.utils import formatDate, formatDateTime, formatDuration, formatTime


# The main template directory
FILTER_IMPORTS = [
    'from indico.util.json import dumps as j',
    'from indico.util.string import encode_if_unicode, sanitize_html',
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


def inlineContextHelp(helpContent):
    """
    Allows you to put [?], the context help marker.
    Help content passed as argument helpContent.
    """
    from indico.legacy.webinterface.wcomponents import WTemplated
    params = {"helpContent": helpContent,
              "imgSrc": '{}/help.png'.format(config.IMAGES_BASE_URL)}
    return WTemplated('InlineContextHelp').getHTML(params)


def contextHelp(helpId):
    """
    Allows you to put [?], the context help marker.
    Help content is defined in <div id="helpId"></div>.
    """
    from indico.legacy.webinterface.wcomponents import WTemplated
    params = {"helpId": helpId,
              "imgSrc": '{}/help.png'.format(config.IMAGES_BASE_URL)}
    return WTemplated('ContextHelp').getHTML(params)


def verbose(s, default=""):
    """
    Purpose: avoid showing "None" to user; show default value instead.
    """
    if isinstance(s, bool) and s != None:
        if s:
            return "yes"
        else:
            return "no"
    return s or default


def verbose_dt(dt, default=""):
    """Return verbose date representation."""
    if dt == None:
        return default
    return ("%s_%2s:%2s" % (formatDate(dt.date()).replace(' ', '_'),
                            dt.hour,
                            dt.minute)).replace(' ', '0').replace('_', ' ')


def verbose_t(t, default=""):
    """Return verbose time representation."""
    if t == None:
        return default
    return ("%2d:%2d" % (t.hour, t.minute)).replace(' ', '0')


def escape(s):
    """HTML escape"""
    return xml.sax.saxutils.escape(s)


def quoteattr(s):
    """quotes escape"""
    return xml.sax.saxutils.quoteattr(s)


def linkify(s):
    urlIxStart = s.find('http://')
    if urlIxStart == -1:
        return s
    urlIxEnd = s.find(' ', urlIxStart + 1)
    s = (s[0:urlIxStart] + '<a href="' + s[urlIxStart:urlIxEnd] + '">'
            + s[urlIxStart:urlIxEnd] + "</a> " + s[urlIxEnd:])
    return s


def truncateTitle(title, maxSize=30):
    if len(title) > maxSize:
        return title[:maxSize] + '...'
    else:
        return title


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
    from indico.modules.auth.util import url_for_login, url_for_logout
    from indico.util.date_time import format_date, format_datetime, format_human_timedelta, format_number, format_time
    from indico.util.i18n import ngettext
    from indico.util.mdx_latex import latex_escape
    from indico.util.string import safe_upper
    from indico.web.flask.util import url_for, url_rule_to_js
    from indico.web.util import url_for_index

    if not 'contextHelp' in objDict:
        objDict['contextHelp'] = contextHelp
    if not 'inlineContextHelp' in objDict:
        objDict['inlineContextHelp'] = inlineContextHelp
    if not 'escape' in objDict:
        objDict['escape'] = escape
    if not 'quoteattr' in objDict:
        objDict['quoteattr'] = quoteattr
    if not 'verbose' in objDict:
        objDict['verbose'] = verbose
    if not 'verbose_dt' in objDict:
        objDict['verbose_dt'] = verbose_dt
    if not 'verbose_t' in objDict:
        objDict['verbose_t'] = verbose_t
    if not 'formatTime' in objDict:
        objDict['formatTime'] = formatTime
    if not 'formatDate' in objDict:
        objDict['formatDate'] = formatDate
    if not 'format_datetime' in objDict:
        objDict['format_datetime'] = format_datetime
    if not 'format_date' in objDict:
        objDict['format_date'] = format_date
    if not 'format_time' in objDict:
        objDict['format_time'] = format_time
    if not 'formatDateTime' in objDict:
        objDict['formatDateTime'] = formatDateTime
    if not 'linkify' in objDict:
        objDict['linkify'] = linkify
    if not 'truncateTitle' in objDict:
        objDict['truncateTitle'] = truncateTitle
    if 'rh' not in objDict and '__rh__' in objDict:
        objDict['rh'] = objDict['__rh__']
    if not 'latex_escape' in objDict:
        objDict['latex_escape'] = latex_escape
    # allow fossilization
    if not 'fossilize' in objDict:
        from indico.legacy.common.fossilize import fossilize
        objDict['fossilize'] = fossilize
    if not 'N_' in objDict:
        objDict['ngettext'] = ngettext
    if not 'format_number' in objDict:
        objDict['format_number'] = format_number
    if 'formatDuration' not in objDict:
        objDict['formatDuration'] = formatDuration
    if 'format_human_timedelta' not in objDict:
        objDict['format_human_timedelta'] = format_human_timedelta
    objDict.setdefault('safe_upper', safe_upper)
    # flask proxies
    objDict['_session'] = session
    objDict['_request'] = request
    objDict['_g'] = g
    objDict['_app'] = app
    # flask utils
    objDict['url_for'] = url_for
    objDict['url_rule_to_js'] = url_rule_to_js
    objDict['render_template'] = render_template
    objDict['template_hook'] = mako_call_template_hook
    objDict['url_for_index'] = url_for_index
    objDict['url_for_login'] = url_for_login
    objDict['url_for_logout'] = url_for_logout
