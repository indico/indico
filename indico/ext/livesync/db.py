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
DB Update and related matters
"""

# dependecy libs
from zope.interface import implements

# indico imports
from indico.core.api import Component
from indico.core.api.db import IDBUpdateListener, DBUpdateException

# plugin imports
from indico.ext.livesync.util import getPluginType
from indico.ext.livesync.agent import SyncManager


class SystemUpdateListener(Component):

    implements(IDBUpdateListener)

    def updateDBStructures(self, object, component, fromVersion, toVersion, root):
        """
        Updates the DB for use with livesync
        """

        if component != 'indico.ext.livesync':
            # we do not care about other components, only for this plugin type
            return

        # get our storage
        ptype = getPluginType()
        storage = ptype.getStorage()

        # check if it is empty
        if len(storage) == 0:
            # nice, let's fill it
            storage['agent_manager'] = SyncManager()

        elif not fromVersion:
            # woops, this has already been done, and it is a fresh install!
            raise DBUpdateException("Storage for plugin type '%s' already exists!" % \
                                    ptype.getId())

        else:
            # the storage exists and we are doing an update, not a fresh install
            # in future versions, migration code will be added here
            pass

