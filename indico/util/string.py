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

"""
String manipulation functions
"""

from __future__ import absolute_import

import binascii
import functools
import os
import re
import string
import unicodedata
from enum import Enum
from itertools import chain
from operator import attrgetter
from uuid import uuid4

import bleach
import markdown
import translitcodec  # this is NOT unused. it needs to be imported to register the codec.
from html2text import HTML2Text
from jinja2.filters import do_striptags
from lxml import etree, html
from markupsafe import Markup, escape
from speaklater import _LazyString, is_lazy_string
from sqlalchemy import ForeignKeyConstraint, inspect


# basic list of tags, used for markdown content
BLEACH_ALLOWED_TAGS = bleach.ALLOWED_TAGS + [
    'sup', 'sub', 'small', 'br', 'p', 'table', 'thead', 'tbody', 'th', 'tr', 'td', 'img', 'hr', 'h1', 'h2', 'h3', 'h4',
    'h5', 'h6', 'pre'
]
BLEACH_ALLOWED_ATTRIBUTES = dict(bleach.ALLOWED_ATTRIBUTES, img=['src', 'alt', 'style'])
# extended list of tags, used for HTML content
BLEACH_ALLOWED_TAGS_HTML = BLEACH_ALLOWED_TAGS + [
    'address', 'area', 'bdo', 'big', 'caption', 'center', 'cite', 'col', 'colgroup', 'dd', 'del', 'dfn', 'dir', 'div',
    'dl', 'dt', 'fieldset', 'font', 'ins', 'kbd', 'legend', 'map', 'menu', 'q', 's', 'samp', 'span', 'strike', 'tfoot',
    'tt', 'u', 'var'
]
# yuck, this is ugly, but all these attributes were allowed in legacy...
BLEACH_ALLOWED_ATTRIBUTES_HTML = dict(BLEACH_ALLOWED_ATTRIBUTES, **{'*': [
    'align', 'abbr', 'alt', 'border', 'bgcolor', 'class', 'cellpadding', 'cellspacing', 'color', 'char', 'charoff',
    'cite', 'clear', 'colspan', 'compact', 'dir', 'disabled', 'face', 'href', 'height', 'headers', 'hreflang', 'hspace',
    'id', 'ismap', 'lang', 'name', 'noshade', 'nowrap', 'rel', 'rev', 'rowspan', 'rules', 'size', 'scope', 'shape',
    'span', 'src', 'start', 'style', 'summary', 'tabindex', 'target', 'title', 'type', 'valign', 'value', 'vspace',
    'width', 'wrap'
]})
BLEACH_ALLOWED_STYLES_HTML = [
    'background-color', 'border-top-color', 'border-top-style', 'border-top-width', 'border-top', 'border-right-color',
    'border-right-style', 'border-right-width', 'border-right', 'border-bottom-color', 'border-bottom-style',
    'border-bottom-width', 'border-bottom', 'border-left-color', 'border-left-style', 'border-left-width',
    'border-left', 'border-color', 'border-style', 'border-width', 'border', 'bottom', 'border-collapse',
    'border-spacing', 'color', 'clear', 'clip', 'caption-side', 'display', 'direction', 'empty-cells', 'float',
    'font-size', 'font-family', 'font-style', 'font', 'font-variant', 'font-weight', 'font-size-adjust', 'font-stretch',
    'height', 'left', 'list-style-type', 'list-style-position', 'line-height', 'letter-spacing', 'marker-offset',
    'margin', 'margin-left', 'margin-right', 'margin-top', 'margin-bottom', 'max-height', 'min-height', 'max-width',
    'min-width', 'marks', 'overflow', 'outline-color', 'outline-style', 'outline-width', 'outline', 'orphans',
    'position', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left', 'padding', 'page', 'page-break-after',
    'page-break-before', 'page-break-inside', 'quotes', 'right', 'size', 'text-align', 'top', 'table-layout',
    'text-decoration', 'text-indent', 'text-shadow', 'text-transform', 'unicode-bidi', 'visibility', 'vertical-align',
    'width', 'widows', 'white-space', 'word-spacing', 'word-wrap', 'z-index'
]


LATEX_MATH_PLACEHOLDER = u"\uE000"


def encode_if_unicode(s):
    if isinstance(s, _LazyString) and isinstance(s.value, unicode):
        s = unicode(s)
    return s.encode('utf-8') if isinstance(s, unicode) else s


def safe_upper(text):
    if isinstance(text, unicode):
        return text.upper()
    else:
        return text.decode('utf-8').upper().encode('utf-8')


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
    return fix_broken_string(text, as_unicode=True) if isinstance(text, str) else unicode(text)


def remove_non_alpha(text):
    return ''.join(c for c in text if c.isalnum())


