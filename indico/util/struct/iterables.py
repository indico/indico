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

from collections import OrderedDict, defaultdict
from functools import wraps
from itertools import chain, combinations, groupby, islice, izip_longest

from flask import render_template_string


def group_list(data, key=None, sort_by=None, sort_reverse=False):
    return {group: sorted(list(items), key=sort_by, reverse=sort_reverse)
            for group, items in groupby(sorted(data, key=key), key=key)}


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


def powerset(iterable):
    """powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"""
    # Taken from https://docs.python.org/2/library/itertools.html#recipes
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def committing_iterator(iterable, n=100):
    """Iterates over *iterable* and commits every *n* items.

    It also issues a commit after the iterator has been exhausted.

    :param iterable: An iterable object
    :param n: Number of items to commit after
    """
    from indico.core.db import db

    for i, data in enumerate(iterable, 1):
        yield data
        if i % n == 0:
            db.session.commit()
    db.session.commit()


def grouper(iterable, n, fillvalue=None, skip_missing=False):
    """Collect data into fixed-length chunks or blocks

    :param iterable: an iterable object
    :param n: number of items per chunk
    :param fillvalue: value to pad the last chunk with if necessary
    :param skip_missing: if the last chunk should be smaller instead
                         of being padded with `fillvalue`
    """
    # Taken from https://docs.python.org/2/library/itertools.html#recipes
    args = [iter(iterable)] * n
    if not skip_missing:
        return izip_longest(fillvalue=fillvalue, *args)
    else:
        # skips the missing items in the last tuple instead of padding it
        fillvalue = object()
        return (tuple(x for x in chunk if x is not fillvalue)
                for chunk in izip_longest(fillvalue=fillvalue, *args))


def materialize_iterable(type_=list):
    """Decorator that materializes an iterable.

    Iterates over the result of the decorated function and stores
    the returned values into a collection.  This makes most sense
    on functions that use `yield` for simplicity but should return
    a collection instead of a generator.

    :param type_: The collection type to return. Can be any callable
                  that accepts an iterable.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            rv = fn(*args, **kwargs)
            return None if rv is None else type_(rv)

        return wrapper

    return decorator


def window(seq, n=2):
    """
    Return a sliding window (of width n) over data from the iterable

        s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result
