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

from flask import render_template
from wtforms.widgets.core import HTMLString


class ConcatWidget(object):
    """Renders a list of fields as a simple string joined by an optional separator."""
    def __init__(self, separator='', prefix_label=True):
        self.separator = separator
        self.prefix_label = prefix_label

    def __call__(self, field, label_args=None, field_args=None):
        label_args = label_args or {}
        field_args = field_args or {}
        html = []
        for subfield in field:
            fmt = u'{0} {1}' if self.prefix_label else u'{1} {0}'
            html.append(fmt.format(subfield.label(**label_args), subfield(**field_args)))
        return HTMLString(self.separator.join(html))


class PrincipalWidget(object):
    """Renders a user/group selector widget"""
    def __call__(self, field):
        return HTMLString(render_template('forms/principal_widget.html', field=field))


class JinjaWidget(object):
    """Renders a field using a custom Jinja template"""
    def __init__(self, template, render_func=render_template):
        self.template = template
        self.render_func = render_func

    def __call__(self, field):
        return HTMLString(self.render_func(self.template, field=field))


class MultipleItemsWidget(object):
    """Renders a `MultipleItemsField` using a nice JavaScript widget"""
    def __call__(self, field):
        return HTMLString(render_template('forms/multiple_items_widget.html', field=field))
