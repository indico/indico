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

from __future__ import absolute_import

import binascii
import functools
import re
import string
import unicodedata
from uuid import uuid4

import bleach
import markdown
import translitcodec  # this is NOT unused. it needs to be imported to register the codec.
from enum import Enum
from lxml import html, etree
from speaklater import _LazyString


BLEACH_ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['sup', 'sub', 'small']
LATEX_MATH_PLACEHOLDER = u"\uE000"


def encode_if_unicode(s):
    if isinstance(s, _LazyString) and isinstance(s.value, unicode):
        s = unicode(s)
    return s.encode('utf-8') if isinstance(s, unicode) else s


def unicodeOrNone(s):
    return None if s is None else s.decode('utf-8')


def safe_upper(text):
    if isinstance(text, unicode):
        return text.upper()
    else:
        return text.decode('utf-8').upper().encode('utf-8')


def safe_slice(text, start, stop=None):
    slice_ = slice(start, stop)
    if isinstance(text, unicode):
        return text[slice_]
    else:
        return text.decode('utf-8')[slice_].encode('utf-8')


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
    else:
        text = text.encode('translit/long')
    return text.encode('ascii', 'ignore')


def slugify(value, lower=True):
    """Converts a string to a simpler version useful for URL slugs.

    - normalizes unicode to proper ascii repesentations
    - removes non-alphanumeric characters
    - replaces whitespace with dashes

    :param lower: Whether the slug should be all-lowercase
    """
    value = to_unicode(value).encode('translit/long')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    if lower:
        value = value.lower()
    return re.sub('[-\s]+', '-', value)


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


def render_markdown(text, escape_latex_math=True, md=None, **kwargs):
    """ Mako markdown to HTML filter
        :param text: Markdown source to convert to HTML
        :param escape_latex_math: Whether math expression should
                                  be left untouched
        :param md: An alternative markdown processor (can be used
                   to generate e.g. a different format)
        :param kwargs: Extra arguments to pass on to the markdown
                       processor
    """
    if escape_latex_math:
        math_segments = []

        def _math_replace(m):
            math_segments.append(m.group(0))
            return LATEX_MATH_PLACEHOLDER

        text = re.sub(r'\$[^\$]+\$|\$\$(^\$)\$\$', _math_replace, to_unicode(text))

    if md is None:
        result = markdown.markdown(bleach.clean(text, tags=BLEACH_ALLOWED_TAGS), **kwargs)
    else:
        result = md(text, **kwargs)

    if escape_latex_math:
        return re.sub(LATEX_MATH_PLACEHOLDER, lambda _: math_segments.pop(0), result)
    else:
        return result


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


def seems_html(text):
    return re.search(r'<[a-z]+?>', text) is not None


def strip_control_chars(text):
    return re.sub(r'[\x0B-\x1F]', '', text)


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


def encode_utf8(f):
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        rv = f(*args, **kwargs)
        if not rv:
            return ''
        return rv.encode('utf-8') if isinstance(rv, unicode) else str(rv)

    return _wrapper


def is_legacy_id(id_):
    """Checks if an ID is a broken legacy ID.

    These IDs are not compatible with new code since they are not
    numeric or have a leading zero, resulting in different objects
    with the same numeric id.
    """
    return not isinstance(id_, (int, long)) and (not id_.isdigit() or str(int(id_)) != id_)


def text_to_repr(text, html=False, max_length=50):
    """Converts text to a suitable string for a repr

    :param text: A string which might contain html and/or linebreaks
    :param html: If True, HTML tags are stripped.
    :param max_length: The maximum length before the string is
                       truncated.  Use ``None`` to disable.
    :return: A string that contains no linebreaks or HTML tags.
    """
    if html:
        text = bleach.clean(text, tags=[], strip=True)
    text = re.sub(ur'\s+', u' ', text)
    if max_length is not None and len(text) > max_length:
        text = text[:max_length] + u'...'
    return text.strip()


def alpha_enum(value):
    """Convert integer to ordinal letter code (a, b, c, ... z, aa, bb, ...)."""
    max_len = len(string.ascii_lowercase)
    return unicode(string.ascii_lowercase[value % max_len] * (value / max_len + 1))


