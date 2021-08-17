# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""
String manipulation functions
"""


import binascii
import re
import string
import unicodedata
from enum import Enum
from itertools import chain
from operator import attrgetter
from uuid import uuid4

import bleach
import email_validator
import markdown
import translitcodec
from html2text import HTML2Text
from jinja2.filters import do_striptags
from lxml import etree, html
from markupsafe import Markup, escape
from sqlalchemy import ForeignKeyConstraint, inspect


# basic list of tags, used for markdown content
BLEACH_ALLOWED_TAGS = bleach.ALLOWED_TAGS + [
    'sup', 'sub', 'small', 'br', 'p', 'table', 'thead', 'tbody', 'th', 'tr', 'td', 'img', 'hr', 'h1', 'h2', 'h3', 'h4',
    'h5', 'h6', 'pre', 'dl', 'dd', 'dt'
]
BLEACH_ALLOWED_ATTRIBUTES = {**bleach.ALLOWED_ATTRIBUTES, 'img': ['src', 'alt', 'style']}
# extended list of tags, used for HTML content
BLEACH_ALLOWED_TAGS_HTML = BLEACH_ALLOWED_TAGS + [
    'address', 'area', 'bdo', 'big', 'caption', 'center', 'cite', 'col', 'colgroup', 'del', 'dfn', 'dir', 'div',
    'fieldset', 'font', 'ins', 'kbd', 'legend', 'map', 'menu', 'q', 's', 'samp', 'span', 'strike', 'tfoot', 'tt', 'u',
    'var'
]
# yuck, this is ugly, but all these attributes were allowed in legacy...
BLEACH_ALLOWED_ATTRIBUTES_HTML = BLEACH_ALLOWED_ATTRIBUTES | {'*': [
    'align', 'abbr', 'alt', 'border', 'bgcolor', 'class', 'cellpadding', 'cellspacing', 'color', 'char', 'charoff',
    'cite', 'clear', 'colspan', 'compact', 'dir', 'disabled', 'face', 'href', 'height', 'headers', 'hreflang', 'hspace',
    'id', 'ismap', 'lang', 'name', 'noshade', 'nowrap', 'rel', 'rev', 'rowspan', 'rules', 'size', 'scope', 'shape',
    'span', 'src', 'start', 'style', 'summary', 'tabindex', 'target', 'title', 'type', 'valign', 'value', 'vspace',
    'width', 'wrap'
], 'img': [*BLEACH_ALLOWED_ATTRIBUTES['img'], 'usemap'], 'area': ['coords']}
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


LATEX_MATH_PLACEHOLDER = '\uE000'


def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def remove_non_alpha(text):
    return ''.join(c for c in text if c.isalnum())


def str_to_ascii(text):
    return translitcodec.long_encode(text)[0].encode('ascii', 'ignore').decode().strip()


def strict_str(value):
    """Convert a value to unicode or fails if it is None.

    Useful when converting e.g. IDs to path segments.  Usually they
    should not be ``None`` so we do not want to fail silently (and end
    up with a literal ``None`` in the path).
    """
    if value is None:
        raise TypeError('strict_str does not accept `None`')
    return str(value)


def slugify(*args, **kwargs):
    """Join a series of strings into a URL slug.

    - normalizes strings to proper ascii repesentations
    - removes non-alphanumeric characters
    - replaces whitespace with dashes

    :param lower: Whether the slug should be all-lowercase
    :param maxlen: Maximum slug length
    :param fallback: Fallback in case of an empty slug
    """

    lower = kwargs.get('lower', True)
    maxlen = kwargs.get('maxlen')
    fallback = kwargs.get('fallback', '')

    value = '-'.join(str(val) for val in args)
    value = translitcodec.long_encode(value)[0]
    value = re.sub(r'[^\w\s-]', '', value, flags=re.ASCII).strip()

    if lower:
        value = value.lower()
    value = re.sub(r'[-\s]+', '-', value)
    if maxlen:
        value = value[0:maxlen].rstrip('-')

    return value or fallback


def truncate(text, max_size, ellipsis='...'):
    """Truncate text if it's too long."""
    if len(text) > max_size:
        text = text[:max_size] + ellipsis
    return text


def strip_tags(text):
    """Strip HTML tags and replace adjacent whitespace by one space."""
    return do_striptags(text)


