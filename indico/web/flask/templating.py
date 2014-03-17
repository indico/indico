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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import functools

from flask import current_app as app
from jinja2.ext import Extension
from jinja2.lexer import Token


def underline(s, sep='-'):
    return u'{0}\n{1}'.format(s, sep * len(s))


def get_template_module(template_name, **context):
    """Returns the python module of a template.

    This allows you to call e.g. macros inside it from Python code."""
    app.update_template_context(context)
    tpl = app.jinja_env.get_template(template_name)
    return tpl.make_module(context)


class EnsureUnicodeExtension(Extension):
    """Ensures all strings in Jinja are unicode"""

    @classmethod
    def wrap_func(cls, f):
        """Wraps a function to make sure it returns unicode.

        Useful for custom filters."""

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return cls.ensure_unicode(f(*args, **kwargs))

        return wrapper

    @staticmethod
    def ensure_unicode(s):
        """Converts a bytestring to unicode. Must be registered as a filter!"""
        if isinstance(s, str):
            return s.decode('utf-8')
        return s

    def filter_stream(self, stream):
        # The token stream looks like this:
        # ------------------------
        # variable_begin {{
        # name           event
        # dot            .
        # name           getTitle
        # lparen         (
        # rparen         )
        # pipe           |
        # name           safe
        # variable_end   }}
        # ------------------------
        # Intercepting the end of the actual variable is hard but it's rather easy to get the end of
        # the variable tag or the start of the first filter. As filters are optional we need to check
        # both cases. If we inject the code before the first filter we *probably* don't need to run
        # it again later assuming our filters are nice and only return unicode. If that's not the
        # case we can simply remove the `variable_done` checks.
        # Due to the way Jinja works it is pretty much impossible to apply the filter to arguments
        # passed inside a {% trans foo=..., bar=... %} argument list - we have nothing to detect the
        # end of an argument as the 'comma' token might be inside a function call. So in that case#
        # people simply need to unicodify the strings manually. :(

        variable_done = False
        in_trans = False
        for token in stream:
            # Check if we are inside a trans block - we cannot use filters there!
            if token.type == 'block_begin':
                block_name = stream.current.value
                if block_name == 'trans':
                    in_trans = True
                elif block_name == 'endtrans':
                    in_trans = False

            if not in_trans:
                if token.type == 'pipe':
                    # Inject our filter call before the first filter
                    yield Token(token.lineno, 'pipe', '|')
                    yield Token(token.lineno, 'name', 'ensure_unicode')
                    variable_done = True
                elif token.type == 'variable_end':
                    if not variable_done:
                        # Inject our filter call if we haven't injected it right after the variable
                        yield Token(token.lineno, 'pipe', '|')
                        yield Token(token.lineno, 'name', 'ensure_unicode')
                    variable_done = False

            # Original token
            yield token
