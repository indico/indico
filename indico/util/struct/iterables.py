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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from collections import defaultdict, OrderedDict
from itertools import groupby

from flask import render_template_string


def group_list(data, key=None, sort_by=None):
    return {group: sorted(list(items), key=sort_by) for group, items in groupby(sorted(data, key=key), key=key)}


def group_nested(objects, accessor=lambda x: x, _tree=None, _child_of=None):
    """Groups the equipment list so children follow their their parents."""
    if _tree is None:
        _tree = defaultdict(list)
        for obj in objects:
            _tree[accessor(obj).parent_id].append(obj)

    for obj in _tree[_child_of]:
        yield obj
        for child in group_nested(objects, accessor, _tree, accessor(obj).id):
            yield child


NESTED_TEMPLATE = """
{%- for item in items.itervalues() recursive -%}
    {{- item.name -}}
    {%- if item.children %}
        (<span class="nested-{{ loop.depth }}">{{ loop(item.children.itervalues()) }}</span>)
    {%- endif -%}
    {%- if not loop.last %}, {% endif -%}
{%- endfor -%}
""".strip()


def render_nested(objects, template=NESTED_TEMPLATE):
    """Renders a nested structure such as room equipment to a nice HTML string.

    :param objects: An iterable containing the objects

    All objects in `objects` must have `name`, `id` and `parent_id` attributes.
    """
    # We can't use `obj.children` since that triggers SQL queries
    tree = OrderedDict()
    children = {}
    for obj in group_nested(objects):
        if obj.parent_id is None:
            tree[obj.id] = {'name': obj.name, 'children': OrderedDict()}
            children[obj.id] = tree[obj.id]['children']
        else:
            children[obj.parent_id][obj.id] = {'name': obj.name, 'children': OrderedDict()}
            children[obj.id] = children[obj.parent_id][obj.id]['children']
    return render_template_string(template, items=tree)
