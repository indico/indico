# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.string import MarkdownText, PlainText, RichMarkup
from indico.util.struct.enum import TitledIntEnum


class RenderMode(TitledIntEnum):
    """Rendering formats that a description can be written in."""

    __titles__ = [None, 'HTML', 'Markdown', 'Plain Text']
    html = 1
    markdown = 2
    plain_text = 3


RENDER_MODE_WRAPPER_MAP = {
    RenderMode.html: RichMarkup,
    RenderMode.markdown: MarkdownText,
    RenderMode.plain_text: PlainText
}


class DescriptionMixin(object):
    """Mixin to add an html-enabled description column."""

    possible_render_modes = {RenderMode.plain_text}
    default_render_mode = RenderMode.plain_text

    @declared_attr
    def _description(cls):
        return db.Column(
            'description',
            db.Text,
            nullable=False,
            default=''
        )

    @declared_attr
    def render_mode(cls):
        # Only add the column if there's a choice
        # between several alternatives
        if len(cls.possible_render_modes) > 1:
            return db.Column(
                PyIntEnum(RenderMode),
                default=cls.default_render_mode,
                nullable=False
            )
        else:
            return cls.default_render_mode

    @hybrid_property
    def description(self):
        selected_mode = self.default_render_mode if len(self.possible_render_modes) == 1 else self.render_mode
        description_wrapper = RENDER_MODE_WRAPPER_MAP[selected_mode]
        return description_wrapper(self._description)

    @description.setter
    def description(self, value):
        self._description = value

    @description.expression
    def description(cls):
        return cls._description