def render_markdown(text, escape_latex_math=True, md=None, **kwargs):
    """Mako markdown to HTML filter.

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

        text = re.sub(r'\$[^\$]+\$|\$\$(^\$)\$\$', _math_replace, text)

    if md is None:
        result = bleach.clean(markdown.markdown(text, **kwargs), tags=BLEACH_ALLOWED_TAGS,
                              attributes=BLEACH_ALLOWED_ATTRIBUTES)
    else:
        result = md(text, **kwargs)

    if escape_latex_math:
        return re.sub(LATEX_MATH_PLACEHOLDER, lambda _: math_segments.pop(0), result)
    else:
        return result


def sanitize_for_platypus(text):
    """Sanitize HTML to be used in platypus."""
    from indico.core.config import config
    tags = ['b', 'br', 'em', 'font', 'i', 'img', 'strike', 'strong', 'sub', 'sup', 'u', 'span', 'div', 'p']
    attrs = {
        'font': ['size', 'face', 'color'],
        'img': ['src', 'width', 'height', 'valign']
    }
    res = bleach.clean(text, tags=tags, attributes=attrs, strip=True).strip()
    if not res:
        return ''
    # Convert to XHTML
    doc = html.fromstring(res)
    doc.make_links_absolute(config.BASE_URL, resolve_base_href=False)
    return etree.tostring(doc).decode()


def is_valid_mail(emails_string, multi=True):
    # XXX: This is deprecated, use `validate_email` or `validate_emails` instead!
    # Remove this in 2.2 when the 'multi' mode is not needed anymore (only used in RB)
    # and don't forget to update the paypal plugin as well!
    if not emails_string:
        return False
    return validate_emails(emails_string) if multi else validate_email(emails_string)


def validate_email(email, *, check_dns=True):
    """Validate the given email address.

    This checks both if it looks valid and if it has valid
    MX (or A/AAAA) records.
    """
    try:
        email_validator.validate_email(email, check_deliverability=check_dns)
    except email_validator.EmailNotValidError:
        return False
    else:
        return True


def validate_email_verbose(email):
    """Validate the given email address.

    This checks both if it looks valid and if it has valid
    MX (or A/AAAA) records.

    :return: ``None`` for a valid email address, otherwise ``'invalid'`` or
             ``'undeliverable'`` depending on whether the email address has
             syntax errors or dns validation failed.
    """
    try:
        email_validator.validate_email(email)
    except email_validator.EmailUndeliverableError:
        return 'undeliverable'
    except email_validator.EmailNotValidError:
        return 'invalid'
    else:
        return None


def validate_emails(emails):
    """Validate a space/semicolon/comma-separated list of email addresses."""
    emails = re.split(r'[\s;,]+', emails)
    return all(validate_email(email) for email in emails if email)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


def seems_html(text):
    return re.search(r'<[a-z]+?>', text) is not None


def strip_control_chars(text):
    return re.sub(r'[\x0B-\x1F]', '', text)


def html_color_to_rgb(hexcolor):
    """Convert #RRGGBB to an (R, G, B) tuple."""

    if not hexcolor.startswith('#'):
        raise ValueError(f"Invalid color string '{hexcolor}' (should start with '#')")

    hexcolor = hexcolor[1:]

    if len(hexcolor) not in {3, 6}:
        raise ValueError(f"'#{hexcolor}'' is not in #RRGGBB or #RGB format")

    if len(hexcolor) == 3:
        hexcolor = ''.join(c * 2 for c in hexcolor)

    return tuple(float(int(hexcolor[i:i + 2], 16)) / 255 for i in range(0, 6, 2))


def strip_whitespace(s):
    """Remove trailing/leading whitespace if a string was passed.

    This utility is useful in cases where you might get None or
    non-string values such as WTForms filters.
    """
    if isinstance(s, str):
        s = s.strip()
    return s


def make_unique_token(is_unique):
    """Create a unique UUID4-based token.

    :param is_unique: a callable invoked with the token which should
                      return a boolean indicating if the token is actually
    """
    token = str(uuid4())
    while not is_unique(token):
        token = str(uuid4())
    return token


def is_legacy_id(id_):
    """Check if an ID is a broken legacy ID.

    These IDs are not compatible with new code since they are not
    numeric or have a leading zero, resulting in different objects
    with the same numeric id.
    """
    return not isinstance(id_, int) and (not id_.isdigit() or str(int(id_)) != id_)


def text_to_repr(text, html=False, max_length=50):
    """Convert text to a suitable string for a repr.

    :param text: A string which might contain html and/or linebreaks
    :param html: If True, HTML tags are stripped.
    :param max_length: The maximum length before the string is
                       truncated.  Use ``None`` to disable.
    :return: A string that contains no linebreaks or HTML tags.
    """
    if text is None:
        text = ''
    if html:
        text = bleach.clean(text, tags=[], strip=True)
    text = re.sub(r'\s+', ' ', text)
    if max_length is not None and len(text) > max_length:
        text = text[:max_length] + '...'
    return text.strip()


