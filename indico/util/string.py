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

"""
String manipulation functions
"""

import re
import unicodedata
from lxml import html, etree

import markdown
import bleach


BLEACH_ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['sup', 'sub', 'small']


def unicodeOrNone(string):
    return None if string is None else string.decode('utf-8')


def safe_upper(string):
    if isinstance(string, unicode):
        return string.upper()
    else:
        return string.decode('utf-8').upper().encode('utf-8')


def safe_slice(string, start, stop=None):
    slice_ = slice(start, stop)
    if isinstance(string, unicode):
        return string[slice_]
    else:
        return string.decode('utf-8')[slice_].encode('utf-8')


def remove_accents(text, reencode=True):
    if not isinstance(text, unicode):
        text = text.decode('utf-8')
    result = u''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))
    if reencode:
        return result.encode('utf-8')
    else:
        return result


def fix_broken_string(text):
    try:
        text = text.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = text.decode('latin1')
        except UnicodeDecodeError:
            text = unicode(text, 'utf-8', errors='replace')
    return text.encode('utf-8')


def fix_broken_obj(obj):
    if isinstance(obj, dict):
        return dict((k, fix_broken_obj(v)) for k, v in obj.iteritems())
    elif isinstance(obj, list):
        return map(fix_broken_obj, obj)
    elif isinstance(obj, str):
        return fix_broken_string(obj)
    elif isinstance(obj, unicode):
        pass  # nothing to do
    else:
        raise ValueError('Invalid object type in fix_broken_obj: {0}'.format(type(obj)))


def remove_non_alpha(text):
    return ''.join(c for c in text if c.isalnum())


def html_line_breaks(text):
    return '<p>' + text.replace('\n\n', '</p><p>').replace('\n', '<br/>') + '</p>'


def truncate(text, max_size, ellipsis='...', encoding='utf-8'):
    """
    Truncate text, taking unicode chars into account
    """
    encode = False

    if isinstance(text, str):
        encode = True
        text = text.decode(encoding)

    if len(text) > max_size:
        text = text[:max_size] + ellipsis

    if encode:
        text = text.encode(encoding)

    return text


def permissive_format(text, params):
    """
    Format text using params from dictionary. Function is resistant to missing parentheses
    """
    for k, v in params.iteritems():
        text = text.replace("{" + k + "}", str(v))
    return text


def remove_extra_spaces(text):
    """
    Removes multiple spaces within text and removes whitespace around the text
    'Text     with    spaces ' becomes 'Text with spaces'
    """
    pattern = re.compile(r"  +")
    return pattern.sub(' ', text).strip()


def remove_tags(text):
    """
    Removes html-like tags from given text. Tag names aren't checked,
    <no-valid-tag></no-valid-tag> pair will be removed.
    """
    pattern = re.compile(r"<(\w|\/)[^<\s\"']*?>")
    return remove_extra_spaces(pattern.sub(' ', text))


def render_markdown(text):
    """ Mako markdown to html filter """
    return markdown.markdown(bleach.clean(text, tags=BLEACH_ALLOWED_TAGS)).encode('utf-8')


def sanitize_for_platypus(text):
    """Sanitize HTML to be used in platypus"""
    tags = ['b', 'br', 'em', 'font', 'i', 'img', 'strike', 'strong', 'sub', 'sup', 'u', 'span', 'div', 'p']
    attrs = {
        'font': ['size', 'face', 'color'],
        'img': ['src', 'width', 'height', 'valign']
    }
    res = bleach.clean(text, tags=tags, attributes=attrs, strip=True)
    # Convert to XHTML
    doc = html.fromstring(res)
    return etree.tostring(doc)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]
