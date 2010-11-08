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
Here are included the listeners and other components that are part of the
`livesync` plugin type.
"""

# dependency libs
from zope.interface import implements

# indico imports
from indico.core.api import Component
from indico.core.api.category import ICategoryActionListener
from indico.core.api.db import IDBUpdateListener, DBUpdateException

from indico.ext.livesync.persistent import ActionWrapper
from indico.ext.livesync.util import getPluginType

class LiveSyncCoreListener(Component):

    implements(ICategoryActionListener)

    def _add(self, obj, actions):
        """
        Adds a provided object to the index.
        Actions: ['moved','deleted',..]
        """
        track = getPluginType().getStorage()['track']
        wrapper = ActionWrapper(timestamp, obj, actions)

        track.add(timestamp, wrapper)

    def categoryMoved(self, category, oldOwner, newOwner):

        changes = ['moved']

        # protection status changed?
        if oldOwner.isProtected() != newOwner.isProtected():
            # notify protection change too
            changes += ['protection']

        self._add(category, changes)