def alpha_enum(value):
    """Convert integer to ordinal letter code (a, b, c, ... z, aa, bb, ...)."""
    max_len = len(string.ascii_lowercase)
    return str(string.ascii_lowercase[value % max_len] * (value // max_len + 1))


def format_repr(obj, *args, **kwargs):
    """Create a pretty repr string from object attributes.

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
    formatted_args = [str(_format_value(getattr(obj, arg)))
                      if arg not in fkeys
                      else f'{arg}={_format_value(getattr(obj, arg))}'
                      for arg in args]
    for name, default_value in sorted(kwargs.items()):
        value = getattr(obj, name)
        if value != default_value:
            formatted_args.append(f'{name}={_format_value(value)}')
    if text_arg is not None:
        return '<{}({}): "{}">'.format(obj_name, ', '.join(formatted_args), text_arg)
    elif raw_text_arg is not None:
        return '<{}({}): {}>'.format(obj_name, ', '.join(formatted_args), raw_text_arg)
    elif repr_arg is not None:
        return '<{}({}): {!r}>'.format(obj_name, ', '.join(formatted_args), repr_arg)
    else:
        return '<{}({})>'.format(obj_name, ', '.join(formatted_args))


def snakify(name):
    """Convert a camelCased name to snake_case."""
    # from http://stackoverflow.com/a/1176023/298479
    name = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def camelize(name):
    """Convert a snake_cased name to camelCase."""
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
    return {convert_func(k): _convert_keys(v, convert_func) for k, v in value.items()}


def camelize_keys(dict_):
    """Convert the keys of a dict to camelCase."""
    return _convert_keys(dict_, camelize)


def snakify_keys(dict_):
    """Convert the keys of a dict to snake_case."""
    return _convert_keys(dict_, snakify)


def crc32(data):
    """Calculate a CRC32 checksum.

    When a str is passed, it is encoded as UTF-8.
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return binascii.crc32(data) & 0xffffffff


def normalize_phone_number(value):
    """Normalize phone number so it doesn't contain invalid characters.

    This removes all characters besides a leading +, digits and x as
    described here: http://stackoverflow.com/a/123681/298479
    """
    return re.sub(r'((?!^)\+)|[^0-9x+]', '', value.strip())


def format_full_name(first_name, last_name, title=None, last_name_first=True, last_name_upper=True,
                     abbrev_first_name=True, show_title=False):
    """Return the user's name in the specified notation.

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
        first_name = f'{first_name[0].upper()}.' if abbrev_first_name else first_name
        full_name = f'{last_name}, {first_name}' if last_name_first else f'{first_name} {last_name}'
    return full_name if not show_title or not title else f'{title} {full_name}'


def sanitize_email(email, require_valid=False):
    if '<' in email:
        m = re.search(r'<([^>]+)>', email)
        email = email if m is None else m.group(1)
    if not require_valid or validate_email(email):
        return email
    else:
        return None


def sanitize_html(string):
    return bleach.clean(string, tags=BLEACH_ALLOWED_TAGS_HTML, attributes=BLEACH_ALLOWED_ATTRIBUTES_HTML,
                        styles=BLEACH_ALLOWED_STYLES_HTML)


def html_to_plaintext(string):
    return html.html5parser.fromstring(string).xpath('string()')


class RichMarkup(Markup):
    """Unicode/Markup subclass that detects preformatted text.

    Note that HTML in this string will NOT be escaped when displaying
    it in a jinja template.
    """

    __slots__ = ('_preformatted',)

    def __new__(cls, content='', preformatted=None):
        obj = Markup.__new__(cls, content)
        if preformatted is None:
            tmp = content.lower()
            obj._preformatted = not any(tag in tmp for tag in ('<p>', '<p ', '<br', '<li>'))
        else:
            obj._preformatted = preformatted
        return obj

    def __html__(self):
        # XXX: ensure we have no harmful HTML - there are certain malicious values that
        # are not caught by the legacy sanitizer that runs at submission time
        string = RichMarkup(sanitize_html(str(self)), preformatted=self._preformatted)
        if string._preformatted:
            return f'<div class="preformatted">{string}</div>'
        else:
            return string

    def __getstate__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot)}

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)


class MarkdownText(Markup):
    """Unicode/Markup class that renders markdown."""

    def __html__(self):
        return render_markdown(str(self), extensions=('nl2br', 'tables'))


class PlainText(Markup):
    """Unicode/Markup class that renders plain text."""

    def __html__(self):
        return f'<div class="preformatted">{escape(str(self))}</div>'


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
        field.warning = _('This text has been automatically converted from HTML to Markdown. '
                          "Please double-check that it's properly displayed.")
        ht = HTML2Text(bodywidth=0)
        desc = get_value(obj)
        if RichMarkup(desc)._preformatted:
            desc = desc.replace('\n', '<br>\n')
        field.data = ht.handle(desc)
