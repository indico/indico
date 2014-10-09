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

from types import GeneratorType


def values_from_signal(signal_response, single_value=False, skip_none=True):
    """Combines the results from both single-value and multi-value signals.

    The signal needs to return either a single object (which is not a
    generator) or a generator (usually by returning its values using
    `yield`).

    :param signal_response: The return value of a Signal's `.send()` method
    :param single_value: If each return value should be treated aas a single
                         value in all cases (disables the generator check)
    :param skip_none: If None return values should be skipped
    :return: A set containing the results
    """
    values = set()
    for _, value in signal_response:
        if not single_value and isinstance(value, GeneratorType):
            values.update(value)
        else:
            values.add(value)
    if skip_none:
        values = {v for v in values if v is not None}
    return values
