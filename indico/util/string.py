# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

"""
String manipulation functions
"""

import functools
import re
import unicodedata
from uuid import uuid4

import markdown
import bleach
from lxml import html, etree
from speaklater import _LazyString

try:
    import translitcodec
except ImportError:
    translitcodec = None


BLEACH_ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['sup', 'sub', 'small']


def encode_if_unicode(s):
    if isinstance(s, _LazyString) and isinstance(s.value, unicode):
        s = unicode(s)
    return s.encode('utf-8') if isinstance(s, unicode) else s


def unicodeOrNone(s):
    return None if s is None else s.decode('utf-8')


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


def fix_broken_string(text, as_unicode=False):
    try:
        text = text.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = text.decode('latin1')
        except UnicodeDecodeError:
            text = unicode(text, 'utf-8', errors='replace')
    return text if as_unicode else text.encode('utf-8')


def to_unicode(text):
    """Converts a string to unicode if it isn't already unicode."""
    if isinstance(text, unicode):
        return text
    elif not isinstance(text, str):
        return unicode(text)
    return fix_broken_string(text, as_unicode=True)


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


def unicode_to_ascii(text):
    if not isinstance(text, unicode):
        return text
    elif translitcodec:
        text = text.encode('translit/long')
    else:
        text = unicodedata.normalize('NFKD', text)
    return text.encode('ascii', 'ignore')


def unicode_struct_to_utf8(obj):
    if isinstance(obj, unicode):
        return obj.encode('utf-8', 'replace')
    elif isinstance(obj, list):
        return map(unicode_struct_to_utf8, obj)
    elif isinstance(obj, dict):
        return {unicode_struct_to_utf8(k): unicode_struct_to_utf8(v) for k, v in obj.iteritems()}
    return obj


def return_ascii(f):
    """Decorator to normalize all unicode characters.

    This is useful for __repr__ methods which **MUST** return a plain string to
    avoid encoding to utf8 or ascii all the time."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return unicode_to_ascii(f(*args, **kwargs))
    return wrapper


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


def render_markdown(text, **kwargs):
    """ Mako markdown to html filter """
    return markdown.markdown(bleach.clean(text, tags=BLEACH_ALLOWED_TAGS), **kwargs).encode('utf-8')


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


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


def seems_html(string):
    return re.search(r'<[a-z]+?>', string) is not None


def strip_control_chars(string):
    return re.sub(r'[\x0B-\x1F]', '', string)


def html_color_to_rgb(hexcolor):
    """
    convert #RRGGBB to an (R, G, B) tuple
    """

    if not hexcolor.startswith('#'):
        raise ValueError("Invalid color string '{}' (should start with '#')".format(hexcolor))

    hexcolor = hexcolor[1:]

    if len(hexcolor) not in {3, 6}:
        raise ValueError("'#{}'' is not in #RRGGBB or #RGB format".format(hexcolor))

    if len(hexcolor) == 3:
        hexcolor = ''.join(c * 2 for c in hexcolor)

    return tuple(float(int(hexcolor[i:i + 2], 16)) / 255 for i in range(0, 6, 2))


def strip_whitespace(s):
    """Removes trailing/leading whitespace if a string was passed.

    This utility is useful in cases where you might get None or
    non-string values such as WTForms filters.
    """
    if isinstance(s, basestring):
        s = s.strip()
    return s


def make_unique_token(is_unique):
    """Create a unique UUID4-based token

    :param is_unique: a callable invoked with the token which should
                      return a boolean indicating if the token is actually
    """
    token = unicode(uuid4())
    while not is_unique(token):
        token = unicode(uuid4())
    return token
