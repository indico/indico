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

import string

from collections import namedtuple

from indico.core.db import db


class ColorTuple(namedtuple('ColorTuple', ('text', 'background'))):
    """A tuple that contains text and background color.

    Both colors are unified to 'rrggbb' notation (in case 'rgb' is
    passed) and leading ``#`` is stripped.

    When a text/background color is specifie, the other color needs
    to be specified too.  If no color is specified, the ColorTuple
    is falsy.
    """

    def __new__(cls, text, background):
        colors = [text, background]
        for i, color in enumerate(colors):
            if color.startswith('#'):
                color = color[1:]
            if len(color) == 3:
                color = ''.join(x * 2 for x in color)
            colors[i] = color.lower()
        if any(colors):
            if not all(colors):
                raise ValueError('Both colors must be specified')
            if not all(len(x) == 6 for x in colors):
                raise ValueError('Colors must be be `rgb` or `rrggbb`')
            if not all(c in string.hexdigits for color in colors for c in color):
                raise ValueError('Colors must only use hex digits')
        return super(ColorTuple, cls).__new__(cls, *colors)

    def __nonzero__(self):
        return all(self)


class ColorMixin(object):
    """Mixin to store text+background colors in a model.

    For convenience (e.g. for WTForms integrations when selecting both
    colors at the same time from a palette or in a compound field) it
    provides a `colors` property which returns/accepts a `ColorTuple`
    holding text color and background color.
    """

    text_color = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    background_color = db.Column(
        db.String,
        nullable=False,
        default=''
    )

    @property
    def colors(self):
        return ColorTuple(self.text_color, self.background_color)

    @colors.setter
    def colors(self, value):
        if value is None:
            value = '', ''
        self.text_color, self.background_color = value