def unicode_to_ascii(text):
    if not isinstance(text, unicode):
        text = to_unicode(text)
    text = text.encode('translit/long')
    return text.encode('ascii', 'ignore')


def strict_unicode(value):
    """Convert a value to unicode or fails if it is None.

    Useful when converting e.g. IDs to path segments.  Usually they
    should not be ``None`` so we do not want to fail silently (and end
    up with a literal ``None`` in the path).
    """
    if value is None:
        raise TypeError('strict_unicode does not accept `None`')
    return unicode(value)


def slugify(*args, **kwargs):
    """Joins a series of strings into a URL slug.

    - normalizes unicode to proper ascii repesentations
    - removes non-alphanumeric characters
    - replaces whitespace with dashes

    :param lower: Whether the slug should be all-lowercase
    :param maxlen: Maximum slug length
    """

    lower = kwargs.get('lower', True)
    maxlen = kwargs.get('maxlen')

    value = u'-'.join(to_unicode(val) for val in args)
    value = value.encode('translit/long')
    value = re.sub(ur'[^\w\s-]', u'', value).strip()

    if lower:
        value = value.lower()
    value = re.sub(ur'[-\s]+', u'-', value)
    if maxlen:
        value = value[0:maxlen].rstrip(u'-')

    return value


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


def strip_tags(text):
    """Strip HTML tags and replace adjacent whitespace by one space."""
    encode = False
    if isinstance(text, str):
        encode = True
        text = text.decode('utf-8')
    text = do_striptags(text)
    return text.encode('utf-8') if encode else text


def render_markdown(text, escape_latex_math=True, md=None, **kwargs):
    """ Mako markdown to HTML filter
        :param text: Markdown source to convert to HTML
        :param escape_latex_math: Whether math expression should be left untouched or a function that will be called
                                  to replace math-mode segments.
        :param md: An alternative markdown processor (can be used
                   to generate e.g. a different format)
        :param kwargs: Extra arguments to pass on to the markdown
                       processor
    """
    if escape_latex_math:
        math_segments = []

        def _math_replace(m):
            segment = m.group(0)
            if callable(escape_latex_math):
                segment = escape_latex_math(segment)
            math_segments.append(segment)
            return LATEX_MATH_PLACEHOLDER

        text = re.sub(r'\$[^\$]+\$|\$\$(^\$)\$\$', _math_replace, to_unicode(text))

    if md is None:
        result = bleach.clean(markdown.markdown(text, **kwargs), tags=BLEACH_ALLOWED_TAGS,
                              attributes=BLEACH_ALLOWED_ATTRIBUTES)
    else:
        result = md(text, **kwargs)

    if escape_latex_math:
        return re.sub(LATEX_MATH_PLACEHOLDER, lambda _: math_segments.pop(0), result)
    else:
        return result


def render_markdown_utf8(text):
    """UTF-8 version for Mako usage (will be deprecated)"""
    return render_markdown(text).encode('utf-8')


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