def format_repr(obj, *args, **kwargs):
    """Creates a pretty repr string from object attributes

    :param obj: The object to show the repr for.
    :param args: The names of arguments to include in the repr.
                 The arguments are shown in order using their unicode
                 representation.
    :param kwargs: Each kwarg is included as a ``name=value`` string
                   if it doesn't match the provided value.  This is
                   mainly intended for boolean attributes such as
                   ``is_deleted`` where you don't want them to
                   clutter the repr unless they are set.
    :param _text: When the keyword argument `_text` is provided and
                  not ``None``, it will include its value as extra
                  text in the repr inside quotes.  This is useful
                  for objects which have one longer title or text
                  that doesn't look well in the unquoted
                  comma-separated argument list.
    """
    def _format_value(value):
        if isinstance(value, Enum):
            return value.name
        else:
            return value

    text_arg = kwargs.pop('_text', None)
    obj_name = type(obj).__name__
    formatted_args = [unicode(_format_value(getattr(obj, arg))) for arg in args]
    for name, default_value in sorted(kwargs.items()):
        value = getattr(obj, name)
        if value != default_value:
            formatted_args.append(u'{}={}'.format(name, _format_value(value)))
    if text_arg is None:
        return u'<{}({})>'.format(obj_name, u', '.join(formatted_args))
    else:
        return u'<{}({}): "{}">'.format(obj_name, u', '.join(formatted_args), text_arg)


def snakify(name):
    """Converts a camelCased name to snake_case"""
    # from http://stackoverflow.com/a/1176023/298479
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def camelize(name):
    """Converts a snake_cased name to camelCase."""
    parts = name.split('_')
    underscore = ''
    if name.startswith('_'):
        underscore = '_'
        parts = parts[1:]
    return underscore + parts[0] + ''.join(x.title() for x in parts[1:])


def _convert_keys(value, convert_func):
    if isinstance(value, (list, tuple)):
        return type(value)(_convert_keys(x, convert_func) for x in value)
    elif not isinstance(value, dict):
        return value
    return {convert_func(k): _convert_keys(v, convert_func) for k, v in value.iteritems()}


def camelize_keys(dict_):
    """Convert the keys of a dict to camelCase"""
    return _convert_keys(dict_, camelize)


def snakify_keys(dict_):
    """Convert the keys of a dict to snake_case"""
    return _convert_keys(dict_, snakify)


def crc32(data):
    """Calculates a CRC32 checksum.

    When a unicode object is passed, it is encoded as UTF-8.
    """
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    return binascii.crc32(data) & 0xffffffff


def normalize_phone_number(value):
    """Normalize phone number so it doesn't contain invalid characters

    This removes all characters besides a leading +, digits and x as
    described here: http://stackoverflow.com/a/123681/298479
    """
    return re.sub(r'((?!^)\+)|[^0-9x+]', '', value.strip())


def format_full_name(first_name, last_name, title=None, last_name_first=True, last_name_upper=True,
                     abbrev_first_name=True, show_title=False):
    """Returns the user's name in the specified notation.

    Note: Do not use positional arguments (except for the names/title)
    when calling this method.  Always use keyword arguments!

    :param first_name: The first name
    :param last_name: The last name
    :param title: The title (may be empty/None)
    :param last_name_first: if "lastname, firstname" instead of
                            "firstname lastname" should be used
    :param last_name_upper: if the last name should be all-uppercase
    :param abbrev_first_name: if the first name should be abbreviated to
                              use only the first character
    :param show_title: if the title should be included
    """
    if last_name_upper:
        last_name = last_name.upper()
    first_name = u'{}.'.format(first_name[0].upper()) if abbrev_first_name else first_name
    full_name = u'{}, {}'.format(last_name, first_name) if last_name_first else u'{} {}'.format(first_name, last_name)
    return full_name if not show_title or not title else u'{} {}'.format(title, full_name)


def sanitize_email(email):
    if '<' not in email:
        return email
    m = re.search(r'<([^>]+)>', email)
    return email if m is None else m.group(1)
