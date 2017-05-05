# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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


from functools import wraps

from jinja2.ext import babel_extract

from indico.util.string import encode_if_unicode, trim_inner_whitespace


def ensure_str(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return encode_if_unicode(fn(*args, **kwargs))
    return wrapper


# TODO: Remove this once there's proper support in upstream Jinja
# https://github.com/pallets/jinja/pull/683
def jinja2_babel_extract(fileobj, keywords, comment_tags, options):
    """Custom babel_extract for Jinja.

    Hooks on to Jinja's babel_extract and handles
    whitespace within ``{% trans %}`` tags.
    """
    for lineno, func, message, comments in babel_extract(fileobj, keywords, comment_tags, options):
        if isinstance(message, tuple):
            message = tuple(trim_inner_whitespace(x) if isinstance(x, basestring) else x for x in message)
        else:
            message = trim_inner_whitespace(message)
        yield lineno, func, message, comments
