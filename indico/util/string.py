# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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


def unicodeOrNone(string):
    return None if string is None else string.decode('utf-8')


def remove_accents(text, reencode=True):
    if not isinstance(text, unicode):
        text = text.decode('utf-8')
    result = u''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))
    if reencode:
        return result.encode('utf-8')
    else:
        return result


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
