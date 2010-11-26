# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Base module
"""

# dependency libs
from persistent import Persistent


class ActionWrapper(Persistent):
    """
    "Orderable" wrapper for actions, that encloses information about a performed
    operation
    """

    def __init__(self, timestamp, obj, actions):
        self._timestamp = timestamp
        self._obj = obj
        self._actions = actions

    def getObject(self):
        return self._obj

    def getActions(self):
        return self._actions

    def __cmp__(self, action):
        """
        Comparison takes timestamp into account, then object, then actions
        (high timestamps first)
        """

        # the 'minus' is intentional
        tscmp = -cmp(self._timestamp, action._timestamp)

        if tscmp == 0:
            ocmp = cmp(self._obj, action._obj)
            if ocmp == 0:
                return cmp(sorted(self._actions), sorted(action._actions))
            else:
                return ocmp
        else:
            return tscmp

    def __str__(self):
        return "<ActionWrapper@%s (%s) [%s] %s>" % (hex(id(self)),
                                                    self._obj,
                                                    ','.join(self._actions),
                                                    self._timestamp)
