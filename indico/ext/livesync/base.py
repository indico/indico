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

"""
Base module
"""

# dependency libs
from persistent import Persistent
from indico.core.extpoint import IContributor


MPT_GRANULARITY = 100


class ILiveSyncAgentProvider(IContributor):
    """
    Implemented by classes that provide a LiveSync Agent
    """

    def providesLiveSyncAgentType(self, typeDict):
        pass


class ActionWrapper(Persistent):
    """
    "Orderable" wrapper for actions, that encloses information about a performed
    operation
    """

    def __init__(self, timestamp, obj, actions, objId):
        self._timestamp = timestamp
        self._obj = obj
        self._objId = objId
        self._actions = actions

    def getObject(self):
        return self._obj

    def getObjectId(self):
        return self._objId

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
        return "<ActionWrapper@%s (%s %s) [%s] %s>" % (hex(id(self)),
                                                    self._obj,
                                                    self._objId,
                                                    ','.join(self._actions),
                                                    self._timestamp)

    def __timestamp__(self):
        return self._timestamp
