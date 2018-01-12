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

from itertools import izip_longest
from types import GeneratorType


def values_from_signal(signal_response, single_value=False, skip_none=True, as_list=False,
                       multi_value_types=GeneratorType, return_plugins=False):
    """Combines the results from both single-value and multi-value signals.

    The signal needs to return either a single object (which is not a
    generator) or a generator (usually by returning its values using
    `yield`).

    :param signal_response: The return value of a Signal's `.send()` method
    :param single_value: If each return value should be treated as a single
                         value in all cases (disables the generator check)
    :param skip_none: If None return values should be skipped
    :param as_list: If you want a list instead of a set (only use this if
                    you need non-hashable return values, the order is still
                    not defined!)
    :param multi_value_types: Types which should be considered multi-value.
                              It is used in an `isinstance()` call and if
                              the check succeeds, the value is passed to
                              `list.extend()`
    :param return_plugins: return `(plugin, value)` tuples instead of just
                           the values. `plugin` can be `None` if the signal
                           was not registered in a plugin.
    :return: A set/list containing the results
    """
    values = []
    for func, value in signal_response:
        plugin = getattr(func, 'indico_plugin', None)
        if not single_value and isinstance(value, multi_value_types):
            value_list = list(value)
            if value_list:
                values.extend(izip_longest([plugin], value_list, fillvalue=plugin))
        else:
            values.append((plugin, value))
    if skip_none:
        values = [(p, v) for p, v in values if v is not None]
    if not return_plugins:
        values = [v for p, v in values]
    return values if as_list else set(values)


def named_objects_from_signal(signal_response, name_attr='name', plugin_attr=None):
    """Returns a dict of objects based on an unique attribute on each object.

    The signal needs to return either a single object (which is not a
    generator) or a generator (usually by returning its values using
    `yield`).

    :param signal_response: The return value of a Signal's `.send()` method
    :param name_attr: The attribute containing each object's unique name
    :param plugin_attr: The attribute that will be set to the plugin containing
                        the object (set to `None` for objects in the core)
    :return: dict mapping object names to objects
    """
    objects = values_from_signal(signal_response, return_plugins=True)
    if plugin_attr is not None:
        for plugin, cls in objects:
            setattr(cls, plugin_attr, plugin)
    mapping = {getattr(cls, name_attr): cls for _, cls in objects}
    conflicting = {cls for _, cls in objects} - set(mapping.viewvalues())
    if conflicting:
        names = ', '.join(sorted(getattr(x, name_attr) for x in conflicting))
        raise RuntimeError('Non-unique object names: {}'.format(names))
    return mapping
