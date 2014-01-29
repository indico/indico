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


def encode_if_unicode(s):
    return s.encode('utf-8') if isinstance(s, unicode) else s


def unicodeOrNone(s):
    return None if s is None else s.decode('utf-8')


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


# TODO: reference implementation from MaKaC
# but, it's not totally correct according to RFC, see test cases
# However, this regex is pretty good in term of practicality
# but it may be updated to cover all cases
VALID_EMAIL_REGEX = re.compile(r"""[-a-zA-Z0-9!#$%&'*+/=?\^_`{|}~]+
                                   (?:.[-a-zA-Z0-9!#$%&'*+/=?^_`{|}~]+)*
                                   @
                                   (?:[a-zA-Z0-9](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?.)+
                                   [a-zA-Z0-9](?:[-a-zA-Z0-9]*[a-zA-Z0-9])?""", re.X)


def is_valid_mail(emails_string, multi=True):
    """
    Checks the validity of an email address or a series of email addresses

    - emails_string: a string representing a single email address or several
    email addresses separated by separators
    - multi: flag if multiple email addresses are allowed

    Returns True if emails are valid.
    """

    emails = re.split(r'[\s;,]+', emails_string)

    if not multi and len(emails) > 1:
        return False

    return all(re.match(VALID_EMAIL_REGEX, email) for email in emails if email)
