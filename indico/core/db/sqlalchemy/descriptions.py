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

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.string import MarkdownText, PlainText, RichMarkup
from indico.util.struct.enum import RichIntEnum


class RenderMode(RichIntEnum):
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


class RenderModeMixin(object):
    """Mixin to add a  plaintext/html/markdown-enabled column."""

    possible_render_modes = {RenderMode.plain_text}
    default_render_mode = RenderMode.plain_text

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

    @classmethod
    def _render_getter(cls, attr_name):
        def _getter(self):
            selected_mode = (self.default_render_mode
                             if len(self.possible_render_modes) == 1 or self.render_mode is None
                             else self.render_mode)
            description_wrapper = RENDER_MODE_WRAPPER_MAP[selected_mode]
            return description_wrapper(getattr(self, attr_name))
        return _getter

    @classmethod
    def _render_setter(cls, attr_name):
        def _setter(self, value):
            setattr(self, attr_name, value)
        return _setter

    @classmethod
    def _render_expression(cls, attr_name):
        def _expression(cls):
            return getattr(cls, attr_name)
        return _expression

    @classmethod
    def create_hybrid_property(cls, attr_name):
        """Create a hybrid property that does the rendering of the column.

        :param attr_name: a name for the attribute the unprocessed value can be
                          accessed through (e.g. `_description`).
        """
        return hybrid_property(cls._render_getter(attr_name), fset=cls._render_setter(attr_name),
                               expr=cls._render_expression(attr_name))


class DescriptionMixin(RenderModeMixin):
    marshmallow_aliases = {'_description': 'description'}

    @declared_attr
    def _description(cls):
        return db.Column(
            'description',
            db.Text,
            nullable=False,
            default=''
        )

    description = RenderModeMixin.create_hybrid_property('_description')
