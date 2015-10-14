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

from __future__ import unicode_literals

from flask import render_template
from markupsafe import escape, Markup

from indico.core import signals
from indico.util.signals import named_objects_from_signal


class Placeholder(object):
    """Base class for placeholders.

    Placeholders allow you to insert data in texts provided by users
    while remaining flexible when it comes to HTML escaping and making
    placeholders required or optional.
    """

    #: The name of the placeholder. Must be unique within the context
    #: where the placeholder is used
    name = None
    #: Whether the placeholder must be used at least once.
    required = False
    #: An optional description of the placeholder.
    description = None

    @classmethod
    def render(cls, **kwargs):
        """Converts the placeholder to a string

        When a placeholder contains HTML that should not be escaped,
        the returned value should be returned as a
        :class:`markupsafe.Markup` instance instead of a plain string.

        Subclasses are encouraged to explicitly specify the arguments
        they expect instead of using ``**kwargs``.

        :param kwargs: arguments specific to placeholder's context
        """
        raise NotImplementedError


def _get_placeholders(context, **kwargs):
    return named_objects_from_signal(signals.get_placeholders.send(context, **kwargs))


def replace_placeholders(context, text, **kwargs):
    """Replaces placeholders in a stringt.

    :param context: the context where the placeholders are used
    :param text: the text to replace placeholders in
    :param kwargs: arguments specific to the context
    """
    for name, placeholder in _get_placeholders(context, **kwargs).iteritems():
        p = '{%s}' % name
        if p not in text:
            continue
        text = text.replace(p, escape(placeholder.render(**kwargs)))
    return text


def get_missing_placeholders(context, text, **kwargs):
    """Get the set of missing required placeholders.

    :param context: the context where the placeholders are used
    :param text: the text to check
    :param kwargs: arguments specific to the context
    """
    placeholders = {'{%s}' % name
                    for name, placeholder in _get_placeholders(context, **kwargs).iteritems()
                    if placeholder.required}
    return {p for p in placeholders if p not in text}


def render_placeholder_info(context, **kwargs):
    """Renders the list of available placeholders.

    :param context: the context where the placeholders are used
    :param kwargs: arguments specific to the context
    """
    return Markup(render_template('placeholder_info.html', placeholders=_get_placeholders(context, **kwargs)))