# TODO: reference implementation from indico.legacy
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

    if not emails_string:
        return False
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
        if is_lazy_string(rv):
            rv = rv.value
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
    if text is None:
        text = u''
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
    :param _rawtext: Like `_text` but without surrounding quotes.
    :param _repr: Similar as `_text`, but uses the `repr()` of the
                  passed object instead of quoting it.  Cannot be
                  used together with `_text`.
    """
    def _format_value(value):
        if isinstance(value, Enum):
            return value.name
        else:
            return value

    text_arg = kwargs.pop('_text', None)
    raw_text_arg = kwargs.pop('_rawtext', None)
    repr_arg = kwargs.pop('_repr', None)
    cls = type(obj)
    obj_name = cls.__name__
    fkeys = set(chain.from_iterable(c.column_keys
                                    for t in inspect(cls).tables
                                    for c in t.constraints
                                    if isinstance(c, ForeignKeyConstraint))) if hasattr(cls, '__table__') else set()
    formatted_args = [unicode(_format_value(getattr(obj, arg)))
                      if arg not in fkeys
                      else u'{}={}'.format(arg, _format_value(getattr(obj, arg)))
                      for arg in args]
    for name, default_value in sorted(kwargs.items()):
        value = getattr(obj, name)
        if value != default_value:
            formatted_args.append(u'{}={}'.format(name, _format_value(value)))
    if text_arg is not None:
        return u'<{}({}): "{}">'.format(obj_name, u', '.join(formatted_args), text_arg)
    elif raw_text_arg is not None:
        return u'<{}({}): {}>'.format(obj_name, u', '.join(formatted_args), raw_text_arg)
    elif repr_arg is not None:
        return u'<{}({}): {!r}>'.format(obj_name, u', '.join(formatted_args), repr_arg)
    else:
        return u'<{}({})>'.format(obj_name, u', '.join(formatted_args))


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

    :param first_name: The first name (may be empty)
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
    if not first_name:
        full_name = last_name
    else:
        first_name = u'{}.'.format(first_name[0].upper()) if abbrev_first_name else first_name
        full_name = u'{}, {}'.format(last_name, first_name) if last_name_first else u'{} {}'.format(first_name,
                                                                                                    last_name)
    return full_name if not show_title or not title else u'{} {}'.format(title, full_name)


def sanitize_email(email, require_valid=False):
    if '<' in email:
        m = re.search(r'<([^>]+)>', email)
        email = email if m is None else m.group(1)
    if not require_valid or is_valid_mail(email, False):
        return email
    else:
        return None


def sanitize_html(string):
    return bleach.clean(string, tags=BLEACH_ALLOWED_TAGS_HTML, attributes=BLEACH_ALLOWED_ATTRIBUTES_HTML,
                        styles=BLEACH_ALLOWED_STYLES_HTML)


def trim_inner_whitespace(string, _ws_re=re.compile(r'\s*\n\s*')):
    return _ws_re.sub(' ', string.strip())


def inject_unicode_debug(s, level=1):
    """
    Wrap a string in invisible unicode characters to trigger a unicode
    error when erroneously mixing unicode and bytestrings.  If unicode
    debug mode is not enabled, this function returns its argument
    without touching it.

    :param s: a unicode string
    :param level: the minimum unicode debug level needed to inject
                  the spaces.  the more likely it is to break things
                  the higher it should be.
    """

    # Enabling unicode debugging injects an invisible zero-width space at the
    # beginning and end of every translated string.  This will cause errors in case
    # of implicit conversions from bytes to unicode or vice versa instead of
    # silently succeeding for english (ascii) strings and then failing in languages
    # where the same string is not plain ascii.  This setting should be enabled only
    # during development and never in production.
    # Level 1 will inject it only in translated strings and is usually safe while
    # level 2 will inject it in formatted date/time values too which may result in
    # strange/broken behavior in certain form fields.

    try:
        unicode_debug_level = int(os.environ.get('INDICO_UNICODE_DEBUG', '0'))
    except ValueError:
        unicode_debug_level = 0

    if unicode_debug_level < level:
        return s
    else:
        return u'\N{ZERO WIDTH SPACE}' + s + u'\N{ZERO WIDTH SPACE}'


class RichMarkup(Markup):
    """unicode/Markup subclass that detects preformatted text

    Note that HTML in this string will NOT be escaped when displaying
    it in a jinja template.
    """

    __slots__ = ('_preformatted',)

    def __new__(cls, content=u'', preformatted=None):
        obj = Markup.__new__(cls, content)
        if preformatted is None:
            tmp = content.lower()
            obj._preformatted = not any(tag in tmp for tag in (u'<p>', u'<p ', u'<br', u'<li>'))
        else:
            obj._preformatted = preformatted
        return obj

    def __html__(self):
        # XXX: ensure we have no harmful HTML - there are certain malicious values that
        # are not caught by the legacy sanitizer that runs at submission time
        string = RichMarkup(sanitize_html(unicode(self)), preformatted=self._preformatted)
        if string._preformatted:
            return u'<div class="preformatted">{}</div>'.format(string)
        else:
            return string

    def __getstate__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot)}

    def __setstate__(self, state):
        for slot, value in state.iteritems():
            setattr(self, slot, value)


class MarkdownText(Markup):
    """unicode/Markup class that renders markdown."""

    def __html__(self):
        return render_markdown(unicode(self), extensions=('nl2br', 'tables'))


class PlainText(Markup):
    """unicode/Markup class that renders plain text."""

    def __html__(self):
        return u'<div class="preformatted">{}</div>'.format(escape(unicode(self)))


def handle_legacy_description(field, obj, get_render_mode=attrgetter('render_mode'),
                              get_value=attrgetter('_description')):
    """Check if the object in question is using an HTML description and convert it.

       The description will be automatically converted to Markdown and a warning will
       be shown next to the field.

       :param field: the WTForms field to be checked
       :param obj: the object whose render mode/description will be checked
    """
    from indico.core.db.sqlalchemy.descriptions import RenderMode
    from indico.util.i18n import _
    if get_render_mode(obj) == RenderMode.html:
        field.warning = _(u"This text has been automatically converted from HTML to Markdown. "
                          u"Please double-check that it's properly displayed.")
        ht = HTML2Text(bodywidth=0)
        desc = get_value(obj)
        if RichMarkup(desc)._preformatted:
            desc = desc.replace(u'\n', u'<br>\n')
        field.data = ht.handle(desc)
