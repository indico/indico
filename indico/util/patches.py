# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

"""
Some "monkey patches" for old Python versions
"""

import sys
import re
import operator as ops


VERSION_RE = re.compile(r'(\>=|\>|\<|\<=)?(\d)(?:\.(\d))?')
PATCHES = []


def _version_data(ver):
    m = VERSION_RE.match(ver)
    if m:
        m = m.groups()
        return (m[0], int(m[1]), int(m[2]))
    else:
        raise Exception("Wrong version specification: '{}'".format(ver))


def _version_matches(my_ver, op, rule_ver):

    return {
        None: ops.eq,
        '>': ops.gt,
        '<': ops.lt,
        '>=': ops.ge,
        '<=': ops.le
    }[op](my_ver, rule_ver)


def version(ver):
    def wrapper(f):
        version_data = _version_data(ver)
        PATCHES.append((version_data, f))
    return wrapper


@version('2.6')
def ordered_dict():
    """
    Support for OrderedDict on 2.6 is added by the `ordereddict` package,
    but we need to make it available inside `collections`
    """
    import collections
    try:
        from ordereddict import OrderedDict
        collections.OrderedDict = OrderedDict
    except:
        # during the setup process, indico.* will be imported
        # and this will be triggered
        pass


def apply_patches():
    for (op, maj, minor), func in PATCHES:
        if _version_matches((maj, minor), op, sys.version_info[:2]):
            func()
