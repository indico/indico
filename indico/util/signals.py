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

from types import GeneratorType


def values_from_signal(signal_response, single_value=False, skip_none=True, as_list=False,
                       multi_value_types=GeneratorType):
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
    :return: A set/list containing the results
    """
    values = []
    for _, value in signal_response:
        if not single_value and isinstance(value, multi_value_types):
            values.extend(value)
        else:
            values.append(value)
    if skip_none:
        values = [v for v in values if v is not None]
    return values if as_list else set(values)


def named_objects_from_signal(signal_response, name_attr='name'):
    """Returns a dict of objects based on an unique attribute on each object.

    The signal needs to return either a single object (which is not a
    generator) or a generator (usually by returning its values using
    `yield`).

    :param signal_response: The return value of a Signal's `.send()` method
    :param name_attr: The attribute containing each object's unique name
    :return: dict mapping object names to objects
    """
    objects = values_from_signal(signal_response)
    mapping = {getattr(cls, name_attr): cls for cls in objects}
    conflicting = objects - set(mapping.viewvalues())
    if conflicting:
        names = ', '.join(sorted(getattr(x, name_attr) for x in conflicting))
        raise RuntimeError('Non-unique object names: {}'.format(names))
    return mapping
